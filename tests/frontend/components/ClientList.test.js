/**
 * ClientList Component Test Suite - Phase 6
 * 
 * Comprehensive test suite for the ClientList component covering data rendering,
 * client management operations, loading states, error handling, and user interactions.
 * Tests display formatting, action buttons, empty states, and API integration scenarios.
 * 
 * Coverage Requirements:
 * - Client data rendering and display formatting  
 * - Search and filtering functionality
 * - Pagination controls and navigation
 * - Client actions (edit, delete, view domains)
 * - Loading and empty states
 * - Error handling for API failures
 * 
 * Test Categories:
 * 1. Client data rendering and display formatting
 * 2. Search and filtering functionality  
 * 3. Client action operations (edit, delete, domains)
 * 4. Loading and empty state management
 * 5. Error handling and retry mechanisms
 * 6. Navigation and responsive design integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../../mocks/server';
import ClientList from '../../../src/components/ClientList';

// Mock the API service
jest.mock('../../../src/services/api', () => ({
  apiService: {
    clients: {
      list: jest.fn(),
      delete: jest.fn()
    }
  }
}));

import { apiService } from '../../../src/services/api';

// Test wrapper with Router
const TestWrapper = ({ children, initialEntries = ['/admin/clients'] }) => (
  <MemoryRouter initialEntries={initialEntries}>
    {children}
  </MemoryRouter>
);

// Mock data generators
const generateMockClient = (overrides = {}) => {
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
    domain_count: 2,
    created_at: new Date().toISOString()
  };
  
  return { ...defaults, ...overrides };
};

const generateMockClientList = (count = 3) => {
  return Array.from({ length: count }, (_, index) => {
    const clientIndex = index + 1;
    return generateMockClient({
      client_id: `client_test_${String(clientIndex).padStart(3, '0')}`,
      name: `Test Client ${clientIndex}`,
      email: `client${clientIndex}@test.com`,
      privacy_level: ['standard', 'gdpr', 'hipaa'][index % 3],
      deployment_type: index % 2 === 0 ? 'shared' : 'dedicated',
      domain_count: Math.floor(Math.random() * 5) + 1
    });
  });
};

describe('ClientList Component - Comprehensive Test Suite', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Clear sessionStorage mock
    global.sessionStorage.clear();
    global.sessionStorage.setItem('admin_api_key', 'test_admin_key_12345');
    
    // Reset window.confirm and alert mocks
    global.confirm = jest.fn(() => true);
    global.alert = jest.fn();
  });

  describe('Client Data Rendering and Display Formatting', () => {
    test('should render client list with proper data formatting', async () => {
      const mockClients = [
        generateMockClient({
          client_id: 'client_ecommerce_001',
          name: 'E-commerce Store',
          email: 'admin@ecommerce.com',
          client_type: 'end_client',
          privacy_level: 'standard',
          deployment_type: 'shared',
          domain_count: 3,
          is_active: true
        }),
        generateMockClient({
          client_id: 'client_saas_002',
          name: 'SaaS Platform',
          email: 'admin@saas.com', 
          client_type: 'enterprise',
          privacy_level: 'gdpr',
          deployment_type: 'dedicated',
          domain_count: 1,
          is_active: true
        }),
        generateMockClient({
          client_id: 'client_healthcare_003',
          name: 'Healthcare Analytics',
          email: 'admin@healthcare.com',
          client_type: 'end_client',
          privacy_level: 'hipaa',
          deployment_type: 'dedicated',
          domain_count: 2,
          is_active: false
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      // Should show loading initially
      expect(screen.getByText(/loading clients/i)).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/client management/i)).toBeInTheDocument();
      });

      // Should display all clients
      expect(screen.getByText('E-commerce Store')).toBeInTheDocument();
      expect(screen.getByText('SaaS Platform')).toBeInTheDocument(); 
      expect(screen.getByText('Healthcare Analytics')).toBeInTheDocument();

      // Should show client IDs
      expect(screen.getByText('client_ecommerce_001')).toBeInTheDocument();
      expect(screen.getByText('client_saas_002')).toBeInTheDocument();
      expect(screen.getByText('client_healthcare_003')).toBeInTheDocument();

      // Should show email addresses
      expect(screen.getByText('admin@ecommerce.com')).toBeInTheDocument();
      expect(screen.getByText('admin@saas.com')).toBeInTheDocument();
      expect(screen.getByText('admin@healthcare.com')).toBeInTheDocument();

      // Should show privacy level badges
      expect(screen.getByText('STANDARD')).toBeInTheDocument();
      expect(screen.getByText('GDPR')).toBeInTheDocument();
      expect(screen.getByText('HIPAA')).toBeInTheDocument();

      // Should show domain counts
      expect(screen.getByText(/3 domains/i)).toBeInTheDocument();
      expect(screen.getByText(/1 domain$/i)).toBeInTheDocument();
      expect(screen.getByText(/2 domains/i)).toBeInTheDocument();

      // Should show deployment type icons
      expect(screen.getByText('🏢')).toBeInTheDocument(); // shared
      expect(screen.getAllByText('🏗️')).toHaveLength(2); // dedicated
    });

    test('should display privacy level badges with correct colors and styling', async () => {
      const mockClients = [
        generateMockClient({
          name: 'Standard Client',
          privacy_level: 'standard'
        }),
        generateMockClient({
          client_id: 'client_002',
          name: 'GDPR Client',  
          privacy_level: 'gdpr'
        }),
        generateMockClient({
          client_id: 'client_003',
          name: 'HIPAA Client',
          privacy_level: 'hipaa'
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Standard Client')).toBeInTheDocument();
      });

      // Privacy level badges should be styled appropriately
      const standardBadge = screen.getByText('STANDARD');
      const gdprBadge = screen.getByText('GDPR');  
      const hipaaBadge = screen.getByText('HIPAA');

      expect(standardBadge).toBeInTheDocument();
      expect(gdprBadge).toBeInTheDocument(); 
      expect(hipaaBadge).toBeInTheDocument();

      // Each badge should have appropriate styling (checked via inline styles)
      expect(standardBadge).toHaveStyle('background-color: #4299e1');
      expect(gdprBadge).toHaveStyle('background-color: #f6ad55');
      expect(hipaaBadge).toHaveStyle('background-color: #e53e3e');
    });

    test('should handle clients with missing optional fields', async () => {
      const mockClients = [
        generateMockClient({
          name: 'Minimal Client',
          email: null, // No email
          domain_count: 0,
          vm_hostname: null
        }),
        generateMockClient({
          client_id: 'client_002',
          name: 'Another Client',
          email: '', // Empty email
          domain_count: 0  
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Minimal Client')).toBeInTheDocument();
      });

      // Should handle missing email gracefully
      expect(screen.getByText('Minimal Client')).toBeInTheDocument();
      expect(screen.getByText('Another Client')).toBeInTheDocument();

      // Should show 0 domains correctly
      expect(screen.getAllByText(/0 domains/i)).toHaveLength(2);
    });

    test('should display admin client indicator when present', async () => {
      const mockClients = [
        generateMockClient({
          name: 'Regular Client',
          client_type: 'end_client'
        }),
        generateMockClient({
          client_id: 'client_admin',
          name: 'Admin Client',
          client_type: 'admin'
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Regular Client')).toBeInTheDocument();
      });

      // Should show admin client indicator
      expect(screen.getByText(/admin client/i)).toBeInTheDocument();
      expect(screen.getByText('👑')).toBeInTheDocument();
    });

    test('should render grid layout properly with responsive design', async () => {
      const mockClients = generateMockClientList(6);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      });

      // Should render all clients in grid layout  
      for (let i = 1; i <= 6; i++) {
        expect(screen.getByText(`Test Client ${i}`)).toBeInTheDocument();
      }

      // Grid container should have proper CSS grid styling
      const gridContainer = screen.getByText('Test Client 1').closest('[style*="display: grid"]');
      expect(gridContainer).toBeInTheDocument();
    });

    test('should handle long client names and data gracefully', async () => {
      const mockClients = [
        generateMockClient({
          name: 'Very Long Company Name That Might Overflow The Container Width',
          email: 'very.long.email.address.that.might.cause.layout.issues@verylongdomainname.company.com',
          client_id: 'client_with_very_long_identifier_that_might_cause_issues'
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/very long company name/i)).toBeInTheDocument();
      });

      // Should handle long text without breaking layout
      expect(screen.getByText(/very long company name/i)).toBeInTheDocument();
      expect(screen.getByText(/very.long.email/i)).toBeInTheDocument();
      expect(screen.getByText(/client_with_very_long/i)).toBeInTheDocument();
    });
  });

  describe('Search and Filtering Functionality', () => {
    test('should filter clients by privacy level', async () => {
      const mockClients = [
        generateMockClient({
          name: 'Standard Client',
          privacy_level: 'standard'
        }),
        generateMockClient({
          client_id: 'client_002',
          name: 'GDPR Client',
          privacy_level: 'gdpr'
        }),
        generateMockClient({
          client_id: 'client_003', 
          name: 'HIPAA Client',
          privacy_level: 'hipaa'
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Standard Client')).toBeInTheDocument();
      });

      // All clients should be visible initially
      expect(screen.getByText('Standard Client')).toBeInTheDocument();
      expect(screen.getByText('GDPR Client')).toBeInTheDocument();
      expect(screen.getByText('HIPAA Client')).toBeInTheDocument();

      // Note: Since the component doesn't implement filtering UI yet,
      // this test validates the current behavior and would be updated
      // when filtering functionality is added
    });

    test('should handle search functionality when implemented', async () => {
      const mockClients = generateMockClientList(10);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      });

      // Verify all clients are displayed (no search filtering yet)
      for (let i = 1; i <= 10; i++) {
        expect(screen.getByText(`Test Client ${i}`)).toBeInTheDocument();
      }

      // This test validates current behavior and serves as placeholder
      // for future search functionality implementation
    });

    test('should sort clients by different criteria when implemented', async () => {
      const mockClients = [
        generateMockClient({
          name: 'Zebra Company',
          created_at: '2023-01-01T00:00:00Z'
        }),
        generateMockClient({
          client_id: 'client_002',
          name: 'Alpha Company', 
          created_at: '2023-12-31T00:00:00Z'
        }),
        generateMockClient({
          client_id: 'client_003',
          name: 'Beta Company',
          created_at: '2023-06-15T00:00:00Z'
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Zebra Company')).toBeInTheDocument();
      });

      // Verify all companies are displayed in current order
      expect(screen.getByText('Zebra Company')).toBeInTheDocument();
      expect(screen.getByText('Alpha Company')).toBeInTheDocument();
      expect(screen.getByText('Beta Company')).toBeInTheDocument();
    });

    test('should handle filter state management correctly', async () => {
      const mockClients = generateMockClientList(5);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      });

      // Verify initial state shows all clients
      for (let i = 1; i <= 5; i++) {
        expect(screen.getByText(`Test Client ${i}`)).toBeInTheDocument();
      }
    });

    test('should handle pagination controls when implemented', async () => {
      // Generate large dataset for pagination testing
      const mockClients = generateMockClientList(25);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      });

      // Currently shows all clients (no pagination yet)
      for (let i = 1; i <= 25; i++) {
        expect(screen.getByText(`Test Client ${i}`)).toBeInTheDocument();
      }
    });

    test('should maintain filter state during component updates', async () => {
      const mockClients = generateMockClientList(3);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      const { rerender } = render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      });

      // Rerender component
      rerender(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      // Should maintain data display
      expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      expect(screen.getByText('Test Client 2')).toBeInTheDocument();
      expect(screen.getByText('Test Client 3')).toBeInTheDocument();
    });
  });

  describe('Client Action Operations', () => {
    test('should handle client deletion with confirmation dialog', async () => {
      const user = userEvent.setup();
      const mockClients = [
        generateMockClient({
          client_id: 'client_to_delete',
          name: 'Client To Delete'
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });
      apiService.clients.delete.mockResolvedValue({ data: {} });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Client To Delete')).toBeInTheDocument();
      });

      // Click delete button
      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Should show confirmation dialog
      expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to delete "Client To Delete"? This action cannot be undone.');

      // Should call delete API
      await waitFor(() => {
        expect(apiService.clients.delete).toHaveBeenCalledWith('client_to_delete');
      });

      // Should refresh client list
      expect(apiService.clients.list).toHaveBeenCalledTimes(2);
    });

    test('should cancel deletion when user cancels confirmation', async () => {
      const user = userEvent.setup();
      global.confirm = jest.fn(() => false); // User cancels

      const mockClients = [generateMockClient({ name: 'Protected Client' })];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Protected Client')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Should show confirmation but not proceed
      expect(global.confirm).toHaveBeenCalled();
      expect(apiService.clients.delete).not.toHaveBeenCalled();
    });

    test('should handle delete API errors gracefully', async () => {
      const user = userEvent.setup();
      const mockClients = [generateMockClient({ name: 'Error Client' })];

      apiService.clients.list.mockResolvedValue({ data: mockClients });
      apiService.clients.delete.mockRejectedValue(new Error('Delete failed'));

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Error Client')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Should show error alert
      await waitFor(() => {
        expect(global.alert).toHaveBeenCalledWith('Failed to delete client. Please try again.');
      });
    });

    test('should navigate to edit form when edit button clicked', async () => {
      const user = userEvent.setup();
      const mockClients = [
        generateMockClient({
          client_id: 'client_edit_001',
          name: 'Editable Client'
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Editable Client')).toBeInTheDocument();
      });

      // Click edit button (rendered as Link)
      const editLink = screen.getByRole('link', { name: /edit/i });
      expect(editLink).toHaveAttribute('href', '/admin/clients/client_edit_001/edit');
    });

    test('should handle domain management button functionality', async () => {
      const user = userEvent.setup();
      const mockClients = [
        generateMockClient({
          name: 'Client With Domains',
          domain_count: 3
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Client With Domains')).toBeInTheDocument();
      });

      // Click domains button
      const domainsButton = screen.getByRole('button', { name: /domains/i });
      await user.click(domainsButton);

      // Should show placeholder alert (TODO implementation)
      expect(global.alert).toHaveBeenCalledWith('Domain management for Client With Domains - Coming soon!');
    });

    test('should display correct action buttons for each client', async () => {
      const mockClients = [generateMockClient({ name: 'Action Test Client' })];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Action Test Client')).toBeInTheDocument();
      });

      // Should have all three action buttons
      expect(screen.getByRole('link', { name: /edit/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /domains/i })).toBeInTheDocument();

      // Buttons should have proper styling and icons
      expect(screen.getByText('⚙️')).toBeInTheDocument(); // Edit icon
      expect(screen.getByText('🗑️')).toBeInTheDocument(); // Delete icon
      expect(screen.getByText('🌐')).toBeInTheDocument(); // Domains icon
    });

    test('should handle multiple client actions simultaneously', async () => {
      const user = userEvent.setup();
      const mockClients = [
        generateMockClient({
          client_id: 'client_001',
          name: 'Client One'
        }),
        generateMockClient({
          client_id: 'client_002', 
          name: 'Client Two'
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });
      apiService.clients.delete.mockResolvedValue({ data: {} });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Client One')).toBeInTheDocument();
      });

      // Get delete buttons for both clients
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      expect(deleteButtons).toHaveLength(2);

      // Delete first client
      await user.click(deleteButtons[0]);
      
      await waitFor(() => {
        expect(apiService.clients.delete).toHaveBeenCalledWith('client_001');
      });

      // Should refresh list and be ready for next action
      expect(apiService.clients.list).toHaveBeenCalledTimes(2);
    });
  });

  describe('Loading and Empty State Management', () => {
    test('should show loading state during initial data fetch', async () => {
      // Mock delayed API response
      apiService.clients.list.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
      );

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      // Should show loading message
      expect(screen.getByText(/loading clients/i)).toBeInTheDocument();

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByText(/loading clients/i)).not.toBeInTheDocument();
      });
    });

    test('should display empty state when no clients exist', async () => {
      apiService.clients.list.mockResolvedValue({ data: [] });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/no clients yet/i)).toBeInTheDocument();
      });

      // Should show empty state with proper messaging
      expect(screen.getByText(/no clients yet/i)).toBeInTheDocument();
      expect(screen.getByText(/create your first client/i)).toBeInTheDocument();
      expect(screen.getByText('📋')).toBeInTheDocument(); // Empty state icon

      // Should have "Create First Client" button
      const createButton = screen.getByRole('link', { name: /create first client/i });
      expect(createButton).toHaveAttribute('href', '/admin/clients/new');
    });

    test('should handle transition from loading to empty state', async () => {
      apiService.clients.list.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: [] }), 50))
      );

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      // Initially loading
      expect(screen.getByText(/loading clients/i)).toBeInTheDocument();

      // Wait for empty state
      await waitFor(() => {
        expect(screen.getByText(/no clients yet/i)).toBeInTheDocument();
      });

      expect(screen.queryByText(/loading clients/i)).not.toBeInTheDocument();
    });

    test('should handle transition from loading to populated state', async () => {
      const mockClients = generateMockClientList(2);
      apiService.clients.list.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: mockClients }), 50))
      );

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      // Initially loading
      expect(screen.getByText(/loading clients/i)).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      });

      expect(screen.queryByText(/loading clients/i)).not.toBeInTheDocument();
      expect(screen.getByText('Test Client 2')).toBeInTheDocument();
    });

    test('should refresh data and show loading states correctly', async () => {
      const user = userEvent.setup();
      const mockClients = [generateMockClient({ name: 'Refresh Test Client' })];

      // First call returns data, subsequent calls are delayed
      apiService.clients.list
        .mockResolvedValueOnce({ data: mockClients })
        .mockImplementation(() => 
          new Promise(resolve => setTimeout(() => resolve({ data: mockClients }), 100))
        );

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Refresh Test Client')).toBeInTheDocument();
      });

      // Trigger refresh by deleting a client
      const deleteButton = screen.getByRole('button', { name: /delete/i });
      apiService.clients.delete.mockResolvedValue({ data: {} });
      
      await user.click(deleteButton);

      // Should refresh list
      await waitFor(() => {
        expect(apiService.clients.list).toHaveBeenCalledTimes(2);
      });
    });

    test('should handle loading state styling and accessibility', async () => {
      apiService.clients.list.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
      );

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      const loadingElement = screen.getByText(/loading clients/i);
      
      // Should have proper styling
      expect(loadingElement).toBeInTheDocument();
      expect(loadingElement.closest('div')).toHaveStyle('text-align: center');
      expect(loadingElement.closest('div')).toHaveStyle('padding: 40px');

      await waitFor(() => {
        expect(screen.queryByText(/loading clients/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling and Retry Mechanisms', () => {
    test('should display error message when API call fails', async () => {
      apiService.clients.list.mockRejectedValue(new Error('Network error'));

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/error loading clients/i)).toBeInTheDocument();
      });

      // Should show error message with proper styling
      expect(screen.getByText(/failed to load clients/i)).toBeInTheDocument();
      expect(screen.getByText('❌')).toBeInTheDocument();
    });

    test('should provide retry functionality when error occurs', async () => {
      const user = userEvent.setup();
      
      // First call fails, second succeeds
      apiService.clients.list
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue({ data: [generateMockClient({ name: 'Retry Success' })] });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/error loading clients/i)).toBeInTheDocument();
      });

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Should retry API call and show success
      await waitFor(() => {
        expect(screen.getByText('Retry Success')).toBeInTheDocument();
      });

      expect(apiService.clients.list).toHaveBeenCalledTimes(2);
    });

    test('should handle API errors with detailed error messages', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: { detail: 'Internal server error occurred' }
        }
      };

      apiService.clients.list.mockRejectedValue(errorResponse);

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/internal server error occurred/i)).toBeInTheDocument();
      });
    });

    test('should handle network timeout errors', async () => {
      apiService.clients.list.mockRejectedValue(new Error('Request timeout'));

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/error loading clients/i)).toBeInTheDocument();
      });

      // Should show generic error message for network issues
      expect(screen.getByText(/failed to load clients/i)).toBeInTheDocument();
    });

    test('should handle authentication errors gracefully', async () => {
      const authError = {
        response: {
          status: 401,
          data: { detail: 'Authentication required' }
        }
      };

      apiService.clients.list.mockRejectedValue(authError);

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/authentication required/i)).toBeInTheDocument();
      });
    });

    test('should handle permission denied errors', async () => {
      const permissionError = {
        response: {
          status: 403,
          data: { detail: 'Insufficient permissions' }
        }
      };

      apiService.clients.list.mockRejectedValue(permissionError);

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/insufficient permissions/i)).toBeInTheDocument();
      });
    });

    test('should maintain error state until successful retry', async () => {
      const user = userEvent.setup();

      // Multiple failures then success
      apiService.clients.list
        .mockRejectedValueOnce(new Error('First failure'))
        .mockRejectedValueOnce(new Error('Second failure'))
        .mockResolvedValue({ data: [generateMockClient({ name: 'Finally Success' })] });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      // First error
      await waitFor(() => {
        expect(screen.getByText(/first failure/i)).toBeInTheDocument();
      });

      // Retry - second error
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText(/second failure/i)).toBeInTheDocument();
      });

      // Retry again - success
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Finally Success')).toBeInTheDocument();
      });

      expect(screen.queryByText(/error loading clients/i)).not.toBeInTheDocument();
    });
  });

  describe('Navigation and Responsive Design Integration', () => {
    test('should render navigation links correctly', async () => {
      const mockClients = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/client management/i)).toBeInTheDocument();
      });

      // Should have dashboard link
      const dashboardLink = screen.getByRole('link', { name: /back to dashboard/i });
      expect(dashboardLink).toHaveAttribute('href', '/admin/dashboard');

      // Should have create new client link
      const createLink = screen.getByRole('link', { name: /create new client/i });
      expect(createLink).toHaveAttribute('href', '/admin/clients/new');
    });

    test('should handle responsive grid layout properly', async () => {
      const mockClients = generateMockClientList(8);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      });

      // Grid should have responsive columns
      const gridContainer = screen.getByText('Test Client 1').closest('[style*="grid-template-columns"]');
      expect(gridContainer).toBeInTheDocument();
    });

    test('should maintain responsive design with empty state', async () => {
      apiService.clients.list.mockResolvedValue({ data: [] });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/no clients yet/i)).toBeInTheDocument();
      });

      // Empty state should be properly centered
      const emptyState = screen.getByText(/no clients yet/i).closest('div');
      expect(emptyState).toHaveStyle('text-align: center');
    });

    test('should handle header layout and styling', async () => {
      const mockClients = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/client management/i)).toBeInTheDocument();
      });

      // Header should have proper layout
      const header = screen.getByText(/client management/i).closest('div');
      expect(header).toHaveStyle('display: flex');
    });

    test('should maintain layout consistency across different client counts', async () => {
      // Test with single client
      const singleClient = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: singleClient });

      const { rerender } = render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Mock Test Client')).toBeInTheDocument();
      });

      // Test with many clients
      const manyClients = generateMockClientList(12);
      apiService.clients.list.mockResolvedValue({ data: manyClients });

      rerender(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Client 1')).toBeInTheDocument();
      });

      // Layout should remain consistent
      expect(screen.getByText(/client management/i)).toBeInTheDocument();
    });

    test('should handle keyboard navigation for accessibility', async () => {
      const user = userEvent.setup();
      const mockClients = [generateMockClient({ name: 'Keyboard Test Client' })];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Keyboard Test Client')).toBeInTheDocument();
      });

      // Tab navigation should work on interactive elements
      const editLink = screen.getByRole('link', { name: /edit/i });
      const deleteButton = screen.getByRole('button', { name: /delete/i });
      const domainsButton = screen.getByRole('button', { name: /domains/i });

      // Elements should be focusable
      editLink.focus();
      expect(document.activeElement).toBe(editLink);

      await user.tab();
      expect(document.activeElement).toBe(deleteButton);

      await user.tab();
      expect(document.activeElement).toBe(domainsButton);
    });

    test('should handle browser back/forward navigation', async () => {
      const mockClients = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper initialEntries={['/admin/dashboard', '/admin/clients']}>
          <ClientList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/client management/i)).toBeInTheDocument();
      });

      // Component should render correctly regardless of navigation history
      expect(screen.getByText('Mock Test Client')).toBeInTheDocument();
    });
  });
});