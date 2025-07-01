# backend/app/config.py
import os
from typing import Optional

class Settings:
    """Application configuration settings"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/pixel_management"
    )
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Evothesis Pixel Management"
    VERSION: str = "1.0.0"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Alternative frontend port
        "http://localhost",       # Production nginx
    ]
    
    # Authentication (Simple for MVP)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "change_me_in_production")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Default client configuration
    DEFAULT_PRIVACY_LEVEL: str = "standard"
    DEFAULT_BILLING_RATE: float = 0.01  # $0.01 per 1000 events
    
    # Feature flags
    ENABLE_AUDIT_LOG: bool = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
    
    class Config:
        case_sensitive = True

# Global settings instance
settings = Settings()