# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from google.cloud import firestore

from .firestore_client import firestore_client
from .schemas import (
    ClientCreate, ClientUpdate, ClientResponse, 
    DomainCreate, DomainResponse, ClientConfigResponse,
    APIKeyCreate, APIKeyCreateResponse, APIKeyResponse
)
from .auth import get_current_user_client_id, require_owner_access, require_owner_or_self_access
from .auth_middleware import BasicAuthMiddleware, require_config_read_permission

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Evothesis Pixel Management", version="1.0.0")

# CORS middleware (before auth middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Basic Auth middleware for production protection
# This will protect ALL routes including static files
if os.getenv("ENVIRONMENT") == "production":
    logger.info("Production mode: Enabling Basic Authentication")
    auth_middleware = BasicAuthMiddleware()
    app.middleware("http")(auth_middleware)
else:
    logger.info("Development mode: Basic Authentication disabled")

# Add this debug endpoint temporarily
@app.get("/debug/static")
async def debug_static():
    """Debug static file structure"""
    import os
    result = {}
    
    if os.path.exists("/app/static"):
        result["static_exists"] = True
        result["static_contents"] = os.listdir("/app/static")
        
        # Check for nested static
        if os.path.exists("/app/static/static"):
            result["nested_static_contents"] = os.listdir("/app/static/static")
        else:
            result["nested_static_exists"] = False
        
        # Find all JS and CSS files recursively
        js_files = []
        css_files = []
        for root, dirs, files in os.walk("/app/static"):
            for file in files:
                full_path = os.path.join(root, file)
                if file.endswith('.js'):
                    js_files.append(full_path)
                elif file.endswith('.css'):
                    css_files.append(full_path)
        
        result["js_files"] = js_files
        result["css_files"] = css_files
    else:
        result["static_exists"] = False
    
    return result

# ============================================================================
# PUBLIC API: Configuration Endpoints (SERVICE-TO-SERVICE)
# These endpoints are called by server-infrastructure service
# PROTECTED BY API KEY AUTHENTICATION
# ============================================================================

@app.get("/api/v1/config/domain/{domain}")
async def get_domain_config(
    domain: str, 
    api_key_data: Dict[str, Any] = Depends(require_config_read_permission)
):
    """
    Get client configuration for a domain (SERVICE-TO-SERVICE ONLY)
    
    REQUIRES: X-API-Key header with config:read permission
    Used by: server-infrastructure service for domain validation
    
    This endpoint validates that a domain is authorized and returns
    the associated client information for tracking pixel generation.
    """
    try:
        # Normalize domain
        domain = domain.lower().strip()
        
        # Look up domain in domain index (O(1) lookup)
        domain_doc = firestore_client.domain_index_ref.document(domain).get()
        
        if not domain_doc.exists:
            logger.warning(f"Domain {domain} not found (API key: {api_key_data['id']})")
            raise HTTPException(status_code=404, detail="Domain not authorized")
        
        domain_data = domain_doc.to_dict()
        client_id = domain_data['client_id']
        
        # Get client configuration
        client_doc = firestore_client.clients_ref.document(client_id).get()
        
        if not client_doc.exists:
            logger.error(f"Client {client_id} for domain {domain} not found")
            raise HTTPException(status_code=404, detail="Client configuration error")
        
        client_data = client_doc.to_dict()
        
        # Check if client is active
        if not client_data.get('is_active', True):
            logger.warning(f"Client {client_id} for domain {domain} inactive (API key: {api_key_data['id']})")
            raise HTTPException(status_code=404, detail="Client inactive")
        
        # Build response (matches what server-infrastructure expects)
        config = {
            "client_id": client_id,
            "domain": domain,
            "is_primary": domain_data.get('is_primary', False),
            "privacy_level": client_data['privacy_level'],
            "deployment_type": client_data['deployment_type'],
            "vm_hostname": client_data.get('vm_hostname')
        }
        
        logger.info(f"Domain {domain} → client {client_id} (API key: {api_key_data['id']})")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain config lookup failed for {domain}: {e}")
        raise HTTPException(status_code=500, detail="Configuration service error")

@app.get("/api/v1/config/client/{client_id}", response_model=ClientConfigResponse)
async def get_client_config_api(
    client_id: str,
    api_key_data: Dict[str, Any] = Depends(require_config_read_permission)
):
    """
    Get detailed client configuration (SERVICE-TO-SERVICE ONLY)
    
    REQUIRES: X-API-Key header with config:read permission
    Used by: server-infrastructure service for pixel generation
    
    This endpoint returns complete client configuration including
    privacy settings, IP collection rules, and feature flags.
    """
    try:
        client_doc = firestore_client.clients_ref.document(client_id).get()
        
        if not client_doc.exists:
            logger.warning(f"Client {client_id} not found (API key: {api_key_data['id']})")
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = client_doc.to_dict()
        if not client_data.get('is_active', True):
            logger.warning(f"Client {client_id} inactive (API key: {api_key_data['id']})")
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
        
        logger.info(f"Client config served for {client_id} (privacy: {client_data['privacy_level']}, API key: {api_key_data['id']})")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Client config lookup failed for {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Configuration service error")

# ============================================================================
# Startup: Initialize Firestore and Create Default Admin
# ============================================================================

@app.on_event("startup")
async def initialize_firestore():
    """Initialize Firestore and create default admin client"""
    try:
        # Test Firestore connection (will auto-create database if needed)
        firestore_client.db.collection('_initialization').document('startup').set({
            'initialized_at': firestore.SERVER_TIMESTAMP,
            'service': 'pixel-management',
            'version': '1.0.0'
        })
        
        # Create default admin client
        await create_default_admin()
        
        logger.info("Firestore initialized successfully")
        
    except Exception as e:
        logger.error(f"Firestore initialization failed: {e}")
        # Don't raise - let the service start anyway for debugging

async def create_default_admin():
    """Create default Evothesis admin client if it doesn't exist"""
    admin_client_id = "client_evothesis_admin"
    
    try:
        admin_doc = firestore_client.clients_ref.document(admin_client_id).get()
        
        if not admin_doc.exists:
            admin_data = {
                "client_id": admin_client_id,
                "name": "Evothesis Admin",
                "email": "admin@evothesis.com",
                "owner": admin_client_id,           # Self-owned
                "billing_entity": admin_client_id,  # Self-billed
                "client_type": "admin",
                "deployment_type": "shared",
                "privacy_level": "standard",
                "ip_collection_enabled": True,
                "ip_salt": firestore_client.generate_ip_salt(),
                "consent_required": False,
                "features": {},
                "billing_rate_per_1k": 0.01,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": None,
                "is_active": True
            }
            
            firestore_client.clients_ref.document(admin_client_id).set(admin_data)
            logger.info(f"Created default admin client: {admin_client_id}")
        else:
            logger.info("Default admin client already exists")
            
    except Exception as e:
        logger.error(f"Failed to create default admin client: {e}")

# ============================================================================
# ADMIN API: API Key Management
# ============================================================================

@app.post("/api/v1/admin/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(api_key_data: APIKeyCreate):
    """Create new API key for service-to-service authentication"""
    try:
        user_client_id = get_current_user_client_id()
        
        key_id, api_key = firestore_client.create_api_key(
            name=api_key_data.name,
            permissions=api_key_data.permissions,
            created_by=user_client_id,
            expires_at=api_key_data.expires_at
        )
        
        return APIKeyCreateResponse(
            id=key_id,
            name=api_key_data.name,
            api_key=api_key,
            key_preview=f"{api_key[:8]}...{api_key[-4:]}",
            permissions=api_key_data.permissions,
            created_at=datetime.utcnow(),
            expires_at=api_key_data.expires_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")

@app.get("/api/v1/admin/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys():
    """List all API keys (with masked key values)"""
    try:
        user_client_id = get_current_user_client_id()
        
        api_keys = []
        keys_stream = firestore_client.api_keys_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        
        for doc in keys_stream:
            key_data = doc.to_dict()
            
            api_keys.append(APIKeyResponse(
                id=key_data['id'],
                name=key_data['name'],
                permissions=key_data['permissions'],
                key_preview=f"evpx_****...****",
                created_at=key_data['created_at'],
                created_by=key_data['created_by'],
                is_active=key_data['is_active'],
                last_used_at=key_data.get('last_used_at'),
                expires_at=key_data.get('expires_at')
            ))
        
        logger.info(f"Listed {len(api_keys)} API keys for user {user_client_id}")
        return api_keys
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve API keys")

@app.delete("/api/v1/admin/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    """Deactivate an API key"""
    try:
        user_client_id = get_current_user_client_id()
        
        success = firestore_client.deactivate_api_key(key_id)
        if success:
            logger.info(f"API key {key_id} deactivated by {user_client_id}")
            return {"message": f"API key {key_id} deactivated"}
        else:
            raise HTTPException(status_code=404, detail="API key not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate API key {key_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate API key")

# ============================================================================
# ADMIN API: Client Management
# ============================================================================

@app.get("/api/v1/admin/clients", response_model=List[ClientResponse])
async def list_clients():
    """List all clients with domain count"""
    try:
        user_client_id = get_current_user_client_id()
        
        # Get all clients (for now, admin can see all - add filtering later)
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
        
        logger.info(f"Listed {len(clients)} clients")
        return clients
        
    except Exception as e:
        logger.error(f"Failed to list clients: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clients")

@app.post("/api/v1/admin/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate):
    """Create new client"""
    try:
        user_client_id = get_current_user_client_id()
        
        # Generate unique client ID
        client_id = firestore_client.generate_client_id()
        
        # Set billing entity to owner if not specified
        billing_entity = client_data.billing_entity or client_data.owner
        
        # Generate salt for GDPR/HIPAA clients
        ip_salt = None
        if client_data.privacy_level in ["gdpr", "hipaa"]:
            ip_salt = firestore_client.generate_ip_salt()
        
        # Build client document
        client_doc = {
            "client_id": client_id,
            "name": client_data.name,
            "email": client_data.email,
            "client_type": client_data.client_type,
            "owner": client_data.owner,
            "billing_entity": billing_entity,
            "deployment_type": client_data.deployment_type,
            "privacy_level": client_data.privacy_level,
            "ip_collection_enabled": client_data.privacy_level == "standard",
            "ip_salt": ip_salt,
            "consent_required": client_data.privacy_level in ["gdpr", "hipaa"],
            "features": client_data.features,
            "billing_rate_per_1k": 0.01,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": None,
            "is_active": True
        }
        
        # Store in Firestore
        firestore_client.clients_ref.document(client_id).set(client_doc)
        
        # Log configuration change
        change_doc = {
            "client_id": client_id,
            "changed_by": user_client_id,
            "change_description": f"Client created: {client_data.name}",
            "old_config": None,
            "new_config": client_doc,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        firestore_client.config_changes_ref.add(change_doc)
        
        # Build response
        created_data = client_doc.copy()
        created_data['created_at'] = datetime.utcnow()  # Replace server timestamp for response
        
        response = ClientResponse(
            client_id=client_id,
            name=client_data.name,
            email=client_data.email,
            client_type=client_data.client_type,
            owner=client_data.owner,
            billing_entity=billing_entity,
            privacy_level=client_data.privacy_level,
            ip_collection_enabled=created_data['ip_collection_enabled'],
            consent_required=created_data['consent_required'],
            features=client_data.features,
            deployment_type=client_data.deployment_type,
            vm_hostname=None,
            billing_rate_per_1k=0.01,
            created_at=created_data['created_at'],
            updated_at=created_data.get('updated_at'),
            is_active=created_data.get('is_active', True),
            domain_count=0  # New client has no domains yet
        )
        
        logger.info(f"Created client {client_id} (owner: {client_data.owner})")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create client: {e}")
        raise HTTPException(status_code=500, detail="Failed to create client")

@app.get("/api/v1/admin/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str):
    """Get client details"""
    try:
        user_client_id = get_current_user_client_id()
        
        # Check authorization and get client data
        client_data = require_owner_or_self_access(user_client_id, client_id)
        
        # Count domains for this client
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
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve client")

@app.put("/api/v1/admin/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, update_data: ClientUpdate):
    """Update client configuration"""
    try:
        user_client_id = get_current_user_client_id()
        
        # Check authorization and get current data
        current_data = require_owner_access(user_client_id, client_id)
        
        # Build update dictionary (only include non-None values)
        update_dict = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        # Always update the timestamp
        update_dict['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Update in Firestore
        firestore_client.clients_ref.document(client_id).update(update_dict)
        
        # Log configuration change
        change_doc = {
            "client_id": client_id,
            "changed_by": user_client_id,
            "change_description": f"Client updated: {', '.join(update_dict.keys())}",
            "old_config": {k: current_data.get(k) for k in update_dict.keys() if k != 'updated_at'},
            "new_config": {k: v for k, v in update_dict.items() if k != 'updated_at'},
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        firestore_client.config_changes_ref.add(change_doc)
        
        # Return updated client
        return await get_client(client_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update client")

# ============================================================================
# ADMIN API: Domain Management
# ============================================================================

@app.post("/api/v1/admin/clients/{client_id}/domains")
async def add_domain(client_id: str, domain_data: DomainCreate):
    """Add domain to client"""
    try:
        user_client_id = get_current_user_client_id()
        
        # Check authorization
        client_data = require_owner_access(user_client_id, client_id)
        
        domain = domain_data.domain.lower().strip()
        
        # Check if domain already exists
        existing_domain = firestore_client.domain_index_ref.document(domain).get()
        if existing_domain.exists:
            existing_data = existing_domain.to_dict()
            if existing_data['client_id'] != client_id:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Domain {domain} already assigned to client {existing_data['client_id']}"
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Domain {domain} already assigned to this client"
                )
        
        # Create domain index entry (for fast lookups)
        domain_index_doc = {
            "client_id": client_id,
            "domain": domain,
            "is_primary": domain_data.is_primary,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        firestore_client.domain_index_ref.document(domain).set(domain_index_doc)
        
        # Also create detailed domain document
        domain_doc_id = f"{client_id}_{domain.replace('.', '_')}"
        domain_doc = {
            "client_id": client_id,
            "domain": domain,
            "is_primary": domain_data.is_primary,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        firestore_client.db.collection('domains').document(domain_doc_id).set(domain_doc)
        
        # Log configuration change
        change_doc = {
            "client_id": client_id,
            "changed_by": user_client_id,
            "change_description": f"Domain added: {domain}",
            "old_config": None,
            "new_config": {"domain": domain, "is_primary": domain_data.is_primary},
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        firestore_client.config_changes_ref.add(change_doc)
        
        logger.info(f"Added domain {domain} to client {client_id}")
        return {"message": f"Domain {domain} added to client {client_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add domain {domain} to client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add domain")

@app.get("/api/v1/admin/clients/{client_id}/domains", response_model=List[DomainResponse])
async def get_client_domains(client_id: str):
    """Get all domains for a client"""
    try:
        user_client_id = get_current_user_client_id()
        
        # Check authorization
        require_owner_or_self_access(user_client_id, client_id)
        
        domains = []
        domain_docs = firestore_client.domain_index_ref.where('client_id', '==', client_id).stream()
        
        for doc in domain_docs:
            domain_data = doc.to_dict()
            domains.append(DomainResponse(
                id=doc.id,
                domain=domain_data['domain'],
                is_primary=domain_data.get('is_primary', False),
                created_at=domain_data['created_at']
            ))
        
        return domains
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get domains for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve domains")

@app.delete("/api/v1/admin/clients/{client_id}/domains/{domain}")
async def remove_domain(client_id: str, domain: str):
    """Remove domain from client"""
    try:
        user_client_id = get_current_user_client_id()
        
        # Check authorization
        require_owner_access(user_client_id, client_id)
        
        domain = domain.lower().strip()
        
        # Check if domain exists and belongs to this client
        domain_doc = firestore_client.domain_index_ref.document(domain).get()
        if not domain_doc.exists:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        domain_data = domain_doc.to_dict()
        if domain_data['client_id'] != client_id:
            raise HTTPException(status_code=400, detail="Domain does not belong to this client")
        
        # Remove from domain index
        firestore_client.domain_index_ref.document(domain).delete()
        
        # Remove detailed domain document
        domain_doc_id = f"{client_id}_{domain.replace('.', '_')}"
        firestore_client.db.collection('domains').document(domain_doc_id).delete()
        
        # Log configuration change
        change_doc = {
            "client_id": client_id,
            "changed_by": user_client_id,
            "change_description": f"Domain removed: {domain}",
            "old_config": {"domain": domain, "is_primary": domain_data.get('is_primary', False)},
            "new_config": None,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        firestore_client.config_changes_ref.add(change_doc)
        
        logger.info(f"Removed domain {domain} from client {client_id}")
        return {"message": f"Domain {domain} removed from client {client_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove domain {domain} from client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove domain")

# ============================================================================
# Health Check & Status
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

# Serve React static files (for production deployment) - MOVE TO END
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