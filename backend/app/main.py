"""
FastAPI main application for pixel management system.

This is the streamlined entry point that uses the app factory pattern
for clean separation of concerns and modular architecture.

The application provides:
- Client CRUD operations with privacy compliance (GDPR, HIPAA, standard)
- Domain authorization and management with global indexing
- Dynamic JavaScript pixel generation with domain validation
- Health monitoring and configuration endpoints
- Static file serving for production React frontend
- Comprehensive CORS and rate limiting middleware

All route logic has been extracted to dedicated modules in the routes/ package.
Configuration management is centralized in config/settings.py.
"""

import logging
from .app_factory import create_app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI application using the factory pattern
app = create_app()

logger.info("SecurePixel Management API initialized successfully")