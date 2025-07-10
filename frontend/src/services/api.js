// frontend/src/services/api.js - Secure API service with dynamic authentication
import axios from 'axios';
import React from 'react';

// API base URL configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 
                    (process.env.NODE_ENV === 'production' 
                        ? window.location.origin 
                        : 'http://localhost:8000');

// Create axios instance
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    }
});

// Authentication state management
class AuthManager {
    constructor() {
        this.apiKey = null;
        this.loadStoredApiKey();
    }
    
    loadStoredApiKey() {
        const stored = sessionStorage.getItem('admin_api_key');
        if (stored) {
            this.apiKey = stored;
        }
    }
    
    setApiKey(key) {
        this.apiKey = key;
        if (key) {
            sessionStorage.setItem('admin_api_key', key);
        } else {
            sessionStorage.removeItem('admin_api_key');
        }
    }
    
    getApiKey() {
        return this.apiKey;
    }
    
    isAuthenticated() {
        return !!this.apiKey;
    }
    
    logout() {
        this.setApiKey(null);
    }
}

const authManager = new AuthManager();

// Request interceptor for authentication
apiClient.interceptors.request.use(
    (config) => {
        // Add authentication header for admin endpoints
        if (config.url && config.url.includes('/admin/')) {
            const apiKey = authManager.getApiKey();
            
            if (apiKey) {
                config.headers.Authorization = `Bearer ${apiKey}`;
            } else {
                console.error('❌ Cannot authenticate admin request - not logged in');
                throw new Error('Authentication required');
            }
        }
        
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        // Handle authentication errors
        if (error.response?.status === 401) {
            console.error('🔒 Authentication failed');
            
            // If it's an admin endpoint, the user needs to re-login
            if (error.config.url?.includes('/admin/')) {
                console.error('❌ Admin authentication failed - session expired');
                // Clear stored API key
                authManager.logout();
            }
        }
        
        return Promise.reject(error);
    }
);

// API service methods
export const apiService = {
    // Authentication methods
    auth: {
        login: (apiKey) => {
            authManager.setApiKey(apiKey);
        },
        
        logout: () => {
            authManager.logout();
        },
        
        isAuthenticated: () => {
            return authManager.isAuthenticated();
        },
        
        getApiKey: () => {
            return authManager.getApiKey();
        }
    },

    // Test API key validity
    testApiKey: async (apiKey) => {
        try {
            // Temporarily set API key for testing
            const originalKey = authManager.getApiKey();
            authManager.setApiKey(apiKey);
            
            // Test with a simple admin request
            await apiClient.get('/api/v1/admin/clients');
            
            return { success: true };
        } catch (error) {
            // Restore original key if test failed
            return { success: false, error: error.message };
        }
    },

    // Health check (public)
    health: () => apiClient.get('/health'),

    // Client management (admin - requires authentication)
    clients: {
        list: () => apiClient.get('/api/v1/admin/clients'),
        
        get: (clientId) => apiClient.get(`/api/v1/admin/clients/${clientId}`),
        
        create: (clientData) => apiClient.post('/api/v1/admin/clients', clientData),
        
        update: (clientId, updates) => apiClient.put(`/api/v1/admin/clients/${clientId}`, updates),
        
        delete: (clientId) => apiClient.delete(`/api/v1/admin/clients/${clientId}`)
    },

    // Domain management (admin - requires authentication)
    domains: {
        list: (clientId) => apiClient.get(`/api/v1/admin/clients/${clientId}/domains`),
        
        add: (clientId, domainData) => apiClient.post(`/api/v1/admin/clients/${clientId}/domains`, domainData),
        
        remove: (clientId, domain) => apiClient.delete(`/api/v1/admin/clients/${clientId}/domains/${domain}`)
    },

    // Configuration (public - no auth needed)
    config: {
        getByDomain: (domain) => apiClient.get(`/api/v1/config/domain/${domain}`),
        
        getByClient: (clientId) => apiClient.get(`/api/v1/config/client/${clientId}`)
    }
};

// React hook for authentication status
export const useAuth = () => {
    const [isAuthenticated, setIsAuthenticated] = React.useState(authManager.isAuthenticated());
    
    const login = (apiKey) => {
        apiService.auth.login(apiKey);
        setIsAuthenticated(true);
    };
    
    const logout = () => {
        apiService.auth.logout();
        setIsAuthenticated(false);
    };
    
    React.useEffect(() => {
        // Check if user is still authenticated on component mount
        setIsAuthenticated(authManager.isAuthenticated());
    }, []);
    
    return {
        isAuthenticated,
        login,
        logout,
        apiKey: authManager.getApiKey()
    };
};

export default apiClient;
