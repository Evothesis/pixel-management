# backend/app/auth.py
from fastapi import HTTPException
from typing import Optional, Dict, Any
import logging

from .firestore_client import firestore_client

logger = logging.getLogger(__name__)

def get_current_user_client_id() -> str:
    """Get current user's client ID - MVP implementation"""
    # For MVP, return default admin client
    # TODO: Implement proper JWT authentication from headers
    return "client_evothesis_admin"

def require_owner_access(user_client_id: str, target_client_id: str) -> Dict[str, Any]:
    """Ensure user can admin the target client"""
    try:
        target_doc = firestore_client.clients_ref.document(target_client_id).get()
        
        if not target_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        target_data = target_doc.to_dict()
        
        # Check if user is the owner OR the client themselves
        if target_data['owner'] != user_client_id and user_client_id != target_client_id:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: Only the client owner can modify this client"
            )
        
        return target_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authorization check failed: {e}")
        raise HTTPException(status_code=500, detail="Authorization service error")

def require_owner_or_self_access(user_client_id: str, target_client_id: str) -> Dict[str, Any]:
    """Ensure user can view the target client (owner or self)"""
    try:
        target_doc = firestore_client.clients_ref.document(target_client_id).get()
        
        if not target_doc.exists:
            raise HTTPException(status_code=404, detail="Client not found")
        
        target_data = target_doc.to_dict()
        
        # Check if user is the owner OR the client themselves  
        if target_data['owner'] != user_client_id and user_client_id != target_client_id:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: Only the client owner or the client themselves can view this data"
            )
        
        return target_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authorization check failed: {e}")
        raise HTTPException(status_code=500, detail="Authorization service error")