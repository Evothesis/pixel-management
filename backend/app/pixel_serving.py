from fastapi import Request, HTTPException, Response
from pathlib import Path
import json
import logging
from typing import Dict, Any, Optional
import threading
import time

from .firestore_client import firestore_client

logger = logging.getLogger(__name__)

class PixelTemplateCache:
    """Thread-safe template caching system"""
    
    def __init__(self):
        self._template_cache: Optional[str] = None
        self._cache_timestamp: float = 0
        self._lock = threading.Lock()
        
    def get_template(self) -> str:
        """Get cached template or load from file"""
        with self._lock:
            # Cache for 1 hour or until restart
            if (self._template_cache is None or 
                time.time() - self._cache_timestamp > 3600):
                self._template_cache = self._load_template_from_file()
                self._cache_timestamp = time.time()
                logger.info("Loaded and cached pixel template")
            
            return self._template_cache
    
    def _load_template_from_file(self) -> str:
        """Load template from filesystem"""
        template_path = Path(__file__).parent / "pixel_templates" / "tracking.js"
        
        if not template_path.exists():
            logger.error(f"Pixel template not found at {template_path}")
            raise FileNotFoundError(f"Pixel template missing: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                
            if '{CONFIG_PLACEHOLDER}' not in template_content:
                raise ValueError("Template missing CONFIG_PLACEHOLDER marker")
                
            return template_content
            
        except Exception as e:
            logger.error(f"Failed to load pixel template: {e}")
            raise

# Global template cache instance
template_cache = PixelTemplateCache()

def generate_pixel_javascript(client_config: Dict[str, Any], collection_endpoint: str) -> str:
    """Generate client-specific tracking pixel JavaScript"""
    try:
        # Get base template
        template_code = template_cache.get_template()
        
        # Enhance config with collection endpoint
        enhanced_config = client_config.copy()
        enhanced_config['collection_endpoint'] = collection_endpoint
        enhanced_config['pixel_version'] = '1.0.0'
        enhanced_config['generated_at'] = time.time()
        
        # Inject configuration
        config_json = json.dumps(enhanced_config, indent=2, ensure_ascii=False)
        pixel_code = template_code.replace('{CONFIG_PLACEHOLDER}', config_json)
        
        logger.info(f"Generated pixel for client {client_config.get('client_id')} with endpoint {collection_endpoint}")
        return pixel_code
        
    except Exception as e:
        logger.error(f"Failed to generate pixel JavaScript: {e}")
        raise HTTPException(status_code=500, detail="Pixel generation failed")

async def validate_domain_authorization(requesting_domain: str, client_id: str) -> Dict[str, Any]:
    """
    Validate that requesting domain is authorized for specified client_id
    Returns client configuration if authorized, raises HTTPException if not
    """
    try:
        # Check domain authorization using existing domain index
        domain_docs = list(
            firestore_client.domain_index_ref
            .where('domain', '==', requesting_domain)
            .limit(1)
            .stream()
        )
        
        if not domain_docs:
            logger.warning(f"Domain {requesting_domain} not authorized for any client")
            raise HTTPException(
                status_code=403, 
                detail=f"Domain {requesting_domain} not authorized for tracking"
            )
        
        domain_data = domain_docs[0].to_dict()
        authorized_client_id = domain_data['client_id']
        
        # Verify domain is authorized for this specific client_id
        if authorized_client_id != client_id:
            logger.warning(f"Domain {requesting_domain} authorized for {authorized_client_id}, not {client_id}")
            raise HTTPException(
                status_code=403,
                detail=f"Domain {requesting_domain} not authorized for client {client_id}"
            )
        
        logger.info(f"Domain {requesting_domain} validated for client {client_id}")
        
        # Get client configuration using existing logic
        client_doc = firestore_client.clients_ref.document(client_id).get()
        
        if not client_doc.exists:
            logger.warning(f"Client not found: {client_id}")
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = client_doc.to_dict()
        
        if not client_data.get('is_active', True):
            logger.warning(f"Inactive client access attempt: {client_id}")
            raise HTTPException(status_code=404, detail="Client inactive")
        
        # Build configuration for pixel
        config = {
            'client_id': client_data['client_id'],
            'privacy_level': client_data['privacy_level'],
            'ip_collection': {
                'enabled': client_data['ip_collection_enabled'],
                'hash_required': client_data['privacy_level'] in ['gdpr', 'hipaa'],
                'salt': client_data.get('ip_salt') if client_data['privacy_level'] in ['gdpr', 'hipaa'] else None
            },
            'consent': {
                'required': client_data['consent_required'],
                'default_behavior': 'block' if client_data['privacy_level'] in ['gdpr', 'hipaa'] else 'allow'
            },
            'features': client_data.get('features', {}),
            'deployment': {
                'type': client_data['deployment_type'],
                'hostname': client_data.get('vm_hostname')
            }
        }
        
        logger.info(f"Retrieved config for client {client_id} (privacy: {client_data['privacy_level']})")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain authorization failed for {requesting_domain}/{client_id}: {e}")
        raise HTTPException(status_code=500, detail="Authorization service error")

async def serve_pixel(request: Request, client_id: str, collection_endpoint: str) -> Response:
    """
    Main pixel serving function
    Validates domain authorization and returns client-specific JavaScript
    """
    try:
        # Validate client_id format
        if not client_id or len(client_id) < 3 or not client_id.replace('_', '').replace('-', '').isalnum():
            raise HTTPException(status_code=400, detail="Invalid client_id format")
        
        # Extract requesting domain
        origin = request.headers.get("origin", "")
        if origin:
            requesting_domain = origin.replace("http://", "").replace("https://", "").split(":")[0]
        else:
            # Fallback to referer
            referer = request.headers.get("referer", "")
            if referer:
                requesting_domain = referer.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        
        if not requesting_domain:
            logger.warning("Unable to determine requesting domain - missing origin and referer headers")
            raise HTTPException(status_code=400, detail="Unable to determine requesting domain")
        
        # Validate domain authorization and get client config
        client_config = await validate_domain_authorization(requesting_domain, client_id)
        
        # Generate pixel JavaScript
        pixel_js = generate_pixel_javascript(client_config, collection_endpoint)
        
        # Return with appropriate caching headers
        return Response(
            content=pixel_js,
            media_type="application/javascript",
            headers={
                "Cache-Control": "public, max-age=300",  # 5 minute browser cache
                "Content-Type": "application/javascript; charset=utf-8",
                "X-Client-ID": client_id,
                "X-Authorized-Domain": requesting_domain,
                "X-Privacy-Level": client_config.get('privacy_level', 'standard'),
                "X-Generated-At": str(int(time.time()))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pixel serving error for {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Pixel service error")