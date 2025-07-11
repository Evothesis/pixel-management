#!/bin/bash
# test_automation.sh - Automated API and Authentication Testing

set -e

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
ADMIN_API_KEY=""
TEST_CLIENT_ID=""
TOTAL_TESTS=0
PASSED_TESTS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test tracking
test_count() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

test_pass() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "   ${GREEN}✅ PASS${NC}: $1"
}

test_fail() {
    echo -e "   ${RED}❌ FAIL${NC}: $1"
}

test_info() {
    echo -e "${BLUE}🧪 TEST $TOTAL_TESTS${NC}: $1"
}

test_section() {
    echo ""
    echo -e "${YELLOW}▶ $1${NC}"
    echo "======================================"
}

# Get API key from setup endpoint
get_api_key() {
    echo "🔑 Getting admin API key from setup endpoint..."
    
    SETUP_RESPONSE=$(curl -s "$API_BASE/admin/setup-info" 2>/dev/null || echo "")
    
    if [ -z "$SETUP_RESPONSE" ]; then
        echo -e "${RED}❌ Backend not responding at $API_BASE${NC}"
        exit 1
    fi
    
    ADMIN_API_KEY=$(echo "$SETUP_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data['admin_api_key'])
except:
    print('')
" 2>/dev/null)
    
    if [ -z "$ADMIN_API_KEY" ]; then
        echo -e "${RED}❌ Could not extract API key from setup endpoint${NC}"
        exit 1
    fi
    
    echo "🔑 Using API Key: ${ADMIN_API_KEY:0:20}..."
}

# Test 1: Health endpoint
test_health() {
    test_section "Health & Connectivity"
    test_count
    test_info "Health endpoint accessibility"
    
    HEALTH_RESPONSE=$(curl -s "$API_BASE/health" 2>/dev/null || echo "")
    
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        test_pass "Health endpoint returns healthy status"
    else
        test_fail "Health endpoint not responding correctly"
    fi
}

# Test 2: Authentication blocking
test_auth_blocking() {
    test_section "Authentication Security"
    test_count
    test_info "Admin endpoint blocks unauthenticated requests"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/v1/admin/clients" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "403" ]; then
        test_pass "Admin endpoint correctly blocks unauthenticated access (HTTP 403)"
    else
        test_fail "Admin endpoint should block unauthenticated access, got HTTP $HTTP_CODE"
    fi
}

# Test 3: Valid authentication
test_auth_success() {
    test_count
    test_info "Admin endpoint accepts valid authentication"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $ADMIN_API_KEY" \
        "$API_BASE/api/v1/admin/clients" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Valid API key grants access to admin endpoints (HTTP 200)"
    else
        test_fail "Valid API key should grant access, got HTTP $HTTP_CODE"
    fi
}

# Test 4: Invalid API key rejection
test_invalid_auth() {
    test_count
    test_info "Admin endpoint rejects invalid API key"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer invalid_key_12345" \
        "$API_BASE/api/v1/admin/clients" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "401" ]; then
        test_pass "Invalid API key correctly rejected (HTTP 401)"
    else
        test_fail "Invalid API key should be rejected, got HTTP $HTTP_CODE"
    fi
}

# Test 5: Client CRUD operations
test_client_crud() {
    test_section "Client Management CRUD"
    
    # Create client
    test_count
    test_info "Create new client"
    
    CLIENT_DATA='{
        "name": "Automated Test Client",
        "email": "automated-test@example.com",
        "client_type": "end_client",
        "owner": "client_evothesis_admin",
        "deployment_type": "shared",
        "privacy_level": "standard",
        "features": {}
    }'
    
    CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $ADMIN_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$CLIENT_DATA" \
        "$API_BASE/api/v1/admin/clients" 2>/dev/null || echo -e "\n000")
    
    # Extract HTTP code (last line) and response body (all but last line)
    HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
    RESPONSE_BODY=$(echo "$CREATE_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        TEST_CLIENT_ID=$(echo "$RESPONSE_BODY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data['client_id'])
except:
    print('')
" 2>/dev/null)
        
        if [ -n "$TEST_CLIENT_ID" ]; then
            test_pass "Client created successfully (ID: $TEST_CLIENT_ID)"
        else
            test_fail "Client created but no client_id returned"
        fi
    else
        test_fail "Client creation failed (HTTP $HTTP_CODE)"
    fi
    
    # Read client
    if [ -n "$TEST_CLIENT_ID" ]; then
        test_count
        test_info "Read created client"
        
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $ADMIN_API_KEY" \
            "$API_BASE/api/v1/admin/clients/$TEST_CLIENT_ID" 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ]; then
            test_pass "Client retrieved successfully"
        else
            test_fail "Failed to retrieve client (HTTP $HTTP_CODE)"
        fi
    fi
    
    # Verify client in list
    test_count
    test_info "Verify client appears in list"
    
    LIST_RESPONSE=$(curl -s \
        -H "Authorization: Bearer $ADMIN_API_KEY" \
        "$API_BASE/api/v1/admin/clients" 2>/dev/null || echo "")
    
    if echo "$LIST_RESPONSE" | grep -q "Automated Test Client"; then
        test_pass "Client appears in client list"
    else
        test_fail "Client not found in client list"
    fi
}

# Test 6: Domain management
test_domain_management() {
    test_section "Domain Management"
    
    if [ -z "$TEST_CLIENT_ID" ]; then
        echo "   ⚠️  Skipping domain tests (no test client available)"
        return
    fi
    
    # Add domain
    test_count
    test_info "Add domain to client"
    
    DOMAIN_DATA='{"domain": "automated-test.example.com", "is_primary": true}'
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $ADMIN_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$DOMAIN_DATA" \
        "$API_BASE/api/v1/admin/clients/$TEST_CLIENT_ID/domains" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Domain added successfully"
    else
        test_fail "Failed to add domain (HTTP $HTTP_CODE)"
    fi
    
    # List domains
    test_count
    test_info "List client domains"
    
    DOMAINS_RESPONSE=$(curl -s \
        -H "Authorization: Bearer $ADMIN_API_KEY" \
        "$API_BASE/api/v1/admin/clients/$TEST_CLIENT_ID/domains" 2>/dev/null || echo "")
    
    if echo "$DOMAINS_RESPONSE" | grep -q "automated-test.example.com"; then
        test_pass "Domain appears in domain list"
    else
        test_fail "Domain not found in domain list"
    fi
}

# Test 7: Public endpoints
test_public_endpoints() {
    test_section "Public Endpoint Access"
    
    test_count
    test_info "Config endpoint accessible without auth"
    
    # This should work without authentication
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "$API_BASE/api/v1/config/client/client_evothesis_admin" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Public config endpoint accessible without auth"
    else
        test_fail "Public config endpoint should be accessible (HTTP $HTTP_CODE)"
    fi
}

# Cleanup
cleanup() {
    test_section "Cleanup"
    
    if [ -n "$TEST_CLIENT_ID" ]; then
        test_count
        test_info "Delete test client"
        
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X DELETE \
            -H "Authorization: Bearer $ADMIN_API_KEY" \
            "$API_BASE/api/v1/admin/clients/$TEST_CLIENT_ID" 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ]; then
            test_pass "Test client deleted successfully"
        else
            test_fail "Failed to delete test client (HTTP $HTTP_CODE)"
        fi
    fi
}

# Generate test report
generate_report() {
    echo ""
    echo "======================================"
    echo -e "${BLUE}📊 TEST SUMMARY${NC}"
    echo "======================================"
    echo -e "Total Tests: ${YELLOW}$TOTAL_TESTS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"
    
    if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
        echo ""
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
        echo -e "${GREEN}✅ Authentication system working correctly${NC}"
        echo -e "${GREEN}✅ API endpoints functioning properly${NC}"
        echo -e "${GREEN}✅ Ready for frontend testing${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}❌ SOME TESTS FAILED${NC}"
        echo -e "${YELLOW}⚠️  Check backend logs and configuration${NC}"
        exit 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🚀 Pixel Management API Test Suite${NC}"
    echo "======================================"
    echo "Testing backend: $API_BASE"
    echo ""
    
    get_api_key
    test_health
    test_auth_blocking
    test_auth_success
    test_invalid_auth
    test_client_crud
    test_domain_management
    test_public_endpoints
    cleanup
    generate_report
}

# Handle interruption
trap cleanup EXIT

# Run tests
main "$@"