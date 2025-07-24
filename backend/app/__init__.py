"""
FastAPI application package for pixel management system.

This package contains the core backend components for a privacy-compliant pixel tracking
system. It provides REST API endpoints for client management, domain authorization,
and dynamic JavaScript pixel generation. The system supports multiple privacy levels
(standard, GDPR, HIPAA) and includes comprehensive authentication and audit logging.

Main modules:
- main: FastAPI application with REST API endpoints
- auth: API key authentication and authorization
- models: Firestore document models for clients, domains
- schemas: Pydantic request/response models
- firestore_client: Google Firestore database client
- pixel_serving: Dynamic JavaScript tracking pixel generation
- rate_limiter: Request rate limiting middleware
"""