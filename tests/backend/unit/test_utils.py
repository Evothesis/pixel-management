"""
Backend Utility Functions Unit Tests - Phase 7

Comprehensive testing of utility functions for data validation, transformation,
helper functions for Firestore document manipulation, error handling utilities,
logging functions, and performance monitoring/metrics collection utilities.

This test suite covers utility functions across multiple modules including
authentication utilities, pixel generation helpers, template processing,
data validation functions, and performance monitoring utilities.

Coverage Requirements:
- Utility functions for data validation and transformation
- Helper functions for Firestore document manipulation
- Error handling utilities and logging functions
- Performance monitoring and metrics collection utilities

Test Categories:
1. Data validation and transformation utilities
2. Performance monitoring and metrics collection utilities
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import hashlib
import secrets
import json
import time
import logging
import threading
from pathlib import Path

# Import modules to test their utility functions
from app.auth import AdminAuthenticator, log_admin_action
from app.pixel_serving import PixelTemplateCache, generate_pixel_javascript, validate_domain_authorization
from app.firestore_client import FirestoreClient


class TestDataValidationAndTransformation:
    """Test data validation and transformation utility functions"""
    
    def test_admin_authenticator_secure_key_generation(self):
        """Test AdminAuthenticator utility methods for secure key operations"""
        with patch.dict('os.environ', {}, clear=True):
            # Test secure API key generation
            auth = AdminAuthenticator()
            
            # Verify generated key format
            assert auth.admin_api_key.startswith('evothesis_admin_')
            assert len(auth.admin_api_key) > 20
            
            # Verify key is hashed properly
            expected_hash = hashlib.sha256(auth.admin_api_key.encode()).hexdigest()
            assert auth.api_key_hash == expected_hash
            
            # Test key verification utility
            assert auth.verify_api_key(auth.admin_api_key) is True
            assert auth.verify_api_key('invalid_key') is False
            assert auth.verify_api_key('') is False
            
            # Test key identifier generation utility
            key_id = auth.get_api_key_id(auth.admin_api_key)
            assert 'admin_key_...' in key_id
            assert key_id.endswith(auth.admin_api_key[-8:])
    
    def test_admin_authenticator_error_handling_utilities(self):
        """Test AdminAuthenticator error handling and edge cases"""
        with patch.dict('os.environ', {}, clear=True):
            auth = AdminAuthenticator()
            
            # Test malformed key handling
            with patch('hashlib.sha256') as mock_hash:
                mock_hash.side_effect = Exception("Hash error")
                assert auth.verify_api_key('test_key') is False
            
            # Test short key identifier handling
            short_key = "abc"
            key_id = auth.get_api_key_id(short_key)
            assert key_id == "admin_key_short"
            
            # Test empty key handling
            assert auth.verify_api_key(None) is False
            
            # Test timing-safe comparison with various inputs
            test_cases = [
                'valid_key_123',
                'invalid_key_456',
                '12345',
                '',
                None
            ]
            
            for test_key in test_cases:
                try:
                    result = auth.verify_api_key(test_key) if test_key else False
                    assert isinstance(result, bool)
                except Exception:
                    # Should handle all exceptions gracefully
                    assert False, f"Exception raised for key: {test_key}"

    def test_firestore_client_utility_functions(self):
        """Test FirestoreClient utility and helper functions"""
        client = FirestoreClient()
        
        # Test client ID generation utility
        client_id = client.generate_client_id()
        assert client_id.startswith('client_')
        assert len(client_id) == 19  # 'client_' + 12 chars
        assert client_id.replace('client_', '').islower()
        assert client_id.replace('client_', '').replace('_', '').isalnum()
        
        # Test multiple generations are unique
        client_ids = {client.generate_client_id() for _ in range(100)}
        assert len(client_ids) == 100  # All should be unique
        
        # Test IP salt generation utility
        salt1 = client.generate_ip_salt()
        salt2 = client.generate_ip_salt()
        
        assert len(salt1) == 64  # 32 bytes = 64 hex chars
        assert len(salt2) == 64
        assert salt1 != salt2  # Should be unique
        assert all(c in '0123456789abcdef' for c in salt1)  # Valid hex
        assert all(c in '0123456789abcdef' for c in salt2)  # Valid hex
    
    def test_firestore_client_api_key_utilities(self):
        """Test Firestore API key management utilities"""
        client = FirestoreClient()
        
        # Test API key generation format
        api_key = client.generate_api_key()
        assert api_key.startswith('evpx_')
        assert len(api_key) == 37  # 'evpx_' + 32 chars
        
        # Test multiple generations are unique
        api_keys = {client.generate_api_key() for _ in range(50)}
        assert len(api_keys) == 50
        
        # Test API key hashing utility
        test_key = 'test_api_key_12345'
        key_hash = client.hash_api_key(test_key)
        
        assert isinstance(key_hash, str)
        assert len(key_hash) > 50  # bcrypt hash should be long
        assert '$2b$' in key_hash  # bcrypt format identifier
        
        # Test key verification utility
        assert client.verify_api_key(test_key, key_hash) is True
        assert client.verify_api_key('wrong_key', key_hash) is False
        assert client.verify_api_key('', key_hash) is False
        
        # Test preview generation utility
        preview = client.create_api_key_preview(api_key)
        assert '...' in preview
        assert len(preview) < len(api_key)
        
        # Test short key preview
        short_key = 'abc'
        short_preview = client.create_api_key_preview(short_key)
        assert short_preview == 'abc...'

    def test_pixel_template_caching_utilities(self):
        """Test pixel template caching and processing utilities"""
        # Test template cache initialization
        cache = PixelTemplateCache()
        assert cache._template_cache is None
        assert cache._cache_timestamp == 0
        
        # Mock template file
        mock_template_content = """
        // Pixel tracking template
        var config = {CONFIG_PLACEHOLDER};
        console.log('Tracking initialized', config);
        """
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open_with_content(mock_template_content)):
            
            # Test template loading
            template = cache.get_template()
            assert template == mock_template_content
            assert '{CONFIG_PLACEHOLDER}' in template
            
            # Test caching behavior
            assert cache._template_cache == mock_template_content
            assert cache._cache_timestamp > 0
            
            # Test cache hit (should not reload)
            with patch('builtins.open') as mock_open:
                template2 = cache.get_template()
                assert template2 == template
                mock_open.assert_not_called()  # Should use cache
        
        # Test cache expiration
        with patch('time.time', return_value=cache._cache_timestamp + 3601), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open_with_content("// Updated template")):
            
            updated_template = cache.get_template()
            assert updated_template == "// Updated template"
    
    def test_javascript_generation_utilities(self):
        """Test JavaScript pixel generation and configuration utilities"""
        # Test basic configuration transformation
        client_config = {
            'client_id': 'client_test_123',
            'privacy_level': 'standard',
            'features': {'analytics': True}
        }
        
        collection_endpoint = 'https://collect.evothesis.com/v1/events'
        
        # Mock template
        mock_template = 'var config = {CONFIG_PLACEHOLDER}; // Tracking code'
        
        with patch('app.pixel_serving.template_cache.get_template', return_value=mock_template):
            
            pixel_js = generate_pixel_javascript(client_config, collection_endpoint)
            
            # Verify configuration injection
            assert 'client_test_123' in pixel_js
            assert collection_endpoint in pixel_js
            assert 'pixel_version' in pixel_js
            assert 'generated_at' in pixel_js
            
            # Verify JSON is valid and properly formatted
            config_start = pixel_js.find('{')
            config_end = pixel_js.rfind('}') + 1
            extracted_config = pixel_js[config_start:config_end]
            
            parsed_config = json.loads(extracted_config)
            assert parsed_config['client_id'] == 'client_test_123'
            assert parsed_config['collection_endpoint'] == collection_endpoint
            assert 'pixel_version' in parsed_config
            assert 'generated_at' in parsed_config

    def test_data_validation_edge_cases(self):
        """Test data validation utilities with edge cases and malformed data"""
        client = FirestoreClient()
        
        # Test API key verification with malformed hash
        with patch('bcrypt.checkpw', side_effect=Exception("Bcrypt error")):
            result = client.verify_api_key('test_key', 'malformed_hash')
            assert result is False
        
        # Test ID generation under different conditions
        with patch('secrets.choice', side_effect=['a'] * 12):
            client_id = client.generate_client_id()
            assert client_id == 'client_aaaaaaaaaaaa'
        
        # Test salt generation with different entropy
        with patch('secrets.token_hex', return_value='deadbeef' * 8):
            salt = client.generate_ip_salt()
            assert salt == 'deadbeef' * 8


class TestPerformanceMonitoringAndMetrics:
    """Test performance monitoring and metrics collection utilities"""
    
    def test_template_cache_thread_safety(self):
        """Test PixelTemplateCache thread safety and performance"""
        cache = PixelTemplateCache()
        
        mock_template = 'var config = {CONFIG_PLACEHOLDER};'
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open_with_content(mock_template)):
            
            # Test concurrent access
            results = []
            errors = []
            
            def cache_access_worker():
                try:
                    template = cache.get_template()
                    results.append(template)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=cache_access_worker)
                threads.append(thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            # Verify thread safety
            assert len(errors) == 0, f"Thread safety errors: {errors}"
            assert len(results) == 10
            assert all(result == mock_template for result in results)
    
    def test_admin_audit_logging_utilities(self):
        """Test admin audit logging and performance tracking"""
        with patch('logging.getLogger') as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance
            
            # Test audit logging utility
            log_admin_action(
                action="CLIENT_CREATE",
                client_id="client_test_123", 
                api_key_id="admin_key_...12345678",
                details="Created new ecommerce client"
            )
            
            # Verify log entry structure
            mock_log_instance.info.assert_called_once()
            call_args = mock_log_instance.info.call_args[0][0]
            
            assert "ADMIN_AUDIT:" in call_args
            assert "CLIENT_CREATE" in call_args
            assert "client_test_123" in call_args
            assert "admin_key_...12345678" in call_args
            
            # Parse the log entry
            log_data_start = call_args.find('{')
            log_data = json.loads(call_args[log_data_start:])
            
            assert log_data['action'] == "CLIENT_CREATE"
            assert log_data['client_id'] == "client_test_123"
            assert log_data['api_key_id'] == "admin_key_...12345678"
            assert log_data['details'] == "Created new ecommerce client"
            assert 'timestamp' in log_data
    
    def test_pixel_generation_performance_tracking(self):
        """Test pixel generation performance metrics"""
        client_config = {
            'client_id': 'client_perf_test',
            'privacy_level': 'hipaa',
            'features': {'analytics': True, 'conversion': True}
        }
        
        mock_template = '/* TEMPLATE START */ var config = {CONFIG_PLACEHOLDER}; /* TEMPLATE END */'
        
        with patch('app.pixel_serving.template_cache.get_template', return_value=mock_template):
            
            # Test performance tracking in generated pixel
            start_time = time.time()
            pixel_js = generate_pixel_javascript(client_config, 'https://api.test.com/collect')
            end_time = time.time()
            
            # Verify generated_at timestamp is recent
            config_start = pixel_js.find('{')
            config_end = pixel_js.rfind('}') + 1
            config_json = json.loads(pixel_js[config_start:config_end])
            
            generated_at = config_json['generated_at']
            assert start_time <= generated_at <= end_time
            
            # Verify pixel version tracking
            assert config_json['pixel_version'] == '1.0.0'
            
            # Test with complex configuration
            complex_config = {
                'client_id': 'client_complex_perf',
                'privacy_level': 'gdpr',
                'features': {f'feature_{i}': True for i in range(50)},
                'large_data': ['item' for _ in range(100)]
            }
            
            start_time = time.time()
            complex_pixel = generate_pixel_javascript(complex_config, 'https://complex.api.com/collect')
            end_time = time.time()
            
            # Should still complete reasonably quickly
            assert end_time - start_time < 1.0  # Less than 1 second
            assert len(complex_pixel) > len(pixel_js)  # Should be larger
    
    def test_template_cache_performance_metrics(self):
        """Test template cache performance and memory efficiency"""
        cache = PixelTemplateCache()
        
        # Test cache miss timing
        large_template = 'var config = {CONFIG_PLACEHOLDER};\n' + '// Comment line\n' * 1000
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open_with_content(large_template)):
            
            # First access - cache miss
            start_time = time.time()
            template1 = cache.get_template()
            first_access_time = time.time() - start_time
            
            # Second access - cache hit
            start_time = time.time()
            template2 = cache.get_template()
            second_access_time = time.time() - start_time
            
            # Cache hit should be significantly faster
            assert template1 == template2
            assert second_access_time < first_access_time / 2
            
            # Test memory efficiency - should use same string object
            assert template1 is template2  # Same object reference
    
    def test_error_handling_performance_impact(self):
        """Test that error handling utilities don't impact performance significantly"""
        client = FirestoreClient()
        
        # Test rapid API key generation (should handle high load)
        start_time = time.time()
        api_keys = [client.generate_api_key() for _ in range(100)]
        generation_time = time.time() - start_time
        
        assert len(set(api_keys)) == 100  # All unique
        assert generation_time < 5.0  # Should complete quickly
        
        # Test rapid validation operations
        test_key = client.generate_api_key()
        key_hash = client.hash_api_key(test_key)
        
        start_time = time.time()
        for _ in range(50):
            client.verify_api_key(test_key, key_hash)
        verification_time = time.time() - start_time
        
        assert verification_time < 2.0  # Should complete quickly
        
        # Test error handling doesn't add significant overhead
        start_time = time.time()
        for _ in range(50):
            client.verify_api_key('invalid_key', key_hash)  # Will fail
        error_time = time.time() - start_time
        
        # Error cases shouldn't be dramatically slower
        assert error_time < verification_time * 3


def mock_open_with_content(content):
    """Helper function to create mock open with specific content"""
    from unittest.mock import mock_open
    return mock_open(read_data=content)