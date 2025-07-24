"""
Pydantic data models for Firestore document schemas in pixel management system.

This module defines the data structures for storing client, domain, and index
information in Google Firestore. All models include validation, type safety,
and automatic serialization for database operations.

Data models:
- ClientDocument: Complete client configuration with privacy settings
- DomainDocument: Domain registration and authorization data  
- DomainIndexDocument: Global domain-to-client mapping for fast lookups

Each model corresponds to a Firestore collection and includes all necessary
fields for privacy compliance, billing, deployment configuration, and audit
tracking. The models support multiple privacy levels (standard, GDPR, HIPAA)
and various deployment types (shared, dedicated).
"""

# backend/app/models.py - FIXED VERSION FOR IMMEDIATE DEPLOYMENT
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

class ClientDocument(BaseModel):
    """Client document model for Firestore"""
    client_id: str
    name: str
    email: Optional[EmailStr] = None
    
    # Owner and billing relationship
    owner: str                              # Who controls this client's data and config
    billing_entity: str                     # Who pays for this client's usage
    client_type: str = "end_client"         # "end_client", "agency", "enterprise", "admin"
    
    # Infrastructure configuration
    deployment_type: str = "shared"         # "shared", "dedicated"
    vm_hostname: Optional[str] = None
    
    # Privacy & compliance configuration  
    privacy_level: str = "standard"         # "standard", "gdpr", "hipaa"
    ip_collection_enabled: bool = True
    ip_salt: Optional[str] = None           # Generated salt for IP hashing
    consent_required: bool = False
    
    # Tracking features configuration
    features: Dict[str, Any] = {}
    
    # Billing configuration
    billing_rate_per_1k: float = 0.01       # $0.01 per 1000 events
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

class DomainDocument(BaseModel):
    """Domain document model for client subcollection"""
    domain: str
    is_primary: bool = False
    created_at: datetime

class DomainIndexDocument(BaseModel):
    """Domain index document for O(1) domain lookups"""
    client_id: str                          # Which client owns this domain
    domain: str                             # The domain name
    is_primary: bool = False                # Whether this is the primary domain
    created_at: datetime

class ConfigChangeDocument(BaseModel):
    """Configuration change audit log"""
    client_id: str
    changed_by: str                         # User/admin who made the change
    change_description: str
    old_config: Optional[Dict[str, Any]] = None
    new_config: Optional[Dict[str, Any]] = None
    timestamp: datetime

# For backward compatibility - these are the exact imports the main.py expects
__all__ = [
    'ClientDocument',
    'DomainDocument', 
    'DomainIndexDocument',
    'ConfigChangeDocument'
]