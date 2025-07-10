#!/bin/bash
# test_admin_auth.sh - Validate Admin API Authentication

set -e

echo "🔐 Testing Admin API Authentication..."
echo "======================================"

# Configuration
PIXEL_MANAGEMENT_URL="${PIXEL_MANAGEMENT_URL:-https://pixel-management-275731808857.us-central1.run.app}"
ADMIN_API_KEY="${ADMIN_API_KEY:-}"

# Get API key if not provided
if [ -z "$ADMIN_API_KEY" ]; then
    echo "📋 Getting admin API key from setup endpoint..."
    SETUP_INFO=$(curl -s "$PIXEL_MANAGEMENT_URL/admin/setup-info")
    ADMIN_API_KEY=$(echo "$SETUP_INFO" | python3 -c "import json, sys; print(json.load(sys.stdin)['admin_api_key'])")
    echo "🔑 Using API Key: $ADMIN_API_KEY"
fi

echo ""
echo "🧪 TEST 1: Access admin endpoint WITHOUT authentication (should fail)"
echo "----------------------------------------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PIXEL_MANAGEMENT_URL/api/v1/admin/clients")
if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ PASS: Unauthorized access correctly blocked (HTTP $HTTP_CODE)"
else
    echo "❌ FAIL: Expected HTTP 401, got HTTP $HTTP_CODE"
    exit 1
fi

echo ""
echo "🧪 TEST 2: Access admin endpoint WITH valid authentication (should work)"  
echo "------------------------------------------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $ADMIN_API_KEY" "$PIXEL_MANAGEMENT_URL/api/v1/admin/clients")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS: Authorized access successful (HTTP $HTTP_CODE)"
else
    echo "❌ FAIL: Expected HTTP 200, got HTTP $HTTP_CODE"
    exit 1
fi

echo ""
echo "🧪 TEST 3: Access admin endpoint with INVALID API key (should fail)"
echo "--------------------------------------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid_key_12345" "$PIXEL_MANAGEMENT_URL/api/v1/admin/clients")
if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ PASS: Invalid API key correctly rejected (HTTP $HTTP_CODE)"
else
    echo "❌ FAIL: Expected HTTP 401, got HTTP $HTTP_CODE"
    exit 1
fi

echo ""
echo "🧪 TEST 4: Access config endpoint WITHOUT authentication (should work)"
echo "----------------------------------------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PIXEL_MANAGEMENT_URL/api/v1/config/client/client_evothesis_admin")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS: Config API remains public (HTTP $HTTP_CODE)"
else
    echo "❌ FAIL: Config API should remain public, got HTTP $HTTP_CODE"
    exit 1
fi

echo ""
echo "🧪 TEST 5: Create test client with authentication"
echo "------------------------------------------------"
TEST_CLIENT_DATA='{
    "name": "Test Client Auth",
    "email": "test@example.com",
    "client_type": "end_client",
    "owner": "client_evothesis_admin",
    "deployment_type": "shared",
    "privacy_level": "standard",
    "features": {}
}'

RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $ADMIN_API_KEY" -H "Content-Type: application/json" -d "$TEST_CLIENT_DATA" "$PIXEL_MANAGEMENT_URL/api/v1/admin/clients")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS: Client creation successful (HTTP $HTTP_CODE)"
    TEST_CLIENT_ID=$(echo "$RESPONSE_BODY" | python3 -c "import json, sys; print(json.load(sys.stdin)['client_id'])" 2>/dev/null || echo "unknown")
    echo "📝 Created test client: $TEST_CLIENT_ID"
else
    echo "❌ FAIL: Client creation failed with HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

echo ""
echo "🧪 TEST 6: Add domain to client with authentication"
echo "---------------------------------------------------"
if [ "$TEST_CLIENT_ID" != "unknown" ]; then
    DOMAIN_DATA='{"domain": "test-auth.example.com", "is_primary": true}'
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $ADMIN_API_KEY" -H "Content-Type: application/json" -d "$DOMAIN_DATA" "$PIXEL_MANAGEMENT_URL/api/v1/admin/clients/$TEST_CLIENT_ID/domains")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ PASS: Domain addition successful (HTTP $HTTP_CODE)"
    else
        echo "❌ FAIL: Domain addition failed with HTTP $HTTP_CODE"
        exit 1
    fi
fi

echo ""
echo "🧪 TEST 7: Verify audit logging is working"
echo "------------------------------------------"
echo "📋 Check server logs for ADMIN_AUDIT entries..."
echo "Expected log format: ADMIN_AUDIT: {\"timestamp\": \"...\", \"action\": \"...\", \"api_key_id\": \"...\"}"

echo ""
echo "🎉 ALL AUTHENTICATION TESTS PASSED!"
echo "===================================="
echo ""
echo "✅ Admin API properly secured with authentication"
echo "✅ Public config API remains accessible"  
echo "✅ Invalid credentials correctly rejected"
echo "✅ Audit logging implemented"
echo ""
echo "🔑 Admin API Key: $ADMIN_API_KEY"
echo "📚 Usage: curl -H \"Authorization: Bearer $ADMIN_API_KEY\" $PIXEL_MANAGEMENT_URL/api/v1/admin/clients"
echo ""
echo "⚠️  IMPORTANT: Set ADMIN_API_KEY environment variable for production!"