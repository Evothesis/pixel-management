/**
 * Frontend Authentication Flow Integration Tests - Phase 7
 * 
 * End-to-end authentication workflow testing including complete user journeys
 * from login to logout, authentication persistence, session management,
 * protected route access, and failure scenario handling.
 * 
 * This test suite covers the complete authentication integration across
 * AuthContext, API service, routing, and session storage management.
 * 
 * Coverage Requirements:
 * - Complete authentication workflow from login to logout
 * - Authentication persistence and session management
 * - Protected route access and unauthorized redirects
 * - Authentication failure scenarios and recovery
 * 
 * Test Categories:
 * 1. Complete authentication workflow (login → dashboard → logout)
 * 2. Authentication persistence and session management
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../../../src/mocks/server';
import App from '../../../src/App';
import { AuthProvider } from '../../../src/contexts/AuthContext';

// Mock the API service for controlled testing
jest.mock('../../../src/services/api', () => ({
  apiService: {
    testApiKey: jest.fn(),
    clients: {
      list: jest.fn()
    },
    health: jest.fn()
  }
}));

import { apiService } from '../../../src/services/api';

describe('Authentication Flow Integration Tests', () => {
  // Mock sessionStorage for consistent testing
  let mockSessionStorage = {};
  
  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Mock sessionStorage
    mockSessionStorage = {};
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
    
    // Mock window.location.reload
    delete window.location;
    window.location = { reload: jest.fn(), href: '' };
    
    // Reset API service mocks
    apiService.testApiKey.mockReset();
    apiService.clients.list.mockReset();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Complete Authentication Workflow', () => {
    test('should complete full authentication flow: login → dashboard → logout', async () => {
      const user = userEvent.setup();
      
      // Mock successful API key validation
      apiService.testApiKey.mockResolvedValue({
        success: true
      });
      
      // Mock successful client list fetch
      apiService.clients.list.mockResolvedValue({
        data: [
          {
            client_id: 'client_test_001',
            name: 'Test E-commerce Store',
            email: 'admin@teststore.com',
            client_type: 'end_client',
            privacy_level: 'standard',
            deployment_type: 'shared',
            is_active: true,
            domain_count: 2
          }
        ]
      });
      
      // Start with login route in MemoryRouter
      render(
        <MemoryRouter initialEntries={['/login']}>
          <App />
        </MemoryRouter>
      );
      
      // STEP 1: Should start at login page
      await waitFor(() => {
        expect(screen.getByText(/securepixel admin/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/admin api key/i)).toBeInTheDocument();
      });
      
      // STEP 2: Enter valid API key and submit
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      const validApiKey = 'test_admin_key_12345';
      await user.type(apiKeyInput, validApiKey);
      await user.click(submitButton);
      
      // Should show verifying state
      await waitFor(() => {
        expect(screen.getByText(/verifying/i)).toBeInTheDocument();
      });
      
      // STEP 3: Should redirect to dashboard after successful authentication
      await waitFor(() => {
        expect(screen.getByText(/securepixel management/i)).toBeInTheDocument();
        expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Should show API key in header
      expect(screen.getByText(/api key: test_admin_key_12.../i)).toBeInTheDocument();
      
      // Verify authentication was stored in sessionStorage
      expect(window.sessionStorage.setItem).toHaveBeenCalledWith('admin_api_key', validApiKey);
      
      // STEP 4: Navigate to clients page to verify protected routes work
      const clientsNavButton = screen.getByText(/client management/i);
      await user.click(clientsNavButton);
      
      // Should navigate to clients page
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      });
      
      // Should load client data
      expect(apiService.clients.list).toHaveBeenCalled();
      
      // STEP 5: Logout workflow
      const logoutButton = screen.getByRole('button', { name: /logout/i });
      await user.click(logoutButton);
      
      // Should clear session storage
      expect(window.sessionStorage.removeItem).toHaveBeenCalledWith('admin_api_key');
      
      // Should redirect to login page (via window.location.href)
      expect(window.location.href).toBe('/login');
    });

    test('should handle authentication failure scenarios and recovery', async () => {
      const user = userEvent.setup();
      
      // Mock initial API key validation failure
      apiService.testApiKey
        .mockResolvedValueOnce({
          success: false,
          error: 'Invalid API key'
        })
        .mockResolvedValueOnce({
          success: true
        });
      
      // Mock successful client list fetch for retry
      apiService.clients.list.mockResolvedValue({
        data: []
      });
      
      render(
        <MemoryRouter initialEntries={['/login']}>
          <App />
        </MemoryRouter>
      );
      
      // STEP 1: First login attempt with invalid key
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'invalid_key');
      await user.click(submitButton);
      
      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/invalid api key/i)).toBeInTheDocument();
      });
      
      // Should remain on login page
      expect(screen.getByLabelText(/admin api key/i)).toBeInTheDocument();
      
      // Should not store invalid key in session storage
      expect(window.sessionStorage.setItem).not.toHaveBeenCalled();
      
      // STEP 2: Clear error and try again with valid key
      await user.clear(apiKeyInput);
      await user.type(apiKeyInput, 'valid_key_12345');
      
      // Error should clear on input focus
      fireEvent.focus(apiKeyInput);
      await waitFor(() => {
        expect(screen.queryByText(/invalid api key/i)).not.toBeInTheDocument();
      });
      
      // Submit with valid key
      await user.click(submitButton);
      
      // STEP 3: Should succeed and redirect to dashboard
      await waitFor(() => {
        expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Should store valid key in session storage
      expect(window.sessionStorage.setItem).toHaveBeenCalledWith('admin_api_key', 'valid_key_12345');
    });
  });

  describe('Authentication Persistence and Session Management', () => {
    test('should restore authentication state from sessionStorage on app load', async () => {
      // Pre-populate sessionStorage with valid API key
      const existingApiKey = 'stored_api_key_12345';
      mockSessionStorage['admin_api_key'] = existingApiKey;
      
      // Mock successful client list fetch
      apiService.clients.list.mockResolvedValue({
        data: [
          {
            client_id: 'client_001',
            name: 'Stored Client',
            email: 'stored@example.com'
          }
        ]
      });
      
      // Start app with root route (should redirect to dashboard if authenticated)
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );
      
      // Should show loading state initially
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
      
      // Should automatically redirect to dashboard without login
      await waitFor(() => {
        expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Should show stored API key in header
      expect(screen.getByText(/api key: stored_api_key_12.../i)).toBeInTheDocument();
      
      // Should not show login form
      expect(screen.queryByLabelText(/admin api key/i)).not.toBeInTheDocument();
    });

    test('should handle protected route access with authentication flow', async () => {
      const user = userEvent.setup();
      
      // Start with protected route when not authenticated
      render(
        <MemoryRouter initialEntries={['/admin/clients']}>
          <App />
        </MemoryRouter>
      );
      
      // Should redirect to login page for protected route access
      await waitFor(() => {
        expect(screen.getByText(/securepixel admin/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/admin api key/i)).toBeInTheDocument();
      });
      
      // Should not show protected content
      expect(screen.queryByText(/client configuration/i)).not.toBeInTheDocument();
      
      // Complete authentication
      apiService.testApiKey.mockResolvedValue({ success: true });
      apiService.clients.list.mockResolvedValue({ data: [] });
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_key_12345');
      await user.click(submitButton);
      
      // Should redirect to dashboard after authentication (not directly to originally requested route)
      await waitFor(() => {
        expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // User can then navigate to clients page
      const clientsNavButton = screen.getByText(/client management/i);
      await user.click(clientsNavButton);
      
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      });
    });

    test('should handle session expiration and automatic logout', async () => {
      // Start with authenticated state
      mockSessionStorage['admin_api_key'] = 'expired_key_12345';
      
      // Mock API failure that triggers logout (401 response)
      apiService.clients.list.mockRejectedValue({
        response: { status: 401 },
        message: 'Unauthorized'
      });
      
      // Mock server handler for 401 response
      server.use(
        rest.get('/api/v1/admin/clients', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Token expired' })
          );
        })
      );
      
      render(
        <MemoryRouter initialEntries={['/admin/dashboard']}>
          <App />
        </MemoryRouter>
      );
      
      // Should initially show dashboard (from stored auth)
      await waitFor(() => {
        expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      });
      
      // Navigate to clients page to trigger API call
      const user = userEvent.setup();
      const clientsNavButton = screen.getByText(/client management/i);
      await user.click(clientsNavButton);
      
      // API call should fail with 401, triggering automatic logout
      // Due to the API interceptor clearing session storage and reloading
      await waitFor(() => {
        expect(window.sessionStorage.removeItem).toHaveBeenCalledWith('admin_api_key');
      });
      
      // Should trigger page reload which would show login page
      expect(window.location.reload).toHaveBeenCalled();
    });

    test('should handle concurrent authentication state changes', async () => {
      const user = userEvent.setup();
      
      // Mock successful authentication
      apiService.testApiKey.mockResolvedValue({ success: true });
      apiService.clients.list.mockResolvedValue({ data: [] });
      
      render(
        <MemoryRouter initialEntries={['/login']}>
          <App />
        </MemoryRouter>
      );
      
      // Complete login
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_key');
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      });
      
      // Simulate external session storage change (e.g., another tab)
      act(() => {
        mockSessionStorage['admin_api_key'] = 'new_key_from_other_tab';
        window.dispatchEvent(new Event('storage'));
      });
      
      // Should update the displayed API key
      await waitFor(() => {
        expect(screen.getByText(/api key: new_key_from_ot.../i)).toBeInTheDocument();
      });
      
      // Simulate session clearing from another tab
      act(() => {
        delete mockSessionStorage['admin_api_key'];
        window.dispatchEvent(new Event('storage'));
      });
      
      // Should trigger logout flow
      expect(window.sessionStorage.removeItem).toHaveBeenCalled();
    });
  });

  describe('Error Recovery and Edge Cases', () => {
    test('should handle network errors during authentication flow', async () => {
      const user = userEvent.setup();
      
      // Mock network error
      apiService.testApiKey.mockRejectedValue(new Error('Network error'));
      
      render(
        <MemoryRouter initialEntries={['/login']}>
          <App />
        </MemoryRouter>
      );
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_key');
      await user.click(submitButton);
      
      // Should show connection error
      await waitFor(() => {
        expect(screen.getByText(/connection error/i)).toBeInTheDocument();
      });
      
      // Should remain on login page
      expect(screen.getByLabelText(/admin api key/i)).toBeInTheDocument();
      
      // Form should be re-enabled for retry
      expect(apiKeyInput).not.toBeDisabled();
      expect(submitButton).not.toBeDisabled();
    });

    test('should handle malformed sessionStorage data gracefully', async () => {
      // Set malformed data in sessionStorage
      mockSessionStorage['admin_api_key'] = ''; // Empty string
      
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );
      
      // Should treat empty string as no authentication
      await waitFor(() => {
        expect(screen.getByText(/securepixel admin/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/admin api key/i)).toBeInTheDocument();
      });
      
      // Should not attempt to use empty string as API key
      expect(screen.queryByText(/admin dashboard/i)).not.toBeInTheDocument();
    });
  });
});