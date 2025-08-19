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

    return res(
      ctx.status(200),
      ctx.json([
        {
          client_id: 'client_test_001',
          name: 'Test E-commerce Store',
          email: 'admin@teststore.com',
          client_type: 'ecommerce',
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
          client_type: 'saas',
          owner: 'admin@gdprsaas.com',
          privacy_level: 'gdpr',
          deployment_type: 'dedicated',
          is_active: true,
          domain_count: 1,
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

    if (req.body.domain === 'duplicate.com') {
      return res(
        ctx.status(409),
        ctx.json({ detail: 'Domain already assigned to another client' })
      );
    }

    return res(
      ctx.status(201),
      ctx.json({
        id: `${clientId}_${req.body.domain.replace('.', '_')}`,
        domain: req.body.domain,
        is_primary: req.body.is_primary || false,
        created_at: new Date().toISOString()
      })
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