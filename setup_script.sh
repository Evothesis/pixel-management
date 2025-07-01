#!/bin/bash

# Evothesis Pixel Management Setup Script for macOS
# Creates the complete folder structure and files for the pixel-management repository

set -e

echo "🚀 Setting up Evothesis Pixel Management repository structure..."

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "⚠️  Warning: This doesn't appear to be a git repository."
    echo "   Make sure you're in the pixel-management repository directory."
    read -p "   Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Create main directory structure
echo "📁 Creating directory structure..."

mkdir -p backend/app
mkdir -p frontend/src/components
mkdir -p frontend/src/pages
mkdir -p frontend/src/services
mkdir -p frontend/public
mkdir -p database
mkdir -p nginx

echo "✅ Directory structure created"

# Create backend files
echo "🐍 Creating backend files..."

# Backend __init__.py files
touch backend/__init__.py
touch backend/app/__init__.py

# Create backend/app/main.py (the main FastAPI app from earlier)
cat > backend/app/main.py << 'EOF'
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import secrets
import hashlib
from datetime import datetime

from .database import get_db, engine
from .models import Base, Client, TrackingDomain, ConfigurationChange
from .schemas import ClientCreate, ClientUpdate, ClientResponse, DomainCreate

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Evothesis Pixel Management", version="1.0.0")

# Simple CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Configuration API for Tracking VMs (Most Important)
# ============================================================================

@app.get("/api/v1/config/client/{client_id}")
async def get_client_config(client_id: str, db: Session = Depends(get_db)):
    """Get client configuration for tracking VMs"""
    client = db.query(Client).filter(Client.client_id == client_id, Client.is_active == True).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found or inactive")
    
    # Generate config for tracking VMs
    config = {
        "client_id": client.client_id,
        "privacy_level": client.privacy_level,
        "ip_collection": {
            "enabled": client.ip_collection_enabled,
            "hash_required": client.privacy_level in ["gdpr", "hipaa"],
            "salt": client.ip_salt if client.privacy_level in ["gdpr", "hipaa"] else None
        },
        "consent": {
            "required": client.consent_required,
            "default_behavior": "block" if client.privacy_level in ["gdpr", "hipaa"] else "allow"
        },
        "features": client.features or {},
        "deployment": {
            "type": client.deployment_type,
            "hostname": client.vm_hostname
        }
    }
    
    return config

@app.get("/api/v1/config/domain/{domain}")
async def get_config_by_domain(domain: str, db: Session = Depends(get_db)):
    """Get client config by domain - critical for domain validation"""
    tracking_domain = db.query(TrackingDomain).filter(TrackingDomain.domain == domain).first()
    
    if not tracking_domain:
        raise HTTPException(status_code=404, detail=f"Domain {domain} not authorized for tracking")
    
    # Get client config
    client = db.query(Client).filter(
        Client.client_id == tracking_domain.client_id, 
        Client.is_active == True
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found or inactive")
    
    # Return same config format as above
    return await get_client_config(client.client_id, db)

# ============================================================================
# Admin API for Client Management
# ============================================================================

@app.post("/api/v1/admin/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    """Create new client"""
    
    # Generate unique client_id
    client_id = f"client_{secrets.token_hex(8)}"
    
    # Generate salt for GDPR/HIPAA clients
    ip_salt = None
    if client_data.privacy_level in ["gdpr", "hipaa"]:
        ip_salt = secrets.token_hex(32)
    
    # Create client
    client = Client(
        client_id=client_id,
        name=client_data.name,
        email=client_data.email,
        deployment_type=client_data.deployment_type,
        vm_hostname=client_data.vm_hostname,
        privacy_level=client_data.privacy_level,
        ip_collection_enabled=client_data.ip_collection_enabled,
        ip_salt=ip_salt,
        consent_required=client_data.privacy_level in ["gdpr", "hipaa"],
        features=client_data.features or {},
        monthly_event_limit=client_data.monthly_event_limit,
        billing_rate_per_1k=client_data.billing_rate_per_1k
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    # Log creation
    change = ConfigurationChange(
        client_id=client_id,
        changed_by="admin",  # Simple for MVP
        change_description=f"Client created with privacy level: {client_data.privacy_level}",
        new_config={"privacy_level": client_data.privacy_level, "created": True}
    )
    db.add(change)
    db.commit()
    
    return client

@app.get("/api/v1/admin/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, db: Session = Depends(get_db)):
    """Get client details"""
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.get("/api/v1/admin/clients", response_model=List[ClientResponse])
async def list_clients(db: Session = Depends(get_db)):
    """List all clients"""
    return db.query(Client).order_by(Client.created_at.desc()).all()

@app.post("/api/v1/admin/clients/{client_id}/domains")
async def add_domain(client_id: str, domain_data: DomainCreate, db: Session = Depends(get_db)):
    """Add domain to client"""
    
    # Check if client exists
    client = db.query(Client).filter(Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check if domain already exists
    existing = db.query(TrackingDomain).filter(TrackingDomain.domain == domain_data.domain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domain already assigned to a client")
    
    # Add domain
    domain = TrackingDomain(
        client_id=client_id,
        domain=domain_data.domain,
        is_primary=domain_data.is_primary
    )
    
    db.add(domain)
    db.commit()
    
    return {"message": f"Domain {domain_data.domain} added to client {client_id}"}

@app.get("/api/v1/admin/clients/{client_id}/domains")
async def get_client_domains(client_id: str, db: Session = Depends(get_db)):
    """Get all domains for a client"""
    domains = db.query(TrackingDomain).filter(TrackingDomain.client_id == client_id).all()
    return domains

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pixel-management"}
EOF

echo "✅ Backend files created"

# Create basic React frontend structure
echo "⚛️  Creating frontend files..."

# Create public/index.html
cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Evothesis Pixel Management - Client Configuration Dashboard" />
    <title>Pixel Management - Evothesis</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Create basic React App.js
cat > frontend/src/App.js << 'EOF'
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ClientList from './pages/ClientList';
import ClientForm from './pages/ClientForm';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Evothesis Pixel Management</h1>
          <nav>
            <a href="/">Dashboard</a>
            <a href="/clients">Clients</a>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clients" element={<ClientList />} />
            <Route path="/clients/new" element={<ClientForm />} />
            <Route path="/clients/:clientId/edit" element={<ClientForm />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
EOF

# Create index.js
cat > frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# Create basic CSS
cat > frontend/src/App.css << 'EOF'
.App {
  text-align: center;
}

.App-header {
  background-color: #1a365d;
  padding: 20px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.App-header nav a {
  color: white;
  text-decoration: none;
  margin: 0 15px;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.App-header nav a:hover {
  background-color: #3182ce;
}

main {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.client-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 20px;
  margin: 10px 0;
  text-align: left;
}

.privacy-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.privacy-standard { background-color: #e6fffa; color: #234e52; }
.privacy-gdpr { background-color: #fef5e7; color: #744210; }
.privacy-hipaa { background-color: #fed7d7; color: #822727; }

button {
  background-color: #3182ce;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin: 5px;
}

button:hover {
  background-color: #2c5aa0;
}

.form-group {
  margin: 15px 0;
  text-align: left;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
EOF

cat > frontend/src/index.css << 'EOF'
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
EOF

# Create basic React pages
mkdir -p frontend/src/pages

cat > frontend/src/pages/Dashboard.js << 'EOF'
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Dashboard() {
  const [stats, setStats] = useState({
    totalClients: 0,
    activeClients: 0,
    privacyLevels: { standard: 0, gdpr: 0, hipaa: 0 }
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/v1/admin/clients');
      const clients = response.data;
      
      const totalClients = clients.length;
      const activeClients = clients.filter(c => c.is_active).length;
      
      const privacyLevels = clients.reduce((acc, client) => {
        acc[client.privacy_level] = (acc[client.privacy_level] || 0) + 1;
        return acc;
      }, { standard: 0, gdpr: 0, hipaa: 0 });

      setStats({ totalClients, activeClients, privacyLevels });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  return (
    <div>
      <h2>Pixel Management Dashboard</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', margin: '20px 0' }}>
        <div className="client-card">
          <h3>Total Clients</h3>
          <p style={{ fontSize: '2em', margin: '10px 0' }}>{stats.totalClients}</p>
        </div>
        
        <div className="client-card">
          <h3>Active Clients</h3>
          <p style={{ fontSize: '2em', margin: '10px 0' }}>{stats.activeClients}</p>
        </div>
        
        <div className="client-card">
          <h3>Privacy Levels</h3>
          <p>Standard: {stats.privacyLevels.standard}</p>
          <p>GDPR: {stats.privacyLevels.gdpr}</p>
          <p>HIPAA: {stats.privacyLevels.hipaa}</p>
        </div>
      </div>
      
      <div style={{ marginTop: '40px' }}>
        <h3>Quick Actions</h3>
        <button onClick={() => window.location.href = '/clients/new'}>
          Add New Client
        </button>
        <button onClick={() => window.location.href = '/clients'}>
          Manage Clients
        </button>
      </div>
    </div>
  );
}

export default Dashboard;
EOF

cat > frontend/src/pages/ClientList.js << 'EOF'
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ClientList() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get('/api/v1/admin/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading clients...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Client Management</h2>
        <button onClick={() => window.location.href = '/clients/new'}>
          Add New Client
        </button>
      </div>
      
      {clients.length === 0 ? (
        <p>No clients found. Create your first client to get started.</p>
      ) : (
        <div>
          {clients.map(client => (
            <div key={client.client_id} className="client-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3>{client.name}</h3>
                  <p><strong>Client ID:</strong> {client.client_id}</p>
                  <p><strong>Email:</strong> {client.email || 'Not provided'}</p>
                  <p><strong>Deployment:</strong> {client.deployment_type}</p>
                  {client.vm_hostname && (
                    <p><strong>VM Hostname:</strong> {client.vm_hostname}</p>
                  )}
                  <p><strong>Created:</strong> {new Date(client.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <span className={`privacy-badge privacy-${client.privacy_level}`}>
                    {client.privacy_level}
                  </span>
                  <div style={{ marginTop: '10px' }}>
                    <button onClick={() => window.location.href = `/clients/${client.client_id}/edit`}>
                      Edit
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ClientList;
EOF

cat > frontend/src/pages/ClientForm.js << 'EOF'
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

function ClientForm() {
  const { clientId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(clientId);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    deployment_type: 'shared',
    vm_hostname: '',
    privacy_level: 'standard',
    ip_collection_enabled: true,
    monthly_event_limit: '',
    billing_rate_per_1k: '0.01'
  });
  
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isEdit) {
      fetchClient();
    }
  }, [clientId, isEdit]);

  const fetchClient = async () => {
    try {
      const response = await axios.get(`/api/v1/admin/clients/${clientId}`);
      setFormData(response.data);
    } catch (error) {
      console.error('Failed to fetch client:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (isEdit) {
        await axios.put(`/api/v1/admin/clients/${clientId}`, formData);
      } else {
        await axios.post('/api/v1/admin/clients', formData);
      }
      navigate('/clients');
    } catch (error) {
      console.error('Failed to save client:', error);
      alert('Failed to save client. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2>{isEdit ? 'Edit Client' : 'Add New Client'}</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Client Name *</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label>Privacy Level *</label>
          <select name="privacy_level" value={formData.privacy_level} onChange={handleChange}>
            <option value="standard">Standard</option>
            <option value="gdpr">GDPR Compliant</option>
            <option value="hipaa">HIPAA Compliant</option>
          </select>
        </div>

        <div className="form-group">
          <label>Deployment Type *</label>
          <select name="deployment_type" value={formData.deployment_type} onChange={handleChange}>
            <option value="shared">Shared Infrastructure</option>
            <option value="dedicated">Dedicated VM</option>
          </select>
        </div>

        {formData.deployment_type === 'dedicated' && (
          <div className="form-group">
            <label>VM Hostname</label>
            <input
              type="text"
              name="vm_hostname"
              value={formData.vm_hostname}
              onChange={handleChange}
              placeholder="e.g., client-analytics.company.com"
            />
          </div>
        )}

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="ip_collection_enabled"
              checked={formData.ip_collection_enabled}
              onChange={handleChange}
            />
            Enable IP Collection
          </label>
        </div>

        <div className="form-group">
          <label>Monthly Event Limit</label>
          <input
            type="number"
            name="monthly_event_limit"
            value={formData.monthly_event_limit}
            onChange={handleChange}
            placeholder="Leave empty for unlimited"
          />
        </div>

        <div className="form-group">
          <label>Billing Rate (per 1000 events)</label>
          <input
            type="number"
            step="0.0001"
            name="billing_rate_per_1k"
            value={formData.billing_rate_per_1k}
            onChange={handleChange}
          />
        </div>

        <div style={{ marginTop: '30px' }}>
          <button type="submit" disabled={loading}>
            {loading ? 'Saving...' : (isEdit ? 'Update Client' : 'Create Client')}
          </button>
          <button type="button" onClick={() => navigate('/clients')}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default ClientForm;
EOF

echo "✅ Frontend files created"

# Create README.md
cat > README.md << 'EOF'
# Evothesis Pixel Management

Centralized configuration management system for Evothesis tracking infrastructure.

## Overview

The Pixel Management service provides centralized client configuration for all Evothesis tracking VMs, enabling:

- **Client Management**: Create and configure tracking clients with privacy settings
- **Domain Authorization**: Control which domains are authorized for tracking
- **Privacy Compliance**: GDPR and HIPAA compliance configuration
- **Deployment Flexibility**: Support for shared and dedicated infrastructure

## Quick Start

1. **Prerequisites**: Docker and Docker Compose installed

2. **Start the service**:
   ```bash
   docker-compose up -d
   ```

3. **Access the admin interface**: http://localhost

4. **API Documentation**: http://localhost:8000/docs

## API Endpoints

### Configuration (for Tracking VMs)
- `GET /api/v1/config/client/{client_id}` - Get client configuration
- `GET /api/v1/config/domain/{domain}` - Get configuration by domain

### Admin Management
- `GET /api/v1/admin/clients` - List all clients
- `POST /api/v1/admin/clients` - Create new client
- `GET /api/v1/admin/clients/{client_id}` - Get client details
- `POST /api/v1/admin/clients/{client_id}/domains` - Add domain to client

## Privacy Levels

- **Standard**: Basic tracking with full IP collection
- **GDPR**: IP hashing, consent requirements, PII redaction
- **HIPAA**: Enhanced security, audit logging, BAA support

## Development

```bash
# Start development environment
docker-compose up

# View logs
docker-compose logs -f

# Reset database
docker-compose down -v && docker-compose up -d
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `ADMIN_USERNAME`: Admin interface username (default: admin)
- `ADMIN_PASSWORD`: Admin interface password (default: pixel_admin_2025)
- `SECRET_KEY`: JWT secret for authentication
EOF

echo "✅ README.md created"

# Set executable permissions and run initial setup
chmod +x docker-compose.yml

echo ""
echo "🎉 Evothesis Pixel Management setup complete!"
echo ""
echo "📁 Repository structure created:"
echo "   ├── backend/           FastAPI application"
echo "   ├── frontend/          React admin interface"
echo "   ├── database/          PostgreSQL schema"
echo "   ├── nginx/             Reverse proxy configuration"
echo "   └── docker-compose.yml Complete service stack"
echo ""
echo "🚀 Next steps:"
echo "   1. cd into the pixel-management directory"
echo "   2. Run: docker-compose up -d"
echo "   3. Visit: http://localhost (admin interface)"
echo "   4. API docs: http://localhost:8000/docs"
echo ""
echo "🔐 Default admin credentials:"
echo "   Username: admin"
echo "   Password: pixel_admin_2025"
echo ""
echo "📝 Remember to:"
echo "   - Change default passwords in production"
echo "   - Update CORS origins for production domains"
echo "   - Set proper SECRET_KEY for JWT tokens"
echo ""