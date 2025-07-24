/**
 * React application entry point for pixel management admin interface.
 * 
 * This is the main bootstrap file that initializes the React application and
 * mounts it to the DOM. It serves as the entry point for the entire admin
 * interface, setting up the root component and CSS imports.
 * 
 * The application provides a web-based interface for managing tracking clients,
 * domain authorization, and system configuration with secure API key authentication.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
