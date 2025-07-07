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
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --only=production
COPY frontend/ ./
RUN npm run build

# Backend stage serves built frontend
FROM python:3.11-slim
COPY --from=frontend-builder /app/frontend/build ./static
# FastAPI serves static files from /static route
```

### **Static File Serving**
```python
# Backend serves React app
app.mount("/static", StaticFiles(directory="/app/static/static"), name="static")

@app.get("/", include_in_schema=False)
async def serve_react_app():
    return FileResponse("/app/static/index.html")
```

## 🔍 Monitoring & Analytics

### **Error Handling**
```javascript
// Comprehensive error handling with user feedback
const handleApiError = (error) => {
  if (error.status === 401) {
    alert('Session expired. Please refresh and login again.');
  } else if (error.status === 403) {
    alert('Access denied. Check your permissions.');
  } else {
    alert('Operation failed. Please try again.');
  }
};
```

### **Performance Monitoring**
- **Bundle Size**: Optimized with code splitting
- **Load Times**: Minimized with lazy loading
- **API Response Times**: Visual loading indicators
- **Error Tracking**: User-friendly error messages

### **User Experience Metrics**
- **Form Completion**: Real-time validation reduces errors
- **Navigation**: Intuitive menu structure and breadcrumbs
- **Feedback**: Immediate confirmation for all actions
- **Help Integration**: Contextual help and user guide access

## 📊 Data Management

### **State Management**
```javascript
// React hooks for state management
const [clients, setClients] = useState([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

// API data fetching with error handling
useEffect(() => {
  const fetchClients = async () => {
    try {
      const response = await fetch('/api/v1/admin/clients');
      if (response.ok) {
        const data = await response.json();
        setClients(data);
      } else {
        setError('Failed to load clients');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };
  
  fetchClients();
}, []);
```

### **Form Data Handling**
- **Controlled Components**: React state drives form values
- **Validation**: Real-time validation with helpful messages
- **Submission**: Optimistic updates with rollback on failure
- **Auto-save**: Draft preservation for long forms

## 🧪 Testing & Quality

### **Testing Strategy**
```bash
# Unit tests for components
npm test

# Component testing
npm run test:watch

# Coverage reporting
npm run test:coverage
```

### **Quality Assurance**
- **ESLint**: Code style and error checking
- **Prettier**: Consistent code formatting
- **React DevTools**: Development debugging
- **Browser Testing**: Cross-browser compatibility

### **Accessibility Testing**
- **Screen Reader**: Testing with NVDA/JAWS
- **Keyboard Navigation**: Tab order and focus management
- **Color Contrast**: WCAG AA compliance
- **Semantic HTML**: Proper heading structure

## 🔧 Customization & Extension

### **Adding New Features**
```javascript
// Example: Adding new client field
// 1. Update ClientForm component
<div className="form-group">
  <label htmlFor="new_field">New Field</label>
  <input
    type="text"
    id="new_field"
    name="new_field"
    value={formData.new_field}
    onChange={handleChange}
  />
</div>

// 2. Update form validation
// 3. Update API integration
// 4. Update display components
```

### **Styling Customization**
```css
/* Custom CSS variables for theming */
:root {
  --primary-color: #1a365d;
  --accent-color: #3182ce;
  --background-color: #ffffff;
  --text-color: #4a5568;
}

/* Component-specific styling */
.client-card {
  border: 1px solid var(--accent-color);
  border-radius: 8px;
  padding: 20px;
  margin: 10px 0;
}
```

### **API Integration Patterns**
```javascript
// Reusable API utility
const apiCall = async (endpoint, options = {}) => {
  const response = await fetch(`/api/v1${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.status}`);
  }
  
  return response.json();
};
```

## 🚨 Security Considerations

### **Client-Side Security**
- **No Credential Storage**: Browser handles authentication
- **HTTPS Only**: All production traffic encrypted
- **Input Sanitization**: XSS prevention in form inputs
- **API Validation**: All inputs validated on backend

### **Data Protection**
- **No Sensitive Data Caching**: Sensitive data not stored in localStorage
- **Session Management**: Browser-native credential handling
- **Error Messages**: No sensitive information in error responses
- **Audit Trail**: All admin actions logged on backend

### **Best Practices**
```javascript
// Secure form handling
const sanitizeInput = (input) => {
  return input.trim().replace(/<script.*?<\/script>/gi, '');
};

// Safe API error handling
const handleError = (error) => {
  // Never expose sensitive error details to user
  console.error('API Error:', error);
  setError('Operation failed. Please try again.');
};
```

## 📚 Documentation Integration

### **User Guide Features**
- **Interactive Navigation**: Smooth scrolling to sections
- **Code Examples**: Copy-pasteable integration snippets
- **Visual Aids**: Screenshots and diagrams
- **Search Functionality**: Quick access to specific topics

### **Help System**
```javascript
// Contextual help integration
const HelpTooltip = ({ topic, children }) => {
  return (
    <div className="help-tooltip">
      {children}
      <span className="help-icon" onClick={() => showHelp(topic)}>?</span>
    </div>
  );
};
```

## 🔮 Future Enhancements

### **Planned Features**
- **Advanced Dashboard**: Real-time charts and analytics
- **Bulk Operations**: Multi-client management tools
- **User Management**: Multiple admin accounts with roles
- **Export Functionality**: CSV/PDF reports
- **Mobile App**: React Native companion app

### **Technical Improvements**
- **Progressive Web App**: Offline functionality
- **Performance Optimization**: Lazy loading and code splitting
- **Advanced Caching**: Smart data caching strategies
- **Real-time Updates**: WebSocket integration for live data

---

**Built with ❤️ for intuitive client configuration and domain management**