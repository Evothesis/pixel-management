"""
Local geolocation database module using DB-IP City Lite.

This module provides IP geolocation services using a local DB-IP database
instead of external API calls. Features include:
- Local CSV database parsing and indexing
- Interval tree for O(log n) IP range lookups  
- In-memory caching for performance
- Automatic database updates

IP Geolocation by DB-IP (https://db-ip.com) under Creative Commons Attribution 4.0.
"""

from .db_loader import GeolocationDatabase

__all__ = ['GeolocationDatabase']