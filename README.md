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
- **Access Control**: HTTP Basic Auth protection for admin interface

### **⚙️ Deployment Flexibility**
- **Shared Infrastructure**: Cost-effective multi-tenant tracking VMs
- **Dedicated VMs**: High-traffic clients with isolated infrastructure
- **Seamless Migration**: Upgrade from shared to dedicated as needed

## 🚀 Technology Stack

- **Frontend**: React 18 with modern hooks and routing
- **Backend**: FastAPI with async/await and automatic API documentation
- **Database**: Google Firestore for scalable, real-time data storage
- **Hosting**: Google Cloud Run for serverless, auto-scaling deployment
- **Authentication**: HTTP Basic Auth with Cloud Run environment variables

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

### **Admin Management API (Protected by Basic Auth)**

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

## 🔐 Authentication & Security

### **Production Authentication**
- **HTTP Basic Auth**: Protects entire admin interface and API endpoints
- **Cloud Run Environment Variables**: Secure credential management
- **Session-based**: Browser login with username/password

### **Admin Access**
- **Username**: Set via `ADMIN_USERNAME` environment variable (default: `admin`)
- **Password**: Set via `ADMIN_PASSWORD` environment variable
- **Access Control**: Single admin user with full system access

### **Security Features**
- **Domain Authorization**: Only authorized domains can collect tracking data
- **IP Hashing**: Client-specific salts for GDPR/HIPAA compliance
- **Audit Trail**: All configuration changes logged with timestamps
- **Service Health**: Health endpoint accessible for Cloud Run monitoring

## 🌐 Production Deployment

### **Quick Deploy to Google Cloud Run**

```bash
# 1. Clone and navigate to repository
git clone <repository-url>
cd pixel-management

# 2. Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. Deploy to Cloud Run
./deploy-production.sh

# 4. Configure authentication via Cloud Run console
# - Go to Cloud Run console > pixel-management
# - Edit & Deploy New Revision > Variables & Secrets
# - Add: ADMIN_USERNAME=admin, ADMIN_PASSWORD=YourSecurePassword
# - Deploy
```

### **Prerequisites**
- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed locally (for build process)

### **Environment Variables**
Set these in Cloud Run console after deployment:

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Yes | Your Google Cloud project ID |
| `ENVIRONMENT` | Yes | Set to `production` |
| `ADMIN_USERNAME` | Yes | Admin login username |
| `ADMIN_PASSWORD` | Yes | Admin login password (8+ chars) |

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

## 🛠️ Local Development

### **Development Setup**

```bash
# 1. Clone repository
git clone <repository-url>
cd pixel-management

# 2. Set up Google Cloud credentials
# Download service account key as credentials.json
# Place in project root
export GOOGLE_CLOUD_PROJECT=your-project-id

# 3. Start development environment
docker-compose -f docker-compose.local.yml up -d

# 4. Access development interface
# Backend: http://localhost:8000
# Frontend: http://localhost:3000 (if using full webapp)
# API Docs: http://localhost:8000/docs
```

### **Development vs Production**
- **Development**: No authentication required
- **Production**: HTTP Basic Auth enabled automatically
- **Environment Detection**: Based on `ENVIRONMENT=production` variable

## 📈 Usage & Management

### **Client Management Workflow**

1. **Create Client**
   - Set privacy level (Standard/GDPR/HIPAA)
   - Choose deployment type (Shared/Dedicated)
   - Configure billing entity

2. **Add Authorized Domains**
   - Each domain must be explicitly authorized
   - Supports multiple domains per client
   - Primary domain designation

3. **Deploy Tracking**
   - Tracking VMs validate domains in real-time
   - Only authorized domains can collect data
   - Client-specific privacy settings applied

### **Domain Authorization Security**
```bash
# Test domain authorization
curl https://pixel-management-url/api/v1/config/domain/example.com

# Should return client configuration, not 404
```

## 🔍 Monitoring & Operations

### **Health Monitoring**
```bash
# Service health check
curl https://pixel-management-url/health

# Expected response:
# {"status":"healthy","service":"pixel-management","database":"firestore_connected"}
```

### **Performance Metrics**
- **Response Time**: Monitor domain authorization endpoint latency (<100ms target)
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

## 🔒 Security Best Practices

### **Production Security Checklist**
- [x] HTTP Basic Auth enabled for admin interface
- [x] Strong admin password set via Cloud Run console
- [x] Domain authorization prevents unauthorized tracking
- [x] Audit logging for all configuration changes
- [x] Service account with minimal Firestore permissions
- [ ] **TODO**: API key authentication for service-to-service calls
- [ ] **TODO**: Rate limiting for API endpoints
- [ ] **TODO**: CORS restrictions for production domains

### **Security Features**
- **Authentication**: HTTP Basic Auth protects all admin functionality
- **Authorization**: Domain-based access control for tracking
- **Audit Trail**: All configuration changes logged with timestamps
- **Data Protection**: Client-specific privacy settings and IP hashing
- **Service Security**: Health checks exempt from authentication

## 🆘 Troubleshooting

### **Common Issues**

**Login Required on Every Page Load**
- Check that `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set in Cloud Run console
- Verify environment variables after deployment revision
- Clear browser cache/cookies and try incognito mode

**Domain Authorization Failing**
```bash
# Check if domain exists in system
curl -u admin:password https://pixel-management-url/api/v1/config/domain/yourdomain.com

# Should return client config, not 404
```

**Service Won't Start**
```bash
# Check deployment logs
gcloud run services logs read pixel-management --region us-central1 --limit 50

# Common issues: missing environment variables, import errors
```

### **Debug Commands**
```bash
# Test authentication
curl -u admin:password https://pixel-management-url/api/v1/admin/clients

# Check Firestore connectivity
curl -u admin:password https://pixel-management-url/health

# View all configuration changes
curl -u admin:password https://pixel-management-url/api/v1/admin/configuration-changes
```

## 🤝 Contributing

### **Development Standards**
- **Python**: Black formatting, type hints, comprehensive docstrings
- **React**: ESLint configuration, functional components with hooks
- **API Design**: RESTful conventions, proper HTTP status codes
- **Security**: All admin endpoints protected, sensitive data encrypted

### **Deployment Process**
1. Test changes locally with `docker-compose.local.yml`
2. Verify all imports and dependencies
3. Deploy to staging environment for integration testing
4. Production deployment via `./deploy-production.sh`
5. Configure authentication via Cloud Run console

## 📚 Documentation

- [Cloud Run Authentication Setup](documentation/CLOUD_RUN_AUTH_SETUP.md) - Detailed console configuration
- [Backend API Documentation](backend/README.md) - FastAPI implementation details
- [Frontend Documentation](frontend/README.md) - React interface guide

## 🚨 Current Security Status

### **Implemented ✅**
- HTTP Basic Auth for admin interface
- Cloud Run console credential management
- Domain authorization for tracking VMs
- Audit logging for configuration changes

### **TODO 🔧**
- API key authentication for service-to-service communication
- Rate limiting for API endpoints
- CORS restrictions for production
- JWT-based authentication for multiple admin users

---

**Built with ❤️ for centralized configuration management and domain authorization**