# Pixel Management - Comprehensive Unit Test Implementation Plan

## Testing Framework Requirements

### Backend (Python/FastAPI)
- **Framework**: pytest >= 7.4.0
- **Required Packages**:
  ```
  pytest==7.4.0
  pytest-asyncio==0.21.0
  pytest-cov==4.1.0
  httpx==0.24.1
  pytest-mock==3.11.1
  fakeredis==2.18.1
  pytest-env==0.8.2
  freezegun==1.2.2
  factory-boy==3.3.0
  ```

### Frontend (React)
- **Framework**: Jest + React Testing Library
- **Required Packages**:
  ```json
  "@testing-library/react": "^14.0.0",
  "@testing-library/jest-dom": "^6.0.0",
  "@testing-library/user-event": "^14.0.0",
  "jest": "^29.0.0",
  "msw": "^1.3.0"
  ```

## Backend Unit Tests

### 1. Authentication Module Tests (`test_auth.py`)

#### Test 1.1: Valid API Key Authentication
```python
def test_valid_api_key_authentication():
    """
    Test that valid API key grants access to protected endpoints.
    
    Setup:
    - Set ADMIN_API_KEY environment variable
    - Create test client with valid Bearer token
    
    Execution:
    - Send request to protected endpoint with valid API key
    
    Pass Conditions:
    - Response status code == 200
    - Response contains expected data
    - No authentication error in response
    """
```

#### Test 1.2: Invalid API Key Rejection
```python
def test_invalid_api_key_rejection():
    """
    Test that invalid API keys are rejected with proper error.
    
    Setup:
    - Set ADMIN_API_KEY environment variable
    - Create test client with invalid Bearer token
    
    Execution:
    - Send request to protected endpoint with invalid API key
    
    Pass Conditions:
    - Response status code == 403
    - Response contains error message "Invalid API key"
    - Request is logged as unauthorized attempt
    """
```

#### Test 1.3: Missing API Key Handling
```python
def test_missing_api_key_handling():
    """
    Test that missing API keys return proper 401 error.
    
    Setup:
    - Set ADMIN_API_KEY environment variable
    - Create test client without Authorization header
    
    Execution:
    - Send request to protected endpoint without API key
    
    Pass Conditions:
    - Response status code == 401
    - Response contains "Not authenticated" error
    - No sensitive information leaked in error
    """
```

#### Test 1.4: Health Endpoint Bypass
```python
def test_health_endpoint_requires_no_auth():
    """
    Test that health endpoint works without authentication.
    
    Setup:
    - Create test client without any authentication
    
    Execution:
    - Send GET request to /health endpoint
    
    Pass Conditions:
    - Response status code == 200
    - Response contains "status": "healthy"
    - No authentication required
    """
```

### 2. Client Management Tests (`test_client_operations.py`)

#### Test 2.1: Create Client with Valid Data
```python
def test_create_client_valid_data():
    """
    Test client creation with all required fields.
    
    Setup:
    - Mock Firestore client
    - Prepare valid client data with all privacy levels
    
    Execution:
    - POST to /api/v1/admin/clients with valid payload
    
    Pass Conditions:
    - Response status code == 201
    - Client ID generated and returned
    - Client document created in Firestore
    - Audit log entry created
    - Domain index initialized
    """
```

#### Test 2.2: Create Client Data Validation
```python
def test_create_client_validation():
    """
    Test that invalid client data is rejected.
    
    Test Cases:
    - Missing required fields (name, owner, privacy_level)
    - Invalid privacy_level (not in standard/gdpr/hipaa)
    - Invalid deployment_type (not in shared/dedicated)
    - SQL injection attempts in string fields
    
    Pass Conditions (each case):
    - Response status code == 422
    - Specific validation error message returned
    - No data written to database
    """
```

#### Test 2.3: Update Client Configuration
```python
def test_update_client_configuration():
    """
    Test client configuration updates.
    
    Setup:
    - Create test client in Firestore
    - Prepare update payload
    
    Execution:
    - PUT to /api/v1/admin/clients/{client_id}
    
    Pass Conditions:
    - Response status code == 200
    - Only specified fields updated
    - Unspecified fields remain unchanged
    - Audit log contains changes
    - Updated timestamp reflects change
    """
```

#### Test 2.4: Client Deactivation
```python
def test_client_deactivation():
    """
    Test soft delete/deactivation of clients.
    
    Setup:
    - Create active client with domains
    
    Execution:
    - PUT to /api/v1/admin/clients/{client_id} with is_active=false
    
    Pass Conditions:
    - Client marked as inactive
    - Associated domains remain but marked inactive
    - Domain index updated
    - Deactivation logged in audit trail
    """
```

### 3. Domain Management Tests (`test_domain_operations.py`)

#### Test 3.1: Add Domain to Client
```python
def test_add_domain_to_client():
    """
    Test domain addition with validation.
    
    Setup:
    - Create test client
    - Prepare valid domain
    
    Execution:
    - POST to /api/v1/admin/clients/{client_id}/domains
    
    Pass Conditions:
    - Response status code == 201
    - Domain added to client's domain list
    - Domain index updated for O(1) lookup
    - Domain normalized (lowercase, no spaces)
    - Audit log entry created
    """
```

#### Test 3.2: Domain Format Validation
```python
def test_domain_format_validation():
    """
    Test that invalid domain formats are rejected.
    
    Test Cases:
    - Domain with protocol (http://example.com)
    - Domain with path (/path)
    - Invalid characters (!@#$)
    - Empty string
    - Subdomain depth > 5
    
    Pass Conditions (each case):
    - Response status code == 422
    - Specific validation error returned
    - No domain added to database
    """
```

#### Test 3.3: Duplicate Domain Prevention
```python
def test_duplicate_domain_prevention():
    """
    Test that domains can't be assigned to multiple clients.
    
    Setup:
    - Create two test clients
    - Add domain to first client
    
    Execution:
    - Attempt to add same domain to second client
    
    Pass Conditions:
    - Response status code == 409
    - Error message indicates domain already assigned
    - Domain remains with original client only
    """
```

#### Test 3.4: Primary Domain Designation
```python
def test_primary_domain_designation():
    """
    Test primary domain assignment and uniqueness.
    
    Setup:
    - Create client with multiple domains
    
    Execution:
    - Set one domain as primary
    - Attempt to set second domain as primary
    
    Pass Conditions:
    - Only one primary domain per client
    - Previous primary automatically unset
    - Primary domain flag properly stored
    """
```

### 4. Domain Authorization Tests (`test_domain_authorization.py`)

#### Test 4.1: Authorized Domain Lookup
```python
def test_authorized_domain_lookup():
    """
    Test O(1) domain authorization check.
    
    Setup:
    - Create client with authorized domain
    - Mock domain in domain_index
    
    Execution:
    - GET to /api/v1/config/domain/{domain}
    
    Pass Conditions:
    - Response time < 100ms
    - Correct client_id returned
    - Privacy settings included
    - No authentication required
    """
```

#### Test 4.2: Unauthorized Domain Handling
```python
def test_unauthorized_domain_handling():
    """
    Test response for unauthorized domains.
    
    Setup:
    - Ensure domain not in domain_index
    
    Execution:
    - GET to /api/v1/config/domain/{unknown_domain}
    
    Pass Conditions:
    - Response status code == 404
    - No client information leaked
    - Response time < 100ms
    """
```

### 5. Pixel Generation Tests (`test_pixel_serving.py`)

#### Test 5.1: Dynamic Pixel Generation
```python
def test_dynamic_pixel_generation():
    """
    Test JavaScript pixel generation with client config.
    
    Setup:
    - Create client with specific privacy settings
    
    Execution:
    - GET to /pixel/{client_id}/tracking.js
    
    Pass Conditions:
    - Valid JavaScript returned
    - Contains correct client_id
    - Privacy settings embedded correctly
    - Content-Type header = application/javascript
    - Minified for production
    """
```

#### Test 5.2: Privacy Level Enforcement in Pixel
```python
def test_privacy_level_enforcement_in_pixel():
    """
    Test that pixel respects privacy configuration.
    
    Test Cases:
    - GDPR: IP hashing code included
    - HIPAA: Enhanced encryption included
    - Standard: Full tracking enabled
    
    Pass Conditions (each case):
    - Correct privacy code blocks present
    - Consent management for GDPR
    - No PII collection for HIPAA
    """
```

### 6. Firestore Integration Tests (`test_firestore_operations.py`)

#### Test 6.1: Transaction Atomicity
```python
def test_firestore_transaction_atomicity():
    """
    Test atomic operations across collections.
    
    Setup:
    - Mock Firestore with transaction support
    
    Execution:
    - Perform multi-collection update in transaction
    - Force failure midway
    
    Pass Conditions:
    - All changes rolled back on failure
    - No partial updates persisted
    - Error properly propagated
    """
```

#### Test 6.2: Concurrent Update Handling
```python
def test_concurrent_update_handling():
    """
    Test optimistic locking and concurrent updates.
    
    Setup:
    - Create client document
    - Simulate two concurrent update requests
    
    Execution:
    - Both requests attempt to update same document
    
    Pass Conditions:
    - One update succeeds
    - Second update retries or fails gracefully
    - No data corruption
    - Final state consistent
    """
```

### 7. Rate Limiting Tests (`test_rate_limiting.py`)

#### Test 7.1: Rate Limit Enforcement
```python
def test_rate_limit_enforcement():
    """
    Test that rate limits are properly enforced.
    
    Setup:
    - Configure rate limit (10 requests/minute)
    
    Execution:
    - Send 15 requests rapidly
    
    Pass Conditions:
    - First 10 requests succeed
    - Requests 11-15 return 429 status
    - Retry-After header present
    - Rate limit resets after window
    """
```

### 8. CORS Configuration Tests (`test_cors.py`)

#### Test 8.1: CORS Headers Validation
```python
def test_cors_headers_validation():
    """
    Test CORS configuration for production security.
    
    Setup:
    - Configure production CORS origins
    
    Execution:
    - Send requests from various origins
    
    Pass Conditions:
    - Allowed origins receive Access-Control headers
    - Disallowed origins rejected
    - Credentials supported for allowed origins
    - OPTIONS preflight handled correctly
    """
```

## Frontend Unit Tests

### 9. Authentication Component Tests (`AdminLogin.test.js`)

#### Test 9.1: Successful Login Flow
```javascript
test('successful login with valid API key', async () => {
  /**
   * Setup:
   * - Mock successful API response
   * - Render AdminLogin component
   * 
   * Execution:
   * - Enter valid API key
   * - Submit form
   * 
   * Pass Conditions:
   * - API key stored in sessionStorage
   * - User redirected to dashboard
   * - Loading state shown during authentication
   * - No error messages displayed
   */
});
```

#### Test 9.2: Failed Login Handling
```javascript
test('failed login with invalid API key', async () => {
  /**
   * Setup:
   * - Mock 403 API response
   * - Render AdminLogin component
   * 
   * Execution:
   * - Enter invalid API key
   * - Submit form
   * 
   * Pass Conditions:
   * - Error message displayed
   * - No redirect occurs
   * - API key not stored
   * - Form remains accessible for retry
   */
});
```

### 10. Client Management Component Tests (`ClientList.test.js`)

#### Test 10.1: Client List Rendering
```javascript
test('renders client list with correct data', async () => {
  /**
   * Setup:
   * - Mock API response with test clients
   * - Render ClientList component
   * 
   * Execution:
   * - Wait for data load
   * 
   * Pass Conditions:
   * - All clients displayed in table
   * - Privacy levels shown with correct colors
   * - Domain counts accurate
   * - Edit/Delete buttons present
   */
});
```

#### Test 10.2: Client Deletion
```javascript
test('client deletion with confirmation', async () => {
  /**
   * Setup:
   * - Mock delete API endpoint
   * - Render ClientList with test data
   * 
   * Execution:
   * - Click delete button
   * - Confirm deletion dialog
   * 
   * Pass Conditions:
   * - Confirmation dialog appears
   * - API delete endpoint called
   * - Client removed from list
   * - Success message displayed
   */
});
```

### 11. Client Form Component Tests (`ClientForm.test.js`)

#### Test 11.1: Form Validation
```javascript
test('validates required fields before submission', async () => {
  /**
   * Setup:
   * - Render ClientForm component
   * 
   * Execution:
   * - Submit form with missing fields
   * 
   * Pass Conditions:
   * - Validation errors displayed
   * - Form submission prevented
   * - Specific field errors highlighted
   * - No API call made
   */
});
```

#### Test 11.2: Domain Addition Interface
```javascript
test('adds domain to client with validation', async () => {
  /**
   * Setup:
   * - Mock domain addition API
   * - Render ClientForm for existing client
   * 
   * Execution:
   * - Enter valid domain
   * - Click add domain button
   * 
   * Pass Conditions:
   * - Domain added to list immediately
   * - API call successful
   * - Domain input cleared
   * - No duplicate domains allowed
   */
});
```

### 12. Dashboard Component Tests (`Dashboard.test.js`)

#### Test 12.1: Statistics Display
```javascript
test('displays accurate system statistics', async () => {
  /**
   * Setup:
   * - Mock API with statistics data
   * - Render Dashboard component
   * 
   * Execution:
   * - Wait for data load
   * 
   * Pass Conditions:
   * - Total clients count correct
   * - Active clients count correct
   * - Privacy level breakdown accurate
   * - Loading state shown initially
   */
});
```

## Integration Tests

### 13. End-to-End Flow Tests (`test_e2e_flows.py`)

#### Test 13.1: Complete Client Setup Flow
```python
def test_complete_client_setup_flow():
    """
    Test full client creation and configuration flow.
    
    Execution:
    1. Create client via API
    2. Add multiple domains
    3. Set primary domain
    4. Verify pixel generation
    5. Test domain authorization
    
    Pass Conditions:
    - All operations succeed sequentially
    - Final state consistent across all systems
    - Pixel serves correct configuration
    - Domain authorization returns correct client
    """
```

### 14. Performance Tests (`test_performance.py`)

#### Test 14.1: Domain Authorization Performance
```python
def test_domain_authorization_performance():
    """
    Test O(1) lookup performance at scale.
    
    Setup:
    - Create 10,000 domains across 1,000 clients
    
    Execution:
    - Perform 1,000 random domain lookups
    
    Pass Conditions:
    - Average response time < 100ms
    - 95th percentile < 200ms
    - No degradation with scale
    - Memory usage stable
    """
```

#### Test 14.2: Concurrent Request Handling
```python
def test_concurrent_request_handling():
    """
    Test system under concurrent load.
    
    Setup:
    - Prepare 100 concurrent clients
    
    Execution:
    - Send 100 simultaneous requests
    
    Pass Conditions:
    - All requests complete successfully
    - No race conditions
    - Response times remain acceptable
    - No memory leaks
    """
```

## Test Coverage Requirements

### Minimum Coverage Targets
- **Overall Coverage**: >= 85%
- **Critical Paths**: >= 95%
- **Authentication**: 100%
- **Domain Authorization**: >= 90%
- **Error Handling**: >= 80%

### Critical Path Definition
- Authentication flow
- Domain authorization lookup
- Client creation and configuration
- Pixel generation
- Privacy compliance enforcement

## Continuous Integration Configuration

### GitHub Actions Workflow
```yaml
name: Pixel Management Tests
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests with coverage
        run: |
          pytest --cov=app --cov-report=xml --cov-report=term
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run tests with coverage
        run: cd frontend && npm run test:coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Mock Data Factories

### Client Factory
```python
class ClientFactory:
    """
    Generate test client data with realistic variations.
    
    Attributes:
    - name: Company names with variety
    - owner: Different owner patterns
    - privacy_level: All three levels
    - deployment_type: Both types
    - features: Realistic feature combinations
    """
```

### Domain Factory
```python
class DomainFactory:
    """
    Generate valid test domains.
    
    Patterns:
    - Simple domains (example.com)
    - Subdomains (app.example.com)
    - Multiple subdomains (api.v2.example.com)
    - Various TLDs (.com, .org, .io, .app)
    """
```

## Test Data Management

### Setup and Teardown
- Use pytest fixtures for database setup
- Isolate tests with transaction rollback
- Clear Firestore emulator between tests
- Reset mock data after each test

### Test Database Configuration
```python
@pytest.fixture
def test_db():
    """
    Provide isolated test database.
    
    - Use Firestore emulator for tests
    - Clear all collections before each test
    - Provide helper methods for data creation
    - Automatic cleanup after test completion
    """
```

## Failure Scenarios to Test

### Network Failures
- Firestore connection timeout
- Intermittent network errors
- Partial request completion

### Data Corruption
- Malformed JSON payloads
- Invalid UTF-8 sequences
- Oversized payloads

### Security Attempts
- SQL injection in parameters
- XSS in client names
- Path traversal in domains
- Token replay attacks

## Production Readiness Criteria

All tests must pass with:
1. No flaky tests (run 10 times successfully)
2. Coverage targets met
3. Performance benchmarks achieved
4. Security tests comprehensive
5. Error handling verified
6. Concurrent operation safety proven
7. Memory leak tests passed
8. Load tests completed

## Test Execution Commands

```bash
# Run all backend tests
pytest backend/tests -v --cov=app --cov-report=html

# Run specific test category
pytest backend/tests/test_auth.py -v

# Run with performance profiling
pytest backend/tests --profile

# Run frontend tests
cd frontend && npm test

# Run frontend with coverage
cd frontend && npm run test:coverage

# Run integration tests only
pytest backend/tests -m integration

# Run security tests only
pytest backend/tests -m security
```