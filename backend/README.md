# Pixel Management Backend

**FastAPI-based configuration API with Firestore database and secure admin authentication**

## 🏗️ Architecture

Provides secure client configuration management and real-time domain authorization for the Evothesis tracking infrastructure.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin UI      │───▶│  FastAPI API    │───▶│   Firestore DB  │
│ - React frontend│    │ - Authentication│    │ - Client configs│
│ - Form validation│    │ - CORS handling │    │ - Domain index  │
│ - Domain mgmt   │    │ - Input validation│   │ - Audit trails │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Tracking VMs   │
                    │ - Config lookup │
                    │ - Domain auth   │
                    │ - Privacy rules │
                    └─────────────────┘
```

## 🔐 Authentication System

**Environment-Based Security:**
- **Production**: HTTP Basic Auth automatically enabled when `ENVIRONMENT=production`
- **Development**: Authentication disabled for local development
- **API Keys**: Secure admin API key system for service-to-service communication

**Security Features:**
- Timing-safe password comparison using `secrets.compare_digest()`
- Automatic secure API key generation if not configured
- Health check endpoint exemption for Cloud Run monitoring
- Comprehensive audit logging for all admin operations

## 📁 Core Components

```
backend/
├── app/
│   ├── main.py              # FastAPI app with auth middleware
│   ├── auth.py              # Admin API key authentication  
│   ├── firestore_client.py  # Database connection & utilities
│   ├── schemas.py           # Pydantic validation models
│   └── models.py            # Data structure definitions
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── README.md               # This documentation
```

## 🚀 Key Features

**Client Configuration Management:**
- Complete CRUD operations for client records
- Privacy level enforcement (Standard/GDPR/HIPAA)
- Deployment type configuration (Shared/Dedicated)
- Real-time configuration updates

**Domain Authorization Engine:**
- O(1) domain lookup performance via optimized Firestore index
- Sub-100ms response times for tracking VM authorization
- Comprehensive domain metadata management
- Primary domain designation

**Rate Limiting & Performance:**
- Sophisticated in-memory rate limiting system
- Different limits for admin vs config vs pixel endpoints
- IP-based tracking with automatic cleanup
- Sub-100ms response times for critical endpoints

**Dynamic Pixel Serving:**
- Template-based JavaScript tracking pixel generation
- Client-specific configuration injection
- Domain authorization validation before serving
- Privacy compliance built into generated code

**Audit & Compliance:**
- Complete configuration change audit trail
- Admin action logging with timestamps and user identification
- Privacy compliance validation and enforcement
- GDPR/HIPAA data handling requirements

## 📡 API Endpoints

### Configuration API (No Authentication)
**Critical for tracking VM performance - must be sub-100ms**

```bash
# Domain authorization lookup
GET /api/v1/config/domain/{domain}
# Returns: client_id, privacy_level, ip_collection settings

# Client configuration retrieval
GET /api/v1/config/client/{client_id}  
# Returns: complete client configuration for tracking
```

### Admin API (Authentication Required)
**Secured with API key authentication**

```bash
# Client management
GET    /api/v1/admin/clients              # List all clients
POST   /api/v1/admin/clients              # Create new client
GET    /api/v1/admin/clients/{client_id}  # Get client details
PUT    /api/v1/admin/clients/{client_id}  # Update client config

# Domain management
POST   /api/v1/admin/clients/{client_id}/domains     # Add domain
GET    /api/v1/admin/clients/{client_id}/domains     # List domains  
DELETE /api/v1/admin/clients/{client_id}/domains/{domain} # Remove domain

# System management
GET    /health                            # Health check (no auth)
GET    /api/v1/admin/configuration-changes # Audit trail

# Pixel serving
GET    /pixel/{client_id}/tracking.js     # Dynamic tracking pixel
```

## 🗄️ Data Models

**Client Configuration:**
```python
class ClientCreate(BaseModel):
    name: str
    owner: str                    # Who controls this client
    billing_entity: str           # Who pays for usage
    privacy_level: str            # "standard", "gdpr", "hipaa"
    deployment_type: str          # "shared", "dedicated"
    features: Dict[str, Any]      # Custom feature flags
```

**Domain Management:**
```python  
class DomainCreate(BaseModel):
    domain: str                   # Validated domain name
    is_primary: bool = False      # Primary domain flag
```

**Configuration Response:**
```python
class ClientConfigResponse(BaseModel):
    client_id: str
    privacy_level: str
    ip_collection: Dict[str, Any] # IP handling rules
    consent: Dict[str, Any]       # Consent requirements
    features: Dict[str, Any]      # Feature configuration
```

## 🔧 Local Development

**Setup:**
```bash
# 1. Clone repository
git clone <repository>
cd pixel-management/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export ENVIRONMENT=development  # Disables auth

# 4. Run development server
uvicorn app.main:app --reload --port 8000
```

**Development Features:**
- Auto-reload on code changes
- Interactive API documentation at `/docs`
- No authentication required
- Detailed logging for debugging

## 🚀 Production Deployment

**Cloud Run Deployment:**
```bash
# Deploy via root deployment script
cd pixel-management/
./deploy-pixel-management.sh
```

**Required Environment Variables:**
```bash
ENVIRONMENT=production          # Enables authentication
GOOGLE_CLOUD_PROJECT=project-id # Firestore project
ADMIN_API_KEY=secure-key       # Admin authentication
```

**Production Configuration:**
- Automatic HTTPS via Cloud Run
- Firestore authentication via service account
- Health checks for auto-scaling
- CORS configuration for frontend integration

## 🔍 Monitoring & Debugging

**Health Check:**
```bash
# Basic connectivity test
curl https://your-service-url/health

# Expected response:
{
  "status": "healthy",
  "service": "pixel-management", 
  "database": "firestore_connected",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Admin Authentication Test:**
```bash
# Test API key authentication
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-service-url/api/v1/admin/clients
```

**Common Issues:**
- **500 errors**: Check Firestore permissions and project ID
- **401 errors**: Verify ADMIN_API_KEY environment variable
- **403 errors**: Check admin API key in Authorization header
- **Import errors**: Verify all dependencies in requirements.txt

## 📊 Performance Targets

**Response Time SLAs:**
- Domain authorization: <100ms (critical for tracking performance)
- Admin operations: <500ms
- Health checks: <50ms
- Bulk operations: <2000ms

**Scaling Characteristics:**
- Memory usage: ~200MB baseline, ~512MB under load
- CPU usage: Low except during bulk configuration updates
- Database: Firestore auto-scales transparently
- Concurrent requests: 80+ per instance

## 🛡️ Security Implementation

**Authentication Flow:**
1. Admin UI sends API key in Authorization header
2. `verify_admin_access()` validates key securely
3. All admin actions logged with user identification
4. Configuration endpoints remain public for tracking VMs

**Data Protection:**
- All admin actions audited in `configuration_changes` collection
- IP salts generated for GDPR/HIPAA clients
- Secure credential handling with proper environment variable usage
- Input validation via Pydantic models prevents injection attacks

**Access Control:**
- Admin endpoints protected with API key authentication
- Configuration endpoints public but read-only
- Health endpoint public for Cloud Run monitoring
- Audit trail immutable for compliance requirements

---

**Production-ready FastAPI service powering centralized analytics configuration**