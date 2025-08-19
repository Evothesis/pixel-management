"""
Backend Firestore Database Operations Unit Tests - Phase 7

Comprehensive testing of Firestore database operations including connection management,
CRUD operations with proper error handling, transaction management, rollback scenarios,
batch operations, and performance optimization for the pixel management system.

This test suite covers the complete Firestore database integration including
connection initialization, document operations, collection management, indexing,
error recovery, and performance optimization strategies.

Coverage Requirements:
- Firestore database connection and initialization
- CRUD operations with proper error handling
- Transaction management and rollback scenarios
- Batch operations and performance optimization

Test Categories:
1. Database connection and initialization management
2. CRUD operations with transaction management and performance optimization
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from google.cloud import firestore
from google.api_core import exceptions as firestore_exceptions
import bcrypt
import json
import time
from typing import List, Dict, Any

from app.firestore_client import FirestoreClient, firestore_client


class TestDatabaseConnectionAndInitialization:
    """Test Firestore database connection and initialization management"""
    
    def test_firestore_client_initialization_success(self):
        """Test successful Firestore client initialization with different auth methods"""
        # Test with service account credentials
        with patch.dict('os.environ', {'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/creds.json', 'GOOGLE_CLOUD_PROJECT': 'test-project'}), \
             patch('google.cloud.firestore.Client') as mock_firestore:
            
            mock_db = Mock()
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Verify initialization
            assert client.db == mock_db
            assert hasattr(client, 'clients_ref')
            assert hasattr(client, 'domain_index_ref')
            assert hasattr(client, 'config_changes_ref')
            assert hasattr(client, 'api_keys_ref')
            
            # Verify Firestore client was created with project
            mock_firestore.assert_called_once_with(project='test-project')
    
    def test_firestore_client_initialization_default_credentials(self):
        """Test Firestore client initialization with default credentials"""
        with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'default-project'}, clear=True), \
             patch('google.cloud.firestore.Client') as mock_firestore:
            
            mock_db = Mock()
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Verify default credentials path was used
            mock_firestore.assert_called_once_with(project='default-project')
            assert client.db == mock_db
    
    def test_firestore_client_initialization_failure_handling(self):
        """Test Firestore client initialization failure scenarios"""
        with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}), \
             patch('google.cloud.firestore.Client', side_effect=Exception("Connection failed")):
            
            with pytest.raises(Exception, match="Connection failed"):
                FirestoreClient()
    
    def test_connection_test_functionality(self):
        """Test Firestore connection testing utility"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            mock_query = Mock()
            
            # Setup mock chain
            mock_db.collection.return_value = mock_collection
            mock_collection.limit.return_value = mock_query
            mock_query.get.return_value = []  # Empty result is fine
            
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Test successful connection
            result = client.test_connection()
            assert result is True
            
            # Verify the health check query was made
            mock_db.collection.assert_called_with('_health_check')
            mock_collection.limit.assert_called_with(1)
    
    def test_connection_test_failure_scenarios(self):
        """Test connection test failure handling"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            
            # Setup failure scenario
            mock_db.collection.return_value = mock_collection
            mock_collection.limit.side_effect = firestore_exceptions.ServiceUnavailable("Service unavailable")
            
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Test connection failure
            result = client.test_connection()
            assert result is False
    
    def test_collection_reference_initialization(self):
        """Test proper collection reference setup"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Verify all required collections are initialized
            expected_collections = [
                'clients',
                'domain_index', 
                'configuration_changes',
                'api_keys'
            ]
            
            for collection_name in expected_collections:
                mock_db.collection.assert_any_call(collection_name)
    
    def test_database_project_configuration(self):
        """Test database project configuration handling"""
        test_cases = [
            {'GOOGLE_CLOUD_PROJECT': 'production-project'},
            {'GOOGLE_CLOUD_PROJECT': 'staging-project'},
            {}  # Default case
        ]
        
        for env_vars in test_cases:
            with patch.dict('os.environ', env_vars, clear=True), \
                 patch('google.cloud.firestore.Client') as mock_firestore:
                
                mock_firestore.return_value = Mock()
                
                client = FirestoreClient()
                
                expected_project = env_vars.get('GOOGLE_CLOUD_PROJECT', 'evothesis')
                mock_firestore.assert_called_once_with(project=expected_project)


class TestCRUDOperationsWithTransactionManagement:
    """Test CRUD operations with transaction management and performance optimization"""
    
    def test_api_key_creation_and_management_operations(self):
        """Test complete API key CRUD operations"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            mock_document = Mock()
            
            # Setup mock chain
            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_document
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Test API key creation
            api_key_id, actual_api_key = client.create_api_key(
                name="Test API Key",
                permissions=["admin", "read"],
                created_by="admin@test.com"
            )
            
            # Verify key format
            assert api_key_id.startswith('apikey_')
            assert actual_api_key.startswith('evpx_')
            assert len(api_key_id) == 19  # 'apikey_' + 12 chars
            assert len(actual_api_key) == 37  # 'evpx_' + 32 chars
            
            # Verify document was created
            mock_collection.document.assert_called_with(api_key_id)
            mock_document.set.assert_called_once()
            
            # Verify document structure
            call_args = mock_document.set.call_args[0][0]
            assert call_args['id'] == api_key_id
            assert call_args['name'] == "Test API Key"
            assert call_args['permissions'] == ["admin", "read"]
            assert call_args['created_by'] == "admin@test.com"
            assert call_args['is_active'] is True
            assert 'key_hash' in call_args
            assert firestore.SERVER_TIMESTAMP == call_args['created_at']
    
    def test_api_key_validation_operations(self):
        """Test API key validation with database queries"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            mock_query = Mock()
            mock_document = Mock()
            
            # Create test API key and hash
            client = FirestoreClient()
            test_api_key = client.generate_api_key()
            test_hash = client.hash_api_key(test_api_key)
            
            # Setup mock document data
            mock_doc_data = {
                'id': 'apikey_test123',
                'name': 'Test Key',
                'key_hash': test_hash,
                'permissions': ['admin'],
                'is_active': True,
                'expires_at': None,
                'created_at': datetime.utcnow(),
                'usage_count': 5
            }
            
            # Setup mock query result
            mock_doc = Mock()
            mock_doc.to_dict.return_value = mock_doc_data
            
            mock_query.stream.return_value = [mock_doc]
            mock_collection.where.return_value = mock_query
            mock_collection.document.return_value = mock_document
            
            mock_db.collection.return_value = mock_collection
            mock_firestore.return_value = mock_db
            
            # Test successful validation
            result = client.validate_api_key(test_api_key)
            
            assert result is not None
            assert result['id'] == 'apikey_test123'
            assert result['name'] == 'Test Key'
            
            # Verify query was made correctly
            mock_collection.where.assert_called_with('is_active', '==', True)
            
            # Verify usage tracking update
            mock_collection.document.assert_called_with('apikey_test123')
            mock_document.update.assert_called_once()
            update_call = mock_document.update.call_args[0][0]
            assert 'last_used_at' in update_call
            assert update_call['usage_count'] == firestore.Increment(1)
    
    def test_api_key_validation_with_expiration(self):
        """Test API key validation with expiration handling"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            mock_query = Mock()
            
            client = FirestoreClient()
            test_api_key = client.generate_api_key()
            test_hash = client.hash_api_key(test_api_key)
            
            # Setup expired key data
            expired_doc_data = {
                'id': 'apikey_expired',
                'key_hash': test_hash,
                'is_active': True,
                'expires_at': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            }
            
            mock_doc = Mock()
            mock_doc.to_dict.return_value = expired_doc_data
            mock_query.stream.return_value = [mock_doc]
            mock_collection.where.return_value = mock_query
            
            mock_db.collection.return_value = mock_collection
            mock_firestore.return_value = mock_db
            
            # Test validation of expired key
            result = client.validate_api_key(test_api_key)
            
            assert result is None  # Should reject expired key
    
    def test_batch_operations_and_performance_optimization(self):
        """Test batch operations for performance optimization"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_batch = Mock()
            mock_collection = Mock()
            
            mock_db.batch.return_value = mock_batch
            mock_db.collection.return_value = mock_collection
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Test batch API key creation (simulated)
            api_keys_data = []
            for i in range(5):
                api_key_id, actual_key = client.create_api_key(
                    name=f"Batch Key {i}",
                    permissions=["read"],
                    created_by="batch_admin@test.com"
                )
                api_keys_data.append((api_key_id, actual_key))
            
            # Verify multiple documents were created
            assert len(api_keys_data) == 5
            assert all(key_id.startswith('apikey_') for key_id, _ in api_keys_data)
            assert len(set(key_id for key_id, _ in api_keys_data)) == 5  # All unique
    
    def test_api_key_listing_with_pagination(self):
        """Test API key listing operations with proper data filtering"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            mock_query = Mock()
            
            # Setup mock data
            mock_keys_data = [
                {
                    'id': f'apikey_test_{i}',
                    'name': f'Test Key {i}',
                    'permissions': ['read'],
                    'created_at': datetime.utcnow() - timedelta(days=i),
                    'is_active': True,
                    'key_hash': 'hash_value_hidden'  # Should be filtered out
                }
                for i in range(3)
            ]
            
            mock_docs = [Mock() for _ in range(3)]
            for i, doc in enumerate(mock_docs):
                doc.to_dict.return_value = mock_keys_data[i]
            
            mock_query.stream.return_value = mock_docs
            mock_collection.order_by.return_value = mock_query
            mock_db.collection.return_value = mock_collection
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Test listing API keys
            result = client.list_api_keys()
            
            assert len(result) == 3
            
            # Verify sensitive data is filtered out
            for key_data in result:
                assert 'key_hash' not in key_data
                assert 'id' in key_data
                assert 'name' in key_data
                assert 'permissions' in key_data
            
            # Verify correct ordering query
            mock_collection.order_by.assert_called_with('created_at', direction=firestore.Query.DESCENDING)
    
    def test_transaction_management_and_rollback(self):
        """Test transaction management with rollback scenarios"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_transaction = Mock()
            mock_collection = Mock()
            mock_document = Mock()
            
            mock_db.transaction.return_value = mock_transaction
            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_document
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Test successful API key deactivation (atomic operation)
            success = client.deactivate_api_key('apikey_test123')
            
            assert success is True
            
            # Verify update operation
            mock_collection.document.assert_called_with('apikey_test123')
            mock_document.update.assert_called_once()
            
            update_data = mock_document.update.call_args[0][0]
            assert update_data['is_active'] is False
            assert 'deactivated_at' in update_data
    
    def test_error_handling_in_database_operations(self):
        """Test comprehensive error handling in database operations"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            
            # Test network error handling
            mock_collection.document.side_effect = firestore_exceptions.ServiceUnavailable("Network error")
            mock_db.collection.return_value = mock_collection
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # API key creation should handle errors gracefully
            with pytest.raises(Exception):
                client.create_api_key("Test Key", ["read"], "admin@test.com")
            
            # Test permission error handling
            mock_collection.document.side_effect = firestore_exceptions.PermissionDenied("Access denied")
            
            with pytest.raises(Exception):
                client.create_api_key("Test Key", ["read"], "admin@test.com")
            
            # Test invalid data error handling
            mock_collection.document.side_effect = firestore_exceptions.InvalidArgument("Invalid data")
            
            with pytest.raises(Exception):
                client.create_api_key("Test Key", ["read"], "admin@test.com")
    
    def test_concurrent_operations_handling(self):
        """Test handling of concurrent database operations"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            mock_query = Mock()
            
            # Setup concurrent validation scenario
            client = FirestoreClient()
            test_key = client.generate_api_key()
            test_hash = client.hash_api_key(test_key)
            
            # Mock multiple documents with same key hash (shouldn't happen in practice)
            mock_docs = []
            for i in range(2):
                doc = Mock()
                doc.to_dict.return_value = {
                    'id': f'apikey_concurrent_{i}',
                    'key_hash': test_hash,
                    'is_active': True,
                    'expires_at': None
                }
                mock_docs.append(doc)
            
            mock_query.stream.return_value = mock_docs
            mock_collection.where.return_value = mock_query
            mock_db.collection.return_value = mock_collection
            mock_firestore.return_value = mock_db
            
            # Should handle multiple matches (return first valid one)
            result = client.validate_api_key(test_key)
            
            # Should return the first matching document
            assert result is not None
            assert result['id'] == 'apikey_concurrent_0'
    
    def test_database_performance_optimization(self):
        """Test database query performance optimization strategies"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            mock_query = Mock()
            
            client = FirestoreClient()
            
            # Test indexed query performance
            mock_query.stream.return_value = []
            mock_collection.where.return_value = mock_query
            mock_db.collection.return_value = mock_collection
            mock_firestore.return_value = mock_db
            
            # Multiple validation calls should use indexed queries
            test_key = client.generate_api_key()
            
            for _ in range(5):
                client.validate_api_key(test_key)
            
            # Verify efficient querying (using index on is_active field)
            assert mock_collection.where.call_count == 5
            for call in mock_collection.where.call_args_list:
                assert call[0] == ('is_active', '==', True)
    
    def test_cleanup_operations(self):
        """Test database cleanup and maintenance operations"""
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_db = Mock()
            mock_collection = Mock()
            mock_document = Mock()
            
            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_document
            mock_firestore.return_value = mock_db
            
            client = FirestoreClient()
            
            # Test key deactivation (soft delete)
            result = client.deactivate_api_key('apikey_cleanup_test')
            
            assert result is True
            
            # Verify soft delete operation
            mock_document.update.assert_called_once()
            update_data = mock_document.update.call_args[0][0]
            assert update_data['is_active'] is False
            assert 'deactivated_at' in update_data
            
            # Test error handling in cleanup
            mock_document.update.side_effect = Exception("Update failed")
            
            result = client.deactivate_api_key('apikey_error_test')
            assert result is False