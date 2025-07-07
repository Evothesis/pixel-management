# backend/app/auth_middleware.py
import base64
import os
import secrets
from typing import Optional
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import Response as FastAPIResponse
import logging

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