"""
Public configuration endpoints for tracking infrastructure.

These endpoints provide client configuration data to tracking VMs and
return domain authorization information for pixel serving.
"""

from fastapi import APIRouter, HTTPException
import logging

from ..firestore_client import firestore_client
from ..schemas import ClientConfigResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


@router.get("/config/domain/{domain}", response_model=ClientConfigResponse)
async def get_config_by_domain(domain: str):
    """
    CRITICAL: Domain authorization endpoint for tracking infrastructure
    This endpoint validates domain authorization and returns client configuration
    """
    try:
        # Validate domain format
        if not domain or len(domain) < 3:
            raise HTTPException(status_code=400, detail="Invalid domain format")
        
        # Lookup domain in domain_index
        domain_docs = list(
            firestore_client.domain_index_ref
            .where('domain', '==', domain.lower())
            .limit(1)
            .stream()
        )
        
        if not domain_docs:
            logger.warning(f"Domain {domain} not authorized")
            raise HTTPException(status_code=404, detail="Domain not authorized")
        
        domain_data = domain_docs[0].to_dict()
        client_id = domain_data['client_id']
        
        # Get client configuration
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            logger.error(f"Client {client_id} not found for authorized domain {domain}")
            raise HTTPException(status_code=500, detail="Client configuration error")
        
        client_data = client_doc.to_dict()
        
        # Build configuration response
        config = ClientConfigResponse(
            client_id=client_id,
            privacy_level=client_data['privacy_level'],
            ip_collection={
                "enabled": client_data.get('ip_collection_enabled', True),
                "hash_required": client_data['privacy_level'] in ['gdpr', 'hipaa'],
                "salt": client_data.get('ip_salt')
            },
            consent={
                "required": client_data.get('consent_required', False),
                "default_behavior": "opt_out" if client_data['privacy_level'] == 'gdpr' else "allow"
            },
            features=client_data.get('features', {}),
            deployment={
                "type": client_data.get('deployment_type', 'shared'),
                "hostname": client_data.get('vm_hostname')
            }
        )
        
        logger.info(f"Served config for domain {domain} -> client {client_id}")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain config lookup failed for {domain}: {e}")
        raise HTTPException(status_code=500, detail="Configuration service error")


@router.get("/config/client/{client_id}", response_model=ClientConfigResponse)
async def get_config_by_client_id(client_id: str):
    """Get client configuration by client_id (for tracking VMs)"""
    try:
        # Validate client_id format
        if not client_id or len(client_id) < 3:
            raise HTTPException(status_code=400, detail="Invalid client_id format")
        
        # Get client configuration
        client_doc = firestore_client.clients_ref.document(client_id).get()
        if not client_doc.exists:
            logger.warning(f"Client {client_id} not found")
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = client_doc.to_dict()
        
        # Build configuration response
        config = ClientConfigResponse(
            client_id=client_id,
            privacy_level=client_data['privacy_level'],
            ip_collection={
                "enabled": client_data.get('ip_collection_enabled', True),
                "hash_required": client_data['privacy_level'] in ['gdpr', 'hipaa'],
                "salt": client_data.get('ip_salt')
            },
            consent={
                "required": client_data.get('consent_required', False),
                "default_behavior": "opt_out" if client_data['privacy_level'] == 'gdpr' else "allow"
            },
            features=client_data.get('features', {}),
            deployment={
                "type": client_data.get('deployment_type', 'shared'),
                "hostname": client_data.get('vm_hostname')
            }
        )
        
        logger.info(f"Served config for client {client_id} (privacy: {client_data['privacy_level']})")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Client config lookup failed for {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Configuration service error")


@router.get("/domains/all")
async def list_all_domains():
    """Get all authorized domains across all clients for CORS configuration"""
    try:
        # Get all domains from domain_index
        domain_docs = list(firestore_client.domain_index_ref.stream())
        
        domains = []
        for doc in domain_docs:
            domain_data = doc.to_dict()
            domains.append(domain_data['domain'])
        
        logger.info(f"Served {len(domains)} domains for CORS configuration")
        return {"domains": domains, "count": len(domains)}
        
    except Exception as e:
        logger.error(f"Failed to get all domains: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve domains")