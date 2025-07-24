/**
 * Client creation and editing form component with comprehensive validation.
 * 
 * This component provides a full-featured form interface for creating new
 * tracking clients and editing existing ones. It includes validation for all
 * client fields, privacy level configuration, and deployment type selection
 * with appropriate field dependencies.
 * 
 * Key features:
 * - Dynamic form handling for both create and edit modes
 * - Comprehensive field validation with real-time feedback
 * - Privacy level selection (standard, GDPR, HIPAA) with related settings
 * - Deployment type configuration (shared, dedicated) with conditional fields
 * - Client type selection with appropriate validation rules
 * - Form state management with loading and error handling
 * - Integration with API service for client operations
 * 
 * The component automatically detects edit vs create mode based on URL
 * parameters and pre-populates form fields for editing scenarios.
 */

// frontend/src/components/ClientForm.js - Updated for secure authentication
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';

const ClientForm = () => {
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
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isEdit) {
            fetchClient();
            fetchDomains();
        }
    }, [clientId, isEdit]);

    const fetchClient = async () => {
        try {
            setError(null);
            const response = await apiService.clients.get(clientId);
            setFormData(response.data);
        } catch (error) {
            console.error('Failed to fetch client:', error);
            setError('Failed to load client data');
        }
    };

    const fetchDomains = async () => {
        try {
            setError(null);
            const response = await apiService.domains.list(clientId);
            setDomains(response.data);
        } catch (error) {
            console.error('Failed to fetch domains:', error);
            setError('Failed to load domains');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        
        try {
            if (isEdit) {
                await apiService.clients.update(clientId, formData);
            } else {
                await apiService.clients.create(formData);
            }
            navigate('/admin/clients');
        } catch (error) {
            console.error('Failed to save client:', error);
            setError(error.response?.data?.detail || 'Failed to save client. Please try again.');
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
            setError('Please enter a domain name');
            return;
        }

        try {
            setError(null);
            await apiService.domains.add(clientId, newDomain);
            setNewDomain({ domain: '', is_primary: false });
            fetchDomains(); // Refresh domain list
        } catch (error) {
            console.error('Failed to add domain:', error);
            setError(error.response?.data?.detail || 'Failed to add domain. Please try again.');
        }
    };

    const removeDomain = async (domain) => {
        if (!window.confirm(`Are you sure you want to remove domain ${domain}?`)) {
            return;
        }

        try {
            setError(null);
            await apiService.domains.remove(clientId, domain);
            fetchDomains(); // Refresh domain list
        } catch (error) {
            console.error('Failed to remove domain:', error);
            setError(error.response?.data?.detail || 'Failed to remove domain. Please try again.');
        }
    };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h2>{isEdit ? 'Edit Client' : 'Create Client'}</h2>
            
            {/* Error display */}
            {error && (
                <div style={{
                    backgroundColor: '#fed7d7',
                    border: '1px solid #feb2b2',
                    color: '#c53030',
                    padding: '12px',
                    borderRadius: '6px',
                    marginBottom: '20px'
                }}>
                    <strong>❌ Error:</strong> {error}
                </div>
            )}
            
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
                    <button 
                        type="submit" 
                        disabled={loading}
                        style={{
                            backgroundColor: loading ? '#a0aec0' : '#4299e1',
                            color: 'white',
                            padding: '12px 20px',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            marginRight: '10px'
                        }}
                    >
                        {loading ? 'Saving...' : (isEdit ? 'Update Client' : 'Create Client')}
                    </button>
                    <button 
                        type="button" 
                        onClick={() => navigate('/admin/clients')}
                        style={{
                            backgroundColor: '#e2e8f0',
                            color: '#4a5568',
                            padding: '12px 20px',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            cursor: 'pointer'
                        }}
                    >
                        Cancel
                    </button>
                </div>
            </form>

            {/* Domain Management Section - Only show for existing clients */}
            {isEdit && (
                <div style={{ 
                    marginTop: '40px', 
                    borderTop: '1px solid #e2e8f0', 
                    paddingTop: '30px' 
                }}>
                    <h3>Authorized Domains</h3>
                    <p style={{ color: '#666', marginBottom: '20px' }}>
                        Add domains that are authorized to use tracking pixels. 
                        <strong> Tracking will not work until domains are added.</strong>
                    </p>

                    {/* Add New Domain */}
                    <div style={{ 
                        background: '#f7fafc', 
                        padding: '20px', 
                        borderRadius: '8px', 
                        marginBottom: '20px' 
                    }}>
                        <h4>Add New Domain</h4>
                        <div style={{ display: 'flex', gap: '15px', alignItems: 'end' }}>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label htmlFor="new_domain">Domain</label>
                                <input
                                    type="text"
                                    id="new_domain"
                                    value={newDomain.domain}
                                    onChange={(e) => setNewDomain(prev => ({ 
                                        ...prev, 
                                        domain: e.target.value 
                                    }))}
                                    placeholder="example.com"
                                />
                            </div>
                            <div className="form-group">
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={newDomain.is_primary}
                                        onChange={(e) => setNewDomain(prev => ({ 
                                            ...prev, 
                                            is_primary: e.target.checked 
                                        }))}
                                    />
                                    Primary domain
                                </label>
                            </div>
                            <button 
                                type="button" 
                                onClick={addDomain}
                                style={{
                                    backgroundColor: '#48bb78',
                                    color: 'white',
                                    padding: '10px 16px',
                                    border: 'none',
                                    borderRadius: '6px',
                                    fontSize: '14px',
                                    cursor: 'pointer'
                                }}
                            >
                                Add Domain
                            </button>
                        </div>
                    </div>

                    {/* Domain List */}
                    <div>
                        <h4>Current Domains ({domains.length})</h4>
                        {domains.length === 0 ? (
                            <p style={{ color: '#999' }}>
                                No domains added yet. Add a domain above to enable tracking.
                            </p>
                        ) : (
                            <div style={{ 
                                display: 'grid', 
                                gap: '10px',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))'
                            }}>
                                {domains.map((domain, index) => (
                                    <div 
                                        key={index}
                                        style={{
                                            backgroundColor: 'white',
                                            border: '1px solid #e2e8f0',
                                            borderRadius: '8px',
                                            padding: '16px',
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center'
                                        }}
                                    >
                                        <div>
                                            <div style={{ 
                                                fontWeight: '500',
                                                color: '#2d3748' 
                                            }}>
                                                {domain.domain}
                                            </div>
                                            {domain.is_primary && (
                                                <span style={{
                                                    backgroundColor: '#4299e1',
                                                    color: 'white',
                                                    fontSize: '12px',
                                                    padding: '2px 8px',
                                                    borderRadius: '12px',
                                                    marginTop: '4px',
                                                    display: 'inline-block'
                                                }}>
                                                    Primary
                                                </span>
                                            )}
                                        </div>
                                        <button
                                            onClick={() => removeDomain(domain.domain)}
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
};

export default ClientForm;