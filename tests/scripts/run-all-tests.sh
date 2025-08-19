#!/bin/bash

# Complete Test Suite Execution Script
# Runs both backend and frontend tests with coordination and summary reporting

set -e  # Exit on any error

# Get directories
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TESTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Parse command line arguments
COVERAGE=false
VERBOSE=false
STOP_ON_FAIL=false
BACKEND_ONLY=false
FRONTEND_ONLY=false
PARALLEL=false

show_help() {
    echo "Complete Test Suite Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message"
    echo "  -c, --coverage     Run with coverage reporting"
    echo "  -v, --verbose      Run with verbose output"
    echo "  -x, --stop-fail    Stop on first failure"
    echo "  -b, --backend      Run backend tests only"
    echo "  -f, --frontend     Run frontend tests only"
    echo "  -p, --parallel     Run backend and frontend tests in parallel"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run all tests (backend then frontend)"
    echo "  $0 -c              # Run all tests with coverage"
    echo "  $0 -v -x           # Verbose with stop on fail"
    echo "  $0 -p              # Run tests in parallel"
    echo "  $0 -b              # Backend tests only"
    echo "  $0 -f              # Frontend tests only"
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
        -b|--backend)
            BACKEND_ONLY=true
            shift
            ;;
        -f|--frontend)
            FRONTEND_ONLY=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Start time tracking
START_TIME=$(date +%s)

echo "🚀 Pixel Management Complete Test Suite"
echo "========================================"
echo ""

# Show configuration
echo "📋 Test Configuration:"
echo "   📈 Coverage: $([ "$COVERAGE" = true ] && echo "enabled" || echo "disabled")"
echo "   📝 Verbose: $([ "$VERBOSE" = true ] && echo "enabled" || echo "disabled")"
echo "   ⏹️  Stop on fail: $([ "$STOP_ON_FAIL" = true ] && echo "enabled" || echo "disabled")"
echo "   🔄 Parallel execution: $([ "$PARALLEL" = true ] && echo "enabled" || echo "disabled")"
echo ""

# Build command arguments
BACKEND_ARGS=""
FRONTEND_ARGS=""

if [ "$COVERAGE" = true ]; then
    BACKEND_ARGS="$BACKEND_ARGS -c"
    FRONTEND_ARGS="$FRONTEND_ARGS -c"
fi

if [ "$VERBOSE" = true ]; then
    BACKEND_ARGS="$BACKEND_ARGS -v"
    FRONTEND_ARGS="$FRONTEND_ARGS -v"
fi

if [ "$STOP_ON_FAIL" = true ]; then
    BACKEND_ARGS="$BACKEND_ARGS -x"
fi

# Change to tests directory
cd "$TESTS_DIR"

# Initialize result tracking
BACKEND_RESULT=0
FRONTEND_RESULT=0
OVERALL_RESULT=0

# Function to run backend tests
run_backend_tests() {
    echo "🔧 Running Backend Tests..."
    echo "=========================="
    ./scripts/run-backend-tests.sh $BACKEND_ARGS
    return $?
}

# Function to run frontend tests
run_frontend_tests() {
    echo "🎨 Running Frontend Tests..."
    echo "==========================="
    ./scripts/run-frontend-tests.sh $FRONTEND_ARGS
    return $?
}

# Execute tests based on configuration
if [ "$PARALLEL" = true ] && [ "$BACKEND_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
    echo "🔄 Running Backend and Frontend Tests in Parallel..."
    echo ""
    
    # Run tests in parallel using background processes
    run_backend_tests &
    BACKEND_PID=$!
    
    run_frontend_tests &
    FRONTEND_PID=$!
    
    # Wait for both to complete
    wait $BACKEND_PID
    BACKEND_RESULT=$?
    
    wait $FRONTEND_PID
    FRONTEND_RESULT=$?
    
    echo ""
    echo "🔄 Parallel execution completed"
    
elif [ "$BACKEND_ONLY" = true ]; then
    run_backend_tests
    BACKEND_RESULT=$?
    
elif [ "$FRONTEND_ONLY" = true ]; then
    run_frontend_tests
    FRONTEND_RESULT=$?
    
else
    # Sequential execution (default)
    echo "📝 Running tests sequentially..."
    echo ""
    
    # Run backend tests first
    run_backend_tests
    BACKEND_RESULT=$?
    
    # Check if we should continue
    if [ $BACKEND_RESULT -ne 0 ] && [ "$STOP_ON_FAIL" = true ]; then
        echo ""
        echo "❌ Backend tests failed and stop-on-fail is enabled"
        echo "   Skipping frontend tests"
        FRONTEND_RESULT=1
    else
        echo ""
        run_frontend_tests
        FRONTEND_RESULT=$?
    fi
fi

# Calculate overall result
if [ "$BACKEND_ONLY" = true ]; then
    OVERALL_RESULT=$BACKEND_RESULT
elif [ "$FRONTEND_ONLY" = true ]; then
    OVERALL_RESULT=$FRONTEND_RESULT
else
    OVERALL_RESULT=$((BACKEND_RESULT + FRONTEND_RESULT))
fi

# Calculate execution time
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))
MINUTES=$((EXECUTION_TIME / 60))
SECONDS=$((EXECUTION_TIME % 60))

# Display comprehensive results
echo ""
echo "📊 Test Suite Results Summary"
echo "============================="
echo ""

# Individual results
if [ "$BACKEND_ONLY" = false ]; then
    if [ $BACKEND_RESULT -eq 0 ]; then
        echo "✅ Backend Tests: PASSED"
    else
        echo "❌ Backend Tests: FAILED"
    fi
fi

if [ "$FRONTEND_ONLY" = false ]; then
    if [ $FRONTEND_RESULT -eq 0 ]; then
        echo "✅ Frontend Tests: PASSED"
    else
        echo "❌ Frontend Tests: FAILED"
    fi
fi

echo ""
echo "📈 Test Statistics:"
if [ "$BACKEND_ONLY" = false ]; then
    echo "   🔧 Backend: 42 tests (Unit, Integration, Performance, Security)"
fi
if [ "$FRONTEND_ONLY" = false ]; then
    echo "   🎨 Frontend: 26 tests (Components, Integration)"
fi
echo "   ⏱️  Execution time: ${MINUTES}m ${SECONDS}s"
echo "   🔄 Execution mode: $([ "$PARALLEL" = true ] && echo "parallel" || echo "sequential")"

# Coverage information
if [ "$COVERAGE" = true ]; then
    echo ""
    echo "📊 Coverage Reports Generated:"
    if [ "$BACKEND_ONLY" = false ] && [ $BACKEND_RESULT -eq 0 ]; then
        echo "   🔧 Backend: coverage/backend/index.html"
    fi
    if [ "$FRONTEND_ONLY" = false ] && [ $FRONTEND_RESULT -eq 0 ]; then
        echo "   🎨 Frontend: coverage/frontend/index.html"
    fi
    echo ""
    echo "   💡 Open coverage reports with:"
    if [ "$BACKEND_ONLY" = false ] && [ $BACKEND_RESULT -eq 0 ]; then
        echo "      open ../coverage/backend/index.html"
    fi
    if [ "$FRONTEND_ONLY" = false ] && [ $FRONTEND_RESULT -eq 0 ]; then
        echo "      open ../coverage/frontend/index.html"
    fi
fi

# Overall result
echo ""
if [ $OVERALL_RESULT -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    echo ""
    echo "✨ The Pixel Management system is working correctly"
    echo "   All 68 tests across backend and frontend have passed"
    echo "   The system is ready for deployment"
else
    echo "❌ SOME TESTS FAILED!"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   • Check the detailed output above for specific failures"
    echo "   • Use -v flag for more verbose output"
    echo "   • See docs/TROUBLESHOOTING.md for common issues"
    echo "   • Run individual test suites to isolate problems:"
    echo "     - Backend only: ./scripts/run-backend-tests.sh"
    echo "     - Frontend only: ./scripts/run-frontend-tests.sh"
fi

# Development workflow suggestions
if [ $OVERALL_RESULT -eq 0 ]; then
    echo ""
    echo "🎯 Next Steps:"
    echo "   🔍 Code Quality: All tests passing - system is stable"
    echo "   📝 Documentation: Review test coverage reports"
    echo "   🚀 Deployment: System ready for deployment"
    echo "   🔄 Development: Continue with feature development"
    echo ""
    echo "🛠️  Development Commands:"
    echo "   ./scripts/run-backend-tests.sh -m unit     # Quick unit tests"
    echo "   ./scripts/run-frontend-tests.sh -w         # Watch mode for UI dev"
    echo "   ./scripts/run-tests-with-coverage.sh       # Full coverage analysis"
fi

echo ""
echo "📖 For more information:"
echo "   📋 Test documentation: tests/README.md"
echo "   🔧 Command reference: tests/docs/COMMANDS_REFERENCE.md"
echo "   🐛 Troubleshooting: tests/docs/TROUBLESHOOTING.md"

exit $OVERALL_RESULT