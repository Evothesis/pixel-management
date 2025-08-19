"""
Global Test Configuration

Shared fixtures and configuration for all tests in the Pixel Management system.
Provides common test utilities, environment setup, and cross-cutting concerns.
"""

import os
import sys
import pytest
from datetime import datetime
from typing import Generator

# Add backend app to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Environment setup for testing
os.environ["TESTING"] = "true"
os.environ["ADMIN_API_KEY"] = "test_admin_key_12345"
os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment variables for the entire test session."""
    original_env = os.environ.copy()
    
    # Test-specific environment variables
    test_env = {
        "TESTING": "true",
        "ADMIN_API_KEY": "test_admin_key_12345",
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "FIRESTORE_EMULATOR_HOST": "localhost:8080",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:8080",
        "COLLECTION_API_URL": "http://localhost:8001/collect"
    }
    
    # Update environment
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_timestamp():
    """Provide a consistent timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0)


@pytest.fixture
def sample_client_id():
    """Provide a consistent test client ID."""
    return "client_test123456"


@pytest.fixture
def sample_domain():
    """Provide a consistent test domain."""
    return "example.com"


@pytest.fixture
def valid_admin_headers():
    """Provide valid admin authentication headers."""
    return {
        "Authorization": "Bearer test_admin_key_12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def invalid_admin_headers():
    """Provide invalid admin authentication headers."""
    return {
        "Authorization": "Bearer invalid_key",
        "Content-Type": "application/json"
    }


@pytest.fixture
def no_auth_headers():
    """Provide headers without authentication."""
    return {
        "Content-Type": "application/json"
    }


# Performance testing utilities
@pytest.fixture
def performance_threshold():
    """Define performance thresholds for testing."""
    return {
        "domain_lookup_ms": 100,
        "pixel_generation_ms": 150,
        "api_response_ms": 500,
        "concurrent_requests": 100
    }


# Test data cleanup utilities
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically clean up test data after each test."""
    yield
    # Cleanup logic will be implemented in backend-specific conftest.py


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "auth: Authentication tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "critical: Critical path tests requiring 95% coverage"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically apply markers based on test location and names."""
    for item in items:
        # Apply markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Apply markers based on test names
        if "auth" in item.name.lower():
            item.add_marker(pytest.mark.auth)
            item.add_marker(pytest.mark.critical)
        
        if any(keyword in item.name.lower() for keyword in ["domain_lookup", "pixel_generation", "client_create"]):
            item.add_marker(pytest.mark.critical)


# Test reporting utilities
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add extra information to test reports."""
    outcome = yield
    rep = outcome.get_result()
    
    # Add custom attributes for reporting
    if rep.when == "call":
        rep.test_file = str(item.fspath)
        rep.test_category = getattr(item, 'pytestmark', [])