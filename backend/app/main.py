"""
FastAPI main application for pixel management system.

This is the core REST API server that provides client management, domain authorization,
and dynamic JavaScript pixel generation. The application serves both API endpoints for
admin operations and public endpoints for pixel tracking infrastructure.

Key functionality:
- Client CRUD operations with privacy compliance (GDPR, HIPAA, standard)
- Domain authorization and management with global indexing
- Dynamic JavaScript pixel generation with domain validation
- Health monitoring and configuration endpoints
- Static file serving for production React frontend
- Comprehensive CORS and rate limiting middleware

API structure:
- /health: Health check endpoint
- /api/v1/config/*: Public configuration endpoints for tracking VMs
- /pixel/*: Dynamic JavaScript tracking pixel generation
- /api/v1/admin/*: Protected admin endpoints requiring API key authentication

The application supports both development (with React dev server) and production
(serving static files) deployment modes.
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging
from datetime import datetime
from google.cloud import firestore
import os

from .firestore_client import firestore_client
from .models import ClientDocument, DomainDocument, DomainIndexDocument  
from .schemas import (
    ClientCreate, ClientUpdate, ClientResponse, 
    DomainCreate, DomainResponse, ClientConfigResponse
)
from .auth import verify_admin_access, log_admin_action
from .rate_limiter import RateLimitMiddleware
from .pixel_serving import serve_pixel

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SecurePixel Management", version="1.0.0")

# ============================================================================
# Environment Configuration
# ============================================================================

# Collection endpoint configuration
COLLECTION_API_URL = os.getenv(
    "COLLECTION_API_URL", 
    "http://localhost:8001/collect"  # Default to local server-infrastructure
)

# Secure CORS configuration - environment-based origins
def get_cors_origins():
    """Get CORS origins from environment with secure defaults"""
    # Production origins from environment
    cors_origins_env = os.getenv("CORS_ORIGINS", "")
    production_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    
    # Development origins
    dev_origins = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8001",
        "http://localhost"
    ]
    
    # Use production origins if configured, otherwise dev origins
    if production_origins:
        allowed_origins = production_origins
        logger.info(f"Using production CORS origins: {len(allowed_origins)} domains")
    else:
        allowed_origins = dev_origins
        logger.warning("Using development CORS origins - set CORS_ORIGINS for production")
    
    return allowed_origins

# Configure CORS with specific origins instead of wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)
app.add_middleware(RateLimitMiddleware)

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
                    "name": "SecurePixel Admin",
                    "email": "admin@securepixel.com",
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
# Health Check (Public)
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check with database connectivity test"""
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
# Configuration API (Public - for Tracking VMs)
# ============================================================================

@app.get("/api/v1/config/domain/{domain}", response_model=ClientConfigResponse)
async def get_config_by_domain(domain: str):
    """
    CRITICAL: Domain authorization endpoint for tracking infrastructure
    This endpoint validates domain authorization and returns client configuration
    """
    try:
        # Validate domain format
        if not domain or len(domain) < 3:
            raise HTTPException(status_code=400, detail="Invalid domain format")
        
        # Lookup domain in domain_index
        domain_docs = list(
            firestore_client.domain_index_ref
            .where('domain', '==', domain.lower())
            .limit(1)
            .stream()
        )
        
        if not domain_docs:
            logger.warning(f"Domain {domain} not authorized")
            raise HTTPException(status_code=404, detail="Domain not authorized")
        
        domain_data = domain_docs[0].to_dict()
        client_id = domain_data['client_id']
        
        # Get client configuration
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            logger.error(f"Client {client_id} not found for authorized domain {domain}")
            raise HTTPException(status_code=500, detail="Client configuration error")
        
        client_data = client_doc.to_dict()
        
        # Build configuration response
        config = ClientConfigResponse(
            client_id=client_id,
            privacy_level=client_data['privacy_level'],
            ip_collection={
                "enabled": client_data.get('ip_collection_enabled', True),
                "hash_required": client_data['privacy_level'] in ['gdpr', 'hipaa'],
                "salt": client_data.get('ip_salt')
            },
            consent={
                "required": client_data.get('consent_required', False),
                "default_behavior": "opt_out" if client_data['privacy_level'] == 'gdpr' else "allow"
            },
            features=client_data.get('features', {}),
            deployment={
                "type": client_data.get('deployment_type', 'shared'),
                "hostname": client_data.get('vm_hostname')
            }
        )
        
        logger.info(f"Served config for domain {domain} -> client {client_id}")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain config lookup failed for {domain}: {e}")
        raise HTTPException(status_code=500, detail="Configuration service error")

@app.get("/api/v1/config/client/{client_id}", response_model=ClientConfigResponse)
async def get_config_by_client_id(client_id: str):
    """Get client configuration by client_id (for tracking VMs)"""
    try:
        # Validate client_id format
        if not client_id or len(client_id) < 3:
            raise HTTPException(status_code=400, detail="Invalid client_id format")
        
        # Get client configuration
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            logger.warning(f"Client {client_id} not found")
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = client_doc.to_dict()
        
        # Build configuration response
        config = ClientConfigResponse(
            client_id=client_id,
            privacy_level=client_data['privacy_level'],
            ip_collection={
                "enabled": client_data.get('ip_collection_enabled', True),
                "hash_required": client_data['privacy_level'] in ['gdpr', 'hipaa'],
                "salt": client_data.get('ip_salt')
            },
            consent={
                "required": client_data.get('consent_required', False),
                "default_behavior": "opt_out" if client_data['privacy_level'] == 'gdpr' else "allow"
            },
            features=client_data.get('features', {}),
            deployment={
                "type": client_data.get('deployment_type', 'shared'),
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

@app.get("/api/v1/domains/all")
async def list_all_domains():
    """Get all authorized domains across all clients for CORS configuration"""
    try:
        # Get all domains from domain_index
        domain_docs = list(firestore_client.domain_index_ref.stream())
        
        domains = []
        for doc in domain_docs:
            domain_data = doc.to_dict()
            domains.append(domain_data['domain'])
        
        logger.info(f"Served {len(domains)} domains for CORS configuration")
        return {"domains": domains, "count": len(domains)}
        
    except Exception as e:
        logger.error(f"Failed to get all domains: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve domains")


# ============================================================================
# Pixel Serving (Dynamic JavaScript Generation)
# ============================================================================

@app.get("/pixel/{client_id}/tracking.js")
async def serve_pixel_js(
    request: Request,
    client_id: str = Path(..., regex=r'^[a-zA-Z0-9_-]+$', max_length=100)
):
    """
    Serve client-specific tracking JavaScript with domain authorization
    
    SECURITY: Validates requesting domain is authorized for specified client_id
    PERFORMANCE: Template caching with 5-minute browser cache
    """
    return await serve_pixel(request, client_id, COLLECTION_API_URL)

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

@app.post("/api/v1/admin/clients", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    api_key_id: str = Depends(verify_admin_access)
):
    """Create new client - REQUIRES ADMIN AUTH"""
    try:
        # Generate unique client_id
        import uuid
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
            import secrets
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

@app.get("/api/v1/admin/clients/{client_id}", response_model=ClientResponse)
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

@app.put("/api/v1/admin/clients/{client_id}", response_model=ClientResponse)
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

# ============================================================================
# SECURED ADMIN API: Domain Management (AUTHENTICATION REQUIRED)
# ============================================================================

@app.post("/api/v1/admin/clients/{client_id}/domains", response_model=DomainResponse)
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

@app.get("/api/v1/admin/clients/{client_id}/domains", response_model=List[DomainResponse])
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

@app.delete("/api/v1/admin/clients/{client_id}/domains/{domain}")
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