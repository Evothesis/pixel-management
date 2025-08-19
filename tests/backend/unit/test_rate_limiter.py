"""
Rate Limiter Performance Tests - Phase 5

Performance tests for rate limiting functionality in the pixel management system.
Tests sliding window algorithm efficiency, burst handling, memory usage, and cleanup
operations to ensure optimal rate limiting performance under various load conditions.

Performance Requirements:
- Rate limit check: <10ms
- Memory usage: bounded growth
- Cleanup efficiency: <50ms
- Burst handling: consistent enforcement

Test Categories:
1. Sliding window algorithm performance with timing verification
2. Burst request handling with fairness testing
3. Memory efficiency and cleanup operations profiling
4. Rate limiter cleanup performance and effectiveness
"""

import pytest
import time
import threading
import tracemalloc
import statistics
from unittest.mock import Mock, patch
from collections import deque
from typing import Dict, List, Tuple

from app.rate_limiter import RateLimitMiddleware
from fastapi import Request


@pytest.mark.performance
@pytest.mark.unit
class TestRateLimiterPerformance:
    """Performance tests for rate limiting functionality."""

    @pytest.fixture
    def performance_thresholds(self):
        """Performance thresholds for rate limiting operations."""
        return {
            "rate_check_ms": 10,
            "cleanup_operation_ms": 50,
            "memory_growth_mb": 5,
            "burst_handling_ms": 20
        }

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a RateLimitMiddleware instance for testing."""
        mock_app = Mock()
        return RateLimitMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request for testing."""
        request = Mock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {}
        request.url.path = "/api/v1/admin/clients"
        return request

    def test_sliding_window_algorithm_performance(self, mock_rate_limiter, performance_thresholds):
        """
        Test sliding window algorithm performance under normal load.
        
        Verifies that the sliding window rate limiting algorithm performs
        efficiently with consistent timing for rate limit checks.
        """
        test_ip = "192.168.1.100"
        test_path = "/api/v1/admin/clients"
        current_time = time.time()
        
        # Clear any existing state
        mock_rate_limiter.request_history.clear()
        
        check_times = []
        results = []
        
        # Perform multiple rate limit checks
        for i in range(100):
            start_time = time.perf_counter()
            
            is_limited, retry_after = mock_rate_limiter.is_rate_limited(
                test_ip, test_path, current_time + (i * 0.5)
            )
            
            end_time = time.perf_counter()
            check_time_ms = (end_time - start_time) * 1000
            check_times.append(check_time_ms)
            results.append((is_limited, retry_after))
        
        # Analyze performance metrics
        avg_check_time = statistics.mean(check_times)
        max_check_time = max(check_times)
        p95_check_time = statistics.quantiles(check_times, n=20)[18] if len(check_times) > 20 else max_check_time
        
        # Performance assertions
        assert avg_check_time < performance_thresholds["rate_check_ms"], \
            f"Average rate check time {avg_check_time:.3f}ms exceeds {performance_thresholds['rate_check_ms']}ms threshold"
        assert max_check_time < performance_thresholds["rate_check_ms"] * 2, \
            f"Max rate check time {max_check_time:.3f}ms too high"
        assert p95_check_time < performance_thresholds["rate_check_ms"] * 1.5, \
            f"95th percentile rate check time {p95_check_time:.3f}ms too high"
        
        # Verify rate limiting logic
        allowed_requests = [r for r in results if not r[0]]  # not is_limited
        blocked_requests = [r for r in results if r[0]]      # is_limited
        
        # Should allow requests up to the limit (30 for admin endpoints)
        assert len(blocked_requests) > 0, "Rate limiting should eventually block requests"
        assert len(allowed_requests) <= 30, f"Too many requests allowed: {len(allowed_requests)}"
        
        print(f"Sliding window performance - Avg: {avg_check_time:.3f}ms, "
              f"95th percentile: {p95_check_time:.3f}ms, "
              f"Allowed: {len(allowed_requests)}, Blocked: {len(blocked_requests)}")

    def test_burst_request_handling_performance(self, mock_rate_limiter, performance_thresholds):
        """
        Test burst request handling performance and fairness.
        
        Verifies that the rate limiter handles sudden bursts of requests
        efficiently while maintaining consistent enforcement timing.
        """
        test_ip = "192.168.1.200"
        test_path = "/api/v1/config/domain/example.com"
        burst_time = time.time()
        
        # Clear existing state
        mock_rate_limiter.request_history.clear()
        
        # Simulate burst of requests (all at same timestamp)
        burst_size = 75  # Exceeds 60 req/min limit for config endpoints
        burst_results = []
        burst_times = []
        
        for i in range(burst_size):
            start_time = time.perf_counter()
            
            is_limited, retry_after = mock_rate_limiter.is_rate_limited(
                test_ip, test_path, burst_time + (i * 0.01)  # Small time increments
            )
            
            end_time = time.perf_counter()
            processing_time_ms = (end_time - start_time) * 1000
            
            burst_results.append((is_limited, retry_after, processing_time_ms))
            burst_times.append(processing_time_ms)
        
        # Analyze burst handling performance
        avg_burst_time = statistics.mean(burst_times)
        max_burst_time = max(burst_times)
        
        allowed_in_burst = [r for r in burst_results if not r[0]]
        blocked_in_burst = [r for r in burst_results if r[0]]
        
        # Performance assertions
        assert avg_burst_time < performance_thresholds["burst_handling_ms"], \
            f"Average burst handling time {avg_burst_time:.3f}ms exceeds {performance_thresholds['burst_handling_ms']}ms threshold"
        assert max_burst_time < performance_thresholds["burst_handling_ms"] * 2, \
            f"Max burst handling time {max_burst_time:.3f}ms too high"
        
        # Fairness and correctness assertions
        assert len(allowed_in_burst) <= 60, f"Too many requests allowed in burst: {len(allowed_in_burst)}"
        assert len(blocked_in_burst) > 0, "Burst should trigger rate limiting"
        
        # Verify retry_after values are reasonable for blocked requests
        retry_after_values = [r[1] for r in blocked_in_burst if r[1] > 0]
        if retry_after_values:
            avg_retry_after = statistics.mean(retry_after_values)
            assert 1 <= avg_retry_after <= 60, f"Retry after values not reasonable: avg={avg_retry_after}"
        
        print(f"Burst handling performance - Avg: {avg_burst_time:.3f}ms, "
              f"Max: {max_burst_time:.3f}ms, "
              f"Allowed: {len(allowed_in_burst)}, Blocked: {len(blocked_in_burst)}")

    def test_rate_limiter_memory_efficiency(self, mock_rate_limiter, performance_thresholds):
        """
        Test rate limiter memory usage efficiency and bounded growth.
        
        Verifies that memory usage remains bounded as request history grows
        and that cleanup operations effectively manage memory consumption.
        """
        # Start memory tracking
        tracemalloc.start()
        
        # Get baseline memory
        baseline_snapshot = tracemalloc.take_snapshot()
        baseline_stats = baseline_snapshot.statistics('lineno')
        baseline_memory = sum(stat.size for stat in baseline_stats)
        
        # Clear existing state
        mock_rate_limiter.request_history.clear()
        
        # Simulate many requests from different IPs to grow request history
        base_time = time.time()
        ip_count = 50
        requests_per_ip = 20
        
        for ip_num in range(ip_count):
            test_ip = f"192.168.1.{ip_num + 1}"
            test_path = "/api/v1/config/domain/example.com"
            
            for req_num in range(requests_per_ip):
                timestamp = base_time + (req_num * 2)  # 2-second intervals
                is_limited, retry_after = mock_rate_limiter.is_rate_limited(
                    test_ip, test_path, timestamp
                )
        
        # Measure memory after loading
        loaded_snapshot = tracemalloc.take_snapshot()
        loaded_stats = loaded_snapshot.statistics('lineno')
        loaded_memory = sum(stat.size for stat in loaded_stats)
        
        # Trigger cleanup
        cleanup_time = base_time + 3600  # 1 hour later
        mock_rate_limiter.cleanup_expired(cleanup_time)
        
        # Measure memory after cleanup
        cleaned_snapshot = tracemalloc.take_snapshot()
        cleaned_stats = cleaned_snapshot.statistics('lineno')
        cleaned_memory = sum(stat.size for stat in cleaned_stats)
        
        # Calculate memory changes
        memory_growth_mb = (loaded_memory - baseline_memory) / (1024 * 1024)
        memory_freed_mb = (loaded_memory - cleaned_memory) / (1024 * 1024)
        final_growth_mb = (cleaned_memory - baseline_memory) / (1024 * 1024)
        
        # Stop memory tracking
        tracemalloc.stop()
        
        # Memory efficiency assertions
        assert memory_growth_mb < performance_thresholds["memory_growth_mb"], \
            f"Memory growth {memory_growth_mb:.2f}MB exceeds {performance_thresholds['memory_growth_mb']}MB threshold"
        assert memory_freed_mb > 0, "Cleanup should free some memory"
        assert final_growth_mb < memory_growth_mb, "Final memory should be less than peak usage"
        
        # Verify request history structure
        assert len(mock_rate_limiter.request_history) <= ip_count, \
            "Request history should not exceed number of unique IPs after cleanup"
        
        print(f"Memory efficiency - Growth: {memory_growth_mb:.2f}MB, "
              f"Freed by cleanup: {memory_freed_mb:.2f}MB, "
              f"Final growth: {final_growth_mb:.2f}MB")

    def test_cleanup_operation_performance(self, mock_rate_limiter, performance_thresholds):
        """
        Test cleanup operation performance and effectiveness.
        
        Verifies that cleanup operations complete within acceptable time limits
        and effectively remove expired entries from request history.
        """
        # Clear existing state
        mock_rate_limiter.request_history.clear()
        
        # Create large request history with mixed timestamps
        base_time = time.time()
        old_time = base_time - 3600  # 1 hour ago (should be cleaned)
        recent_time = base_time - 30  # 30 seconds ago (should remain)
        
        # Add old entries (should be cleaned up)
        for ip_num in range(100):
            test_ip = f"192.168.10.{ip_num + 1}"
            history = deque()
            
            # Add old entries
            for req in range(10):
                timestamp = old_time + (req * 5)  # 5-second intervals
                history.append((timestamp, "/api/v1/admin/clients"))
            
            # Add recent entries
            for req in range(5):
                timestamp = recent_time + (req * 2)  # 2-second intervals
                history.append((timestamp, "/api/v1/admin/clients"))
            
            mock_rate_limiter.request_history[test_ip] = history
        
        # Measure cleanup performance
        cleanup_times = []
        entries_before_cleanup = sum(len(hist) for hist in mock_rate_limiter.request_history.values())
        
        # Perform multiple cleanup operations
        for i in range(10):
            cleanup_time = base_time + (i * 10)  # Different cleanup times
            
            start_time = time.perf_counter()
            mock_rate_limiter.cleanup_expired(cleanup_time)
            end_time = time.perf_counter()
            
            cleanup_duration_ms = (end_time - start_time) * 1000
            cleanup_times.append(cleanup_duration_ms)
        
        entries_after_cleanup = sum(len(hist) for hist in mock_rate_limiter.request_history.values())
        
        # Analyze cleanup performance
        avg_cleanup_time = statistics.mean(cleanup_times)
        max_cleanup_time = max(cleanup_times)
        cleanup_ratio = (entries_before_cleanup - entries_after_cleanup) / entries_before_cleanup
        
        # Performance assertions
        assert avg_cleanup_time < performance_thresholds["cleanup_operation_ms"], \
            f"Average cleanup time {avg_cleanup_time:.3f}ms exceeds {performance_thresholds['cleanup_operation_ms']}ms threshold"
        assert max_cleanup_time < performance_thresholds["cleanup_operation_ms"] * 2, \
            f"Max cleanup time {max_cleanup_time:.3f}ms too high"
        
        # Effectiveness assertions
        assert cleanup_ratio > 0.5, f"Cleanup should remove significant entries, only {cleanup_ratio:.1%} removed"
        assert entries_after_cleanup > 0, "Some recent entries should remain after cleanup"
        assert entries_after_cleanup < entries_before_cleanup, "Cleanup should reduce entry count"
        
        # Verify no empty deques remain (memory efficiency)
        empty_histories = [ip for ip, hist in mock_rate_limiter.request_history.items() if len(hist) == 0]
        assert len(empty_histories) == 0, f"Cleanup should remove empty histories, found {len(empty_histories)}"
        
        print(f"Cleanup performance - Avg: {avg_cleanup_time:.3f}ms, "
              f"Max: {max_cleanup_time:.3f}ms, "
              f"Cleanup ratio: {cleanup_ratio:.1%}, "
              f"Entries: {entries_before_cleanup} -> {entries_after_cleanup}")