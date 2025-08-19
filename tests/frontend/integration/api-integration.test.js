/**
 * Frontend API Integration Tests - Phase 7
 * 
 * Comprehensive testing of API service integration including error handling,
 * network failure scenarios, retry mechanisms, response parsing, data transformation,
 * and authentication token management in real-world usage scenarios.
 * 
 * This test suite covers the complete API service integration including
 * error boundaries, network resilience, authentication handling, and
 * response transformation across all API endpoints.
 * 
 * Coverage Requirements:
 * - API service integration with error handling
 * - Network failure scenarios and retry mechanisms
 * - API response parsing and data transformation
 * - Authentication token management in API calls
 * 
 * Test Categories:
 * 1. API service error handling and network resilience
 * 2. Authentication integration and token management
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../../../src/mocks/server';
import { apiService } from '../../../src/services/api';
import App from '../../../src/App';

// Test the real API service (not mocked) for integration testing
describe('API Service Integration Tests', () => {
  let mockSessionStorage = {};
  let originalAxios;
  
  beforeEach(() => {
    // Mock sessionStorage
    mockSessionStorage = {
      'admin_api_key': 'test_integration_key_12345'
    };
    
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn((key) => mockSessionStorage[key] || null),
        setItem: jest.fn((key, value) => {
          mockSessionStorage[key] = value;
        }),
        removeItem: jest.fn((key) => {
          delete mockSessionStorage[key];
        }),
        clear: jest.fn(() => {
          mockSessionStorage = {};
        })
      },
      writable: true
    });
    
    // Mock window.location for redirect handling
    delete window.location;
    window.location = { 
      reload: jest.fn(),
      href: '',
      origin: 'http://localhost:3000'
    };
    
    // Reset MSW server to ensure clean state
    server.resetHandlers();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('API Service Error Handling and Network Resilience', () => {
    test('should handle comprehensive error scenarios across multiple API endpoints', async () => {
      const user = userEvent.setup();
      
      // Configure MSW server for different error scenarios
      server.use(
        // Authentication endpoint - success
        rest.get('/api/v1/admin/clients', (req, res, ctx) => {
          const authHeader = req.headers.get('Authorization');
          if (authHeader === 'Bearer test_integration_key_12345') {
            // First call - network error simulation
            if (req.url.searchParams.get('attempt') !== '2') {
              return res.networkError('Network connection failed');
            }
            // Second call - success
            return res(
              ctx.status(200),
              ctx.json([
                {
                  client_id: 'client_network_test',
                  name: 'Network Test Client',
                  email: 'network@test.com',
                  client_type: 'ecommerce',
                  privacy_level: 'standard',
                  is_active: true
                }
              ])
            );
          }
          return res(ctx.status(401), ctx.json({ detail: 'Unauthorized' }));
        }),
        
        // Client creation - server error then success
        rest.post('/api/v1/admin/clients', (req, res, ctx) => {
          const authHeader = req.headers.get('Authorization');
          if (authHeader !== 'Bearer test_integration_key_12345') {
            return res(ctx.status(401), ctx.json({ detail: 'Unauthorized' }));
          }
          
          // Simulate server error on first attempt
          if (req.body.name === 'Server Error Test') {
            return res(
              ctx.status(500),
              ctx.json({ detail: 'Internal server error during client creation' })
            );
          }
          
          // Simulate validation error
          if (req.body.email === 'invalid-email') {
            return res(
              ctx.status(422),
              ctx.json({
                detail: [
                  {
                    loc: ['body', 'email'],
                    msg: 'Invalid email format',
                    type: 'value_error'
                  }
                ]
              })
            );
          }
          
          // Success
          return res(
            ctx.status(201),
            ctx.json({
              client_id: 'client_error_recovery',
              name: req.body.name,
              email: req.body.email,
              client_type: req.body.client_type,
              privacy_level: req.body.privacy_level,
              is_active: true
            })
          );
        }),
        
        // Timeout simulation
        rest.get('/api/v1/admin/clients/:clientId', (req, res, ctx) => {
          return res(
            ctx.delay(15000) // Exceed timeout
          );
        })
      );
      
      render(
        <MemoryRouter initialEntries={['/admin/clients']}>
          <App />
        </MemoryRouter>
      );
      
      // Wait for initial auth and navigation
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      });
      
      // SCENARIO 1: Network error handling and recovery
      // The first API call should fail with network error
      await waitFor(() => {
        expect(screen.getByText(/error loading clients/i)).toBeInTheDocument();
      });
      
      // Retry should work (simulate second attempt)
      const retryButton = screen.getByRole('button', { name: /retry/i });
      
      // Mock the retry attempt with success parameter
      server.use(
        rest.get('/api/v1/admin/clients', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json([
              {
                client_id: 'client_network_test',
                name: 'Network Test Client',
                email: 'network@test.com',
                client_type: 'ecommerce',
                privacy_level: 'standard',
                is_active: true
              }
            ])
          );
        })
      );
      
      await user.click(retryButton);
      
      await waitFor(() => {
        expect(screen.getByText(/network test client/i)).toBeInTheDocument();
        expect(screen.queryByText(/error loading clients/i)).not.toBeInTheDocument();
      });
      
      // SCENARIO 2: Server error during client creation
      const createClientButton = screen.getByRole('button', { name: /create new client/i });
      await user.click(createClientButton);
      
      await waitFor(() => {
        expect(screen.getByText(/create new client/i)).toBeInTheDocument();
      });
      
      // Fill form with data that triggers server error
      const nameInput = screen.getByLabelText(/client name/i);
      const emailInput = screen.getByLabelText(/email address/i);
      const clientTypeSelect = screen.getByLabelText(/client type/i);
      
      await user.type(nameInput, 'Server Error Test');
      await user.type(emailInput, 'servererror@test.com');
      await user.selectOptions(clientTypeSelect, 'ecommerce');
      
      const createButton = screen.getByRole('button', { name: /create client/i });
      await user.click(createButton);
      
      // Should show server error
      await waitFor(() => {
        expect(screen.getByText(/internal server error/i)).toBeInTheDocument();
      });
      
      // Form should remain populated for retry
      expect(screen.getByDisplayValue('Server Error Test')).toBeInTheDocument();
      
      // SCENARIO 3: Validation error handling
      await user.clear(nameInput);
      await user.clear(emailInput);
      await user.type(nameInput, 'Validation Test Client');
      await user.type(emailInput, 'invalid-email'); // Invalid format
      
      await user.click(createButton);
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
      });
      
      // Correct the error and retry
      await user.clear(emailInput);
      await user.type(emailInput, 'valid@test.com');
      
      await user.click(createButton);
      
      // Should succeed
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    test('should handle API timeout scenarios and provide appropriate feedback', async () => {
      const user = userEvent.setup();
      
      // Configure MSW for timeout scenarios
      server.use(
        rest.get('/api/v1/admin/clients', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json([
              {
                client_id: 'client_timeout_test',
                name: 'Timeout Test Client',
                email: 'timeout@test.com'
              }
            ])
          );
        }),
        
        // Simulate timeout on client detail fetch
        rest.get('/api/v1/admin/clients/:clientId', (req, res, ctx) => {
          return res(
            ctx.delay(12000) // Exceed 10 second timeout
          );
        })
      );
      
      render(
        <MemoryRouter initialEntries={['/admin/clients']}>
          <App />
        </MemoryRouter>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/timeout test client/i)).toBeInTheDocument();
      });
      
      // Try to edit client (will trigger timeout)
      const clientRow = screen.getByText(/timeout test client/i).closest('tr');
      const editButton = clientRow.querySelector('button[title*="edit"], button[aria-label*="edit"]') || 
                        clientRow.querySelector('button:has(svg)') ||
                        screen.getByRole('button', { name: /edit/i });
      
      await user.click(editButton);
      
      // Should show loading state first
      await waitFor(() => {
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
      });
      
      // Should show timeout error after delay
      await waitFor(() => {
        expect(screen.getByText(/timeout|timed out|took too long/i)).toBeInTheDocument();
      }, { timeout: 15000 });
      
      // Should provide option to try again
      const tryAgainButton = screen.getByRole('button', { name: /try again|retry/i });
      expect(tryAgainButton).toBeInTheDocument();
    });
  });

  describe('Authentication Integration and Token Management', () => {
    test('should handle token authentication across multiple API calls and manage token lifecycle', async () => {
      const user = userEvent.setup();
      let tokenValidationCount = 0;
      
      // Configure MSW to track token usage
      server.use(
        rest.get('/api/v1/admin/clients', (req, res, ctx) => {
          const authHeader = req.headers.get('Authorization');
          
          // Validate token format and presence
          if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res(ctx.status(401), ctx.json({ detail: 'Missing or invalid authorization header' }));
          }
          
          const token = authHeader.replace('Bearer ', '');
          
          // Track token validation
          tokenValidationCount++;
          
          // Simulate token expiration after 3 uses
          if (tokenValidationCount > 3) {
            return res(ctx.status(401), ctx.json({ detail: 'Token expired' }));
          }
          
          return res(
            ctx.status(200),
            ctx.json([
              {
                client_id: 'client_token_test',
                name: 'Token Test Client',
                email: 'token@test.com',
                client_type: 'ecommerce',
                privacy_level: 'standard',
                is_active: true
              }
            ])
          );
        }),
        
        rest.get('/api/v1/admin/clients/:clientId', (req, res, ctx) => {
          const authHeader = req.headers.get('Authorization');
          
          if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res(ctx.status(401), ctx.json({ detail: 'Missing authorization header' }));
          }
          
          tokenValidationCount++;
          
          if (tokenValidationCount > 3) {
            return res(ctx.status(401), ctx.json({ detail: 'Token expired' }));
          }
          
          return res(
            ctx.status(200),
            ctx.json({
              client_id: req.params.clientId,
              name: 'Token Test Client',
              email: 'token@test.com',
              client_type: 'ecommerce',
              privacy_level: 'standard'
            })
          );
        }),
        
        rest.post('/api/v1/admin/clients', (req, res, ctx) => {
          const authHeader = req.headers.get('Authorization');
          
          if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res(ctx.status(401), ctx.json({ detail: 'Missing authorization header' }));
          }
          
          tokenValidationCount++;
          
          if (tokenValidationCount > 3) {
            return res(ctx.status(401), ctx.json({ detail: 'Token expired' }));
          }
          
          return res(
            ctx.status(201),
            ctx.json({
              client_id: 'client_new_token_test',
              name: req.body.name,
              email: req.body.email,
              client_type: req.body.client_type
            })
          );
        })
      );
      
      render(
        <MemoryRouter initialEntries={['/admin/clients']}>
          <App />
        </MemoryRouter>
      );
      
      // STEP 1: Initial API call with token
      await waitFor(() => {
        expect(screen.getByText(/token test client/i)).toBeInTheDocument();
      });
      
      expect(tokenValidationCount).toBe(1);
      
      // STEP 2: Edit client (triggers another API call)
      const clientRow = screen.getByText(/token test client/i).closest('tr');
      const editButton = clientRow.querySelector('button') || screen.getByRole('button', { name: /edit/i });
      await user.click(editButton);
      
      await waitFor(() => {
        expect(screen.getByText(/edit client/i)).toBeInTheDocument();
      });
      
      expect(tokenValidationCount).toBe(2);
      
      // STEP 3: Go back and create new client
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);
      
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      });
      
      const createButton = screen.getByRole('button', { name: /create new client/i });
      await user.click(createButton);
      
      await waitFor(() => {
        expect(screen.getByText(/create new client/i)).toBeInTheDocument();
      });
      
      // Fill and submit form
      const nameInput = screen.getByLabelText(/client name/i);
      const emailInput = screen.getByLabelText(/email address/i);
      const clientTypeSelect = screen.getByLabelText(/client type/i);
      
      await user.type(nameInput, 'Token Lifecycle Test');
      await user.type(emailInput, 'lifecycle@test.com');
      await user.selectOptions(clientTypeSelect, 'ecommerce');
      
      const submitButton = screen.getByRole('button', { name: /create client/i });
      await user.click(submitButton);
      
      // STEP 4: This should succeed (token still valid)
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      expect(tokenValidationCount).toBe(3);
      
      // STEP 5: Try another operation that should trigger token expiration
      const newCreateButton = screen.getByRole('button', { name: /create new client/i });
      await user.click(newCreateButton);
      
      // This should trigger token expiration (4th call)
      await waitFor(() => {
        expect(tokenValidationCount).toBe(4);
      });
      
      // Should handle token expiration by clearing session and reloading
      await waitFor(() => {
        expect(window.sessionStorage.removeItem).toHaveBeenCalledWith('admin_api_key');
        expect(window.location.reload).toHaveBeenCalled();
      });
    });

    test('should handle authentication header injection and error responses consistently', async () => {
      const user = userEvent.setup();
      
      // Test different authentication scenarios
      const authTestCases = [
        {
          scenario: 'missing_token',
          sessionStorageKey: null,
          expectedError: 'Authentication required'
        },
        {
          scenario: 'invalid_token',
          sessionStorageKey: 'invalid_token_format',
          expectedError: 'Invalid API key'
        },
        {
          scenario: 'valid_token',
          sessionStorageKey: 'test_integration_key_12345',
          expectedSuccess: true
        }
      ];
      
      for (const testCase of authTestCases) {
        // Reset token validation count
        let currentCallCount = 0;
        
        // Clear and set session storage for this test case
        mockSessionStorage = testCase.sessionStorageKey 
          ? { 'admin_api_key': testCase.sessionStorageKey }
          : {};
        
        server.use(
          rest.get('/api/v1/admin/clients', (req, res, ctx) => {
            const authHeader = req.headers.get('Authorization');
            currentCallCount++;
            
            if (testCase.scenario === 'missing_token') {
              if (!authHeader) {
                return res(ctx.status(401), ctx.json({ detail: 'Authentication required' }));
              }
            }
            
            if (testCase.scenario === 'invalid_token') {
              if (authHeader !== 'Bearer test_integration_key_12345') {
                return res(ctx.status(401), ctx.json({ detail: 'Invalid API key' }));
              }
            }
            
            if (testCase.scenario === 'valid_token') {
              if (authHeader === 'Bearer test_integration_key_12345') {
                return res(
                  ctx.status(200),
                  ctx.json([
                    {
                      client_id: 'client_auth_success',
                      name: 'Auth Success Client',
                      email: 'success@test.com'
                    }
                  ])
                );
              }
            }
            
            return res(ctx.status(401), ctx.json({ detail: 'Unauthorized' }));
          })
        );
        
        const { unmount } = render(
          <MemoryRouter initialEntries={['/admin/clients']}>
            <App />
          </MemoryRouter>
        );
        
        if (testCase.expectedSuccess) {
          // Should load successfully
          await waitFor(() => {
            expect(screen.getByText(/auth success client/i)).toBeInTheDocument();
          });
          
          expect(currentCallCount).toBe(1);
        } else {
          // Should handle authentication error
          if (testCase.scenario === 'missing_token') {
            // Should redirect to login
            await waitFor(() => {
              expect(screen.getByText(/securepixel admin/i)).toBeInTheDocument();
            });
          } else {
            // Should show error or redirect
            await waitFor(() => {
              expect(
                screen.getByText(/securepixel admin/i) ||
                screen.getByText(new RegExp(testCase.expectedError, 'i'))
              ).toBeInTheDocument();
            });
          }
        }
        
        unmount();
      }
    });
  });

  describe('Response Processing and Data Transformation', () => {
    test('should handle complex API responses and transform data correctly', async () => {
      // Configure MSW with complex response formats
      server.use(
        rest.get('/api/v1/admin/clients', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json([
              {
                client_id: 'client_complex_001',
                name: 'Complex Data Client',
                email: 'complex@test.com',
                client_type: 'enterprise',
                owner: 'complex@test.com',
                privacy_level: 'hipaa',
                deployment_type: 'dedicated',
                vm_hostname: 'client-001.evothesis.com',
                billing_entity: 'Healthcare Corp',
                is_active: true,
                domain_count: 5,
                created_at: '2024-01-15T10:30:00Z',
                updated_at: '2024-01-20T14:15:30Z',
                metadata: {
                  last_access: '2024-01-25T09:45:00Z',
                  ip_collection_enabled: true,
                  consent_management: true
                }
              }
            ])
          );
        })
      );
      
      render(
        <MemoryRouter initialEntries={['/admin/clients']}>
          <App />
        </MemoryRouter>
      );
      
      // Verify complex data is displayed correctly
      await waitFor(() => {
        expect(screen.getByText(/complex data client/i)).toBeInTheDocument();
        expect(screen.getByText(/hipaa/i)).toBeInTheDocument();
        expect(screen.getByText(/dedicated/i)).toBeInTheDocument();
        expect(screen.getByText(/5/)).toBeInTheDocument(); // domain count
      });
    });

    test('should handle malformed API responses gracefully', async () => {
      // Configure MSW with malformed responses
      server.use(
        rest.get('/api/v1/admin/clients', (req, res, ctx) => {
          // Return malformed JSON
          return res(
            ctx.status(200),
            ctx.text('{ "invalid": json syntax }') // Malformed JSON
          );
        })
      );
      
      render(
        <MemoryRouter initialEntries={['/admin/clients']}>
          <App />
        </MemoryRouter>
      );
      
      // Should handle JSON parsing error gracefully
      await waitFor(() => {
        expect(screen.getByText(/error loading clients/i)).toBeInTheDocument();
      });
    });
  });
});