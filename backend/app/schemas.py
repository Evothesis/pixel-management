# backend/app/schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import secrets
import string

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
    owner: str                              # Who controls this client
    billing_entity: str                     # Who pays for this client
    privacy_level: str
    ip_collection_enabled: bool
    consent_required: bool
    features: Dict[str, Any]
    deployment_type: str
    vm_hostname: Optional[str]
    billing_rate_per_1k: float
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    domain_count: int = 0                   # Computed field for convenience

# Configuration schemas (for tracking VMs)
class ClientConfigResponse(BaseModel):
    """Configuration response for tracking infrastructure"""
    client_id: str
    privacy_level: str
    ip_collection: Dict[str, Any]
    consent: Dict[str, Any]
    features: Dict[str, Any]
    deployment: Dict[str, Any]

# Configuration change tracking
class ConfigurationChangeResponse(BaseModel):
    id: str
    client_id: str
    changed_by: str
    change_description: str
    old_config: Optional[Dict[str, Any]]
    new_config: Optional[Dict[str, Any]]
    timestamp: datetime

# API Key schemas
class APIKeyBase(BaseModel):
    name: str
    permissions: List[str] = ["config:read"]  # Default permission for service-to-service
    expires_at: Optional[datetime] = None

class APIKeyCreate(APIKeyBase):
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('API key name must be at least 3 characters')
        if len(v.strip()) > 50:
            raise ValueError('API key name must be less than 50 characters')
        return v.strip()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = ["config:read", "admin:write"]
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f'Invalid permission: {permission}. Valid permissions: {valid_permissions}')
        return v
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Expiration date must be in the future')
        return v

class APIKeyResponse(APIKeyBase):
    id: str
    key_preview: str  # First 8 chars + "..." for display
    created_at: datetime
    created_by: str  # client_id that created this key
    is_active: bool
    last_used_at: Optional[datetime] = None

class APIKeyCreateResponse(BaseModel):
    """Response when creating a new API key - includes the actual key"""
    id: str
    name: str
    api_key: str  # The actual key - only shown once!
    key_preview: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    message: str = "Store this API key securely - it will not be shown again"

# Internal model for database storage
class APIKeyDocument(BaseModel):
    """Internal model for storing API keys in Firestore"""
    id: str
    name: str
    key_hash: str  # Hashed version using bcrypt
    permissions: List[str]
    created_at: datetime
    created_by: str  # client_id that created this key
    expires_at: Optional[datetime]
    is_active: bool
    last_used_at: Optional[datetime]
    usage_count: int = 0