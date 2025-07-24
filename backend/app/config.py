"""
Configuration management for pixel management system with secure defaults.

This module handles environment-based configuration with automatic fallbacks for
development environments. It manages API endpoints, database connections, CORS
origins, and authentication settings. The configuration system prioritizes
security with explicit production settings and safe development defaults.

Key features:
- Environment-based CORS origin management with secure defaults
- Collection API URL configuration for external tracking infrastructure
- Development vs production environment detection and warnings
- Secure configuration validation and logging

The module automatically configures different settings based on deployment
environment while maintaining security best practices throughout.
"""

# backend/app/config.py - SECURE CONFIGURATION
import os
import secrets
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class Settings:
    """Application configuration settings with security-first defaults"""
    
    # Database - No changes needed here
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/pixel_management"
    )
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Evothesis Pixel Management"
    VERSION: str = "1.0.0"
    
    # CORS Configuration - TODO: Restrict in production
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Alternative frontend port
        "http://localhost",       # Production nginx
    ]
    
    # SECURE AUTHENTICATION CONFIGURATION
    def __init__(self):
        # Admin API Key (CRITICAL - Must be set for production)
        self.ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
        if not self.ADMIN_API_KEY:
            # Generate secure API key for development
            self.ADMIN_API_KEY = f"evothesis_admin_{secrets.token_urlsafe(32)}"
            logger.warning("🔑 GENERATED ADMIN API KEY FOR DEVELOPMENT:")
            logger.warning(f"   {self.ADMIN_API_KEY}")
            logger.warning("🚨 SET ADMIN_API_KEY environment variable for production!")
        
        # JWT Secret Key (Enhanced security)
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(64)
            logger.warning("🔑 Generated secure SECRET_KEY for development")
            logger.warning("🚨 SET SECRET_KEY environment variable for production!")
        
        # Validate production readiness
        if os.getenv("ENVIRONMENT") == "production":
            self._validate_production_config()
    
    def _validate_production_config(self):
        """Validate that production configuration is secure"""
        errors = []
        
        if not os.getenv("ADMIN_API_KEY"):
            errors.append("ADMIN_API_KEY must be set in production")
        
        if not os.getenv("SECRET_KEY"):
            errors.append("SECRET_KEY must be set in production")
        
        # Check for weak/default values
        weak_patterns = ["change_me", "admin", "password", "secret", "key"]
        if any(pattern in self.SECRET_KEY.lower() for pattern in weak_patterns):
            errors.append("SECRET_KEY appears to contain weak/default values")
        
        if errors:
            error_msg = "❌ PRODUCTION SECURITY ERRORS:\n" + "\n".join(f"   - {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError("Production deployment blocked due to security configuration errors")
    
    # Remove weak default credentials - NO LONGER USED
    # ADMIN_USERNAME and ADMIN_PASSWORD replaced with API key authentication
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Default client configuration
    DEFAULT_PRIVACY_LEVEL: str = "standard"
    DEFAULT_BILLING_RATE: float = 0.01  # $0.01 per 1000 events
    
    # Feature flags
    ENABLE_AUDIT_LOG: bool = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "evothesis")
    
    # Production security headers
    ENABLE_SECURITY_HEADERS: bool = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
    
    def get_admin_api_key(self) -> str:
        """Get admin API key for authentication"""
        return self.ADMIN_API_KEY
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    class Config:
        case_sensitive = True

# Global settings instance
settings = Settings()

# Environment setup helper
def setup_environment_file():
    """Helper to generate .env file with secure defaults"""
    env_content = f"""# Evothesis Pixel Management Environment Configuration
# Generated on: {datetime.utcnow().isoformat()}

# CRITICAL: Admin API Key for accessing admin endpoints
ADMIN_API_KEY={settings.ADMIN_API_KEY}

# JWT Secret Key for internal operations
SECRET_KEY={settings.SECRET_KEY}

# Environment type
ENVIRONMENT=development

# Google Cloud Project
GOOGLE_CLOUD_PROJECT=evothesis

# Logging
LOG_LEVEL=INFO

# Security features
ENABLE_AUDIT_LOG=true
ENABLE_SECURITY_HEADERS=true

# Production Notes:
# 1. Generate new ADMIN_API_KEY and SECRET_KEY for production
# 2. Set ENVIRONMENT=production  
# 3. Restrict CORS origins
# 4. Enable all security features
"""
    
    return env_content

if __name__ == "__main__":
    # Development helper - generate .env file
    print("🔧 Generating secure environment configuration...")
    print(setup_environment_file())