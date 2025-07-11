# backend/app/auth.py - COMPLETE REPLACEMENT
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import secrets
import hashlib
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Security scheme for FastAPI docs
security = HTTPBearer()

class AdminAuthenticator:
    """Simple, secure API key authentication for admin endpoints"""
    
    def __init__(self):
        # Get admin API key from environment with secure fallback
        self.admin_api_key = os.getenv("ADMIN_API_KEY")
        
        if not self.admin_api_key:
            # Generate secure API key if not provided
            self.admin_api_key = self._generate_secure_api_key()
            logger.warning(f"Generated admin key: ...{self.admin_api_key[-8:]}")
            logger.warning("Set ADMIN_API_KEY environment variable for production!")
        
        # Hash the API key for secure comparison
        self.api_key_hash = hashlib.sha256(self.admin_api_key.encode()).hexdigest()
        
    def _generate_secure_api_key(self) -> str:
        """Generate a cryptographically secure API key"""
        return f"evothesis_admin_{secrets.token_urlsafe(32)}"
    
    def verify_api_key(self, provided_key: str) -> bool:
        """Verify provided API key against stored hash"""
        try:
            provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
            return secrets.compare_digest(self.api_key_hash, provided_hash)
        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            return False
    
    def get_api_key_id(self, api_key: str) -> str:
        """Get identifier for API key (for audit logging)"""
        # Return last 8 characters for audit trails
        return f"admin_key_...{api_key[-8:]}" if len(api_key) >= 8 else "admin_key_short"

# Global authenticator instance
admin_auth = AdminAuthenticator()

async def verify_admin_access(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to verify admin API key
    Returns API key identifier for audit logging
    """
    if not credentials:
        logger.warning("Admin endpoint accessed without credentials")
        raise HTTPException(
            status_code=401,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not admin_auth.verify_api_key(credentials.credentials):
        logger.warning(f"Invalid API key used for admin access: ...{credentials.credentials[-8:]}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Return API key identifier for audit logging
    api_key_id = admin_auth.get_api_key_id(credentials.credentials)
    logger.info(f"Admin access granted to {api_key_id}")
    return api_key_id

def log_admin_action(action: str, client_id: Optional[str], api_key_id: str, details: Optional[str] = None):
    """Log admin actions for audit trail"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "api_key_id": api_key_id,
        "client_id": client_id,
        "details": details
    }
    
    logger.info(f"ADMIN_AUDIT: {log_entry}")