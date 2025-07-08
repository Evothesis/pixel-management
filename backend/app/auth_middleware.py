# backend/app/auth_middleware.py
import base64
import os
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Response, status, Depends
from fastapi.responses import Response as FastAPIResponse
import logging
from .firestore_client import firestore_client

logger = logging.getLogger(__name__)

class BasicAuthMiddleware:
    """HTTP Basic Authentication middleware for immediate production protection"""
    
    def __init__(self):
        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not self.admin_password:
            # In production, generate a temporary password and log it
            # This handles the case where Cloud Run console vars aren't set yet
            self.admin_password = secrets.token_urlsafe(16)
            logger.warning("="*60)
            logger.warning("🔒 ADMIN_PASSWORD not set in environment variables")
            logger.warning(f"🔑 Temporary password generated: {self.admin_password}")
            logger.warning("⚠️  Configure ADMIN_PASSWORD in Cloud Run console:")
            logger.warning("   1. Go to Cloud Run console")
            logger.warning("   2. Edit & Deploy New Revision")
            logger.warning("   3. Set environment variables:")
            logger.warning("      ADMIN_USERNAME=admin")
            logger.warning("      ADMIN_PASSWORD=YourSecurePassword")
            logger.warning("="*60)
        else:
            logger.info(f"✅ Basic auth configured for user: {self.admin_username}")
        
        # Always log the current auth status for debugging
        logger.info(f"🔐 Authentication status: username={self.admin_username}, password_set={bool(self.admin_password)}")
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """Verify basic auth credentials"""
        return (
            secrets.compare_digest(username, self.admin_username) and
            secrets.compare_digest(password, self.admin_password)
        )
    
    def get_credentials_from_header(self, authorization: Optional[str]) -> Optional[tuple[str, str]]:
        """Extract credentials from Authorization header"""
        if not authorization:
            return None
        
        try:
            scheme, credentials = authorization.split(' ', 1)
            if scheme.lower() != 'basic':
                return None
            
            decoded = base64.b64decode(credentials).decode('utf-8')
            username, password = decoded.split(':', 1)
            return username, password
        except (ValueError, UnicodeDecodeError):
            return None
    
    async def __call__(self, request: Request, call_next):
        """Middleware to check basic auth on all requests"""
        
        # Skip auth check for health endpoint (needed for Cloud Run)
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get authorization header
        authorization = request.headers.get("Authorization")
        credentials = self.get_credentials_from_header(authorization)
        
        if not credentials:
            return self._require_auth()
        
        username, password = credentials
        if not self.verify_credentials(username, password):
            logger.warning(f"Failed login attempt for user: {username}")
            return self._require_auth()
        
        # Auth successful, proceed with request
        return await call_next(request)
    
    def _require_auth(self):
        """Return 401 with Basic Auth challenge"""
        return FastAPIResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Authentication required",
            headers={"WWW-Authenticate": "Basic realm=\"Pixel Management Admin\""}
        )

# backend/app/auth_middleware.py - ADD APIKeyMiddleware CLASS TO EXISTING FILE

# ADD these imports to the existing imports at the top
from fastapi import Depends
from .firestore_client import firestore_client
from typing import Dict, Any

# ADD this new class to the existing auth_middleware.py file

class APIKeyMiddleware:
    """API Key authentication middleware for service-to-service communication"""
    
    def __init__(self):
        self.firestore_client = firestore_client
        logger.info("🔑 API Key middleware initialized")
    
    async def authenticate_api_key(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Authenticate API key from X-API-Key header
        Returns API key data if valid, None if invalid
        """
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            logger.warning(f"Missing X-API-Key header for {request.url.path}")
            return None
        
        # Validate API key
        try:
            key_data = self.firestore_client.validate_api_key(api_key)
            if key_data:
                logger.info(f"Valid API key {key_data['id']} used for {request.url.path}")
                return key_data
            else:
                logger.warning(f"Invalid API key for {request.url.path}")
                return None
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    async def require_api_key(self, request: Request) -> Dict[str, Any]:
        """
        Dependency function to require API key authentication
        Raises HTTPException if no valid API key
        """
        key_data = await self.authenticate_api_key(request)
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Valid API key required",
                headers={"WWW-Authenticate": "X-API-Key"}
            )
        return key_data
    
    def check_permission(self, key_data: Dict[str, Any], required_permission: str) -> bool:
        """Check if API key has required permission"""
        return required_permission in key_data.get('permissions', [])
    
    async def require_permission(self, request: Request, permission: str) -> Dict[str, Any]:
        """
        Dependency function to require specific permission
        """
        key_data = await self.require_api_key(request)
        
        if not self.check_permission(key_data, permission):
            logger.warning(f"API key {key_data['id']} lacks permission '{permission}' for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return key_data

# Create global instance for dependency injection
api_key_middleware = APIKeyMiddleware()

# Dependency functions for FastAPI routes
async def require_config_read_permission(request: Request) -> Dict[str, Any]:
    """Require config:read permission for configuration endpoints"""
    return await api_key_middleware.require_permission(request, "config:read")