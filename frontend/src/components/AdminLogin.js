/**
 * Admin login form component for API key authentication.
 * 
 * This component provides a secure login interface for pixel management admin access
 * using API key authentication. It features form validation, error handling, and
 * integration with the authentication context for seamless login flow.
 * 
 * Key features:
 * - Form-based API key input with validation
 * - Real-time authentication with backend API validation
 * - Error state management and user feedback
 * - Loading states during authentication process
 * - Integration with AuthContext for global state updates
 * - Responsive design with clean, professional styling
 * 
 * The component handles the complete login flow from user input through API
 * validation to successful authentication and redirect to admin interface.
 */

// frontend/src/components/AdminLogin.js
import React, { useState } from 'react';
import { apiService } from '../services/api';

const AdminLogin = ({ onLoginSuccess }) => {
    const [apiKey, setApiKey] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!apiKey.trim()) {
            setError('Please enter an API key');
            return;
        }
        
        setLoading(true);
        setError(null);
        
        console.log('🔐 Attempting login...');

        try {
            // Test the API key
            const testResult = await apiService.testApiKey(apiKey.trim());
            
            if (testResult.success) {
                console.log('✅ Login successful');
                
                // Notify parent component
                onLoginSuccess(apiKey.trim());
                
                // Clear form
                setApiKey('');
            } else {
                console.error('❌ Login failed:', testResult.error);
                setError(testResult.error || 'Invalid API key. Please check your credentials.');
            }
        } catch (error) {
            console.error('❌ Login error:', error);
            setError('Connection error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#f5f5f5',
            fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
            <div style={{
                backgroundColor: 'white',
                padding: '40px',
                borderRadius: '8px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                maxWidth: '400px',
                width: '100%'
            }}>
                <div style={{ textAlign: 'center', marginBottom: '30px' }}>
                    <h1 style={{ 
                        color: '#2d3748', 
                        marginBottom: '8px',
                        fontSize: '24px',
                        fontWeight: '600'
                    }}>
                        🔐 Evothesis Admin
                    </h1>
                    <p style={{ 
                        color: '#718096', 
                        margin: 0,
                        fontSize: '14px'
                    }}>
                        Pixel Management Console
                    </p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '6px',
                            color: '#4a5568',
                            fontSize: '14px',
                            fontWeight: '500'
                        }}>
                            Admin API Key
                        </label>
                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="Enter your admin API key"
                            required
                            disabled={loading}
                            autoComplete="current-password"
                            style={{
                                width: '100%',
                                padding: '12px',
                                border: error ? '1px solid #e53e3e' : '1px solid #e2e8f0',
                                borderRadius: '6px',
                                fontSize: '14px',
                                boxSizing: 'border-box',
                                backgroundColor: loading ? '#f7fafc' : 'white',
                                transition: 'border-color 0.2s, background-color 0.2s'
                            }}
                            onFocus={() => setError(null)}
                        />
                    </div>

                    {error && (
                        <div style={{
                            backgroundColor: '#fed7d7',
                            border: '1px solid #feb2b2',
                            color: '#c53030',
                            padding: '12px',
                            borderRadius: '6px',
                            marginBottom: '20px',
                            fontSize: '14px'
                        }}>
                            ⚠️ {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading || !apiKey.trim()}
                        style={{
                            width: '100%',
                            padding: '12px',
                            backgroundColor: loading || !apiKey.trim() ? '#cbd5e0' : '#4299e1',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '500',
                            cursor: loading || !apiKey.trim() ? 'not-allowed' : 'pointer',
                            transition: 'background-color 0.2s'
                        }}
                    >
                        {loading ? 'Verifying...' : 'Access Admin Panel'}
                    </button>
                </form>

                <div style={{
                    marginTop: '30px',
                    padding: '16px',
                    backgroundColor: '#f7fafc',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#718096'
                }}>
                    <strong>🔑 Need your API key?</strong><br/>
                    Check your secure deployment credentials file:<br/>
                    <code style={{ backgroundColor: '#edf2f7', padding: '2px 4px', borderRadius: '2px' }}>
                        ~/.evothesis-credentials/pixel-management-credentials-*.txt
                    </code>
                </div>
                
                {process.env.NODE_ENV === 'development' && (
                    <div style={{
                        marginTop: '16px',
                        padding: '12px',
                        backgroundColor: '#fffbeb',
                        border: '1px solid #f59e0b',
                        borderRadius: '6px',
                        fontSize: '12px',
                        color: '#92400e'
                    }}>
                        <strong>🚧 Development Mode</strong><br/>
                        Console logs are enabled for debugging
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminLogin;