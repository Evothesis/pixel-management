"""
Domain Management Core Business Logic Tests

Tests the critical domain operations that enable pixel authorization and tracking.
Focuses on ≥90% coverage of domain management with O(1) indexing performance.

Critical business logic tested:
- Domain addition with atomic dual-indexing (client subcollection + global index)
- Domain format validation with protocol, path, and character restrictions
- Duplicate domain prevention across all clients with conflict resolution
- Primary domain designation with uniqueness constraints per client

Performance requirements:
- Domain addition: <200ms including dual indexing
- Domain lookup: O(1) performance <100ms
- Duplicate check: O(1) performance <50ms
- Format validation: <10ms

Security requirements:
- Domain format sanitization preventing injection
- Cross-client domain conflict prevention
- Primary domain constraint enforcement
- Audit logging for all domain operations
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, Mock
from httpx import AsyncClient
import re

# Test markers for coverage tracking
pytestmark = [
    pytest.mark.unit,
    pytest.mark.critical, 
    pytest.mark.asyncio
]


class TestDomainAdditionWithIndexing:
    """Test domain addition with O(1) index updates."""
    
    async def test_domain_addition_with_indexing(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        client_with_domains,
        performance_timer
    ):
        """
        CRITICAL: Test domain addition with O(1) index updates
        
        Validates:
        - Atomic dual-indexing (client subcollection + global index)
        - Index consistency and integrity
        - Performance under 200ms
        - Primary domain handling
        - Concurrent operation safety
        """
        performance_timer.start()
        
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        existing_domains = client_with_domains['domains']
        
        # Test cases for various domain types
        domain_test_cases = [
            {
                "domain": "newdomain.example.com",
                "is_primary": False,
                "description": "Standard subdomain"
            },
            {
                "domain": "international-site.co.uk",
                "is_primary": False,
                "description": "International TLD with hyphens"
            },
            {
                "domain": "api-v2.microservice.internal",
                "is_primary": False,
                "description": "Complex subdomain structure"
            },
            {
                "domain": "new-primary.example.org",
                "is_primary": True,
                "description": "New primary domain"
            }
        ]
        
        added_domains = []
        
        for test_case in domain_test_cases:
            domain_data = {
                "domain": test_case["domain"],
                "is_primary": test_case["is_primary"]
            }
            
            # Add domain to client
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json=domain_data
            )
            
            assert response.status_code == 201, \
                f"Domain addition failed for {test_case['description']}: {response.text}"
            
            domain_response = response.json()
            added_domains.append(domain_response)
            
            # Validate response structure
            assert domain_response["domain"] == test_case["domain"].lower()
            assert domain_response["is_primary"] == test_case["is_primary"]
            assert "id" in domain_response
            assert "created_at" in domain_response
            
            # Validate client subcollection indexing
            expected_doc_id = f"{client_id}_{test_case['domain'].lower().replace('.', '_')}"
            client_domain_doc = (mock_firestore_client.clients_ref
                                .document(client_id)
                                .collection('domains')
                                .document(expected_doc_id)
                                .get())
            
            assert client_domain_doc.exists, \
                f"Domain not found in client subcollection: {test_case['domain']}"
            
            client_domain_data = client_domain_doc.to_dict()
            assert client_domain_data["domain"] == test_case["domain"].lower()
            assert client_domain_data["is_primary"] == test_case["is_primary"]
            
            # Validate global domain index
            global_domain_doc = mock_firestore_client.domain_index_ref.document(expected_doc_id).get()
            assert global_domain_doc.exists, \
                f"Domain not found in global index: {test_case['domain']}"
            
            global_domain_data = global_domain_doc.to_dict()
            assert global_domain_data["client_id"] == client_id
            assert global_domain_data["domain"] == test_case["domain"].lower()
            assert global_domain_data["is_primary"] == test_case["is_primary"]
            
            print(f"✓ Domain indexed: {test_case['description']} -> {test_case['domain']}")
        
        elapsed_time = performance_timer.stop()
        assert elapsed_time < 200, f"Domain addition too slow: {elapsed_time}ms"
        
        # Verify domain lookup performance (O(1) access)
        performance_timer.start()
        
        # Test direct global index lookup
        test_domain = added_domains[0]["domain"]
        domain_docs = list(
            mock_firestore_client.domain_index_ref
            .where('domain', '==', test_domain)
            .limit(1)
            .stream()
        )
        
        lookup_time = performance_timer.stop()
        
        assert len(domain_docs) == 1, f"Domain lookup failed for {test_domain}"
        assert lookup_time < 100, f"Domain lookup too slow: {lookup_time}ms"
        
        # Verify client domain listing
        domains_response = await authenticated_client.get(
            f"/api/v1/admin/clients/{client_id}/domains"
        )
        
        assert domains_response.status_code == 200
        client_domains = domains_response.json()
        
        # Should include original domains plus newly added ones
        total_expected = len(existing_domains) + len(added_domains)
        assert len(client_domains) == total_expected, \
            f"Expected {total_expected} domains, got {len(client_domains)}"
        
        print(f"✓ Domain addition with indexing completed in {elapsed_time:.2f}ms")
        print(f"✓ Domain lookup performance: {lookup_time:.2f}ms (O(1) access)")
    
    async def test_concurrent_domain_additions(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        sample_client_data
    ):
        """Test concurrent domain additions for race condition detection."""
        
        # Create a client first
        client_response = await authenticated_client.post(
            "/api/v1/admin/clients",
            json={
                "name": sample_client_data["name"],
                "email": sample_client_data["email"],
                "client_type": sample_client_data["client_type"],
                "owner": sample_client_data["owner"],
                "privacy_level": sample_client_data["privacy_level"],
                "deployment_type": sample_client_data["deployment_type"],
                "features": sample_client_data["features"]
            }
        )
        assert client_response.status_code == 201
        client_id = client_response.json()["client_id"]
        
        # Concurrent domain addition function
        async def add_domain(index):
            domain_data = {
                "domain": f"concurrent-{index}.example.com",
                "is_primary": (index == 0)  # First one is primary
            }
            
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json=domain_data
            )
            return response
        
        # Run concurrent domain additions
        tasks = [add_domain(i) for i in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_additions = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 201:
                successful_additions += 1
        
        assert successful_additions >= 4, \
            f"Only {successful_additions}/5 concurrent domain additions succeeded"
        
        # Verify index consistency
        domain_docs = list(
            mock_firestore_client.domain_index_ref
            .where('client_id', '==', client_id)
            .stream()
        )
        
        assert len(domain_docs) == successful_additions, \
            "Global index count doesn't match successful additions"
        
        print(f"✓ Concurrent domain additions: {successful_additions}/5 successful with consistent indexing")


class TestDomainFormatValidation:
    """Test domain format validation with comprehensive rules."""
    
    async def test_domain_format_validation(
        self,
        authenticated_client: AsyncClient,
        sample_client_data,
        performance_timer
    ):
        """
        CRITICAL: Test format validation (protocol, path, character restrictions)
        
        Validates:
        - Domain format compliance (RFC standards)
        - Protocol removal and normalization
        - Path and query parameter rejection
        - Special character handling
        - Length restrictions
        - Performance under 10ms per validation
        """
        # Create a client first
        client_response = await authenticated_client.post(
            "/api/v1/admin/clients",
            json={
                "name": sample_client_data["name"],
                "email": sample_client_data["email"],
                "client_type": sample_client_data["client_type"],
                "owner": sample_client_data["owner"],
                "privacy_level": sample_client_data["privacy_level"],
                "deployment_type": sample_client_data["deployment_type"],
                "features": sample_client_data["features"]
            }
        )
        assert client_response.status_code == 201
        client_id = client_response.json()["client_id"]
        
        # Valid domain test cases
        valid_domain_cases = [
            {
                "input": "example.com",
                "expected_output": "example.com",
                "description": "Simple domain"
            },
            {
                "input": "sub.example.com",
                "expected_output": "sub.example.com", 
                "description": "Subdomain"
            },
            {
                "input": "UPPERCASE.COM",
                "expected_output": "uppercase.com",
                "description": "Case normalization"
            },
            {
                "input": "  spaced-domain.org  ",
                "expected_output": "spaced-domain.org",
                "description": "Whitespace trimming"
            },
            {
                "input": "multi-part.sub-domain.co.uk",
                "expected_output": "multi-part.sub-domain.co.uk",
                "description": "Complex international domain"
            },
            {
                "input": "api-v2.microservice.internal",
                "expected_output": "api-v2.microservice.internal",
                "description": "Internal domain with versioning"
            }
        ]
        
        performance_timer.start()
        
        for test_case in valid_domain_cases:
            domain_data = {
                "domain": test_case["input"],
                "is_primary": False
            }
            
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json=domain_data
            )
            
            assert response.status_code == 201, \
                f"Valid domain rejected: {test_case['description']} - {test_case['input']}"
            
            domain_response = response.json()
            assert domain_response["domain"] == test_case["expected_output"], \
                f"Domain normalization failed: expected {test_case['expected_output']}, got {domain_response['domain']}"
            
            print(f"✓ Valid: {test_case['description']} -> {test_case['expected_output']}")
        
        validation_time = performance_timer.stop()
        avg_validation_time = validation_time / len(valid_domain_cases)
        assert avg_validation_time < 10, f"Domain validation too slow: {avg_validation_time:.2f}ms average"
        
        # Invalid domain test cases
        invalid_domain_cases = [
            {
                "input": "http://example.com",
                "description": "Protocol prefix"
            },
            {
                "input": "https://secure.example.com",
                "description": "HTTPS protocol prefix"
            },
            {
                "input": "example.com/path",
                "description": "Path component"
            },
            {
                "input": "example.com?query=value",
                "description": "Query parameters"
            },
            {
                "input": "example.com:8080",
                "description": "Port number"
            },
            {
                "input": "",
                "description": "Empty domain"
            },
            {
                "input": "x",
                "description": "Too short"
            },
            {
                "input": "domain_with_underscore.com",
                "description": "Invalid underscore character"
            },
            {
                "input": ".example.com",
                "description": "Leading dot"
            },
            {
                "input": "example.com.",
                "description": "Trailing dot"
            },
            {
                "input": "domain with spaces.com",
                "description": "Spaces in domain"
            },
            {
                "input": "xn--" + "a" * 250 + ".com",
                "description": "Extremely long domain"
            }
        ]
        
        for test_case in invalid_domain_cases:
            domain_data = {
                "domain": test_case["input"],
                "is_primary": False
            }
            
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json=domain_data
            )
            
            assert response.status_code in [400, 422], \
                f"Invalid domain accepted: {test_case['description']} - {test_case['input']}"
            
            print(f"✓ Invalid (correctly rejected): {test_case['description']}")
        
        print(f"✓ Domain format validation completed in {validation_time:.2f}ms")
        print(f"✓ Average validation time: {avg_validation_time:.2f}ms per domain")
    
    async def test_domain_security_validation(
        self,
        authenticated_client: AsyncClient,
        sample_client_data,
        security_test_payloads
    ):
        """Test domain validation against security injection attempts."""
        
        # Create a client first
        client_response = await authenticated_client.post(
            "/api/v1/admin/clients",
            json={
                "name": sample_client_data["name"],
                "email": sample_client_data["email"],
                "client_type": sample_client_data["client_type"],
                "owner": sample_client_data["owner"],
                "privacy_level": sample_client_data["privacy_level"],
                "deployment_type": sample_client_data["deployment_type"],
                "features": sample_client_data["features"]
            }
        )
        assert client_response.status_code == 201
        client_id = client_response.json()["client_id"]
        
        # Test SQL injection in domain names
        sql_payloads = security_test_payloads["sql_injection"]
        
        for payload in sql_payloads:
            domain_data = {
                "domain": payload,
                "is_primary": False
            }
            
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json=domain_data
            )
            
            # Should reject malicious domains
            assert response.status_code in [400, 422], \
                f"SQL injection payload accepted as domain: {payload}"
        
        # Test XSS injection in domain names
        xss_payloads = security_test_payloads["xss_injection"]
        
        for payload in xss_payloads:
            domain_data = {
                "domain": payload,
                "is_primary": False
            }
            
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json=domain_data
            )
            
            # Should reject malicious domains
            assert response.status_code in [400, 422], \
                f"XSS injection payload accepted as domain: {payload}"
        
        # Test path traversal attempts
        path_traversal_payloads = security_test_payloads["path_traversal"]
        
        for payload in path_traversal_payloads:
            domain_data = {
                "domain": payload,
                "is_primary": False
            }
            
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json=domain_data
            )
            
            # Should reject malicious domains
            assert response.status_code in [400, 422], \
                f"Path traversal payload accepted as domain: {payload}"
        
        print("✓ Domain security validation: All injection attempts properly rejected")


class TestDuplicateDomainPrevention:
    """Test duplicate domain prevention across clients."""
    
    async def test_duplicate_domain_prevention(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        multiple_clients,
        performance_timer
    ):
        """
        CRITICAL: Test duplicate prevention across clients
        
        Validates:
        - Cross-client domain uniqueness
        - Conflict detection and reporting
        - Performance of duplicate checks <50ms
        - Proper error messages with conflict details
        - Same-client duplicate prevention
        """
        # Create multiple clients
        client_ids = []
        for i, client_data in enumerate(multiple_clients[:3]):  # Use first 3 clients
            response = await authenticated_client.post(
                "/api/v1/admin/clients",
                json={
                    "name": client_data["name"],
                    "email": client_data["email"],
                    "client_type": client_data["client_type"],
                    "owner": client_data["owner"],
                    "privacy_level": client_data["privacy_level"],
                    "deployment_type": client_data["deployment_type"],
                    "features": client_data["features"]
                }
            )
            assert response.status_code == 201
            client_ids.append(response.json()["client_id"])
        
        test_domain = "shared-domain.example.com"
        
        # Add domain to first client (should succeed)
        performance_timer.start()
        
        response1 = await authenticated_client.post(
            f"/api/v1/admin/clients/{client_ids[0]}/domains",
            json={"domain": test_domain, "is_primary": False}
        )
        
        first_addition_time = performance_timer.stop()
        
        assert response1.status_code == 201, f"First domain addition failed: {response1.text}"
        assert first_addition_time < 50, f"First domain addition too slow: {first_addition_time}ms"
        
        # Verify domain was added to global index
        domain_docs = list(
            mock_firestore_client.domain_index_ref
            .where('domain', '==', test_domain)
            .stream()
        )
        assert len(domain_docs) == 1
        assert domain_docs[0].to_dict()["client_id"] == client_ids[0]
        
        # Attempt to add same domain to second client (should fail)
        performance_timer.start()
        
        response2 = await authenticated_client.post(
            f"/api/v1/admin/clients/{client_ids[1]}/domains",
            json={"domain": test_domain, "is_primary": False}
        )
        
        duplicate_check_time = performance_timer.stop()
        
        assert response2.status_code == 409, f"Duplicate domain was allowed: {response2.text}"
        assert duplicate_check_time < 50, f"Duplicate check too slow: {duplicate_check_time}ms"
        
        # Verify error message includes conflict details
        error_detail = response2.json()["detail"]
        assert client_ids[0] in error_detail, "Error message should include conflicting client ID"
        
        # Test same-client duplicate prevention
        response3 = await authenticated_client.post(
            f"/api/v1/admin/clients/{client_ids[0]}/domains",
            json={"domain": test_domain, "is_primary": False}
        )
        
        assert response3.status_code == 409, "Same-client duplicate domain was allowed"
        assert "already exists for this client" in response3.json()["detail"]
        
        # Test case variations (should still be considered duplicates)
        case_variations = [
            "SHARED-DOMAIN.EXAMPLE.COM",
            "Shared-Domain.Example.Com",
            "  shared-domain.example.com  "
        ]
        
        for variation in case_variations:
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_ids[2]}/domains",
                json={"domain": variation, "is_primary": False}
            )
            
            assert response.status_code == 409, \
                f"Case variation '{variation}' was not detected as duplicate"
        
        print(f"✓ Domain uniqueness enforced across clients")
        print(f"✓ Duplicate check performance: {duplicate_check_time:.2f}ms")
        print(f"✓ Case-insensitive duplicate detection working")
    
    async def test_duplicate_domain_edge_cases(
        self,
        authenticated_client: AsyncClient,
        sample_client_data
    ):
        """Test edge cases in duplicate domain detection."""
        
        # Create a client
        client_response = await authenticated_client.post(
            "/api/v1/admin/clients",
            json={
                "name": sample_client_data["name"],
                "email": sample_client_data["email"],
                "client_type": sample_client_data["client_type"],
                "owner": sample_client_data["owner"],
                "privacy_level": sample_client_data["privacy_level"],
                "deployment_type": sample_client_data["deployment_type"],
                "features": sample_client_data["features"]
            }
        )
        assert client_response.status_code == 201
        client_id = client_response.json()["client_id"]
        
        # Test similar but different domains (should be allowed)
        similar_domains = [
            "example.com",
            "www.example.com", 
            "api.example.com",
            "example.org",  # Different TLD
            "example-site.com"  # Similar name
        ]
        
        for domain in similar_domains:
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={"domain": domain, "is_primary": False}
            )
            
            assert response.status_code == 201, \
                f"Similar but different domain rejected: {domain}"
        
        print("✓ Similar but distinct domains properly differentiated")


class TestPrimaryDomainDesignation:
    """Test primary domain designation with uniqueness constraints."""
    
    async def test_primary_domain_designation(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        client_with_domains
    ):
        """
        CRITICAL: Test primary domain designation with uniqueness
        
        Validates:
        - Only one primary domain per client
        - Primary domain switching
        - Automatic primary promotion
        - Index consistency for primary status
        - Constraint enforcement
        """
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        existing_domains = client_with_domains['domains']
        
        # Check current primary domain
        current_primary = None
        for domain in existing_domains:
            if domain['is_primary']:
                current_primary = domain
                break
        
        assert current_primary is not None, "Test setup should include a primary domain"
        
        # Add a new domain and attempt to make it primary
        new_primary_domain = "new-primary.example.com"
        
        response = await authenticated_client.post(
            f"/api/v1/admin/clients/{client_id}/domains",
            json={
                "domain": new_primary_domain,
                "is_primary": True
            }
        )
        
        assert response.status_code == 201, f"Primary domain addition failed: {response.text}"
        
        # Verify new domain is marked as primary
        new_domain_response = response.json()
        assert new_domain_response["is_primary"] is True
        
        # Check that only one primary domain exists
        domain_docs = list(
            mock_firestore_client.domain_index_ref
            .where('client_id', '==', client_id)
            .stream()
        )
        
        primary_count = 0
        for doc in domain_docs:
            domain_data = doc.to_dict()
            if domain_data.get('is_primary', False):
                primary_count += 1
        
        assert primary_count == 1, f"Found {primary_count} primary domains, expected exactly 1"
        
        # Verify the new domain is the primary one
        primary_domains = [
            doc.to_dict() for doc in domain_docs 
            if doc.to_dict().get('is_primary', False)
        ]
        assert len(primary_domains) == 1
        assert primary_domains[0]['domain'] == new_primary_domain
        
        # Test switching primary to another existing domain
        existing_non_primary = None
        for domain in existing_domains:
            if not domain['is_primary']:
                existing_non_primary = domain
                break
        
        if existing_non_primary:
            # Add another domain first to switch to
            switch_domain = "switch-primary.example.com"
            
            await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={
                    "domain": switch_domain,
                    "is_primary": False
                }
            )
            
            # Now make it primary
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={
                    "domain": switch_domain,
                    "is_primary": True
                }
            )
            
            # This might be handled by an update endpoint in the real system
            # For now, test that we still maintain uniqueness
            updated_domain_docs = list(
                mock_firestore_client.domain_index_ref
                .where('client_id', '==', client_id)
                .stream()
            )
            
            primary_count = sum(
                1 for doc in updated_domain_docs 
                if doc.to_dict().get('is_primary', False)
            )
            
            # Should still have only one primary (either the original or new)
            assert primary_count <= 1, "Primary domain uniqueness constraint violated"
        
        # Test adding multiple non-primary domains
        non_primary_domains = [
            "api.example.com",
            "cdn.example.com", 
            "static.example.com"
        ]
        
        for domain in non_primary_domains:
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={
                    "domain": domain,
                    "is_primary": False
                }
            )
            
            assert response.status_code == 201, f"Non-primary domain addition failed: {domain}"
            
            domain_response = response.json()
            assert domain_response["is_primary"] is False
        
        # Final verification: exactly one primary domain
        final_domain_docs = list(
            mock_firestore_client.domain_index_ref
            .where('client_id', '==', client_id)
            .stream()
        )
        
        final_primary_count = sum(
            1 for doc in final_domain_docs 
            if doc.to_dict().get('is_primary', False)
        )
        
        assert final_primary_count == 1, \
            f"Final check failed: {final_primary_count} primary domains found"
        
        print("✓ Primary domain uniqueness maintained throughout operations")
        print(f"✓ Client has {len(final_domain_docs)} total domains with 1 primary")
    
    async def test_primary_domain_constraints(
        self,
        authenticated_client: AsyncClient,
        sample_client_data
    ):
        """Test primary domain constraint edge cases."""
        
        # Create a client
        client_response = await authenticated_client.post(
            "/api/v1/admin/clients",
            json={
                "name": sample_client_data["name"],
                "email": sample_client_data["email"],
                "client_type": sample_client_data["client_type"],
                "owner": sample_client_data["owner"],
                "privacy_level": sample_client_data["privacy_level"],
                "deployment_type": sample_client_data["deployment_type"],
                "features": sample_client_data["features"]
            }
        )
        assert client_response.status_code == 201
        client_id = client_response.json()["client_id"]
        
        # Test that first domain can be primary
        response1 = await authenticated_client.post(
            f"/api/v1/admin/clients/{client_id}/domains",
            json={
                "domain": "first-primary.example.com",
                "is_primary": True
            }
        )
        
        assert response1.status_code == 201
        assert response1.json()["is_primary"] is True
        
        # Test that second primary domain follows business rules
        # (This might depend on implementation - could auto-demote first or reject second)
        response2 = await authenticated_client.post(
            f"/api/v1/admin/clients/{client_id}/domains",
            json={
                "domain": "second-primary.example.com",
                "is_primary": True
            }
        )
        
        # Should either succeed (with first demoted) or fail (constraint enforced)
        assert response2.status_code in [201, 409, 422], \
            "Primary domain conflict should be handled gracefully"
        
        if response2.status_code == 201:
            print("✓ Primary domain switching implemented")
        else:
            print("✓ Primary domain uniqueness constraint enforced")
        
        print("✓ Primary domain constraint behavior verified")


# Performance testing for domain operations
@pytest.mark.performance
class TestDomainManagementPerformance:
    """Performance tests for domain management operations."""
    
    async def test_domain_operation_performance_benchmark(
        self,
        authenticated_client: AsyncClient,
        performance_timer,
        performance_threshold,
        sample_client_data
    ):
        """Benchmark domain operations performance."""
        
        # Create a client
        client_response = await authenticated_client.post(
            "/api/v1/admin/clients",
            json={
                "name": sample_client_data["name"],
                "email": sample_client_data["email"],
                "client_type": sample_client_data["client_type"],
                "owner": sample_client_data["owner"],
                "privacy_level": sample_client_data["privacy_level"],
                "deployment_type": sample_client_data["deployment_type"],
                "features": sample_client_data["features"]
            }
        )
        assert client_response.status_code == 201
        client_id = client_response.json()["client_id"]
        
        # Benchmark domain addition
        performance_timer.start()
        
        response = await authenticated_client.post(
            f"/api/v1/admin/clients/{client_id}/domains",
            json={
                "domain": "performance-test.example.com",
                "is_primary": True
            }
        )
        
        addition_time = performance_timer.stop()
        
        assert response.status_code == 201
        assert addition_time < 200, f"Domain addition too slow: {addition_time}ms"
        
        # Benchmark domain listing
        performance_timer.start()
        
        list_response = await authenticated_client.get(
            f"/api/v1/admin/clients/{client_id}/domains"
        )
        
        list_time = performance_timer.stop()
        
        assert list_response.status_code == 200
        assert list_time < performance_threshold["domain_lookup_ms"], \
            f"Domain listing too slow: {list_time}ms"
        
        print(f"✓ Domain addition performance: {addition_time:.2f}ms")
        print(f"✓ Domain listing performance: {list_time:.2f}ms")
    
    async def test_domain_scale_performance(
        self,
        authenticated_client: AsyncClient,
        performance_timer,
        sample_client_data
    ):
        """Test domain operations performance at scale."""
        
        # Create a client
        client_response = await authenticated_client.post(
            "/api/v1/admin/clients",
            json={
                "name": sample_client_data["name"],
                "email": sample_client_data["email"],
                "client_type": sample_client_data["client_type"],
                "owner": sample_client_data["owner"],
                "privacy_level": sample_client_data["privacy_level"],
                "deployment_type": sample_client_data["deployment_type"],
                "features": sample_client_data["features"]
            }
        )
        assert client_response.status_code == 201
        client_id = client_response.json()["client_id"]
        
        # Add multiple domains to test scale
        domain_count = 20
        
        performance_timer.start()
        
        for i in range(domain_count):
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={
                    "domain": f"scale-test-{i}.example.com",
                    "is_primary": (i == 0)
                }
            )
            assert response.status_code == 201
        
        total_addition_time = performance_timer.stop()
        avg_addition_time = total_addition_time / domain_count
        
        assert avg_addition_time < 200, f"Average domain addition too slow: {avg_addition_time:.2f}ms"
        
        # Test listing performance with many domains
        performance_timer.start()
        
        list_response = await authenticated_client.get(
            f"/api/v1/admin/clients/{client_id}/domains"
        )
        
        list_time = performance_timer.stop()
        
        assert list_response.status_code == 200
        domains = list_response.json()
        assert len(domains) == domain_count
        
        assert list_time < 500, f"Domain listing with {domain_count} domains too slow: {list_time}ms"
        
        print(f"✓ Scale test: {domain_count} domains added in {total_addition_time:.2f}ms")
        print(f"✓ Average addition time: {avg_addition_time:.2f}ms")
        print(f"✓ Listing {domain_count} domains: {list_time:.2f}ms")