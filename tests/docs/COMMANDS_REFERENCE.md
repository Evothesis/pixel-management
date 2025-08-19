# Complete Test Commands Reference

## Overview

This document provides a comprehensive reference for all test execution commands in the Pixel Management system. Use this guide for both individual test execution and full suite runs.

## Table of Contents

1. [Backend Test Commands](#backend-test-commands)
2. [Frontend Test Commands](#frontend-test-commands)
3. [Combined Test Commands](#combined-test-commands)
4. [Coverage Commands](#coverage-commands)
5. [Performance Test Commands](#performance-test-commands)
6. [Security Test Commands](#security-test-commands)
7. [Debugging Commands](#debugging-commands)
8. [CI/CD Commands](#cicd-commands)

---

## Backend Test Commands

### Basic Test Execution

```bash
# Run all backend tests
pytest backend/

# Run all backend tests with verbose output
pytest backend/ -v

# Run all backend tests with extra verbose output
pytest backend/ -vv

# Run tests and stop on first failure
pytest backend/ -x

# Run tests with detailed failure information
pytest backend/ --tb=long
```

### Test Discovery and File Execution

```bash
# Run specific test file
pytest backend/unit/test_auth.py

# Run specific test file with verbose output
pytest backend/unit/test_auth.py -v

# Run multiple specific files
pytest backend/unit/test_auth.py backend/unit/test_client_management.py

# Run all tests in a directory
pytest backend/unit/
pytest backend/integration/
pytest backend/security/
```

### Test Class and Function Execution

```bash
# Run specific test class
pytest backend/unit/test_auth.py::TestAuthentication

# Run specific test function
pytest backend/unit/test_auth.py::TestAuthentication::test_valid_api_key

# Run specific test function with verbose output
pytest backend/unit/test_auth.py::TestAuthentication::test_valid_api_key -v -s

# Run multiple test functions
pytest backend/unit/test_auth.py::TestAuthentication::test_valid_api_key backend/unit/test_auth.py::TestAuthentication::test_invalid_api_key
```

### Test Categories with Markers

```bash
# Run only unit tests
pytest backend/ -m unit

# Run only integration tests
pytest backend/ -m integration

# Run only performance tests
pytest backend/ -m performance

# Run only security tests
pytest backend/ -m security

# Run only authentication tests
pytest backend/ -m auth

# Run only critical path tests
pytest backend/ -m critical

# Run only slow tests
pytest backend/ -m slow
```

### Combined Marker Expressions

```bash
# Run unit AND auth tests
pytest backend/ -m "unit and auth"

# Run performance OR security tests
pytest backend/ -m "performance or security"

# Run unit tests but NOT slow tests
pytest backend/ -m "unit and not slow"

# Run critical tests with high coverage requirement
pytest backend/ -m critical --cov-fail-under=95

# Run all tests except slow ones
pytest backend/ -m "not slow"
```

### Specific Test Categories

```bash
# Authentication tests
pytest backend/unit/test_auth.py -v
pytest backend/security/test_auth_security.py -v

# Client management tests
pytest backend/unit/test_client_management.py -v
pytest backend/integration/test_client_workflows.py -v

# Domain management tests
pytest backend/unit/test_domain_management.py -v
pytest backend/unit/test_domain_authorization.py -v
pytest backend/integration/test_domain_workflows.py -v

# Database tests
pytest backend/unit/test_firestore_client.py -v
pytest backend/unit/test_firestore_operations.py -v

# API and application tests
pytest backend/unit/test_main.py -v
pytest backend/unit/test_schemas.py -v
pytest backend/unit/test_utils.py -v
```

---

## Frontend Test Commands

### Basic Test Execution

```bash
# Run all frontend tests (from project root)
cd frontend && npm test -- --coverage --watchAll=false

# Run all frontend tests with verbose output
cd frontend && npm test -- --verbose --watchAll=false

# Run tests in watch mode (for development)
cd frontend && npm test

# Run tests with coverage
cd frontend && npm run test:coverage
```

### Component Test Execution

```bash
# Run specific component tests
cd frontend && npm test -- --testNamePattern="AdminLogin"
cd frontend && npm test -- --testNamePattern="ClientForm"
cd frontend && npm test -- --testNamePattern="ClientList"
cd frontend && npm test -- --testNamePattern="Dashboard"

# Run specific test file
cd frontend && npm test -- --testPathPattern="components/AdminLogin.test.js"
cd frontend && npm test -- --testPathPattern="components/ClientForm.test.js"
cd frontend && npm test -- --testPathPattern="components/ClientList.test.js"
cd frontend && npm test -- --testPathPattern="components/Dashboard.test.js"
```

### Integration Test Execution

```bash
# Run all integration tests
cd frontend && npm test -- --testPathPattern="integration/"

# Run specific integration tests
cd frontend && npm test -- --testPathPattern="integration/auth-flow.test.js"
cd frontend && npm test -- --testPathPattern="integration/client-management.test.js"
cd frontend && npm test -- --testPathPattern="integration/api-integration.test.js"
```

### Frontend Test Categories

```bash
# Run all component tests
cd frontend && npm test -- --testPathPattern="components/"

# Run all integration tests
cd frontend && npm test -- --testPathPattern="integration/"

# Run tests with specific patterns
cd frontend && npm test -- --testNamePattern="should render"
cd frontend && npm test -- --testNamePattern="should handle"
cd frontend && npm test -- --testNamePattern="should validate"
```

### Frontend Debug and Development

```bash
# Run tests with detailed output
cd frontend && npm test -- --verbose --watchAll=false

# Run tests in debug mode
cd frontend && npm test -- --runInBand --watchAll=false

# Update snapshots
cd frontend && npm test -- --updateSnapshot --watchAll=false

# Run tests with custom reporter
cd frontend && npm test -- --reporters=default --reporters=jest-junit --watchAll=false
```

---

## Combined Test Commands

### Using Helper Scripts

```bash
# Run all tests (backend + frontend)
./scripts/run-all-tests.sh

# Run backend tests only
./scripts/run-backend-tests.sh

# Run frontend tests only
./scripts/run-frontend-tests.sh

# Run tests with full coverage reporting
./scripts/run-tests-with-coverage.sh

# Set up test environment
./scripts/setup-test-env.sh
```

### Manual Combined Execution

```bash
# Run backend tests then frontend tests
pytest backend/ && cd frontend && npm test -- --coverage --watchAll=false

# Run with error handling
pytest backend/ -x && cd frontend && npm test -- --coverage --watchAll=false --passWithNoTests
```

---

## Coverage Commands

### Backend Coverage

```bash
# Basic coverage
pytest backend/ --cov=../backend/app

# Coverage with missing lines
pytest backend/ --cov=../backend/app --cov-report=term-missing

# Coverage with HTML report
pytest backend/ --cov=../backend/app --cov-report=html:coverage/backend

# Coverage with XML report (for CI/CD)
pytest backend/ --cov=../backend/app --cov-report=xml:coverage/backend/coverage.xml

# Coverage with multiple formats
pytest backend/ --cov=../backend/app --cov-report=term-missing --cov-report=html:coverage/backend --cov-report=xml:coverage/backend/coverage.xml

# Coverage with failure threshold
pytest backend/ --cov=../backend/app --cov-fail-under=85

# Coverage for specific modules
pytest backend/unit/test_auth.py --cov=../backend/app/auth --cov-report=term-missing
```

### Frontend Coverage

```bash
# Basic coverage
cd frontend && npm run test:coverage

# Coverage with detailed output
cd frontend && npm test -- --coverage --coverageReporters=text-lcov --watchAll=false

# Coverage with HTML report
cd frontend && npm test -- --coverage --coverageReporters=html --watchAll=false

# Coverage with specific thresholds
cd frontend && npm test -- --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}' --watchAll=false
```

### Combined Coverage

```bash
# Generate both backend and frontend coverage
./scripts/run-tests-with-coverage.sh

# View coverage reports
open coverage/backend/index.html
open coverage/frontend/index.html
```

---

## Performance Test Commands

### Backend Performance Tests

```bash
# All performance tests
pytest backend/ -m performance -v

# Domain lookup performance
pytest backend/unit/test_domain_lookup_perf.py -v

# Concurrent request handling
pytest backend/unit/test_concurrent_requests.py -v

# Performance tests with timing details
pytest backend/ -m performance -v -s --durations=10

# Performance tests with benchmarking
pytest backend/ -m performance --benchmark-only
```

### Performance Monitoring

```bash
# Run tests with execution time tracking
pytest backend/ --durations=10

# Run tests with memory profiling
pytest backend/ --profile

# Run performance tests with detailed output
pytest backend/unit/test_domain_lookup_perf.py -v -s
pytest backend/unit/test_concurrent_requests.py -v -s
```

---

## Security Test Commands

### Backend Security Tests

```bash
# All security tests
pytest backend/security/ -v

# Authentication security
pytest backend/security/test_auth_security.py -v

# Injection attack protection
pytest backend/security/test_injection_attacks.py -v

# Security tests with detailed output
pytest backend/security/ -v -s
```

### Security Test Categories

```bash
# Run security marker tests
pytest backend/ -m security -v

# Authentication security specifically
pytest backend/ -m "security and auth" -v

# Run security tests with coverage
pytest backend/security/ --cov=../backend/app --cov-report=term-missing
```

---

## Debugging Commands

### Backend Debugging

```bash
# Run with Python debugger
pytest backend/unit/test_auth.py::TestAuthentication::test_valid_api_key -v -s --pdb

# Run with detailed tracebacks
pytest backend/ --tb=long

# Run with extra detailed tracebacks
pytest backend/ --tb=line

# Run with capture disabled (see print statements)
pytest backend/ -s

# Run with warnings enabled
pytest backend/ -v --disable-warnings=false
```

### Frontend Debugging

```bash
# Run tests with Node.js debugging
cd frontend && node --inspect-brk node_modules/.bin/react-scripts test --runInBand --no-cache --watchAll=false

# Run tests with increased memory
cd frontend && node --max_old_space_size=4096 node_modules/.bin/react-scripts test --watchAll=false

# Run tests with debugging output
cd frontend && DEBUG=* npm test -- --watchAll=false
```

### Test Data and State Debugging

```bash
# Run tests with fixture debugging
pytest backend/ -v -s --setup-show

# Run tests with detailed assertions
pytest backend/ -vv

# Run tests and keep test database for inspection
pytest backend/ --keepdb
```

---

## CI/CD Commands

### Local CI Simulation

```bash
# Simulate CI environment
TESTING=true CI=true pytest backend/ --cov=../backend/app --cov-report=xml

# Run tests as CI would (no terminal colors, XML output)
pytest backend/ --tb=short --cov=../backend/app --cov-report=xml:coverage.xml

# Frontend CI simulation
cd frontend && CI=true npm test -- --coverage --coverageReporters=cobertura --watchAll=false
```

### Quality Gates

```bash
# Run tests with strict quality requirements
pytest backend/ -m critical --cov=../backend/app --cov-fail-under=95

# Run all tests with coverage requirements
pytest backend/ --cov=../backend/app --cov-fail-under=85

# Run with performance validation
pytest backend/ -m performance --benchmark-min-rounds=3
```

---

## Advanced Usage

### Parallel Execution

```bash
# Run backend tests in parallel
pytest backend/ -n auto

# Run specific number of parallel processes
pytest backend/ -n 4

# Distribute tests across processes
pytest backend/ --dist=loadfile
```

### Test Output Formats

```bash
# JUnit XML output
pytest backend/ --junitxml=test-results.xml

# JSON output
pytest backend/ --json-report --json-report-file=test-results.json

# Custom output format
pytest backend/ --tb=line --no-header --quiet
```

### Environment-Specific Commands

```bash
# Development environment
ENVIRONMENT=development pytest backend/

# Testing environment
ENVIRONMENT=testing pytest backend/

# With custom configuration
pytest backend/ --override-ini="addopts=-v --tb=short"
```

---

## Quick Reference

### Most Common Commands

```bash
# Quick test run
pytest backend/ -x -v

# Quick frontend test
cd frontend && npm test -- --watchAll=false

# Full test suite
./scripts/run-all-tests.sh

# Coverage check
./scripts/run-tests-with-coverage.sh

# Performance validation
pytest backend/ -m performance -v

# Security validation
pytest backend/ -m security -v
```

### Emergency Debugging

```bash
# Debug failing test
pytest backend/unit/test_auth.py::test_failing_function -vv -s --pdb

# Check test discovery
pytest backend/ --collect-only

# Validate test environment
pytest backend/ --setup-only
```

For more detailed information, see:
- [Testing Workflow](TESTING_WORKFLOW.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Main README](../README.md)