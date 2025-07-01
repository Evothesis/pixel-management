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
    deployment_type: 'shared',
    vm_hostname: '',
    privacy_level: 'standard',
    ip_collection_enabled: true,
    monthly_event_limit: '',
    billing_rate_per_1k: '0.01'
  });
  
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isEdit) {
      fetchClient();
    }
  }, [clientId, isEdit]);

  const fetchClient = async () => {
    try {
      const response = await axios.get(`/api/v1/admin/clients/${clientId}`);
      setFormData(response.data);
    } catch (error) {
      console.error('Failed to fetch client:', error);
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

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2>{isEdit ? 'Edit Client' : 'Add New Client'}</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Client Name *</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label>Privacy Level *</label>
          <select name="privacy_level" value={formData.privacy_level} onChange={handleChange}>
            <option value="standard">Standard</option>
            <option value="gdpr">GDPR Compliant</option>
            <option value="hipaa">HIPAA Compliant</option>
          </select>
        </div>

        <div className="form-group">
          <label>Deployment Type *</label>
          <select name="deployment_type" value={formData.deployment_type} onChange={handleChange}>
            <option value="shared">Shared Infrastructure</option>
            <option value="dedicated">Dedicated VM</option>
          </select>
        </div>

        {formData.deployment_type === 'dedicated' && (
          <div className="form-group">
            <label>VM Hostname</label>
            <input
              type="text"
              name="vm_hostname"
              value={formData.vm_hostname}
              onChange={handleChange}
              placeholder="e.g., client-analytics.company.com"
            />
          </div>
        )}

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="ip_collection_enabled"
              checked={formData.ip_collection_enabled}
              onChange={handleChange}
            />
            Enable IP Collection
          </label>
        </div>

        <div className="form-group">
          <label>Monthly Event Limit</label>
          <input
            type="number"
            name="monthly_event_limit"
            value={formData.monthly_event_limit}
            onChange={handleChange}
            placeholder="Leave empty for unlimited"
          />
        </div>

        <div className="form-group">
          <label>Billing Rate (per 1000 events)</label>
          <input
            type="number"
            step="0.0001"
            name="billing_rate_per_1k"
            value={formData.billing_rate_per_1k}
            onChange={handleChange}
          />
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
    </div>
  );
}

export default ClientForm;
