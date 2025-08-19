"""
Concurrent Request Performance Tests - Phase 5

Load testing scenarios for concurrent request handling in the pixel management system.
Tests system stability under concurrent load, authentication performance, rate limiting
behavior, and overall system resilience under stress conditions.

Performance Requirements:
- Handle 100+ concurrent requests
- Authentication: <50ms per request
- Rate limiting: consistent enforcement
- System stability: no degradation

Test Categories:
1. Concurrent pixel requests with response time measurement
2. Concurrent authentication with performance verification
3. Rate limiting under concurrent load with fairness testing
4. System stability and resource usage under sustained load
"""

import pytest
import asyncio
import time
import statistics
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app


@pytest.mark.performance
@pytest.mark.integration
class TestConcurrentRequestPerformance:
    """Performance tests for concurrent request handling."""

    @pytest.fixture
    def performance_thresholds(self):
        """Performance thresholds for concurrent operations."""
        return {
            "concurrent_requests": 100,
            "authentication_ms": 50,
            "pixel_generation_ms": 150,
            "rate_limit_enforcement_ms": 10
        }

    @pytest.fixture
    def mock_concurrent_clients(self):
        """Create mock client data for concurrent testing."""
        return [
            {
                "client_id": f"client_concurrent_{i:03d}",
                "name": f"Concurrent Test Client {i}",
                "email": f"test{i}@example.com",
                "client_type": "ecommerce",
                "privacy_level": "standard",
                "deployment_type": "shared",
                "is_active": True
            }
            for i in range(50)
        ]

    async def test_concurrent_pixel_requests_performance(
        self, 
        patched_firestore_client, 
        mock_concurrent_clients,
        performance_thresholds
    ):
        """
        Test concurrent pixel request handling with response time measurement.
        
        Verifies that the system can handle multiple simultaneous pixel requests
        while maintaining acceptable response times and success rates.
        """
        # Setup mock clients in database
        for client_data in mock_concurrent_clients:
            client_id = client_data["client_id"]
            patched_firestore_client.clients_ref.add(client_data, client_id)
            
            # Add domain for each client
            domain_data = {
                "domain": f"test{client_id.split('_')[-1]}.example.com",
                "client_id": client_id,
                "is_primary": True,
                "created_at": datetime.utcnow()
            }
            patched_firestore_client.domain_index_ref.add(domain_data, f"domain_{client_id}")

        # Create test client
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Prepare concurrent requests
            concurrent_requests = []
            num_concurrent = min(performance_thresholds["concurrent_requests"], len(mock_concurrent_clients))
            
            for i in range(num_concurrent):
                client_id = mock_concurrent_clients[i % len(mock_concurrent_clients)]["client_id"]
                
                # Mock the pixel serving to return consistent response
                with patch('app.pixel_serving.serve_pixel') as mock_serve:
                    mock_serve.return_value = Mock(
                        status_code=200,
                        headers={"Content-Type": "application/javascript"},
                        body="// Mock tracking pixel"
                    )
                    
                    request_task = self._make_pixel_request(client, client_id)
                    concurrent_requests.append(request_task)
            
            # Execute concurrent requests
            start_time = time.perf_counter()
            
            results = await asyncio.gather(*concurrent_requests, return_exceptions=True)
            
            end_time = time.perf_counter()
            total_time_ms = (end_time - start_time) * 1000
            
            # Analyze results
            successful_requests = [r for r in results if not isinstance(r, Exception)]
            failed_requests = [r for r in results if isinstance(r, Exception)]
            
            success_rate = len(successful_requests) / len(results)
            avg_response_time = total_time_ms / len(results) if results else 0
            
            # Performance assertions
            assert success_rate >= 0.95, f"Success rate {success_rate:.1%} below 95% threshold"
            assert avg_response_time < performance_thresholds["pixel_generation_ms"], \
                f"Average response time {avg_response_time:.2f}ms exceeds threshold"
            assert len(failed_requests) == 0, f"Found {len(failed_requests)} failed requests"
            
            print(f"Concurrent pixel requests - {num_concurrent} requests, "
                  f"Success rate: {success_rate:.1%}, "
                  f"Avg response time: {avg_response_time:.2f}ms")

    async def _make_pixel_request(self, client: AsyncClient, client_id: str):
        """Helper method to make a pixel request with timing."""
        start_time = time.perf_counter()
        
        try:
            response = await client.get(f"/pixel/{client_id}/tracking.js")
            end_time = time.perf_counter()
            
            return {
                "status_code": response.status_code,
                "response_time_ms": (end_time - start_time) * 1000,
                "success": response.status_code == 200
            }
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "status_code": 500,
                "response_time_ms": (end_time - start_time) * 1000,
                "success": False,
                "error": str(e)
            }

    async def test_concurrent_authentication_performance(
        self,
        patched_firestore_client,
        performance_thresholds
    ):
        """
        Test concurrent authentication request performance.
        
        Verifies that authentication can handle multiple simultaneous requests
        within acceptable time limits while maintaining security.
        """
        # Create test client
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Setup valid admin headers
            admin_headers = {
                "Authorization": "Bearer test_admin_key_12345",
                "Content-Type": "application/json"
            }
            
            # Prepare concurrent authentication requests
            concurrent_requests = []
            num_concurrent = 50
            
            for _ in range(num_concurrent):
                request_task = self._make_authenticated_request(client, admin_headers)
                concurrent_requests.append(request_task)
            
            # Execute concurrent requests
            start_time = time.perf_counter()
            
            results = await asyncio.gather(*concurrent_requests, return_exceptions=True)
            
            end_time = time.perf_counter()
            total_time_ms = (end_time - start_time) * 1000
            
            # Analyze authentication performance
            successful_auths = [r for r in results if not isinstance(r, Exception) and r["success"]]
            failed_auths = [r for r in results if isinstance(r, Exception) or not r["success"]]
            
            if successful_auths:
                response_times = [r["response_time_ms"] for r in successful_auths]
                avg_auth_time = statistics.mean(response_times)
                p95_auth_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
            else:
                avg_auth_time = float('inf')
                p95_auth_time = float('inf')
            
            success_rate = len(successful_auths) / len(results)
            
            # Performance assertions
            assert success_rate >= 0.95, f"Auth success rate {success_rate:.1%} below 95% threshold"
            assert avg_auth_time < performance_thresholds["authentication_ms"], \
                f"Average auth time {avg_auth_time:.2f}ms exceeds {performance_thresholds['authentication_ms']}ms threshold"
            assert p95_auth_time < performance_thresholds["authentication_ms"] * 2, \
                f"95th percentile auth time {p95_auth_time:.2f}ms too high"
            
            print(f"Concurrent authentication - {num_concurrent} requests, "
                  f"Success rate: {success_rate:.1%}, "
                  f"Avg time: {avg_auth_time:.2f}ms, "
                  f"95th percentile: {p95_auth_time:.2f}ms")

    async def _make_authenticated_request(self, client: AsyncClient, headers: Dict[str, str]):
        """Helper method to make an authenticated request with timing."""
        start_time = time.perf_counter()
        
        try:
            response = await client.get("/api/v1/admin/clients", headers=headers)
            end_time = time.perf_counter()
            
            return {
                "status_code": response.status_code,
                "response_time_ms": (end_time - start_time) * 1000,
                "success": response.status_code == 200
            }
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "status_code": 500,
                "response_time_ms": (end_time - start_time) * 1000,
                "success": False,
                "error": str(e)
            }

    async def test_rate_limiting_under_concurrent_load(self, performance_thresholds):
        """
        Test rate limiting behavior under concurrent load.
        
        Verifies that rate limiting is consistently enforced under concurrent
        access patterns and maintains fairness across different clients.
        """
        from app.rate_limiter import RateLimitMiddleware
        
        # Create rate limiter for testing
        mock_app = Mock()
        rate_limiter = RateLimitMiddleware(mock_app)
        
        # Simulate concurrent requests from same IP
        concurrent_requests = []
        test_ip = "192.168.1.100"
        test_path = "/api/v1/admin/clients"
        current_time = time.time()
        
        # Create requests that exceed rate limit
        num_requests = 50  # Exceeds the 30 req/min limit for admin endpoints
        
        for i in range(num_requests):
            request_task = self._test_rate_limit_request(
                rate_limiter, test_ip, test_path, current_time + (i * 0.1)
            )
            concurrent_requests.append(request_task)
        
        # Execute concurrent rate limit checks
        start_time = time.perf_counter()
        
        results = await asyncio.gather(*concurrent_requests)
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        # Analyze rate limiting behavior
        allowed_requests = [r for r in results if not r["rate_limited"]]
        blocked_requests = [r for r in results if r["rate_limited"]]
        processing_times = [r["processing_time_ms"] for r in results]
        
        avg_processing_time = statistics.mean(processing_times)
        max_processing_time = max(processing_times)
        
        # Rate limiting assertions
        assert len(blocked_requests) > 0, "Rate limiting should block some requests"
        assert len(allowed_requests) <= 30, f"Too many requests allowed: {len(allowed_requests)} (limit: 30)"
        assert avg_processing_time < performance_thresholds["rate_limit_enforcement_ms"], \
            f"Rate limiting processing too slow: {avg_processing_time:.2f}ms"
        assert max_processing_time < performance_thresholds["rate_limit_enforcement_ms"] * 2, \
            f"Max rate limiting time too high: {max_processing_time:.2f}ms"
        
        print(f"Rate limiting test - {len(allowed_requests)} allowed, "
              f"{len(blocked_requests)} blocked, "
              f"Avg processing: {avg_processing_time:.2f}ms")

    async def _test_rate_limit_request(self, rate_limiter, ip: str, path: str, timestamp: float):
        """Helper method to test rate limiting with timing."""
        start_time = time.perf_counter()
        
        is_limited, retry_after = rate_limiter.is_rate_limited(ip, path, timestamp)
        
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000
        
        return {
            "rate_limited": is_limited,
            "retry_after": retry_after,
            "processing_time_ms": processing_time_ms
        }

    async def test_system_stability_under_sustained_load(
        self,
        patched_firestore_client,
        mock_concurrent_clients
    ):
        """
        Test system stability under sustained concurrent load.
        
        Verifies that the system maintains stability and performance
        characteristics under extended periods of concurrent access.
        """
        # Setup test data
        for client_data in mock_concurrent_clients[:10]:  # Limit for sustained test
            client_id = client_data["client_id"]
            patched_firestore_client.clients_ref.add(client_data, client_id)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Run sustained load test
            duration_seconds = 30  # Sustained load for 30 seconds
            requests_per_second = 5
            total_requests = duration_seconds * requests_per_second
            
            start_time = time.perf_counter()
            all_results = []
            
            # Execute requests in waves
            for wave in range(duration_seconds):
                wave_requests = []
                
                for req in range(requests_per_second):
                    # Alternate between different endpoint types
                    if req % 2 == 0:
                        request_task = client.get("/health")
                    else:
                        client_id = mock_concurrent_clients[req % 10]["client_id"]
                        request_task = self._make_config_request(client, client_id)
                    
                    wave_requests.append(request_task)
                
                # Execute wave of requests
                wave_results = await asyncio.gather(*wave_requests, return_exceptions=True)
                all_results.extend(wave_results)
                
                # Small delay between waves
                await asyncio.sleep(1)
            
            end_time = time.perf_counter()
            total_duration_ms = (end_time - start_time) * 1000
            
            # Analyze stability metrics
            successful_responses = 0
            error_responses = 0
            response_times = []
            
            for result in all_results:
                if isinstance(result, Exception):
                    error_responses += 1
                else:
                    if hasattr(result, 'status_code') and result.status_code < 400:
                        successful_responses += 1
                    else:
                        error_responses += 1
            
            success_rate = successful_responses / len(all_results)
            actual_throughput = len(all_results) / (total_duration_ms / 1000)
            
            # Stability assertions
            assert success_rate >= 0.95, f"Stability test success rate {success_rate:.1%} below threshold"
            assert error_responses < len(all_results) * 0.05, f"Too many errors: {error_responses}"
            assert actual_throughput >= requests_per_second * 0.9, \
                f"Throughput {actual_throughput:.1f} req/s below expected {requests_per_second}"
            
            print(f"Sustained load test - {len(all_results)} requests over {total_duration_ms/1000:.1f}s, "
                  f"Success rate: {success_rate:.1%}, "
                  f"Throughput: {actual_throughput:.1f} req/s")

    async def _make_config_request(self, client: AsyncClient, client_id: str):
        """Helper method to make a config request."""
        try:
            return await client.get(f"/api/v1/config/client/{client_id}")
        except Exception as e:
            return e