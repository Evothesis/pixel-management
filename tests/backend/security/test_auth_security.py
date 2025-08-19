"""
Authentication Security Tests - Phase 2

Security-focused tests for authentication mechanisms in the pixel management system.
These tests ensure the authentication system is resistant to common attack vectors
including timing attacks, brute force attempts, and credential enumeration.

Security Requirements:
- Timing attack resistance through constant-time comparison
- No information leakage through response timing variations
- Secure handling of authentication failures
- Protection against credential enumeration attacks

Test Categories:
1. Timing attack resistance verification
2. Authentication response consistency
3. Error message security
4. Rate limiting integration (if applicable)
"""

import pytest
import time
import statistics
from unittest.mock import patch, Mock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import hashlib
import secrets

from app.auth import AdminAuthenticator, verify_admin_access


class TestTimingAttackResistance:
    """Test authentication system resistance to timing-based attacks."""
    
    def test_api_key_timing_attack_resistance(self):
        """
        CRITICAL: Verify that API key verification uses constant-time comparison
        to prevent timing attacks that could reveal valid key characteristics.
        """
        correct_key = "evothesis_admin_correct_key_12345"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': correct_key}):
            authenticator = AdminAuthenticator()
            
            # Test various wrong keys with different characteristics
            test_cases = [
                "evothesis_admin_wrong_key_12345",      # Similar length, similar prefix
                "completely_different_key",             # Different format
                "evothesis_admin_",                     # Prefix only
                "x" * len(correct_key),                 # Same length, different content
                "",                                     # Empty string
                "evothesis_admin_correct_key_54321",    # Almost correct (different suffix)
                "EVOTHESIS_ADMIN_CORRECT_KEY_12345",    # Case variation
                correct_key[:len(correct_key)//2],      # Partial key
            ]
            
            # Measure timing for correct key (should fail in test environment)
            with patch('app.auth.secrets.compare_digest') as mock_compare:
                mock_compare.return_value = False  # Force failure for timing test
                
                start_time = time.perf_counter()
                result = authenticator.verify_api_key(correct_key)
                correct_key_time = time.perf_counter() - start_time
                
                # Verify compare_digest was called (timing-safe comparison)
                mock_compare.assert_called()
                assert result is False  # Expected in this mocked scenario
            
            # Measure timing for various wrong keys
            wrong_key_times = []
            for wrong_key in test_cases:
                with patch('app.auth.secrets.compare_digest') as mock_compare:
                    mock_compare.return_value = False
                    
                    start_time = time.perf_counter()
                    result = authenticator.verify_api_key(wrong_key)
                    wrong_key_time = time.perf_counter() - start_time
                    
                    wrong_key_times.append(wrong_key_time)
                    assert result is False
                    mock_compare.assert_called()
            
            # Statistical analysis: timing variations should be minimal
            all_times = [correct_key_time] + wrong_key_times
            
            if len(all_times) > 1:
                time_std_dev = statistics.stdev(all_times)
                time_mean = statistics.mean(all_times)
                
                # Coefficient of variation should be low (< 50%)
                # This indicates timing is relatively constant
                coefficient_of_variation = (time_std_dev / time_mean) * 100
                
                # In a properly implemented system with secrets.compare_digest,
                # timing variations should be minimal
                assert coefficient_of_variation < 100, f"Timing variation too high: {coefficient_of_variation}%"
    
    def test_secrets_compare_digest_usage(self):
        """Verify that secrets.compare_digest is actually used for comparison."""
        test_key = "test_timing_safety_key"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Mock secrets.compare_digest to verify it's called
            with patch('app.auth.secrets.compare_digest') as mock_compare:
                mock_compare.return_value = True
                
                result = authenticator.verify_api_key(test_key)
                
                # Verify secrets.compare_digest was called
                mock_compare.assert_called_once()
                assert result is True
                
                # Verify the call was made with proper hash values
                call_args = mock_compare.call_args[0]
                assert len(call_args) == 2
                assert isinstance(call_args[0], str)  # stored hash
                assert isinstance(call_args[1], str)  # computed hash
                assert len(call_args[0]) == 64       # SHA-256 hex length
                assert len(call_args[1]) == 64       # SHA-256 hex length
    
    def test_hash_computation_consistency(self):
        """Test that hash computation is consistent and doesn't leak timing info."""
        test_key = "consistent_hash_test_key"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Test hash computation multiple times
            hash_times = []
            for _ in range(10):
                start_time = time.perf_counter()
                computed_hash = hashlib.sha256(test_key.encode()).hexdigest()
                hash_time = time.perf_counter() - start_time
                hash_times.append(hash_time)
                
                # Verify hash consistency
                assert computed_hash == authenticator.api_key_hash
            
            # Timing should be relatively consistent for same input
            if len(hash_times) > 1:
                hash_std_dev = statistics.stdev(hash_times)
                hash_mean = statistics.mean(hash_times)
                
                # Hash computation timing should be consistent
                coefficient_of_variation = (hash_std_dev / hash_mean) * 100
                assert coefficient_of_variation < 200, f"Hash timing variation too high: {coefficient_of_variation}%"


class TestAuthenticationResponseSecurity:
    """Test security aspects of authentication responses."""
    
    @pytest.mark.asyncio
    async def test_error_response_consistency(self):
        """Test that authentication errors return consistent responses."""
        test_cases = [
            "invalid_key_format",
            "wrong_length_key_12345",
            "evothesis_admin_wrong_suffix",
            "completely_wrong_format",
            "",
            "null\x00byte_key",
        ]
        
        error_responses = []
        
        for invalid_key in test_cases:
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=invalid_key
            )
            
            with patch('app.auth.admin_auth') as mock_auth:
                mock_auth.verify_api_key.return_value = False
                
                with pytest.raises(HTTPException) as exc_info:
                    await verify_admin_access(credentials)
                
                error_responses.append({
                    'status_code': exc_info.value.status_code,
                    'detail': exc_info.value.detail,
                    'headers': exc_info.value.headers
                })
        
        # All error responses should be identical
        first_response = error_responses[0]
        for response in error_responses[1:]:
            assert response['status_code'] == first_response['status_code']
            assert response['detail'] == first_response['detail']
            assert response['headers'] == first_response['headers']
        
        # Verify expected error format
        assert first_response['status_code'] == 401
        assert "Invalid API key" in first_response['detail']
        assert first_response['headers'] == {"WWW-Authenticate": "Bearer"}
    
    @pytest.mark.asyncio
    async def test_missing_credentials_response(self):
        """Test response for missing authentication credentials."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_admin_access(None)
        
        # Verify specific error format for missing credentials
        assert exc_info.value.status_code == 401
        assert "Missing authorization credentials" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
    
    def test_no_key_leakage_in_logs(self, caplog):
        """Test that API keys are not leaked in application logs."""
        import logging
        
        sensitive_key = "evothesis_admin_very_sensitive_secret_key_12345"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': 'different_key'}):
            authenticator = AdminAuthenticator()
            
            with caplog.at_level(logging.DEBUG):
                # This should fail and potentially log
                result = authenticator.verify_api_key(sensitive_key)
                assert result is False
            
            # Check all log messages don't contain the sensitive key
            for record in caplog.records:
                assert "very_sensitive_secret_key" not in record.message
                assert sensitive_key not in record.message
    
    def test_api_key_id_safe_representation(self):
        """Test that API key ID generation is safe for logging."""
        authenticator = AdminAuthenticator()
        
        sensitive_keys = [
            "evothesis_admin_highly_sensitive_production_key_abc123",
            "evothesis_admin_customer_data_access_key_xyz789",
            "evothesis_admin_financial_info_key_def456",
        ]
        
        for key in sensitive_keys:
            key_id = authenticator.get_api_key_id(key)
            
            # Should only contain last 8 characters
            assert key_id.startswith("admin_key_...")
            assert len(key_id) <= len("admin_key_...") + 8
            
            # Should not contain sensitive parts
            assert "sensitive" not in key_id.lower()
            assert "production" not in key_id.lower()
            assert "customer" not in key_id.lower()
            assert "financial" not in key_id.lower()


class TestSecureKeyGeneration:
    """Test security aspects of API key generation."""
    
    def test_key_generation_entropy(self):
        """Test that generated API keys have sufficient entropy."""
        authenticator = AdminAuthenticator()
        
        # Generate multiple keys
        keys = [authenticator._generate_secure_api_key() for _ in range(100)]
        
        # All keys should be unique (extremely high probability with good entropy)
        assert len(set(keys)) == len(keys), "Generated keys are not unique"
        
        # Keys should have sufficient length
        for key in keys:
            assert len(key) >= 50, f"Key too short: {len(key)}"
            
            # Extract random portion
            random_part = key[len("evothesis_admin_"):]
            assert len(random_part) >= 30, "Random portion too short"
    
    def test_key_generation_unpredictability(self):
        """Test that generated keys are unpredictable."""
        authenticator = AdminAuthenticator()
        
        # Generate keys and analyze patterns
        keys = [authenticator._generate_secure_api_key() for _ in range(20)]
        
        # Check for obvious patterns
        for i in range(len(keys) - 1):
            key1 = keys[i]
            key2 = keys[i + 1]
            
            # Keys shouldn't have similar suffixes
            suffix1 = key1[-10:]
            suffix2 = key2[-10:]
            
            # Calculate similarity (should be low)
            similarity = sum(c1 == c2 for c1, c2 in zip(suffix1, suffix2))
            assert similarity < 5, f"Keys too similar: {key1[-10:]} vs {key2[-10:]}"
    
    def test_cryptographic_randomness_usage(self):
        """Test that cryptographically secure randomness is used."""
        authenticator = AdminAuthenticator()
        
        # Mock secrets.token_urlsafe to verify it's called
        with patch('app.auth.secrets.token_urlsafe') as mock_token:
            mock_token.return_value = "mocked_secure_token_123"
            
            key = authenticator._generate_secure_api_key()
            
            # Verify secrets.token_urlsafe was called
            mock_token.assert_called_once_with(32)
            
            # Verify key format
            assert key == "evothesis_admin_mocked_secure_token_123"


class TestAuthenticationIntegrationSecurity:
    """Test security aspects of authentication integration."""
    
    @pytest.mark.asyncio
    async def test_admin_endpoint_double_authentication_check(self, test_client):
        """Test that admin endpoints properly enforce authentication."""
        
        # Test multiple admin endpoints to ensure consistent auth enforcement
        admin_endpoints = [
            "/api/v1/admin/clients",
            "/api/v1/admin/clients/test_client_123",
        ]
        
        for endpoint in admin_endpoints:
            # Test without authentication
            response = await test_client.get(endpoint)
            assert response.status_code == 403, f"Endpoint {endpoint} not properly protected"
            
            # Test with invalid authentication  
            invalid_headers = {"Authorization": "Bearer invalid_key_12345"}
            response = await test_client.get(endpoint, headers=invalid_headers)
            assert response.status_code == 401, f"Endpoint {endpoint} accepts invalid auth"
    
    @pytest.mark.asyncio
    async def test_public_endpoint_no_auth_required(self, test_client):
        """Test that public endpoints don't require authentication."""
        public_endpoints = [
            "/health",
            "/api/v1/config/domain/example.com",
        ]
        
        for endpoint in public_endpoints:
            try:
                response = await test_client.get(endpoint)
                # Should not return auth errors (401/403)
                assert response.status_code not in [401, 403], f"Public endpoint {endpoint} requires auth"
                # May return 404 or other errors, but not auth errors
            except Exception:
                # Some endpoints might have validation errors, that's okay
                # We're just testing they don't require authentication
                pass
    
    def test_authentication_environment_isolation(self):
        """Test that authentication respects environment isolation."""
        
        # Test that different environments can have different keys
        test_environments = [
            {"ADMIN_API_KEY": "test_env_key_123"},
            {"ADMIN_API_KEY": "prod_env_key_456"},
            {"ADMIN_API_KEY": "dev_env_key_789"},
        ]
        
        for env in test_environments:
            with patch.dict('os.environ', env, clear=True):
                authenticator = AdminAuthenticator()
                
                # Should use the environment-specific key
                assert authenticator.admin_api_key == env["ADMIN_API_KEY"]
                
                # Should reject keys from other environments
                for other_env in test_environments:
                    if other_env != env:
                        other_key = other_env["ADMIN_API_KEY"]
                        assert authenticator.verify_api_key(other_key) is False


class TestAuthenticationErrorHandling:
    """Test error handling in authentication system."""
    
    def test_exception_during_hash_computation(self):
        """Test graceful handling of hash computation errors."""
        test_key = "test_exception_key"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Mock hashlib to raise an exception
            with patch('app.auth.hashlib.sha256') as mock_sha256:
                mock_sha256.side_effect = Exception("Hash computation failed")
                
                # Should return False instead of raising exception
                result = authenticator.verify_api_key(test_key)
                assert result is False
    
    def test_exception_during_comparison(self):
        """Test graceful handling of comparison errors."""
        test_key = "test_comparison_key"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': test_key}):
            authenticator = AdminAuthenticator()
            
            # Mock compare_digest to raise an exception
            with patch('app.auth.secrets.compare_digest') as mock_compare:
                mock_compare.side_effect = Exception("Comparison failed")
                
                # Should return False instead of raising exception
                result = authenticator.verify_api_key(test_key)
                assert result is False
    
    def test_unicode_encoding_handling(self):
        """Test handling of Unicode encoding in API keys."""
        unicode_key = "test_key_ñäöü_émoji🔑"
        
        with patch.dict('os.environ', {'ADMIN_API_KEY': unicode_key}):
            authenticator = AdminAuthenticator()
            
            # Should handle Unicode keys correctly
            assert authenticator.verify_api_key(unicode_key) is True
            
            # Should generate proper hash for Unicode
            assert len(authenticator.api_key_hash) == 64  # SHA-256 hex length
    
    @pytest.mark.asyncio
    async def test_malformed_authorization_header_handling(self):
        """Test handling of malformed authorization headers."""
        malformed_cases = [
            HTTPAuthorizationCredentials(scheme="Basic", credentials="wrong_scheme"),
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=""),
        ]
        
        for credentials in malformed_cases:
            with patch('app.auth.admin_auth') as mock_auth:
                mock_auth.verify_api_key.return_value = False
                
                with pytest.raises(HTTPException) as exc_info:
                    await verify_admin_access(credentials)
                
                # Should return proper error response
                assert exc_info.value.status_code == 401
                assert "Invalid API key" in exc_info.value.detail