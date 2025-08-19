import { rest } from 'msw';

// Mock API handlers for testing
export const handlers = [
  // Health check endpoint
  rest.get('/health', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        service: 'pixel-management',
        database: 'firestore_connected',
        timestamp: new Date().toISOString()
      })
    );
  }),

  // Admin endpoints (require authentication)
  rest.get('/api/v1/admin/clients', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader || authHeader !== 'Bearer test_admin_key_12345') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Invalid API key' })
      );
    }

    // Simulate server error for error testing
    const testError = req.url.searchParams.get('test_error');
    if (testError === 'server_error') {
      return res(
        ctx.status(500),
        ctx.json({ detail: 'Database connection failed' })
      );
    }

    if (testError === 'network_error') {
      return res.networkError('Network connection error');
    }

    return res(
      ctx.status(200),
      ctx.json([
        {
          client_id: 'client_test_001',
          name: 'Test E-commerce Store',
          email: 'admin@teststore.com',
          client_type: 'end_client',
          owner: 'admin@teststore.com',
          privacy_level: 'standard',
          deployment_type: 'shared',
          is_active: true,
          domain_count: 2,
          created_at: new Date().toISOString()
        },
        {
          client_id: 'client_test_002',
          name: 'GDPR Compliant SaaS',
          email: 'admin@gdprsaas.com',
          client_type: 'end_client',
          owner: 'admin@gdprsaas.com',
          privacy_level: 'gdpr',
          deployment_type: 'dedicated',
          is_active: true,
          domain_count: 1,
          created_at: new Date().toISOString()
        },
        {
          client_id: 'client_test_003',
          name: 'Healthcare Analytics Platform',
          email: 'admin@healthanalytics.com',
          client_type: 'enterprise',
          owner: 'admin@healthanalytics.com',
          privacy_level: 'hipaa',
          deployment_type: 'dedicated',
          is_active: true,
          domain_count: 3,
          created_at: new Date().toISOString()
        }
      ])
    );
  }),

  rest.post('/api/v1/admin/clients', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader || authHeader !== 'Bearer test_admin_key_12345') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Invalid API key' })
      );
    }

    // Handle validation errors
    if (req.body.name === 'Duplicate Company') {
      return res(
        ctx.status(409),
        ctx.json({ detail: 'Client name already exists' })
      );
    }

    if (req.body.name === 'Invalid Client') {
      return res(
        ctx.status(422),
        ctx.json({ 
          detail: [
            {
              loc: ['body', 'name'],
              msg: 'Invalid client name format',
              type: 'value_error'
            }
          ]
        })
      );
    }

    // Simulate network/server errors for testing
    if (req.body.name === 'Server Error Client') {
      return res(
        ctx.status(500),
        ctx.json({ detail: 'Internal server error during client creation' })
      );
    }

    // Simulate successful client creation
    return res(
      ctx.status(201),
      ctx.json({
        client_id: 'client_new_123',
        name: req.body.name,
        email: req.body.email,
        client_type: req.body.client_type,
        owner: req.body.owner,
        privacy_level: req.body.privacy_level,
        deployment_type: req.body.deployment_type,
        vm_hostname: req.body.vm_hostname,
        billing_entity: req.body.billing_entity,
        is_active: true,
        domain_count: 0,
        created_at: new Date().toISOString()
      })
    );
  }),

  rest.get('/api/v1/admin/clients/:clientId', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    const { clientId } = req.params;
    
    if (!authHeader || authHeader !== 'Bearer test_admin_key_12345') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Invalid API key' })
      );
    }

    if (clientId === 'client_not_found') {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Client not found' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({
        client_id: clientId,
        name: 'Test Client',
        email: 'test@example.com',
        client_type: 'ecommerce',
        owner: 'test@example.com',
        privacy_level: 'standard',
        deployment_type: 'shared',
        is_active: true,
        domain_count: 2,
        created_at: new Date().toISOString()
      })
    );
  }),

  rest.put('/api/v1/admin/clients/:clientId', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    const { clientId } = req.params;
    
    if (!authHeader || authHeader !== 'Bearer test_admin_key_12345') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Invalid API key' })
      );
    }

    if (clientId === 'client_not_found') {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Client not found' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({
        client_id: clientId,
        name: req.body.name || 'Updated Client',
        email: 'test@example.com',
        client_type: 'ecommerce',
        owner: 'test@example.com',
        privacy_level: req.body.privacy_level || 'standard',
        deployment_type: 'shared',
        is_active: req.body.is_active !== undefined ? req.body.is_active : true,
        domain_count: 2,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
    );
  }),

  // Domain management endpoints
  rest.get('/api/v1/admin/clients/:clientId/domains', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    const { clientId } = req.params;
    
    if (!authHeader || authHeader !== 'Bearer test_admin_key_12345') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Invalid API key' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json([
        {
          id: `${clientId}_example_com`,
          domain: 'example.com',
          is_primary: true,
          created_at: new Date().toISOString()
        },
        {
          id: `${clientId}_app_example_com`,
          domain: 'app.example.com',
          is_primary: false,
          created_at: new Date().toISOString()
        }
      ])
    );
  }),

  rest.post('/api/v1/admin/clients/:clientId/domains', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    const { clientId } = req.params;
    
    if (!authHeader || authHeader !== 'Bearer test_admin_key_12345') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Invalid API key' })
      );
    }

    // Test various domain validation scenarios
    if (req.body.domain === 'duplicate.com') {
      return res(
        ctx.status(409),
        ctx.json({ detail: 'Domain already assigned to another client' })
      );
    }

    if (req.body.domain === 'invalid-domain') {
      return res(
        ctx.status(422),
        ctx.json({ detail: 'Invalid domain format' })
      );
    }

    if (req.body.domain === 'server-error.com') {
      return res(
        ctx.status(500),
        ctx.json({ detail: 'Internal server error while adding domain' })
      );
    }

    if (!req.body.domain || req.body.domain.trim() === '') {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Domain name is required' })
      );
    }

    return res(
      ctx.status(201),
      ctx.json({
        id: `${clientId}_${req.body.domain.replace(/\./g, '_')}`,
        domain: req.body.domain,
        is_primary: req.body.is_primary || false,
        created_at: new Date().toISOString()
      })
    );
  }),

  rest.delete('/api/v1/admin/clients/:clientId', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    const { clientId } = req.params;
    
    if (!authHeader || authHeader !== 'Bearer test_admin_key_12345') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Invalid API key' })
      );
    }

    if (clientId === 'client_not_found') {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Client not found' })
      );
    }

    if (clientId === 'client_delete_error') {
      return res(
        ctx.status(500),
        ctx.json({ detail: 'Internal server error during deletion' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({ message: 'Client deleted successfully' })
    );
  }),

  rest.delete('/api/v1/admin/clients/:clientId/domains/:domain', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader || authHeader !== 'Bearer test_admin_key_12345') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Invalid API key' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({ message: 'Domain removed successfully' })
    );
  }),

  // Configuration endpoints (public)
  rest.get('/api/v1/config/domain/:domain', (req, res, ctx) => {
    const { domain } = req.params;
    
    if (domain === 'unauthorized.com') {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Domain not authorized' })
      );
    }

    return res(
      ctx.status(200),
      ctx.json({
        client_id: 'client_test_001',
        privacy_level: 'standard',
        ip_collection: {
          enabled: true,
          hash_required: false,
          salt: null
        },
        consent: {
          required: false,
          default_behavior: 'allow'
        },
        features: {
          analytics: true,
          conversion_tracking: true
        },
        deployment: {
          type: 'shared',
          hostname: null
        }
      })
    );
  }),

  // Error scenarios for testing
  rest.get('/api/v1/admin/error-test', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({ detail: 'Internal server error' })
    );
  }),

  // Network error simulation
  rest.get('/api/v1/admin/network-error', (req, res, ctx) => {
    return res.networkError('Network connection error');
  })
];

// Helper function to create authentication error response
export const createAuthError = () => {
  return {
    status: 403,
    json: { detail: 'Invalid API key' }
  };
};

// Helper function to create validation error response
export const createValidationError = (field, message) => {
  return {
    status: 422,
    json: { 
      detail: [
        {
          loc: ['body', field],
          msg: message,
          type: 'value_error'
        }
      ]
    }
  };
};

// Helper function to create delayed response for testing loading states
export const createDelayedResponse = (data, delay = 100) => {
  return new Promise(resolve => {
    setTimeout(() => resolve(data), delay);
  });
};

// Helper function to create network timeout response
export const createTimeoutError = () => {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error('Request timeout')), 5000);
  });
};

// Mock data generators for consistent testing
export const generateMockClient = (overrides = {}) => {
  const defaults = {
    client_id: 'client_mock_001',
    name: 'Mock Test Client',
    email: 'test@mockclient.com',
    client_type: 'end_client',
    owner: 'test@mockclient.com',
    privacy_level: 'standard',
    deployment_type: 'shared',
    vm_hostname: null,
    billing_entity: '',
    is_active: true,
    domain_count: 0,
    created_at: new Date().toISOString()
  };
  
  return { ...defaults, ...overrides };
};

export const generateMockDomain = (clientId, overrides = {}) => {
  const defaults = {
    id: `${clientId}_example_com`,
    domain: 'example.com',
    is_primary: false,
    created_at: new Date().toISOString()
  };
  
  return { ...defaults, ...overrides };
};

// Performance testing helpers
export const generateLargeClientDataset = (count = 100) => {
  return Array.from({ length: count }, (_, index) => {
    const clientIndex = index + 1;
    return generateMockClient({
      client_id: `client_perf_${String(clientIndex).padStart(3, '0')}`,
      name: `Performance Test Client ${clientIndex}`,
      email: `client${clientIndex}@perftest.com`,
      privacy_level: ['standard', 'gdpr', 'hipaa'][index % 3],
      deployment_type: index % 2 === 0 ? 'shared' : 'dedicated',
      domain_count: Math.floor(Math.random() * 5)
    });
  });
};