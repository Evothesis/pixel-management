"""
Pydantic schemas for API request/response validation and serialization.

This module defines the input/output data structures for all REST API endpoints
in the pixel management system. It provides request validation, response
formatting, and automatic API documentation generation through FastAPI integration.

Schema categories:
- Client schemas: ClientCreate, ClientUpdate, ClientResponse for client management
- Domain schemas: DomainCreate, DomainResponse for domain authorization
- Configuration schemas: ClientConfigResponse for tracking VM configuration
- System schemas: Health check and status response formats

All schemas include comprehensive validation rules, type safety, and automatic
OpenAPI documentation generation. They serve as the contract between frontend
clients and the backend API, ensuring data consistency and proper error handling.
"""

# backend/app/schemas.py - API request/response schemas
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

# Domain schemas
class DomainBase(BaseModel):
    domain: str
    is_primary: bool = False

class DomainCreate(DomainBase):
    @validator('domain')
    def validate_domain(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Domain must be at least 3 characters')
        return v.lower().strip()

class DomainResponse(DomainBase):
    id: str                                 # Firestore document ID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Client schemas
class ClientBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    client_type: str = "end_client"

class ClientCreate(ClientBase):
    owner: str                              # Required - who controls this client
    billing_entity: Optional[str] = None    # Optional - defaults to owner
    deployment_type: str = "shared"
    privacy_level: str = "standard"
    vm_hostname: Optional[str] = None
    features: Dict[str, Any] = {}
    
    @validator('privacy_level')
    def validate_privacy_level(cls, v):
        if v not in ['standard', 'gdpr', 'hipaa']:
            raise ValueError('Privacy level must be standard, gdpr, or hipaa')
        return v
    
    @validator('deployment_type')
    def validate_deployment_type(cls, v):
        if v not in ['shared', 'dedicated']:
            raise ValueError('Deployment type must be shared or dedicated')
        return v
    
    @validator('client_type')
    def validate_client_type(cls, v):
        if v not in ['end_client', 'agency', 'enterprise', 'admin']:
            raise ValueError('Client type must be end_client, agency, enterprise, or admin')
        return v

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    billing_entity: Optional[str] = None     # Can change who pays
    privacy_level: Optional[str] = None
    ip_collection_enabled: Optional[bool] = None
    consent_required: Optional[bool] = None
    features: Optional[Dict[str, Any]] = None
    deployment_type: Optional[str] = None
    vm_hostname: Optional[str] = None
    is_active: Optional[bool] = None

class ClientResponse(ClientBase):
    client_id: str
    owner: str
    billing_entity: str
    privacy_level: str
    ip_collection_enabled: bool
    consent_required: bool
    features: Dict[str, Any]
    deployment_type: str
    vm_hostname: Optional[str] = None
    billing_rate_per_1k: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    domain_count: int = 0                   # Count of domains for this client
    
    class Config:
        from_attributes = True

# Configuration response for tracking VMs
class ClientConfigResponse(BaseModel):
    client_id: str
    privacy_level: str
    ip_collection: Dict[str, Any]           # {enabled, hash_required, salt}
    consent: Dict[str, Any]                 # {required, default_behavior}
    features: Dict[str, Any]
    deployment: Dict[str, Any]              # {type, hostname}

# Health check response
class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    timestamp: str
    error: Optional[str] = None