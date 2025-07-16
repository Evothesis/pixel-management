# Pixel Management Frontend

**React-based admin interface for centralized client configuration and domain management**

## 🏗️ Architecture

Modern React application providing comprehensive analytics configuration management with real-time validation and responsive design.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin User    │───▶│  React Frontend │───▶│  FastAPI Backend│
│ - Browser access│    │ - Client CRUD   │    │ - API endpoints │
│ - Form interaction│   │ - Domain mgmt   │    │ - Authentication│
│ - Real-time feedback│ │ - Dashboard     │    │ - Data validation│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Core Features

**🏢 Client Management Interface**
- Complete client lifecycle management (create, edit, deactivate)
- Privacy level configuration with clear compliance indicators
- Deployment type selection (shared infrastructure vs dedicated VMs)
- Owner and billing entity relationship management

**🌐 Domain Authorization Management**
- Real-time domain addition with instant validation
- Primary domain designation for client identification
- Bulk domain operations for enterprise clients
- Domain removal with safety confirmations

**📊 Administrative Dashboard**
- System overview with client statistics and health metrics
- Quick action buttons for common administrative tasks
- Real-time system status indicators
- Performance monitoring widgets

**📚 User Documentation**
- User guide component available (not currently integrated into main navigation)
- Code examples for tracking implementation
- Troubleshooting procedures and common solutions
- Privacy compliance guidance

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html         # HTML template with meta tags
├── src/
│   ├── App.js             # Main application with routing
│   ├── App.css            # Global styles and design system
│   ├── index.js           # React DOM mounting point
│   ├── components/        # Core UI components (primary location)
│   │   ├── Dashboard.js   # System overview and quick stats
│   │   ├── ClientList.js  # Client table with search/filter
│   │   ├── ClientForm.js  # Client creation/editing form
│   │   └── AdminLogin.js  # Authentication interface
│   ├── pages/             # Alternative component location
│   ├── contexts/          # React context providers
│   │   └── AuthContext.js # Authentication state management
│   └── services/          # API integration layer
│       └── api.js         # HTTP client with auth headers
├── package.json           # Dependencies and build scripts
├── Dockerfile             # Development container config
└── README.md              # This documentation
```

## 🎨 User Interface Design

**Design System:**
- **Typography**: System font stack (system-ui, -apple-system, sans-serif)
- **Color Palette**: Navy primary (#2d3748), blue accent (#4299e1)
- **Layout**: Clean, spacious design with clear visual hierarchy
- **Responsive**: Mobile-friendly interface supporting tablets and phones

**Component Architecture:**
- **Functional Components**: Modern React hooks pattern throughout
- **Controlled Forms**: React state drives all form interactions
- **Error Boundaries**: Graceful error handling with recovery guidance
- **Loading States**: Visual feedback for all asynchronous operations

## 🚀 Key Components

### Dashboard (`pages/Dashboard.js`)
**System overview with real-time metrics:**
- Client count by privacy level (Standard/GDPR/HIPAA)
- Active domain count and authorization status
- Recent configuration changes and admin activity
- System health indicators and performance metrics

### Client Management (`pages/ClientList.js` & `pages/ClientForm.js`)
**Complete client lifecycle management:**

```javascript
// Client creation with privacy compliance
const handleSubmit = async (formData) => {
  const response = await fetch('/api/v1/admin/clients', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: formData.name,
      privacy_level: formData.privacy_level, // standard/gdpr/hipaa
      deployment_type: formData.deployment_type, // shared/dedicated
      owner: formData.owner,
      billing_entity: formData.billing_entity
    })
  });
  
  if (response.ok) {
    setClients([...clients, await response.json()]);
  }
};
```

### Domain Management Interface
**Domain authorization within client forms:**

```javascript
// Add domain functionality integrated into ClientForm
const addDomain = async () => {
  const response = await fetch(`/api/v1/admin/clients/${clientId}/domains`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      domain: newDomain.toLowerCase().trim(),
      is_primary: false 
    })
  });
  
  if (response.ok) {
    refreshDomains(); // Update domain list immediately
    setNewDomain(''); // Clear input field
  }
};
```

**Note:** Standalone domain management interface shows "Coming soon!" - bulk operations not yet implemented.

## 🔧 Development Workflow

**Local Development:**
```bash
# 1. Install dependencies
cd frontend/
npm install

# 2. Start development server
npm start

# 3. Access development interface
# http://localhost:3000 (auto-proxy to backend:8000)
```

**Available Scripts:**
```bash
npm start       # Development server with hot reload
npm run build   # Production build with optimization
npm test        # Jest test suite
npm run lint    # ESLint code quality check
```

**Development Features:**
- Hot reload for instant feedback during development
- Proxy configuration routes API calls to backend automatically
- React DevTools integration for component debugging
- Source maps for easy debugging in browser

## 🏗️ Production Integration

**Build Process:**
```bash
# Multi-stage Docker build optimizes for production
FROM node:18-alpine AS builder
WORKDIR /app/frontend
COPY package*.json ./
RUN npm install --production
COPY . ./
RUN npm run build  # Creates optimized static files
```

**Backend Integration:**
The frontend is served directly by the FastAPI backend in production:

```python
# Backend serves React static files
app.mount("/static", StaticFiles(directory="/app/static/static"))

@app.get("/", include_in_schema=False)
async def serve_react_app():
    return FileResponse("/app/static/index.html")
```

## 📊 State Management & Data Flow

**React Hooks Pattern:**
```javascript
// Centralized state management with hooks
const [clients, setClients] = useState([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

// API integration with error handling
useEffect(() => {
  const fetchClients = async () => {
    try {
      const response = await fetch('/api/v1/admin/clients');
      if (response.ok) {
        setClients(await response.json());
      } else {
        setError('Failed to load clients');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  fetchClients();
}, []);
```

**Form Validation:**
- Real-time validation with immediate user feedback
- Required field indicators with clear visual cues
- Privacy level validation with compliance warnings
- Domain format validation with helpful error messages

## 🛡️ Security & Error Handling

**Authentication Integration:**
```javascript
// Automatic session management
const handleApiError = (error) => {
  if (error.status === 401) {
    alert('Session expired. Please refresh and login again.');
    window.location.reload();
  } else if (error.status === 403) {
    alert('Access denied. Check your permissions.');
  } else {
    alert('Operation failed. Please try again.');
  }
};
```

**Input Sanitization:**
- All form inputs validated before submission
- Domain names normalized (lowercase, trimmed)
- XSS prevention via React's built-in escaping
- CSRF protection via same-origin policy

## 🎯 User Experience Features

**Responsive Design:**
- Mobile-first approach with progressive enhancement
- Touch-friendly interface for tablet administration
- Flexible grid layouts adapt to screen size
- Optimized typography scales appropriately

**Accessibility:**
- Semantic HTML with proper heading hierarchy
- Keyboard navigation support throughout interface
- Screen reader compatibility with ARIA labels
- High contrast color scheme meets WCAG guidelines

**Performance Optimization:**
- Code splitting reduces initial bundle size
- Lazy loading for non-critical components
- Image optimization and compression
- Service worker caching for offline functionality

## 🧪 Testing Strategy

**Component Testing:**
```bash
# Run test suite
npm test

# Watch mode for development
npm run test:watch

# Coverage reporting
npm run test:coverage
```

**Quality Assurance:**
- ESLint for code style consistency
- Prettier for automatic code formatting
- Jest for unit and integration testing
- React Testing Library for component testing

## 📱 Mobile Interface

**Responsive Breakpoints:**
- **Mobile**: 320px - 768px (optimized touch interface)
- **Tablet**: 768px - 1024px (hybrid touch/mouse interface)  
- **Desktop**: 1024px+ (full mouse-driven interface)

**Mobile-Friendly Features:**
- Responsive CSS Grid layouts
- Touch-friendly button sizing
- Adaptable card-based interface
- Standard mobile browser optimizations

---

**Modern React interface enabling efficient analytics infrastructure management**