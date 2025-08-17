"""
Admin client management endpoints.

Provides CRUD operations for client management with proper authentication
and audit logging. All endpoints require admin API key authentication.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging
import uuid
import secrets
from datetime import datetime
from google.cloud import firestore

from ..firestore_client import firestore_client
from ..schemas import ClientCreate, ClientUpdate, ClientResponse
from ..auth import verify_admin_access, log_admin_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin")


@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(api_key_id: str = Depends(verify_admin_access)):
    """List all clients with domain count - REQUIRES ADMIN AUTH"""
    try:
        # Get all clients
        clients_stream = firestore_client.clients_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        
        clients = []
        for doc in clients_stream:
            client_data = doc.to_dict()
            
            # Count domains for this client
            domain_count = len(list(
                firestore_client.domain_index_ref
                .where('client_id', '==', client_data['client_id'])
                .stream()
            ))
            
            # Convert to response model
            client_response = ClientResponse(
                **client_data,
                domain_count=domain_count
            )
            clients.append(client_response)
        
        log_admin_action(api_key_id, "list_clients", {"count": len(clients)})
        logger.info(f"Listed {len(clients)} clients for admin {api_key_id}")
        return clients
        
    except Exception as e:
        logger.error(f"Failed to list clients: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clients")


@router.post("/clients", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    api_key_id: str = Depends(verify_admin_access)
):
    """Create new client - REQUIRES ADMIN AUTH"""
    try:
        # Generate unique client_id
        client_id = f"client_{uuid.uuid4().hex[:12]}"
        
        # Prepare client document
        client_doc_data = {
            "client_id": client_id,
            "name": client_data.name,
            "email": client_data.email,
            "client_type": client_data.client_type,
            "owner": client_data.owner,
            "billing_entity": client_data.billing_entity or client_data.owner,
            "privacy_level": client_data.privacy_level,
            "ip_collection_enabled": True,
            "consent_required": client_data.privacy_level in ['gdpr', 'hipaa'],
            "features": client_data.features,
            "deployment_type": client_data.deployment_type,
            "vm_hostname": client_data.vm_hostname,
            "billing_rate_per_1k": 0.01,  # Default rate
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Generate IP salt for privacy levels that require it
        if client_data.privacy_level in ['gdpr', 'hipaa']:
            client_doc_data['ip_salt'] = secrets.token_urlsafe(32)
        
        # Save to Firestore
        firestore_client.clients_ref.document(client_id).set(client_doc_data)
        
        # Log admin action
        log_admin_action(api_key_id, "create_client", {
            "client_id": client_id,
            "name": client_data.name,
            "privacy_level": client_data.privacy_level
        })
        
        # Return response
        response = ClientResponse(**client_doc_data, domain_count=0)
        logger.info(f"Created client {client_id} for admin {api_key_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create client: {e}")
        raise HTTPException(status_code=500, detail="Failed to create client")


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    api_key_id: str = Depends(verify_admin_access)
):
    """Get client details - REQUIRES ADMIN AUTH"""
    try:
        # Get client document
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = client_doc.to_dict()
        
        # Count domains
        domain_count = len(list(
            firestore_client.domain_index_ref
            .where('client_id', '==', client_id)
            .stream()
        ))
        
        # Return response
        response = ClientResponse(**client_data, domain_count=domain_count)
        logger.info(f"Retrieved client {client_id} for admin {api_key_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve client")


@router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    updates: ClientUpdate,
    api_key_id: str = Depends(verify_admin_access)
):
    """Update client configuration - REQUIRES ADMIN AUTH"""
    try:
        # Get existing client
        client_doc = firestore_client.clients_ref.document(client_id)
        current_data = client_doc.get()
        
        if not current_data.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        current_client_data = current_data.to_dict()
        
        # Prepare updates
        update_data = {}
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        update_data['updated_at'] = datetime.utcnow()
        
        # Update in Firestore
        client_doc.update(update_data)
        
        # Get updated data
        updated_doc = client_doc.get()
        updated_data = updated_doc.to_dict()
        
        # Count domains
        domain_count = len(list(
            firestore_client.domain_index_ref
            .where('client_id', '==', client_id)
            .stream()
        ))
        
        # Log admin action
        log_admin_action(api_key_id, "update_client", {
            "client_id": client_id,
            "updated_fields": list(update_data.keys())
        })
        
        # Return response
        response = ClientResponse(**updated_data, domain_count=domain_count)
        logger.info(f"Updated client {client_id} for admin {api_key_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update client")