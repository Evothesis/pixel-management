#!/bin/bash
# post-deploy-test.sh - Verify deployment worked correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Post-Deployment Verification Tests${NC}"
echo -e "${BLUE}=====================================${NC}"

# Get service URL and API key from deployment
SERVICE_URL="${1:-https://pixel-management-evothesis.us-central1.run.app}"
API_KEY="$2"

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}📋 Getting API key from service...${NC}"
    API_KEY=$(curl -s "$SERVICE_URL/admin/setup-info" | python3 -c "import json, sys; print(json.load(sys.stdin)['admin_api_key'])" 2>/dev/null || echo "")
    
    if [ -z "$API_KEY" ]; then
        echo -e "${RED}❌ Could not retrieve API key from service${NC}"
        echo "   Usage: $0 <service_url> <api_key>"
        exit 1
    fi
fi

echo "🌐 Service URL: $SERVICE_URL"
echo "🔑 API Key: ${API_KEY:0:20}..."
echo ""

# Test counter
TESTS_PASSED=0
TESTS_TOTAL=0

run_test() {
    local test_name="$1"
    local command="$2"
    local expected_code="$3"
    local description="$4"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "${YELLOW}Test $TESTS_TOTAL: $test_name${NC}"
    echo "   $description"
    
    HTTP_CODE=$(eval "$command")
    
    if [ "$HTTP_CODE" = "$expected_code" ]; then
        echo -e "${GREEN}   ✅ PASS (HTTP $HTTP_CODE)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}   ❌ FAIL (Expected HTTP $expected_code, got HTTP $HTTP_CODE)${NC}"
    fi
    echo ""
}

# Test 1: Health Check
run_test "Health Check" \
    "curl -s -o /dev/null -w '%{http_code}' '$SERVICE_URL/health'" \
    "200" \
    "Basic service health and connectivity"

# Test 2: Frontend Loading
run_test "Frontend Loading" \
    "curl -s -o /dev/null -w '%{http_code}' '$SERVICE_URL/'" \
    "200" \
    "React frontend serves correctly"

# Test 3: API Documentation
run_test "API Documentation" \
    "curl -s -o /dev/null -w '%{http_code}' '$SERVICE_URL/docs'" \
    "200" \
    "FastAPI documentation accessible"

# Test 4: Unauthorized Admin Access (Should Fail)
run_test "Unauthorized Admin Access" \
    "curl -s -o /dev/null -w '%{http_code}' '$SERVICE_URL/api/v1/admin/clients'" \
    "401" \
    "Admin endpoints properly secured"

# Test 5: Authorized Admin Access (Should Work)
run_test "Authorized Admin Access" \
    "curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer $API_KEY' '$SERVICE_URL/api/v1/admin/clients'" \
    "200" \
    "Valid API key grants admin access"

# Test 6: Invalid API Key (Should Fail)
run_test "Invalid API Key" \
    "curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer invalid_key_123' '$SERVICE_URL/api/v1/admin/clients'" \
    "401" \
    "Invalid API keys are rejected"

# Test 7: Public Config API (Should Work)
run_test "Public Config API" \
    "curl -s -o /dev/null -w '%{http_code}' '$SERVICE_URL/api/v1/config/client/client_evothesis_admin'" \
    "200" \
    "Config API remains publicly accessible"

# Test 8: Domain Authorization (Should Fail for Unknown Domain)
run_test "Domain Authorization" \
    "curl -s -o /dev/null -w '%{http_code}' '$SERVICE_URL/api/v1/config/domain/unknown-domain.com'" \
    "404" \
    "Unknown domains are properly rejected"

echo -e "${BLUE}📊 Test Results Summary${NC}"
echo -e "${BLUE}======================${NC}"

if [ "$TESTS_PASSED" -eq "$TESTS_TOTAL" ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! ($TESTS_PASSED/$TESTS_TOTAL)${NC}"
    echo -e "${GREEN}✅ Deployment is working correctly${NC}"
    
    echo ""
    echo -e "${BLUE}🚀 Ready for Production Use!${NC}"
    echo ""
    echo -e "${YELLOW}Quick Start Guide:${NC}"
    echo ""
    echo "1. Access Admin Panel:"
    echo "   🌐 $SERVICE_URL"
    echo ""
    echo "2. Use API directly:"
    echo "   📋 List clients:"
    echo "      curl -H \"Authorization: Bearer $API_KEY\" \\"
    echo "           $SERVICE_URL/api/v1/admin/clients"
    echo ""
    echo "   🏗️  Create client:"
    echo "      curl -X POST \\"
    echo "           -H \"Authorization: Bearer $API_KEY\" \\"
    echo "           -H \"Content-Type: application/json\" \\"
    echo "           -d '{\"name\":\"Test Client\",\"owner\":\"client_evothesis_admin\",\"deployment_type\":\"shared\",\"privacy_level\":\"standard\"}' \\"
    echo "           $SERVICE_URL/api/v1/admin/clients"
    echo ""
    echo "3. API Documentation:"
    echo "   📚 $SERVICE_URL/docs"
    
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED! ($TESTS_PASSED/$TESTS_TOTAL passed)${NC}"
    echo -e "${RED}🚨 Deployment may have issues${NC}"
    
    echo ""
    echo -e "${YELLOW}🔧 Troubleshooting:${NC}"
    echo "1. Check service logs:"
    echo "   gcloud run logs read pixel-management --region=us-central1"
    echo ""
    echo "2. Verify environment variables:"
    echo "   gcloud run services describe pixel-management --region=us-central1"
    echo ""
    echo "3. Test manual deployment:"
    echo "   ./deploy-pixel-management.sh"
    
    exit 1
fi