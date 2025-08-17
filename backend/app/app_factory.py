"""
Application factory for pixel management system.

Centralizes FastAPI app creation, middleware configuration, router registration,
and static file serving setup.
"""

import logging
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config.settings import settings
from .rate_limiter import RateLimitMiddleware
from .firestore_client import firestore_client
from .services.geolocation import geolocation_service

# Import route modules
from .routes import health, config, pixel, admin_clients, admin_domains

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns configured FastAPI app with all middleware, routes, and static file serving.
    """
    # Create FastAPI app
    app = FastAPI(title="SecurePixel Management", version="1.0.0")
    
    # Configure middleware
    configure_middleware(app)
    
    # Include routers
    include_routers(app)
    
    # Configure static file serving
    configure_static_files(app)
    
    # Add startup event
    configure_startup_events(app)
    
    return app


def configure_middleware(app: FastAPI) -> None:
    """Configure CORS and rate limiting middleware"""
    # Configure CORS with specific origins instead of wildcard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )
    
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)


def include_routers(app: FastAPI) -> None:
    """Include all route modules"""
    # Health check (no prefix)
    app.include_router(health.router, tags=["health"])
    
    # Public configuration endpoints
    app.include_router(config.router, tags=["configuration"])
    
    # Dynamic pixel serving
    app.include_router(pixel.router, tags=["pixel"])
    
    # Admin endpoints
    app.include_router(admin_clients.router, tags=["admin-clients"])
    app.include_router(admin_domains.router, tags=["admin-domains"])


def configure_static_files(app: FastAPI) -> None:
    """Configure static file serving for production React app"""
    if settings.static_files_enabled:
        # Mount static files
        app.mount("/static", StaticFiles(directory=f"{settings.static_dir}/static"), name="static")
        
        @app.get("/", include_in_schema=False)
        async def serve_react_app():
            """Serve React app for production"""
            return FileResponse(f"{settings.static_dir}/index.html")
        
        logger.info("Static file serving enabled for production React app")
    else:
        logger.info("Static file serving disabled - development mode")


def configure_startup_events(app: FastAPI) -> None:
    """Configure application startup events"""
    
    @app.on_event("startup")
    async def initialize_services():
        """Initialize Firestore and PostgreSQL geolocation services"""
        try:
            # Initialize Firestore
            if firestore_client.test_connection():
                logger.info("Firestore connection successful")
                
                # Create default admin client if it doesn't exist
                admin_client_id = "client_evothesis_admin"
                admin_doc = firestore_client.clients_ref.document(admin_client_id).get()
                
                if not admin_doc.exists:
                    admin_client_data = {
                        "client_id": admin_client_id,
                        "name": "SecurePixel Admin",
                        "email": "admin@securepixel.com",
                        "client_type": "admin",
                        "owner": admin_client_id,  # Self-owned
                        "billing_entity": admin_client_id,
                        "privacy_level": "standard",
                        "ip_collection_enabled": True,
                        "consent_required": False,
                        "features": {"admin_panel": True},
                        "deployment_type": "dedicated",
                        "vm_hostname": None,
                        "billing_rate_per_1k": 0.0,
                        "created_at": datetime.utcnow(),
                        "is_active": True
                    }
                    
                    firestore_client.clients_ref.document(admin_client_id).set(admin_client_data)
                    logger.info(f"Created default admin client: {admin_client_id}")
                else:
                    logger.info("Default admin client already exists")
            else:
                logger.error("Failed to connect to Firestore")
            
            # Initialize PostgreSQL geolocation service
            await geolocation_service.initialize()
            logger.info("Geolocation service initialized")
                
        except Exception as e:
            logger.error(f"Startup initialization failed: {e}")
    
    @app.on_event("shutdown")
    async def cleanup_services():
        """Cleanup services on shutdown"""
        try:
            await geolocation_service.close()
            logger.info("Services cleaned up successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")