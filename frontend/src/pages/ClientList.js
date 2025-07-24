/**
 * Legacy client list page component (use components/ClientList.js instead).
 * 
 * This file appears to be an alternative implementation of the client list
 * functionality that directly imports axios rather than using the centralized
 * API service. The active client list implementation is located in the
 * components directory and integrates properly with the authentication system.
 * 
 * This file may be a backup or alternative implementation that should be
 * evaluated for removal or consolidation with the main client list component.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ClientList() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get('/api/v1/admin/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading clients...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Client Management</h2>
        <button onClick={() => window.location.href = '/clients/new'}>
          Add New Client
        </button>
      </div>
      
      {clients.length === 0 ? (
        <p>No clients found. Create your first client to get started.</p>
      ) : (
        <div>
          {clients.map(client => (
            <div key={client.client_id} className="client-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3>{client.name}</h3>
                  <p><strong>Client ID:</strong> {client.client_id}</p>
                  <p><strong>Email:</strong> {client.email || 'Not provided'}</p>
                  <p><strong>Deployment:</strong> {client.deployment_type}</p>
                  {client.vm_hostname && (
                    <p><strong>VM Hostname:</strong> {client.vm_hostname}</p>
                  )}
                  <p><strong>Created:</strong> {new Date(client.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <span className={`privacy-badge privacy-${client.privacy_level}`}>
                    {client.privacy_level}
                  </span>
                  <div style={{ marginTop: '10px' }}>
                    <button onClick={() => window.location.href = `/clients/${client.client_id}/edit`}>
                      Edit
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ClientList;
