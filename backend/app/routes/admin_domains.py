"""
Admin domain management endpoints.

Provides domain authorization management for clients with proper authentication
and audit logging. All endpoints require admin API key authentication.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging
from datetime import datetime
from google.cloud import firestore

from ..firestore_client import firestore_client
from ..schemas import DomainCreate, DomainResponse
from ..auth import verify_admin_access, log_admin_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin")


@router.post("/clients/{client_id}/domains", response_model=DomainResponse)
async def add_domain_to_client(
    client_id: str,
    domain_data: DomainCreate,
    api_key_id: str = Depends(verify_admin_access)
):
    """Add domain to client - REQUIRES ADMIN AUTH"""
    try:
        # Verify client exists
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        domain_name = domain_data.domain.lower().strip()
        
        # Check if domain already exists
        existing_domains = list(
            firestore_client.domain_index_ref
            .where('domain', '==', domain_name)
            .stream()
        )
        
        if existing_domains:
            existing_client = existing_domains[0].to_dict()['client_id']
            if existing_client != client_id:
                raise HTTPException(
                    status_code=409, 
                    detail=f"Domain already assigned to client {existing_client}"
                )
            else:
                raise HTTPException(status_code=409, detail="Domain already exists for this client")
        
        # Create domain documents
        domain_doc_id = f"{client_id}_{domain_name.replace('.', '_')}"
        domain_doc_data = {
            "domain": domain_name,
            "is_primary": domain_data.is_primary,
            "created_at": datetime.utcnow()
        }
        
        # Add to client's domains subcollection
        firestore_client.clients_ref.document(client_id).collection('domains').document(domain_doc_id).set(domain_doc_data)
        
        # Add to global domain index
        domain_index_data = {
            "client_id": client_id,
            "domain": domain_name,
            "is_primary": domain_data.is_primary,
            "created_at": datetime.utcnow()
        }
        firestore_client.domain_index_ref.document(domain_doc_id).set(domain_index_data)
        
        # Log admin action
        log_admin_action(api_key_id, "add_domain", {
            "client_id": client_id,
            "domain": domain_name,
            "is_primary": domain_data.is_primary
        })
        
        # Return response
        response = DomainResponse(
            id=domain_doc_id,
            **domain_doc_data
        )
        logger.info(f"Added domain {domain_name} to client {client_id} for admin {api_key_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add domain to client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add domain")


@router.get("/clients/{client_id}/domains", response_model=List[DomainResponse])
async def list_client_domains(
    client_id: str,
    api_key_id: str = Depends(verify_admin_access)
):
    """List client domains - REQUIRES ADMIN AUTH"""
    try:
        # Verify client exists
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get domains from domain_index
        domain_docs = list(
            firestore_client.domain_index_ref
            .where('client_id', '==', client_id)
            .order_by('created_at', direction=firestore.Query.DESCENDING)
            .stream()
        )
        
        domains = []
        for doc in domain_docs:
            domain_data = doc.to_dict()
            domain_response = DomainResponse(
                id=doc.id,
                domain=domain_data['domain'],
                is_primary=domain_data.get('is_primary', False),
                created_at=domain_data['created_at']
            )
            domains.append(domain_response)
        
        logger.info(f"Listed {len(domains)} domains for client {client_id} for admin {api_key_id}")
        return domains
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list domains for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list domains")


@router.delete("/clients/{client_id}/domains/{domain}")
async def remove_domain_from_client(
    client_id: str,
    domain: str,
    api_key_id: str = Depends(verify_admin_access)
):
    """Remove domain from client - REQUIRES ADMIN AUTH"""
    try:
        domain_name = domain.lower().strip()
        domain_doc_id = f"{client_id}_{domain_name.replace('.', '_')}"
        
        # Remove from client's domains subcollection
        client_domain_doc = firestore_client.clients_ref.document(client_id).collection('domains').document(domain_doc_id)
        if client_domain_doc.get().exists:
            client_domain_doc.delete()
        
        # Remove from global domain index
        domain_index_doc = firestore_client.domain_index_ref.document(domain_doc_id)
        if domain_index_doc.get().exists:
            domain_index_doc.delete()
        
        # Log admin action
        log_admin_action(api_key_id, "remove_domain", {
            "client_id": client_id,
            "domain": domain_name
        })
        
        logger.info(f"Removed domain {domain_name} from client {client_id} for admin {api_key_id}")
        return {"message": f"Domain {domain_name} removed from client {client_id}"}
        
    except Exception as e:
        logger.error(f"Failed to remove domain {domain} from client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove domain")