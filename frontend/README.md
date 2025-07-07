# Pixel Management Frontend

**React-based admin interface for client configuration and domain management**

## 🏗️ Architecture

The frontend provides a comprehensive admin interface for managing clients, domains, and tracking configurations in the Evothesis analytics platform.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin User    │───▶│  React Frontend │───▶│  FastAPI Backend│
│  - Browser      │    │  - Client CRUD  │    │  - Basic Auth   │
│  - Basic Auth   │    │  - Domain mgmt  │    │  - Firestore    │
│  - HTTP requests│    │  - User Guide   │    │  - API endpoints│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Key Features

### **🏢 Client Management**
- **Create/Edit Clients**: Full CRUD operations for client configuration
- **Privacy Levels**: Standard, GDPR, and HIPAA compliance options
- **Deployment Types**: Shared infrastructure or dedicated VM options
- **Billing Configuration**: Flexible owner and billing entity management

### **🌐 Domain Authorization**
- **Add/Remove Domains**: Authorize domains for tracking pixel access
- **Primary Domain**: Designate main domain for each client
- **Real-time Validation**: Immediate feedback on domain authorization
- **Security First**: All domains must be explicitly authorized

### **📊 Dashboard Overview**
- **Client Statistics**: Total clients, active clients, privacy level distribution
- **Quick Actions**: Rapid access to common management tasks
- **System Status**: Visual indicators for system health

### **📚 User Documentation**
- **Comprehensive Guide**: Step-by-step instructions for all features
- **Troubleshooting**: Common issues and solutions
- **Integration Examples**: Code samples for tracking implementation

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html              # HTML template
├── src/
│   ├── App.js                  # Main application component
│   ├── App.css                 # Global styles
│   ├── index.js                # React entry point
│   ├── index.css               # Base styles
│   └── pages/
│       ├── Dashboard.js        # Admin dashboard overview
│       ├── ClientList.js       # Client listing and management
│       ├── ClientForm.js       # Client creation/editing form
│       └── UserGuide.js        # Comprehensive documentation
├── package.json                # Dependencies and scripts
├── Dockerfile                  # Container configuration
└── README.md                   # This file
```

## 🚀 Core Components

### **Dashboard** (`pages/Dashboard.js`)
- **System Overview**: Client counts and privacy level distribution
- **Quick Actions**: Direct links to common management tasks
- **Real-time Statistics**: Live data from Firestore via API

### **Client Management** (`pages/ClientList.js`, `pages/ClientForm.js`)
- **Client Listing**: Searchable, sortable client directory
- **CRUD Operations**: Create, read, update client configurations
- **Domain Management**: Add/remove authorized domains per client
- **Form Validation**: Real-time validation with helpful error messages

### **User Guide** (`pages/UserGuide.js`)
- **Step-by-Step Instructions**: Complete setup and usage guide
- **Code Examples**: Integration examples for developers
- **Troubleshooting**: Common issues and solutions
- **Security Best Practices**: Domain authorization and privacy compliance

## 🔐 Authentication Integration

### **HTTP Basic Auth Passthrough**
The frontend relies on the browser's native Basic Auth implementation:

```javascript
// No explicit auth handling needed - browser manages credentials
fetch('/api/v1/admin/clients')
  .then(response => response.json())
  .then(data => setClients(data));
```

### **Authentication Flow**
1. **Browser Prompt**: User accesses admin interface
2. **Basic Auth Challenge**: Backend sends WWW-Authenticate header
3. **Credential Entry**: Browser shows login dialog
4. **Session Persistence**: Browser caches credentials for session
5. **API Requests**: All subsequent requests include auth headers

### **User Experience**
- **Single Login**: Enter credentials once per browser session
- **Transparent Auth**: No explicit login/logout UI needed
- **Cross-Tab Persistence**: Credentials shared across tabs
- **Secure Storage**: Browser handles credential security

## ⚙️ Configuration

### **Environment Variables**
```bash
# Development
REACT_APP_API_URL=http://localhost:8000

# Production (automatically configured)
REACT_APP_API_URL=/  # Relative URLs for same-origin requests
```

### **API Integration**
```javascript
// All API calls use relative URLs in production
const API_BASE = process.env.REACT_APP_API_URL || '';

// Example API call
const response = await fetch(`${API_BASE}/api/v1/admin/clients`);
```

### **Proxy Configuration** (Development)
```json
// package.json
{
  "proxy": "http://backend:8000"
}
```

## 🛠️ Development

### **Local Development Setup**
```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Start development server
npm start

# 3. Access development interface
# http://localhost:3000 (with proxy to backend)
```

### **Development vs Production**
- **Development**: Proxy to backend, no auth required, hot reload
- **Production**: Served by FastAPI, Basic Auth required, optimized build

### **Available Scripts**
```bash
npm start          # Start development server with hot reload
npm run build      # Create optimized production build
npm test           # Run test suite
npm run eject      # Eject from Create React App (not recommended)
```

## 🎨 UI/UX Design

### **Design System**
- **Color Palette**: Navy primary, electric blue accent, silver/gray neutrals
- **Typography**: Inter font family for clarity and professionalism
- **Layout**: Clean, spacious design with clear hierarchy
- **Responsive**: Mobile-friendly responsive design

### **Component Patterns**
- **Functional Components**: Modern React hooks pattern
- **Form Handling**: Controlled components with validation
- **Error States**: Clear error messages and recovery guidance
- **Loading States**: Visual feedback for async operations

### **Accessibility**
- **Semantic HTML**: Proper heading hierarchy and form labels
- **Keyboard Navigation**: Tab-accessible interface
- **Screen Reader Support**: ARIA labels and descriptions
- **Color Contrast**: WCAG compliant color combinations

## 📱 User Interface Features

### **Client Management Interface**
```javascript
// Client creation with privacy level selection
<select name="privacy_level" required>
  <option value="standard">Standard - Basic tracking</option>
  <option value="gdpr">GDPR - IP hashing, consent required</option>
  <option value="hipaa">HIPAA - Enhanced security, audit logging</option>
</select>
```

### **Domain Management Interface**
```javascript
// Real-time domain addition with validation
const addDomain = async () => {
  const response = await fetch(`/api/v1/admin/clients/${clientId}/domains`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain: newDomain, is_primary: false })
  });
  
  if (response.ok) {
    refreshDomains(); // Update domain list
  }
};
```

### **Form Validation**
- **Real-time Validation**: Immediate feedback on form inputs
- **Required Field Indicators**: Clear visual indicators for required fields
- **Error Handling**: Descriptive error messages for API failures
- **Success Feedback**: Confirmation messages for successful operations

## 🚀 Production Deployment

### **Build Process**
```bash
# Create optimized production build
npm run build

# Output: build/ directory with static files
# - Minified JavaScript and CSS
# - Optimized images and assets
# - Service worker for caching
```

### **Deployment Integration**
The frontend is built and served by the FastAPI backend in production:

```dockerfile
# Multi-stage build in root Dockerfile
FROM