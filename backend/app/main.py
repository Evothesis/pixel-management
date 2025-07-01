from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import secrets
import hashlib
from datetime import datetime

from .database import get_db, engine
from .models import Base, Client, TrackingDomain, ConfigurationChange
from .schemas import ClientCreate, ClientUpdate, ClientResponse, DomainCreate

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Evothesis Pixel Management", version="1.0.0")

# Simple CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Configuration API for Tracking VMs (Most Important)
# ============================================================================

@app.get("/api/v1/config/client/{client_id}")
async def get_client_config(client_id: str, db: Session = Depends(get_db)):
    """Get client configuration for tracking VMs"""
    client = db.query(Client).filter(Client.client_id == client_id, Client.is_active == True).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found or inactive")
    
    # Generate config for tracking VMs
    config = {
        "client_id": client.client_id,
        "privacy_level": client.privacy_level,
        "ip_collection": {
            "enabled": client.ip_collection_enabled,
            "hash_required": client.privacy_level in ["gdpr", "hipaa"],
            "salt": client.ip_salt if client.privacy_level in ["gdpr", "hipaa"] else None
        },
        "consent": {
            "required": client.consent_required,
            "default_behavior": "block" if client.privacy_level in ["gdpr", "hipaa"] else "allow"
        },
        "features": client.features or {},
        "deployment": {
            "type": client.deployment_type,
            "hostname": client.vm_hostname
        }
    }
    
    return config

@app.get("/api/v1/config/domain/{domain}")
async def get_config_by_domain(domain: str, db: Session = Depends(get_db)):
    """Get client config by domain - critical for domain validation"""
    tracking_domain = db.query(TrackingDomain).filter(TrackingDomain.domain == domain).first()
    
    if not tracking_domain:
        raise HTTPException(status_code=404, detail=f"Domain {domain} not authorized for tracking")
    
    # Get client config
    client = db.query(Client).filter(
        Client.client_id == tracking_domain.client_id, 
        Client.is_active == True
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found or inactive")
    
    # Return same config format as above
    return await get_client_config(client.client_id, db)

# ============================================================================
# Admin API for Client Management
# ============================================================================

@app.post("/api/v1/admin/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    """Create new client"""
    
    # Generate unique client_id
    client_id = f"client_{secrets.token_hex(8)}"
    
    # Generate salt for GDPR/HIPAA clients
    ip_salt = None
    if client_data.privacy_level in ["gdpr", "hipaa"]:
        ip_salt = secrets.token_hex(32)
    
    # Create client
    client = Client(
        client_id=client_id,
        name=client_data.name,
        email=client_data.email,
        deployment_type=client_data.deployment_type,
        vm_hostname=client_data.vm_hostname,
        privacy_level=client_data.privacy_level,
        ip_collection_enabled=client_data.ip_collection_enabled,
        ip_salt=ip_salt,
        consent_required=client_data.privacy_level in ["gdpr", "hipaa"],
        features=client_data.features or {},
        monthly_event_limit=client_data.monthly_event_limit,
        billing_rate_per_1k=client_data.billing_rate_per_1k
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    # Log creation
    change = ConfigurationChange(
        client_id=client_id,
        changed_by="admin",  # Simple for MVP
        change_description=f"Client created with privacy level: {client_data.privacy_level}",
        new_config={"privacy_level": client_data.privacy_level, "created": True}
    )
    db.add(change)
    db.commit()
    
    return client

@app.get("/api/v1/admin/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, db: Session = Depends(get_db)):
    """Get client details"""
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.get("/api/v1/admin/clients", response_model=List[ClientResponse])
async def list_clients(db: Session = Depends(get_db)):
    """List all clients"""
    return db.query(Client).order_by(Client.created_at.desc()).all()

@app.post("/api/v1/admin/clients/{client_id}/domains")
async def add_domain(client_id: str, domain_data: DomainCreate, db: Session = Depends(get_db)):
    """Add domain to client"""
    
    # Check if client exists
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check if domain already exists
    existing = db.query(TrackingDomain).filter(TrackingDomain.domain == domain_data.domain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domain already assigned to a client")
    
    # Add domain
    domain = TrackingDomain(
        client_id=client_id,
        domain=domain_data.domain,
        is_primary=domain_data.is_primary
    )
    
    db.add(domain)
    db.commit()
    
    return {"message": f"Domain {domain_data.domain} added to client {client_id}"}

@app.get("/api/v1/admin/clients/{client_id}/domains")
async def get_client_domains(client_id: str, db: Session = Depends(get_db)):
    """Get all domains for a client"""
    domains = db.query(TrackingDomain).filter(TrackingDomain.client_id == client_id).all()
    return domains

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pixel-management"}
