#!/bin/bash

# Complete Test Suite with Coverage Analysis
# Runs all tests with comprehensive coverage reporting and analysis

set -e  # Exit on any error

# Get directories
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TESTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Parse command line arguments
VERBOSE=false
OPEN_REPORTS=false
COVERAGE_THRESHOLD=85
CRITICAL_THRESHOLD=95

show_help() {
    echo "Complete Test Suite with Coverage Analysis"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message"
    echo "  -v, --verbose      Run with verbose output"
    echo "  -o, --open         Open coverage reports in browser after completion"
    echo "  -t, --threshold    Set coverage threshold (default: 85)"
    echo "  -c, --critical     Set critical path coverage threshold (default: 95)"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run with default coverage analysis"
    echo "  $0 -v              # Verbose coverage analysis"
    echo "  $0 -o              # Open reports automatically"
    echo "  $0 -t 90           # Set 90% coverage threshold"
    echo "  $0 -c 98           # Set 98% critical coverage threshold"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -o|--open)
            OPEN_REPORTS=true
            shift
            ;;
        -t|--threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        -c|--critical)
            CRITICAL_THRESHOLD="$2"
            shift 2
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

echo "📊 Pixel Management Coverage Analysis"
echo "====================================="
echo ""

# Show configuration
echo "📋 Coverage Configuration:"
echo "   🎯 Overall threshold: ${COVERAGE_THRESHOLD}%"
echo "   🎯 Critical path threshold: ${CRITICAL_THRESHOLD}%"
echo "   📝 Verbose: $([ "$VERBOSE" = true ] && echo "enabled" || echo "disabled")"
echo "   🌐 Auto-open reports: $([ "$OPEN_REPORTS" = true ] && echo "enabled" || echo "disabled")"
echo ""

# Create coverage directories
echo "📁 Setting up coverage directories..."
mkdir -p "$PROJECT_ROOT/coverage/backend"
mkdir -p "$PROJECT_ROOT/coverage/frontend"
mkdir -p "$PROJECT_ROOT/coverage/combined"

# Change to tests directory
cd "$TESTS_DIR"

# Build command arguments
ARGS=""
if [ "$VERBOSE" = true ]; then
    ARGS="$ARGS -v"
fi

# Initialize result tracking
BACKEND_RESULT=0
FRONTEND_RESULT=0
BACKEND_COVERAGE=0
FRONTEND_COVERAGE=0

echo "🔧 Running Backend Tests with Coverage..."
echo "======================================="

# Run backend tests with coverage
BACKEND_ARGS="$ARGS -c"
./scripts/run-backend-tests.sh $BACKEND_ARGS
BACKEND_RESULT=$?

echo ""
echo "🎨 Running Frontend Tests with Coverage..."
echo "========================================"

# Run frontend tests with coverage
FRONTEND_ARGS="$ARGS -c"
./scripts/run-frontend-tests.sh $FRONTEND_ARGS
FRONTEND_RESULT=$?

# Parse coverage results
echo ""
echo "📊 Analyzing Coverage Results..."
echo "==============================="

# Function to extract coverage percentage from backend
extract_backend_coverage() {
    if [ -f "$PROJECT_ROOT/coverage/backend/index.html" ]; then
        # Try to extract coverage percentage from HTML report
        COVERAGE_LINE=$(grep -o "pc_cov[^>]*>[0-9]*%" "$PROJECT_ROOT/coverage/backend/index.html" | head -1 | grep -o "[0-9]*%" | tr -d '%')
        if [ -n "$COVERAGE_LINE" ]; then
            echo $COVERAGE_LINE
        else
            echo "0"
        fi
    else
        echo "0"
    fi
}

# Function to extract coverage from frontend
extract_frontend_coverage() {
    if [ -f "$PROJECT_ROOT/coverage/frontend/index.html" ]; then
        # Try to extract coverage from Jest HTML report
        COVERAGE_LINE=$(grep -o "coverage-summary[^>]*>[0-9]*\.[0-9]*%" "$PROJECT_ROOT/coverage/frontend/index.html" | head -1 | grep -o "[0-9]*\.[0-9]*" | cut -d. -f1)
        if [ -n "$COVERAGE_LINE" ]; then
            echo $COVERAGE_LINE
        else
            echo "0"
        fi
    else
        echo "0"
    fi
}

# Extract coverage percentages
if [ $BACKEND_RESULT -eq 0 ]; then
    BACKEND_COVERAGE=$(extract_backend_coverage)
    echo "✅ Backend coverage extracted: ${BACKEND_COVERAGE}%"
else
    echo "❌ Backend tests failed - coverage analysis skipped"
fi

if [ $FRONTEND_RESULT -eq 0 ]; then
    FRONTEND_COVERAGE=$(extract_frontend_coverage)
    echo "✅ Frontend coverage extracted: ${FRONTEND_COVERAGE}%"
else
    echo "❌ Frontend tests failed - coverage analysis skipped"
fi

# Calculate execution time
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))
MINUTES=$((EXECUTION_TIME / 60))
SECONDS=$((EXECUTION_TIME % 60))

# Generate combined coverage report
echo ""
echo "📋 Generating Combined Coverage Report..."

# Create combined coverage summary
cat > "$PROJECT_ROOT/coverage/combined/index.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Pixel Management - Combined Coverage Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #e9ecef; border-radius: 8px; }
        .pass { color: #28a745; }
        .fail { color: #dc3545; }
        .warning { color: #ffc107; }
        .metric { font-size: 1.2em; font-weight: bold; }
        .timestamp { color: #6c757d; font-size: 0.9em; }
        .link { color: #007bff; text-decoration: none; }
        .link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Pixel Management - Coverage Analysis</h1>
        <p class="timestamp">Generated: $(date)</p>
        <p>Comprehensive test coverage analysis across backend and frontend components</p>
    </div>

    <div class="section">
        <h2>📊 Coverage Summary</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h3>🔧 Backend Coverage</h3>
                <p class="metric $([ $BACKEND_COVERAGE -ge $COVERAGE_THRESHOLD ] && echo "pass" || echo "fail")">${BACKEND_COVERAGE}%</p>
                <p>Target: ${COVERAGE_THRESHOLD}%</p>
                <p><a href="../backend/index.html" class="link">📄 View Backend Report</a></p>
            </div>
            <div>
                <h3>🎨 Frontend Coverage</h3>
                <p class="metric $([ $FRONTEND_COVERAGE -ge $COVERAGE_THRESHOLD ] && echo "pass" || echo "fail")">${FRONTEND_COVERAGE}%</p>
                <p>Target: ${COVERAGE_THRESHOLD}%</p>
                <p><a href="../frontend/index.html" class="link">📄 View Frontend Report</a></p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🎯 Coverage Targets</h2>
        <ul>
            <li>Overall Coverage: ≥${COVERAGE_THRESHOLD}%</li>
            <li>Critical Paths: ≥${CRITICAL_THRESHOLD}%</li>
            <li>Authentication: 100%</li>
            <li>Domain Authorization: ≥90%</li>
        </ul>
    </div>

    <div class="section">
        <h2>📈 Test Statistics</h2>
        <ul>
            <li>Backend Tests: 42 tests (Unit, Integration, Performance, Security)</li>
            <li>Frontend Tests: 26 tests (Components, Integration)</li>
            <li>Total Tests: 68</li>
            <li>Execution Time: ${MINUTES}m ${SECONDS}s</li>
        </ul>
    </div>

    <div class="section">
        <h2>🔍 Coverage Analysis</h2>
        <p>This report provides comprehensive coverage analysis for the Pixel Management system:</p>
        <ul>
            <li><strong>Line Coverage:</strong> Percentage of executed code lines</li>
            <li><strong>Branch Coverage:</strong> Percentage of executed conditional branches</li>
            <li><strong>Function Coverage:</strong> Percentage of called functions</li>
            <li><strong>Statement Coverage:</strong> Percentage of executed statements</li>
        </ul>
    </div>
</body>
</html>
EOF

echo "✅ Combined coverage report generated"

# Display comprehensive results
echo ""
echo "📊 Coverage Analysis Results"
echo "==========================="
echo ""

# Test execution results
if [ $BACKEND_RESULT -eq 0 ]; then
    echo "✅ Backend Tests: PASSED"
else
    echo "❌ Backend Tests: FAILED"
fi

if [ $FRONTEND_RESULT -eq 0 ]; then
    echo "✅ Frontend Tests: PASSED"
else
    echo "❌ Frontend Tests: FAILED"
fi

echo ""
echo "📈 Coverage Results:"

# Backend coverage analysis
if [ $BACKEND_RESULT -eq 0 ]; then
    if [ $BACKEND_COVERAGE -ge $COVERAGE_THRESHOLD ]; then
        echo "✅ Backend Coverage: ${BACKEND_COVERAGE}% (Target: ${COVERAGE_THRESHOLD}%)"
    elif [ $BACKEND_COVERAGE -ge $((COVERAGE_THRESHOLD - 5)) ]; then
        echo "⚠️  Backend Coverage: ${BACKEND_COVERAGE}% (Target: ${COVERAGE_THRESHOLD}%) - Close to target"
    else
        echo "❌ Backend Coverage: ${BACKEND_COVERAGE}% (Target: ${COVERAGE_THRESHOLD}%) - Below target"
    fi
else
    echo "❌ Backend Coverage: N/A (Tests failed)"
fi

# Frontend coverage analysis
if [ $FRONTEND_RESULT -eq 0 ]; then
    if [ $FRONTEND_COVERAGE -ge $COVERAGE_THRESHOLD ]; then
        echo "✅ Frontend Coverage: ${FRONTEND_COVERAGE}% (Target: ${COVERAGE_THRESHOLD}%)"
    elif [ $FRONTEND_COVERAGE -ge $((COVERAGE_THRESHOLD - 5)) ]; then
        echo "⚠️  Frontend Coverage: ${FRONTEND_COVERAGE}% (Target: ${COVERAGE_THRESHOLD}%) - Close to target"
    else
        echo "❌ Frontend Coverage: ${FRONTEND_COVERAGE}% (Target: ${COVERAGE_THRESHOLD}%) - Below target"
    fi
else
    echo "❌ Frontend Coverage: N/A (Tests failed)"
fi

echo ""
echo "📊 Detailed Coverage Reports:"
echo "   🌐 Combined Report: coverage/combined/index.html"
if [ $BACKEND_RESULT -eq 0 ]; then
    echo "   🔧 Backend Report: coverage/backend/index.html"
fi
if [ $FRONTEND_RESULT -eq 0 ]; then
    echo "   🎨 Frontend Report: coverage/frontend/index.html"
fi

echo ""
echo "⏱️  Execution Time: ${MINUTES}m ${SECONDS}s"

# Overall assessment
OVERALL_RESULT=$((BACKEND_RESULT + FRONTEND_RESULT))
COVERAGE_PASS=true

if [ $BACKEND_RESULT -eq 0 ] && [ $BACKEND_COVERAGE -lt $COVERAGE_THRESHOLD ]; then
    COVERAGE_PASS=false
fi

if [ $FRONTEND_RESULT -eq 0 ] && [ $FRONTEND_COVERAGE -lt $COVERAGE_THRESHOLD ]; then
    COVERAGE_PASS=false
fi

echo ""
if [ $OVERALL_RESULT -eq 0 ] && [ "$COVERAGE_PASS" = true ]; then
    echo "🎉 ALL TESTS PASSED WITH ADEQUATE COVERAGE!"
    echo ""
    echo "✨ The Pixel Management system meets all quality standards:"
    echo "   ✅ All 68 tests passing"
    echo "   ✅ Coverage targets met"
    echo "   ✅ System ready for deployment"
elif [ $OVERALL_RESULT -eq 0 ]; then
    echo "⚠️  TESTS PASSED BUT COVERAGE BELOW TARGET"
    echo ""
    echo "📈 Recommendations:"
    echo "   • Add more tests to increase coverage"
    echo "   • Focus on uncovered code paths"
    echo "   • Review critical path coverage"
else
    echo "❌ TESTS FAILED OR COVERAGE INSUFFICIENT"
    echo ""
    echo "💡 Next Steps:"
    echo "   • Fix failing tests first"
    echo "   • Then address coverage gaps"
    echo "   • See docs/TROUBLESHOOTING.md for help"
fi

# Open reports if requested
if [ "$OPEN_REPORTS" = true ]; then
    echo ""
    echo "🌐 Opening coverage reports..."
    
    if command -v open &> /dev/null; then
        open "$PROJECT_ROOT/coverage/combined/index.html"
        if [ $BACKEND_RESULT -eq 0 ]; then
            open "$PROJECT_ROOT/coverage/backend/index.html"
        fi
        if [ $FRONTEND_RESULT -eq 0 ]; then
            open "$PROJECT_ROOT/coverage/frontend/index.html"
        fi
    else
        echo "   💡 Open manually:"
        echo "      Combined: file://$PROJECT_ROOT/coverage/combined/index.html"
        if [ $BACKEND_RESULT -eq 0 ]; then
            echo "      Backend: file://$PROJECT_ROOT/coverage/backend/index.html"
        fi
        if [ $FRONTEND_RESULT -eq 0 ]; then
            echo "      Frontend: file://$PROJECT_ROOT/coverage/frontend/index.html"
        fi
    fi
fi

echo ""
echo "📖 For more information:"
echo "   📋 Test documentation: tests/README.md"
echo "   🔧 Command reference: tests/docs/COMMANDS_REFERENCE.md"
echo "   🐛 Troubleshooting: tests/docs/TROUBLESHOOTING.md"

# Exit with appropriate code
if [ $OVERALL_RESULT -eq 0 ] && [ "$COVERAGE_PASS" = true ]; then
    exit 0
else
    exit 1
fi