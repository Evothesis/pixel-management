// frontend/src/components/ClientList.js - Updated for secure authentication
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';

const ClientList = () => {
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchClients();
    }, []);

    const fetchClients = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await apiService.clients.list();
            setClients(response.data);
        } catch (error) {
            console.error('Failed to fetch clients:', error);
            setError(error.response?.data?.detail || 'Failed to load clients');
        } finally {
            setLoading(false);
        }
    };

    const getPrivacyLevelColor = (level) => {
        switch (level) {
            case 'standard': return '#4299e1';
            case 'gdpr': return '#f6ad55';
            case 'hipaa': return '#e53e3e';
            default: return '#718096';
        }
    };

    const getDeploymentTypeIcon = (type) => {
        return type === 'dedicated' ? '🏗️' : '🏢';
    };

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: '40px' }}>
                <div style={{ fontSize: '18px', color: '#718096' }}>
                    Loading clients...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{
                backgroundColor: '#fed7d7',
                border: '1px solid #feb2b2',
                color: '#c53030',
                padding: '16px',
                borderRadius: '8px',
                margin: '20px'
            }}>
                <strong>❌ Error loading clients:</strong> {error}
                <button 
                    onClick={fetchClients}
                    style={{
                        marginLeft: '10px',
                        backgroundColor: '#c53030',
                        color: 'white',
                        border: 'none',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px'
            }}>
                <h1 style={{ margin: 0, color: '#2d3748' }}>
                    📊 Client Management
                </h1>
                <Link 
                    to="/admin/clients/new"
                    style={{
                        backgroundColor: '#4299e1',
                        color: 'white',
                        padding: '10px 16px',
                        textDecoration: 'none',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: '500'
                    }}
                >
                    ➕ Create New Client
                </Link>
            </div>

            {clients.length === 0 ? (
                <div style={{
                    backgroundColor: '#f7fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '40px',
                    textAlign: 'center'
                }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
                    <h3 style={{ margin: '0 0 8px 0', color: '#4a5568' }}>No clients yet</h3>
                    <p style={{ margin: '0 0 20px 0', color: '#718096' }}>
                        Create your first client to start managing tracking configurations.
                    </p>
                    <Link 
                        to="/admin/clients/new"
                        style={{
                            backgroundColor: '#4299e1',
                            color: 'white',
                            padding: '12px 20px',
                            textDecoration: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '500'
                        }}
                    >
                        Create First Client
                    </Link>
                </div>
            ) : (
                <div style={{
                    display: 'grid',
                    gap: '16px',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))'
                }}>
                    {clients.map(client => (
                        <div 
                            key={client.client_id}
                            style={{
                                backgroundColor: 'white',
                                border: '1px solid #e2e8f0',
                                borderRadius: '8px',
                                padding: '20px',
                                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                            }}
                        >
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'flex-start',
                                marginBottom: '12px'
                            }}>
                                <div>
                                    <h3 style={{ 
                                        margin: '0 0 4px 0', 
                                        color: '#2d3748',
                                        fontSize: '16px' 
                                    }}>
                                        {client.name}
                                    </h3>
                                    <div style={{ 
                                        fontSize: '12px', 
                                        color: '#718096',
                                        fontFamily: 'monospace'
                                    }}>
                                        {client.client_id}
                                    </div>
                                </div>
                                <div style={{
                                    backgroundColor: getPrivacyLevelColor(client.privacy_level),
                                    color: 'white',
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontWeight: '500'
                                }}>
                                    {client.privacy_level.toUpperCase()}
                                </div>
                            </div>

                            <div style={{ 
                                fontSize: '14px', 
                                color: '#4a5568',
                                marginBottom: '12px'
                            }}>
                                {client.email && (
                                    <div style={{ marginBottom: '4px' }}>
                                        📧 {client.email}
                                    </div>
                                )}
                                <div style={{ marginBottom: '4px' }}>
                                    {getDeploymentTypeIcon(client.deployment_type)} {client.deployment_type}
                                </div>
                                <div>
                                    🌐 {client.domain_count} domain{client.domain_count !== 1 ? 's' : ''}
                                </div>
                            </div>

                            <div style={{
                                display: 'flex',
                                gap: '8px',
                                marginTop: '16px'
                            }}>
                                <Link
                                    to={`/admin/clients/${client.client_id}/edit`}
                                    style={{
                                        flex: 1,
                                        backgroundColor: '#4299e1',
                                        color: 'white',
                                        padding: '8px 12px',
                                        textDecoration: 'none',
                                        borderRadius: '4px',
                                        fontSize: '12px',
                                        textAlign: 'center',
                                        fontWeight: '500'
                                    }}
                                >
                                    ⚙️ Edit
                                </Link>
                                <button
                                    onClick={() => {
                                        // TODO: Implement domain management
                                        alert(`Domain management for ${client.name} - Coming soon!`);
                                    }}
                                    style={{
                                        flex: 1,
                                        backgroundColor: '#38a169',
                                        color: 'white',
                                        border: 'none',
                                        padding: '8px 12px',
                                        borderRadius: '4px',
                                        fontSize: '12px',
                                        cursor: 'pointer',
                                        fontWeight: '500'
                                    }}
                                >
                                    🌐 Domains
                                </button>
                            </div>

                            {client.client_type === 'admin' && (
                                <div style={{
                                    marginTop: '8px',
                                    padding: '6px 8px',
                                    backgroundColor: '#fef5e7',
                                    border: '1px solid #f6ad55',
                                    borderRadius: '4px',
                                    fontSize: '11px',
                                    color: '#c05621'
                                }}>
                                    👑 Admin Client
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ClientList;