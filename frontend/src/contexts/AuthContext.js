// frontend/src/contexts/AuthContext.js
import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

// Single source of truth for authentication state
const AuthContext = createContext();

// Authentication manager - singleton pattern
class AuthenticationManager {
    constructor() {
        this.apiKey = null;
        this.isInitialized = false;
        this.subscribers = new Set();
    }
    
    initialize() {
        if (this.isInitialized) return;
        
        try {
            const stored = sessionStorage.getItem('admin_api_key');
            if (stored && stored.trim()) {
                this.apiKey = stored.trim();
                console.log('🔑 Loaded API key from storage');
            } else {
                console.log('🔑 No stored API key found');
            }
        } catch (error) {
            console.error('🔑 Error loading API key:', error);
        }
        
        this.isInitialized = true;
        this.notifySubscribers();
    }
    
    setApiKey(key) {
        const cleanKey = key ? key.trim() : null;
        
        if (cleanKey !== this.apiKey) {
            this.apiKey = cleanKey;
            
            try {
                if (cleanKey) {
                    sessionStorage.setItem('admin_api_key', cleanKey);
                    console.log('🔑 API key saved');
                } else {
                    sessionStorage.removeItem('admin_api_key');
                    console.log('🔑 API key removed');
                }
            } catch (error) {
                console.error('🔑 Error saving API key:', error);
            }
            
            this.notifySubscribers();
        }
    }
    
    getApiKey() {
        return this.apiKey;
    }
    
    isAuthenticated() {
        return this.isInitialized && !!this.apiKey;
    }
    
    subscribe(callback) {
        this.subscribers.add(callback);
        return () => this.subscribers.delete(callback);
    }
    
    notifySubscribers() {
        this.subscribers.forEach(callback => callback({
            isAuthenticated: this.isAuthenticated(),
            apiKey: this.getApiKey(),
            isInitialized: this.isInitialized
        }));
    }
    
    logout() {
        this.setApiKey(null);
    }
}

// Single instance
const authManager = new AuthenticationManager();

// Provider component
export const AuthProvider = ({ children }) => {
    const [authState, setAuthState] = useState({
        isAuthenticated: false,
        apiKey: null,
        isInitialized: false,
        isLoading: true
    });
    
    const initializationRef = useRef(false);
    
    // Stable callback functions
    const login = useCallback((apiKey) => {
        console.log('🔐 Login called');
        authManager.setApiKey(apiKey);
    }, []);
    
    const logout = useCallback(() => {
        console.log('🔐 Logout called');
        authManager.logout();
    }, []);
    
    // Subscribe to auth manager changes
    useEffect(() => {
        console.log('🔐 Setting up auth subscription');
        
        const unsubscribe = authManager.subscribe((newState) => {
            console.log('🔐 Auth state update:', newState);
            setAuthState({
                ...newState,
                isLoading: false
            });
        });
        
        // Initialize only once
        if (!initializationRef.current) {
            initializationRef.current = true;
            console.log('🔐 Initializing auth manager...');
            
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                authManager.initialize();
            }, 50);
        }
        
        return unsubscribe;
    }, []);
    
    const contextValue = {
        ...authState,
        login,
        logout
    };
    
    console.log('🔐 AuthProvider render:', contextValue);
    
    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};

// Hook to use auth context
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

// Export auth manager for direct API calls
export { authManager };