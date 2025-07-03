import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

function ClientForm() {
  const { clientId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(clientId);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    client_type: 'end_client',
    owner: 'client_evothesis_admin', // Default to admin owner
    billing_entity: '', // Will default to owner if not specified
    deployment_type: 'shared',
    vm_hostname: '',
    privacy_level: 'standard',
    features: {}
  });
  
  const [domains, setDomains] = useState([]);
  const [newDomain, setNewDomain] = useState({ domain: '', is_primary: false });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isEdit) {
      fetchClient();
      fetchDomains();
    }
  }, [clientId, isEdit]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchClient = async () => {
    try {
      const response = await axios.get(`/api/v1/admin/clients/${clientId}`);
      setFormData(response.data);
    } catch (error) {
      console.error('Failed to fetch client:', error);
    }
  };

  const fetchDomains = async () => {
    try {
      const response = await axios.get(`/api/v1/admin/clients/${clientId}/domains`);
      setDomains(response.data);
    } catch (error) {
      console.error('Failed to fetch domains:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (isEdit) {
        await axios.put(`/api/v1/admin/clients/${clientId}`, formData);
      } else {
        await axios.post('/api/v1/admin/clients', formData);
      }
      navigate('/clients');
    } catch (error) {
      console.error('Failed to save client:', error);
      alert('Failed to save client. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const addDomain = async () => {
    if (!newDomain.domain.trim()) {
      alert('Please enter a domain name');
      return;
    }

    try {
      await axios.post(`/api/v1/admin/clients/${clientId}/domains`, newDomain);
      setNewDomain({ domain: '', is_primary: false });
      fetchDomains(); // Refresh domain list
    } catch (error) {
      console.error('Failed to add domain:', error);
      alert('Failed to add domain. Please try again.');
    }
  };

  const removeDomain = async (domain) => {
    if (!window.confirm(`Are you sure you want to remove domain ${domain}?`)) {
      return;
    }

    try {
      await axios.delete(`/api/v1/admin/clients/${clientId}/domains/${domain}`);
      fetchDomains(); // Refresh domain list
    } catch (error) {
      console.error('Failed to remove domain:', error);
      alert('Failed to remove domain. Please try again.');
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2>{isEdit ? 'Edit Client' : 'Create Client'}</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Company Name *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="client_type">Client Type</label>
          <select
            id="client_type"
            name="client_type"
            value={formData.client_type}
            onChange={handleChange}
          >
            <option value="end_client">End Client</option>
            <option value="agency">Agency</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="privacy_level">Privacy Level *</label>
          <select
            id="privacy_level"
            name="privacy_level"
            value={formData.privacy_level}
            onChange={handleChange}
            required
          >
            <option value="standard">Standard - Basic tracking</option>
            <option value="gdpr">GDPR - IP hashing, consent required</option>
            <option value="hipaa">HIPAA - Enhanced security, audit logging</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="deployment_type">Deployment Type</label>
          <select
            id="deployment_type"
            name="deployment_type"
            value={formData.deployment_type}
            onChange={handleChange}
          >
            <option value="shared">Shared Infrastructure</option>
            <option value="dedicated">Dedicated VM</option>
          </select>
        </div>

        {formData.deployment_type === 'dedicated' && (
          <div className="form-group">
            <label htmlFor="vm_hostname">VM Hostname</label>
            <input
              type="text"
              id="vm_hostname"
              name="vm_hostname"
              value={formData.vm_hostname}
              onChange={handleChange}
              placeholder="analytics.clientcompany.com"
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="billing_entity">Billing Entity</label>
          <input
            type="text"
            id="billing_entity"
            name="billing_entity"
            value={formData.billing_entity}
            onChange={handleChange}
            placeholder="Leave empty to use owner as billing entity"
          />
          <small>Client ID of who receives invoices (defaults to owner)</small>
        </div>

        <div style={{ marginTop: '30px' }}>
          <button type="submit" disabled={loading}>
            {loading ? 'Saving...' : (isEdit ? 'Update Client' : 'Create Client')}
          </button>
          <button type="button" onClick={() => navigate('/clients')}>
            Cancel
          </button>
        </div>
      </form>

      {/* Domain Management Section - Only show for existing clients */}
      {isEdit && (
        <div style={{ marginTop: '40px', borderTop: '1px solid #e2e8f0', paddingTop: '30px' }}>
          <h3>Authorized Domains</h3>
          <p style={{ color: '#666', marginBottom: '20px' }}>
            Add domains that are authorized to use tracking pixels. <strong>Tracking will not work until domains are added.</strong>
          </p>

          {/* Add New Domain */}
          <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
            <h4>Add New Domain</h4>
            <div style={{ display: 'flex', gap: '15px', alignItems: 'end' }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label htmlFor="new_domain">Domain</label>
                <input
                  type="text"
                  id="new_domain"
                  value={newDomain.domain}
                  onChange={(e) => setNewDomain(prev => ({ ...prev, domain: e.target.value }))}
                  placeholder="example.com"
                />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={newDomain.is_primary}
                    onChange={(e) => setNewDomain(prev => ({ ...prev, is_primary: e.target.checked }))}
                  />
                  Primary domain
                </label>
              </div>
              <button type="button" onClick={addDomain}>
                Add Domain
              </button>
            </div>
          </div>

          {/* Domain List */}
          <div>
            <h4>Current Domains ({domains.length})</h4>
            {domains.length === 0 ? (
              <p style={{ color: '#999' }}>No domains added yet. Add domains above to enable tracking.</p>
            ) : (
              <div>
                {domains.map(domain => (
                  <div key={domain.id} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    padding: '15px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    marginBottom: '10px'
                  }}>
                    <div>
                      <strong>{domain.domain}</strong>
                      {domain.is_primary && (
                        <span style={{ 
                          marginLeft: '10px', 
                          padding: '2px 8px', 
                          backgroundColor: '#48bb78', 
                          color: 'white', 
                          borderRadius: '4px', 
                          fontSize: '12px' 
                        }}>
                          PRIMARY
                        </span>
                      )}
                      <div style={{ color: '#666', fontSize: '14px' }}>
                        Added: {new Date(domain.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <button 
                      type="button" 
                      onClick={() => removeDomain(domain.domain)}
                      style={{ backgroundColor: '#e53e3e', color: 'white' }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ClientForm;