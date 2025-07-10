// frontend/src/components/AdminLogin.js - Secure API Key Login
import React, { useState } from 'react';
import { apiService } from '../services/api';

const AdminLogin = ({ onLoginSuccess }) => {
    const [apiKey, setApiKey] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Validate API key by attempting to list clients
            const testResponse = await apiService.testApiKey(apiKey);
            
            if (testResponse.success) {
                // Store API key securely in session storage
                sessionStorage.setItem('admin_api_key', apiKey);
                
                // Notify parent component of successful login
                onLoginSuccess(apiKey);
            } else {
                setError('Invalid API key. Please check your credentials.');
            }
        } catch (error) {
            if (error.response?.status === 401) {
                setError('Invalid API key. Access denied.');
            } else {
                setError('Connection error. Please try again.');
            }
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
                            style={{
                                width: '100%',
                                padding: '12px',
                                border: '1px solid #e2e8f0',
                                borderRadius: '6px',
                                fontSize: '14px',
                                boxSizing: 'border-box',
                                backgroundColor: loading ? '#f7fafc' : 'white'
                            }}
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
                    Contact your system administrator or check your deployment credentials file.
                </div>
            </div>
        </div>
    );
};

export default AdminLogin;
