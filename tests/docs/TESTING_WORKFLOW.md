# Developer Testing Workflow

## Overview

This guide provides a comprehensive workflow for developers working with the Pixel Management test suite. It covers daily development practices, testing strategies, and best practices for maintaining high code quality.

## Table of Contents

1. [Quick Start Workflow](#quick-start-workflow)
2. [Development Testing Patterns](#development-testing-patterns)
3. [Test-Driven Development (TDD)](#test-driven-development-tdd)
4. [Code Coverage Guidelines](#code-coverage-guidelines)
5. [Performance Testing Workflow](#performance-testing-workflow)
6. [Security Testing Workflow](#security-testing-workflow)
7. [Integration Testing Strategy](#integration-testing-strategy)
8. [Debugging Failed Tests](#debugging-failed-tests)
9. [Pre-Commit Testing](#pre-commit-testing)
10. [Continuous Integration Workflow](#continuous-integration-workflow)

---

## Quick Start Workflow

### New Developer Setup
```bash
# 1. Clone repository and setup environment
git clone <repository>
cd pixel-management

# 2. Setup test environment
cd tests
./scripts/setup-test-env.sh

# 3. Verify everything works
./scripts/run-all-tests.sh

# 4. Run with coverage to see baseline
./scripts/run-tests-with-coverage.sh -o
```

### Daily Development Workflow
```bash
# 1. Pull latest changes and run tests
git pull origin main
cd tests && ./scripts/run-all-tests.sh

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Develop with test-first approach
# - Write failing test
# - Implement feature
# - Make test pass
# - Refactor

# 4. Run relevant tests frequently
./scripts/run-backend-tests.sh -t backend/unit/test_your_module.py
./scripts/run-frontend-tests.sh -t YourComponent

# 5. Before committing
./scripts/run-all-tests.sh -c
```

---

## Development Testing Patterns

### Backend Development Pattern

#### 1. Unit Test First
```bash
# Create new test file for your module
touch backend/unit/test_your_feature.py

# Write failing test
pytest backend/unit/test_your_feature.py -v

# Implement feature to make test pass
pytest backend/unit/test_your_feature.py -v

# Run related tests
pytest backend/unit/ -k "your_feature" -v
```

#### 2. Integration Testing
```bash
# After unit tests pass, add integration tests
pytest backend/integration/test_your_workflow.py -v

# Test with real-like scenarios
pytest backend/integration/ -v
```

#### 3. Performance Validation
```bash
# Run performance tests for your changes
pytest backend/ -m performance -v

# Check specific performance requirements
pytest backend/unit/test_domain_lookup_perf.py -v
```

### Frontend Development Pattern

#### 1. Component Testing
```bash
# Test component in isolation
cd frontend && npm test -- --testNamePattern="YourComponent"

# Test with user interactions
cd frontend && npm test -- --testPathPattern="components/YourComponent.test.js" -v

# Watch mode for development
cd frontend && npm test -- --testNamePattern="YourComponent" --watch
```

#### 2. Integration Testing
```bash
# Test component integration
cd frontend && npm test -- --testPathPattern="integration/"

# Test API integration
cd frontend && npm test -- --testNamePattern="api integration"
```

#### 3. End-to-End Workflow Testing
```bash
# Test complete user workflows
cd frontend && npm test -- --testPathPattern="integration/auth-flow.test.js"
cd frontend && npm test -- --testPathPattern="integration/client-management.test.js"
```

---

## Test-Driven Development (TDD)

### TDD Cycle for Backend Features

#### 1. Red Phase (Write Failing Test)
```python
# backend/unit/test_new_feature.py
def test_new_feature_should_do_something():
    # Arrange
    client_data = {"name": "Test Client"}
    
    # Act
    result = new_feature_function(client_data)
    
    # Assert
    assert result["status"] == "success"
    assert "client_id" in result
```

```bash
# Run failing test
pytest backend/unit/test_new_feature.py::test_new_feature_should_do_something -v
```

#### 2. Green Phase (Make Test Pass)
```python
# backend/app/new_feature.py
def new_feature_function(client_data):
    return {
        "status": "success",
        "client_id": f"client_{uuid.uuid4().hex[:8]}"
    }
```

```bash
# Verify test passes
pytest backend/unit/test_new_feature.py::test_new_feature_should_do_something -v
```

#### 3. Refactor Phase (Improve Code)
```bash
# Run all related tests to ensure refactoring doesn't break anything
pytest backend/unit/ -k "new_feature" -v

# Run with coverage to ensure good test coverage
pytest backend/unit/test_new_feature.py --cov=../backend/app/new_feature --cov-report=term-missing
```

### TDD Cycle for Frontend Components

#### 1. Red Phase (Write Failing Test)
```javascript
// frontend/src/components/NewComponent.test.js
import { render, screen } from '@testing-library/react';
import NewComponent from './NewComponent';

test('should render component with title', () => {
    render(<NewComponent title="Test Title" />);
    expect(screen.getByText('Test Title')).toBeInTheDocument();
});
```

```bash
# Run failing test
cd frontend && npm test -- --testNamePattern="should render component with title"
```

#### 2. Green Phase (Make Test Pass)
```jsx
// frontend/src/components/NewComponent.js
const NewComponent = ({ title }) => {
    return <h1>{title}</h1>;
};

export default NewComponent;
```

#### 3. Refactor Phase (Improve Component)
```bash
# Run all component tests
cd frontend && npm test -- --testNamePattern="NewComponent"
```

---

## Code Coverage Guidelines

### Backend Coverage Requirements
- **Overall**: ≥85%
- **Critical Paths**: ≥95%
- **Authentication**: 100%
- **Domain Authorization**: ≥90%
- **New Features**: ≥90%

### Frontend Coverage Requirements
- **Components**: ≥90%
- **Integration Workflows**: ≥85%
- **User Interactions**: ≥90%
- **New Components**: ≥85%

### Measuring Coverage

#### Backend Coverage
```bash
# Check current coverage
pytest backend/ --cov=../backend/app --cov-report=term-missing

# Coverage for specific module
pytest backend/unit/test_auth.py --cov=../backend/app/auth --cov-report=term-missing

# Generate HTML report
pytest backend/ --cov=../backend/app --cov-report=html:../coverage/backend

# Check coverage thresholds
pytest backend/ --cov=../backend/app --cov-fail-under=85
```

#### Frontend Coverage
```bash
# Check current coverage
cd frontend && npm run test:coverage

# Coverage with threshold
cd frontend && npm test -- --coverage --coverageThreshold='{"global":{"lines":85}}'

# Generate HTML report
cd frontend && npm test -- --coverage --coverageReporters=html
```

### Improving Coverage

#### Finding Uncovered Code
```bash
# Backend: View detailed coverage report
open ../coverage/backend/index.html

# Frontend: View detailed coverage report
open ../coverage/frontend/index.html

# Backend: Terminal report with missing lines
pytest backend/ --cov=../backend/app --cov-report=term-missing
```

#### Adding Tests for Uncovered Code
```bash
# Identify uncovered lines and add tests
pytest backend/unit/test_module.py --cov=../backend/app/module --cov-report=term-missing

# Focus on critical paths first
pytest backend/ -m critical --cov=../backend/app --cov-report=term-missing
```

---

## Performance Testing Workflow

### Backend Performance Testing

#### 1. Domain Authorization Performance
```bash
# Test domain lookup performance
pytest backend/unit/test_domain_lookup_perf.py -v -s

# Requirements: <100ms average, <200ms 95th percentile
pytest backend/unit/test_domain_lookup_perf.py::test_domain_lookup_performance -v
```

#### 2. Concurrent Request Testing
```bash
# Test concurrent request handling
pytest backend/unit/test_concurrent_requests.py -v -s

# Requirements: Handle 100+ simultaneous requests
pytest backend/unit/test_concurrent_requests.py::test_concurrent_client_creation -v
```

#### 3. Performance Monitoring
```bash
# Run all performance tests
pytest backend/ -m performance -v --durations=10

# Monitor execution times
pytest backend/ --durations=10
```

### Performance Benchmarking

#### Setting Performance Baselines
```bash
# Run performance tests multiple times to establish baseline
for i in {1..5}; do
    echo "Run $i:"
    pytest backend/unit/test_domain_lookup_perf.py -v
done
```

#### Performance Regression Testing
```bash
# Before making changes
pytest backend/ -m performance -v > performance_before.log

# After making changes
pytest backend/ -m performance -v > performance_after.log

# Compare results
diff performance_before.log performance_after.log
```

---

## Security Testing Workflow

### Security Test Categories

#### 1. Authentication Security
```bash
# Test authentication mechanisms
pytest backend/security/test_auth_security.py -v

# Test API key security
pytest backend/unit/test_auth.py -m auth -v
```

#### 2. Injection Attack Prevention
```bash
# Test injection attack protection
pytest backend/security/test_injection_attacks.py -v

# Test SQL injection prevention
pytest backend/security/test_injection_attacks.py::test_sql_injection_protection -v
```

#### 3. Input Validation
```bash
# Test input validation
pytest backend/unit/test_schemas.py -v

# Test boundary conditions
pytest backend/unit/ -k "validation" -v
```

### Security Testing Best Practices

#### 1. Regular Security Testing
```bash
# Run security tests daily
pytest backend/ -m security -v

# Include in pre-commit checks
pytest backend/security/ -v
```

#### 2. Security Regression Testing
```bash
# After security fixes
pytest backend/security/ -v

# Verify fix doesn't break other functionality
pytest backend/ -v
```

---

## Integration Testing Strategy

### Backend Integration Testing

#### 1. Client Workflow Testing
```bash
# Test complete client management workflows
pytest backend/integration/test_client_workflows.py -v

# Test specific workflow
pytest backend/integration/test_client_workflows.py::test_complete_client_setup_flow -v
```

#### 2. Domain Workflow Testing
```bash
# Test domain management workflows
pytest backend/integration/test_domain_workflows.py -v
```

### Frontend Integration Testing

#### 1. Authentication Flow Testing
```bash
# Test complete authentication workflow
cd frontend && npm test -- --testPathPattern="integration/auth-flow.test.js"
```

#### 2. Client Management Flow Testing
```bash
# Test complete client CRUD workflow
cd frontend && npm test -- --testPathPattern="integration/client-management.test.js"
```

#### 3. API Integration Testing
```bash
# Test API service integration
cd frontend && npm test -- --testPathPattern="integration/api-integration.test.js"
```

---

## Debugging Failed Tests

### Backend Test Debugging

#### 1. Verbose Output
```bash
# Run with maximum verbosity
pytest backend/unit/test_failing.py -vv -s

# Show detailed traceback
pytest backend/unit/test_failing.py --tb=long

# Show only short traceback
pytest backend/unit/test_failing.py --tb=short
```

#### 2. Interactive Debugging
```bash
# Drop into debugger on failure
pytest backend/unit/test_failing.py --pdb

# Drop into debugger on first failure
pytest backend/unit/test_failing.py --pdb -x
```

#### 3. Test Isolation
```bash
# Run single test
pytest backend/unit/test_module.py::TestClass::test_method -v

# Run tests in isolation
pytest backend/unit/test_module.py --forked
```

### Frontend Test Debugging

#### 1. Debug Mode
```bash
# Run tests in debug mode
cd frontend && npm test -- --runInBand --watchAll=false

# Increase memory for debugging
cd frontend && node --max_old_space_size=4096 npm test
```

#### 2. Console Debugging
```bash
# Enable console output
cd frontend && npm test -- --verbose --watchAll=false

# Run with debug environment
cd frontend && DEBUG=* npm test -- --watchAll=false
```

### Common Debugging Scenarios

#### 1. Import Errors
```bash
# Check Python path
cd tests && python -c "import sys; print(sys.path)"

# Test imports manually
cd tests && python -c "from app.main import app; print('Import successful')"
```

#### 2. Environment Issues
```bash
# Check environment variables
cd tests && python -c "import os; print(os.environ.get('TESTING'))"

# Verify test configuration
pytest --collect-only backend/
```

#### 3. Test Data Issues
```bash
# Run with test data debugging
pytest backend/ -v --setup-show

# Clear test data
rm -rf test_data/
```

---

## Pre-Commit Testing

### Automated Pre-Commit Checks

#### 1. Quick Test Suite
```bash
# Fast tests only (under 10 seconds)
pytest backend/ -m "not slow" -x
cd frontend && npm test -- --watchAll=false --testTimeout=5000
```

#### 2. Critical Path Testing
```bash
# Test critical functionality
pytest backend/ -m critical -x
```

#### 3. Modified Files Only
```bash
# Test only changed files (requires git)
CHANGED_BACKEND=$(git diff --name-only HEAD^ | grep "backend/" | sed 's/backend\///g')
if [ ! -z "$CHANGED_BACKEND" ]; then
    pytest backend/ -k "$CHANGED_BACKEND" -x
fi
```

### Pre-Commit Script Example
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running pre-commit tests..."

# Quick backend tests
pytest backend/ -m "not slow" -x --tb=short
if [ $? -ne 0 ]; then
    echo "Backend tests failed"
    exit 1
fi

# Quick frontend tests
cd frontend && npm test -- --watchAll=false --passWithNoTests
if [ $? -ne 0 ]; then
    echo "Frontend tests failed"
    exit 1
fi

echo "Pre-commit tests passed"
```

---

## Continuous Integration Workflow

### Local CI Simulation
```bash
# Simulate CI environment
TESTING=true CI=true ./scripts/run-all-tests.sh

# Test with coverage requirements
./scripts/run-tests-with-coverage.sh -t 85
```

### Branch Testing Strategy
```bash
# Feature branch testing
git checkout feature/new-feature
./scripts/run-all-tests.sh -x

# Integration testing before merge
git checkout main
git pull origin main
git checkout feature/new-feature
git rebase main
./scripts/run-all-tests.sh
```

### Release Testing
```bash
# Full test suite with strict requirements
./scripts/run-tests-with-coverage.sh -t 90 -c 95

# Performance validation
pytest backend/ -m performance --benchmark-min-rounds=3

# Security validation
pytest backend/ -m security -v
```

---

## Best Practices Summary

### Daily Development
1. ✅ Run tests before starting work
2. ✅ Write tests first (TDD approach)
3. ✅ Run relevant tests frequently during development
4. ✅ Maintain high coverage on new code
5. ✅ Run full test suite before committing

### Code Quality
1. ✅ Aim for ≥90% coverage on new features
2. ✅ Write clear, descriptive test names
3. ✅ Test edge cases and error conditions
4. ✅ Keep tests independent and isolated
5. ✅ Maintain test performance

### Team Collaboration
1. ✅ Document test scenarios for complex features
2. ✅ Share testing patterns and utilities
3. ✅ Review test code in pull requests
4. ✅ Maintain shared test data and fixtures
5. ✅ Keep test documentation updated

### Performance & Security
1. ✅ Include performance tests for critical paths
2. ✅ Test security boundaries and authentication
3. ✅ Validate input handling and edge cases
4. ✅ Monitor test execution times
5. ✅ Regular security test reviews

---

## Quick Reference Commands

```bash
# Setup
./scripts/setup-test-env.sh

# Daily development
./scripts/run-backend-tests.sh -t test_file.py -v
./scripts/run-frontend-tests.sh -t ComponentName -w

# Pre-commit
./scripts/run-all-tests.sh -x

# Coverage analysis
./scripts/run-tests-with-coverage.sh -o

# Performance testing
pytest backend/ -m performance -v

# Security testing
pytest backend/ -m security -v

# Debug failing test
pytest backend/unit/test_file.py::test_function -vv --pdb
```

For more detailed information, see:
- [Commands Reference](COMMANDS_REFERENCE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Main README](../README.md)