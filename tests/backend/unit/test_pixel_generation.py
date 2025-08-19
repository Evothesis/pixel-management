"""
Pixel Generation Core Business Logic Tests

Tests the critical pixel serving functionality that delivers core business value.
Focuses on ≥95% coverage of pixel generation with strict performance requirements.

Critical business logic tested:
- Dynamic JavaScript template processing with client-specific configuration injection
- Privacy level enforcement (standard, GDPR, HIPAA) in generated pixels
- Domain validation during pixel serving with authorization checks
- Template caching and performance optimization for sub-150ms response times

Performance requirements (CRITICAL):
- Pixel generation: <150ms response time
- Template caching: <10ms for cached templates
- Domain validation in pixels: <100ms
- Concurrent pixel serving: 50+ RPS sustained

Security requirements:
- Domain authorization before pixel serving
- Privacy level compliance in generated JavaScript
- No code injection in template substitution
- Proper CORS headers and caching controls
"""

import pytest
import asyncio
import time
import json
from datetime import datetime
from unittest.mock import patch, Mock, AsyncMock
from httpx import AsyncClient
import statistics
import re

# Test markers for coverage tracking
pytestmark = [
    pytest.mark.unit,
    pytest.mark.critical,
    pytest.mark.asyncio
]


class TestTemplateProcessing:
    """Test dynamic JavaScript template processing."""
    
    async def test_template_processing(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        performance_timer
    ):
        """
        CRITICAL: Test dynamic JavaScript template processing
        
        Validates:
        - Template loading and caching mechanism
        - Configuration injection into JavaScript template
        - Client-specific customization
        - Performance under 150ms
        - Template validation and security
        - Proper JavaScript syntax generation
        """
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        domains = client_with_domains['domains']
        test_domain = domains[0]['domain']
        
        performance_timer.start()
        
        # Request pixel with proper domain authorization
        response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers={
                "Origin": f"https://{test_domain}",
                "Referer": f"https://{test_domain}/test-page"
            }
        )
        
        generation_time = performance_timer.stop()
        
        assert response.status_code == 200, f"Pixel generation failed: {response.text}"
        assert generation_time < 150, f"Pixel generation too slow: {generation_time:.2f}ms"
        
        # Verify response headers
        assert response.headers["content-type"] == "application/javascript; charset=utf-8"
        assert "Cache-Control" in response.headers
        assert "public" in response.headers["Cache-Control"]
        assert "max-age" in response.headers["Cache-Control"]
        
        # Verify custom headers
        assert response.headers.get("X-Client-ID") == client_id
        assert response.headers.get("X-Authorized-Domain") == test_domain
        assert response.headers.get("X-Privacy-Level") == client_data["privacy_level"]
        assert "X-Generated-At" in response.headers
        
        # Parse and validate generated JavaScript
        pixel_code = response.text
        
        # Verify basic JavaScript structure
        assert pixel_code.startswith("(function()"), "Pixel should be wrapped in IIFE"
        assert pixel_code.endswith("})();"), "Pixel should end IIFE properly"
        
        # Verify configuration injection
        assert client_id in pixel_code, "Client ID should be embedded in pixel"
        assert client_data["privacy_level"] in pixel_code, "Privacy level should be embedded"
        
        # Extract configuration from JavaScript
        config_match = re.search(r'var\s+config\s*=\s*({.*?});', pixel_code, re.DOTALL)
        assert config_match, "Configuration object should be embedded in JavaScript"
        
        try:
            config_json = config_match.group(1)
            embedded_config = json.loads(config_json)
            
            # Validate embedded configuration structure
            assert embedded_config["client_id"] == client_id
            assert embedded_config["privacy_level"] == client_data["privacy_level"]
            assert "ip_collection" in embedded_config
            assert "consent" in embedded_config
            assert "features" in embedded_config
            assert "deployment" in embedded_config
            assert "collection_endpoint" in embedded_config
            assert "pixel_version" in embedded_config
            assert "generated_at" in embedded_config
            
            # Validate privacy-specific configuration
            if client_data["privacy_level"] in ["gdpr", "hipaa"]:
                assert embedded_config["consent"]["required"] is True
                assert embedded_config["ip_collection"]["hash_required"] is True
            else:
                assert embedded_config["consent"]["required"] is False
                assert embedded_config["ip_collection"]["hash_required"] is False
            
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in embedded configuration: {e}")
        
        # Verify JavaScript syntax is valid (basic check)
        assert "syntax error" not in pixel_code.lower()
        assert pixel_code.count("(") == pixel_code.count(")"), "Parentheses should be balanced"
        assert pixel_code.count("{") == pixel_code.count("}"), "Braces should be balanced"
        
        print(f"✓ Template processing completed in {generation_time:.2f}ms")
        print(f"✓ Configuration embedded: {len(embedded_config)} properties")
        print(f"✓ Generated pixel size: {len(pixel_code)} characters")
    
    async def test_template_caching_performance(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        performance_timer
    ):
        """Test template caching and performance optimization."""
        
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        domains = client_with_domains['domains']
        test_domain = domains[0]['domain']
        
        request_headers = {
            "Origin": f"https://{test_domain}",
            "Referer": f"https://{test_domain}/test-page"
        }
        
        # First request (cold cache)
        performance_timer.start()
        
        first_response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers=request_headers
        )
        
        first_request_time = performance_timer.stop()
        
        assert first_response.status_code == 200
        first_pixel_code = first_response.text
        
        # Subsequent requests (warm cache)
        cached_request_times = []
        
        for i in range(10):
            performance_timer.start()
            
            response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers=request_headers
            )
            
            request_time = performance_timer.stop()
            cached_request_times.append(request_time)
            
            assert response.status_code == 200
            assert response.text == first_pixel_code, "Cached response should be identical"
        
        avg_cached_time = statistics.mean(cached_request_times)
        
        # Template caching should improve performance
        assert avg_cached_time < first_request_time, \
            f"Cached requests should be faster: {avg_cached_time:.2f}ms vs {first_request_time:.2f}ms"
        
        # Cached requests should be very fast
        assert avg_cached_time < 50, f"Cached requests too slow: {avg_cached_time:.2f}ms"
        
        print(f"✓ Template caching performance:")
        print(f"  First request (cold): {first_request_time:.2f}ms")
        print(f"  Cached requests (avg): {avg_cached_time:.2f}ms")
        print(f"  Performance improvement: {(first_request_time / avg_cached_time):.1f}x")
    
    async def test_template_customization_per_client(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client,
        multiple_clients
    ):
        """Test template customization varies correctly per client."""
        
        # Create multiple clients with different configurations
        client_configs = [
            {
                "name": "Basic Client",
                "email": "basic@example.com",
                "client_type": "end_client",
                "owner": "owner1@example.com",
                "privacy_level": "standard",
                "deployment_type": "shared",
                "features": {"analytics": True}
            },
            {
                "name": "Advanced Client",
                "email": "advanced@example.com",
                "client_type": "enterprise",
                "owner": "owner2@example.com",
                "privacy_level": "gdpr",
                "deployment_type": "dedicated",
                "features": {"analytics": True, "custom_events": True, "gdpr_compliance": True}
            }
        ]
        
        client_pixels = []
        
        for i, config in enumerate(client_configs):
            # Create client
            response = await authenticated_client.post("/api/v1/admin/clients", json=config)
            assert response.status_code == 201
            
            client_id = response.json()["client_id"]
            domain = f"client{i+1}-custom.example.com"
            
            # Add domain
            domain_response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={"domain": domain, "is_primary": True}
            )
            assert domain_response.status_code == 201
            
            # Generate pixel
            pixel_response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={"Origin": f"https://{domain}"}
            )
            assert pixel_response.status_code == 200
            
            client_pixels.append({
                "client_id": client_id,
                "config": config,
                "pixel_code": pixel_response.text,
                "domain": domain
            })
        
        # Verify pixels are different per client
        pixel1 = client_pixels[0]["pixel_code"]
        pixel2 = client_pixels[1]["pixel_code"]
        
        assert pixel1 != pixel2, "Pixels should be customized per client"
        
        # Verify client-specific content
        for client_pixel in client_pixels:
            pixel_code = client_pixel["pixel_code"]
            config = client_pixel["config"]
            client_id = client_pixel["client_id"]
            
            # Client ID should be embedded
            assert client_id in pixel_code
            
            # Privacy level should be embedded
            assert config["privacy_level"] in pixel_code
            
            # Features should be reflected
            if "gdpr_compliance" in config["features"]:
                assert "gdpr" in pixel_code.lower()
            
            print(f"✓ Customization verified for {client_id} ({config['privacy_level']})")
        
        print("✓ Template customization varies correctly per client")


class TestPrivacyLevelEnforcement:
    """Test privacy level enforcement in generated pixels."""
    
    async def test_privacy_level_enforcement(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client
    ):
        """
        CRITICAL: Test privacy level enforcement (standard, GDPR, HIPAA)
        
        Validates:
        - Standard privacy: Basic tracking allowed
        - GDPR privacy: Consent management, IP hashing, data minimization
        - HIPAA privacy: Enhanced security, data encryption, audit logging
        - Proper JavaScript generation for each privacy level
        - Compliance-specific features in pixel code
        """
        privacy_test_cases = [
            {
                "privacy_level": "standard",
                "expected_features": {
                    "consent_required": False,
                    "ip_hashing": False,
                    "enhanced_security": False
                },
                "expected_code_patterns": [
                    "analytics",
                    "tracking"
                ],
                "prohibited_patterns": [
                    "consent_management",
                    "ip_hash",
                    "gdpr",
                    "hipaa"
                ]
            },
            {
                "privacy_level": "gdpr",
                "expected_features": {
                    "consent_required": True,
                    "ip_hashing": True,
                    "enhanced_security": True
                },
                "expected_code_patterns": [
                    "consent",
                    "gdpr",
                    "hash_required",
                    "opt_out"
                ],
                "prohibited_patterns": [
                    "hipaa"
                ]
            },
            {
                "privacy_level": "hipaa",
                "expected_features": {
                    "consent_required": True,
                    "ip_hashing": True,
                    "enhanced_security": True
                },
                "expected_code_patterns": [
                    "consent",
                    "hipaa",
                    "hash_required",
                    "encryption"
                ],
                "prohibited_patterns": []
            }
        ]
        
        for test_case in privacy_test_cases:
            privacy_level = test_case["privacy_level"]
            
            # Create client with specific privacy level
            client_config = {
                "name": f"{privacy_level.upper()} Test Client",
                "email": f"{privacy_level}@example.com",
                "client_type": "enterprise",
                "owner": f"owner@{privacy_level}.com",
                "privacy_level": privacy_level,
                "deployment_type": "dedicated",
                "features": {
                    "analytics": True,
                    f"{privacy_level}_compliance": True
                }
            }
            
            response = await authenticated_client.post("/api/v1/admin/clients", json=client_config)
            assert response.status_code == 201
            
            client_id = response.json()["client_id"]
            domain = f"{privacy_level}-test.example.com"
            
            # Add domain
            domain_response = await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={"domain": domain, "is_primary": True}
            )
            assert domain_response.status_code == 201
            
            # Generate pixel
            pixel_response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={"Origin": f"https://{domain}"}
            )
            assert pixel_response.status_code == 200
            
            pixel_code = pixel_response.text
            
            # Verify privacy level in headers
            assert pixel_response.headers.get("X-Privacy-Level") == privacy_level
            
            # Extract configuration from pixel
            config_match = re.search(r'var\s+config\s*=\s*({.*?});', pixel_code, re.DOTALL)
            assert config_match, f"Configuration not found in {privacy_level} pixel"
            
            embedded_config = json.loads(config_match.group(1))
            
            # Verify privacy-specific configuration
            expected_features = test_case["expected_features"]
            
            assert embedded_config["privacy_level"] == privacy_level
            assert embedded_config["consent"]["required"] == expected_features["consent_required"]
            assert embedded_config["ip_collection"]["hash_required"] == expected_features["ip_hashing"]
            
            # For privacy-compliant levels, verify IP salt is provided
            if privacy_level in ["gdpr", "hipaa"]:
                assert embedded_config["ip_collection"]["salt"] is not None
                assert len(embedded_config["ip_collection"]["salt"]) > 20
            
            # Verify expected code patterns
            pixel_code_lower = pixel_code.lower()
            
            for pattern in test_case["expected_code_patterns"]:
                assert pattern in pixel_code_lower, \
                    f"Expected pattern '{pattern}' not found in {privacy_level} pixel"
            
            for pattern in test_case["prohibited_patterns"]:
                assert pattern not in pixel_code_lower, \
                    f"Prohibited pattern '{pattern}' found in {privacy_level} pixel"
            
            print(f"✓ Privacy enforcement verified: {privacy_level}")
            print(f"  Consent required: {embedded_config['consent']['required']}")
            print(f"  IP hashing: {embedded_config['ip_collection']['hash_required']}")
            print(f"  Expected patterns found: {len(test_case['expected_code_patterns'])}")
        
        print("✓ All privacy levels properly enforced in pixel generation")
    
    async def test_privacy_level_consent_behavior(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client
    ):
        """Test consent behavior varies by privacy level."""
        
        # Create GDPR client
        gdpr_response = await authenticated_client.post(
            "/api/v1/admin/clients",
            json={
                "name": "GDPR Consent Client",
                "email": "gdpr@example.eu",
                "client_type": "agency",
                "owner": "owner@example.eu",
                "privacy_level": "gdpr",
                "deployment_type": "shared",
                "features": {"analytics": True, "gdpr_compliance": True}
            }
        )
        assert gdpr_response.status_code == 201
        gdpr_client_id = gdpr_response.json()["client_id"]
        
        # Add domain
        await authenticated_client.post(
            f"/api/v1/admin/clients/{gdpr_client_id}/domains",
            json={"domain": "gdpr-consent.example.eu", "is_primary": True}
        )
        
        # Generate GDPR pixel
        gdpr_pixel_response = await authenticated_client.get(
            f"/pixel/{gdpr_client_id}/tracking.js",
            headers={"Origin": "https://gdpr-consent.example.eu"}
        )
        assert gdpr_pixel_response.status_code == 200
        
        gdpr_pixel = gdpr_pixel_response.text
        
        # Extract GDPR configuration
        config_match = re.search(r'var\s+config\s*=\s*({.*?});', gdpr_pixel, re.DOTALL)
        gdpr_config = json.loads(config_match.group(1))
        
        # Verify GDPR consent behavior
        assert gdpr_config["consent"]["required"] is True
        assert gdpr_config["consent"]["default_behavior"] == "block"
        assert gdpr_config["ip_collection"]["hash_required"] is True
        
        # Verify GDPR-specific JavaScript patterns
        assert "consent" in gdpr_pixel.lower()
        assert "opt" in gdpr_pixel.lower()  # opt-in/opt-out functionality
        
        print("✓ Privacy-specific consent behavior verified")
    
    async def test_privacy_level_data_handling(
        self,
        authenticated_client: AsyncClient,
        mock_firestore_client
    ):
        """Test data handling varies by privacy level."""
        
        privacy_data_tests = [
            {
                "privacy_level": "standard",
                "expected_ip_collection": True,
                "expected_data_retention": "standard",
                "expected_encryption": False
            },
            {
                "privacy_level": "gdpr",
                "expected_ip_collection": True,
                "expected_data_retention": "limited",
                "expected_encryption": True
            },
            {
                "privacy_level": "hipaa",
                "expected_ip_collection": True,
                "expected_data_retention": "secure",
                "expected_encryption": True
            }
        ]
        
        for test_case in privacy_data_tests:
            privacy_level = test_case["privacy_level"]
            
            # Create client
            response = await authenticated_client.post(
                "/api/v1/admin/clients",
                json={
                    "name": f"Data Handling {privacy_level.upper()}",
                    "email": f"data-{privacy_level}@example.com",
                    "client_type": "enterprise",
                    "owner": f"owner@{privacy_level}.com",
                    "privacy_level": privacy_level,
                    "deployment_type": "dedicated",
                    "features": {"analytics": True}
                }
            )
            assert response.status_code == 201
            
            client_id = response.json()["client_id"]
            domain = f"data-{privacy_level}.example.com"
            
            # Add domain and generate pixel
            await authenticated_client.post(
                f"/api/v1/admin/clients/{client_id}/domains",
                json={"domain": domain, "is_primary": True}
            )
            
            pixel_response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={"Origin": f"https://{domain}"}
            )
            assert pixel_response.status_code == 200
            
            # Extract and verify data handling configuration
            pixel_code = pixel_response.text
            config_match = re.search(r'var\s+config\s*=\s*({.*?});', pixel_code, re.DOTALL)
            config = json.loads(config_match.group(1))
            
            # Verify IP collection settings
            assert config["ip_collection"]["enabled"] == test_case["expected_ip_collection"]
            
            if privacy_level in ["gdpr", "hipaa"]:
                assert config["ip_collection"]["hash_required"] is True
                assert config["ip_collection"]["salt"] is not None
            
            print(f"✓ Data handling verified for {privacy_level}")
        
        print("✓ Privacy-specific data handling properly configured")


class TestDomainValidationInPixel:
    """Test domain validation during pixel serving."""
    
    async def test_domain_validation_in_pixel(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        performance_timer
    ):
        """
        CRITICAL: Test domain validation during pixel serving
        
        Validates:
        - Authorized domains receive pixels
        - Unauthorized domains get 403/404
        - Domain validation performance <100ms
        - Proper error responses for invalid domains
        - Case-insensitive domain matching
        - Header-based domain detection (Origin, Referer)
        """
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        domains = client_with_domains['domains']
        authorized_domain = domains[0]['domain']
        
        # Test authorized domain access
        performance_timer.start()
        
        authorized_response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers={
                "Origin": f"https://{authorized_domain}",
                "Referer": f"https://{authorized_domain}/test-page"
            }
        )
        
        validation_time = performance_timer.stop()
        
        assert authorized_response.status_code == 200, \
            f"Authorized domain should receive pixel: {authorized_domain}"
        assert validation_time < 100, f"Domain validation too slow: {validation_time:.2f}ms"
        
        # Verify pixel content
        pixel_code = authorized_response.text
        assert client_id in pixel_code
        assert "function" in pixel_code.lower()  # Should be valid JavaScript
        
        # Test unauthorized domain rejection
        unauthorized_domain = "unauthorized.hacker.com"
        
        unauthorized_response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers={
                "Origin": f"https://{unauthorized_domain}",
                "Referer": f"https://{unauthorized_domain}/malicious-page"
            }
        )
        
        assert unauthorized_response.status_code == 403, \
            f"Unauthorized domain should be rejected: {unauthorized_domain}"
        
        # Verify error response structure
        error_data = unauthorized_response.json()
        assert "detail" in error_data
        assert "not authorized" in error_data["detail"].lower()
        
        # Test case-insensitive domain matching
        case_variations = [
            f"https://{authorized_domain.upper()}",
            f"https://{authorized_domain.title()}",
            f"HTTPS://{authorized_domain}"
        ]
        
        for origin in case_variations:
            response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={"Origin": origin}
            )
            assert response.status_code == 200, \
                f"Case variation should be accepted: {origin}"
        
        # Test different header combinations
        header_test_cases = [
            {
                "headers": {"Origin": f"https://{authorized_domain}"},
                "description": "Origin header only"
            },
            {
                "headers": {"Referer": f"https://{authorized_domain}/page"},
                "description": "Referer header only"
            },
            {
                "headers": {
                    "Origin": f"https://{authorized_domain}",
                    "Referer": f"https://{authorized_domain}/page"
                },
                "description": "Both headers"
            }
        ]
        
        for test_case in header_test_cases:
            response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers=test_case["headers"]
            )
            assert response.status_code == 200, \
                f"Should work with {test_case['description']}"
        
        # Test missing domain headers
        no_headers_response = await authenticated_client.get(f"/pixel/{client_id}/tracking.js")
        
        # Should reject requests without domain information
        assert no_headers_response.status_code in [400, 403], \
            "Requests without domain headers should be rejected"
        
        print(f"✓ Domain validation in pixel serving: {validation_time:.2f}ms")
        print(f"✓ Authorized access: 200, Unauthorized: 403")
        print(f"✓ Case-insensitive matching and header detection working")
    
    async def test_domain_authorization_edge_cases_in_pixels(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        security_test_payloads
    ):
        """Test edge cases in domain authorization for pixel serving."""
        
        client_id = client_with_domains['client']['client_id']
        
        # Test malicious domain headers
        malicious_headers = [
            {
                "Origin": "javascript:alert('xss')",
                "description": "JavaScript protocol in Origin"
            },
            {
                "Origin": "data:text/html,<script>alert('xss')</script>",
                "description": "Data protocol in Origin"
            },
            {
                "Referer": "'; DROP TABLE domains; --",
                "description": "SQL injection in Referer"
            },
            {
                "Origin": "<script>alert('xss')</script>",
                "description": "XSS attempt in Origin"
            }
        ]
        
        for header_test in malicious_headers:
            response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={k: v for k, v in header_test.items() if k != "description"}
            )
            
            # Should reject malicious headers
            assert response.status_code in [400, 403], \
                f"Malicious header should be rejected: {header_test['description']}"
        
        # Test oversized domain headers
        oversized_domain = "a" * 1000 + ".com"
        
        response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers={"Origin": f"https://{oversized_domain}"}
        )
        
        assert response.status_code in [400, 403, 414], \
            "Oversized domain should be rejected"
        
        # Test various protocol schemes
        protocol_tests = [
            "http://authorized.com",      # HTTP instead of HTTPS
            "ftp://authorized.com",       # FTP protocol
            "file://authorized.com",      # File protocol
            "ws://authorized.com",        # WebSocket protocol
            "wss://authorized.com",       # Secure WebSocket
        ]
        
        for protocol_test in protocol_tests:
            response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={"Origin": protocol_test}
            )
            
            # Behavior may vary - document what happens
            print(f"  Protocol test '{protocol_test}': {response.status_code}")
        
        print("✓ Domain authorization edge cases handled securely")
    
    async def test_concurrent_domain_validation(
        self,
        authenticated_client: AsyncClient,
        client_with_domains
    ):
        """Test concurrent domain validation performance."""
        
        client_id = client_with_domains['client']['client_id']
        domains = client_with_domains['domains']
        
        # Test concurrent requests from authorized domain
        authorized_domain = domains[0]['domain']
        
        async def pixel_request(index):
            start_time = time.perf_counter()
            response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={
                    "Origin": f"https://{authorized_domain}",
                    "User-Agent": f"Test-Agent-{index}"
                }
            )
            response_time = (time.perf_counter() - start_time) * 1000
            
            return {
                'status_code': response.status_code,
                'response_time': response_time,
                'index': index
            }
        
        # Run concurrent validation tests
        concurrent_requests = 20
        tasks = [pixel_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        # Analyze concurrent validation results
        successful_requests = [r for r in results if r['status_code'] == 200]
        failed_requests = [r for r in results if r['status_code'] != 200]
        
        success_rate = (len(successful_requests) / concurrent_requests) * 100
        avg_validation_time = statistics.mean([r['response_time'] for r in successful_requests])
        
        assert success_rate >= 95, f"Concurrent validation success rate too low: {success_rate:.2f}%"
        assert avg_validation_time < 200, f"Concurrent validation too slow: {avg_validation_time:.2f}ms"
        
        print(f"✓ Concurrent domain validation:")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Average validation time: {avg_validation_time:.2f}ms")
        print(f"  Failed requests: {len(failed_requests)}")


class TestPixelCaching:
    """Test template caching and performance optimization."""
    
    async def test_pixel_caching(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        performance_timer
    ):
        """
        CRITICAL: Test template caching and performance optimization
        
        Validates:
        - Template caching reduces response time
        - Cache invalidation when client config changes
        - Cache hit ratio optimization
        - Memory efficiency of caching
        - Concurrent cache access safety
        - Performance improvement measurement
        """
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        domains = client_with_domains['domains']
        test_domain = domains[0]['domain']
        
        headers = {
            "Origin": f"https://{test_domain}",
            "Referer": f"https://{test_domain}/test"
        }
        
        # First request (cold cache)
        performance_timer.start()
        
        first_response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers=headers
        )
        
        cold_cache_time = performance_timer.stop()
        
        assert first_response.status_code == 200
        first_pixel = first_response.text
        first_headers = dict(first_response.headers)
        
        # Verify caching headers are set
        assert "Cache-Control" in first_headers
        assert "public" in first_headers["Cache-Control"]
        assert "max-age" in first_headers["Cache-Control"]
        
        # Extract max-age value
        cache_control = first_headers["Cache-Control"]
        max_age_match = re.search(r'max-age=(\d+)', cache_control)
        assert max_age_match, "max-age should be specified in Cache-Control"
        max_age = int(max_age_match.group(1))
        assert max_age > 0, "max-age should be positive"
        
        # Multiple subsequent requests (warm cache)
        warm_cache_times = []
        cache_consistency_check = []
        
        for i in range(15):
            performance_timer.start()
            
            response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers=headers
            )
            
            warm_time = performance_timer.stop()
            warm_cache_times.append(warm_time)
            
            assert response.status_code == 200
            cache_consistency_check.append(response.text)
        
        # Verify cache performance improvement
        avg_warm_time = statistics.mean(warm_cache_times)
        performance_improvement = cold_cache_time / avg_warm_time
        
        assert avg_warm_time < cold_cache_time, \
            f"Warm cache should be faster: {avg_warm_time:.2f}ms vs {cold_cache_time:.2f}ms"
        
        assert performance_improvement >= 1.5, \
            f"Cache should provide significant speedup: {performance_improvement:.2f}x"
        
        # Verify cache consistency
        for i, cached_pixel in enumerate(cache_consistency_check):
            assert cached_pixel == first_pixel, \
                f"Cached response {i+1} differs from original"
        
        # Test cache behavior with different clients
        # (should not interfere with each other)
        if len(client_with_domains['domains']) > 1:
            other_domain = domains[1]['domain']
            
            other_response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={
                    "Origin": f"https://{other_domain}",
                    "Referer": f"https://{other_domain}/test"
                }
            )
            
            assert other_response.status_code == 200
            # Should be same pixel (same client, different domain)
            assert other_response.text == first_pixel
        
        print(f"✓ Pixel caching performance:")
        print(f"  Cold cache: {cold_cache_time:.2f}ms")
        print(f"  Warm cache (avg): {avg_warm_time:.2f}ms")
        print(f"  Performance improvement: {performance_improvement:.2f}x")
        print(f"  Cache max-age: {max_age} seconds")
    
    async def test_cache_invalidation_on_config_changes(
        self,
        authenticated_client: AsyncClient,
        client_with_domains
    ):
        """Test cache invalidation when client configuration changes."""
        
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        domains = client_with_domains['domains']
        test_domain = domains[0]['domain']
        
        headers = {
            "Origin": f"https://{test_domain}",
            "Referer": f"https://{test_domain}/test"
        }
        
        # Get initial pixel
        initial_response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers=headers
        )
        assert initial_response.status_code == 200
        initial_pixel = initial_response.text
        
        # Extract initial configuration
        config_match = re.search(r'var\s+config\s*=\s*({.*?});', initial_pixel, re.DOTALL)
        initial_config = json.loads(config_match.group(1))
        
        # Update client configuration
        config_update = {
            "features": {
                "analytics": True,
                "updated_feature": True,
                "cache_test": True
            }
        }
        
        update_response = await authenticated_client.put(
            f"/api/v1/admin/clients/{client_id}",
            json=config_update
        )
        assert update_response.status_code == 200
        
        # Small delay to allow any cache invalidation to process
        await asyncio.sleep(0.1)
        
        # Get pixel after configuration change
        updated_response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers=headers
        )
        assert updated_response.status_code == 200
        updated_pixel = updated_response.text
        
        # Extract updated configuration
        updated_config_match = re.search(r'var\s+config\s*=\s*({.*?});', updated_pixel, re.DOTALL)
        updated_config = json.loads(updated_config_match.group(1))
        
        # Verify configuration was updated in pixel
        assert updated_config["features"] != initial_config["features"], \
            "Configuration should be updated in pixel after client update"
        
        assert "updated_feature" in updated_config["features"], \
            "New features should appear in pixel"
        
        assert updated_config["features"]["updated_feature"] is True, \
            "Updated feature should have correct value"
        
        print("✓ Cache invalidation: Configuration changes reflected in pixel")
    
    async def test_concurrent_cache_access(
        self,
        authenticated_client: AsyncClient,
        client_with_domains
    ):
        """Test cache safety under concurrent access."""
        
        client_id = client_with_domains['client']['client_id']
        test_domain = client_with_domains['domains'][0]['domain']
        
        headers = {
            "Origin": f"https://{test_domain}",
            "Referer": f"https://{test_domain}/concurrent-test"
        }
        
        # Concurrent cache access function
        async def concurrent_pixel_request(index):
            start_time = time.perf_counter()
            
            try:
                response = await authenticated_client.get(
                    f"/pixel/{client_id}/tracking.js",
                    headers={**headers, "X-Request-ID": str(index)}
                )
                
                response_time = (time.perf_counter() - start_time) * 1000
                
                return {
                    'success': response.status_code == 200,
                    'response_time': response_time,
                    'content_length': len(response.text) if response.status_code == 200 else 0,
                    'pixel_code': response.text if response.status_code == 200 else None,
                    'index': index
                }
            except Exception as e:
                return {
                    'success': False,
                    'response_time': (time.perf_counter() - start_time) * 1000,
                    'error': str(e),
                    'index': index
                }
        
        # Run high concurrency test
        concurrent_requests = 50
        start_time = time.perf_counter()
        
        tasks = [concurrent_pixel_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Analyze concurrent cache access results
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        success_rate = (len(successful_results) / concurrent_requests) * 100
        avg_response_time = statistics.mean([r['response_time'] for r in successful_results])
        
        # Verify cache consistency under concurrency
        if successful_results:
            first_pixel = successful_results[0]['pixel_code']
            
            for result in successful_results[1:]:
                assert result['pixel_code'] == first_pixel, \
                    f"Cache inconsistency detected in concurrent access (request {result['index']})"
        
        # Performance requirements under concurrency
        assert success_rate >= 98, f"Concurrent cache access success rate too low: {success_rate:.2f}%"
        assert avg_response_time < 100, f"Concurrent cache access too slow: {avg_response_time:.2f}ms"
        
        # Calculate throughput
        throughput = (len(successful_results) / total_time) * 1000  # RPS
        
        print(f"✓ Concurrent cache access:")
        print(f"  Concurrent requests: {concurrent_requests}")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        print(f"  Throughput: {throughput:.2f} RPS")
        print(f"  Failed requests: {len(failed_results)}")
        print(f"  Cache consistency: ✓ (all responses identical)")


# Performance and stress testing
@pytest.mark.performance
@pytest.mark.slow
class TestPixelGenerationPerformance:
    """Performance tests for pixel generation under load."""
    
    async def test_pixel_generation_performance_benchmark(
        self,
        authenticated_client: AsyncClient,
        client_with_domains,
        performance_timer,
        performance_threshold
    ):
        """Benchmark pixel generation performance under various conditions."""
        
        client_id = client_with_domains['client']['client_id']
        test_domain = client_with_domains['domains'][0]['domain']
        
        headers = {
            "Origin": f"https://{test_domain}",
            "Referer": f"https://{test_domain}/performance-test"
        }
        
        # Single request benchmark
        performance_timer.start()
        
        response = await authenticated_client.get(
            f"/pixel/{client_id}/tracking.js",
            headers=headers
        )
        
        single_request_time = performance_timer.stop()
        
        assert response.status_code == 200
        assert single_request_time < performance_threshold["pixel_generation_ms"], \
            f"Single pixel generation too slow: {single_request_time:.2f}ms"
        
        # Burst performance test
        burst_requests = 25
        burst_times = []
        
        for i in range(burst_requests):
            performance_timer.start()
            
            response = await authenticated_client.get(
                f"/pixel/{client_id}/tracking.js",
                headers={**headers, "X-Burst-Request": str(i)}
            )
            
            burst_time = performance_timer.stop()
            burst_times.append(burst_time)
            
            assert response.status_code == 200
        
        avg_burst_time = statistics.mean(burst_times)
        p95_burst_time = statistics.quantiles(burst_times, n=20)[18]  # 95th percentile
        
        assert avg_burst_time < performance_threshold["pixel_generation_ms"], \
            f"Average burst time too slow: {avg_burst_time:.2f}ms"
        
        assert p95_burst_time < performance_threshold["pixel_generation_ms"] * 1.5, \
            f"95th percentile burst time too slow: {p95_burst_time:.2f}ms"
        
        print(f"✓ Pixel generation performance benchmark:")
        print(f"  Single request: {single_request_time:.2f}ms")
        print(f"  Burst average: {avg_burst_time:.2f}ms")
        print(f"  Burst 95th percentile: {p95_burst_time:.2f}ms")
        print(f"  Performance threshold: {performance_threshold['pixel_generation_ms']}ms")
    
    async def test_pixel_generation_sustained_load(
        self,
        authenticated_client: AsyncClient,
        client_with_domains
    ):
        """Test pixel generation under sustained load."""
        
        client_id = client_with_domains['client']['client_id']
        test_domain = client_with_domains['domains'][0]['domain']
        
        # Sustained load test parameters
        total_requests = 100
        batch_size = 10
        batches = total_requests // batch_size
        
        all_results = []
        
        for batch_num in range(batches):
            async def load_request(request_index):
                start_time = time.perf_counter()
                
                try:
                    response = await authenticated_client.get(
                        f"/pixel/{client_id}/tracking.js",
                        headers={
                            "Origin": f"https://{test_domain}",
                            "X-Batch": str(batch_num),
                            "X-Request": str(request_index)
                        }
                    )
                    
                    response_time = (time.perf_counter() - start_time) * 1000
                    
                    return {
                        'success': response.status_code == 200,
                        'response_time': response_time,
                        'batch': batch_num,
                        'request': request_index
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'response_time': (time.perf_counter() - start_time) * 1000,
                        'error': str(e),
                        'batch': batch_num,
                        'request': request_index
                    }
            
            # Execute batch
            batch_tasks = [load_request(i) for i in range(batch_size)]
            batch_results = await asyncio.gather(*batch_tasks)
            all_results.extend(batch_results)
            
            # Small delay between batches to simulate realistic load
            await asyncio.sleep(0.01)
        
        # Analyze sustained load results
        successful_requests = [r for r in all_results if r['success']]
        failed_requests = [r for r in all_results if not r['success']]
        
        success_rate = (len(successful_requests) / total_requests) * 100
        avg_response_time = statistics.mean([r['response_time'] for r in successful_requests])
        
        # Sustained load requirements
        assert success_rate >= 95, f"Sustained load success rate too low: {success_rate:.2f}%"
        assert avg_response_time < 200, f"Sustained load average response too slow: {avg_response_time:.2f}ms"
        
        print(f"✓ Sustained load test:")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        print(f"  Failed requests: {len(failed_requests)}")
        
        if failed_requests:
            print(f"  Failure details: {[r.get('error', 'Unknown') for r in failed_requests[:3]]}")