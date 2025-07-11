#!/bin/bash
# deploy-production.sh - Deploy to Cloud Run for production use

set -e

echo "🚀 Deploying Pixel Management to Google Cloud Run"
echo "   Authentication will be configured via Cloud Run console"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Check if project is set
if [ -z "$(gcloud config get-value project)" ]; then
    echo "❌ Please set your Google Cloud project:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
echo "📋 Deploying to project: $PROJECT_ID"

echo "📋 Deployment Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Region: us-central1"
echo "   Service: pixel-management"
echo "   Environment: production"
echo ""
echo "⚠️  IMPORTANT: Authentication must be configured after deployment"
echo "   via the Cloud Run console environment variables:"
echo "   - ADMIN_USERNAME (recommended: admin)"
echo "   - ADMIN_PASSWORD (set a strong password)"

read -p "🚀 Proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

echo "🏗️  Starting Cloud Run deployment..."

gcloud run deploy pixel-management \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars GOOGLE_CLOUD_PROJECT="$PROJECT_ID" \
  --set-env-vars ENVIRONMENT=production

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "🔧 NEXT STEPS - Configure Authentication:"
    echo "   1. Go to Google Cloud Console > Cloud Run"
    echo "   2. Click on 'pixel-management' service"
    echo "   3. Click 'EDIT & DEPLOY NEW REVISION'"
    echo "   4. Go to 'Variables & Secrets' tab"
    echo "   5. Add these environment variables:"
    echo "      ADMIN_USERNAME = admin"
    echo "      ADMIN_PASSWORD = [your secure password]"
    echo "   6. Click 'DEPLOY'"
    echo ""
    echo "🌐 Service URL (will require auth after step 6):"
    gcloud run services describe pixel-management --region=us-central1 --format='value(status.url)'
    echo ""
    echo "⚠️  Until authentication is configured, the service will"
    echo "   generate a random password (check logs for temp password)"
else
    echo "❌ Deployment failed"
    exit 1
fi