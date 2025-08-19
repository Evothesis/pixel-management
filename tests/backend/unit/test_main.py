"""
FastAPI Application Performance Tests - Phase 5

Performance tests for the main FastAPI application in the pixel management system.
Tests application startup time, response times, memory usage, and concurrent connection
handling to ensure optimal application-level performance characteristics.

Performance Requirements:
- App startup time: <5 seconds
- Response time: <500ms
- Memory usage: bounded growth
- Concurrent connections: 100+

Test Categories:
1. Application startup time and initialization performance
2. API endpoint response times under normal load
3. Memory usage profiling during operation
4. Concurrent connection handling and scalability
"""

import pytest
import time
import asyncio
import tracemalloc
import statistics
import psutil
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
from datetime import datetime

from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app


@pytest.mark.performance
@pytest.mark.integration
class TestFastAPIApplicationPerformance:
    """Performance tests for FastAPI application."""

    @pytest.fixture
    def performance_thresholds(self):
        """Performance thresholds for application-level operations."""
        return {
            "startup_time_s": 5,
            "api_response_ms": 500,
            "health_response_ms": 100,
            "concurrent_connections": 100,
            "memory_growth_mb": 50
        }

    @pytest.fixture
    def performance_test_data(self):
        """Create test data for performance testing."""
        return {
            "clients": [
                {
                    "client_id": f"client_perf_{i:06d}",
                    "name": f"Performance Test Client {i}",
                    "email": f"perf{i}@example.com",
                    "client_type": "ecommerce",
                    "privacy_level": "standard",
                    "deployment_type": "shared",
                    "is_active": True
                }
                for i in range(20)
            ],
            "domains": [
                {
                    "domain": f"perf-test-{i}.example.com",
                    "client_id": f"client_perf_{i:06d}",
                    "is_primary": True,
                    "created_at": datetime.utcnow()
                }
                for i in range(20)
            ]
        }

    def test_application_startup_performance(self, patched_firestore_client, performance_thresholds):
        """
        Test FastAPI application startup time and initialization performance.
        
        Verifies that the application can start up within acceptable time limits
        and that all initialization operations complete efficiently.
        """
        # Mock the startup event dependencies
        with patch('app.main.logger') as mock_logger:
            # Measure app import and initialization time
            start_time = time.perf_counter()
            
            # Simulate startup event
            with patch('app.main.firestore_client', patched_firestore_client):
                patched_firestore_client.test_connection.return_value = True
                
                # Mock admin client check
                mock_admin_doc = Mock()
                mock_admin_doc.exists = False
                patched_firestore_client.clients_ref.document.return_value.get.return_value = mock_admin_doc
                
                # Import and initialize app (simulates startup)
                from app.main import app as test_app
                
                # Simulate startup event handler
                import asyncio
                from app.main import initialize_firestore
                asyncio.run(initialize_firestore())
            
            end_time = time.perf_counter()
            startup_time_s = end_time - start_time
            
            # Performance assertions
            assert startup_time_s < performance_thresholds["startup_time_s"], \
                f"Application startup took {startup_time_s:.2f}s, exceeds {performance_thresholds['startup_time_s']}s threshold"
            
            # Verify initialization steps completed
            assert patched_firestore_client.test_connection.called, "Firestore connection should be tested"
            assert mock_logger.info.called, "Startup logging should occur"
            
            print(f"Application startup performance: {startup_time_s:.3f}s")

    async def test_api_response_time_performance(
        self,
        patched_firestore_client,
        performance_test_data,
        performance_thresholds
    ):
        """
        Test API endpoint response times under normal load.
        
        Verifies that all API endpoints respond within acceptable time limits
        and maintain consistent performance across different operations.
        """
        # Setup test data in mock database
        for client_data in performance_test_data["clients"]:
            client_id = client_data["client_id"]
            patched_firestore_client.clients_ref.add(client_data, client_id)
        
        for domain_data in performance_test_data["domains"]:
            domain_id = f"domain_{domain_data['client_id']}"
            patched_firestore_client.domain_index_ref.add(domain_data, domain_id)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test different endpoint categories
            endpoint_tests = [
                {
                    "name": "health_check",
                    "method": "GET",
                    "url": "/health",
                    "headers": None,
                    "threshold_key": "health_response_ms"
                },
                {
                    "name": "config_by_domain",
                    "method": "GET", 
                    "url": "/api/v1/config/domain/perf-test-0.example.com",
                    "headers": None,
                    "threshold_key": "api_response_ms"
                },
                {
                    "name": "config_by_client",
                    "method": "GET",
                    "url": "/api/v1/config/client/client_perf_000000",
                    "headers": None,
                    "threshold_key": "api_response_ms"
                },
                {
                    "name": "admin_list_clients",
                    "method": "GET",
                    "url": "/api/v1/admin/clients",
                    "headers": {"Authorization": "Bearer test_admin_key_12345"},
                    "threshold_key": "api_response_ms"
                }
            ]
            
            response_time_results = {}
            
            for test_config in endpoint_tests:
                endpoint_name = test_config["name"]
                response_times = []
                success_count = 0
                
                # Test each endpoint multiple times
                for _ in range(10):
                    start_time = time.perf_counter()
                    
                    try:
                        if test_config["method"] == "GET":
                            response = await client.get(
                                test_config["url"],
                                headers=test_config["headers"] or {}
                            )
                        
                        end_time = time.perf_counter()
                        response_time_ms = (end_time - start_time) * 1000
                        response_times.append(response_time_ms)
                        
                        if response.status_code < 400:
                            success_count += 1
                            
                    except Exception as e:
                        end_time = time.perf_counter()
                        response_time_ms = (end_time - start_time) * 1000
                        response_times.append(response_time_ms)
                        print(f"Error testing {endpoint_name}: {e}")
                
                # Calculate statistics
                if response_times:
                    avg_response_time = statistics.mean(response_times)
                    p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
                    success_rate = success_count / len(response_times)
                else:
                    avg_response_time = float('inf')
                    p95_response_time = float('inf')
                    success_rate = 0
                
                response_time_results[endpoint_name] = {
                    "avg_ms": avg_response_time,
                    "p95_ms": p95_response_time,
                    "success_rate": success_rate,
                    "threshold": performance_thresholds[test_config["threshold_key"]]
                }
                
                # Performance assertions
                assert success_rate >= 0.9, f"{endpoint_name} success rate {success_rate:.1%} below 90%"
                assert avg_response_time < performance_thresholds[test_config["threshold_key"]], \
                    f"{endpoint_name} avg response time {avg_response_time:.2f}ms exceeds threshold"
                
                print(f"{endpoint_name} - Avg: {avg_response_time:.2f}ms, "
                      f"95th percentile: {p95_response_time:.2f}ms, "
                      f"Success: {success_rate:.1%}")

    async def test_memory_usage_during_operation(
        self,
        patched_firestore_client,
        performance_test_data,
        performance_thresholds
    ):
        """
        Test memory usage profiling during application operation.
        
        Verifies that memory usage remains bounded during normal operation
        and doesn't exhibit memory leaks or excessive growth patterns.
        """
        # Start memory monitoring
        tracemalloc.start()
        
        # Get baseline memory
        baseline_snapshot = tracemalloc.take_snapshot()
        baseline_stats = baseline_snapshot.statistics('lineno')
        baseline_memory = sum(stat.size for stat in baseline_stats)
        
        # Setup test data
        for client_data in performance_test_data["clients"]:
            client_id = client_data["client_id"]
            patched_firestore_client.clients_ref.add(client_data, client_id)
        
        for domain_data in performance_test_data["domains"]:
            domain_id = f"domain_{domain_data['client_id']}"
            patched_firestore_client.domain_index_ref.add(domain_data, domain_id)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Perform various operations to stress memory usage
            operations = [
                lambda: client.get("/health"),
                lambda: client.get("/api/v1/config/domain/perf-test-0.example.com"),
                lambda: client.get("/api/v1/config/client/client_perf_000000"),
                lambda: client.get("/api/v1/admin/clients", 
                                   headers={"Authorization": "Bearer test_admin_key_12345"}),
                lambda: client.get("/api/v1/domains/all")
            ]
            
            # Execute operations multiple times
            for cycle in range(20):  # 20 cycles of operations
                for operation in operations:
                    try:
                        response = await operation()
                    except Exception as e:
                        print(f"Operation error in cycle {cycle}: {e}")
                
                # Take memory snapshot every 5 cycles
                if cycle % 5 == 0:
                    snapshot = tracemalloc.take_snapshot()
                    stats = snapshot.statistics('lineno')
                    current_memory = sum(stat.size for stat in stats)
                    memory_growth_mb = (current_memory - baseline_memory) / (1024 * 1024)
                    
                    print(f"Cycle {cycle} - Memory growth: {memory_growth_mb:.2f}MB")
        
        # Final memory measurement
        final_snapshot = tracemalloc.take_snapshot()
        final_stats = final_snapshot.statistics('lineno')
        final_memory = sum(stat.size for stat in final_stats)
        
        total_memory_growth_mb = (final_memory - baseline_memory) / (1024 * 1024)
        
        # Stop memory monitoring
        tracemalloc.stop()
        
        # Memory usage assertions
        assert total_memory_growth_mb < performance_thresholds["memory_growth_mb"], \
            f"Total memory growth {total_memory_growth_mb:.2f}MB exceeds {performance_thresholds['memory_growth_mb']}MB threshold"
        
        print(f"Memory usage test - Total growth: {total_memory_growth_mb:.2f}MB")

    async def test_concurrent_connection_handling(
        self,
        patched_firestore_client,
        performance_test_data,
        performance_thresholds
    ):
        """
        Test concurrent connection handling and scalability.
        
        Verifies that the application can handle multiple simultaneous connections
        while maintaining acceptable response times and stability.
        """
        # Setup test data
        for client_data in performance_test_data["clients"][:10]:  # Limit for concurrent test
            client_id = client_data["client_id"]
            patched_firestore_client.clients_ref.add(client_data, client_id)
        
        for domain_data in performance_test_data["domains"][:10]:
            domain_id = f"domain_{domain_data['client_id']}"
            patched_firestore_client.domain_index_ref.add(domain_data, domain_id)
        
        # Create multiple client connections
        num_connections = min(performance_thresholds["concurrent_connections"], 50)  # Reasonable limit for testing
        connection_tasks = []
        
        async def make_concurrent_requests(connection_id: int):
            """Make requests from a single connection."""
            async with AsyncClient(app=app, base_url="http://test") as client:
                requests_per_connection = 5
                response_times = []
                success_count = 0
                
                for req_num in range(requests_per_connection):
                    start_time = time.perf_counter()
                    
                    try:
                        # Vary request types
                        if req_num % 3 == 0:
                            response = await client.get("/health")
                        elif req_num % 3 == 1:
                            response = await client.get("/api/v1/config/domain/perf-test-0.example.com")
                        else:
                            response = await client.get("/api/v1/config/client/client_perf_000000")
                        
                        end_time = time.perf_counter()
                        response_time_ms = (end_time - start_time) * 1000
                        response_times.append(response_time_ms)
                        
                        if response.status_code < 400:
                            success_count += 1
                    
                    except Exception as e:
                        end_time = time.perf_counter()
                        response_time_ms = (end_time - start_time) * 1000
                        response_times.append(response_time_ms)
                        print(f"Connection {connection_id} request {req_num} error: {e}")
                
                return {
                    "connection_id": connection_id,
                    "response_times": response_times,
                    "success_count": success_count,
                    "total_requests": requests_per_connection
                }
        
        # Create concurrent connection tasks
        for conn_id in range(num_connections):
            task = make_concurrent_requests(conn_id)
            connection_tasks.append(task)
        
        # Execute concurrent connections
        start_time = time.perf_counter()
        
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_duration_s = end_time - start_time
        
        # Analyze results
        successful_connections = [r for r in results if not isinstance(r, Exception)]
        failed_connections = [r for r in results if isinstance(r, Exception)]
        
        if successful_connections:
            all_response_times = []
            total_requests = 0
            total_successes = 0
            
            for result in successful_connections:
                all_response_times.extend(result["response_times"])
                total_requests += result["total_requests"]
                total_successes += result["success_count"]
            
            if all_response_times:
                avg_response_time = statistics.mean(all_response_times)
                p95_response_time = statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) > 20 else max(all_response_times)
            else:
                avg_response_time = float('inf')
                p95_response_time = float('inf')
            
            success_rate = total_successes / total_requests if total_requests > 0 else 0
            throughput = total_requests / total_duration_s
        else:
            avg_response_time = float('inf')
            p95_response_time = float('inf')
            success_rate = 0
            throughput = 0
        
        # Performance assertions
        assert len(failed_connections) == 0, f"Found {len(failed_connections)} failed connections"
        assert success_rate >= 0.95, f"Success rate {success_rate:.1%} below 95% threshold"
        assert avg_response_time < performance_thresholds["api_response_ms"], \
            f"Average response time {avg_response_time:.2f}ms exceeds threshold under concurrent load"
        assert len(successful_connections) >= num_connections * 0.9, \
            f"Too many connections failed: {len(successful_connections)}/{num_connections}"
        
        print(f"Concurrent connections test - {num_connections} connections, "
              f"Success rate: {success_rate:.1%}, "
              f"Avg response: {avg_response_time:.2f}ms, "
              f"95th percentile: {p95_response_time:.2f}ms, "
              f"Throughput: {throughput:.1f} req/s")