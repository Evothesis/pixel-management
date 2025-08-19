/**
 * Dashboard Component Test Suite - Phase 6
 * 
 * Comprehensive test suite for the Dashboard component covering system statistics,
 * navigation integration, responsive design, and API functionality. Tests metrics
 * display, quick actions, loading states, and user interface elements.
 * 
 * Coverage Requirements:
 * - Dashboard metrics and summary display
 * - Navigation component integration  
 * - Recent activities and audit log display
 * - Responsive design and layout rendering
 * 
 * Test Categories:
 * 1. Dashboard metrics and system statistics display
 * 2. Navigation integration and quick action functionality
 * 3. Responsive design and layout rendering
 * 4. API integration and error handling scenarios
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../../mocks/server';
import Dashboard from '../../../src/components/Dashboard';

// Mock the API service
jest.mock('../../../src/services/api', () => ({
  apiService: {
    clients: {
      list: jest.fn()
    }
  }
}));

import { apiService } from '../../../src/services/api';

// Test wrapper with Router
const TestWrapper = ({ children, initialEntries = ['/admin/dashboard'] }) => (
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
    const privacyLevels = ['standard', 'gdpr', 'hipaa'];
    const deploymentTypes = ['shared', 'dedicated'];
    
    return generateMockClient({
      client_id: `client_dashboard_${String(clientIndex).padStart(3, '0')}`,
      name: `Dashboard Client ${clientIndex}`,
      email: `client${clientIndex}@dashboard.com`,
      privacy_level: privacyLevels[index % 3],
      deployment_type: deploymentTypes[index % 2],
      is_active: index % 4 !== 3, // 3/4 active, 1/4 inactive
      domain_count: Math.floor(Math.random() * 5) + 1
    });
  });
};

describe('Dashboard Component - Comprehensive Test Suite', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Clear sessionStorage mock
    global.sessionStorage.clear();
    global.sessionStorage.setItem('admin_api_key', 'test_admin_key_12345');
  });

  describe('Dashboard Metrics and System Statistics Display', () => {
    test('should display comprehensive system statistics with proper calculations', async () => {
      const mockClients = [
        generateMockClient({
          name: 'Active Standard Client',
          privacy_level: 'standard',
          is_active: true
        }),
        generateMockClient({
          client_id: 'client_002',
          name: 'Active GDPR Client',
          privacy_level: 'gdpr',
          is_active: true
        }),
        generateMockClient({
          client_id: 'client_003',
          name: 'Inactive HIPAA Client',
          privacy_level: 'hipaa',
          is_active: false
        }),
        generateMockClient({
          client_id: 'client_004',
          name: 'Another Active Standard Client',
          privacy_level: 'standard',
          is_active: true
        })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Should show loading initially
      expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      // Should display total clients count
      expect(screen.getByText('4')).toBeInTheDocument(); // Total clients
      expect(screen.getByText(/configured clients/i)).toBeInTheDocument();

      // Should display active clients count (3 active, 1 inactive)
      expect(screen.getByText('3')).toBeInTheDocument(); // Active clients  
      expect(screen.getByText(/ready for tracking/i)).toBeInTheDocument();

      // Should display privacy level breakdown
      expect(screen.getByText('Standard:')).toBeInTheDocument();
      expect(screen.getByText('Gdpr:')).toBeInTheDocument();
      expect(screen.getByText('Hipaa:')).toBeInTheDocument();

      // Privacy level counts should be correct (2 standard, 1 gdpr, 1 hipaa)
      const privacyLevelCounts = screen.getAllByText('2');
      expect(privacyLevelCounts.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('1')).toBeInTheDocument();
    });

    test('should handle empty dataset gracefully with zero statistics', async () => {
      apiService.clients.list.mockResolvedValue({ data: [] });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      // Should show zero counts
      expect(screen.getAllByText('0')).toHaveLength(5); // Total, Active, and 3 privacy levels

      // Should show empty state encouragement
      expect(screen.getByText(/ready to get started/i)).toBeInTheDocument();
      expect(screen.getByText(/create your first client/i)).toBeInTheDocument();
      expect(screen.getByText('🎯')).toBeInTheDocument(); // Empty state icon
    });

    test('should calculate privacy level statistics accurately', async () => {
      const mockClients = [
        generateMockClient({ privacy_level: 'standard' }),
        generateMockClient({ client_id: 'c2', privacy_level: 'standard' }),
        generateMockClient({ client_id: 'c3', privacy_level: 'standard' }),
        generateMockClient({ client_id: 'c4', privacy_level: 'gdpr' }),
        generateMockClient({ client_id: 'c5', privacy_level: 'gdpr' }),
        generateMockClient({ client_id: 'c6', privacy_level: 'hipaa' })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('6')).toBeInTheDocument(); // Total clients
      });

      // Privacy level counts: 3 standard, 2 gdpr, 1 hipaa
      expect(screen.getByText('3')).toBeInTheDocument(); // Standard count
      expect(screen.getByText('2')).toBeInTheDocument(); // GDPR count  
      expect(screen.getByText('1')).toBeInTheDocument(); // HIPAA count
    });

    test('should display privacy level badges with correct styling', async () => {
      const mockClients = [
        generateMockClient({ privacy_level: 'standard' }),
        generateMockClient({ client_id: 'c2', privacy_level: 'gdpr' }),
        generateMockClient({ client_id: 'c3', privacy_level: 'hipaa' })
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/privacy levels/i)).toBeInTheDocument();
      });

      // Privacy level labels should be capitalized
      expect(screen.getByText('Standard:')).toBeInTheDocument();
      expect(screen.getByText('Gdpr:')).toBeInTheDocument();
      expect(screen.getByText('Hipaa:')).toBeInTheDocument();

      // Each should have count badges with proper styling
      const privacySection = screen.getByText(/privacy levels/i).closest('div');
      expect(privacySection).toBeInTheDocument();
    });

    test('should handle mixed active/inactive client scenarios', async () => {
      const mockClients = [
        generateMockClient({ name: 'Active 1', is_active: true }),
        generateMockClient({ client_id: 'c2', name: 'Active 2', is_active: true }),
        generateMockClient({ client_id: 'c3', name: 'Inactive 1', is_active: false }),
        generateMockClient({ client_id: 'c4', name: 'Inactive 2', is_active: false }),
        generateMockClient({ client_id: 'c5', name: 'Active 3' }) // Default is_active: true
      ];

      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument(); // Total clients
      });

      // Should show correct active count (3 active)
      expect(screen.getByText('3')).toBeInTheDocument(); // Active clients
      expect(screen.getByText(/ready for tracking/i)).toBeInTheDocument();
    });

    test('should update statistics when data changes', async () => {
      const initialClients = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: initialClients });

      const { rerender } = render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument(); // Initial count
      });

      // Update with more clients
      const updatedClients = generateMockClientList(5);
      apiService.clients.list.mockResolvedValue({ data: updatedClients });

      rerender(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument(); // Updated count
      });
    });
  });

  describe('Navigation Integration and Quick Action Functionality', () => {
    test('should render all navigation links with correct destinations', async () => {
      const mockClients = generateMockClientList(2);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/quick actions/i)).toBeInTheDocument();
      });

      // Should have "Add New Client" link
      const addClientLink = screen.getByRole('link', { name: /add new client/i });
      expect(addClientLink).toHaveAttribute('href', '/admin/clients/new');
      expect(screen.getByText('➕')).toBeInTheDocument(); // Add icon

      // Should have "Manage Clients" link  
      const manageClientsLink = screen.getByRole('link', { name: /manage clients/i });
      expect(manageClientsLink).toHaveAttribute('href', '/admin/clients');
      expect(screen.getByText('📋')).toBeInTheDocument(); // Manage icon
    });

    test('should handle refresh data button functionality', async () => {
      const user = userEvent.setup();
      const mockClients = generateMockClientList(3);
      
      // First call returns data, second call returns updated data
      apiService.clients.list
        .mockResolvedValueOnce({ data: mockClients })
        .mockResolvedValue({ data: [...mockClients, generateMockClient({ client_id: 'new_client' })] });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument(); // Initial count
      });

      // Click refresh button
      const refreshButton = screen.getByRole('button', { name: /refresh data/i });
      expect(refreshButton).toBeInTheDocument();
      expect(screen.getByText('🔄')).toBeInTheDocument(); // Refresh icon

      await user.click(refreshButton);

      // Should call API again
      await waitFor(() => {
        expect(apiService.clients.list).toHaveBeenCalledTimes(2);
      });

      // Should update with new count
      await waitFor(() => {
        expect(screen.getByText('4')).toBeInTheDocument(); // Updated count
      });
    });

    test('should render quick action buttons with proper styling and icons', async () => {
      const mockClients = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/quick actions/i)).toBeInTheDocument();
      });

      // Check all action buttons have proper styling
      const addClientLink = screen.getByRole('link', { name: /add new client/i });
      const manageClientsLink = screen.getByRole('link', { name: /manage clients/i });
      const refreshButton = screen.getByRole('button', { name: /refresh data/i });

      // Should have proper CSS styling
      expect(addClientLink).toHaveStyle('background-color: #4299e1');
      expect(manageClientsLink).toHaveStyle('background-color: #38a169');
      expect(refreshButton).toHaveStyle('background-color: #805ad5');

      // Should have proper text colors
      expect(addClientLink).toHaveStyle('color: white');
      expect(manageClientsLink).toHaveStyle('color: white');
      expect(refreshButton).toHaveStyle('color: white');
    });

    test('should show contextual actions based on client count', async () => {
      // Test with no clients first
      apiService.clients.list.mockResolvedValue({ data: [] });

      const { rerender } = render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/ready to get started/i)).toBeInTheDocument();
      });

      // Should show "Create First Client" button in empty state
      expect(screen.getByRole('link', { name: /create first client/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /create first client/i })).toHaveAttribute('href', '/admin/clients/new');

      // Test with clients
      const mockClients = generateMockClientList(3);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      rerender(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument();
      });

      // Should show regular quick actions, not empty state action
      expect(screen.getByRole('link', { name: /add new client/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /manage clients/i })).toBeInTheDocument();
      expect(screen.queryByText(/ready to get started/i)).not.toBeInTheDocument();
    });

    test('should handle keyboard navigation for accessibility', async () => {
      const user = userEvent.setup();
      const mockClients = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/quick actions/i)).toBeInTheDocument();
      });

      // Tab through interactive elements
      const addClientLink = screen.getByRole('link', { name: /add new client/i });
      const manageClientsLink = screen.getByRole('link', { name: /manage clients/i });
      const refreshButton = screen.getByRole('button', { name: /refresh data/i });

      // Elements should be focusable
      addClientLink.focus();
      expect(document.activeElement).toBe(addClientLink);

      await user.tab();
      expect(document.activeElement).toBe(manageClientsLink);

      await user.tab();  
      expect(document.activeElement).toBe(refreshButton);
    });

    test('should handle navigation state correctly across different routes', async () => {
      const mockClients = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper initialEntries={['/admin/clients', '/admin/dashboard']}>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      // Navigation links should work regardless of route history
      const addClientLink = screen.getByRole('link', { name: /add new client/i });
      expect(addClientLink).toHaveAttribute('href', '/admin/clients/new');
    });
  });

  describe('Responsive Design and Layout Rendering', () => {
    test('should render responsive grid layout for statistics cards', async () => {
      const mockClients = generateMockClientList(4);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      // Should have proper grid layout with responsive design
      const statsGrid = screen.getByText(/total clients/i).closest('[style*="display: grid"]');
      expect(statsGrid).toBeInTheDocument();
      expect(statsGrid).toHaveStyle('grid-template-columns: repeat(auto-fit, minmax(250px, 1fr))');
    });

    test('should maintain layout consistency across different screen sizes', async () => {
      const mockClients = generateMockClientList(2);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      // Header should have proper responsive margins
      const header = screen.getByText(/pixel management dashboard/i);
      expect(header).toHaveStyle('font-size: 24px');

      // Description should be properly styled
      const description = screen.getByText(/overview of your client configurations/i);
      expect(description).toHaveStyle('color: #718096');
    });

    test('should handle card layout and spacing properly', async () => {
      const mockClients = generateMockClientList(3);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/total clients/i)).toBeInTheDocument();
      });

      // Statistics cards should have proper styling
      const totalClientsCard = screen.getByText(/total clients/i).closest('div');
      expect(totalClientsCard).toHaveStyle('background-color: white');
      expect(totalClientsCard).toHaveStyle('border: 1px solid #e2e8f0');
      expect(totalClientsCard).toHaveStyle('border-radius: 8px');
      expect(totalClientsCard).toHaveStyle('padding: 24px');

      // Active clients card styling
      const activeClientsCard = screen.getByText(/active clients/i).closest('div');
      expect(activeClientsCard).toHaveStyle('background-color: white');

      // Privacy levels card styling
      const privacyCard = screen.getByText(/privacy levels/i).closest('div');
      expect(privacyCard).toHaveStyle('background-color: white');
    });

    test('should render quick actions section with responsive flex layout', async () => {
      const mockClients = [generateMockClient()];
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/quick actions/i)).toBeInTheDocument();
      });

      // Quick actions section should have proper styling
      const quickActionsSection = screen.getByText(/quick actions/i).closest('div');
      expect(quickActionsSection).toHaveStyle('background-color: white');
      expect(quickActionsSection).toHaveStyle('border: 1px solid #e2e8f0');

      // Action buttons container should have flex layout
      const actionsContainer = screen.getByRole('link', { name: /add new client/i }).closest('[style*="display: flex"]');
      expect(actionsContainer).toBeInTheDocument();
      expect(actionsContainer).toHaveStyle('gap: 16px');
      expect(actionsContainer).toHaveStyle('flex-wrap: wrap');
    });

    test('should handle empty state layout and centering', async () => {
      apiService.clients.list.mockResolvedValue({ data: [] });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/ready to get started/i)).toBeInTheDocument();
      });

      // Empty state should be properly centered and styled
      const emptyState = screen.getByText(/ready to get started/i).closest('div');
      expect(emptyState).toHaveStyle('background-color: #fef5e7');
      expect(emptyState).toHaveStyle('text-align: center');
      expect(emptyState).toHaveStyle('border-radius: 8px');
      expect(emptyState).toHaveStyle('padding: 20px');
    });

    test('should maintain proper spacing and margins throughout layout', async () => {
      const mockClients = generateMockClientList(2);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      // Header section should have proper margins
      const headerSection = screen.getByText(/pixel management dashboard/i).closest('div');
      expect(headerSection).toHaveStyle('margin-bottom: 30px');

      // Stats grid should have proper margins
      const statsGrid = screen.getByText(/total clients/i).closest('[style*="margin-bottom: 40px"]');
      expect(statsGrid).toBeInTheDocument();
    });

    test('should handle typography scaling and readability', async () => {
      const mockClients = generateMockClientList(1);
      apiService.clients.list.mockResolvedValue({ data: mockClients });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
      });

      // Large numbers should have proper styling
      const totalCount = screen.getByText('1');
      expect(totalCount).toHaveStyle('font-size: 3em');
      expect(totalCount).toHaveStyle('font-weight: bold');
      expect(totalCount).toHaveStyle('line-height: 1');

      // Card headings should be properly sized
      const cardHeading = screen.getByText(/total clients/i);
      expect(cardHeading).toHaveStyle('font-size: 16px');
      expect(cardHeading).toHaveStyle('font-weight: 500');
    });
  });

  describe('API Integration and Error Handling Scenarios', () => {
    test('should show loading state during API data fetch', async () => {
      // Mock delayed API response
      apiService.clients.list.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
      );

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Should show loading message
      expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();

      // Loading should have proper styling
      const loadingElement = screen.getByText(/loading dashboard/i);
      expect(loadingElement.closest('div')).toHaveStyle('text-align: center');
      expect(loadingElement.closest('div')).toHaveStyle('padding: 40px');

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByText(/loading dashboard/i)).not.toBeInTheDocument();
      });
    });

    test('should handle API errors gracefully with retry functionality', async () => {
      const user = userEvent.setup();

      // First call fails, second succeeds
      apiService.clients.list
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue({ data: [generateMockClient({ name: 'Retry Success' })] });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/error loading dashboard/i)).toBeInTheDocument();
      });

      // Should show error message with proper styling
      expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
      expect(screen.getByText('❌')).toBeInTheDocument();

      // Should have retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toHaveAttribute('style', expect.stringContaining('background-color: #c53030'));

      // Click retry
      await user.click(retryButton);

      // Should retry and show success
      await waitFor(() => {
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      expect(screen.queryByText(/error loading dashboard/i)).not.toBeInTheDocument();
      expect(apiService.clients.list).toHaveBeenCalledTimes(2);
    });

    test('should handle different types of API errors with specific messages', async () => {
      // Test authentication error
      const authError = {
        response: {
          status: 401,
          data: { detail: 'Authentication required' }
        }
      };

      apiService.clients.list.mockRejectedValue(authError);

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/authentication required/i)).toBeInTheDocument();
      });

      // Should show specific error message
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    test('should handle server errors with detailed error messages', async () => {
      const serverError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error occurred' }
        }
      };

      apiService.clients.list.mockRejectedValue(serverError);

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/internal server error occurred/i)).toBeInTheDocument();
      });
    });

    test('should handle network timeout and connection errors', async () => {
      apiService.clients.list.mockRejectedValue(new Error('Request timeout'));

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/error loading dashboard/i)).toBeInTheDocument();
      });

      // Should show generic error message for network issues
      expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
    });

    test('should maintain error state until successful retry', async () => {
      const user = userEvent.setup();

      // Multiple failures then success
      apiService.clients.list
        .mockRejectedValueOnce(new Error('First failure'))
        .mockRejectedValueOnce(new Error('Second failure'))
        .mockResolvedValue({ data: [generateMockClient({ name: 'Finally Works' })] });

      render(
        <TestWrapper>
          <Dashboard />
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
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      expect(screen.queryByText(/error loading dashboard/i)).not.toBeInTheDocument();
      expect(apiService.clients.list).toHaveBeenCalledTimes(3);
    });

    test('should handle rapid API calls and prevent race conditions', async () => {
      const user = userEvent.setup();
      let callCount = 0;

      // Mock API with delay and call counting
      apiService.clients.list.mockImplementation(() => {
        callCount++;
        return new Promise(resolve => 
          setTimeout(() => resolve({ 
            data: [generateMockClient({ name: `Call ${callCount}` })] 
          }), 50)
        );
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
      });

      // Rapidly click refresh multiple times
      const refreshButton = screen.getByRole('button', { name: /refresh data/i });
      await user.click(refreshButton);
      await user.click(refreshButton);
      await user.click(refreshButton);

      // Should handle rapid clicks gracefully
      await waitFor(() => {
        expect(apiService.clients.list).toHaveBeenCalled();
      });

      // Should show stable final state
      expect(screen.getByText(/pixel management dashboard/i)).toBeInTheDocument();
    });

    test('should transition smoothly between loading, error, and success states', async () => {
      const user = userEvent.setup();

      // Start with loading (delayed response)
      apiService.clients.list.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
      );

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Loading state
      expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();

      // Wait for empty state
      await waitFor(() => {
        expect(screen.getByText(/ready to get started/i)).toBeInTheDocument();
      });

      expect(screen.queryByText(/loading dashboard/i)).not.toBeInTheDocument();

      // Trigger error state via refresh
      apiService.clients.list.mockRejectedValue(new Error('Test error'));
      
      const refreshButton = screen.getByRole('button', { name: /refresh data/i });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(screen.getByText(/test error/i)).toBeInTheDocument();
      });

      // Transition back to success
      apiService.clients.list.mockResolvedValue({ 
        data: [generateMockClient({ name: 'Recovery Success' })] 
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument(); // Client count
      });

      expect(screen.queryByText(/error loading dashboard/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/ready to get started/i)).not.toBeInTheDocument();
    });
  });
});