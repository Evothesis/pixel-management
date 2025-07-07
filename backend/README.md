# Pixel Management Backend

**FastAPI-based configuration API with Firestore database and HTTP Basic Auth protection**

## 🏗️ Architecture

The backend provides secure client configuration management and domain authorization services for the Evothesis tracking infrastructure.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HTTP Client   │───▶│  FastAPI Backend │───▶│   Firestore DB  │
│  - Admin UI     │    │  - Basic Auth   │    │  - Client data  │
│  - Tracking VMs │    │  - CORS handling│    │  - Domain index │
│  - API calls    │    │  - Input validation│  │  - Audit logs   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔐 Authentication & Security

### **HTTP Basic Authentication**
- **Production Mode**: Automatically enabled when `ENVIRONMENT=production`
- **Development Mode**: Authentication disabled for local development
- **Credential Source**: Cloud Run environment variables
- **Coverage**: All routes except `/health` endpoint

### **Authentication Middleware**
```python
# Automatic environment-based protection
if os.getenv("ENVIRONMENT") == "production":
    auth_middleware = BasicAuthMiddleware()
    app.middleware("http")(auth_middleware)
```

### **Security Features**
- **Secure Credentials**: Uses `secrets.compare_digest()` for timing-safe comparison
- **Temporary Passwords**: Auto-generates secure temporary password if none configured
- **Clear Logging**: Detailed authentication status for debugging
- **Health Check Exception**: `/health` endpoint bypasses auth for Cloud Run

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application with auth
│   ├── auth_middleware.py      # HTTP Basic Auth implementation
│   ├── firestore_client.py     # Firestore connection and utilities
│   ├── schemas.py              # Pydantic models for validation
│   ├── auth.py                 # User context and authorization
│   └── config.py               # Application configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
└── README.md                   # This file
```

## 🚀 Core Components

### **FastAPI Application** (`main.py`)
- **Authentication Integration**: Automatic Basic Auth for production
- **CORS Configuration**: Cross-origin support with security headers
- **Health Monitoring**: System status and Firestore connectivity
- **Error Handling**: Comprehensive exception handling and logging
- **Static File Serving**: React frontend serving for production deployment

### **Authentication Middleware** (`auth_middleware.py`)
- **Environment Detection**: Production vs development mode
- **Credential Management**: Secure password handling from environment
- **Browser Integration**: Proper WWW-Authenticate headers
- **Fallback Security**: Temporary password generation with clear instructions

### **Firestore Integration** (`firestore_client.py`)
- **Connection Management**: Auto-detecting authentication methods
- **Collection References**: Pre-configured collection access
- **Utility Functions**: Client ID generation, IP salt creation
- **Connection Testing**: Health check integration

### **Data Models** (`schemas.py`)
- **Request Validation**: Pydantic models for API endpoints
- **Response Formatting**: Consistent API response structures
- **Data Validation**: Input sanitization and type checking
- **Privacy Compliance**: Built-in validation for privacy levels

## 📡 API Endpoints

### **Critical Configuration Endpoints** (No Auth Required)
```bash
# Domain authorization for tracking VMs
GET /api/v1/config/domain/{domain}
# Returns client configuration for authorized domains

# Client configuration retrieval  
GET /api/v1/config/client/{client_id}
# Returns detailed client configuration
```

### **Admin Management Endpoints** (Basic Auth Required)
```bash
# Client CRUD operations
GET    /api/v1/admin/clients           # List all clients
POST   /api/v1/admin/clients           # Create new client
GET    /api/v1/admin/clients/{id}      # Get client details
PUT    /api/v1/admin/clients/{id}      # Update client configuration

# Domain management
POST   /api/v1/admin/clients/{id}/domains
GET    /api/v1/admin/clients/{id}/domains
DELETE /api/v1/admin/clients/{id}/domains/{domain}
```

### **System Endpoints**
```bash
GET /health                            # System health check (no auth)
GET /debug/static                      # Static file debugging (auth required)
```

## ⚙️ Configuration

### **Environment Variables**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Yes | - | Google Cloud project ID |
| `ENVIRONMENT` | Yes | `development` | Deployment environment |
| `ADMIN_USERNAME` | Production | `admin` | Basic auth username |
| `ADMIN_PASSWORD` | Production | Auto-generated | Basic auth password |
| `PORT` | No | `8080` | Server port (Cloud Run sets this) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

### **Authentication Configuration**
```bash
# Production deployment (via Cloud Run console)
ENVIRONMENT=production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourSecurePassword123

# Development (no auth required)
ENVIRONMENT=development
```

### **Firestore Configuration**
- **Authentication**: Automatic via Google Cloud service account
- **Database**: Auto-created in specified Google Cloud project
- **Collections**: Automatically initialized on startup

## 🛠️ Local Development

### **Setup**
```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Set up Google Cloud credentials
export GOOGLE_CLOUD_PROJECT=your-project-id
# Place service account key as ../credentials.json

# 3. Run development server
export ENVIRONMENT=development
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **Development vs Production**
- **Development**: No authentication, detailed logging, hot reload
- **Production**: Basic Auth enabled, optimized logging, static file serving

### **Testing Authentication**
```bash
# Development (no auth)
curl http://localhost:8000/api/v1/admin/clients

# Production (with auth)
curl -u admin:password https://production-url/api/v1/admin/clients
```

## 🚀 Production Deployment

### **Cloud Run Deployment**
The backend is designed for serverless deployment on Google Cloud Run:

```bash
# Deploy with authentication setup
./deploy-production.sh

# Then configure via Cloud Run console:
# ADMIN_USERNAME=admin
# ADMIN_PASSWORD=YourSecurePassword
```

### **Container Configuration**
- **Base Image**: `python:3.11-slim`
- **Port**: 8080 (Cloud Run standard)
- **Health Check**: `/health` endpoint
- **Static Files**: React frontend served from `/app/static`

### **Scaling Configuration**
- **Memory**: 512Mi (configurable)
- **CPU**: 1 vCPU (configurable)
- **Concurrency**: 80 requests per instance
- **Auto-scaling**: 0-10 instances based on traffic

## 🔍 Monitoring & Debugging

### **Health Monitoring**
```bash
# Check service health
curl https://your-service-url/health

# Expected response:
{
  "status": "healthy",
  "service": "pixel-management",
  "database": "firestore_connected",
  "timestamp": "2025-01-07T12:00:00.000Z"
}
```

### **Authentication Debugging**
```bash
# Check auth status in logs
gcloud run services logs read pixel-management --region us-central1

# Look for these messages:
# "✅ Basic auth configured for user: admin"
# "🔐 Authentication status: username=admin, password_set=True"
```

### **Common Issues**

**Authentication Not Working**
- Verify `ENVIRONMENT=production` is set
- Check `ADMIN_USERNAME` and `ADMIN_PASSWORD` in Cloud Run console
- Redeploy revision after setting environment variables

**Firestore Connection Issues**
- Verify `GOOGLE_CLOUD_PROJECT` is correct
- Check service account permissions for Firestore
- Enable Firestore API in Google Cloud console

**Import Errors on Startup**
- Check all required dependencies in `requirements.txt`
- Verify file structure matches import statements
- Review deployment logs for specific missing modules

## 📊 Performance Considerations

### **Response Time Targets**
- **Domain Authorization**: <100ms (critical for tracking performance)
- **Admin Operations**: <500ms
- **Health Checks**: <50ms

### **Optimization Features**
- **Async Operations**: All I/O operations use async/await
- **Connection Pooling**: Firestore client reuse
- **Efficient Queries**: O(1) domain lookups via index
- **Minimal Dependencies**: Only essential packages included

### **Scaling Guidelines**
- **Single Instance**: Handles 80 concurrent requests
- **Memory Usage**: ~200MB baseline, ~512MB under load
- **CPU Usage**: Low except during bulk operations
- **Database**: Firestore auto-scales transparently

## 🔒 Security Implementation

### **Input Validation**
- **Pydantic Models**: All API inputs validated with type checking
- **Domain Validation**: Domain names sanitized and normalized
- **SQL Injection Prevention**: Firestore queries are parameterized
- **XSS Protection**: All outputs properly escaped

### **Authentication Security**
- **Timing-Safe Comparison**: Uses `secrets.compare_digest()`
- **Secure Headers**: Proper WWW-Authenticate implementation
- **Password Requirements**: Minimum 8 characters enforced
- **No Password Logging**: Credentials never appear in logs

### **Data Protection**
- **Audit Logging**: All configuration changes tracked
- **Privacy Compliance**: Client-specific privacy level enforcement
- **Access Control**: Domain authorization prevents unauthorized access
- **Secure Defaults**: Conservative security settings by default

## 🧪 Testing

### **Manual Testing**
```bash
# Test authentication
curl -u admin:password https://your-url/api/v1/admin/clients

# Test domain authorization
curl https://your-url/api/v1/config/domain/example.com

# Test health endpoint
curl https://your-url/health
```

### **Load Testing**
```bash
# Basic load test
ab -n 100 -c 10 -A admin:password https://your-url/api/v1/admin/clients
```

## 🚨 Security Status

### **Current Security Features ✅**
- HTTP Basic Authentication for admin endpoints
- Environment-based authentication control
- Secure credential comparison
- Health endpoint security exemption
- Comprehensive audit logging

### **TODO Security Enhancements 🔧**
- API key authentication for service-to-service calls
- Rate limiting per IP/client
- CORS restrictions for production domains
- JWT-based authentication for multiple users
- Request signing for critical endpoints

---

**Built with ❤️ for secure configuration management and domain authorization**