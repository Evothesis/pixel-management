# Pixel Management Test Suite

## Overview

Comprehensive test suite for the Pixel Management system with **68 total tests** covering backend and frontend components. This test suite ensures reliability, security, and performance across all system components.

### Test Coverage
- **Backend Tests**: 42 tests (Unit, Integration, Performance, Security)
- **Frontend Tests**: 26 tests (Components, Integration, Workflows)
- **Overall Coverage Target**: ≥85%
- **Critical Path Coverage**: ≥95%
- **Authentication Coverage**: 100%

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- All dependencies installed (see Setup section)

### Run All Tests
```bash
# From the tests directory
./scripts/run-all-tests.sh

# Or run backend and frontend separately
./scripts/run-backend-tests.sh
./scripts/run-frontend-tests.sh
```

### Run Tests with Coverage
```bash
./scripts/run-tests-with-coverage.sh
```

## Test Structure

```
tests/
├── README.md                           # This file
├── conftest.py                         # Global test configuration
├── pytest.ini                         # Pytest configuration (in project root)
├── docs/                              # Detailed documentation
│   ├── COMMANDS_REFERENCE.md          # Complete command reference
│   ├── TESTING_WORKFLOW.md            # Developer workflow guide
│   └── TROUBLESHOOTING.md             # Common issues and solutions
├── scripts/                           # Test execution scripts
│   ├── setup-test-env.sh              # Environment setup
│   ├── run-backend-tests.sh           # Backend test execution
│   ├── run-frontend-tests.sh          # Frontend test execution
│   ├── run-all-tests.sh               # Complete test suite
│   └── run-tests-with-coverage.sh     # Coverage reporting
├── backend/                           # Backend tests (42 tests)
│   ├── conftest.py                    # Backend-specific fixtures
│   ├── unit/                          # Unit tests (28 tests)
│   │   ├── test_auth.py               # Authentication (4 tests)
│   │   ├── test_client_management.py  # Client operations (4 tests)
│   │   ├── test_domain_management.py  # Domain management (4 tests)
│   │   ├── test_domain_authorization.py # Domain auth (4 tests)
│   │   ├── test_pixel_generation.py   # Pixel serving (4 tests)
│   │   ├── test_firestore_client.py   # Database client (4 tests)
│   │   ├── test_firestore_operations.py # DB operations (2 tests)
│   │   ├── test_schemas.py            # Data validation (4 tests)
│   │   ├── test_utils.py              # Utility functions (2 tests)
│   │   ├── test_rate_limiter.py       # Rate limiting (4 tests)
│   │   ├── test_main.py               # FastAPI app (4 tests)
│   │   ├── test_concurrent_requests.py # Concurrency (4 tests)
│   │   └── test_domain_lookup_perf.py # Performance (4 tests)
│   ├── integration/                   # Integration tests (8 tests)
│   │   ├── test_client_workflows.py   # Client workflows (5 tests)
│   │   └── test_domain_workflows.py   # Domain workflows (4 tests)
│   └── security/                      # Security tests (2 tests)
│       ├── test_auth_security.py      # Auth security (1 test)
│       └── test_injection_attacks.py  # Injection protection (1 test)
└── frontend/                          # Frontend tests (26 tests)
    ├── components/                    # Component tests (20 tests)
    │   ├── AdminLogin.test.js         # Login component (4 tests)
    │   ├── ClientForm.test.js         # Client form (6 tests)
    │   ├── ClientList.test.js         # Client list (6 tests)
    │   └── Dashboard.test.js          # Dashboard (4 tests)
    └── integration/                   # Frontend integration (6 tests)
        ├── auth-flow.test.js          # Authentication flow (2 tests)
        ├── client-management.test.js  # Client CRUD flow (2 tests)
        └── api-integration.test.js    # API integration (2 tests)
```

## Setup Instructions

### 1. Environment Setup
```bash
# Run the setup script
./scripts/setup-test-env.sh

# Or manually install dependencies
cd ../backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### 2. Environment Variables
The test suite automatically sets required environment variables:
- `TESTING=true`
- `ADMIN_API_KEY=test_admin_key_12345`
- `GOOGLE_CLOUD_PROJECT=test-project`
- `FIRESTORE_EMULATOR_HOST=localhost:8080`

## Common Test Commands

### Backend Tests
```bash
# All backend tests
pytest backend/

# By category
pytest backend/unit/ -m unit
pytest backend/integration/ -m integration
pytest backend/security/ -m security

# Specific test file
pytest backend/unit/test_auth.py -v

# Specific test class or function
pytest backend/unit/test_auth.py::TestAuthentication::test_valid_api_key -v

# With coverage
pytest backend/ --cov=../backend/app --cov-report=term-missing
```

### Frontend Tests
```bash
# All frontend tests (from project root)
cd frontend && npm test -- --coverage --watchAll=false

# Specific component
cd frontend && npm test -- --testNamePattern="ClientForm"

# Specific test file
cd frontend && npm test -- --testPathPattern="components/ClientForm.test.js"

# Integration tests only
cd frontend && npm test -- --testPathPattern="integration/"
```

### Performance Tests
```bash
# Backend performance tests
pytest backend/unit/test_domain_lookup_perf.py -v
pytest backend/unit/test_concurrent_requests.py -v

# With performance markers
pytest backend/ -m performance -v
```

### Security Tests
```bash
# All security tests
pytest backend/security/ -v

# Specific security tests
pytest backend/security/test_auth_security.py -v
pytest backend/security/test_injection_attacks.py -v
```

## Test Markers

Use pytest markers to run specific test categories:

- `unit` - Unit tests
- `integration` - Integration tests  
- `performance` - Performance tests
- `security` - Security tests
- `auth` - Authentication tests
- `critical` - Critical path tests (95% coverage required)
- `slow` - Tests that take >1 second

### Examples
```bash
pytest backend/ -m "unit and auth"
pytest backend/ -m "performance or security"
pytest backend/ -m "critical" --cov-fail-under=95
```

## Coverage Requirements

### Backend Coverage Targets
- **Overall**: ≥85%
- **Critical Paths**: ≥95%
- **Authentication Module**: 100%
- **Domain Authorization**: ≥90%

### Frontend Coverage Targets
- **Components**: ≥90%
- **Integration Workflows**: ≥85%
- **User Interactions**: ≥90%

### Generate Coverage Reports
```bash
# HTML coverage report
./scripts/run-tests-with-coverage.sh

# View coverage reports
open coverage/backend/index.html
open coverage/frontend/index.html
```

## Performance Benchmarks

The test suite validates these performance requirements:

- **Domain Authorization**: <100ms average, <200ms 95th percentile
- **Pixel Generation**: <150ms average response time
- **API Endpoints**: <500ms average response time
- **Concurrent Requests**: Handle 100+ simultaneous requests

## Troubleshooting

For common issues and solutions, see:
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Testing Workflow](docs/TESTING_WORKFLOW.md)
- [Complete Command Reference](docs/COMMANDS_REFERENCE.md)

## Next Steps

1. **Run Setup**: `./scripts/setup-test-env.sh`
2. **Run All Tests**: `./scripts/run-all-tests.sh`
3. **Check Coverage**: `./scripts/run-tests-with-coverage.sh`
4. **Review Results**: Check coverage reports and test output

For detailed documentation, see the `docs/` directory.