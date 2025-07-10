// frontend/src/App.js - Main app with secure authentication flow (FIXED IMPORTS)
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AdminLogin from './components/AdminLogin';
import ClientList from './pages/ClientList';
import ClientForm from './pages/ClientForm';
import { useAuth } from './services/api';

// Protected route component
const ProtectedRoute = ({ children }) => {
    const { isAuthenticated } = useAuth();
    
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }
    
    return children;
};

// Admin header with logout
const AdminHeader = () => {
    const { logout, apiKey } = useAuth();
    
    const handleLogout = () => {
        logout();
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

// Main admin dashboard
const AdminDashboard = () => {
    return (
        <div>
            <AdminHeader />
            <div style={{ padding: '20px' }}>
                <Routes>
                    <Route path="/" element={<Navigate to="/clients" replace />} />
                    <Route path="/clients" element={<ClientList />} />
                    <Route path="/clients/new" element={<ClientForm />} />
                    <Route path="/clients/:clientId/edit" element={<ClientForm />} />
                    <Route path="*" element={<Navigate to="/clients" replace />} />
                </Routes>
            </div>
        </div>
    );
};

// Main App component
const App = () => {
    const { isAuthenticated, login } = useAuth();

    const handleLoginSuccess = (apiKey) => {
        login(apiKey);
    };

    return (
        <Router>
            <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
                <Routes>
                    {/* Login route */}
                    <Route 
                        path="/login" 
                        element={
                            isAuthenticated ? 
                            <Navigate to="/admin" replace /> : 
                            <AdminLogin onLoginSuccess={handleLoginSuccess} />
                        } 
                    />
                    
                    {/* Protected admin routes */}
                    <Route 
                        path="/admin/*" 
                        element={
                            <ProtectedRoute>
                                <AdminDashboard />
                            </ProtectedRoute>
                        } 
                    />
                    
                    {/* Root route */}
                    <Route 
                        path="/" 
                        element={
                            isAuthenticated ? 
                            <Navigate to="/admin" replace /> : 
                            <Navigate to="/login" replace />
                        } 
                    />
                    
                    {/* Catch all - redirect to appropriate page */}
                    <Route 
                        path="*" 
                        element={
                            isAuthenticated ? 
                            <Navigate to="/admin" replace /> : 
                            <Navigate to="/login" replace />
                        } 
                    />
                </Routes>
            </div>
        </Router>
    );
};

export default App;
