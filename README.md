# Evothesis Pixel Management

**Centralized client configuration and domain authorization system for secure analytics infrastructure**

🌐 **Production**: https://pixel-management-275731808857.us-central1.run.app

## 🏗️ System Architecture

Multi-service analytics platform providing centralized configuration management, domain authorization, and privacy-compliant data collection.

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ Pixel Management    │───▶│   Tracking VMs      │───▶│  Client Websites    │
│ - Config management │    │ - Domain validation │    │ - Authorized domains│
│ - Domain auth API   │    │ - Privacy compliance│    │ - Dynamic pixels    │
│ - Admin interface   │    │ - Real-time config  │    │ - Event collection  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
          │                                                        │
          ▼                                                        ▼
    ┌─────────────────┐                               ┌─────────────────────┐
    │  Firestore DB   │                               │  Collection API     │
    │ - Client configs│◀──────────────────────────────│ - Event processing  │
    │ - Domain index  │                               │ - PostgreSQL/S3     │
    │ - Audit logs    │                               │ - Export pipeline   │
    └─────────────────┘                               └─────────────────────┘
```

## 🎯 Core Features

**🔒 Domain Authorization Engine**
- Sub-100ms domain validation for tracking VMs
- O(1) lookup performance via optimized Firestore index
- Prevents unauthorized data collection

**🛡️ Privacy Compliance Management**
- **Standard**: Full tracking capabilities  
- **GDPR**: IP hashing, consent requirements, PII redaction
- **HIPAA**: Enhanced security, audit logging, dedicated infrastructure

**👥 Multi-Tenant Client Management**
- Agency/enterprise model with owner-based billing
- Flexible deployment: shared infrastructure or dedicated VMs
- Real-time configuration updates across all tracking endpoints

## 📁 Repository Structure

```
pixel-management/
├── backend/           # FastAPI configuration API
│   ├── app/           # Core application logic
│   │   ├── main.py    # API endpoints and auth
│   │   ├── auth.py    # Admin authentication
│   │   ├── schemas.py # Data validation models
│   │   └── firestore_client.py # Database integration
│   └── Dockerfile     # Container configuration
├── frontend/          # React admin interface  
│   ├── src/pages/     # Dashboard, client management
│   ├── package.json   # Dependencies and scripts
│   └── Dockerfile     # Development container
├── api/               # Event collection service
│   ├── app/           # FastAPI data collection API
│   └── requirements.txt # Python dependencies
├── deploy-pixel-management.sh # Production deployment
└── Dockerfile         # Multi-stage production build
```

## 🚀 Quick Start

### Production Deployment
```bash
# 1. Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Deploy to Cloud Run
./deploy-pixel-management.sh

# 3. Configure authentication in Cloud Run console
# Set: ADMIN_USERNAME=admin, ADMIN_PASSWORD=secure_password
```

### Local Development
```bash
# 1. Clone and setup
git clone <repository>
cd pixel-management

# 2. Start development environment
docker-compose -f docker-compose.local.yml up -d

# 3. Access services
# Admin UI: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Collection API: http://localhost:8001
```

## 🔧 Configuration Management

**Client Creation Workflow:**
1. Create client with privacy level (Standard/GDPR/HIPAA)
2. Configure deployment type (Shared/Dedicated)  
3. Add authorized domains for tracking
4. Deploy tracking pixels to websites

**Domain Authorization:**
- All domains must be explicitly authorized
- Real-time validation prevents unauthorized collection
- Primary domain designation for client identification

## 🔐 Security & Compliance

**Authentication:**
- Production: HTTP Basic Auth via Cloud Run environment variables
- Development: No authentication for local development
- API Key authentication for service-to-service communication

**Privacy Compliance:**
- **GDPR**: Automatic IP hashing, consent management, data subject rights
- **HIPAA**: Enhanced audit logging, encryption, dedicated infrastructure
- **SOC 2**: Comprehensive audit trails and access controls

## 🎛️ API Reference

### Configuration Endpoints (No Auth)
```bash
# Domain authorization for tracking VMs
GET /api/v1/config/domain/{domain}

# Client configuration retrieval
GET /api/v1/config/client/{client_id}
```

### Admin Management (Auth Required)
```bash
# Client management
GET    /api/v1/admin/clients
POST   /api/v1/admin/clients
PUT    /api/v1/admin/clients/{client_id}

# Domain management  
POST   /api/v1/admin/clients/{client_id}/domains
DELETE /api/v1/admin/clients/{client_id}/domains/{domain}
```

## 📊 Database Schema

**Firestore Collections:**
- `clients`: Client configurations and privacy settings
- `domain_index`: O(1) domain → client_id lookup table  
- `domains`: Detailed domain metadata
- `configuration_changes`: Complete audit trail

## 🛠️ Development

**Requirements:**
- Python 3.11+ (Backend)
- Node.js 18+ (Frontend)
- Docker & Docker Compose
- Google Cloud SDK

**Code Standards:**
- Python: Black formatting, type hints, comprehensive tests
- React: ESLint, functional components, responsive design
- API: RESTful conventions, proper HTTP status codes

## 🔍 Monitoring & Operations

**Health Checks:**
```bash
# System health
curl https://pixel-management-url/health

# Authentication test  
curl -u admin:password https://pixel-management-url/api/v1/admin/clients
```

**Troubleshooting:**
- Deployment logs: `gcloud run services logs read pixel-management`
- Domain authorization: Check domain exists in `domain_index` collection
- Authentication: Verify environment variables in Cloud Run console

## 📚 Documentation

- [Backend API](backend/README.md) - FastAPI implementation details
- [Frontend Interface](frontend/README.md) - React admin interface  
- [Collection API](api/README.md) - Event processing service

---

**Built for enterprise-grade analytics infrastructure with privacy compliance and domain security**