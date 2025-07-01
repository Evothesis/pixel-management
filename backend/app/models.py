# backend/app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    
    # Infrastructure configuration
    deployment_type = Column(String(20), default="shared", nullable=False)  # shared, dedicated
    vm_hostname = Column(String(255), nullable=True)
    
    # Privacy & compliance configuration
    privacy_level = Column(String(20), default="standard", nullable=False)  # standard, gdpr, hipaa
    ip_collection_enabled = Column(Boolean, default=True, nullable=False)
    ip_salt = Column(String(128), nullable=True)  # Per-client salt for hashing
    consent_required = Column(Boolean, default=False, nullable=False)
    
    # Tracking feature configuration (stored as JSON)
    features = Column(JSONB, default={}, nullable=False)
    
    # Billing configuration
    monthly_event_limit = Column(Integer, nullable=True)
    billing_rate_per_1k = Column(Numeric(6, 4), default=0.01, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tracking_domains = relationship("TrackingDomain", back_populates="client", cascade="all, delete-orphan")
    configuration_changes = relationship("ConfigurationChange", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Client(client_id='{self.client_id}', name='{self.name}', privacy_level='{self.privacy_level}')>"

class TrackingDomain(Base):
    __tablename__ = "tracking_domains"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(50), ForeignKey("clients.client_id", ondelete="CASCADE"), nullable=False)
    domain = Column(String(255), nullable=False, unique=True, index=True)  # Each domain can only belong to one client
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    client = relationship("Client", back_populates="tracking_domains")
    
    def __repr__(self):
        return f"<TrackingDomain(domain='{self.domain}', client_id='{self.client_id}')>"

class ConfigurationChange(Base):
    __tablename__ = "configuration_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(50), ForeignKey("clients.client_id", ondelete="CASCADE"), nullable=False)
    changed_by = Column(String(100), nullable=False)  # Admin user (simple string for MVP)
    change_description = Column(Text, nullable=False)
    old_config = Column(JSONB, nullable=True)
    new_config = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    client = relationship("Client", back_populates="configuration_changes")
    
    def __repr__(self):
        return f"<ConfigurationChange(client_id='{self.client_id}', changed_by='{self.changed_by}', timestamp='{self.timestamp}')>"