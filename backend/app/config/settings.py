"""
Environment configuration and settings for pixel management system.

Centralizes environment variable validation, CORS origin configuration,
and application settings management.
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)


def check_required_env_vars():
    """Simple validation for critical environment variables"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    required = ["GOOGLE_CLOUD_PROJECT"]
    
    # Additional requirements for non-development
    if environment != "development":
        required.extend(["COLLECTION_API_URL", "ADMIN_API_KEY"])
    
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        raise ValueError(f"Required environment variables missing: {', '.join(missing)}")


def get_collection_api_url() -> str:
    """Get the collection API URL with environment-specific defaults"""
    collection_api_url = os.getenv("COLLECTION_API_URL")
    if not collection_api_url:
        # Default to localhost for development only
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment == "development":
            collection_api_url = "http://localhost:8001/collect"
            logger.warning("Using default localhost COLLECTION_API_URL for development")
        else:
            logger.error("COLLECTION_API_URL environment variable is required for non-development environments")
            raise ValueError("COLLECTION_API_URL environment variable must be set for production/staging")
    
    return collection_api_url


def get_cors_origins() -> List[str]:
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


class Settings:
    """Application settings container"""
    
    def __init__(self):
        # Validate environment variables at initialization
        check_required_env_vars()
        
        # Core configuration
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.admin_api_key = os.getenv("ADMIN_API_KEY")
        
        # API configuration
        self.collection_api_url = get_collection_api_url()
        self.cors_origins = get_cors_origins()
        
        # Static file configuration
        self.static_dir = "/app/static"
        self.static_files_enabled = os.path.exists(self.static_dir)


# Global settings instance
settings = Settings()