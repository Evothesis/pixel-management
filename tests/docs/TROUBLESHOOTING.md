# Testing Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when running the Pixel Management test suite. Use this resource to quickly resolve testing problems and get back to development.

## Table of Contents

1. [Setup Issues](#setup-issues)
2. [Environment Problems](#environment-problems)
3. [Backend Test Issues](#backend-test-issues)
4. [Frontend Test Issues](#frontend-test-issues)
5. [Coverage Issues](#coverage-issues)
6. [Performance Test Issues](#performance-test-issues)
7. [Import and Path Issues](#import-and-path-issues)
8. [Database and Mock Issues](#database-and-mock-issues)
9. [CI/CD Issues](#cicd-issues)
10. [Common Error Messages](#common-error-messages)

---

## Setup Issues

### Problem: setup-test-env.sh fails
```bash
Error: Python 3 is not installed
```

**Solution:**
```bash
# Install Python 3.11 or higher
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-venv

# Verify installation
python3 --version
```

### Problem: Virtual environment creation fails
```bash
Error: No module named venv
```

**Solution:**
```bash
# Install python3-venv (Ubuntu/Debian)
sudo apt install python3-venv

# Or use alternative virtual environment
pip install virtualenv
virtualenv venv
```

### Problem: Node.js/npm not found
```bash
Error: Node.js is not installed
```

**Solution:**
```bash
# Install Node.js 18+ using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Or install directly
# macOS
brew install node@18

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Problem: Permission denied on scripts
```bash
Error: Permission denied: ./scripts/setup-test-env.sh
```

**Solution:**
```bash
# Make scripts executable
chmod +x tests/scripts/*.sh

# Or run with bash explicitly
bash tests/scripts/setup-test-env.sh
```

---

## Environment Problems

### Problem: Environment variables not set
```bash
KeyError: 'ADMIN_API_KEY'
```

**Solution:**
```bash
# Check current environment
cd tests && python -c "import os; print(os.environ.get('TESTING'))"

# Set manually if needed
export TESTING=true
export ADMIN_API_KEY=test_admin_key_12345
export GOOGLE_CLOUD_PROJECT=test-project

# Or source environment file
source .env.test
```

### Problem: Wrong Python path
```bash
ModuleNotFoundError: No module named 'app'
```

**Solution:**
```bash
# Check current directory and Python path
pwd
cd tests && python -c "import sys; print(sys.path)"

# Run from correct directory
cd /path/to/pixel-management/tests
pytest backend/

# Or set PYTHONPATH explicitly
export PYTHONPATH=/path/to/pixel-management/backend:$PYTHONPATH
```

### Problem: Virtual environment not activated
```bash
Error: pytest not found
```

**Solution:**
```bash
# Activate virtual environment
cd backend && source venv/bin/activate

# Verify activation
which python
which pytest

# Install requirements if needed
pip install -r requirements.txt
```

---

## Backend Test Issues

### Problem: Firestore connection errors
```bash
Error: Firestore emulator not running
```

**Solution:**
```bash
# Check if emulator is needed
export FIRESTORE_EMULATOR_HOST=localhost:8080

# Or use mock client (default in tests)
# Tests should use mocked Firestore client automatically

# Verify mock is working
cd tests && python -c "
from app.firestore_client import firestore_client
print('Mock client:', hasattr(firestore_client, '_mock'))
"
```

### Problem: Import errors in tests
```bash
ImportError: attempted relative import with no known parent package
```

**Solution:**
```bash
# Run tests from tests directory
cd tests
pytest backend/unit/test_auth.py

# Not from backend directory
# cd backend && pytest ../tests/backend/unit/test_auth.py  # WRONG

# Check conftest.py is setting up paths correctly
cd tests && python -c "
import sys
print('Current path:', sys.path)
from app.main import app
print('Import successful')
"
```

### Problem: Test database conflicts
```bash
Error: Database already exists
```

**Solution:**
```bash
# Clean test database
rm -rf test_data/
rm -rf .pytest_cache/

# Run tests with fresh state
pytest backend/ --cache-clear

# Use test isolation
pytest backend/ --forked
```

### Problem: Async test issues
```bash
RuntimeError: This event loop is already running
```

**Solution:**
```bash
# Check pytest-asyncio configuration
cat pytest.ini | grep asyncio

# Should show: asyncio_mode = auto

# If missing, add to pytest.ini:
[tool:pytest]
asyncio_mode = auto

# Or run specific test with asyncio
pytest backend/unit/test_auth.py -v --asyncio-mode=auto
```

---

## Frontend Test Issues

### Problem: Jest configuration errors
```bash
Error: Cannot find module 'react-scripts'
```

**Solution:**
```bash
# Install frontend dependencies
cd frontend && npm install

# Verify package.json scripts
cat package.json | grep -A 5 scripts

# Run with explicit path
cd frontend && npx react-scripts test --watchAll=false
```

### Problem: React Testing Library issues
```bash
Error: Cannot find module '@testing-library/react'
```

**Solution:**
```bash
# Install testing dependencies
cd frontend && npm install @testing-library/react @testing-library/jest-dom

# Verify installation
cd frontend && npm list @testing-library/react

# Check if setupTests.js exists
ls frontend/src/setupTests.js
```

### Problem: MSW (Mock Service Worker) errors
```bash
Error: MSW server not setup
```

**Solution:**
```bash
# Check MSW configuration in test files
grep -r "setupServer" frontend/src/

# Ensure MSW is properly initialized in tests
# Should have beforeAll/afterAll hooks for server start/stop

# Install MSW if missing
cd frontend && npm install msw --save-dev
```

### Problem: Test timeout issues
```bash
Error: Test timeout of 5000ms exceeded
```

**Solution:**
```bash
# Increase timeout
cd frontend && npm test -- --testTimeout=30000 --watchAll=false

# Or configure in package.json
{
  "jest": {
    "testTimeout": 30000
  }
}

# Run specific test with timeout
cd frontend && npm test -- --testNamePattern="specific test" --testTimeout=60000
```

---

## Coverage Issues

### Problem: Coverage reports not generated
```bash
Error: No coverage report found
```

**Solution:**
```bash
# Backend: Check coverage configuration
cat pytest.ini | grep cov

# Verify coverage directory exists
mkdir -p coverage/backend coverage/frontend

# Run with explicit coverage
pytest backend/ --cov=../backend/app --cov-report=html:../coverage/backend

# Frontend: Check package.json script
cd frontend && npm run test:coverage
```

### Problem: Coverage percentage calculation issues
```bash
Warning: Coverage data appears to be corrupted
```

**Solution:**
```bash
# Clear coverage cache
rm -rf .coverage*
rm -rf coverage/

# Regenerate coverage
./scripts/run-tests-with-coverage.sh

# Backend: Clean pytest cache
rm -rf .pytest_cache/

# Frontend: Clean Jest cache
cd frontend && npm test -- --clearCache
```

### Problem: Coverage thresholds not met
```bash
Error: Coverage failed under minimum threshold
```

**Solution:**
```bash
# Check current coverage
pytest backend/ --cov=../backend/app --cov-report=term-missing

# Identify uncovered lines
open coverage/backend/index.html

# Add tests for uncovered code
# Focus on critical paths first
pytest backend/ -m critical --cov=../backend/app --cov-report=term-missing

# Adjust threshold temporarily for debugging
pytest backend/ --cov=../backend/app --cov-fail-under=75
```

---

## Performance Test Issues

### Problem: Performance tests failing
```bash
AssertionError: Domain lookup took 150ms, expected <100ms
```

**Solution:**
```bash
# Run performance tests multiple times to get average
for i in {1..3}; do
    pytest backend/unit/test_domain_lookup_perf.py -v
done

# Check system load
top -l 1 | grep "CPU usage"

# Run with less concurrency
pytest backend/unit/test_concurrent_requests.py -v --workers=2

# Skip performance tests temporarily
pytest backend/ -m "not performance" -v
```

### Problem: Inconsistent performance results
```bash
Warning: Performance results vary significantly
```

**Solution:**
```bash
# Close other applications to reduce system load
# Run tests on dedicated testing machine

# Use performance markers for isolation
pytest backend/ -m performance --forked

# Run multiple iterations
pytest backend/ -m performance --count=5

# Check for memory leaks
pytest backend/ -m performance --profile
```

---

## Import and Path Issues

### Problem: Module not found errors
```bash
ModuleNotFoundError: No module named 'app.main'
```

**Solution:**
```bash
# Check current directory
pwd  # Should be in /path/to/pixel-management/tests

# Check Python path setup in conftest.py
grep -n "sys.path" tests/conftest.py

# Verify backend directory structure
ls -la backend/app/

# Test import manually
cd tests && python -c "
import sys
sys.path.insert(0, '../backend')
from app.main import app
print('Import successful')
"
```

### Problem: Relative import errors
```bash
ImportError: attempted relative import with no known parent package
```

**Solution:**
```bash
# Don't use relative imports in test files
# Instead of: from ..app.main import app
# Use: from app.main import app

# Run tests from tests directory, not subdirectories
cd tests
pytest backend/unit/test_auth.py  # CORRECT

# Not from subdirectory
# cd tests/backend && pytest unit/test_auth.py  # WRONG
```

---

## Database and Mock Issues

### Problem: Mock not working
```bash
Error: Real API calls being made instead of mock
```

**Solution:**
```bash
# Check mock setup in conftest.py
grep -A 10 "mock_firestore_client" tests/backend/conftest.py

# Verify mock is being used
cd tests && python -c "
import pytest
from unittest.mock import Mock
# Check if fixture is properly configured
"

# Ensure tests use fixtures
# Test function should have mock_firestore_client parameter
```

### Problem: Test data persistence
```bash
Error: Test data from previous run affecting current test
```

**Solution:**
```bash
# Clear test data
rm -rf test_data/
rm -rf .pytest_cache/

# Use test isolation
pytest backend/ --forked

# Check conftest.py teardown
grep -A 5 "teardown" tests/conftest.py

# Ensure proper cleanup in fixtures
# Use yield instead of return in fixtures
```

---

## CI/CD Issues

### Problem: Tests pass locally but fail in CI
```bash
Error: Tests failing in CI environment
```

**Solution:**
```bash
# Simulate CI environment locally
CI=true TESTING=true ./scripts/run-all-tests.sh

# Check environment differences
env | grep -E "(NODE_ENV|TESTING|CI)"

# Use exact CI commands locally
TESTING=true pytest backend/ --tb=short --cov=../backend/app --cov-report=xml

# Check for timing issues
pytest backend/ --maxfail=1 --tb=line
```

### Problem: Coverage upload issues
```bash
Error: Failed to upload coverage
```

**Solution:**
```bash
# Verify coverage files exist
ls -la coverage/

# Check coverage file format
file coverage/backend/coverage.xml

# Generate coverage in correct format
pytest backend/ --cov=../backend/app --cov-report=xml:coverage/backend/coverage.xml
cd frontend && npm test -- --coverage --coverageReporters=cobertura
```

---

## Common Error Messages

### "No tests ran"
```bash
# Check test discovery
pytest --collect-only backend/

# Verify test file naming
ls backend/unit/test_*.py

# Check pytest configuration
cat pytest.ini | grep python_files
```

### "Fixture not found"
```bash
# Check conftest.py files exist
ls tests/conftest.py tests/backend/conftest.py

# Verify fixture names
grep "def.*fixture" tests/conftest.py tests/backend/conftest.py

# Check fixture scope
grep -A 2 "@pytest.fixture" tests/backend/conftest.py
```

### "Permission denied"
```bash
# Fix script permissions
chmod +x tests/scripts/*.sh

# Check file ownership
ls -la tests/scripts/

# Run with bash explicitly
bash tests/scripts/run-all-tests.sh
```

### "Port already in use"
```bash
# Find process using port
lsof -i :8000
lsof -i :3000

# Kill process
kill -9 <PID>

# Use different ports for testing
export PORT=8001
export FRONTEND_PORT=3001
```

### "Memory limit exceeded"
```bash
# Increase Node.js memory
cd frontend && node --max_old_space_size=4096 npm test

# Run tests in smaller batches
pytest backend/unit/ -v
pytest backend/integration/ -v

# Use test isolation
pytest backend/ --forked --workers=2
```

---

## Quick Diagnostic Commands

### Environment Check
```bash
# Check all required tools
python3 --version
node --version
npm --version
cd backend && source venv/bin/activate && pytest --version

# Check environment variables
env | grep -E "(TESTING|ADMIN_API_KEY|GOOGLE_CLOUD_PROJECT)"

# Test imports
cd tests && python -c "from app.main import app; print('Backend import OK')"
cd frontend && npm test -- --dry-run --passWithNoTests
```

### Test Discovery Check
```bash
# Backend test discovery
cd tests && pytest --collect-only backend/ | grep "test session starts"

# Frontend test discovery
cd frontend && npm test -- --listTests --passWithNoTests

# Check test file naming
find tests/ -name "test_*.py" -o -name "*_test.py"
find frontend/src/ -name "*.test.js"
```

### Quick Test Run
```bash
# Fastest possible test run
pytest backend/unit/test_auth.py::TestAuthentication::test_valid_api_key -v
cd frontend && npm test -- --testNamePattern="should render" --watchAll=false
```

---

## Getting Help

### When to Seek Help
1. 🔍 Error persists after trying solutions in this guide
2. 🔍 Multiple tests failing with unclear error messages
3. 🔍 Performance degradation across test suite
4. 🔍 Environment setup fails on specific system
5. 🔍 CI/CD pipeline consistently failing

### Information to Provide
```bash
# System information
uname -a
python3 --version
node --version

# Error reproduction
./scripts/run-all-tests.sh > test_output.log 2>&1

# Environment details
env | grep -E "(PATH|TESTING|PYTHON|NODE)" > environment.log

# Test discovery
pytest --collect-only backend/ > test_discovery.log 2>&1
```

### Additional Resources
- [Testing Workflow](TESTING_WORKFLOW.md)
- [Commands Reference](COMMANDS_REFERENCE.md)
- [Main README](../README.md)
- [Project Documentation](../../documentation/)

---

## Quick Fix Checklist

Before seeking help, try these quick fixes:

- [ ] Run from correct directory (`cd tests`)
- [ ] Activate virtual environment (`source backend/venv/bin/activate`)
- [ ] Check environment variables (`env | grep TESTING`)
- [ ] Clear cache (`rm -rf .pytest_cache/`)
- [ ] Update dependencies (`pip install -r requirements.txt && npm install`)
- [ ] Make scripts executable (`chmod +x tests/scripts/*.sh`)
- [ ] Check Python path (`python -c "import sys; print(sys.path)"`)
- [ ] Verify imports (`python -c "from app.main import app"`)
- [ ] Run setup script (`./scripts/setup-test-env.sh`)
- [ ] Try minimal test (`pytest backend/unit/test_auth.py::test_valid_api_key -v`)