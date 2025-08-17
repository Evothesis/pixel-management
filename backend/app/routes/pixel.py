"""
Dynamic pixel serving endpoint.

Handles client-specific tracking JavaScript generation with domain authorization
and template caching for optimal performance.
"""

from fastapi import APIRouter, Request, Path

from ..pixel_serving import serve_pixel
from ..config.settings import settings

router = APIRouter()


@router.get("/pixel/{client_id}/tracking.js")
async def serve_pixel_js(
    request: Request,
    client_id: str = Path(..., regex=r'^[a-zA-Z0-9_-]+$', max_length=100)
):
    """
    Serve client-specific tracking JavaScript with domain authorization
    
    SECURITY: Validates requesting domain is authorized for specified client_id
    PERFORMANCE: Template caching with 5-minute browser cache
    """
    return await serve_pixel(request, client_id, settings.collection_api_url)