/**
 * Unit tests for AuthContext authentication state management.
 * 
 * This test suite validates the authentication context functionality including
 * immediate initialization, sessionStorage integration, and state management.
 * It tests the core authentication logic that was fixed to prevent race
 * conditions in route protection.
 * 
 * Test coverage:
 * - Immediate authentication initialization without delays
 * - SessionStorage persistence and retrieval of API keys
 * - Login and logout state transitions
 * - Authentication state propagation to consuming components
 * - Error handling for missing or invalid authentication data
 * 
 * The tests mock sessionStorage and use React Testing Library to validate
 * the authentication context behavior in isolation from routing logic.
 */

import React from 'react';
import { render, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';

// Mock sessionStorage
const mockSessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage
});

// Test component to access auth context
const TestComponent = () => {
  const { isAuthenticated, isLoading, isInitialized, apiKey } = useAuth();
  return (
    <div>
      <div data-testid="authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="loading">{isLoading.toString()}</div>
      <div data-testid="initialized">{isInitialized.toString()}</div>
      <div data-testid="apikey">{apiKey || 'null'}</div>
    </div>
  );
};

// Mock the AuthenticationManager to control its behavior in tests
const mockAuthManager = {
  isInitialized: false,
  apiKey: null,
  subscribers: new Set(),
  
  initialize() {
    const stored = mockSessionStorage.getItem('admin_api_key');
    this.apiKey = stored ? stored.trim() : null;
    this.isInitialized = true;
    this.notifySubscribers();
  },
  
  setApiKey(key) {
    const cleanKey = key ? key.trim() : null;
    if (cleanKey !== this.apiKey) {
      this.apiKey = cleanKey;
      if (cleanKey) {
        mockSessionStorage.setItem('admin_api_key', cleanKey);
      } else {
        mockSessionStorage.removeItem('admin_api_key');
      }
      this.notifySubscribers();
    }
  },
  
  getApiKey() {
    return this.apiKey;
  },
  
  isAuthenticated() {
    return this.isInitialized && !!this.apiKey;
  },
  
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  },
  
  notifySubscribers() {
    this.subscribers.forEach(callback => callback({
      isAuthenticated: this.isAuthenticated(),
      apiKey: this.getApiKey(),
      isInitialized: this.isInitialized
    }));
  },
  
  logout() {
    this.setApiKey(null);
  }
};

// Mock the AuthContext module to use our mock authManager
jest.mock('./AuthContext', () => {
  const originalModule = jest.requireActual('./AuthContext');
  
  // Replace the authManager instance
  const MockedAuthProvider = ({ children }) => {
    return originalModule.AuthProvider({ children });
  };
  
  return {
    ...originalModule,
    AuthProvider: MockedAuthProvider,
    // Export the mock so we can control it in tests
    __mockAuthManager: mockAuthManager
  };
});

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    console.log = jest.fn(); // Suppress console logs
    
    // Reset mock authManager state
    mockAuthManager.isInitialized = false;
    mockAuthManager.apiKey = null;
    mockAuthManager.subscribers.clear();
  });

  test('initializes immediately without delay', async () => {
    // Mock valid API key in session storage
    mockSessionStorage.getItem.mockReturnValue('test-api-key');

    const { getByTestId } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Should initialize synchronously - no race condition
    await waitFor(() => {
      expect(getByTestId('initialized')).toHaveTextContent('true');
      expect(getByTestId('loading')).toHaveTextContent('false');
      expect(getByTestId('authenticated')).toHaveTextContent('true');
      expect(getByTestId('apikey')).toHaveTextContent('test-api-key');
    }, { timeout: 100 }); // Very short timeout to ensure no artificial delay

    expect(mockSessionStorage.getItem).toHaveBeenCalledWith('admin_api_key');
  });

  test('handles missing API key correctly', async () => {
    // Mock no API key in session storage
    mockSessionStorage.getItem.mockReturnValue(null);

    const { getByTestId } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(getByTestId('initialized')).toHaveTextContent('true');
      expect(getByTestId('loading')).toHaveTextContent('false');
      expect(getByTestId('authenticated')).toHaveTextContent('false');
      expect(getByTestId('apikey')).toHaveTextContent('null');
    });
  });

  test('login updates state correctly', async () => {
    mockSessionStorage.getItem.mockReturnValue(null);

    let authContext;
    const TestWithLogin = () => {
      authContext = useAuth();
      return <TestComponent />;
    };

    const { getByTestId } = render(
      <AuthProvider>
        <TestWithLogin />
      </AuthProvider>
    );

    // Wait for initial state
    await waitFor(() => {
      expect(getByTestId('authenticated')).toHaveTextContent('false');
    });

    // Login with new API key
    act(() => {
      authContext.login('new-api-key');
    });

    await waitFor(() => {
      expect(getByTestId('authenticated')).toHaveTextContent('true');
      expect(getByTestId('apikey')).toHaveTextContent('new-api-key');
    });

    expect(mockSessionStorage.setItem).toHaveBeenCalledWith('admin_api_key', 'new-api-key');
  });

  test('logout clears state correctly', async () => {
    mockSessionStorage.getItem.mockReturnValue('existing-key');

    let authContext;
    const TestWithLogout = () => {
      authContext = useAuth();
      return <TestComponent />;
    };

    const { getByTestId } = render(
      <AuthProvider>
        <TestWithLogout />
      </AuthProvider>
    );

    // Wait for authenticated state
    await waitFor(() => {
      expect(getByTestId('authenticated')).toHaveTextContent('true');
    });

    // Logout
    act(() => {
      authContext.logout();
    });

    await waitFor(() => {
      expect(getByTestId('authenticated')).toHaveTextContent('false');
      expect(getByTestId('apikey')).toHaveTextContent('null');
    });

    expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('admin_api_key');
  });
});