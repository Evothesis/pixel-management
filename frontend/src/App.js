// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AdminLogin from './components/AdminLogin';
import ClientList from './pages/ClientList';
import ClientForm from './pages/ClientForm';

// Loading component
const LoadingScreen = () => (
    <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5'
    }}>
        <div style={{ textAlign: 'center' }}>
            <div style={{
                width: '40px',
                height: '40px',
                border: '4px solid #e2e8f0',
                borderTop: '4px solid #4299e1',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 16px'
            }}></div>
            <p style={{ color: '#718096', margin: 0 }}>Loading...</p>
        </div>
    </div>
);

// Protected route component
const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, isLoading, isInitialized } = useAuth();
    
    console.log('🛡️ ProtectedRoute check:', { 
        isAuthenticated, 
        isLoading, 
        isInitialized 
    });
    
    // Show loading while auth is initializing
    if (!isInitialized || isLoading) {
        console.log('🛡️ ProtectedRoute: Still loading auth state');
        return <LoadingScreen />;
    }
    
    // Only redirect after we're sure about auth state
    if (!isAuthenticated) {
        console.log('🛡️ ProtectedRoute: Not authenticated, redirecting to login');
        return <Navigate to="/login" replace />;
    }
    
    console.log('🛡️ ProtectedRoute: Authenticated, showing protected content');
    return children;
};

// Admin header component
const AdminHeader = () => {
    const { logout, apiKey } = useAuth();
    
    const handleLogout = () => {
        console.log('🚪 Logout button clicked');
        logout();
        // Force navigation to login
        window.location.href = '/login';
    };
    
    return (
        <header style={{
            backgroundColor: '#2d3748',
            color: 'white',
            padding: '12px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
        }}>
            <div>
                <h1 style={{ margin: 0, fontSize: '18px' }}>
                    🏢 Evothesis Pixel Management
                </h1>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                <span style={{ fontSize: '12px', color: '#a0aec0' }}>
                    API Key: {apiKey ? `${apiKey.substring(0, 15)}...` : 'Not set'}
                </span>
                <button
                    onClick={handleLogout}
                    style={{
                        backgroundColor: '#e53e3e',
                        color: 'white',
                        border: 'none',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer'
                    }}
                >
                    Logout
                </button>
            </div>
        </header>
    );
};

// Main app content component
const AppContent = () => {
    const { isAuthenticated, isLoading, isInitialized, login } = useAuth();
    
    console.log('📱 AppContent render:', { 
        isAuthenticated, 
        isLoading, 
        isInitialized 
    });
    
    // Show loading screen while initializing
    if (!isInitialized || isLoading) {
        console.log('📱 AppContent: Auth still loading');
        return <LoadingScreen />;
    }
    
    const handleLoginSuccess = (apiKey) => {
        console.log('✅ Login successful in AppContent');
        login(apiKey);
    };
    
    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
            <Routes>
                {/* Login route */}
                <Route 
                    path="/login" 
                    element={
                        isAuthenticated ? (
                            <Navigate to="/admin/clients" replace />
                        ) : (
                            <AdminLogin onLoginSuccess={handleLoginSuccess} />
                        )
                    } 
                />
                
                {/* Protected admin routes */}
                <Route 
                    path="/admin/clients" 
                    element={
                        <ProtectedRoute>
                            <AdminHeader />
                            <div style={{ padding: '20px' }}>
                                <ClientList />
                            </div>
                        </ProtectedRoute>
                    } 
                />
                
                <Route 
                    path="/admin/clients/new" 
                    element={
                        <ProtectedRoute>
                            <AdminHeader />
                            <div style={{ padding: '20px' }}>
                                <ClientForm />
                            </div>
                        </ProtectedRoute>
                    } 
                />
                
                <Route 
                    path="/admin/clients/:clientId/edit" 
                    element={
                        <ProtectedRoute>
                            <AdminHeader />
                            <div style={{ padding: '20px' }}>
                                <ClientForm />
                            </div>
                        </ProtectedRoute>
                    } 
                />
                
                {/* Admin root redirect */}
                <Route 
                    path="/admin" 
                    element={<Navigate to="/admin/clients" replace />} 
                />
                
                {/* Root route */}
                <Route 
                    path="/" 
                    element={
                        isAuthenticated ? (
                            <Navigate to="/admin/clients" replace />
                        ) : (
                            <Navigate to="/login" replace />
                        )
                    } 
                />
                
                {/* Catch all */}
                <Route 
                    path="*" 
                    element={
                        isAuthenticated ? (
                            <Navigate to="/admin/clients" replace />
                        ) : (
                            <Navigate to="/login" replace />
                        )
                    } 
                />
            </Routes>
        </div>
    );
};

// Main App component with AuthProvider wrapper
const App = () => {
    console.log('🚀 App component mounting');
    
    return (
        <AuthProvider>
            <Router>
                <AppContent />
                
                {/* Add CSS for loading spinner */}
                <style jsx global>{`
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `}</style>
            </Router>
        </AuthProvider>
    );
};

export default App;