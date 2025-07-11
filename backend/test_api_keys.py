# test_api_keys.py - CREATE THIS NEW FILE in pixel-management/backend/
# Simple test script to validate API key functionality

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.firestore_client import FirestoreClient
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_key_operations():
    """Test API key creation, validation, and management"""
    try:
        # Initialize Firestore client
        client = FirestoreClient()
        logger.info("✅ Firestore client initialized")
        
        # Test 1: Generate API key
        api_key = client.generate_api_key()
        logger.info(f"✅ Generated API key: {client.create_api_key_preview(api_key)}")
        assert api_key.startswith("evpx_"), "API key should start with evpx_"
        assert len(api_key) == 37, "API key should be 37 characters (evpx_ + 32 chars)"
        
        # Test 2: Hash and verify API key
        key_hash = client.hash_api_key(api_key)
        logger.info("✅ Hashed API key")
        assert client.verify_api_key(api_key, key_hash), "API key verification should succeed"
        assert not client.verify_api_key("wrong_key", key_hash), "Wrong key should fail verification"
        
        # Test 3: Create API key in Firestore
        key_id, actual_key = client.create_api_key(
            name="Test Service Key",
            permissions=["config:read"],
            created_by="client_test_admin"
        )
        logger.info(f"✅ Created API key in Firestore: {key_id}")
        
        # Test 4: Validate API key
        key_data = client.validate_api_key(actual_key)
        assert key_data is not None, "API key validation should succeed"
        assert key_data['name'] == "Test Service Key", "Key name should match"
        assert "config:read" in key_data['permissions'], "Should have config:read permission"
        logger.info("✅ API key validation successful")
        
        # Test 5: Invalid key should fail
        invalid_data = client.validate_api_key("evpx_invalid_key_here_123456789")
        assert invalid_data is None, "Invalid API key should return None"
        logger.info("✅ Invalid key correctly rejected")
        
        # Test 6: List API keys
        api_keys = client.list_api_keys()
        assert len(api_keys) >= 1, "Should have at least our test key"
        logger.info(f"✅ Listed {len(api_keys)} API keys")
        
        # Test 7: Deactivate API key
        success = client.deactivate_api_key(key_id)
        assert success, "Key deactivation should succeed"
        logger.info("✅ API key deactivated")
        
        # Test 8: Deactivated key should fail validation
        deactivated_data = client.validate_api_key(actual_key)
        assert deactivated_data is None, "Deactivated key should not validate"
        logger.info("✅ Deactivated key correctly rejected")
        
        logger.info("\n🎉 All API key tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Set up environment for testing
    os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'evothesis')
    
    print("Testing API Key functionality...")
    print("=" * 50)
    
    success = test_api_key_operations()
    
    if success:
        print("\n✅ Task 1 Complete: API Key Data Model & Storage implemented successfully!")
        print("\nNext steps:")
        print("1. Add the schemas to your existing schemas.py file")
        print("2. Add the methods to your existing firestore_client.py file") 
        print("3. Add bcrypt==4.1.2 to requirements.txt")
        print("4. Test the integration")
    else:
        print("\n❌ Tests failed - please check the implementation")
    
    exit(0 if success else 1)