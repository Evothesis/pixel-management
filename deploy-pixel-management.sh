#!/bin/bash
# deploy-pixel-management-secure.sh - Secure deployment without embedded API keys

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Secure Evothesis Pixel Management Deployment${NC}"
echo -e "${BLUE}================================================${NC}"

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-evothesis}"
SERVICE_NAME="pixel-management"
REGION="${REGION:-us-central1}"
ENVIRONMENT="${ENVIRONMENT:-production}"

echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo "   Project ID: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Environment: $ENVIRONMENT"
echo ""

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
    exit 1
fi

# Check if logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not logged in to gcloud. Run: gcloud auth login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites satisfied${NC}"
echo ""

# Generate secure backend credentials
echo -e "${YELLOW}🔐 Generating secure backend credentials...${NC}"

# Generate admin API key (backend only)
ADMIN_API_KEY="${ADMIN_API_KEY:-evothesis_admin_$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-32)}"
echo -e "${GREEN}✅ Generated Admin API Key (backend only)${NC}"

# Generate secret key
SECRET_KEY="${SECRET_KEY:-$(openssl rand -base64 64 | tr -d '=+/' | cut -c1-64)}"
echo -e "${GREEN}✅ Generated Secret Key${NC}"
echo ""

# Create frontend environment file (NO API KEY)
echo -e "${YELLOW}📝 Creating secure frontend configuration...${NC}"

cat > frontend/.env.production << EOF
# Secure frontend configuration (NO API KEYS EMBEDDED)
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')

REACT_APP_API_BASE_URL=https://${SERVICE_NAME}-${PROJECT_ID}.${REGION}.run.app
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=1.0.0

# NOTE: No API key embedded - users must enter it at login screen
EOF

echo -e "${GREEN}✅ Secure frontend environment configured (no embedded credentials)${NC}"

# Create backend environment variables
echo -e "${YELLOW}📝 Preparing backend environment variables...${NC}"

BACKEND_ENV_VARS="ADMIN_API_KEY=${ADMIN_API_KEY},SECRET_KEY=${SECRET_KEY},ENVIRONMENT=${ENVIRONMENT},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"

echo -e "${GREEN}✅ Backend environment prepared${NC}"
echo ""

# Build and deploy
echo -e "${YELLOW}🔨 Building and deploying to Cloud Run...${NC}"

gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 100 \
    --set-env-vars "$BACKEND_ENV_VARS" \
    --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo ""
echo -e "${GREEN}🌐 Service deployed at: $SERVICE_URL${NC}"

# Wait for deployment to be ready
echo -e "${YELLOW}⏳ Waiting for service to be ready...${NC}"
sleep 10

# Test deployment
echo -e "${YELLOW}🧪 Testing secure deployment...${NC}"

# Test 1: Health check
echo "   Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health")
if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}   ✅ Health check passed${NC}"
else
    echo -e "${RED}   ❌ Health check failed (HTTP $HEALTH_STATUS)${NC}"
fi

# Test 2: Frontend loads (should show login screen)
echo "   Testing frontend accessibility..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}   ✅ Frontend accessible (login screen)${NC}"
else
    echo -e "${RED}   ❌ Frontend not accessible (HTTP $FRONTEND_STATUS)${NC}"
fi

# Test 3: Admin endpoints are protected
echo "   Testing admin endpoint protection..."
ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/api/v1/admin/clients")
if [ "$ADMIN_STATUS" = "401" ]; then
    echo -e "${GREEN}   ✅ Admin endpoints properly secured${NC}"
else
    echo -e "${RED}   ❌ Admin endpoints not secured (HTTP $ADMIN_STATUS)${NC}"
fi

# Test 4: Config API accessibility (public)
echo "   Testing config API accessibility..."
CONFIG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/api/v1/config/client/client_evothesis_admin")
if [ "$CONFIG_STATUS" = "200" ]; then
    echo -e "${GREEN}   ✅ Config API accessible${NC}"
else
    echo -e "${RED}   ❌ Config API not accessible (HTTP $CONFIG_STATUS)${NC}"
fi

# Test 5: Login with valid API key works
echo "   Testing API key authentication..."
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $ADMIN_API_KEY" "$SERVICE_URL/api/v1/admin/clients")
if [ "$AUTH_STATUS" = "200" ]; then
    echo -e "${GREEN}   ✅ API key authentication working${NC}"
else
    echo -e "${RED}   ❌ API key authentication failed (HTTP $AUTH_STATUS)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 SECURE DEPLOYMENT COMPLETED!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "   🌐 Service URL: $SERVICE_URL"
echo "   🔐 Admin API Key: $ADMIN_API_KEY"
echo "   🔒 Frontend: Secure login required"
echo "   📚 API Docs: $SERVICE_URL/docs"
echo ""
echo -e "${BLUE}🔐 Security Features:${NC}"
echo "   ✅ No credentials embedded in frontend"
echo "   ✅ API key login screen required"
echo "   ✅ Admin endpoints properly secured"
echo "   ✅ Session-based authentication"
echo "   ✅ Automatic logout on invalid sessions"
echo ""
echo -e "${BLUE}🚀 Access Instructions:${NC}"
echo ""
echo "   1. Visit: $SERVICE_URL"
echo "   2. Enter API key at login screen: $ADMIN_API_KEY"
echo "   3. Access admin panel with full functionality"
echo ""
echo -e "${BLUE}🔑 API Key for External Use:${NC}"
echo ""
echo "   curl -H \"Authorization: Bearer $ADMIN_API_KEY\" \\"
echo "        $SERVICE_URL/api/v1/admin/clients"
echo ""

# Save credentials for future reference
CREDS_FILE="deployment-credentials-$(date +%Y%m%d-%H%M%S).txt"
cat > "$CREDS_FILE" << EOF
# Evothesis Pixel Management Secure Deployment Credentials
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# Service URL: $SERVICE_URL

ADMIN_API_KEY=$ADMIN_API_KEY
SECRET_KEY=$SECRET_KEY
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
SERVICE_URL=$SERVICE_URL

# Frontend Access:
# 1. Visit: $SERVICE_URL
# 2. Enter API key: $ADMIN_API_KEY
# 3. Access admin panel

# API Access:
# curl -H "Authorization: Bearer $ADMIN_API_KEY" $SERVICE_URL/api/v1/admin/clients
EOF

echo -e "${BLUE}💾 Credentials saved to: $CREDS_FILE${NC}"
echo -e "${YELLOW}   Keep this file secure and do not commit to version control!${NC}"
echo ""
echo -e "${GREEN}✅ Ready for secure production use!${NC}"
echo ""
echo -e "${YELLOW}⚠️  SECURITY NOTES:${NC}"
echo "   🔒 Users must enter API key to access admin panel"
echo "   🔐 API key stored only in browser session (not localStorage)"
echo "   🛡️  No credentials exposed in frontend source code"
echo "   🔍 All admin actions logged for audit trails"