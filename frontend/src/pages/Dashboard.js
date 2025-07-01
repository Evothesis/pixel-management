import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Dashboard() {
  const [stats, setStats] = useState({
    totalClients: 0,
    activeClients: 0,
    privacyLevels: { standard: 0, gdpr: 0, hipaa: 0 }
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/v1/admin/clients');
      const clients = response.data;
      
      const totalClients = clients.length;
      const activeClients = clients.filter(c => c.is_active).length;
      
      const privacyLevels = clients.reduce((acc, client) => {
        acc[client.privacy_level] = (acc[client.privacy_level] || 0) + 1;
        return acc;
      }, { standard: 0, gdpr: 0, hipaa: 0 });

      setStats({ totalClients, activeClients, privacyLevels });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  return (
    <div>
      <h2>Pixel Management Dashboard</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', margin: '20px 0' }}>
        <div className="client-card">
          <h3>Total Clients</h3>
          <p style={{ fontSize: '2em', margin: '10px 0' }}>{stats.totalClients}</p>
        </div>
        
        <div className="client-card">
          <h3>Active Clients</h3>
          <p style={{ fontSize: '2em', margin: '10px 0' }}>{stats.activeClients}</p>
        </div>
        
        <div className="client-card">
          <h3>Privacy Levels</h3>
          <p>Standard: {stats.privacyLevels.standard}</p>
          <p>GDPR: {stats.privacyLevels.gdpr}</p>
          <p>HIPAA: {stats.privacyLevels.hipaa}</p>
        </div>
      </div>
      
      <div style={{ marginTop: '40px' }}>
        <h3>Quick Actions</h3>
        <button onClick={() => window.location.href = '/clients/new'}>
          Add New Client
        </button>
        <button onClick={() => window.location.href = '/clients'}>
          Manage Clients
        </button>
      </div>
    </div>
  );
}

export default Dashboard;
