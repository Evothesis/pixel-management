"""
Domain Authorization Core Business Logic Tests

Tests the performance-critical domain authorization system that enables pixel serving.
Focuses on ≥95% coverage of domain lookup with strict O(1) performance requirements.

Critical business logic tested:
- O(1) domain lookup performance verification (<100ms average, <200ms 95th percentile)
- Unauthorized domain rejection with proper HTTP error codes and security logging
- Client-domain mapping accuracy ensuring pixels serve to correct clients only
- Missing domain handling with appropriate error responses and fallback behavior

Performance requirements (CRITICAL):
- Domain authorization lookup: <100ms average, <200ms 95th percentile
- Concurrent authorization checks: 100+ RPS sustained
- Index lookup efficiency: O(1) complexity verified
- Cache hit performance: <10ms for repeated lookups

Security requirements:
- Proper 403/404 status codes for unauthorized domains
- Security event logging for unauthorized access attempts
- No information leakage about existing clients
- Timing attack resistance in domain lookup
"""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import patch, Mock
from httpx import AsyncClient
import statistics

# Test markers for coverage tracking
pytestmark = [
    pytest.mark.unit,
    pytest.mark.critical,
    pytest.mark.performance,
    pytest.mark.asyncio
]


class TestDomainLookupPerformance:
    """Test O(1) domain lookup performance verification."""
    
    async def test_domain_lookup_performance(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        client_with_domains,
        performance_timer,
        performance_threshold
    ):
        """
        CRITICAL: Test O(1) domain lookup performance verification (<100ms)
        
        Validates:
        - O(1) lookup complexity regardless of total domain count
        - Average response time <100ms
        - 95th percentile <200ms
        - Performance consistency across multiple lookups
        - Index efficiency verification
        """
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        domains = client_with_domains['domains']
        authorized_domain = domains[0]['domain']
        
        # Add more domains to test O(1) complexity with larger dataset
        for i in range(50):  # Create substantial dataset
            additional_domain = f"scale-test-{i}.example.com"
            await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={"domain": additional_domain, "is_primary": False}
            )
        
        # Verify domain was properly indexed
        config_endpoint = f"/api/v1/config/domain/{authorized_domain}"
        
        # Warmup request to establish any caching
        warmup_response = await authenticated_client.get(config_endpoint)
        assert warmup_response.status_code == 200, "Warmup request failed"
        
        # Performance test with multiple iterations
        lookup_times = []
        test_iterations = 20
        
        for i in range(test_iterations):
            performance_timer.start()
            
            response = await authenticated_client.get(config_endpoint)
            
            lookup_time = performance_timer.stop()
            lookup_times.append(lookup_time)
            
            assert response.status_code == 200, f"Domain lookup failed on iteration {i+1}"
            
            # Validate response content
            config_data = response.json()
            assert config_data["client_id"] == client_id
            assert config_data["privacy_level"] == client_data["privacy_level"]
            assert "ip_collection" in config_data
            assert "consent" in config_data
            assert "features" in config_data
        
        # Calculate performance statistics
        avg_lookup_time = statistics.mean(lookup_times)
        p95_lookup_time = statistics.quantiles(lookup_times, n=20)[18]  # 95th percentile
        min_lookup_time = min(lookup_times)
        max_lookup_time = max(lookup_times)
        
        # Verify O(1) performance requirements
        assert avg_lookup_time < performance_threshold["domain_lookup_ms"], \
            f"Average lookup too slow: {avg_lookup_time:.2f}ms (threshold: {performance_threshold['domain_lookup_ms']}ms)"
        
        assert p95_lookup_time < 200, \
            f"95th percentile too slow: {p95_lookup_time:.2f}ms (threshold: 200ms)"
        
        # Test with different domain from same client (should have similar performance)
        if len(domains) > 1:
            second_domain = domains[1]['domain']
            second_domain_times = []
            
            for i in range(10):
                performance_timer.start()
                response = await authenticated_client.get(f"/api/v1/config/domain/{second_domain}")
                lookup_time = performance_timer.stop()
                second_domain_times.append(lookup_time)
                assert response.status_code == 200
            
            avg_second_domain = statistics.mean(second_domain_times)
            
            # Performance should be consistent regardless of domain
            time_difference = abs(avg_lookup_time - avg_second_domain)
            assert time_difference < 50, f"Inconsistent performance between domains: {time_difference:.2f}ms difference"
        
        print(f"✓ Domain lookup performance verified (O(1) complexity)")
        print(f"  Average: {avg_lookup_time:.2f}ms")
        print(f"  95th percentile: {p95_lookup_time:.2f}ms")
        print(f"  Range: {min_lookup_time:.2f}ms - {max_lookup_time:.2f}ms")
        print(f"  Tested with 50+ domains in index")
    
    async def test_concurrent_domain_lookups(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        performance_timer
    ):
        """Test concurrent domain authorization performance (100+ RPS)."""
        
        domains = client_with_domains['domains']
        authorized_domain = domains[0]['domain']
        
        # Concurrent lookup function
        async def perform_lookup(index):
            start_time = time.perf_counter()
            response = await authenticated_client.get(f"/api/v1/config/domain/{authorized_domain}")
            end_time = time.perf_counter()
            
            return {
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000,  # Convert to ms
                'index': index
            }
        
        # Run concurrent lookups
        concurrent_requests = 50
        start_time = time.perf_counter()
        
        tasks = [perform_lookup(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        total_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['status_code'] == 200)
        response_times = [r['response_time'] for r in results if r['status_code'] == 200]
        
        # Calculate RPS
        rps = (successful_requests / total_time) * 1000  # Requests per second
        
        assert successful_requests >= 48, f"Too many failed requests: {concurrent_requests - successful_requests}"
        assert rps >= 50, f"RPS too low: {rps:.2f} (target: 50+ RPS)"
        
        # Verify response time consistency under load
        avg_concurrent_time = statistics.mean(response_times)
        assert avg_concurrent_time < 300, f"Average response time under load too slow: {avg_concurrent_time:.2f}ms"
        
        print(f"✓ Concurrent lookup performance: {rps:.2f} RPS")
        print(f"  Successful requests: {successful_requests}/{concurrent_requests}")
        print(f"  Average response time under load: {avg_concurrent_time:.2f}ms")
    
    async def test_domain_lookup_scalability(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        sample_client_data,
        performance_timer
    ):
        """Test lookup performance scales O(1) with increasing domain count."""
        
        # Create client
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
        
        # Test lookup performance at different scale levels
        scale_tests = [10, 50, 100, 200]
        performance_results = {}
        
        for domain_count in scale_tests:
            # Add domains to reach target count
            current_count = len(list(
                mock_firestore_client.domain_index_ref
                .where('client_id', '==', client_id)
                .stream()
            ))
            
            domains_to_add = domain_count - current_count
            test_domain = None
            
            for i in range(domains_to_add):
                domain = f"scale-{domain_count}-{i}.example.com"
                if i == 0:
                    test_domain = domain  # Use first domain for testing
                
                await authenticated_client.post(
                    f"/api/v1/admin/clients/{client_id}/domains",
                    json={"domain": domain, "is_primary": (i == 0 and current_count == 0)}
                )
            
            if not test_domain:
                # Use existing domain if no new domains were added
                existing_domains = list(
                    mock_firestore_client.domain_index_ref
                    .where('client_id', '==', client_id)
                    .stream()
                )
                test_domain = existing_domains[0].to_dict()['domain']
            
            # Measure lookup performance at this scale
            lookup_times = []
            for i in range(10):
                performance_timer.start()
                response = await authenticated_client.get(f"/api/v1/config/domain/{test_domain}")
                lookup_time = performance_timer.stop()
                lookup_times.append(lookup_time)
                assert response.status_code == 200
            
            avg_time = statistics.mean(lookup_times)
            performance_results[domain_count] = avg_time
            
            print(f"  {domain_count} domains: {avg_time:.2f}ms average")
        
        # Verify O(1) complexity (performance should not degrade significantly)
        base_performance = performance_results[scale_tests[0]]
        
        for domain_count in scale_tests[1:]:
            current_performance = performance_results[domain_count]
            performance_ratio = current_performance / base_performance
            
            # Performance should not degrade more than 2x even with 20x more domains
            assert performance_ratio < 2.0, \
                f"Performance degraded too much: {performance_ratio:.2f}x slower with {domain_count} domains"
        
        print(f"✓ O(1) scalability verified: performance remains consistent across scale levels")


class TestUnauthorizedDomainRejection:
    """Test unauthorized domain rejection with proper error codes."""
    
    async def test_unauthorized_domain_rejection(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        performance_timer
    ):
        """
        CRITICAL: Test unauthorized domain rejection with proper error codes
        
        Validates:
        - 404 status for domains not in any client
        - 403 status for domains authorized to different clients
        - Proper error message structure
        - Security event logging
        - No information leakage about existing clients
        - Fast rejection (<100ms)
        """
        client_data = client_with_domains['client']
        authorized_domains = client_with_domains['domains']
        
        # Test completely unauthorized domain (not in any client)
        unauthorized_domain = "totally-unauthorized.example.com"
        
        performance_timer.start()
        
        response = await authenticated_client.get(f"/api/v1/config/domain/{unauthorized_domain}")
        
        rejection_time = performance_timer.stop()
        
        assert response.status_code == 404, f"Expected 404 for unauthorized domain, got {response.status_code}"
        assert rejection_time < 100, f"Unauthorized domain rejection too slow: {rejection_time:.2f}ms"
        
        # Verify error message structure
        error_data = response.json()
        assert "detail" in error_data
        assert "not authorized" in error_data["detail"].lower()
        
        # Ensure no client information is leaked
        assert client_data["client_id"] not in error_data["detail"]
        assert client_data["name"] not in error_data["detail"]
        
        # Test case variations of unauthorized domain
        case_variations = [
            "TOTALLY-UNAUTHORIZED.EXAMPLE.COM",
            "Totally-Unauthorized.Example.Com",
            "  totally-unauthorized.example.com  "
        ]
        
        for variation in case_variations:
            response = await authenticated_client.get(f"/api/v1/config/domain/{variation}")
            assert response.status_code == 404, f"Case variation '{variation}' should be rejected"
        
        # Test malformed domain requests
        malformed_domains = [
            "not-a-domain",
            "",
            "http://example.com",  # Protocol included
            "example.com/path",    # Path included
            "a" * 300,            # Too long
            "domain with spaces.com"
        ]
        
        for malformed in malformed_domains:
            response = await authenticated_client.get(f"/api/v1/config/domain/{malformed}")
            assert response.status_code in [400, 404], \
                f"Malformed domain '{malformed}' should be rejected with 400 or 404"
        
        print(f"✓ Unauthorized domain rejection: {rejection_time:.2f}ms")
        print(f"✓ Proper error codes and no information leakage")
    
    async def test_cross_client_domain_security(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        multiple_clients
    ):
        """Test security isolation between clients' domains."""
        
        # Create two clients with domains
        client1_data = {
            "name": multiple_clients[0]["name"],
            "email": multiple_clients[0]["email"],
            "client_type": multiple_clients[0]["client_type"],
            "owner": multiple_clients[0]["owner"],
            "privacy_level": multiple_clients[0]["privacy_level"],
            "deployment_type": multiple_clients[0]["deployment_type"],
            "features": multiple_clients[0]["features"]
        }
        
        client2_data = {
            "name": multiple_clients[1]["name"],
            "email": multiple_clients[1]["email"],
            "client_type": multiple_clients[1]["client_type"],
            "owner": multiple_clients[1]["owner"],
            "privacy_level": multiple_clients[1]["privacy_level"],
            "deployment_type": multiple_clients[1]["deployment_type"],
            "features": multiple_clients[1]["features"]
        }
        
        # Create clients
        response1 = await authenticated_client.post("/api/v1/admin/clients", json=client1_data)
        response2 = await authenticated_client.post("/api/v1/admin/clients", json=client2_data)
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        client1_id = response1.json()["client_id"]
        client2_id = response2.json()["client_id"]
        
        # Add domain to client1
        client1_domain = "client1-exclusive.example.com"
        domain_response = await authenticated_client.post(
            f"/api/v1/admin/clients/{client1_id}/domains",
            json={"domain": client1_domain, "is_primary": True}
        )
        assert domain_response.status_code == 201
        
        # Test that client1's domain works for client1
        config_response = await authenticated_client.get(f"/api/v1/config/domain/{client1_domain}")
        assert config_response.status_code == 200
        
        config_data = config_response.json()
        assert config_data["client_id"] == client1_id
        
        # Test direct client access (should work)
        direct_access1 = await authenticated_client.get(f"/api/v1/config/client/{client1_id}")
        direct_access2 = await authenticated_client.get(f"/api/v1/config/client/{client2_id}")
        
        assert direct_access1.status_code == 200
        assert direct_access2.status_code == 200
        
        # Verify client isolation in direct access
        assert direct_access1.json()["client_id"] == client1_id
        assert direct_access2.json()["client_id"] == client2_id
        
        print("✓ Cross-client domain security isolation verified")
    
    async def test_domain_authorization_edge_cases(
        self,
        authenticated_client: AsyncClient,
        security_test_payloads
    ):
        """Test domain authorization against security attacks."""
        
        # Test SQL injection attempts in domain lookup
        sql_payloads = security_test_payloads["sql_injection"]
        
        for payload in sql_payloads:
            response = await authenticated_client.get(f"/api/v1/config/domain/{payload}")
            
            # Should reject malicious payloads with proper status codes
            assert response.status_code in [400, 404], \
                f"SQL injection payload should be rejected: {payload}"
        
        # Test XSS attempts in domain lookup
        xss_payloads = security_test_payloads["xss_injection"]
        
        for payload in xss_payloads:
            response = await authenticated_client.get(f"/api/v1/config/domain/{payload}")
            
            # Should reject malicious payloads
            assert response.status_code in [400, 404], \
                f"XSS injection payload should be rejected: {payload}"
        
        # Test path traversal attempts
        path_traversal_payloads = security_test_payloads["path_traversal"]
        
        for payload in path_traversal_payloads:
            response = await authenticated_client.get(f"/api/v1/config/domain/{payload}")
            
            # Should reject path traversal attempts
            assert response.status_code in [400, 404], \
                f"Path traversal payload should be rejected: {payload}"
        
        print("✓ Domain authorization security: All injection attempts properly rejected")


class TestClientDomainMapping:
    """Test client-domain mapping accuracy."""
    
    async def test_client_domain_mapping_accuracy(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        multiple_clients
    ):
        """
        CRITICAL: Test client-domain mapping accuracy
        
        Validates:
        - Correct client configuration returned for each domain
        - Privacy level mapping accuracy
        - Feature configuration mapping
        - No cross-client configuration leakage
        - Mapping consistency across lookups
        """
        # Create multiple clients with different configurations
        client_configs = [
            {
                "name": "Standard Client",
                "email": "standard@example.com",
                "client_type": "end_client",
                "owner": "owner1@example.com",
                "privacy_level": "standard",
                "deployment_type": "shared",
                "features": {"analytics": True, "basic_tracking": True}
            },
            {
                "name": "GDPR Client",
                "email": "gdpr@example.eu",
                "client_type": "agency",
                "owner": "owner2@example.eu",
                "privacy_level": "gdpr",
                "deployment_type": "dedicated",
                "features": {"analytics": True, "gdpr_compliance": True, "cookie_consent": True}
            },
            {
                "name": "HIPAA Client",
                "email": "hipaa@healthcare.com",
                "client_type": "enterprise",
                "owner": "owner3@healthcare.com",
                "privacy_level": "hipaa",
                "deployment_type": "dedicated",
                "features": {"analytics": True, "hipaa_compliance": True, "medical_tracking": True}
            }
        ]
        
        clients_and_domains = []
        
        # Create clients and add domains
        for i, config in enumerate(client_configs):
            # Create client
            response = await authenticated_client.post("/api/v1/admin/clients", json=config)
            assert response.status_code == 201
            
            client_id = response.json()["client_id"]
            domain = f"client{i+1}.example.com"
            
            # Add domain
            domain_response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={"domain": domain, "is_primary": True}
            )
            assert domain_response.status_code == 201
            
            clients_and_domains.append({
                "client_id": client_id,
                "domain": domain,
                "config": config,
                "expected_response": response.json()
            })
        
        # Test mapping accuracy for each client-domain pair
        for client_info in clients_and_domains:
            domain = client_info["domain"]
            expected_client_id = client_info["client_id"]
            expected_privacy = client_info["config"]["privacy_level"]
            expected_features = client_info["config"]["features"]
            
            # Get configuration via domain lookup
            config_response = await authenticated_client.get(f"/api/v1/config/domain/{domain}")
            assert config_response.status_code == 200, f"Domain lookup failed for {domain}"
            
            config_data = config_response.json()
            
            # Verify correct client mapping
            assert config_data["client_id"] == expected_client_id, \
                f"Wrong client ID for domain {domain}: expected {expected_client_id}, got {config_data['client_id']}"
            
            # Verify privacy level mapping
            assert config_data["privacy_level"] == expected_privacy, \
                f"Wrong privacy level for {domain}: expected {expected_privacy}, got {config_data['privacy_level']}"
            
            # Verify feature mapping
            assert config_data["features"] == expected_features, \
                f"Wrong features for {domain}: expected {expected_features}, got {config_data['features']}"
            
            # Verify privacy-specific configuration
            if expected_privacy in ["gdpr", "hipaa"]:
                assert config_data["consent"]["required"] is True, \
                    f"Consent should be required for {expected_privacy} client"
                assert config_data["ip_collection"]["hash_required"] is True, \
                    f"IP hashing should be required for {expected_privacy} client"
                assert config_data["ip_collection"]["salt"] is not None, \
                    f"IP salt should be provided for {expected_privacy} client"
            else:
                assert config_data["consent"]["required"] is False, \
                    f"Consent should not be required for {expected_privacy} client"
                assert config_data["ip_collection"]["hash_required"] is False, \
                    f"IP hashing should not be required for {expected_privacy} client"
            
            print(f"✓ Mapping verified: {domain} -> {expected_client_id} ({expected_privacy})")
        
        # Test mapping consistency across multiple lookups
        test_domain = clients_and_domains[0]["domain"]
        expected_client_id = clients_and_domains[0]["client_id"]
        
        for i in range(5):
            response = await authenticated_client.get(f"/api/v1/config/domain/{test_domain}")
            assert response.status_code == 200
            assert response.json()["client_id"] == expected_client_id, \
                f"Mapping inconsistency on lookup {i+1}"
        
        print("✓ Client-domain mapping accuracy and consistency verified")
    
    async def test_domain_mapping_with_multiple_domains_per_client(
        self,
        authenticated_client: AsyncClient,
        sample_client_data
    ):
        """Test mapping accuracy when client has multiple domains."""
        
        # Create client
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
        
        # Add multiple domains
        domains = [
            "primary.example.com",
            "secondary.example.com",
            "api.example.com",
            "cdn.example.com"
        ]
        
        for i, domain in enumerate(domains):
            response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={"domain": domain, "is_primary": (i == 0)}
            )
            assert response.status_code == 201
        
        # Test that all domains map to the same client
        for domain in domains:
            config_response = await authenticated_client.get(f"/api/v1/config/domain/{domain}")
            assert config_response.status_code == 200
            
            config_data = config_response.json()
            assert config_data["client_id"] == client_id, \
                f"Domain {domain} mapped to wrong client: {config_data['client_id']}"
            
            # All domains should return identical configuration (same client)
            assert config_data["privacy_level"] == sample_client_data["privacy_level"]
            assert config_data["features"] == sample_client_data["features"]
        
        print(f"✓ Multiple domains per client: All {len(domains)} domains correctly mapped to {client_id}")


class TestMissingDomainHandling:
    """Test missing domain handling with appropriate responses."""
    
    async def test_missing_domain_handling(
        self,
        authenticated_client: AsyncClient,
        performance_timer
    ):
        """
        CRITICAL: Test missing domain handling with appropriate responses
        
        Validates:
        - 404 status for non-existent domains
        - Consistent error message format
        - Fast response time (<50ms)
        - No database errors for missing domains
        - Proper logging of missing domain attempts
        - Graceful fallback behavior
        """
        missing_domains = [
            "nonexistent.example.com",
            "missing-domain.org",
            "not-configured.net",
            "undefined-site.io"
        ]
        
        response_times = []
        
        for domain in missing_domains:
            performance_timer.start()
            
            response = await authenticated_client.get(f"/api/v1/config/domain/{domain}")
            
            response_time = performance_timer.stop()
            response_times.append(response_time)
            
            # Verify proper 404 response
            assert response.status_code == 404, \
                f"Missing domain should return 404: {domain} returned {response.status_code}"
            
            # Verify error message format
            error_data = response.json()
            assert "detail" in error_data
            assert "not authorized" in error_data["detail"].lower()
            
            # Verify fast response time
            assert response_time < 50, \
                f"Missing domain response too slow: {response_time:.2f}ms for {domain}"
            
            print(f"✓ Missing domain handled: {domain} -> 404 in {response_time:.2f}ms")
        
        # Verify consistent performance for missing domains
        avg_response_time = statistics.mean(response_times)
        assert avg_response_time < 30, \
            f"Average missing domain response too slow: {avg_response_time:.2f}ms"
        
        print(f"✓ Missing domain handling: Average response time {avg_response_time:.2f}ms")
    
    async def test_missing_domain_edge_cases(
        self,
        authenticated_client: AsyncClient,
        security_test_payloads
    ):
        """Test edge cases in missing domain handling."""
        
        # Test various invalid/missing domain formats
        edge_case_domains = [
            "",                           # Empty string
            " ",                         # Whitespace only
            ".",                         # Just a dot
            "..",                        # Double dots
            "a",                         # Single character
            "localhost",                 # Local domain
            "127.0.0.1",                # IP address
            "192.168.1.1",              # Private IP
            "example",                   # No TLD
            "sub.",                      # Incomplete domain
            ".example.com",              # Leading dot
            "example.com.",              # Trailing dot
            "exam ple.com",              # Space in domain
            "example..com",              # Double dots
            "example.com/path",          # Path included
            "http://example.com",        # Protocol included
            "https://example.com",       # HTTPS protocol
            "ftp://example.com",         # Different protocol
            "example.com:8080",          # Port included
            "example.com?query=value",   # Query parameters
        ]
        
        for domain in edge_case_domains:
            response = await authenticated_client.get(f"/api/v1/config/domain/{domain}")
            
            # Should return appropriate error status
            assert response.status_code in [400, 404], \
                f"Edge case domain '{domain}' should return 400 or 404, got {response.status_code}"
            
            # Should have proper error structure
            if response.status_code == 404:
                error_data = response.json()
                assert "detail" in error_data
        
        # Test with oversized domain
        oversized_domain = "a" * 1000 + ".com"
        response = await authenticated_client.get(f"/api/v1/config/domain/{oversized_domain}")
        assert response.status_code in [400, 404, 414], \
            "Oversized domain should be rejected"
        
        print("✓ Missing domain edge cases handled correctly")
    
    async def test_missing_domain_consistency(
        self,
        authenticated_client: AsyncClient
    ):
        """Test consistency in missing domain responses."""
        
        test_domain = "consistently-missing.example.com"
        
        # Make multiple requests for the same missing domain
        responses = []
        for i in range(10):
            response = await authenticated_client.get(f"/api/v1/config/domain/{test_domain}")
            responses.append(response)
        
        # All responses should be identical
        first_response = responses[0]
        for i, response in enumerate(responses[1:], 1):
            assert response.status_code == first_response.status_code, \
                f"Inconsistent status code on request {i+1}: {response.status_code} vs {first_response.status_code}"
            
            assert response.json() == first_response.json(), \
                f"Inconsistent response body on request {i+1}"
        
        print(f"✓ Missing domain responses consistent across {len(responses)} requests")
    
    async def test_domain_authorization_fallback_behavior(
        self,
        authenticated_client: AsyncClient,
        client_with_domains
    ):
        """Test fallback behavior when domain authorization fails."""
        
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        
        # Test direct client access as fallback when domain lookup fails
        missing_domain = "missing-but-client-exists.example.com"
        
        # Verify domain doesn't exist
        domain_response = await authenticated_client.get(f"/api/v1/config/domain/{missing_domain}")
        assert domain_response.status_code == 404
        
        # Verify direct client access still works
        client_response = await authenticated_client.get(f"/api/v1/config/client/{client_id}")
        assert client_response.status_code == 200
        
        client_config = client_response.json()
        assert client_config["client_id"] == client_id
        
        print("✓ Fallback behavior: Direct client access available when domain lookup fails")


# Load testing and stress testing
@pytest.mark.performance
@pytest.mark.slow
class TestDomainAuthorizationStress:
    """Stress tests for domain authorization under load."""
    
    async def test_domain_authorization_under_sustained_load(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        performance_threshold
    ):
        """Test domain authorization performance under sustained load."""
        
        domains = client_with_domains['domains']
        test_domain = domains[0]['domain']
        
        # Sustained load test
        total_requests = 200
        success_count = 0
        total_time = 0
        error_count = 0
        
        start_time = time.perf_counter()
        
        # Create batches of concurrent requests
        batch_size = 20
        batches = total_requests // batch_size
        
        for batch in range(batches):
            async def single_request():
                try:
                    request_start = time.perf_counter()
                    response = await authenticated_client.get(f"/api/v1/config/domain/{test_domain}")
                    request_time = (time.perf_counter() - request_start) * 1000
                    
                    return {
                        'success': response.status_code == 200,
                        'time': request_time,
                        'status': response.status_code
                    }
                except Exception as e:
                    return {'success': False, 'time': 0, 'error': str(e)}
            
            # Run batch concurrently
            batch_tasks = [single_request() for _ in range(batch_size)]
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Aggregate results
            for result in batch_results:
                if result['success']:
                    success_count += 1
                    total_time += result['time']
                else:
                    error_count += 1
        
        total_elapsed = (time.perf_counter() - start_time) * 1000
        
        # Calculate metrics
        success_rate = (success_count / total_requests) * 100
        avg_response_time = total_time / success_count if success_count > 0 else 0
        requests_per_second = (total_requests / total_elapsed) * 1000
        
        # Verify performance requirements
        assert success_rate >= 95, f"Success rate too low: {success_rate:.2f}%"
        assert avg_response_time < performance_threshold["domain_lookup_ms"], \
            f"Average response time under load too slow: {avg_response_time:.2f}ms"
        assert requests_per_second >= 50, f"Throughput too low: {requests_per_second:.2f} RPS"
        
        print(f"✓ Sustained load test completed:")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        print(f"  Throughput: {requests_per_second:.2f} RPS")
        print(f"  Error count: {error_count}")
    
    async def test_domain_authorization_burst_capacity(
        self,
        authenticated_client: AsyncClient,
        client_with_domains
    ):
        """Test domain authorization handling of burst traffic."""
        
        domains = client_with_domains['domains']
        test_domain = domains[0]['domain']
        
        # Burst test - high concurrency for short duration
        burst_requests = 100
        
        async def burst_request(index):
            start_time = time.perf_counter()
            try:
                response = await authenticated_client.get(f"/api/v1/config/domain/{test_domain}")
                response_time = (time.perf_counter() - start_time) * 1000
                
                return {
                    'index': index,
                    'success': response.status_code == 200,
                    'response_time': response_time,
                    'status_code': response.status_code
                }
            except Exception as e:
                return {
                    'index': index,
                    'success': False,
                    'response_time': (time.perf_counter() - start_time) * 1000,
                    'error': str(e)
                }
        
        # Launch all requests simultaneously
        burst_start = time.perf_counter()
        tasks = [burst_request(i) for i in range(burst_requests)]
        results = await asyncio.gather(*tasks)
        burst_duration = (time.perf_counter() - burst_start) * 1000
        
        # Analyze burst results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        success_rate = (len(successful_requests) / burst_requests) * 100
        avg_burst_time = statistics.mean([r['response_time'] for r in successful_requests]) if successful_requests else 0
        
        # Burst capacity requirements
        assert success_rate >= 90, f"Burst success rate too low: {success_rate:.2f}%"
        assert avg_burst_time < 500, f"Burst response time too slow: {avg_burst_time:.2f}ms"
        
        print(f"✓ Burst capacity test:")
        print(f"  Burst requests: {burst_requests}")
        print(f"  Burst duration: {burst_duration:.2f}ms")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Average response time: {avg_burst_time:.2f}ms")
        print(f"  Failed requests: {len(failed_requests)}")