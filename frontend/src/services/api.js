/**
 * API service layer for pixel management admin interface.
 * 
 * This module provides a centralized HTTP client for all backend communications
 * using axios. It handles authentication headers, request/response formatting,
 * error handling, and environment-based URL configuration for both development
 * and production deployments.
 * 
 * Key features:
 * - Axios-based HTTP client with automatic authentication header injection
 * - Environment-aware API base URL configuration (development vs production)
 * - Comprehensive client management operations (CRUD)
 * - Domain management and authorization operations
 * - Error handling with detailed error response formatting
 * - Request interceptors for authentication token management
 * 
 * API endpoints:
 * - Client operations: create, read, update, delete clients
 * - Domain operations: add, list, remove domains from clients
 * - Authentication: login validation and token management
 * 
 * The service integrates with the authentication context to provide seamless
 * API access throughout the admin interface.
 */

// frontend/src/services/api.js - FIXED VERSION
import axios from 'axios';

// API base URL configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 
                    (process.env.NODE_ENV === 'production' 
                        ? window.location.origin 
                        : `${window.location.protocol}//${window.location.host}`);

console.log('🌐 API Base URL:', API_BASE_URL);

// Create axios instance
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    }
});

// FIXED: Request interceptor that reads directly from sessionStorage
apiClient.interceptors.request.use(
    (config) => {
        console.log('📤 API Request:', config.method?.toUpperCase(), config.url);
        
        // Add authentication header for admin endpoints
        if (config.url && config.url.includes('/admin/')) {
            // FIXED: Read directly from sessionStorage instead of authManager
            const apiKey = sessionStorage.getItem('admin_api_key');
            
            if (apiKey) {
                config.headers.Authorization = `Bearer ${apiKey}`;
                console.log('🔐 Added auth header for admin endpoint:', `Bearer ${apiKey.substring(0, 20)}...`);
            } else {
                console.error('❌ No API key available in sessionStorage');
                return Promise.reject(new Error('Authentication required'));
            }
        }
        
        return config;
    },
    (error) => {
        console.error('📤 Request interceptor error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => {
        console.log('📥 API Response:', response.status, response.config.url);
        return response;
    },
    (error) => {
        const status = error.response?.status;
        const url = error.config?.url;
        
        console.error('📥 API Error:', status, url, error.message);
        
        // Handle authentication errors
        if (status === 401) {
            console.error('🔒 Authentication failed - invalid or expired API key');
            
            // If it's an admin endpoint, clear the API key
            if (url?.includes('/admin/')) {
                console.error('❌ Clearing invalid API key');
                sessionStorage.removeItem('admin_api_key');
                // Trigger a full page reload to reset authentication state
                window.location.reload();
            }
        } else if (status === 403) {
            console.error('🚫 Access denied - insufficient permissions');
        } else if (status >= 500) {
            console.error('🔥 Server error:', status);
        }
        
        return Promise.reject(error);
    }
);

// API service methods
export const apiService = {
    // Test API key validity
    testApiKey: async (apiKey) => {
        console.log('🧪 Testing API key...');
        
        try {
            // Create a test request with the provided API key
            const testResponse = await axios.get(
                `${API_BASE_URL}/api/v1/admin/clients`,
                {
                    headers: {
                        'Authorization': `Bearer ${apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 8000
                }
            );
            
            console.log('✅ API key test successful:', testResponse.status);
            return { 
                success: true, 
                status: testResponse.status,
                data: testResponse.data 
            };
        } catch (error) {
            const status = error.response?.status;
            
            console.error('❌ API key test failed:', status, error.message);
            
            let errorMessage = 'Connection error';
            if (status === 401) {
                errorMessage = 'Invalid API key';
            } else if (status === 403) {
                errorMessage = 'Valid API key but insufficient permissions';
            } else if (status >= 500) {
                errorMessage = 'Server error - please try again';
            }
            
            return { 
                success: false, 
                error: errorMessage,
                status: status
            };
        }
    },

    // Health check (public)
    health: () => {
        console.log('💓 Health check request');
        return apiClient.get('/health');
    },

    // Client management (admin - requires authentication)
    clients: {
        list: () => {
            console.log('📋 Fetching client list');
            return apiClient.get('/api/v1/admin/clients');
        },
        
        get: (clientId) => {
            console.log('👤 Fetching client:', clientId);
            return apiClient.get(`/api/v1/admin/clients/${clientId}`);
        },
        
        create: (clientData) => {
            console.log('➕ Creating client:', clientData.name);
            return apiClient.post('/api/v1/admin/clients', clientData);
        },
        
        update: (clientId, updates) => {
            console.log('✏️ Updating client:', clientId);
            return apiClient.put(`/api/v1/admin/clients/${clientId}`, updates);
        },
        
        delete: (clientId) => {
            console.log('🗑️ Deleting client:', clientId);
            return apiClient.delete(`/api/v1/admin/clients/${clientId}`);
        }
    },

    // Domain management (admin - requires authentication)
    domains: {
        list: (clientId) => {
            console.log('🌐 Fetching domains for client:', clientId);
            return apiClient.get(`/api/v1/admin/clients/${clientId}/domains`);
        },
        
        add: (clientId, domainData) => {
            console.log('➕ Adding domain to client:', clientId, domainData.domain);
            return apiClient.post(`/api/v1/admin/clients/${clientId}/domains`, domainData);
        },
        
        remove: (clientId, domain) => {
            console.log('🗑️ Removing domain from client:', clientId, domain);
            return apiClient.delete(`/api/v1/admin/clients/${clientId}/domains/${domain}`);
        }
    },

    // Configuration (public - no auth needed)
    config: {
        getByDomain: (domain) => {
            console.log('🔍 Getting config by domain:', domain);
            return apiClient.get(`/api/v1/config/domain/${domain}`);
        },
        
        getByClient: (clientId) => {
            console.log('🔍 Getting config by client:', clientId);
            return apiClient.get(`/api/v1/config/client/${clientId}`);
        }
    }
};

// Export the configured axios instance as default
export default apiClient;