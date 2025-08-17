"""
Secure IP address extraction from HTTP requests.

This utility handles IP address extraction from various sources including
proxy headers, with security validation and fallback mechanisms. Designed
for pixel serving environments where accurate client IP detection is crucial
for geolocation and analytics.

Features:
- Secure proxy header parsing (X-Forwarded-For, X-Real-IP)
- Private IP validation and filtering
- Fallback chain with request.client.host
- IPv4/IPv6 support with validation
- Security logging for suspicious patterns

Handles common proxy configurations from CDNs, load balancers, and reverse proxies.
"""

import ipaddress
import logging
import re
from typing import Optional, List
from fastapi import Request

logger = logging.getLogger(__name__)


class IPExtractionError(Exception):
    """Custom exception for IP extraction errors"""
    pass


def _is_valid_ip(ip_str: str) -> bool:
    """
    Validate IP address format (IPv4 or IPv6).
    
    Args:
        ip_str: String to validate as IP address
        
    Returns:
        True if valid IP address format, False otherwise
    """
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False


def _is_private_ip(ip_str: str) -> bool:
    """
    Check if IP address is private/internal.
    
    Private IPs include:
    - RFC 1918 private ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Localhost (127.0.0.1, ::1)
    - Link-local addresses
    - Reserved ranges
    
    Args:
        ip_str: IP address string to check
        
    Returns:
        True if IP is private/internal, False if public
    """
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except ValueError:
        # Invalid IP format is considered "private" (unusable)
        return True


def _parse_forwarded_header(header_value: str) -> List[str]:
    """
    Parse X-Forwarded-For header value into list of IP addresses.
    
    X-Forwarded-For format: "client, proxy1, proxy2"
    The leftmost IP is typically the original client IP.
    
    Args:
        header_value: Raw X-Forwarded-For header value
        
    Returns:
        List of IP addresses, with client IP first
    """
    if not header_value:
        return []
    
    # Split by comma and clean up whitespace
    ips = [ip.strip() for ip in header_value.split(',')]
    
    # Filter out empty strings and validate IP format
    valid_ips = []
    for ip in ips:
        if ip and _is_valid_ip(ip):
            valid_ips.append(ip)
        elif ip:  # Log invalid but non-empty values
            logger.debug(f"Invalid IP in X-Forwarded-For: {ip}")
    
    return valid_ips


def _extract_from_x_forwarded_for(request: Request) -> Optional[str]:
    """
    Extract client IP from X-Forwarded-For header.
    
    This header is commonly set by load balancers, CDNs, and reverse proxies.
    Format: "client_ip, proxy1_ip, proxy2_ip"
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address if found and valid, None otherwise
    """
    xff_header = request.headers.get("x-forwarded-for")
    if not xff_header:
        return None
    
    ips = _parse_forwarded_header(xff_header)
    if not ips:
        return None
    
    # Return the first (leftmost) IP, which should be the client
    client_ip = ips[0]
    
    # Security check: ensure it's not a private IP being spoofed
    if _is_private_ip(client_ip):
        logger.debug(f"X-Forwarded-For contains private IP: {client_ip}")
        return None
    
    logger.debug(f"Client IP from X-Forwarded-For: {client_ip}")
    return client_ip


def _extract_from_x_real_ip(request: Request) -> Optional[str]:
    """
    Extract client IP from X-Real-IP header.
    
    This header is commonly set by nginx and other reverse proxies.
    Contains single IP address of the real client.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address if found and valid, None otherwise
    """
    real_ip = request.headers.get("x-real-ip")
    if not real_ip:
        return None
    
    real_ip = real_ip.strip()
    
    # Validate IP format
    if not _is_valid_ip(real_ip):
        logger.debug(f"Invalid X-Real-IP format: {real_ip}")
        return None
    
    # Security check: ensure it's not a private IP
    if _is_private_ip(real_ip):
        logger.debug(f"X-Real-IP contains private IP: {real_ip}")
        return None
    
    logger.debug(f"Client IP from X-Real-IP: {real_ip}")
    return real_ip


def _extract_from_cf_connecting_ip(request: Request) -> Optional[str]:
    """
    Extract client IP from CF-Connecting-IP header.
    
    This header is set by Cloudflare with the original client IP.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address if found and valid, None otherwise
    """
    cf_ip = request.headers.get("cf-connecting-ip")
    if not cf_ip:
        return None
    
    cf_ip = cf_ip.strip()
    
    # Validate IP format
    if not _is_valid_ip(cf_ip):
        logger.debug(f"Invalid CF-Connecting-IP format: {cf_ip}")
        return None
    
    # Security check: ensure it's not a private IP
    if _is_private_ip(cf_ip):
        logger.debug(f"CF-Connecting-IP contains private IP: {cf_ip}")
        return None
    
    logger.debug(f"Client IP from CF-Connecting-IP: {cf_ip}")
    return cf_ip


def _extract_from_direct_connection(request: Request) -> Optional[str]:
    """
    Extract IP from direct connection (request.client.host).
    
    This is the fallback when no proxy headers are available or valid.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address if available and valid, None otherwise
    """
    if not hasattr(request, 'client') or not request.client:
        logger.debug("No client connection info available")
        return None
    
    direct_ip = request.client.host
    if not direct_ip:
        logger.debug("No host in client connection info")
        return None
    
    # Validate IP format
    if not _is_valid_ip(direct_ip):
        logger.debug(f"Invalid direct connection IP format: {direct_ip}")
        return None
    
    # Note: We don't filter private IPs here because in some deployments
    # the direct connection might legitimately be from a private network
    # (e.g., internal load balancer)
    logger.debug(f"Client IP from direct connection: {direct_ip}")
    return direct_ip


def extract_client_ip(request: Request, trust_proxy_headers: bool = True) -> Optional[str]:
    """
    Extract client IP address from HTTP request with security validation.
    
    Implements a secure fallback chain:
    1. CF-Connecting-IP (Cloudflare)
    2. X-Real-IP (nginx, other reverse proxies)
    3. X-Forwarded-For (load balancers, CDNs)
    4. Direct connection (request.client.host)
    
    Args:
        request: FastAPI request object
        trust_proxy_headers: Whether to trust proxy headers (default: True)
        
    Returns:
        Client IP address if found, None if no valid IP could be extracted
        
    Note:
        - Private IPs from proxy headers are filtered for security
        - Direct connection IPs are not filtered (may be legitimately private)
        - Invalid IP formats are logged and skipped
    """
    client_ip = None
    
    if trust_proxy_headers:
        # Try Cloudflare header first (most reliable if behind CF)
        client_ip = _extract_from_cf_connecting_ip(request)
        
        # Try X-Real-IP (nginx standard)
        if not client_ip:
            client_ip = _extract_from_x_real_ip(request)
        
        # Try X-Forwarded-For (common load balancer header)
        if not client_ip:
            client_ip = _extract_from_x_forwarded_for(request)
    
    # Fallback to direct connection
    if not client_ip:
        client_ip = _extract_from_direct_connection(request)
    
    if client_ip:
        logger.info(f"Extracted client IP: {client_ip}")
        return client_ip
    else:
        logger.warning("Could not extract valid client IP from request")
        return None


def get_client_ip_info(request: Request) -> dict:
    """
    Get comprehensive client IP information for debugging and monitoring.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with IP extraction details and all available headers
    """
    info = {
        "extracted_ip": extract_client_ip(request),
        "headers": {
            "x_forwarded_for": request.headers.get("x-forwarded-for"),
            "x_real_ip": request.headers.get("x-real-ip"), 
            "cf_connecting_ip": request.headers.get("cf-connecting-ip"),
        },
        "direct_connection": getattr(request.client, 'host', None) if hasattr(request, 'client') else None,
        "is_private": False
    }
    
    # Check if extracted IP is private
    if info["extracted_ip"]:
        info["is_private"] = _is_private_ip(info["extracted_ip"])
    
    return info