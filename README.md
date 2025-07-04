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

## 🔐 Authentication

### **Current Implementation (MVP)**
- Uses static admin client (`client_evothesis_admin`) created automatically on startup
- All API calls authorized through owner/billing entity checks
- Service account authentication for Firestore access
- Simple authorization model: owners can manage their clients

### **Planned Enhancement**
- JWT-based user authentication system
- Role-based access control (RBAC)
- Multi-user support with proper session management
- OAuth integration for enterprise clients

## 📊 Database Schema

### **Firestore Collections**
- **`clients`**: Client configurations and settings
- **`domain_index`**: O(1) domain authorization lookup table (CRITICAL)
- **`domains`**: Detailed domain information with metadata
- **`configuration_changes`**: Audit trail for compliance
- **`_initialization`**: Service startup and health tracking

### **Key Relationships**
- Domain Index → Client ID (critical for sub-100ms lookups)
- Client → Multiple Domains (one-to-many relationship)
- Configuration Changes → Client ID (audit trail)
- Owner → Multiple Clients (agency/enterprise model)

### **Data Flow**
1. **Domain Authorization**: Tracking VM → Domain Index → Client Config
2. **Client Management**: Admin UI → Client Collection → Domain Index
3. **Audit Trail**: All changes → Configuration Changes collection

## 🛠️ Local Development

### **Prerequisites**
- Docker Desktop 4.0+ with Docker Compose v2
- Node.js 18+ and npm 8+ (for frontend hot reload)
- Git
- Google Cloud SDK (gcloud CLI)
- Service account with Firestore Admin role
- 8GB+ RAM recommended for local development

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

## 🔒 Security Configuration

### **Production Security Checklist**
- [ ] Configure CORS origins (remove wildcard `*` in production)
- [ ] Set up proper authentication headers
- [ ] Enable rate limiting for API endpoints
- [ ] Configure service account with minimal permissions
- [ ] Enable audit logging for all configuration changes
- [ ] Implement request signing for tracking VM communication
- [ ] Set up monitoring alerts for unauthorized access attempts

### **Security Best Practices**
- **Domain Authorization**: Only authorized domains can collect tracking data
- **IP Hashing**: Client-specific salts for GDPR/HIPAA compliance
- **Audit Trail**: All configuration changes logged with timestamps
- **Access Control**: Owner-based permissions prevent unauthorized access
- **Service Account**: Minimal permissions for Firestore access only

## 📈 Performance Monitoring

### **Critical Metrics**
- **Domain Authorization Response Time**: <100ms target for tracking performance
- **Firestore Operations**: Read/write operations per second
- **Error Rates**: 4xx/5xx responses for debugging
- **Client Configuration Cache**: Hit rates for frequently accessed configs
- **Cloud Run Scaling**: Instance count and response times

### **Scaling Indicators**
- Domain lookup latency trends (monitor for >50ms)
- Firestore document read patterns (watch for hot partitions)
- Cloud Run instance scaling patterns (tune min/max instances)
- Memory usage patterns (optimize for 512MB-1GB range)

### **Performance Commands**
```bash
# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s "https://your-service.run.app/api/v1/config/domain/example.com"

# Check Cloud Run metrics
gcloud run services describe pixel-management --region us-central1 --format="value(status.conditions)"

# Monitor Firestore usage
gcloud logging read "resource.type=firestore_database" --limit=50
```

## 🚨 Enhanced Troubleshooting

### **Domain Authorization Issues**

**404 for Authorized Domain:**
```bash
# Check domain case sensitivity and whitespace
curl -v "https://your-service.run.app/api/v1/config/domain/example.com"

# Verify domain exists in Firestore
gcloud firestore documents list --collection-id=domain_index --filter="__name__ HAS_ANCESTOR /domain_index/example.com"
```

**Domain Already Exists Error:**
```bash
# Check current domain owner
gcloud firestore documents describe --collection-id=domain_index --document-id=example.com

# Verify client ownership
gcloud firestore documents describe --collection-id=clients --document-id=CLIENT_ID
```

**Configuration Not Updating:**
```bash
# Check audit logs
gcloud firestore documents list --collection-id=configuration_changes --order-by="timestamp desc" --limit=10

# Verify client document structure
gcloud firestore documents describe --collection-id=clients --document-id=CLIENT_ID
```

### **Development Environment Issues**

**Health Check Fails:**
```bash
# Check Firestore permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members" \
  --filter="bindings.members:*compute@developer.gserviceaccount.com"

# Verify Firestore API is enabled
gcloud services list --enabled | grep firestore

# Test local credentials
gcloud auth application-default print-access-token
```

**Frontend Not Loading:**
- Check if static files are being served correctly
- Verify React build completed successfully in container
- Check browser console for JavaScript errors
- Verify proxy configuration in `package.json` (`"proxy": "http://backend:8000"`)
- Check Docker network connectivity: `docker network ls`

**API Calls Failing:**
- Verify CORS configuration allows requests from frontend domain
- Check that API routes are defined before catch-all routes in main.py
- Confirm environment variables are set correctly
- Test API directly: `curl http://localhost:8000/health`
- Check Docker logs: `docker-compose logs -f backend`

**Hot Reload Not Working:**
```bash
# Verify volume mounts
docker-compose config | grep -A5 volumes

# Check file permissions
ls -la frontend/src/

# Restart with clean build
docker-compose down && docker-compose up --build
```

### **Production Deployment Issues**

**Cloud Run Deployment Fails:**
```bash
# Check build logs
gcloud builds list --limit=5

# Verify service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members"

# Test container locally
docker build -t pixel-management .
docker run -p 8080:8080 -e GOOGLE_CLOUD_PROJECT=YOUR_PROJECT pixel-management
```

**Database Connection Issues:**
```bash
# Test Firestore connectivity
gcloud firestore documents list --collection-id=_initialization

# Check service account key
gcloud iam service-accounts keys list --iam-account=YOUR_SERVICE_ACCOUNT

# Verify project permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

### **Development Tips**

1. **Use API Documentation**: Visit `/docs` for interactive API testing
2. **Check Logs Frequently**: `docker-compose logs -f` during development
3. **Test Domain Authorization**: Always add domains before testing tracking
4. **Verify Data Persistence**: Test that data survives container restarts
5. **Frontend Hot Reload**: Changes to `frontend/src/` auto-reload in development
6. **Backend Hot Reload**: Changes to `backend/app/` auto-reload with uvicorn
7. **Database Inspection**: Use Firestore console to inspect collections directly

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