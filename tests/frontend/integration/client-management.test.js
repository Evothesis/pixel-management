/**
 * Frontend Client Management Integration Tests - Phase 7
 * 
 * End-to-end client management workflow testing including complete CRUD operations,
 * form pre-population, validation, error handling, navigation flows, and domain
 * management integration across multiple components and services.
 * 
 * This test suite covers the complete client management integration across
 * ClientList, ClientForm, Dashboard components, API service, and routing.
 * 
 * Coverage Requirements:
 * - Complete client creation workflow end-to-end
 * - Client editing workflow with form pre-population
 * - Client deletion workflow with confirmation dialogs
 * - Domain management integration
 * 
 * Test Categories:
 * 1. Complete client CRUD workflow (create → list → edit → delete)
 * 2. Client editing and domain management integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../../../src/mocks/server';
import App from '../../../src/App';

// Mock the API service for controlled testing
jest.mock('../../../src/services/api', () => ({
  apiService: {
    testApiKey: jest.fn(),
    clients: {
      list: jest.fn(),
      get: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn()
    },
    domains: {
      list: jest.fn(),
      add: jest.fn(),
      remove: jest.fn()
    },
    health: jest.fn()
  }
}));

import { apiService } from '../../../src/services/api';

describe('Client Management Integration Tests', () => {
  // Mock sessionStorage and authentication
  let mockSessionStorage = {};
  
  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Mock sessionStorage with valid authentication
    mockSessionStorage = {
      'admin_api_key': 'test_admin_key_12345'
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
    
    // Mock window.location for navigation
    delete window.location;
    window.location = { 
      reload: jest.fn(),
      href: '',
      assign: jest.fn()
    };
    
    // Mock window.confirm for deletion confirmation
    window.confirm = jest.fn();
    
    // Default API mocks for authenticated state
    apiService.testApiKey.mockResolvedValue({ success: true });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Complete Client CRUD Workflow', () => {
    test('should complete full client lifecycle: create → list → edit → delete', async () => {
      const user = userEvent.setup();
      
      // Mock initial empty client list
      apiService.clients.list.mockResolvedValueOnce({
        data: []
      });
      
      // Mock successful client creation
      apiService.clients.create.mockResolvedValue({
        data: {
          client_id: 'client_new_123',
          name: 'Integration Test Client',
          email: 'integration@testclient.com',
          client_type: 'ecommerce',
          owner: 'integration@testclient.com',
          privacy_level: 'standard',
          deployment_type: 'shared',
          vm_hostname: '',
          billing_entity: '',
          is_active: true,
          domain_count: 0,
          created_at: new Date().toISOString()
        }
      });
      
      // Mock updated client list after creation
      apiService.clients.list.mockResolvedValueOnce({
        data: [
          {
            client_id: 'client_new_123',
            name: 'Integration Test Client',
            email: 'integration@testclient.com',
            client_type: 'ecommerce',
            privacy_level: 'standard',
            deployment_type: 'shared',
            is_active: true,
            domain_count: 0
          }
        ]
      });
      
      // Mock client detail fetch for editing
      apiService.clients.get.mockResolvedValue({
        data: {
          client_id: 'client_new_123',
          name: 'Integration Test Client',
          email: 'integration@testclient.com',
          client_type: 'ecommerce',
          owner: 'integration@testclient.com',
          privacy_level: 'standard',
          deployment_type: 'shared',
          vm_hostname: '',
          billing_entity: '',
          is_active: true
        }
      });
      
      // Mock successful client update
      apiService.clients.update.mockResolvedValue({
        data: {
          client_id: 'client_new_123',
          name: 'Updated Integration Test Client',
          email: 'integration@testclient.com',
          client_type: 'ecommerce',
          privacy_level: 'gdpr', // Updated
          deployment_type: 'shared',
          is_active: true
        }
      });
      
      // Mock client list after update
      apiService.clients.list.mockResolvedValueOnce({
        data: [
          {
            client_id: 'client_new_123',
            name: 'Updated Integration Test Client',
            email: 'integration@testclient.com',
            client_type: 'ecommerce',
            privacy_level: 'gdpr',
            deployment_type: 'shared',
            is_active: true,
            domain_count: 0
          }
        ]
      });
      
      // Mock successful client deletion
      apiService.clients.delete.mockResolvedValue({
        data: { message: 'Client deleted successfully' }
      });
      
      // Mock empty client list after deletion
      apiService.clients.list.mockResolvedValueOnce({
        data: []
      });
      
      // Start with dashboard route
      render(
        <MemoryRouter initialEntries={['/admin/dashboard']}>
          <App />
        </MemoryRouter>
      );
      
      // Wait for dashboard to load
      await waitFor(() => {
        expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      });
      
      // STEP 1: Navigate to client management
      const clientManagementButton = screen.getByText(/client management/i);
      await user.click(clientManagementButton);
      
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      });
      
      // Should show empty state initially
      expect(screen.getByText(/no clients found/i)).toBeInTheDocument();
      
      // STEP 2: Create new client
      const createClientButton = screen.getByRole('button', { name: /create new client/i });
      await user.click(createClientButton);
      
      await waitFor(() => {
        expect(screen.getByText(/create new client/i)).toBeInTheDocument();
      });
      
      // Fill out client creation form
      const nameInput = screen.getByLabelText(/client name/i);
      const emailInput = screen.getByLabelText(/email address/i);
      const clientTypeSelect = screen.getByLabelText(/client type/i);
      const privacyLevelSelect = screen.getByLabelText(/privacy level/i);
      
      await user.type(nameInput, 'Integration Test Client');
      await user.type(emailInput, 'integration@testclient.com');
      await user.selectOptions(clientTypeSelect, 'ecommerce');
      await user.selectOptions(privacyLevelSelect, 'standard');
      
      // Submit form
      const createButton = screen.getByRole('button', { name: /create client/i });
      await user.click(createButton);
      
      // Should show creating state
      await waitFor(() => {
        expect(screen.getByText(/creating/i)).toBeInTheDocument();
      });
      
      // Should redirect to client list after creation
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
        expect(screen.getByText(/integration test client/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Verify API was called correctly
      expect(apiService.clients.create).toHaveBeenCalledWith({
        name: 'Integration Test Client',
        email: 'integration@testclient.com',
        client_type: 'ecommerce',
        owner: 'integration@testclient.com',
        privacy_level: 'standard',
        deployment_type: 'shared',
        vm_hostname: '',
        billing_entity: ''
      });
      
      // STEP 3: Edit the created client
      const clientRow = screen.getByText(/integration test client/i).closest('tr');
      const editButton = within(clientRow).getByRole('button', { name: /edit/i });
      await user.click(editButton);
      
      await waitFor(() => {
        expect(screen.getByText(/edit client/i)).toBeInTheDocument();
      });
      
      // Verify form is pre-populated
      expect(screen.getByDisplayValue('Integration Test Client')).toBeInTheDocument();
      expect(screen.getByDisplayValue('integration@testclient.com')).toBeInTheDocument();
      
      // Update client name and privacy level
      const editNameInput = screen.getByDisplayValue('Integration Test Client');
      const editPrivacySelect = screen.getByLabelText(/privacy level/i);
      
      await user.clear(editNameInput);
      await user.type(editNameInput, 'Updated Integration Test Client');
      await user.selectOptions(editPrivacySelect, 'gdpr');
      
      // Submit update
      const updateButton = screen.getByRole('button', { name: /update client/i });
      await user.click(updateButton);
      
      // Should redirect back to list with updated data
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
        expect(screen.getByText(/updated integration test client/i)).toBeInTheDocument();
        expect(screen.getByText(/gdpr/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Verify update API was called correctly
      expect(apiService.clients.update).toHaveBeenCalledWith('client_new_123', {
        name: 'Updated Integration Test Client',
        email: 'integration@testclient.com',
        client_type: 'ecommerce',
        owner: 'integration@testclient.com',
        privacy_level: 'gdpr',
        deployment_type: 'shared',
        vm_hostname: '',
        billing_entity: ''
      });
      
      // STEP 4: Delete the client
      const updatedClientRow = screen.getByText(/updated integration test client/i).closest('tr');
      const deleteButton = within(updatedClientRow).getByRole('button', { name: /delete/i });
      
      // Mock confirmation dialog
      window.confirm.mockReturnValue(true);
      
      await user.click(deleteButton);
      
      // Should show confirmation dialog and proceed with deletion
      expect(window.confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this client? This action cannot be undone.'
      );
      
      // Should return to empty state
      await waitFor(() => {
        expect(screen.getByText(/no clients found/i)).toBeInTheDocument();
        expect(screen.queryByText(/updated integration test client/i)).not.toBeInTheDocument();
      });
      
      // Verify delete API was called
      expect(apiService.clients.delete).toHaveBeenCalledWith('client_new_123');
    });

    test('should handle client creation workflow with validation errors and recovery', async () => {
      const user = userEvent.setup();
      
      // Mock validation error on first attempt
      apiService.clients.create
        .mockRejectedValueOnce({
          response: {
            status: 422,
            data: {
              detail: [
                {
                  loc: ['body', 'email'],
                  msg: 'Invalid email format',
                  type: 'value_error'
                }
              ]
            }
          }
        })
        .mockResolvedValueOnce({
          data: {
            client_id: 'client_corrected_123',
            name: 'Corrected Test Client',
            email: 'corrected@testclient.com',
            client_type: 'ecommerce',
            privacy_level: 'standard'
          }
        });
      
      // Mock client list
      apiService.clients.list.mockResolvedValue({
        data: []
      });
      
      render(
        <MemoryRouter initialEntries={['/admin/clients/new']}>
          <App />
        </MemoryRouter>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/create new client/i)).toBeInTheDocument();
      });
      
      // Fill form with invalid email
      const nameInput = screen.getByLabelText(/client name/i);
      const emailInput = screen.getByLabelText(/email address/i);
      const clientTypeSelect = screen.getByLabelText(/client type/i);
      
      await user.type(nameInput, 'Test Client');
      await user.type(emailInput, 'invalid-email'); // Invalid format
      await user.selectOptions(clientTypeSelect, 'ecommerce');
      
      // Submit form
      const createButton = screen.getByRole('button', { name: /create client/i });
      await user.click(createButton);
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
      });
      
      // Should remain on form with data preserved
      expect(screen.getByDisplayValue('Test Client')).toBeInTheDocument();
      expect(screen.getByDisplayValue('invalid-email')).toBeInTheDocument();
      
      // Correct the email and retry
      await user.clear(emailInput);
      await user.type(emailInput, 'corrected@testclient.com');
      
      await user.click(createButton);
      
      // Should succeed and redirect
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Verify both API calls were made
      expect(apiService.clients.create).toHaveBeenCalledTimes(2);
    });
  });

  describe('Client Editing and Domain Management Integration', () => {
    test('should handle client editing with domain management workflow', async () => {
      const user = userEvent.setup();
      
      // Mock existing client
      const existingClient = {
        client_id: 'client_domain_test',
        name: 'Domain Test Client',
        email: 'domain@testclient.com',
        client_type: 'ecommerce',
        owner: 'domain@testclient.com',
        privacy_level: 'standard',
        deployment_type: 'shared',
        is_active: true,
        domain_count: 1
      };
      
      // Mock client list with existing client
      apiService.clients.list.mockResolvedValue({
        data: [existingClient]
      });
      
      // Mock client detail fetch
      apiService.clients.get.mockResolvedValue({
        data: existingClient
      });
      
      // Mock existing domains
      apiService.domains.list.mockResolvedValue({
        data: [
          {
            id: 'client_domain_test_example_com',
            domain: 'example.com',
            is_primary: true,
            created_at: new Date().toISOString()
          }
        ]
      });
      
      // Mock successful domain addition
      apiService.domains.add.mockResolvedValue({
        data: {
          id: 'client_domain_test_newdomain_com',
          domain: 'newdomain.com',
          is_primary: false,
          created_at: new Date().toISOString()
        }
      });
      
      // Mock updated domain list after addition
      apiService.domains.list.mockResolvedValueOnce({
        data: [
          {
            id: 'client_domain_test_example_com',
            domain: 'example.com',
            is_primary: true,
            created_at: new Date().toISOString()
          },
          {
            id: 'client_domain_test_newdomain_com',
            domain: 'newdomain.com',
            is_primary: false,
            created_at: new Date().toISOString()
          }
        ]
      });
      
      // Mock successful domain removal
      apiService.domains.remove.mockResolvedValue({
        data: { message: 'Domain removed successfully' }
      });
      
      // Mock client update
      apiService.clients.update.mockResolvedValue({
        data: { ...existingClient, name: 'Updated Domain Test Client' }
      });
      
      render(
        <MemoryRouter initialEntries={['/admin/clients']}>
          <App />
        </MemoryRouter>
      );
      
      // Wait for client list to load
      await waitFor(() => {
        expect(screen.getByText(/domain test client/i)).toBeInTheDocument();
      });
      
      // Click edit button
      const clientRow = screen.getByText(/domain test client/i).closest('tr');
      const editButton = within(clientRow).getByRole('button', { name: /edit/i });
      await user.click(editButton);
      
      await waitFor(() => {
        expect(screen.getByText(/edit client/i)).toBeInTheDocument();
      });
      
      // Should show domain management section
      expect(screen.getByText(/domain management/i)).toBeInTheDocument();
      expect(screen.getByText(/example\.com/i)).toBeInTheDocument();
      expect(screen.getByText(/primary/i)).toBeInTheDocument();
      
      // Add a new domain
      const domainInput = screen.getByLabelText(/domain/i);
      const addDomainButton = screen.getByRole('button', { name: /add domain/i });
      
      await user.type(domainInput, 'newdomain.com');
      await user.click(addDomainButton);
      
      // Should show new domain in the list
      await waitFor(() => {
        expect(screen.getByText(/newdomain\.com/i)).toBeInTheDocument();
      });
      
      // Verify domain was added
      expect(apiService.domains.add).toHaveBeenCalledWith('client_domain_test', {
        domain: 'newdomain.com',
        is_primary: false
      });
      
      // Remove the original domain
      const originalDomainRow = screen.getByText(/example\.com/i).closest('tr');
      const removeDomainButton = within(originalDomainRow).getByRole('button', { name: /remove/i });
      
      window.confirm.mockReturnValue(true);
      await user.click(removeDomainButton);
      
      expect(window.confirm).toHaveBeenCalledWith(
        'Are you sure you want to remove this domain? This action cannot be undone.'
      );
      
      // Should remove domain from list
      await waitFor(() => {
        expect(screen.queryByText(/example\.com/i)).not.toBeInTheDocument();
      });
      
      // Verify domain removal API call
      expect(apiService.domains.remove).toHaveBeenCalledWith('client_domain_test', 'example.com');
      
      // Update client basic information
      const nameInput = screen.getByDisplayValue('Domain Test Client');
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Domain Test Client');
      
      // Submit client update
      const updateButton = screen.getByRole('button', { name: /update client/i });
      await user.click(updateButton);
      
      // Should redirect to client list
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Verify client update was called
      expect(apiService.clients.update).toHaveBeenCalledWith('client_domain_test', {
        name: 'Updated Domain Test Client',
        email: 'domain@testclient.com',
        client_type: 'ecommerce',
        owner: 'domain@testclient.com',
        privacy_level: 'standard',
        deployment_type: 'shared',
        vm_hostname: '',
        billing_entity: ''
      });
    });

    test('should handle domain management errors and validation', async () => {
      const user = userEvent.setup();
      
      const existingClient = {
        client_id: 'client_domain_error',
        name: 'Domain Error Client',
        email: 'error@testclient.com',
        client_type: 'ecommerce',
        privacy_level: 'standard',
        is_active: true
      };
      
      // Mock client detail fetch
      apiService.clients.get.mockResolvedValue({
        data: existingClient
      });
      
      // Mock existing domains
      apiService.domains.list.mockResolvedValue({
        data: [
          {
            id: 'client_domain_error_existing_com',
            domain: 'existing.com',
            is_primary: true
          }
        ]
      });
      
      // Mock domain addition errors
      apiService.domains.add
        .mockRejectedValueOnce({
          response: {
            status: 409,
            data: { detail: 'Domain already assigned to another client' }
          }
        })
        .mockRejectedValueOnce({
          response: {
            status: 422,
            data: { detail: 'Invalid domain format' }
          }
        })
        .mockResolvedValueOnce({
          data: {
            id: 'client_domain_error_valid_com',
            domain: 'valid.com',
            is_primary: false
          }
        });
      
      render(
        <MemoryRouter initialEntries={['/admin/clients/client_domain_error/edit']}>
          <App />
        </MemoryRouter>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/edit client/i)).toBeInTheDocument();
      });
      
      // Try to add duplicate domain
      const domainInput = screen.getByLabelText(/domain/i);
      const addButton = screen.getByRole('button', { name: /add domain/i });
      
      await user.type(domainInput, 'duplicate.com');
      await user.click(addButton);
      
      // Should show conflict error
      await waitFor(() => {
        expect(screen.getByText(/domain already assigned to another client/i)).toBeInTheDocument();
      });
      
      // Domain should remain in input for correction
      expect(screen.getByDisplayValue('duplicate.com')).toBeInTheDocument();
      
      // Try invalid domain format
      await user.clear(domainInput);
      await user.type(domainInput, 'invalid-domain');
      await user.click(addButton);
      
      // Should show format error
      await waitFor(() => {
        expect(screen.getByText(/invalid domain format/i)).toBeInTheDocument();
      });
      
      // Add valid domain
      await user.clear(domainInput);
      await user.type(domainInput, 'valid.com');
      await user.click(addButton);
      
      // Should succeed
      await waitFor(() => {
        expect(screen.getByText(/valid\.com/i)).toBeInTheDocument();
        expect(screen.queryByText(/invalid domain format/i)).not.toBeInTheDocument();
      });
      
      // Verify all API calls were made
      expect(apiService.domains.add).toHaveBeenCalledTimes(3);
    });
  });

  describe('Error Handling and Edge Cases', () => {
    test('should handle network errors during client operations gracefully', async () => {
      const user = userEvent.setup();
      
      // Mock network error for client list
      apiService.clients.list.mockRejectedValue(new Error('Network error'));
      
      render(
        <MemoryRouter initialEntries={['/admin/clients']}>
          <App />
        </MemoryRouter>
      );
      
      // Should show error state
      await waitFor(() => {
        expect(screen.getByText(/error loading clients/i)).toBeInTheDocument();
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
      
      // Should provide retry option
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();
      
      // Mock successful retry
      apiService.clients.list.mockResolvedValueOnce({
        data: [
          {
            client_id: 'client_retry_test',
            name: 'Retry Test Client',
            email: 'retry@test.com'
          }
        ]
      });
      
      await user.click(retryButton);
      
      // Should load successfully on retry
      await waitFor(() => {
        expect(screen.getByText(/retry test client/i)).toBeInTheDocument();
        expect(screen.queryByText(/error loading clients/i)).not.toBeInTheDocument();
      });
    });

    test('should handle client form cancellation and navigation', async () => {
      const user = userEvent.setup();
      
      // Mock client list
      apiService.clients.list.mockResolvedValue({
        data: [{ client_id: 'existing_client', name: 'Existing Client' }]
      });
      
      render(
        <MemoryRouter initialEntries={['/admin/clients/new']}>
          <App />
        </MemoryRouter>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/create new client/i)).toBeInTheDocument();
      });
      
      // Fill form partially
      const nameInput = screen.getByLabelText(/client name/i);
      await user.type(nameInput, 'Partial Form');
      
      // Click cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);
      
      // Should navigate back to client list without saving
      await waitFor(() => {
        expect(screen.getByText(/client configuration/i)).toBeInTheDocument();
        expect(screen.getByText(/existing client/i)).toBeInTheDocument();
      });
      
      // Verify no create API call was made
      expect(apiService.clients.create).not.toHaveBeenCalled();
    });
  });
});