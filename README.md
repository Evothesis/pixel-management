# Evothesis Pixel Management

Centralized configuration management system for all Evothesis tracking infrastructure. This service provides domain authorization, client configuration, and privacy compliance management for the entire Evothesis analytics platform.

## 🏗️ Architecture Overview

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  Config Mgmt VM     │───▶│   Shared Infra VM   │───▶│  Client Websites    │
│  - Web Admin UI     │    │  - Multi-tenant     │    │  - Multiple clients │
│  - Client CRUD API  │    │  - Config caching   │    │  - Dynamic pixels   │
│  - Privacy configs  │    │  - Pixel generation │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
          │                                                        │
          └────────────────────┐    ┌─────────────────────────────┘
                               ▼    ▼
                    ┌─────────────────────┐    ┌─────────────────────┐
                    │ Dedicated Client VM │    │ Dedicated Client VM │
                    │ - Single client     │    │ - Single client     │
                    │ - Config caching    │    │ - Config caching    │
                    │ - Pixel generation  │    │ - Pixel generation  │
                    └─────────────────────┘    └─────────────────────┘
```

## 🎯 Key Features

### **Domain Authorization System**
- **Critical Security Feature**: Only authorized domains can collect tracking data
- Prevents unauthorized data collection and ensures compliance
- Real-time domain validation for all tracking requests

### **Privacy Compliance Management**
- **Standard Level**: Full IP collection and basic tracking
- **GDPR Compliance**: IP hashing, consent requirements, automatic PII redaction
- **HIPAA Compliance**: Enhanced security, audit logging, BAA support

### **Multi-Tenant Infrastructure Support**
- **Shared Infrastructure**: Multiple clients on cost-effective shared VMs
- **Dedicated VMs**: High-traffic clients with isolated infrastructure
- **Seamless Migration**: Clients can upgrade from shared to dedicated

### **Centralized Configuration**
- Single source of truth for all client configurations
- Real-time updates without VM redeployment
- Complete audit trail of configuration changes

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (Mac/Windows) or Docker Engine + Docker Compose (Linux)
- 4GB+ RAM recommended
- Ports 80, 3000, 5432, 8000 available

### Installation

1. **Clone and setup the repository:**
   ```bash
   git clone <repository-url>
   cd pixel-management
   chmod +x setup_script.sh
   ./setup_script.sh
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Verify installation:**
   ```bash
   # Check all services are running
   docker-compose ps
   
   # Check API health
   curl http://localhost:8000/health
   ```

4. **Access the admin interface:**
   - **Web Interface**: http://localhost
   - **API Documentation**: http://localhost:8000/docs
   - **Default Credentials**: admin / pixel_admin_2025

## 📡 API Endpoints

### Configuration API (For Tracking VMs)

```bash
# Get client configuration by client ID
GET /api/v1/config/client/{client_id}

# Get configuration by domain (critical for authorization)
GET /api/v1/config/domain/{domain}
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
  "features": {
    "scroll_tracking": true,
    "form_tracking": true,
    "copy_tracking": false
  },
  "deployment": {
    "type": "shared",
    "hostname": null
  }
}
```

### Admin Management API

```bash
# Client management
GET    /api/v1/admin/clients           # List all clients
POST   /api/v1/admin/clients           # Create new client
GET    /api/v1/admin/clients/{id}      # Get client details
PUT    /api/v1/admin/clients/{id}      # Update client

# Domain management
POST   /api/v1/admin/clients/{id}/domains  # Add domain to client
GET    /api/v1/admin/clients/{id}/domains  # List client domains
```

## 🔧 Client Configuration

### Creating a New Client

1. **Via Web Interface:**
   - Navigate to http://localhost
   - Click "Add New Client"
   - Configure privacy level and features
   - Add authorized domains

2. **Via API:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/clients \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Example Corp",
       "email": "admin@example.com",
       "privacy_level": "gdpr",
       "deployment_type": "shared"
     }'
   ```

### Adding Authorized Domains

```bash
# Add domain to client (REQUIRED for tracking)
curl -X POST http://localhost:8000/api/v1/admin/clients/client_abc123/domains \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "is_primary": true
  }'
```

## 🔒 Privacy Compliance Levels

### Standard Level
- Full IP address collection
- Basic event tracking
- Minimal privacy restrictions
- **Use Case**: Internal tools, non-EU traffic

### GDPR Compliance
- **IP Hashing**: Automatic SHA-256 hashing with client-specific salt
- **Consent Required**: Tracking blocked until explicit consent
- **PII Redaction**: Automatic filtering of sensitive form fields
- **Do Not Track**: Respects browser DNT preferences
- **Use Case**: EU visitors, privacy-conscious clients

### HIPAA Compliance
- **Enhanced Security**: All GDPR features plus additional protections
- **Audit Logging**: Complete tracking of all data access
- **BAA Support**: Business Associate Agreement coverage
- **Data Encryption**: Enhanced encryption at rest and in transit
- **Use Case**: Healthcare organizations, PHI handling

## 🚨 Domain Authorization (Critical Security)

**Every domain must be explicitly authorized before tracking can begin.**

### How It Works

1. **Tracking VM receives event** from `example.com`
2. **VM queries pixel management**: `GET /api/v1/config/domain/example.com`
3. **If domain not found**: HTTP 404 → Reject tracking data
4. **If domain authorized**: Return client config → Process tracking data

### Integration Example

```python
# In your tracking infrastructure
def validate_domain_and_get_config(domain: str):
    try:
        response = requests.get(f"{PIXEL_MGMT_URL}/api/v1/config/domain/{domain}")
        if response.status_code == 404:
            # Domain not authorized - reject all tracking
            raise UnauthorizedDomainError(f"Domain {domain} not authorized")
        return response.json()
    except Exception:
        # Fail secure - reject tracking if config service unavailable
        raise ConfigServiceError("Cannot validate domain authorization")
```

## ⚙️ Environment Configuration

### Docker Compose Variables

```bash
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/pixel_management

# Admin authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me_in_production

# Security
SECRET_KEY=your-secret-key-change-in-production

# Development vs Production
NODE_ENV=development
REACT_APP_API_URL=http://localhost:8000
```

### Production Deployment

1. **Update security settings:**
   ```bash
   # Generate secure credentials
   export ADMIN_PASSWORD=$(openssl rand -base64 32)
   export SECRET_KEY=$(openssl rand -base64 32)
   ```

2. **Configure CORS for production:**
   ```python
   # In backend/app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://pixel-mgmt.yourdomain.com"],  # Restrict to your domain
       allow_credentials=True,
       allow_methods=["GET", "POST", "PUT", "DELETE"],
       allow_headers=["Content-Type", "Authorization"],
   )
   ```

3. **Set up SSL/TLS:**
   - Configure nginx with SSL certificates
   - Update API URLs to use HTTPS
   - Enable secure cookie settings

## 📊 Monitoring & Operations

### Health Checks

```bash
# Service health
curl http://localhost:8000/health

# Database connectivity
docker-compose exec backend python -c "from app.database import test_database_connection; print(test_database_connection())"

# Container status
docker-compose ps
```

### Logs and Debugging

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Database operations
docker-compose exec postgres psql -U postgres -d pixel_management -c "SELECT count(*) FROM clients;"
```

### Performance Monitoring

```bash
# Check resource usage
docker stats

# Monitor database performance
docker-compose exec postgres psql -U postgres -d pixel_management -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_live_tup as live_rows
FROM pg_stat_user_tables;
"
```

## 🔧 Integration with Tracking Infrastructure

### Tracking VM Configuration

```python
# Example integration in your tracking infrastructure
class PixelConfigClient:
    def __init__(self, config_service_url: str):
        self.config_service_url = config_service_url
        self.cache = {}  # Local config cache
        self.cache_ttl = 300  # 5 minutes
    
    async def get_client_config(self, domain: str) -> dict:
        """Get client configuration with caching"""
        if domain in self.cache:
            config, timestamp = self.cache[domain]
            if time.time() - timestamp < self.cache_ttl:
                return config
        
        # Fetch from config service
        response = await httpx.get(f"{self.config_service_url}/api/v1/config/domain/{domain}")
        
        if response.status_code == 404:
            raise UnauthorizedDomainError(f"Domain {domain} not authorized for tracking")
        
        config = response.json()
        self.cache[domain] = (config, time.time())
        return config
    
    def generate_tracking_pixel(self, domain: str) -> str:
        """Generate domain-specific tracking pixel JavaScript"""
        config = await self.get_client_config(domain)
        
        # Apply privacy settings based on config
        if config["privacy_level"] in ["gdpr", "hipaa"]:
            # Generate privacy-compliant pixel
            return self.generate_privacy_pixel(config)
        else:
            # Generate standard pixel
            return self.generate_standard_pixel(config)
```

### Pixel Generation Example

```javascript
// Example generated pixel with privacy settings
(function() {
    // Configuration injected from pixel management service
    const config = {
        clientId: "client_abc123",
        privacyLevel: "gdpr",
        ipHashing: {
            enabled: true,
            salt: "client-specific-salt"
        },
        consentRequired: true
    };
    
    // Privacy-compliant tracking logic
    if (config.consentRequired && !hasUserConsent()) {
        console.log('[Tracking] Consent required - tracking blocked');
        return;
    }
    
    // Hash IP if required
    if (config.ipHashing.enabled) {
        const hashedIP = await hashIP(getClientIP(), config.ipHashing.salt);
        // Use hashed IP for tracking
    }
    
    // Continue with tracking...
})();
```

## 🛠️ Development

### Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd pixel-management

# Create development environment
./setup_script.sh

# Start development services with hot reload
docker-compose up
```

### Making Changes

```bash
# Backend changes (hot reload enabled)
# Edit files in backend/app/ - changes auto-reload

# Frontend changes (hot reload enabled)  
# Edit files in frontend/src/ - browser auto-refreshes

# Database schema changes
# Edit database/init.sql and restart postgres service
docker-compose restart postgres
```

### Testing

```bash
# Test API endpoints
curl http://localhost:8000/docs

# Test domain authorization
curl http://localhost:8000/api/v1/config/domain/localhost

# Test client creation
curl -X POST http://localhost:8000/api/v1/admin/clients \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Client", "privacy_level": "standard"}'
```

## 🚨 Troubleshooting

### Common Issues

**Containers won't start:**
```bash
# Check Docker Desktop is running
docker --version

# Check port availability
lsof -i :80 -i :3000 -i :5432 -i :8000

# Rebuild containers
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Database connection errors:**
```bash
# Check PostgreSQL is healthy
docker-compose exec postgres pg_isready -U postgres

# Reset database
docker-compose down -v
docker-compose up postgres -d
# Wait for health check, then start other services
```

**Frontend build failures:**
```bash
# Ensure package.json exists
ls -la frontend/package.json

# Rebuild frontend only
docker-compose build --no-cache frontend
```

**API returns 404 for authorized domains:**
```bash
# Check domain is properly added
curl http://localhost:8000/api/v1/admin/clients/{client_id}/domains

# Check client exists and is active
curl http://localhost:8000/api/v1/admin/clients
```

### Development Tips

1. **Use the web interface** for initial setup - it's easier than API calls
2. **Always add domains** before testing tracking - authorization is required
3. **Check logs frequently** during development: `docker-compose logs -f`
4. **Reset database** if you need fresh start: `docker-compose down -v`

## 🔐 Security Considerations

### Production Security Checklist

- [ ] Change default admin credentials
- [ ] Set strong SECRET_KEY for JWT tokens
- [ ] Configure proper CORS origins
- [ ] Enable SSL/TLS certificates
- [ ] Set up firewall rules for VM access
- [ ] Regular security updates for dependencies
- [ ] Backup database regularly
- [ ] Monitor access logs for suspicious activity

### Privacy Compliance

- [ ] Document data handling procedures
- [ ] Implement user consent management
- [ ] Set up data retention policies
- [ ] Train staff on privacy requirements
- [ ] Regular compliance audits
- [ ] Incident response procedures

## 📚 Additional Resources

- **Main Evothesis Platform**: [server-infrastructure repository]
- **API Documentation**: http://localhost:8000/docs
- **React Documentation**: https://reactjs.org/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **PostgreSQL Documentation**: https://www.postgresql.org/docs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

### Code Standards
- **Python**: Black formatting, type hints, comprehensive docstrings
- **React**: ESLint configuration, functional components with hooks
- **SQL**: Consistent naming, proper indexing, foreign key constraints
- **Documentation**: Update README for any API or configuration changes

## 📄 License

[MIT License](LICENSE) - See LICENSE file for details

---

**Built with ❤️ for secure, privacy-compliant analytics infrastructure**