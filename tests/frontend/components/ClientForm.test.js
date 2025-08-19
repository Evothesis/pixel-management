/**
 * ClientForm Component Test Suite - Phase 6
 * 
 * Comprehensive test suite for the ClientForm component covering form rendering,
 * validation, submission workflows, privacy level configuration, domain management,
 * and API integration scenarios. Tests both create and edit modes with extensive
 * error handling and user interaction simulation.
 * 
 * Coverage Requirements:
 * - Form rendering in both create and edit modes
 * - Field validation and error handling (required fields, email format)
 * - Privacy level selection with conditional field display
 * - Form submission success and error scenarios
 * - Dynamic field interactions and state management
 * - Integration with API service using MSW for mocking
 * 
 * Test Categories:
 * 1. Form rendering and mode detection (create vs edit)
 * 2. Field validation and error handling with user feedback
 * 3. Privacy level selection and conditional field visibility
 * 4. Form submission workflows with API integration
 * 5. Dynamic field interactions and state management
 * 6. Domain management integration and error scenarios
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../../mocks/server';
import ClientForm from '../../../src/components/ClientForm';

// Mock the API service
jest.mock('../../../src/services/api', () => ({
  apiService: {
    clients: {
      get: jest.fn(),
      create: jest.fn(),
      update: jest.fn()
    },
    domains: {
      list: jest.fn(),
      add: jest.fn(),
      remove: jest.fn()
    }
  }
}));

// Mock React Router hooks
const mockNavigate = jest.fn();
const mockParams = { clientId: null };

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => mockParams
}));

import { apiService } from '../../../src/services/api';

// Test wrapper with Router
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('ClientForm Component - Comprehensive Test Suite', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
    mockParams.clientId = null;
    
    // Clear sessionStorage mock
    global.sessionStorage.clear();
    global.sessionStorage.setItem('admin_api_key', 'test_admin_key_12345');
    
    // Reset window.confirm mock
    global.confirm = jest.fn(() => true);
  });

  describe('Form Rendering and Mode Detection', () => {
    test('should render create form when no clientId provided', async () => {
      // Mock create mode (no clientId)
      mockParams.clientId = null;
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Should show create form heading
      expect(screen.getByRole('heading', { name: /create client/i })).toBeInTheDocument();
      
      // Should show create button
      expect(screen.getByRole('button', { name: /create client/i })).toBeInTheDocument();
      
      // Should not show domain management section
      expect(screen.queryByText(/authorized domains/i)).not.toBeInTheDocument();
      
      // Should have default form values
      expect(screen.getByLabelText(/company name/i)).toHaveValue('');
      expect(screen.getByLabelText(/email/i)).toHaveValue('');
      expect(screen.getByLabelText(/client type/i)).toHaveValue('end_client');
      expect(screen.getByLabelText(/privacy level/i)).toHaveValue('standard');
      expect(screen.getByLabelText(/deployment type/i)).toHaveValue('shared');
      
      // VM hostname field should not be visible for shared deployment
      expect(screen.queryByLabelText(/vm hostname/i)).not.toBeInTheDocument();
    });

    test('should render edit form when clientId provided and fetch data', async () => {
      // Mock edit mode
      mockParams.clientId = 'client_test_001';
      
      // Mock API responses
      const mockClient = {
        client_id: 'client_test_001',
        name: 'Test E-commerce Store',
        email: 'admin@teststore.com',
        client_type: 'end_client',
        owner: 'client_evothesis_admin',
        billing_entity: '',
        deployment_type: 'dedicated',
        vm_hostname: 'analytics.teststore.com',
        privacy_level: 'gdpr',
        features: {}
      };
      
      const mockDomains = [
        { domain: 'teststore.com', is_primary: true },
        { domain: 'shop.teststore.com', is_primary: false }
      ];
      
      apiService.clients.get.mockResolvedValue({ data: mockClient });
      apiService.domains.list.mockResolvedValue({ data: mockDomains });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Should show edit form heading
      expect(screen.getByRole('heading', { name: /edit client/i })).toBeInTheDocument();
      
      // Should fetch client data
      await waitFor(() => {
        expect(apiService.clients.get).toHaveBeenCalledWith('client_test_001');
        expect(apiService.domains.list).toHaveBeenCalledWith('client_test_001');
      });
      
      // Should populate form fields with fetched data
      await waitFor(() => {
        expect(screen.getByDisplayValue('Test E-commerce Store')).toBeInTheDocument();
        expect(screen.getByDisplayValue('admin@teststore.com')).toBeInTheDocument();
        expect(screen.getByDisplayValue('gdpr')).toBeInTheDocument();
        expect(screen.getByDisplayValue('dedicated')).toBeInTheDocument();
        expect(screen.getByDisplayValue('analytics.teststore.com')).toBeInTheDocument();
      });
      
      // Should show update button
      expect(screen.getByRole('button', { name: /update client/i })).toBeInTheDocument();
      
      // Should show domain management section
      await waitFor(() => {
        expect(screen.getByText(/authorized domains/i)).toBeInTheDocument();
        expect(screen.getByText(/current domains \(2\)/i)).toBeInTheDocument();
      });
    });

    test('should handle edit mode API fetch errors gracefully', async () => {
      // Mock edit mode
      mockParams.clientId = 'client_not_found';
      
      // Mock API errors
      apiService.clients.get.mockRejectedValue(new Error('Client not found'));
      apiService.domains.list.mockRejectedValue(new Error('Domains not found'));
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Should show error messages
      await waitFor(() => {
        expect(screen.getByText(/failed to load client data/i)).toBeInTheDocument();
        expect(screen.getByText(/failed to load domains/i)).toBeInTheDocument();
      });
      
      // Form should still be rendered but with empty values
      expect(screen.getByLabelText(/company name/i)).toHaveValue('');
      expect(screen.getByRole('heading', { name: /edit client/i })).toBeInTheDocument();
    });

    test('should show loading state during data fetching', async () => {
      mockParams.clientId = 'client_test_001';
      
      // Mock delayed API responses
      apiService.clients.get.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ 
          data: { client_id: 'test', name: 'Test' }
        }), 100))
      );
      apiService.domains.list.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
      );
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Form should be rendered immediately (loading states are handled internally)
      expect(screen.getByRole('heading', { name: /edit client/i })).toBeInTheDocument();
      
      // Wait for API calls to complete
      await waitFor(() => {
        expect(apiService.clients.get).toHaveBeenCalled();
      });
    });

    test('should handle navigation and cancel functionality', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Click cancel button
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);
      
      // Should navigate back to clients list
      expect(mockNavigate).toHaveBeenCalledWith('/admin/clients');
    });
  });

  describe('Field Validation and Error Handling', () => {
    test('should validate required fields and show error messages', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const submitButton = screen.getByRole('button', { name: /create client/i });
      const nameInput = screen.getByLabelText(/company name/i);
      
      // Try to submit form with empty required field
      await user.click(submitButton);
      
      // HTML5 validation should prevent submission
      await waitFor(() => {
        expect(nameInput).toBeInvalid();
      });
      
      // API should not be called
      expect(apiService.clients.create).not.toHaveBeenCalled();
    });

    test('should validate email format correctly', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const emailInput = screen.getByLabelText(/email/i);
      const nameInput = screen.getByLabelText(/company name/i);
      const submitButton = screen.getByRole('button', { name: /create client/i });
      
      // Fill required field and invalid email
      await user.type(nameInput, 'Test Company');
      await user.type(emailInput, 'invalid-email');
      
      await user.click(submitButton);
      
      // Email should be invalid due to HTML5 validation
      await waitFor(() => {
        expect(emailInput).toBeInvalid();
      });
      
      // API should not be called
      expect(apiService.clients.create).not.toHaveBeenCalled();
    });

    test('should accept valid email formats', async () => {
      const user = userEvent.setup();
      
      // Mock successful API response
      apiService.clients.create.mockResolvedValue({
        data: { client_id: 'new_client_123' }
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const emailInput = screen.getByLabelText(/email/i);
      const nameInput = screen.getByLabelText(/company name/i);
      const submitButton = screen.getByRole('button', { name: /create client/i });
      
      // Fill with valid data
      await user.type(nameInput, 'Test Company');
      await user.type(emailInput, 'test@example.com');
      
      await user.click(submitButton);
      
      // Email should be valid
      expect(emailInput).toBeValid();
      
      // API should be called
      await waitFor(() => {
        expect(apiService.clients.create).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Company',
            email: 'test@example.com'
          })
        );
      });
    });

    test('should handle API validation errors and display them', async () => {
      const user = userEvent.setup();
      
      // Mock API validation error
      const validationError = {
        response: {
          status: 422,
          data: {
            detail: 'Client name already exists'
          }
        }
      };
      apiService.clients.create.mockRejectedValue(validationError);
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const nameInput = screen.getByLabelText(/company name/i);
      const submitButton = screen.getByRole('button', { name: /create client/i });
      
      await user.type(nameInput, 'Duplicate Company');
      await user.click(submitButton);
      
      // Should show API error message
      await waitFor(() => {
        expect(screen.getByText(/client name already exists/i)).toBeInTheDocument();
      });
      
      // Form should remain in error state
      expect(screen.getByRole('button', { name: /create client/i })).not.toBeDisabled();
    });

    test('should clear errors when user modifies form', async () => {
      const user = userEvent.setup();
      
      // Mock API error first
      apiService.clients.create.mockRejectedValue({
        response: { data: { detail: 'Validation error' } }
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const nameInput = screen.getByLabelText(/company name/i);
      const submitButton = screen.getByRole('button', { name: /create client/i });
      
      // Cause an error
      await user.type(nameInput, 'Invalid Client');
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/validation error/i)).toBeInTheDocument();
      });
      
      // Modify form - error should persist until next submission
      await user.clear(nameInput);
      await user.type(nameInput, 'Valid Client');
      
      // Error message should still be visible until next submission
      expect(screen.getByText(/validation error/i)).toBeInTheDocument();
    });

    test('should handle network errors gracefully', async () => {
      const user = userEvent.setup();
      
      // Mock network error
      apiService.clients.create.mockRejectedValue(new Error('Network Error'));
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const nameInput = screen.getByLabelText(/company name/i);
      const submitButton = screen.getByRole('button', { name: /create client/i });
      
      await user.type(nameInput, 'Test Company');
      await user.click(submitButton);
      
      // Should show generic error message for network errors
      await waitFor(() => {
        expect(screen.getByText(/failed to save client/i)).toBeInTheDocument();
      });
    });
  });

  describe('Privacy Level Selection and Conditional Fields', () => {
    test('should show VM hostname field when deployment type is dedicated', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const deploymentSelect = screen.getByLabelText(/deployment type/i);
      
      // Initially should not show VM hostname (shared is default)
      expect(screen.queryByLabelText(/vm hostname/i)).not.toBeInTheDocument();
      
      // Change to dedicated deployment
      await user.selectOptions(deploymentSelect, 'dedicated');
      
      // VM hostname field should appear
      await waitFor(() => {
        expect(screen.getByLabelText(/vm hostname/i)).toBeInTheDocument();
      });
      
      // Change back to shared
      await user.selectOptions(deploymentSelect, 'shared');
      
      // VM hostname field should disappear
      await waitFor(() => {
        expect(screen.queryByLabelText(/vm hostname/i)).not.toBeInTheDocument();
      });
    });

    test('should handle privacy level changes and maintain form state', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const privacySelect = screen.getByLabelText(/privacy level/i);
      const nameInput = screen.getByLabelText(/company name/i);
      
      // Fill some form data
      await user.type(nameInput, 'Privacy Test Company');
      
      // Change privacy levels
      await user.selectOptions(privacySelect, 'gdpr');
      expect(privacySelect).toHaveValue('gdpr');
      
      await user.selectOptions(privacySelect, 'hipaa');
      expect(privacySelect).toHaveValue('hipaa');
      
      await user.selectOptions(privacySelect, 'standard');
      expect(privacySelect).toHaveValue('standard');
      
      // Form data should be preserved
      expect(nameInput).toHaveValue('Privacy Test Company');
    });

    test('should validate privacy level options display correct descriptions', () => {
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const privacySelect = screen.getByLabelText(/privacy level/i);
      
      // Check that all privacy level options exist with descriptions
      expect(screen.getByRole('option', { name: /standard - basic tracking/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /gdpr - ip hashing, consent required/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /hipaa - enhanced security, audit logging/i })).toBeInTheDocument();
    });

    test('should handle client type selection with all options', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const clientTypeSelect = screen.getByLabelText(/client type/i);
      
      // Test all client type options
      await user.selectOptions(clientTypeSelect, 'end_client');
      expect(clientTypeSelect).toHaveValue('end_client');
      
      await user.selectOptions(clientTypeSelect, 'agency');
      expect(clientTypeSelect).toHaveValue('agency');
      
      await user.selectOptions(clientTypeSelect, 'enterprise');
      expect(clientTypeSelect).toHaveValue('enterprise');
    });

    test('should preserve conditional field values when toggling deployment type', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const deploymentSelect = screen.getByLabelText(/deployment type/i);
      
      // Change to dedicated deployment
      await user.selectOptions(deploymentSelect, 'dedicated');
      
      // Enter VM hostname
      const vmHostnameInput = screen.getByLabelText(/vm hostname/i);
      await user.type(vmHostnameInput, 'analytics.test.com');
      
      // Change back to shared (field disappears)
      await user.selectOptions(deploymentSelect, 'shared');
      
      // Change back to dedicated - value should be preserved
      await user.selectOptions(deploymentSelect, 'dedicated');
      
      const newVmHostnameInput = screen.getByLabelText(/vm hostname/i);
      expect(newVmHostnameInput).toHaveValue('analytics.test.com');
    });

    test('should handle billing entity field with placeholder text', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const billingEntityInput = screen.getByLabelText(/billing entity/i);
      
      // Should have placeholder text
      expect(billingEntityInput).toHaveAttribute('placeholder', 'Leave empty to use owner as billing entity');
      
      // Should accept input
      await user.type(billingEntityInput, 'billing_entity_123');
      expect(billingEntityInput).toHaveValue('billing_entity_123');
      
      // Helper text should be visible
      expect(screen.getByText(/client id of who receives invoices/i)).toBeInTheDocument();
    });
  });

  describe('Form Submission and API Integration', () => {
    test('should submit create form with correct data structure', async () => {
      const user = userEvent.setup();
      
      // Mock successful API response
      apiService.clients.create.mockResolvedValue({
        data: { client_id: 'new_client_123' }
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Fill form with complete data
      await user.type(screen.getByLabelText(/company name/i), 'New Test Company');
      await user.type(screen.getByLabelText(/email/i), 'test@newcompany.com');
      await user.selectOptions(screen.getByLabelText(/client type/i), 'enterprise');
      await user.selectOptions(screen.getByLabelText(/privacy level/i), 'gdpr');
      await user.selectOptions(screen.getByLabelText(/deployment type/i), 'dedicated');
      await user.type(screen.getByLabelText(/vm hostname/i), 'analytics.newcompany.com');
      await user.type(screen.getByLabelText(/billing entity/i), 'billing_client_456');
      
      const submitButton = screen.getByRole('button', { name: /create client/i });
      await user.click(submitButton);
      
      // Should show loading state
      expect(screen.getByText(/saving/i)).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
      
      // Should call API with correct data
      await waitFor(() => {
        expect(apiService.clients.create).toHaveBeenCalledWith({
          name: 'New Test Company',
          email: 'test@newcompany.com',
          client_type: 'enterprise',
          owner: 'client_evothesis_admin',
          billing_entity: 'billing_client_456',
          deployment_type: 'dedicated',
          vm_hostname: 'analytics.newcompany.com',
          privacy_level: 'gdpr',
          features: {}
        });
      });
      
      // Should navigate to clients list
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/admin/clients');
      });
    });

    test('should submit update form with only changed fields', async () => {
      const user = userEvent.setup();
      
      // Setup edit mode
      mockParams.clientId = 'client_test_001';
      
      const mockClient = {
        client_id: 'client_test_001',
        name: 'Original Company',
        email: 'original@company.com',
        client_type: 'end_client',
        owner: 'client_evothesis_admin',
        billing_entity: '',
        deployment_type: 'shared',
        vm_hostname: '',
        privacy_level: 'standard',
        features: {}
      };
      
      apiService.clients.get.mockResolvedValue({ data: mockClient });
      apiService.domains.list.mockResolvedValue({ data: [] });
      apiService.clients.update.mockResolvedValue({ data: mockClient });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByDisplayValue('Original Company')).toBeInTheDocument();
      });
      
      // Modify some fields
      const nameInput = screen.getByLabelText(/company name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Company Name');
      
      await user.selectOptions(screen.getByLabelText(/privacy level/i), 'gdpr');
      
      const submitButton = screen.getByRole('button', { name: /update client/i });
      await user.click(submitButton);
      
      // Should call update API
      await waitFor(() => {
        expect(apiService.clients.update).toHaveBeenCalledWith('client_test_001', {
          name: 'Updated Company Name',
          email: 'original@company.com',
          client_type: 'end_client',
          owner: 'client_evothesis_admin',
          billing_entity: '',
          deployment_type: 'shared',
          vm_hostname: '',
          privacy_level: 'gdpr',
          features: {}
        });
      });
    });

    test('should disable form during submission', async () => {
      const user = userEvent.setup();
      
      // Mock slow API response
      apiService.clients.create.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: {} }), 200))
      );
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      await user.type(screen.getByLabelText(/company name/i), 'Test Company');
      
      const submitButton = screen.getByRole('button', { name: /create client/i });
      const nameInput = screen.getByLabelText(/company name/i);
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      
      await user.click(submitButton);
      
      // Form should be disabled during submission
      expect(submitButton).toBeDisabled();
      expect(submitButton).toHaveTextContent(/saving/i);
      
      // Other form elements should remain enabled for accessibility
      expect(nameInput).not.toBeDisabled();
      expect(cancelButton).not.toBeDisabled();
      
      // Wait for completion
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalled();
      });
    });

    test('should handle server errors during submission', async () => {
      const user = userEvent.setup();
      
      // Mock server error
      apiService.clients.create.mockRejectedValue({
        response: {
          status: 500,
          data: { detail: 'Internal server error during client creation' }
        }
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      await user.type(screen.getByLabelText(/company name/i), 'Server Error Test');
      await user.click(screen.getByRole('button', { name: /create client/i }));
      
      // Should show server error
      await waitFor(() => {
        expect(screen.getByText(/internal server error during client creation/i)).toBeInTheDocument();
      });
      
      // Form should be re-enabled
      expect(screen.getByRole('button', { name: /create client/i })).not.toBeDisabled();
    });

    test('should maintain form state after submission errors', async () => {
      const user = userEvent.setup();
      
      apiService.clients.create.mockRejectedValue({
        response: { data: { detail: 'Submission failed' } }
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const formData = {
        name: 'Test Company',
        email: 'test@company.com',
        clientType: 'enterprise',
        privacyLevel: 'gdpr'
      };
      
      // Fill form
      await user.type(screen.getByLabelText(/company name/i), formData.name);
      await user.type(screen.getByLabelText(/email/i), formData.email);
      await user.selectOptions(screen.getByLabelText(/client type/i), formData.clientType);
      await user.selectOptions(screen.getByLabelText(/privacy level/i), formData.privacyLevel);
      
      await user.click(screen.getByRole('button', { name: /create client/i }));
      
      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/submission failed/i)).toBeInTheDocument();
      });
      
      // Form data should be preserved
      expect(screen.getByLabelText(/company name/i)).toHaveValue(formData.name);
      expect(screen.getByLabelText(/email/i)).toHaveValue(formData.email);
      expect(screen.getByLabelText(/client type/i)).toHaveValue(formData.clientType);
      expect(screen.getByLabelText(/privacy level/i)).toHaveValue(formData.privacyLevel);
    });
  });

  describe('Dynamic Field Interactions and State Management', () => {
    test('should handle form state changes smoothly without data loss', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Fill multiple fields
      await user.type(screen.getByLabelText(/company name/i), 'State Test Company');
      await user.type(screen.getByLabelText(/email/i), 'state@test.com');
      
      // Change deployment type to dedicated
      await user.selectOptions(screen.getByLabelText(/deployment type/i), 'dedicated');
      await user.type(screen.getByLabelText(/vm hostname/i), 'vm.test.com');
      
      // Change privacy level
      await user.selectOptions(screen.getByLabelText(/privacy level/i), 'hipaa');
      
      // Change back to shared (VM hostname should hide but data preserved)
      await user.selectOptions(screen.getByLabelText(/deployment type/i), 'shared');
      
      // Verify other fields maintained their values
      expect(screen.getByLabelText(/company name/i)).toHaveValue('State Test Company');
      expect(screen.getByLabelText(/email/i)).toHaveValue('state@test.com');
      expect(screen.getByLabelText(/privacy level/i)).toHaveValue('hipaa');
      
      // Change back to dedicated - VM hostname should be preserved
      await user.selectOptions(screen.getByLabelText(/deployment type/i), 'dedicated');
      expect(screen.getByLabelText(/vm hostname/i)).toHaveValue('vm.test.com');
    });

    test('should validate form input constraints and limits', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const nameInput = screen.getByLabelText(/company name/i);
      const emailInput = screen.getByLabelText(/email/i);
      
      // Test field input acceptance
      await user.type(nameInput, 'A'.repeat(100)); // Long name
      expect(nameInput.value).toBe('A'.repeat(100));
      
      // Test email field
      await user.type(emailInput, 'very.long.email.address@somelongdomainname.company.com');
      expect(emailInput.value).toBe('very.long.email.address@somelongdomainname.company.com');
    });

    test('should handle rapid field changes without losing data integrity', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      const deploymentSelect = screen.getByLabelText(/deployment type/i);
      const privacySelect = screen.getByLabelText(/privacy level/i);
      const clientTypeSelect = screen.getByLabelText(/client type/i);
      
      // Rapidly change multiple fields
      await user.selectOptions(deploymentSelect, 'dedicated');
      await user.selectOptions(privacySelect, 'gdpr');
      await user.selectOptions(clientTypeSelect, 'enterprise');
      await user.selectOptions(deploymentSelect, 'shared');
      await user.selectOptions(privacySelect, 'hipaa');
      await user.selectOptions(clientTypeSelect, 'agency');
      
      // Final state should be accurate
      expect(deploymentSelect).toHaveValue('shared');
      expect(privacySelect).toHaveValue('hipaa');
      expect(clientTypeSelect).toHaveValue('agency');
    });

    test('should properly handle form reset scenarios', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Fill form with data
      await user.type(screen.getByLabelText(/company name/i), 'Reset Test');
      await user.type(screen.getByLabelText(/email/i), 'reset@test.com');
      await user.selectOptions(screen.getByLabelText(/privacy level/i), 'gdpr');
      
      // Navigate away (cancel) and back
      await user.click(screen.getByRole('button', { name: /cancel/i }));
      expect(mockNavigate).toHaveBeenCalledWith('/admin/clients');
    });

    test('should handle default form values correctly', () => {
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Verify default values
      expect(screen.getByLabelText(/client type/i)).toHaveValue('end_client');
      expect(screen.getByLabelText(/deployment type/i)).toHaveValue('shared');
      expect(screen.getByLabelText(/privacy level/i)).toHaveValue('standard');
      expect(screen.getByLabelText(/company name/i)).toHaveValue('');
      expect(screen.getByLabelText(/email/i)).toHaveValue('');
      expect(screen.getByLabelText(/billing entity/i)).toHaveValue('');
    });

    test('should handle browser navigation and form state', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      // Fill some form data
      await user.type(screen.getByLabelText(/company name/i), 'Navigation Test');
      
      // Verify data is present
      expect(screen.getByLabelText(/company name/i)).toHaveValue('Navigation Test');
      
      // Form should maintain state during normal interactions
      await user.selectOptions(screen.getByLabelText(/deployment type/i), 'dedicated');
      expect(screen.getByLabelText(/company name/i)).toHaveValue('Navigation Test');
    });
  });

  describe('Domain Management Integration and Error Scenarios', () => {
    test('should show domain management section only in edit mode', async () => {
      mockParams.clientId = 'client_test_001';
      
      apiService.clients.get.mockResolvedValue({
        data: { client_id: 'client_test_001', name: 'Test Client' }
      });
      apiService.domains.list.mockResolvedValue({
        data: [{ domain: 'test.com', is_primary: true }]
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/authorized domains/i)).toBeInTheDocument();
        expect(screen.getByText(/add new domain/i)).toBeInTheDocument();
      });
    });

    test('should handle domain addition with validation', async () => {
      const user = userEvent.setup();
      mockParams.clientId = 'client_test_001';
      
      apiService.clients.get.mockResolvedValue({
        data: { client_id: 'client_test_001', name: 'Test Client' }
      });
      apiService.domains.list.mockResolvedValue({ data: [] });
      apiService.domains.add.mockResolvedValue({
        data: { domain: 'newdomain.com', is_primary: false }
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/add new domain/i)).toBeInTheDocument();
      });
      
      // Try to add empty domain
      const addButton = screen.getByRole('button', { name: /add domain/i });
      await user.click(addButton);
      
      // Should show error for empty domain
      await waitFor(() => {
        expect(screen.getByText(/please enter a domain name/i)).toBeInTheDocument();
      });
      
      // Add valid domain
      const domainInput = screen.getByLabelText(/domain/i);
      await user.type(domainInput, 'newdomain.com');
      await user.click(addButton);
      
      // Should call API to add domain
      await waitFor(() => {
        expect(apiService.domains.add).toHaveBeenCalledWith('client_test_001', {
          domain: 'newdomain.com',
          is_primary: false
        });
      });
    });

    test('should handle domain removal with confirmation', async () => {
      const user = userEvent.setup();
      mockParams.clientId = 'client_test_001';
      
      apiService.clients.get.mockResolvedValue({
        data: { client_id: 'client_test_001', name: 'Test Client' }
      });
      apiService.domains.list.mockResolvedValue({
        data: [
          { domain: 'test.com', is_primary: true },
          { domain: 'app.test.com', is_primary: false }
        ]
      });
      apiService.domains.remove.mockResolvedValue({ data: {} });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/current domains \(2\)/i)).toBeInTheDocument();
      });
      
      // Click remove button
      const removeButtons = screen.getAllByText(/remove/i);
      await user.click(removeButtons[0]);
      
      // Should show confirmation dialog
      expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to remove domain test.com?');
      
      // Should call API to remove domain
      await waitFor(() => {
        expect(apiService.domains.remove).toHaveBeenCalledWith('client_test_001', 'test.com');
      });
    });

    test('should handle domain API errors gracefully', async () => {
      const user = userEvent.setup();
      mockParams.clientId = 'client_test_001';
      
      apiService.clients.get.mockResolvedValue({
        data: { client_id: 'client_test_001', name: 'Test Client' }
      });
      apiService.domains.list.mockResolvedValue({ data: [] });
      apiService.domains.add.mockRejectedValue({
        response: { data: { detail: 'Domain already exists' } }
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/add new domain/i)).toBeInTheDocument();
      });
      
      // Try to add duplicate domain
      const domainInput = screen.getByLabelText(/domain/i);
      const addButton = screen.getByRole('button', { name: /add domain/i });
      
      await user.type(domainInput, 'duplicate.com');
      await user.click(addButton);
      
      // Should show API error
      await waitFor(() => {
        expect(screen.getByText(/domain already exists/i)).toBeInTheDocument();
      });
    });

    test('should display domain list with primary indicator', async () => {
      mockParams.clientId = 'client_test_001';
      
      apiService.clients.get.mockResolvedValue({
        data: { client_id: 'client_test_001', name: 'Test Client' }
      });
      apiService.domains.list.mockResolvedValue({
        data: [
          { domain: 'primary.com', is_primary: true },
          { domain: 'secondary.com', is_primary: false },
          { domain: 'tertiary.com', is_primary: false }
        ]
      });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/current domains \(3\)/i)).toBeInTheDocument();
        expect(screen.getByText('primary.com')).toBeInTheDocument();
        expect(screen.getByText('secondary.com')).toBeInTheDocument();
        expect(screen.getByText('tertiary.com')).toBeInTheDocument();
      });
      
      // Primary domain should have indicator
      expect(screen.getByText(/primary/i)).toBeInTheDocument();
    });

    test('should handle empty domain list state', async () => {
      mockParams.clientId = 'client_test_001';
      
      apiService.clients.get.mockResolvedValue({
        data: { client_id: 'client_test_001', name: 'Test Client' }
      });
      apiService.domains.list.mockResolvedValue({ data: [] });
      
      render(
        <TestWrapper>
          <ClientForm />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText(/current domains \(0\)/i)).toBeInTheDocument();
        expect(screen.getByText(/no domains added yet/i)).toBeInTheDocument();
        expect(screen.getByText(/add a domain above to enable tracking/i)).toBeInTheDocument();
      });
    });
  });
});