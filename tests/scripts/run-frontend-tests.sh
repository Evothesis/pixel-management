#!/bin/bash

# Frontend Test Execution Script
# Runs all frontend tests with proper environment setup and optional coverage

set -e  # Exit on any error

# Get directories
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TESTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Parse command line arguments
COVERAGE=false
VERBOSE=false
WATCH=false
UPDATE_SNAPSHOTS=false
SPECIFIC_TEST=""
DEBUG=false

show_help() {
    echo "Frontend Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_PATTERN]"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message"
    echo "  -c, --coverage     Run with coverage reporting"
    echo "  -v, --verbose      Run with verbose output"
    echo "  -w, --watch        Run in watch mode (for development)"
    echo "  -u, --update       Update snapshots"
    echo "  -d, --debug        Run with debug output"
    echo "  -t, --test         Run specific test pattern or file"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all frontend tests"
    echo "  $0 -c                                 # Run with coverage"
    echo "  $0 -w                                 # Run in watch mode"
    echo "  $0 -t AdminLogin                      # Run AdminLogin tests"
    echo "  $0 -t components/ClientForm.test.js   # Run specific test file"
    echo "  $0 -t \"should render\"                # Run tests matching pattern"
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
        -w|--watch)
            WATCH=true
            shift
            ;;
        -u|--update)
            UPDATE_SNAPSHOTS=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
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

echo "🧪 Running Frontend Tests..."

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Check if package.json exists
if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

# Setup environment
echo "🔧 Setting up environment..."

# Set environment variables
export NODE_ENV=test
export CI=true
export REACT_APP_API_URL=http://localhost:8000
export REACT_APP_ENVIRONMENT=testing

# Change to frontend directory
cd "$FRONTEND_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules not found. Running npm install..."
    npm install
fi

# Build npm test command
NPM_CMD="npm test --"

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    NPM_CMD="$NPM_CMD --coverage"
fi

# Add verbose flag
if [ "$VERBOSE" = true ]; then
    NPM_CMD="$NPM_CMD --verbose"
fi

# Add watch mode
if [ "$WATCH" = true ]; then
    # Remove --watchAll=false for watch mode
    echo "🔄 Running in watch mode (press 'q' to quit)..."
else
    NPM_CMD="$NPM_CMD --watchAll=false"
fi

# Add snapshot update
if [ "$UPDATE_SNAPSHOTS" = true ]; then
    NPM_CMD="$NPM_CMD --updateSnapshot"
fi

# Add debug flag
if [ "$DEBUG" = true ]; then
    NPM_CMD="$NPM_CMD --runInBand"
fi

# Add specific test pattern
if [ -n "$SPECIFIC_TEST" ]; then
    # Check if it looks like a file path
    if [[ "$SPECIFIC_TEST" == *".test.js" ]] || [[ "$SPECIFIC_TEST" == *"/" ]]; then
        NPM_CMD="$NPM_CMD --testPathPattern=\"$SPECIFIC_TEST\""
    else
        NPM_CMD="$NPM_CMD --testNamePattern=\"$SPECIFIC_TEST\""
    fi
fi

# Coverage configuration
if [ "$COVERAGE" = true ]; then
    NPM_CMD="$NPM_CMD --coverageReporters=text-lcov --coverageReporters=html --coverageDirectory=../coverage/frontend"
fi

# Show command being executed
echo "🚀 Executing: $NPM_CMD"
echo ""

# Run the tests
eval $NPM_CMD
TEST_RESULT=$?

# Display results
echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Frontend tests passed!"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo "📊 Coverage report generated:"
        echo "   📄 Terminal report shown above"
        echo "   🌐 HTML report: coverage/frontend/index.html"
        echo "   💡 Open with: open ../coverage/frontend/index.html"
    fi
    
    if [ "$UPDATE_SNAPSHOTS" = true ]; then
        echo ""
        echo "📸 Snapshots updated successfully"
    fi
else
    echo "❌ Frontend tests failed!"
    echo "   💡 Use -v flag for more detailed output"
    echo "   💡 Use -d flag for debug mode"
    echo "   💡 See docs/TROUBLESHOOTING.md for help"
fi

# Show quick stats
echo ""
echo "📊 Test Summary:"
if [ -n "$SPECIFIC_TEST" ]; then
    echo "   🎯 Test pattern: $SPECIFIC_TEST"
else
    echo "   📂 Test scope: All frontend tests"
fi
echo "   📈 Coverage: $([ "$COVERAGE" = true ] && echo "enabled" || echo "disabled")"
echo "   📝 Verbose: $([ "$VERBOSE" = true ] && echo "enabled" || echo "disabled")"
echo "   🔄 Watch mode: $([ "$WATCH" = true ] && echo "enabled" || echo "disabled")"

# Show test file summary
echo ""
echo "📁 Frontend Test Files:"
echo "   🧩 Components: AdminLogin, ClientForm, ClientList, Dashboard"
echo "   🔗 Integration: auth-flow, client-management, api-integration"
echo "   📊 Total: ~26 tests across all components and workflows"

# Provide next steps
if [ $TEST_RESULT -eq 0 ] && [ "$WATCH" = false ]; then
    echo ""
    echo "🎯 Next steps:"
    echo "   Run backend tests:       ./scripts/run-backend-tests.sh"
    echo "   Run all tests:           ./scripts/run-all-tests.sh"
    echo "   Run with full coverage:  ./scripts/run-tests-with-coverage.sh"
    echo "   Development mode:        ./scripts/run-frontend-tests.sh -w"
fi

# Change back to tests directory
cd "$TESTS_DIR"

exit $TEST_RESULT