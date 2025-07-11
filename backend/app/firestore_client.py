# backend/app/firestore_client.py
import os
from google.cloud import firestore
from google.auth import credentials
from google.oauth2 import service_account
from typing import Optional, List, Dict, Any, Tuple
import secrets
import string
from datetime import datetime
import logging
import json
import bcrypt

logger = logging.getLogger(__name__)

class FirestoreClient:
    def __init__(self):
        """Initialize Firestore client with flexible authentication"""
        try:
            # Try different authentication methods
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'evothesis')
            
            # Method 1: Service account key file (if exists)
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                logger.info("Using service account key file authentication")
                self.db = firestore.Client(project=project_id)
            
            # Method 2: Default credentials (gcloud auth)
            else:
                logger.info("Using default credentials authentication")
                self.db = firestore.Client(project=project_id)
            
            # Initialize collection references (AFTER self.db is created)
            self.clients_ref = self.db.collection('clients')
            self.domain_index_ref = self.db.collection('domain_index')
            self.config_changes_ref = self.db.collection('configuration_changes')
            self.api_keys_ref = self.db.collection('api_keys')  # ADD THIS LINE
            
            logger.info(f"Firestore client initialized successfully for project: {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise
    
    def generate_client_id(self) -> str:
        """Generate a unique client ID"""
        return "client_" + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    
    def generate_ip_salt(self) -> str:
        """Generate a unique salt for IP hashing"""
        return secrets.token_hex(32)
    
    def test_connection(self) -> bool:
        """Test Firestore connectivity"""
        try:
            # Simple test - try to access a collection
            self.db.collection('_health_check').limit(1).get()
            return True
        except Exception as e:
            logger.error(f"Firestore connection test failed: {e}")
            return False
    
    # ADD THESE NEW API KEY METHODS:
    
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        # Format: evpx_<32 random chars>
        # evpx = Evothesis Pixel eXchange
        random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        return f"evpx_{random_part}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        # Use bcrypt for secure hashing
        salt = bcrypt.gensalt()
        key_hash = bcrypt.hashpw(api_key.encode('utf-8'), salt)
        return key_hash.decode('utf-8')
    
    def verify_api_key(self, api_key: str, key_hash: str) -> bool:
        """Verify an API key against its hash"""
        try:
            return bcrypt.checkpw(api_key.encode('utf-8'), key_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return False
    
    def create_api_key_preview(self, api_key: str) -> str:
        """Create a preview of the API key for display"""
        if len(api_key) < 12:
            return api_key[:4] + "..."
        return api_key[:8] + "..." + api_key[-4:]
    
    def create_api_key(self, name: str, permissions: List[str], created_by: str, 
                      expires_at: Optional[datetime] = None) -> Tuple[str, str]:
        """
        Create a new API key and store it in Firestore
        Returns: (api_key_id, actual_api_key)
        """
        try:
            # Generate API key and ID
            api_key = self.generate_api_key()
            api_key_id = "apikey_" + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
            
            # Hash the key for storage
            key_hash = self.hash_api_key(api_key)
            
            # Create document
            api_key_doc = {
                "id": api_key_id,
                "name": name,
                "key_hash": key_hash,
                "permissions": permissions,
                "created_at": firestore.SERVER_TIMESTAMP,
                "created_by": created_by,
                "expires_at": expires_at,
                "is_active": True,
                "last_used_at": None,
                "usage_count": 0
            }
            
            # Store in Firestore
            self.api_keys_ref.document(api_key_id).set(api_key_doc)
            
            logger.info(f"Created API key {api_key_id} for {created_by}")
            return api_key_id, api_key
            
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise
    
    def get_api_key(self, api_key_id: str) -> Optional[Dict[str, Any]]:
        """Get API key data by ID"""
        try:
            doc = self.api_keys_ref.document(api_key_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get API key {api_key_id}: {e}")
            return None
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return key data if valid
        Returns None if invalid or expired
        """
        try:
            # Get all active API keys and check against them
            # Note: In production, you might want to optimize this with indexing
            api_keys = self.api_keys_ref.where('is_active', '==', True).stream()
            
            for doc in api_keys:
                key_data = doc.to_dict()
                
                # Check if key matches
                if self.verify_api_key(api_key, key_data['key_hash']):
                    # Check if expired
                    if key_data.get('expires_at'):
                        if datetime.utcnow() > key_data['expires_at']:
                            logger.warning(f"API key {key_data['id']} is expired")
                            return None
                    
                    # Update last used timestamp and usage count
                    self.api_keys_ref.document(key_data['id']).update({
                        'last_used_at': firestore.SERVER_TIMESTAMP,
                        'usage_count': firestore.Increment(1)
                    })
                    
                    logger.info(f"API key {key_data['id']} validated successfully")
                    return key_data
            
            logger.warning("Invalid API key provided")
            return None
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all API keys (without sensitive data)"""
        try:
            keys = []
            api_keys = self.api_keys_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
            
            for doc in api_keys:
                key_data = doc.to_dict()
                # Remove sensitive data
                safe_data = {k: v for k, v in key_data.items() if k != 'key_hash'}
                keys.append(safe_data)
            
            return keys
        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []
    
    def deactivate_api_key(self, api_key_id: str) -> bool:
        """Deactivate an API key"""
        try:
            self.api_keys_ref.document(api_key_id).update({
                'is_active': False,
                'deactivated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Deactivated API key {api_key_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate API key {api_key_id}: {e}")
            return False

# Global instance
firestore_client = FirestoreClient()