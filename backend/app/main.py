# backend/app/main.py
from fastapi import FastAPI, HTTPException
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
from .auth import get_current_user_client_id, require_owner_access, require_owner_or_self_access

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Evothesis Pixel Management", version="1.0.0")

# CORS middleware
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
            logger.info("Created default Evothesis admin client")
        else:
            logger.info("Default admin client already exists")
            
    except Exception as e:
        logger.error(f"Failed to create default admin client: {e}")

# ============================================================================
# CRITICAL: Configuration API for Tracking VMs
# ============================================================================

@app.get("/api/v1/config/domain/{domain}", response_model=ClientConfigResponse)
async def get_config_by_domain(domain: str):
    """
    CRITICAL: Domain authorization for tracking VMs
    This endpoint must be sub-100ms for production performance
    """
    try:
        # O(1) lookup in domain index
        domain_doc = firestore_client.domain_index_ref.document(domain).get()
        
        if not domain_doc.exists:
            logger.warning(f"Unauthorized domain access attempt: {domain}")
            raise HTTPException(
                status_code=404, 
                detail=f"Domain {domain} not authorized for tracking"
            )
        
        domain_data = domain_doc.to_dict()
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
        
        # Build configuration response (same format as SQLAlchemy version)
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Evothesis Pixel Management",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "api_docs": "/docs",
            "config_by_domain": "/api/v1/config/domain/{domain}",
            "config_by_client": "/api/v1/config/client/{client_id}",
            "admin_clients": "/api/v1/admin/clients"
        }
    }