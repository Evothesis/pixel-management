# backend/app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class ClientCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    deployment_type: str = "shared"
    vm_hostname: Optional[str] = None
    privacy_level: str = "standard"
    ip_collection_enabled: bool = True
    features: Optional[Dict[str, Any]] = {}
    monthly_event_limit: Optional[int] = None
    billing_rate_per_1k: float = 0.01

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    deployment_type: Optional[str] = None
    vm_hostname: Optional[str] = None
    privacy_level: Optional[str] = None
    ip_collection_enabled: Optional[bool] = None
    features: Optional[Dict[str, Any]] = None
    monthly_event_limit: Optional[int] = None
    billing_rate_per_1k: Optional[float] = None
    is_active: Optional[bool] = None

class ClientResponse(BaseModel):
    client_id: str
    name: str
    email: Optional[str]
    deployment_type: str
    vm_hostname: Optional[str]
    privacy_level: str
    ip_collection_enabled: bool
    consent_required: bool
    features: Dict[str, Any]
    monthly_event_limit: Optional[int]
    billing_rate_per_1k: float
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class DomainCreate(BaseModel):
    domain: str
    is_primary: bool = False

class DomainResponse(BaseModel):
    id: int
    client_id: str
    domain: str
    is_primary: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
