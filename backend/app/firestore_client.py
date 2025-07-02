# backend/app/firestore_client.py
import os
from google.cloud import firestore
from google.auth import credentials
from google.oauth2 import service_account
from typing import Optional, List, Dict, Any
import secrets
import string
from datetime import datetime
import logging
import json

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
            
            # Initialize collection references
            self.clients_ref = self.db.collection('clients')
            self.domain_index_ref = self.db.collection('domain_index')
            self.config_changes_ref = self.db.collection('configuration_changes')
            
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

# Global instance
firestore_client = FirestoreClient()