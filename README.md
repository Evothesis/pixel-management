# Evothesis Pixel Management

**Centralized configuration management system for Evothesis tracking infrastructure**

🌐 **Production Deployment**: https://pixel-management-275731808857.us-central1.run.app

## 🏗️ Architecture Overview

The Pixel Management system provides centralized client configuration and domain authorization for all Evothesis tracking VMs, enabling secure, privacy-compliant analytics infrastructure.

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  Pixel Management   │───▶│   Tracking VMs      │───▶│  Client Websites    │
│  - Web Admin UI     │    │  - Domain validation│    │  - Authorized sites │
│  - Client CRUD API  │    │  - Config retrieval │    │  - Dynamic pixels   │
│  - Domain auth      │    │  - Privacy enforcement│    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
          │                                                        │
          └────────────────────┐                                  │
                               ▼                                  │
                    ┌─────────────────────┐                      │
                    │   Firestore DB      │                      │
                    │  - Client configs   │◀─────────────────────┘
                    │  - Domain index     │
                    │  - Audit logs       │
                    └─────────────────────┘
```

## 🎯 Key Features

### **🔒 Domain Authorization System**
- **Critical Security**: Only authorized domains can collect tracking data
- **Real-time Validation**: Sub-100ms domain authorization for tracking VMs
- **O(1) Lookup Performance**: Fast domain index prevents unauthorized access

### **🛡️ Privacy Compliance Management**
- **Standard Level**: Full IP collection and basic tracking
- **GDPR Compliance**: IP hashing, consent requirements, automatic PII redaction
- **HIPAA Compliance**: Enhanced security, audit logging, BAA support

### **🏢 Multi-Tenant Architecture**
- **Owner/Billing Model**: Flexible client ownership and billing relationships
- **Agency Support**: Single owner can manage multiple client accounts
- **Access Control**: Role-based permissions for client management

### **⚙️ Deployment Flexibility**
- **Shared Infrastructure**: Cost-effective multi-tenant tracking VMs
- **Dedicated VMs**: High-traffic clients with isolated infrastructure
- **Seamless Migration**: Upgrade from shared to dedicated as needed

## 🚀 Technology Stack

- **Frontend**: React 18 with modern hooks and routing
- **Backend**: FastAPI with async/await and automatic API documentation
- **Database**: Google Firestore for scalable, real-time data storage
- **Hosting**: Google Cloud Run for serverless, auto-scaling deployment
- **Authentication**: Google Cloud IAM with service account security

## 📡 API Endpoints

### **Configuration API (For Tracking VMs)**

```bash
# Get client configuration by domain (CRITICAL for tracking security)
GET /api/v1/config/domain/{domain}

# Get configuration by client ID
GET /api/v1/config/client/{client_id}
```

**Example Response:**
```json
{
  "client_id": "client_abc123def456",
  "privacy_level": "gdpr",
  "ip_collection": {
    "enabled": false,
    "hash_required": true,
    "salt": "client-specific-salt-hash"
  },
  "consent": {
    "required": true,
    "default_behavior": "block"
  },
  "features": {},
  "deployment": {
    "type": "dedicated",
    "hostname": "analytics.clientcompany.com"
  }
}
```

### **Admin Management API**

```bash
# Client management
GET    /api/v1/admin/clients           # List all clients
POST   /api/v1/admin/clients           # Create new client
GET    /api/v1/admin/clients/{id}      # Get client details
PUT    /api/v1/admin/clients/{id}      # Update client configuration

# Domain management  
POST   /api/v1/admin/clients/{id}/domains/{domain}  # Add authorized domain
GET    /api/v1/admin/clients/{id}/domains           # List client domains
DELETE /api/v1/admin/clients/{id}/domains/{domain}  # Remove domain authorization
```

## 🛠️ Local Development

### **Prerequisites**
- Docker Desktop
- Node.js 18+ (for local frontend development)
- Git
- Google Cloud credentials (service account key)

### **Quick Start**

```bash
# Clone the repository
git clone <repository-url>
cd pixel-management

# Set up Google Cloud credentials
# 1. Download service account key as credentials.json
# 2. Place in project root
# 3. Set environment variable
export GOOGLE_CLOUD_PROJECT=your-project-id

# Start development environment (backend only)
docker-compose -f docker-compose.local.yml up -d

# OR start with full web interface (requires frontend setup)
docker-compose -f docker-compose.webapp.yml up -d

# Access points:
# - API Backend: http://localhost:8000
# - API Documentation: http://localhost:8000/docs (Swagger UI)
# - Health Check: http://localhost:8000/health
```

### **Development Workflow**

```bash
# Backend changes (hot reload enabled)
# Edit files in backend/app/ - changes auto-reload

# View logs for debugging
docker-compose -f docker-compose.local.yml logs -f

# Reset development environment  
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

## 🌐 Production Deployment

### **Google Cloud Run Deployment**

**Current Production URL**: https://pixel-management-275731808857.us-central1.run.app

#### **Prerequisites**
- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed locally

#### **Deployment Steps**

1. **Enable Required APIs**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable firestore.googleapis.com
   ```

2. **Set Up Service Account Permissions**
   ```bash
   # Grant Firestore access to default Compute Engine service account
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

3. **Deploy to Cloud Run**
   ```bash
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
     --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
   ```

4. **Verify Deployment**
   ```bash
   # Service health check
   curl https://pixel-management-275731808857.us-central1.run.app/health

   # Expected response:
   # {"status":"healthy","service":"pixel-management","database":"firestore_connected"}
   ```

### **Performance Metrics**
- **Response Time**: Monitor domain authorization endpoint latency
- **Error Rate**: Track 4xx/5xx responses for debugging
- **Database Performance**: Monitor Firestore read/write operations

### **Operational Commands**
```bash
# View service logs
gcloud run services logs read pixel-management --region us-central1

# Check service status
gcloud run services describe pixel-management --region us-central1

# Update service configuration
gcloud run services update pixel-management --region us-central1 --memory 1Gi
```

## 🚨 Troubleshooting

### **Common Issues**

**Health Check Fails:**
```bash
# Check Firestore permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members" \
  --filter="bindings.members:*compute@developer.gserviceaccount.com"

# Verify Firestore API is enabled
gcloud services list --enabled | grep firestore
```

**Frontend Not Loading:**
- Check if static files are being served correctly
- Verify React build completed successfully in container
- Check browser console for JavaScript errors

**API Calls Failing:**
- Verify CORS configuration allows requests from frontend domain
- Check that API routes are defined before catch-all routes in main.py
- Confirm environment variables are set correctly

**Domain Authorization Returning 404:**
- Verify domain was added through admin interface
- Check domain index exists in Firestore
- Ensure domain string exactly matches (case-sensitive)

### **Development Tips**

1. **Use API Documentation**: Visit `/docs` for interactive API testing
2. **Check Logs Frequently**: `docker-compose logs -f` during development
3. **Test Domain Authorization**: Always add domains before testing tracking
4. **Verify Data Persistence**: Test that data survives container restarts

## 📈 Scaling & Performance

### **Current Capacity**
- **Domain Lookups**: >1000 requests/second
- **Client Management**: Hundreds of concurrent admin operations
- **Data Storage**: Unlimited with Firestore's auto-scaling

### **Scaling Strategies**
- **Horizontal Scaling**: Cloud Run auto-scales based on request volume
- **Database Scaling**: Firestore handles scaling automatically
- **Caching**: Implement Redis for high-frequency domain lookups if needed

## 🤝 Contributing

### **Development Standards**
- **Python**: Black formatting, type hints, comprehensive docstrings
- **React**: ESLint configuration, functional components with hooks
- **API Design**: RESTful conventions, proper HTTP status codes
- **Testing**: Unit tests for critical domain authorization logic

### **Deployment Process**
1. Test changes locally with `docker-compose.local.yml`
2. Verify all tests pass and no TypeScript/ESLint errors
3. Deploy to staging environment for integration testing
4. Production deployment via Cloud Run

---

**Built with ❤️ for centralized configuration management and domain authorization**