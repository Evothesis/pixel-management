/**
 * Admin dashboard overview component with system statistics and quick actions.
 * 
 * This component serves as the main landing page for authenticated admin users,
 * providing an overview of system statistics, recent activity, and quick access
 * to common management functions. It displays client counts, domain statistics,
 * and navigation to detailed management interfaces.
 * 
 * Key features:
 * - Real-time system statistics display (client count, domain count)
 * - Quick action buttons for common admin tasks
 * - Recent activity summary and system health indicators
 * - Responsive grid layout with professional styling
 * - Integration with API service for live data fetching
 * - Error handling and loading states for improved UX
 * 
 * The dashboard provides a comprehensive overview of the pixel management
 * system status and serves as the central hub for admin operations.
 */

// frontend/src/components/Dashboard.js - Updated for secure authentication
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';

const Dashboard = () => {
    const [stats, setStats] = useState({
        totalClients: 0,
        activeClients: 0,
        privacyLevels: { standard: 0, gdpr: 0, hipaa: 0 }
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await apiService.clients.list();
            const clients = response.data;
            
            const totalClients = clients.length;
            const activeClients = clients.filter(c => c.is_active !== false).length; // Count active clients
            
            const privacyLevels = clients.reduce((acc, client) => {
                acc[client.privacy_level] = (acc[client.privacy_level] || 0) + 1;
                return acc;
            }, { standard: 0, gdpr: 0, hipaa: 0 });

            setStats({ totalClients, activeClients, privacyLevels });
        } catch (error) {
            console.error('Failed to fetch stats:', error);
            setError(error.response?.data?.detail || 'Failed to load dashboard data');
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

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: '40px' }}>
                <div style={{ fontSize: '18px', color: '#718096' }}>
                    Loading dashboard...
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
                <strong>❌ Error loading dashboard:</strong> {error}
                <button 
                    onClick={fetchStats}
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
            <div style={{ marginBottom: '30px' }}>
                <h1 style={{ margin: '0 0 8px 0', color: '#2d3748', fontSize: '24px' }}>
                    📊 Pixel Management Dashboard
                </h1>
                <p style={{ margin: 0, color: '#718096', fontSize: '16px' }}>
                    Overview of your client configurations and tracking infrastructure
                </p>
            </div>
            
            {/* Stats Grid */}
            <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
                gap: '20px', 
                marginBottom: '40px' 
            }}>
                {/* Total Clients Card */}
                <div style={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '24px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                    <h3 style={{ 
                        margin: '0 0 12px 0', 
                        color: '#4a5568',
                        fontSize: '16px',
                        fontWeight: '500'
                    }}>
                        👥 Total Clients
                    </h3>
                    <p style={{ 
                        fontSize: '3em', 
                        margin: '10px 0',
                        color: '#2d3748',
                        fontWeight: 'bold',
                        lineHeight: '1'
                    }}>
                        {stats.totalClients}
                    </p>
                    <p style={{ 
                        margin: 0, 
                        color: '#718096',
                        fontSize: '14px' 
                    }}>
                        Configured clients
                    </p>
                </div>
                
                {/* Active Clients Card */}
                <div style={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '24px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                    <h3 style={{ 
                        margin: '0 0 12px 0', 
                        color: '#4a5568',
                        fontSize: '16px',
                        fontWeight: '500'
                    }}>
                        ✅ Active Clients
                    </h3>
                    <p style={{ 
                        fontSize: '3em', 
                        margin: '10px 0',
                        color: '#38a169',
                        fontWeight: 'bold',
                        lineHeight: '1'
                    }}>
                        {stats.activeClients}
                    </p>
                    <p style={{ 
                        margin: 0, 
                        color: '#718096',
                        fontSize: '14px' 
                    }}>
                        Ready for tracking
                    </p>
                </div>
                
                {/* Privacy Levels Card */}
                <div style={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '24px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                    <h3 style={{ 
                        margin: '0 0 16px 0', 
                        color: '#4a5568',
                        fontSize: '16px',
                        fontWeight: '500'
                    }}>
                        🔐 Privacy Levels
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {Object.entries(stats.privacyLevels).map(([level, count]) => (
                            <div key={level} style={{ 
                                display: 'flex', 
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '6px 0'
                            }}>
                                <span style={{ 
                                    color: '#4a5568',
                                    fontSize: '14px',
                                    fontWeight: '500'
                                }}>
                                    {level.charAt(0).toUpperCase() + level.slice(1)}:
                                </span>
                                <span style={{ 
                                    backgroundColor: getPrivacyLevelColor(level),
                                    color: 'white',
                                    padding: '4px 8px',
                                    borderRadius: '12px',
                                    fontSize: '12px',
                                    fontWeight: '500',
                                    minWidth: '24px',
                                    textAlign: 'center'
                                }}>
                                    {count}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
            
            {/* Quick Actions */}
            <div style={{
                backgroundColor: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '24px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}>
                <h3 style={{ 
                    margin: '0 0 20px 0', 
                    color: '#2d3748',
                    fontSize: '18px' 
                }}>
                    🚀 Quick Actions
                </h3>
                <div style={{ 
                    display: 'flex', 
                    gap: '16px',
                    flexWrap: 'wrap'
                }}>
                    <Link 
                        to="/admin/clients/new"
                        style={{
                            backgroundColor: '#4299e1',
                            color: 'white',
                            padding: '12px 20px',
                            textDecoration: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '500',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                        }}
                    >
                        ➕ Add New Client
                    </Link>
                    <Link 
                        to="/admin/clients"
                        style={{
                            backgroundColor: '#38a169',
                            color: 'white',
                            padding: '12px 20px',
                            textDecoration: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '500',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                        }}
                    >
                        📋 Manage Clients
                    </Link>
                    <button
                        onClick={fetchStats}
                        style={{
                            backgroundColor: '#805ad5',
                            color: 'white',
                            border: 'none',
                            padding: '12px 20px',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '500',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                        }}
                    >
                        🔄 Refresh Data
                    </button>
                </div>
            </div>

            {/* System Status */}
            {stats.totalClients === 0 && (
                <div style={{
                    backgroundColor: '#fef5e7',
                    border: '1px solid #f6ad55',
                    borderRadius: '8px',
                    padding: '20px',
                    marginTop: '20px',
                    textAlign: 'center'
                }}>
                    <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎯</div>
                    <h3 style={{ margin: '0 0 8px 0', color: '#744210' }}>
                        Ready to Get Started?
                    </h3>
                    <p style={{ margin: '0 0 16px 0', color: '#744210' }}>
                        Create your first client to begin tracking configuration.
                    </p>
                    <Link 
                        to="/admin/clients/new"
                        style={{
                            backgroundColor: '#d69e2e',
                            color: 'white',
                            padding: '10px 20px',
                            textDecoration: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '500'
                        }}
                    >
                        Create First Client
                    </Link>
                </div>
            )}
        </div>
    );
};

export default Dashboard;