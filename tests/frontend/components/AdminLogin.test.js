/**
 * AdminLogin Component Authentication Tests - Phase 2
 * 
 * Test suite for the AdminLogin component focusing on authentication flows,
 * security, and user experience. Provides comprehensive coverage of the
 * authentication interface including form validation, error handling,
 * and successful login scenarios.
 * 
 * Coverage Requirements:
 * - API key format validation
 * - Authentication error handling
 * - Successful login and redirect functionality
 * - Form state management
 * - Security best practices in frontend auth
 * 
 * Test Categories:
 * 1. API key format validation and input handling
 * 2. Authentication error scenarios and user feedback
 * 3. Successful login flow and callback execution
 * 4. Form security and state management
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { server } from '../../mocks/server';
import AdminLogin from '../../../src/components/AdminLogin';

// Mock the API service
jest.mock('../../../src/services/api', () => ({
  apiService: {
    testApiKey: jest.fn()
  }
}));

import { apiService } from '../../../src/services/api';

describe('AdminLogin Component - Authentication Tests', () => {
  const mockOnLoginSuccess = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockOnLoginSuccess.mockClear();
    
    // Reset sessionStorage mock
    global.sessionStorage.clear();
  });

  describe('API Key Format Validation', () => {
    test('should validate API key format - empty input', async () => {
      const user = userEvent.setup();
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      
      // Submit button should be disabled when input is empty
      expect(submitButton).toBeDisabled();
      
      // Try to submit empty form
      await user.click(submitButton);
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/please enter an api key/i)).toBeInTheDocument();
      });
      
      // API should not be called
      expect(apiService.testApiKey).not.toHaveBeenCalled();
      expect(mockOnLoginSuccess).not.toHaveBeenCalled();
    });

    test('should validate API key format - whitespace only', async () => {
      const user = userEvent.setup();
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      
      // Enter whitespace-only input
      await user.type(apiKeyInput, '   ');
      
      // Submit button should still be disabled
      expect(submitButton).toBeDisabled();
      
      // Try to submit
      fireEvent.submit(screen.getByRole('form', { hidden: true }));
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/please enter an api key/i)).toBeInTheDocument();
      });
      
      expect(apiService.testApiKey).not.toHaveBeenCalled();
    });

    test('should accept valid API key format', async () => {
      const user = userEvent.setup();
      
      // Mock successful API response
      apiService.testApiKey.mockResolvedValue({
        success: true
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      
      // Enter valid API key
      const validApiKey = 'evothesis_admin_test_key_12345';
      await user.type(apiKeyInput, validApiKey);
      
      // Submit button should be enabled
      expect(submitButton).not.toBeDisabled();
      
      // Submit form
      await user.click(submitButton);
      
      // Should call API with trimmed key
      await waitFor(() => {
        expect(apiService.testApiKey).toHaveBeenCalledWith(validApiKey);
      });
    });

    test('should trim whitespace from API key input', async () => {
      const user = userEvent.setup();
      
      // Mock successful API response
      apiService.testApiKey.mockResolvedValue({
        success: true
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      // Enter API key with leading/trailing whitespace
      const apiKeyWithWhitespace = '  evothesis_admin_test_key_12345  ';
      const trimmedApiKey = 'evothesis_admin_test_key_12345';
      
      await user.type(apiKeyInput, apiKeyWithWhitespace);
      await user.click(submitButton);
      
      // Should call API with trimmed key
      await waitFor(() => {
        expect(apiService.testApiKey).toHaveBeenCalledWith(trimmedApiKey);
      });
      
      // Should call onLoginSuccess with trimmed key
      await waitFor(() => {
        expect(mockOnLoginSuccess).toHaveBeenCalledWith(trimmedApiKey);
      });
    });

    test('should handle special characters in API key', async () => {
      const user = userEvent.setup();
      
      // Mock successful API response
      apiService.testApiKey.mockResolvedValue({
        success: true
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      // Enter API key with special characters (URL-safe base64)
      const apiKeyWithSpecialChars = 'evothesis_admin_test-key_12345';
      
      await user.type(apiKeyInput, apiKeyWithSpecialChars);
      await user.click(submitButton);
      
      // Should handle special characters correctly
      await waitFor(() => {
        expect(apiService.testApiKey).toHaveBeenCalledWith(apiKeyWithSpecialChars);
      });
    });
  });

  describe('Authentication Error Handling', () => {
    test('should handle invalid API key errors', async () => {
      const user = userEvent.setup();
      
      // Mock API rejection
      apiService.testApiKey.mockResolvedValue({
        success: false,
        error: 'Invalid API key. Please check your credentials.'
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      // Enter invalid API key
      await user.type(apiKeyInput, 'invalid_api_key_12345');
      await user.click(submitButton);
      
      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText(/verifying/i)).toBeInTheDocument();
      });
      
      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/invalid api key. please check your credentials/i)).toBeInTheDocument();
      });
      
      // Should not call onLoginSuccess
      expect(mockOnLoginSuccess).not.toHaveBeenCalled();
      
      // Should return to normal state
      expect(screen.getByRole('button', { name: /access admin panel/i })).toBeInTheDocument();
    });

    test('should handle network/connection errors', async () => {
      const user = userEvent.setup();
      
      // Mock network error
      apiService.testApiKey.mockRejectedValue(new Error('Network error'));
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_api_key_12345');
      await user.click(submitButton);
      
      // Should show connection error
      await waitFor(() => {
        expect(screen.getByText(/connection error. please try again/i)).toBeInTheDocument();
      });
      
      expect(mockOnLoginSuccess).not.toHaveBeenCalled();
    });

    test('should handle API errors without specific error message', async () => {
      const user = userEvent.setup();
      
      // Mock API rejection without specific error
      apiService.testApiKey.mockResolvedValue({
        success: false
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_api_key_12345');
      await user.click(submitButton);
      
      // Should show generic error message
      await waitFor(() => {
        expect(screen.getByText(/invalid api key. please check your credentials/i)).toBeInTheDocument();
      });
    });

    test('should clear error when user starts typing again', async () => {
      const user = userEvent.setup();
      
      // Mock API rejection first
      apiService.testApiKey.mockResolvedValue({
        success: false,
        error: 'Invalid API key'
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      // First attempt with invalid key
      await user.type(apiKeyInput, 'invalid_key');
      await user.click(submitButton);
      
      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/invalid api key/i)).toBeInTheDocument();
      });
      
      // Start typing again
      await user.clear(apiKeyInput);
      await user.type(apiKeyInput, 'new_key');
      
      // Error should be cleared when input gains focus
      fireEvent.focus(apiKeyInput);
      
      await waitFor(() => {
        expect(screen.queryByText(/invalid api key/i)).not.toBeInTheDocument();
      });
    });

    test('should handle 403 Forbidden responses', async () => {
      const user = userEvent.setup();
      
      // Mock 403 response
      server.use(
        rest.post('/api/test-key', (req, res, ctx) => {
          return res(
            ctx.status(403),
            ctx.json({ detail: 'Forbidden: Invalid API key' })
          );
        })
      );
      
      // Mock apiService to simulate the 403 response
      apiService.testApiKey.mockResolvedValue({
        success: false,
        error: 'Forbidden: Invalid API key'
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'forbidden_key');
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/forbidden: invalid api key/i)).toBeInTheDocument();
      });
    });
  });

  describe('Successful Login and Redirect', () => {
    test('should redirect on successful login', async () => {
      const user = userEvent.setup();
      
      // Mock successful authentication
      apiService.testApiKey.mockResolvedValue({
        success: true
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      const validApiKey = 'evothesis_admin_valid_key_12345';
      
      await user.type(apiKeyInput, validApiKey);
      await user.click(submitButton);
      
      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText(/verifying/i)).toBeInTheDocument();
      });
      
      // Should call onLoginSuccess with the API key
      await waitFor(() => {
        expect(mockOnLoginSuccess).toHaveBeenCalledWith(validApiKey);
      });
      
      // Should clear the form
      await waitFor(() => {
        expect(apiKeyInput.value).toBe('');
      });
    });

    test('should handle successful login with different API key formats', async () => {
      const user = userEvent.setup();
      
      const apiKeyFormats = [
        'evothesis_admin_short_123',
        'evothesis_admin_long_key_with_many_characters_12345',
        'evothesis_admin_with-dashes_and_underscores_123',
        'evothesis_admin_MIXED_case_Key_123'
      ];
      
      for (const apiKey of apiKeyFormats) {
        // Reset mocks for each iteration
        mockOnLoginSuccess.mockClear();
        
        // Mock successful response
        apiService.testApiKey.mockResolvedValue({
          success: true
        });
        
        render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
        
        const apiKeyInput = screen.getByLabelText(/admin api key/i);
        const submitButton = screen.getByRole('button', { name: /access admin panel/i });
        
        await user.type(apiKeyInput, apiKey);
        await user.click(submitButton);
        
        await waitFor(() => {
          expect(mockOnLoginSuccess).toHaveBeenCalledWith(apiKey);
        });
        
        // Cleanup for next iteration
        screen.unmount();
      }
    });

    test('should maintain login state during API call', async () => {
      const user = userEvent.setup();
      
      // Mock delayed API response
      apiService.testApiKey.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({ success: true });
          }, 100);
        });
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_key');
      await user.click(submitButton);
      
      // Should show loading state
      expect(screen.getByText(/verifying/i)).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
      expect(apiKeyInput).toBeDisabled();
      
      // Wait for completion
      await waitFor(() => {
        expect(mockOnLoginSuccess).toHaveBeenCalled();
      }, { timeout: 200 });
    });

    test('should log successful authentication (development mode)', async () => {
      const user = userEvent.setup();
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      // Mock successful authentication
      apiService.testApiKey.mockResolvedValue({
        success: true
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_key');
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnLoginSuccess).toHaveBeenCalled();
      });
      
      // Should log authentication attempt and success
      expect(consoleSpy).toHaveBeenCalledWith('🔐 Attempting login...');
      expect(consoleSpy).toHaveBeenCalledWith('✅ Login successful');
      
      consoleSpy.mockRestore();
    });
  });

  describe('Form Security and State Management', () => {
    test('should use password input type for API key', () => {
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      
      // Should be password type to hide input
      expect(apiKeyInput).toHaveAttribute('type', 'password');
    });

    test('should have proper autocomplete attributes', () => {
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      
      // Should have appropriate autocomplete attribute
      expect(apiKeyInput).toHaveAttribute('autocomplete', 'current-password');
    });

    test('should disable form during submission', async () => {
      const user = userEvent.setup();
      
      // Mock slow API response
      apiService.testApiKey.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => resolve({ success: true }), 100);
        });
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_key');
      await user.click(submitButton);
      
      // Form should be disabled during submission
      expect(apiKeyInput).toBeDisabled();
      expect(submitButton).toBeDisabled();
      expect(submitButton).toHaveTextContent(/verifying/i);
      
      // Wait for completion
      await waitFor(() => {
        expect(mockOnLoginSuccess).toHaveBeenCalled();
      });
    });

    test('should handle form submission via Enter key', async () => {
      const user = userEvent.setup();
      
      apiService.testApiKey.mockResolvedValue({
        success: true
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      
      await user.type(apiKeyInput, 'test_key');
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(apiService.testApiKey).toHaveBeenCalledWith('test_key');
      });
    });

    test('should not submit empty form via Enter key', async () => {
      const user = userEvent.setup();
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      
      // Try to submit empty form with Enter
      await user.click(apiKeyInput);
      await user.keyboard('{Enter}');
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/please enter an api key/i)).toBeInTheDocument();
      });
      
      expect(apiService.testApiKey).not.toHaveBeenCalled();
    });

    test('should preserve API key value during error states', async () => {
      const user = userEvent.setup();
      
      // Mock API rejection
      apiService.testApiKey.mockResolvedValue({
        success: false,
        error: 'Invalid API key'
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      const testKey = 'test_api_key_12345';
      
      await user.type(apiKeyInput, testKey);
      await user.click(submitButton);
      
      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/invalid api key/i)).toBeInTheDocument();
      });
      
      // API key should still be in the input for user to modify
      expect(apiKeyInput.value).toBe(testKey);
    });

    test('should reset form state after successful login', async () => {
      const user = userEvent.setup();
      
      apiService.testApiKey.mockResolvedValue({
        success: true
      });
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      await user.type(apiKeyInput, 'test_key');
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnLoginSuccess).toHaveBeenCalled();
      });
      
      // Form should be reset
      expect(apiKeyInput.value).toBe('');
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    });
  });

  describe('Accessibility and User Experience', () => {
    test('should have proper ARIA labels and structure', () => {
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      // Should have proper heading structure
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/securepixel admin/i);
      
      // Should have labeled form controls
      expect(screen.getByLabelText(/admin api key/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /access admin panel/i })).toBeInTheDocument();
    });

    test('should show visual feedback for form validation', async () => {
      const user = userEvent.setup();
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      const apiKeyInput = screen.getByLabelText(/admin api key/i);
      const submitButton = screen.getByRole('button', { name: /access admin panel/i });
      
      // Empty input - button should be disabled
      expect(submitButton).toBeDisabled();
      
      // Type valid input - button should be enabled
      await user.type(apiKeyInput, 'test_key');
      expect(submitButton).not.toBeDisabled();
      
      // Clear input - button should be disabled again
      await user.clear(apiKeyInput);
      expect(submitButton).toBeDisabled();
    });

    test('should display helpful information about API key location', () => {
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      // Should show help text about API key location
      expect(screen.getByText(/need your api key/i)).toBeInTheDocument();
      expect(screen.getByText(/securepixel-credentials/i)).toBeInTheDocument();
    });

    test('should show development mode indicator when appropriate', () => {
      // Mock development environment
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';
      
      render(<AdminLogin onLoginSuccess={mockOnLoginSuccess} />);
      
      // Should show development mode indicator
      expect(screen.getByText(/development mode/i)).toBeInTheDocument();
      expect(screen.getByText(/console logs are enabled/i)).toBeInTheDocument();
      
      // Restore environment
      process.env.NODE_ENV = originalEnv;
    });
  });
});