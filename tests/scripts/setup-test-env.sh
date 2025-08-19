#!/bin/bash

# Test Environment Setup Script
# Sets up all dependencies and environment variables for running the Pixel Management test suite

set -e  # Exit on any error

echo "🚀 Setting up Pixel Management Test Environment..."

# Get the project root directory (assuming we're in tests/scripts/)
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TESTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 Tests directory: $TESTS_DIR"

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python version: $PYTHON_VERSION"

# Check Node.js version
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js version: $NODE_VERSION"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

NPM_VERSION=$(npm --version)
echo "✅ npm version: $NPM_VERSION"

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd "$PROJECT_ROOT/backend"

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in backend directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend dependencies installed"

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd "$PROJECT_ROOT/frontend"

if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

npm install

echo "✅ Frontend dependencies installed"

# Set up environment variables
echo "🔧 Setting up environment variables..."

# Create or update .env file for testing
cd "$PROJECT_ROOT"

cat > .env.test << EOF
# Test Environment Configuration
TESTING=true
ENVIRONMENT=testing

# Authentication
ADMIN_API_KEY=test_admin_key_12345

# Database
GOOGLE_CLOUD_PROJECT=test-project
FIRESTORE_EMULATOR_HOST=localhost:8080

# API Configuration
COLLECTION_API_URL=http://localhost:8001/collect
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOG=true
EOF

echo "✅ Environment variables configured"

# Validate test configuration
echo "🔍 Validating test configuration..."

cd "$TESTS_DIR"

# Check pytest configuration
if [ ! -f "../pytest.ini" ]; then
    echo "❌ pytest.ini not found in project root"
    exit 1
fi

echo "✅ pytest.ini found"

# Check test directory structure
required_dirs=("backend" "frontend" "backend/unit" "backend/integration" "backend/security" "frontend/components" "frontend/integration")

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ Required test directory missing: $dir"
        exit 1
    fi
done

echo "✅ Test directory structure validated"

# Test backend imports
echo "🔍 Testing backend imports..."
cd "$PROJECT_ROOT/backend"
source venv/bin/activate

python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.main import app
    from app.firestore_client import firestore_client
    print('✅ Backend imports successful')
except ImportError as e:
    print(f'❌ Backend import error: {e}')
    sys.exit(1)
"

# Test frontend dependencies
echo "🔍 Testing frontend dependencies..."
cd "$PROJECT_ROOT/frontend"

# Check if React Testing Library is available
npm list @testing-library/react > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ React Testing Library available"
else
    echo "❌ React Testing Library not found"
    exit 1
fi

# Check if Jest is available
npm list jest > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Jest available"
else
    echo "❌ Jest not found"
    exit 1
fi

# Create coverage directories
echo "📁 Creating coverage directories..."
mkdir -p "$PROJECT_ROOT/coverage/backend"
mkdir -p "$PROJECT_ROOT/coverage/frontend"

echo "✅ Coverage directories created"

# Make test scripts executable
echo "🔧 Making test scripts executable..."
chmod +x "$TESTS_DIR/scripts/"*.sh

echo "✅ Test scripts made executable"

# Run a quick smoke test
echo "🧪 Running smoke tests..."

echo "🔬 Testing backend pytest..."
cd "$TESTS_DIR"
export TESTING=true
export ADMIN_API_KEY=test_admin_key_12345
export GOOGLE_CLOUD_PROJECT=test-project

# Activate backend virtual environment
source "$PROJECT_ROOT/backend/venv/bin/activate"

# Test pytest collection
pytest --collect-only backend/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Backend test collection successful"
else
    echo "❌ Backend test collection failed"
    exit 1
fi

echo "🔬 Testing frontend jest..."
cd "$PROJECT_ROOT/frontend"

# Test Jest configuration
npm test -- --passWithNoTests --watchAll=false > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Frontend test configuration successful"
else
    echo "❌ Frontend test configuration failed"
    exit 1
fi

# Summary
echo ""
echo "🎉 Test environment setup complete!"
echo ""
echo "📋 Summary:"
echo "   ✅ Python dependencies installed"
echo "   ✅ Node.js dependencies installed"
echo "   ✅ Environment variables configured"
echo "   ✅ Test directory structure validated"
echo "   ✅ Import tests successful"
echo "   ✅ Coverage directories created"
echo "   ✅ Scripts made executable"
echo "   ✅ Smoke tests passed"
echo ""
echo "🚀 Ready to run tests!"
echo ""
echo "Next steps:"
echo "   Run all tests:           ./scripts/run-all-tests.sh"
echo "   Run backend tests:       ./scripts/run-backend-tests.sh"
echo "   Run frontend tests:      ./scripts/run-frontend-tests.sh"
echo "   Run with coverage:       ./scripts/run-tests-with-coverage.sh"
echo ""
echo "For more information, see: tests/README.md"