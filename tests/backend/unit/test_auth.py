"""
Backend Authentication Tests - Phase 2

Test suite for authentication and authorization functionality in the pixel management system.
Provides comprehensive coverage of the auth.py module including API key validation,
access control, and endpoint protection.

Coverage Requirements:
- 100% coverage of authentication module (critical requirement)
- All authentication flows tested (valid, invalid, missing credentials)
- Health endpoint bypass verification
- Bearer token format validation
- Admin action logging verification

Test Categories:
1. Valid API key authentication with Bearer token
2. Invalid API key rejection with proper HTTP status codes
3. Missing API key handling with authentication challenges
4. Health endpoint bypass without authentication
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import hashlib
import secrets
import logging
from datetime import datetime

from app.auth import (
    AdminAuthenticator, 
    verify_admin_access, 
    log_admin_action,
    admin_auth
)


class TestAdminAuthenticator:
    """Test the AdminAuthenticator class functionality."""
    
    def test_init_with_environment_api_key(self):
        """Test AdminAuthenticator initialization with environment API key."""
        test_key = "test_env_key_12345"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Verify the key is stored correctly
            assert authenticator.admin_api_key == test_key
            
            # Verify the hash is computed correctly
            expected_hash = hashlib.sha256(test_key.encode()).hexdigest()
            assert authenticator.api_key_hash == expected_hash
    
    def test_init_without_environment_api_key(self):
        """Test AdminAuthenticator initialization without environment API key."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('app.auth.secrets.token_urlsafe') as mock_token:
                mock_token.return_value = "mock_random_token_123"
                
                authenticator = AdminAuthenticator()
                
                # Verify key was generated with correct format
                expected_key = "evothesis_admin_mock_random_token_123"
                assert authenticator.admin_api_key == expected_key
                
                # Verify hash was computed
                assert authenticator.api_key_hash is not None
                assert len(authenticator.api_key_hash) == 64  # SHA-256 hex digest length
    
    def test_generate_secure_api_key_format(self):
        """Test that generated API keys follow the correct format."""
        authenticator = AdminAuthenticator()
        
        # Generate multiple keys to verify format consistency
        for _ in range(5):
            key = authenticator._generate_secure_api_key()
            
            # Verify format: evothesis_admin_{random_token}
            assert key.startswith("evothesis_admin_")
            assert len(key) > len("evothesis_admin_")
            
            # Verify the random portion is URL-safe base64
            random_part = key[len("evothesis_admin_"):]
            assert len(random_part) > 20  # Ensure sufficient entropy
    
    def test_verify_api_key_valid(self):
        """Test API key verification with valid key."""
        test_key = "test_valid_key_12345"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Test with correct key
            assert authenticator.verify_api_key(test_key) is True
    
    def test_verify_api_key_invalid(self):
        """Test API key verification with invalid key."""
        correct_key = "test_valid_key_12345"
        wrong_key = "test_invalid_key_54321"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': correct_key}):
            authenticator = AdminAuthenticator()
            
            # Test with wrong key
            assert authenticator.verify_api_key(wrong_key) is False
    
    def test_verify_api_key_empty_string(self):
        """Test API key verification with empty string."""
        test_key = "test_valid_key_12345"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Test with empty string
            assert authenticator.verify_api_key("") is False
    
    def test_verify_api_key_exception_handling(self):
        """Test API key verification handles exceptions gracefully."""
        test_key = "test_valid_key_12345"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Mock hashlib to raise exception
            with patch('app.auth.hashlib.sha256') as mock_sha256:
                mock_sha256.side_effect = Exception("Hash computation failed")
                
                # Should return False on exception
                assert authenticator.verify_api_key(test_key) is False
    
    def test_get_api_key_id_normal_length(self):
        """Test API key ID generation for normal length keys."""
        authenticator = AdminAuthenticator()
        
        test_key = "evothesis_admin_abcdef123456789"
        result = authenticator.get_api_key_id(test_key)
        
        # Should return last 8 characters
        expected = "admin_key_...23456789"
        assert result == expected
    
    def test_get_api_key_id_short_key(self):
        """Test API key ID generation for short keys."""
        authenticator = AdminAuthenticator()
        
        test_key = "short"
        result = authenticator.get_api_key_id(test_key)
        
        # Should return fallback for short keys
        assert result == "admin_key_short"


class TestVerifyAdminAccess:
    """Test the verify_admin_access dependency function."""
    
    @pytest.mark.asyncio
    async def test_valid_api_key_authentication(self):
        """Test successful authentication with valid Bearer token."""
        test_key = "test_admin_key_12345"
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_key
        )
        
        with patch('app.auth.admin_auth') as mock_auth:
            mock_auth.verify_api_key.return_value = True
            mock_auth.get_api_key_id.return_value = "admin_key_...key_12345"
            
            result = await verify_admin_access(credentials)
            
            # Should return API key identifier
            assert result == "admin_key_...key_12345"
            
            # Verify the auth methods were called correctly
            mock_auth.verify_api_key.assert_called_once_with(test_key)
            mock_auth.get_api_key_id.assert_called_once_with(test_key)
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_rejection(self):
        """Test rejection of invalid API key with proper HTTP status."""
        test_key = "invalid_admin_key_54321"
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_key
        )
        
        with patch('app.auth.admin_auth') as mock_auth:
            mock_auth.verify_api_key.return_value = False
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_admin_access(credentials)
            
            # Verify proper HTTP status and headers
            assert exc_info.value.status_code == 401
            assert "Invalid API key" in exc_info.value.detail
            assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
            
            # Verify auth was called
            mock_auth.verify_api_key.assert_called_once_with(test_key)
    
    @pytest.mark.asyncio
    async def test_missing_api_key_handling(self):
        """Test handling of missing authorization credentials."""
        # Test with None credentials (missing Authorization header)
        with pytest.raises(HTTPException) as exc_info:
            await verify_admin_access(None)
        
        # Verify proper HTTP status and challenge
        assert exc_info.value.status_code == 401
        assert "Missing authorization credentials" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


class TestLogAdminAction:
    """Test the admin action logging functionality."""
    
    def test_log_admin_action_complete(self, caplog):
        """Test admin action logging with all parameters."""
        with caplog.at_level(logging.INFO):
            log_admin_action(
                action="create_client",
                client_id="client_test_123",
                api_key_id="admin_key_...12345",
                details="Created e-commerce client"
            )
        
        # Verify log entry was created
        assert len(caplog.records) == 1
        log_record = caplog.records[0]
        
        # Verify log level and message format
        assert log_record.levelname == "INFO"
        assert "ADMIN_AUDIT:" in log_record.message
        
        # Verify log contains expected fields
        log_message = log_record.message
        assert "create_client" in log_message
        assert "client_test_123" in log_message
        assert "admin_key_...12345" in log_message
        assert "Created e-commerce client" in log_message
    
    def test_log_admin_action_minimal(self, caplog):
        """Test admin action logging with minimal parameters."""
        with caplog.at_level(logging.INFO):
            log_admin_action(
                action="list_clients",
                client_id=None,
                api_key_id="admin_key_...67890",
                details=None
            )
        
        # Verify log entry was created
        assert len(caplog.records) == 1
        log_record = caplog.records[0]
        
        # Verify basic structure
        assert log_record.levelname == "INFO"
        assert "ADMIN_AUDIT:" in log_record.message
        assert "list_clients" in log_record.message
        assert "admin_key_...67890" in log_record.message
    
    def test_log_admin_action_iso_timestamp(self, caplog):
        """Test that admin action logging includes ISO formatted timestamp."""
        with caplog.at_level(logging.INFO):
            log_admin_action(
                action="test_action",
                client_id="test_client",
                api_key_id="test_key",
                details="test_details"
            )
        
        log_message = caplog.records[0].message
        
        # Extract timestamp from log message
        # Log format includes ISO timestamp
        assert "timestamp" in log_message
        
        # Verify it looks like an ISO timestamp (basic format check)
        import re
        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+'
        assert re.search(iso_pattern, log_message)


class TestEndpointAuthenticationIntegration:
    """Test authentication integration with FastAPI endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_bypass(self, test_client):
        """Test that health endpoint bypasses authentication."""
        response = await test_client.get("/health")
        
        # Health endpoint should return 200 without authentication
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] in ["healthy", "degraded"]
        assert response_data["service"] == "pixel-management"
        assert "timestamp" in response_data
    
    @pytest.mark.asyncio
    async def test_admin_endpoint_requires_auth(self, test_client):
        """Test that admin endpoints require authentication."""
        # Test without Authorization header
        response = await test_client.get("/api/v1/admin/clients")
        
        # Should return 403 Forbidden (FastAPI converts 401 to 403 for missing auth)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_endpoint_with_valid_auth(self, test_client, valid_admin_headers):
        """Test admin endpoint access with valid authentication."""
        response = await test_client.get(
            "/api/v1/admin/clients",
            headers=valid_admin_headers
        )
        
        # Should return successful response
        assert response.status_code == 200
        
        # Should return list of clients
        response_data = response.json()
        assert isinstance(response_data, list)
    
    @pytest.mark.asyncio
    async def test_admin_endpoint_with_invalid_auth(self, test_client, invalid_admin_headers):
        """Test admin endpoint access with invalid authentication."""
        response = await test_client.get(
            "/api/v1/admin/clients",
            headers=invalid_admin_headers
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        
        response_data = response.json()
        assert "Invalid API key" in response_data["detail"]


class TestAuthenticationSecurityFeatures:
    """Test security-specific features of the authentication system."""
    
    def test_timing_safe_comparison(self):
        """Test that API key verification uses timing-safe comparison."""
        test_key = "test_timing_key_12345"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Verify that secrets.compare_digest is used for comparison
            with patch('app.auth.secrets.compare_digest') as mock_compare:
                mock_compare.return_value = True
                
                result = authenticator.verify_api_key(test_key)
                
                # Verify compare_digest was called
                mock_compare.assert_called_once()
                assert result is True
    
    def test_sha256_hashing(self):
        """Test that API keys are hashed using SHA-256."""
        test_key = "test_hash_key_12345"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Verify hash length (SHA-256 produces 64-character hex)
            assert len(authenticator.api_key_hash) == 64
            
            # Verify hash is deterministic
            expected_hash = hashlib.sha256(test_key.encode()).hexdigest()
            assert authenticator.api_key_hash == expected_hash
    
    def test_api_key_format_validation(self):
        """Test that generated API keys follow secure format requirements."""
        authenticator = AdminAuthenticator()
        
        # Generate multiple keys and verify format consistency
        for _ in range(10):
            key = authenticator._generate_secure_api_key()
            
            # Verify prefix
            assert key.startswith("evothesis_admin_")
            
            # Verify minimum length (prefix + sufficient entropy)
            assert len(key) >= 50
            
            # Verify URL-safe characters in random portion
            random_part = key[len("evothesis_admin_"):]
            import string
            allowed_chars = string.ascii_letters + string.digits + '-_'
            assert all(c in allowed_chars for c in random_part)
    
    def test_error_logging_without_key_exposure(self, caplog):
        """Test that authentication errors don't expose full API keys in logs."""
        test_key = "sensitive_admin_key_secret123"
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_key
        )
        
        with patch('app.auth.admin_auth') as mock_auth:
            mock_auth.verify_api_key.return_value = False
            
            with caplog.at_level(logging.WARNING):
                with pytest.raises(HTTPException):
                    import asyncio
                    asyncio.run(verify_admin_access(credentials))
            
            # Verify logs don't contain the full API key
            log_messages = [record.message for record in caplog.records]
            for message in log_messages:
                assert "sensitive_admin_key_secret123" not in message
                # Should only contain last 8 characters at most
                if "secret123" in message:
                    # Only last 8 chars should appear
                    assert "sensitive_admin_key_" not in message


# Performance and edge case tests
class TestAuthenticationEdgeCases:
    """Test edge cases and performance requirements for authentication."""
    
    def test_very_long_api_key(self):
        """Test authentication with unusually long API key."""
        # Create a very long API key
        long_key = "evothesis_admin_" + "x" * 1000
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': long_key}):
            authenticator = AdminAuthenticator()
            
            # Should handle long keys without issues
            assert authenticator.verify_api_key(long_key) is True
    
    def test_unicode_in_api_key(self):
        """Test authentication handles Unicode characters gracefully."""
        unicode_key = "test_key_with_ünicode_€"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': unicode_key}):
            authenticator = AdminAuthenticator()
            
            # Should handle Unicode encoding correctly
            assert authenticator.verify_api_key(unicode_key) is True
    
    def test_null_bytes_in_api_key(self):
        """Test authentication rejects keys with null bytes."""
        malicious_key = "test_key\x00_with_null"
        normal_key = "test_key_normal"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': normal_key}):
            authenticator = AdminAuthenticator()
            
            # Should reject key with null bytes
            assert authenticator.verify_api_key(malicious_key) is False
    
    @pytest.mark.asyncio
    async def test_concurrent_authentication_requests(self):
        """Test that authentication handles concurrent requests safely."""
        import asyncio
        
        test_key = "test_concurrent_key_12345"
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_key
        )
        
        with patch('app.auth.admin_auth') as mock_auth:
            mock_auth.verify_api_key.return_value = True
            mock_auth.get_api_key_id.return_value = "admin_key_...12345"
            
            # Run multiple authentication requests concurrently
            tasks = [verify_admin_access(credentials) for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(result == "admin_key_...12345" for result in results)
            
            # Verify auth was called for each request
            assert mock_auth.verify_api_key.call_count == 10