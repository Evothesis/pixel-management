# backend/app/main.py - SECURED VERSION WITH ADMIN AUTHENTICATION
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging
from datetime import datetime
from google.cloud import firestore

from .firestore_client import firestore_client
from .models import ClientDocument, DomainDocument, DomainIndexDocument  
from .schemas import (
    ClientCreate, ClientUpdate, ClientResponse, 
    DomainCreate, DomainResponse, ClientConfigResponse
)
# REPLACED OLD AUTH - Import secure admin authentication
from .auth import verify_admin_access, log_admin_action

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Evothesis Pixel Management", version="1.0.0")

# CORS middleware - TODO: Restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Startup: Initialize Firestore and Create Default Admin
# ============================================================================

@app.on_event("startup")
async def initialize_firestore():
    """Initialize Firestore and create default admin client"""
    try:
        # Test Firestore connection
        if firestore_client.test_connection():
            logger.info("Firestore connection successful")
            
            # Create default admin client if it doesn't exist
            admin_client_id = "client_evothesis_admin"
            admin_doc = firestore_client.clients_ref.document(admin_client_id).get()
            
            if not admin_doc.exists:
                admin_client_data = {
                    "client_id": admin_client_id,
                    "name": "Evothesis Admin",
                    "email": "admin@evothesis.com",
                    "client_type": "admin",
                    "owner": admin_client_id,  # Self-owned
                    "billing_entity": admin_client_id,
                    "privacy_level": "standard",
                    "ip_collection_enabled": True,
                    "consent_required": False,
                    "features": {"admin_panel": True},
                    "deployment_type": "dedicated",
                    "vm_hostname": None,
                    "billing_rate_per_1k": 0.0,
                    "created_at": datetime.utcnow(),
                    "is_active": True
                }
                
                firestore_client.clients_ref.document(admin_client_id).set(admin_client_data)
                logger.info(f"Created default admin client: {admin_client_id}")
            else:
                logger.info("Default admin client already exists")
        else:
            logger.error("Failed to connect to Firestore")
            
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")

# ============================================================================
# Configuration API (Public - for Tracking VMs)
# ============================================================================

@app.get("/api/v1/config/domain/{domain}", response_model=ClientConfigResponse)
async def get_config_by_domain(domain: str):
    """
    CRITICAL: Domain authorization endpoint for tracking infrastructure
    This endpoint validates domain authorization and returns client configuration
    """
    try:
        # Look up domain in domain index
        domain_docs = list(firestore_client.domain_index_ref.where('domain', '==', domain).limit(1).stream())
        
        if not domain_docs:
            logger.warning(f"Unauthorized domain access attempt: {domain}")
            raise HTTPException(
                status_code=404, 
                detail=f"Domain {domain} not authorized for tracking"
            )
        
        domain_data = domain_docs[0].to_dict()
        client_id = domain_data['client_id']
        
        logger.info(f"Domain {domain} authorized for client {client_id}")
        
        # Get client configuration
        return await get_client_config(client_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain lookup failed for {domain}: {e}")
        raise HTTPException(status_code=500, detail="Configuration service error")

@app.get("/api/v1/config/client/{client_id}", response_model=ClientConfigResponse)
async def get_client_config(client_id: str):
    """
    CRITICAL: Core configuration retrieval for tracking infrastructure
    Returns client-specific tracking configuration
    """
    try:
        client_doc = firestore_client.clients_ref.document(client_id).get()
        
        if not client_doc.exists:
            logger.warning(f"Client not found: {client_id}")
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = client_doc.to_dict()
        
        if not client_data.get('is_active', True):
            logger.warning(f"Inactive client access attempt: {client_id}")
            raise HTTPException(status_code=404, detail="Client inactive")
        
        # Build configuration response
        config = ClientConfigResponse(
            client_id=client_data['client_id'],
            privacy_level=client_data['privacy_level'],
            ip_collection={
                "enabled": client_data['ip_collection_enabled'],
                "hash_required": client_data['privacy_level'] in ["gdpr", "hipaa"],
                "salt": client_data.get('ip_salt') if client_data['privacy_level'] in ["gdpr", "hipaa"] else None
            },
            consent={
                "required": client_data['consent_required'],
                "default_behavior": "block" if client_data['privacy_level'] in ["gdpr", "hipaa"] else "allow"
            },
            features=client_data.get('features', {}),
            deployment={
                "type": client_data['deployment_type'],
                "hostname": client_data.get('vm_hostname')
            }
        )
        
        logger.info(f"Served config for client {client_id} (privacy: {client_data['privacy_level']})")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Client config lookup failed for {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Configuration service error")

# ============================================================================
# SECURED ADMIN API: Client Management (AUTHENTICATION REQUIRED)
# ============================================================================

@app.get("/api/v1/admin/clients", response_model=List[ClientResponse])
async def list_clients(api_key_id: str = Depends(verify_admin_access)):
    """List all clients with domain count - REQUIRES ADMIN AUTH"""
    try:
        # Get all clients
        clients_stream = firestore_client.clients_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        
        clients = []
        for doc in clients_stream:
            client_data = doc.to_dict()
            
            # Count domains for this client
            domain_count = len(list(firestore_client.domain_index_ref.where('client_id', '==', client_data['client_id']).stream()))
            
            # Build response
            client_response = ClientResponse(
                client_id=client_data['client_id'],
                name=client_data['name'],
                email=client_data.get('email'),
                client_type=client_data.get('client_type', 'end_client'),
                owner=client_data['owner'],
                billing_entity=client_data['billing_entity'],
                privacy_level=client_data['privacy_level'],
                ip_collection_enabled=client_data['ip_collection_enabled'],
                consent_required=client_data['consent_required'],
                features=client_data.get('features', {}),
                deployment_type=client_data['deployment_type'],
                vm_hostname=client_data.get('vm_hostname'),
                billing_rate_per_1k=client_data.get('billing_rate_per_1k', 0.01),
                created_at=client_data['created_at'],
                updated_at=client_data.get('updated_at'),
                is_active=client_data.get('is_active', True),
                domain_count=domain_count
            )
            clients.append(client_response)
        
        # Audit log
        log_admin_action("list_clients", None, api_key_id, f"Retrieved {len(clients)} clients")
        
        logger.info(f"Listed {len(clients)} clients for {api_key_id}")
        return clients
        
    except Exception as e:
        logger.error(f"Failed to list clients: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clients")

@app.post("/api/v1/admin/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, api_key_id: str = Depends(verify_admin_access)):
    """Create new client - REQUIRES ADMIN AUTH"""
    try:
        # Generate unique client ID
        client_id = firestore_client.generate_client_id()
        
        # Generate salt for GDPR/HIPAA clients
        ip_salt = None
        if client_data.privacy_level in ["gdpr", "hipaa"]:
            ip_salt = firestore_client.generate_ip_salt()
        
        # Prepare client document
        now = datetime.utcnow()
        client_doc_data = {
            "client_id": client_id,
            "name": client_data.name,
            "email": client_data.email,
            "client_type": client_data.client_type,
            "owner": client_data.owner,
            "billing_entity": client_data.billing_entity or client_data.owner,
            "privacy_level": client_data.privacy_level,
            "ip_collection_enabled": client_data.privacy_level != "gdpr",  # Default based on privacy
            "ip_salt": ip_salt,
            "consent_required": client_data.privacy_level in ["gdpr", "hipaa"],
            "features": client_data.features,
            "deployment_type": client_data.deployment_type,
            "vm_hostname": client_data.vm_hostname,
            "billing_rate_per_1k": 0.01,  # Default rate
            "created_at": now,
            "updated_at": now,
            "is_active": True
        }
        
        # Save to Firestore
        firestore_client.clients_ref.document(client_id).set(client_doc_data)
        
        # Build response
        response = ClientResponse(
            client_id=client_id,
            name=client_data.name,
            email=client_data.email,
            client_type=client_data.client_type,
            owner=client_data.owner,
            billing_entity=client_doc_data["billing_entity"],
            privacy_level=client_data.privacy_level,
            ip_collection_enabled=client_doc_data["ip_collection_enabled"],
            consent_required=client_doc_data["consent_required"],
            features=client_data.features,
            deployment_type=client_data.deployment_type,
            vm_hostname=client_data.vm_hostname,
            billing_rate_per_1k=0.01,
            created_at=now,
            updated_at=now,
            is_active=True,
            domain_count=0
        )
        
        # Audit log
        log_admin_action("create_client", client_id, api_key_id, f"Created client '{client_data.name}' with privacy level {client_data.privacy_level}")
        
        logger.info(f"Created client {client_id} for {api_key_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create client: {e}")
        raise HTTPException(status_code=500, detail="Failed to create client")

@app.get("/api/v1/admin/clients/{client_id}", response_model=ClientResponse)
async def get_client_details(client_id: str, api_key_id: str = Depends(verify_admin_access)):
    """Get client details - REQUIRES ADMIN AUTH"""
    try:
        client_doc = firestore_client.clients_ref.document(client_id).get()
        
        if not client_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = client_doc.to_dict()
        
        # Count domains
        domain_count = len(list(firestore_client.domain_index_ref.where('client_id', '==', client_id).stream()))
        
        # Build response
        response = ClientResponse(
            client_id=client_data['client_id'],
            name=client_data['name'],
            email=client_data.get('email'),
            client_type=client_data.get('client_type', 'end_client'),
            owner=client_data['owner'],
            billing_entity=client_data['billing_entity'],
            privacy_level=client_data['privacy_level'],
            ip_collection_enabled=client_data['ip_collection_enabled'],
            consent_required=client_data['consent_required'],
            features=client_data.get('features', {}),
            deployment_type=client_data['deployment_type'],
            vm_hostname=client_data.get('vm_hostname'),
            billing_rate_per_1k=client_data.get('billing_rate_per_1k', 0.01),
            created_at=client_data['created_at'],
            updated_at=client_data.get('updated_at'),
            is_active=client_data.get('is_active', True),
            domain_count=domain_count
        )
        
        # Audit log
        log_admin_action("get_client_details", client_id, api_key_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve client")

@app.put("/api/v1/admin/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, updates: ClientUpdate, api_key_id: str = Depends(verify_admin_access)):
    """Update client configuration - REQUIRES ADMIN AUTH"""
    try:
        client_doc_ref = firestore_client.clients_ref.document(client_id)
        client_doc = client_doc_ref.get()
        
        if not client_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Prepare update data (only non-None fields)
        update_data = {}
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # Add updated timestamp
        update_data['updated_at'] = datetime.utcnow()
        
        # Update in Firestore
        client_doc_ref.update(update_data)
        
        # Get updated client for response
        updated_doc = client_doc_ref.get()
        updated_data = updated_doc.to_dict()
        
        # Count domains
        domain_count = len(list(firestore_client.domain_index_ref.where('client_id', '==', client_id).stream()))
        
        # Build response
        response = ClientResponse(
            client_id=updated_data['client_id'],
            name=updated_data['name'],
            email=updated_data.get('email'),
            client_type=updated_data.get('client_type', 'end_client'),
            owner=updated_data['owner'],
            billing_entity=updated_data['billing_entity'],
            privacy_level=updated_data['privacy_level'],
            ip_collection_enabled=updated_data['ip_collection_enabled'],
            consent_required=updated_data['consent_required'],
            features=updated_data.get('features', {}),
            deployment_type=updated_data['deployment_type'],
            vm_hostname=updated_data.get('vm_hostname'),
            billing_rate_per_1k=updated_data.get('billing_rate_per_1k', 0.01),
            created_at=updated_data['created_at'],
            updated_at=updated_data['updated_at'],
            is_active=updated_data.get('is_active', True),
            domain_count=domain_count
        )
        
        # Audit log
        log_admin_action("update_client", client_id, api_key_id, f"Updated fields: {list(update_data.keys())}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update client: {e}")
        raise HTTPException(status_code=500, detail="Failed to update client")

@app.delete("/api/v1/admin/clients/{client_id}")
async def delete_client(client_id: str, api_key_id: str = Depends(verify_admin_access)):
    """Delete client and all associated domains - REQUIRES ADMIN AUTH"""
    try:
        # Verify client exists
        client_doc_ref = firestore_client.clients_ref.document(client_id)
        client_doc = client_doc_ref.get()
        
        if not client_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = client_doc.to_dict()
        client_name = client_data.get('name', 'Unknown')
        
        # Prevent deletion of admin client
        if client_data.get('client_type') == 'admin':
            raise HTTPException(status_code=400, detail="Cannot delete admin client")
        
        # Delete all associated domains
        domain_docs = list(firestore_client.domain_index_ref.where('client_id', '==', client_id).stream())
        for domain_doc in domain_docs:
            domain_doc.reference.delete()
        
        # Delete the client
        client_doc_ref.delete()
        
        # Audit log
        log_admin_action("delete_client", client_id, api_key_id, f"Deleted client: {client_name} and {len(domain_docs)} domains")
        
        return {"message": f"Client {client_name} and {len(domain_docs)} associated domains deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete client: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete client")

@app.post("/api/v1/admin/clients/{client_id}/domains")
async def add_domain_to_client(client_id: str, domain_data: DomainCreate, api_key_id: str = Depends(verify_admin_access)):
    """Add domain to client - REQUIRES ADMIN AUTH"""
    try:
        # Verify client exists
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check if domain already exists
        existing_domains = list(firestore_client.domain_index_ref.where('domain', '==', domain_data.domain).limit(1).stream())
        if existing_domains:
            existing_client_id = existing_domains[0].to_dict()['client_id']
            raise HTTPException(status_code=400, detail=f"Domain {domain_data.domain} already assigned to client {existing_client_id}")
        
        # Add domain to index
        domain_doc_data = {
            "domain": domain_data.domain,
            "client_id": client_id,
            "is_primary": domain_data.is_primary,
            "created_at": datetime.utcnow()
        }
        
        firestore_client.domain_index_ref.add(domain_doc_data)
        
        # Audit log
        log_admin_action("add_domain", client_id, api_key_id, f"Added domain: {domain_data.domain}")
        
        return {"message": f"Domain {domain_data.domain} added to client {client_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add domain: {e}")
        raise HTTPException(status_code=500, detail="Failed to add domain")

@app.get("/api/v1/admin/clients/{client_id}/domains", response_model=List[DomainResponse])
async def get_client_domains(client_id: str, api_key_id: str = Depends(verify_admin_access)):
    """Get domains for client - REQUIRES ADMIN AUTH"""
    try:
        # Verify client exists
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get domains
        domain_docs = list(firestore_client.domain_index_ref.where('client_id', '==', client_id).stream())
        
        domains = []
        for doc in domain_docs:
            domain_data = doc.to_dict()
            domains.append(DomainResponse(
                id=doc.id,
                domain=domain_data['domain'],
                is_primary=domain_data['is_primary'],
                created_at=domain_data['created_at']
            ))
        
        # Audit log
        log_admin_action("list_client_domains", client_id, api_key_id, f"Retrieved {len(domains)} domains")
        
        return domains
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client domains: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve domains")

@app.delete("/api/v1/admin/clients/{client_id}/domains/{domain}")
async def remove_domain_from_client(client_id: str, domain: str, api_key_id: str = Depends(verify_admin_access)):
    """Remove domain from client - REQUIRES ADMIN AUTH"""
    try:
        # Find the domain document
        domain_docs = list(firestore_client.domain_index_ref.where('domain', '==', domain).where('client_id', '==', client_id).limit(1).stream())
        
        if not domain_docs:
            raise HTTPException(status_code=404, detail=f"Domain {domain} not found for client {client_id}")
        
        # Delete the domain
        domain_docs[0].reference.delete()
        
        # Audit log
        log_admin_action("remove_domain", client_id, api_key_id, f"Removed domain: {domain}")
        
        return {"message": f"Domain {domain} removed from client {client_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove domain: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove domain")

# ============================================================================
# Health Check (Public)
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check with Firestore connectivity test"""
    try:
        # Test Firestore connection
        firestore_connected = firestore_client.test_connection()
        
        if firestore_connected:
            return {
                "status": "healthy",
                "service": "pixel-management", 
                "database": "firestore_connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "degraded",
                "service": "pixel-management",
                "database": "firestore_error", 
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy", 
            "service": "pixel-management",
            "database": "firestore_error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# Admin Setup Helper (Development)
# ============================================================================

@app.get("/admin/setup-info")
async def get_admin_setup_info():
    """Get admin setup information for development"""
    from .auth import get_current_admin_api_key
    
    return {
        "service": "Evothesis Pixel Management",
        "version": "1.0.0",
        "admin_api_key": get_current_admin_api_key(),
        "usage": {
            "header": "Authorization: Bearer <admin_api_key>",
            "endpoints": {
                "list_clients": "GET /api/v1/admin/clients",
                "create_client": "POST /api/v1/admin/clients",
                "get_client": "GET /api/v1/admin/clients/{client_id}",
                "update_client": "PUT /api/v1/admin/clients/{client_id}",
                "add_domain": "POST /api/v1/admin/clients/{client_id}/domains",
                "list_domains": "GET /api/v1/admin/clients/{client_id}/domains",
                "remove_domain": "DELETE /api/v1/admin/clients/{client_id}/domains/{domain}"
            }
        }
    }

# ============================================================================
# Static File Serving (Production)
# ============================================================================

# Serve React static files (for production deployment)
if os.path.exists("/app/static"):
    app.mount("/static", StaticFiles(directory="/app/static/static"), name="static")
    
    @app.get("/", include_in_schema=False)
    async def serve_react_app():
        """Serve React app for production"""
        return FileResponse("/app/static/index.html")
    
    @app.get("/{path:path}", include_in_schema=False)
    async def serve_react_routes(path: str):
        """Serve React app for all non-API routes"""
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        return FileResponse("/app/static/index.html")