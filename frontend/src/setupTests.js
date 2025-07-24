/**
 * Jest testing environment setup for React Testing Library.
 * 
 * This configuration file sets up the testing environment for all Jest tests
 * in the pixel management frontend application. It imports jest-dom custom
 * matchers that provide additional DOM assertion capabilities for more
 * expressive and readable test code.
 * 
 * The jest-dom library adds custom matchers like:
 * - toHaveTextContent(): Assert element contains specific text
 * - toBeInTheDocument(): Assert element exists in DOM
 * - toHaveClass(): Assert element has specific CSS classes
 * - toBeVisible(): Assert element is visible to users
 * 
 * This setup runs automatically before all test files and provides enhanced
 * DOM testing capabilities throughout the test suite.
 */

// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';