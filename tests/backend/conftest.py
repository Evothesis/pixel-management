"""
Backend Test Configuration

Backend-specific fixtures for FastAPI application testing.
Provides mocked Firestore client, test HTTP client, and test data factories.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, Generator, List
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
import factory
from factory import fuzzy

# Import the FastAPI app and dependencies
from app.main import app
from app.firestore_client import firestore_client


class MockFirestoreDocument:
    """Mock Firestore document for testing."""
    
    def __init__(self, data: Dict[str, Any] = None, exists: bool = True):
        self._data = data or {}
        self.exists = exists
        self.id = data.get('id', 'mock_doc_id') if data else 'mock_doc_id'
    
    def to_dict(self) -> Dict[str, Any]:
        return self._data.copy()
    
    def get(self):
        return self
    
    def set(self, data: Dict[str, Any]):
        self._data.update(data)
        return self
    
    def update(self, data: Dict[str, Any]):
        self._data.update(data)
        return self
    
    def delete(self):
        self.exists = False
        return self


class MockFirestoreCollection:
    """Mock Firestore collection for testing."""
    
    def __init__(self):
        self._documents: Dict[str, MockFirestoreDocument] = {}
        self._query_filters = []
    
    def document(self, doc_id: str) -> MockFirestoreDocument:
        if doc_id not in self._documents:
            self._documents[doc_id] = MockFirestoreDocument(exists=False)
        return self._documents[doc_id]
    
    def add(self, data: Dict[str, Any], doc_id: str = None) -> MockFirestoreDocument:
        if not doc_id:
            doc_id = f"auto_id_{len(self._documents)}"
        
        doc = MockFirestoreDocument(data)
        doc.id = doc_id
        self._documents[doc_id] = doc
        return doc
    
    def collection(self, collection_name: str):
        # For subcollections
        return MockFirestoreCollection()
    
    def where(self, field: str, operator: str, value: Any):
        # Store filter for stream() method
        self._query_filters.append((field, operator, value))
        return self
    
    def order_by(self, field: str, direction=None):
        return self
    
    def limit(self, count: int):
        return self
    
    def stream(self) -> List[MockFirestoreDocument]:
        """Return documents matching current filters."""
        if not self._query_filters:
            return list(self._documents.values())
        
        results = []
        for doc in self._documents.values():
            if not doc.exists:
                continue
                
            matches_all_filters = True
            for field, operator, value in self._query_filters:
                doc_value = doc.to_dict().get(field)
                
                if operator == '==' and doc_value != value:
                    matches_all_filters = False
                    break
                elif operator == '!=' and doc_value == value:
                    matches_all_filters = False
                    break
                elif operator == '>' and (doc_value is None or doc_value <= value):
                    matches_all_filters = False
                    break
                elif operator == '<' and (doc_value is None or doc_value >= value):
                    matches_all_filters = False
                    break
            
            if matches_all_filters:
                results.append(doc)
        
        # Clear filters after use
        self._query_filters = []
        return results
    
    def clear(self):
        """Clear all documents (for test cleanup)."""
        self._documents.clear()


@pytest.fixture
def mock_firestore_client():
    """Provide a mocked Firestore client for testing."""
    mock_client = Mock()
    
    # Create mock collections
    clients_collection = MockFirestoreCollection()
    domain_index_collection = MockFirestoreCollection()
    audit_log_collection = MockFirestoreCollection()
    
    # Set up collection references
    mock_client.clients_ref = clients_collection
    mock_client.domain_index_ref = domain_index_collection
    mock_client.audit_log_ref = audit_log_collection
    
    # Mock connection test
    mock_client.test_connection.return_value = True
    
    return mock_client


@pytest.fixture
def patched_firestore_client(mock_firestore_client):
    """Patch the global firestore_client with mock."""
    with patch('app.firestore_client.firestore_client', mock_firestore_client):
        # Also patch imports in main.py
        with patch('app.main.firestore_client', mock_firestore_client):
            yield mock_firestore_client


@pytest.fixture
async def test_client(patched_firestore_client):
    """Provide FastAPI test client with mocked dependencies."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_client(test_client, valid_admin_headers):
    """Provide authenticated test client."""
    # Set up the client with auth headers
    test_client.headers.update(valid_admin_headers)
    yield test_client


# Test Data Factories
class ClientFactory(factory.Factory):
    """Factory for generating test client data."""
    
    class Meta:
        model = dict
    
    client_id = factory.Sequence(lambda n: f"client_test_{n:06d}")
    name = factory.Faker('company')
    email = factory.Faker('email')
    client_type = fuzzy.FuzzyChoice(['ecommerce', 'saas', 'media', 'admin'])
    owner = factory.Faker('email')
    billing_entity = factory.LazyAttribute(lambda obj: obj.owner)
    privacy_level = fuzzy.FuzzyChoice(['standard', 'gdpr', 'hipaa'])
    ip_collection_enabled = True
    consent_required = factory.LazyAttribute(lambda obj: obj.privacy_level in ['gdpr', 'hipaa'])
    features = factory.Dict({
        'analytics': True,
        'conversion_tracking': True,
        'custom_events': fuzzy.FuzzyChoice([True, False])
    })
    deployment_type = fuzzy.FuzzyChoice(['shared', 'dedicated'])
    vm_hostname = factory.Maybe(
        'deployment_type',
        yes_declaration=factory.Faker('domain_name'),
        no_declaration=None
    )
    billing_rate_per_1k = fuzzy.FuzzyDecimal(0.005, 0.05, 3)
    created_at = factory.LazyFunction(datetime.utcnow)
    is_active = True
    
    @factory.post_generation
    def ip_salt(obj, create, extracted, **kwargs):
        """Add IP salt for privacy levels that require it."""
        if obj['privacy_level'] in ['gdpr', 'hipaa']:
            import secrets
            obj['ip_salt'] = secrets.token_urlsafe(32)


class DomainFactory(factory.Factory):
    """Factory for generating test domain data."""
    
    class Meta:
        model = dict
    
    domain = factory.Faker('domain_name')
    is_primary = fuzzy.FuzzyChoice([True, False])
    created_at = factory.LazyFunction(datetime.utcnow)


@pytest.fixture
def client_factory():
    """Provide client factory for creating test client data."""
    return ClientFactory


@pytest.fixture
def domain_factory():
    """Provide domain factory for creating test domain data."""
    return DomainFactory


@pytest.fixture
def sample_client_data(client_factory):
    """Provide sample client data for testing."""
    return client_factory()


@pytest.fixture
def sample_domain_data(domain_factory):
    """Provide sample domain data for testing."""
    return domain_factory()


@pytest.fixture
def multiple_clients(client_factory):
    """Provide multiple test clients."""
    return [client_factory() for _ in range(5)]


@pytest.fixture
def client_with_domains(mock_firestore_client, client_factory, domain_factory):
    """Create a client with multiple domains in the mock database."""
    client_data = client_factory()
    client_id = client_data['client_id']
    
    # Add client to mock database
    mock_firestore_client.clients_ref.add(client_data, client_id)
    
    # Add domains
    domains = []
    for i in range(3):
        domain_data = domain_factory()
        domain_data['is_primary'] = (i == 0)  # First domain is primary
        domain_name = domain_data['domain']
        
        # Add to client's domains subcollection
        domain_doc_id = f"{client_id}_{domain_name.replace('.', '_')}"
        mock_firestore_client.clients_ref.document(client_id).collection('domains').add(
            domain_data, domain_doc_id
        )
        
        # Add to domain index
        index_data = {
            'client_id': client_id,
            'domain': domain_name,
            'is_primary': domain_data['is_primary'],
            'created_at': domain_data['created_at']
        }
        mock_firestore_client.domain_index_ref.add(index_data, domain_doc_id)
        domains.append(domain_data)
    
    return {
        'client': client_data,
        'domains': domains
    }


@pytest.fixture(autouse=True)
def cleanup_mock_firestore(mock_firestore_client):
    """Automatically clean up mock Firestore data after each test."""
    yield
    # Clear all collections
    mock_firestore_client.clients_ref.clear()
    mock_firestore_client.domain_index_ref.clear()
    mock_firestore_client.audit_log_ref.clear()


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Utility for timing operations in performance tests."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return (self.end_time - self.start_time) * 1000  # Return milliseconds
    
    return Timer


# Security testing utilities
@pytest.fixture
def security_test_payloads():
    """Provide common security test payloads."""
    return {
        'sql_injection': [
            "'; DROP TABLE clients; --",
            "' OR '1'='1",
            "1; DELETE FROM clients WHERE 1=1 --"
        ],
        'xss_injection': [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ],
        'path_traversal': [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd"
        ],
        'oversized_payload': "A" * 10000,
        'invalid_json': '{"incomplete": json',
        'invalid_utf8': b'\xff\xfe\xfd\xfc'.decode('utf-8', errors='ignore')
    }


# Authentication testing utilities
@pytest.fixture
def auth_test_scenarios():
    """Provide various authentication test scenarios."""
    return {
        'valid_key': "Bearer test_admin_key_12345",
        'invalid_key': "Bearer invalid_key_12345",
        'malformed_header': "InvalidBearer test_key",
        'empty_key': "Bearer ",
        'missing_bearer': "test_admin_key_12345",
        'sql_injection_key': "Bearer '; DROP TABLE admin; --",
        'xss_key': "Bearer <script>alert('xss')</script>"
    }