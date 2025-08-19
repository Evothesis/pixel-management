#!/bin/bash

# Backend Test Execution Script
# Runs all backend tests with proper environment setup and optional coverage

set -e  # Exit on any error

# Get directories
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TESTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Parse command line arguments
COVERAGE=false
VERBOSE=false
MARKERS=""
SPECIFIC_TEST=""
STOP_ON_FAIL=false
PERFORMANCE=false

show_help() {
    echo "Backend Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_PATH]"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message"
    echo "  -c, --coverage     Run with coverage reporting"
    echo "  -v, --verbose      Run with verbose output"
    echo "  -x, --stop-fail    Stop on first failure"
    echo "  -p, --performance  Run only performance tests"
    echo "  -m, --markers      Run tests with specific markers (unit,integration,security,auth,critical)"
    echo "  -t, --test         Run specific test file or test function"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all backend tests"
    echo "  $0 -c                                 # Run with coverage"
    echo "  $0 -v -x                              # Verbose with stop on fail"
    echo "  $0 -m unit                            # Run only unit tests"
    echo "  $0 -m \"unit and auth\"                # Run unit AND auth tests"
    echo "  $0 -t backend/unit/test_auth.py       # Run specific test file"
    echo "  $0 -p                                 # Run performance tests only"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -x|--stop-fail)
            STOP_ON_FAIL=true
            shift
            ;;
        -p|--performance)
            PERFORMANCE=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        *)
            if [[ -z "$SPECIFIC_TEST" ]]; then
                SPECIFIC_TEST="$1"
            fi
            shift
            ;;
    esac
done

echo "🧪 Running Backend Tests..."

# Setup environment
echo "🔧 Setting up environment..."

# Set environment variables
export TESTING=true
export ADMIN_API_KEY=test_admin_key_12345
export GOOGLE_CLOUD_PROJECT=test-project
export FIRESTORE_EMULATOR_HOST=localhost:8080
export ENVIRONMENT=testing

# Activate virtual environment
if [ -f "$BACKEND_DIR/venv/bin/activate" ]; then
    echo "🔧 Activating Python virtual environment..."
    source "$BACKEND_DIR/venv/bin/activate"
else
    echo "⚠️  Virtual environment not found. Make sure to run setup-test-env.sh first"
    echo "   Or activate your virtual environment manually"
fi

# Change to tests directory
cd "$TESTS_DIR"

# Build pytest command
PYTEST_CMD="pytest"

# Add verbose flag
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add stop on fail flag
if [ "$STOP_ON_FAIL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Add markers
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
elif [ "$PERFORMANCE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m performance"
fi

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=../backend/app --cov-report=term-missing --cov-report=html:../coverage/backend"
fi

# Add test path
if [ -n "$SPECIFIC_TEST" ]; then
    TEST_PATH="$SPECIFIC_TEST"
else
    TEST_PATH="backend/"
fi

PYTEST_CMD="$PYTEST_CMD $TEST_PATH"

# Show command being executed
echo "🚀 Executing: $PYTEST_CMD"
echo ""

# Run the tests
eval $PYTEST_CMD
TEST_RESULT=$?

# Display results
echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Backend tests passed!"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo "📊 Coverage report generated:"
        echo "   📄 Terminal report shown above"
        echo "   🌐 HTML report: coverage/backend/index.html"
        echo "   💡 Open with: open ../coverage/backend/index.html"
    fi
    
    if [ "$PERFORMANCE" = true ]; then
        echo ""
        echo "⚡ Performance test results:"
        echo "   🎯 Domain authorization should be <100ms"
        echo "   🎯 Pixel generation should be <150ms"
        echo "   🎯 API endpoints should be <500ms"
    fi
else
    echo "❌ Backend tests failed!"
    echo "   💡 Use -v flag for more detailed output"
    echo "   💡 Use -x flag to stop on first failure"
    echo "   💡 See docs/TROUBLESHOOTING.md for help"
fi

# Show quick stats
echo ""
echo "📊 Test Summary:"
echo "   📂 Test directory: $TEST_PATH"
if [ -n "$MARKERS" ]; then
    echo "   🏷️  Test markers: $MARKERS"
elif [ "$PERFORMANCE" = true ]; then
    echo "   🏷️  Test markers: performance"
fi
echo "   📈 Coverage: $([ "$COVERAGE" = true ] && echo "enabled" || echo "disabled")"
echo "   📝 Verbose: $([ "$VERBOSE" = true ] && echo "enabled" || echo "disabled")"

# Provide next steps
if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "🎯 Next steps:"
    echo "   Run frontend tests:      ./scripts/run-frontend-tests.sh"
    echo "   Run all tests:           ./scripts/run-all-tests.sh"
    echo "   Run with full coverage:  ./scripts/run-tests-with-coverage.sh"
fi

exit $TEST_RESULT