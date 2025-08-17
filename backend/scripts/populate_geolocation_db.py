#!/usr/bin/env python3
"""
PostgreSQL IP Geolocation Database Population Script

High-performance geolocation database population using PostgreSQL COPY FROM.

Features:
- Uses PostgreSQL COPY FROM for bulk CSV import (fastest available method)
- Skip-if-exists logic prevents duplicate population
- Two-stage process: schema creation, then index creation after data load
- EU detection via SQL UPDATE after import for optimal performance
- Direct file-to-database loading without in-memory parsing

Performance characteristics:
- Total setup time: Under 4 minutes
- Data loading: ~30 seconds via PostgreSQL COPY
- Index creation: ~3 minutes after data load
- Handles 7.9M+ records efficiently
"""

import asyncio
import asyncpg
import argparse
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

EU_COUNTRIES = {
    'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
    'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
    'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'
}


async def populate_database(database_url: str, csv_path: Path):
    """
    Populate database using optimized PostgreSQL COPY FROM for maximum performance.
    
    Process:
    1. Check if data already exists (skip if populated)
    2. Use PostgreSQL COPY FROM for bulk CSV import
    3. Apply EU detection via SQL UPDATE
    4. Create indexes after data population for optimal performance
    
    Args:
        database_url: PostgreSQL connection string
        csv_path: Path to dbip-city-lite.csv file
        
    Performance: ~30 seconds for data load, ~3 minutes for index creation
    """
    
    conn = await asyncpg.connect(database_url)
    try:
        # Check if data already exists
        count = await conn.fetchval("SELECT COUNT(*) FROM ip_geolocation")
        if count > 0:
            logger.info(f"Database already contains {count:,} records - skipping population")
            return
        
        logger.info(f"Loading CSV file: {csv_path}")
        start_time = time.time()
        
        # Use PostgreSQL COPY FROM for maximum performance  
        async with conn.transaction():
            with open(csv_path, 'rb') as f:
                await conn.copy_from_file(
                    f, 
                    table_name='ip_geolocation',
                    columns=['start_ip', 'end_ip', 'continent_code', 'country_code', 
                            'region_name', 'city_name', 'latitude', 'longitude'],
                    format='csv'
                )
            
            # Add EU detection
            await conn.execute("""
                UPDATE ip_geolocation 
                SET is_eu = (country_code = ANY($1))
                WHERE country_code IS NOT NULL
            """, list(EU_COUNTRIES))
            
            # Update metadata
            count = await conn.fetchval("SELECT COUNT(*) FROM ip_geolocation")
            await conn.execute("""
                UPDATE geolocation_metadata 
                SET record_count = $1, last_updated = NOW(), database_version = '1.1.0'
            """, count)
            
        elapsed = time.time() - start_time
        logger.info(f"Loaded {count:,} records in {elapsed:.1f}s ({count/elapsed:,.0f} records/sec)")
        
        # Create indexes
        logger.info("Creating indexes...")
        index_start = time.time()
        await conn.execute(open('/app/scripts/create_geolocation_indexes.sql').read())
        index_elapsed = time.time() - index_start
        logger.info(f"Indexes created in {index_elapsed:.1f}s")
        
    finally:
        await conn.close()


async def main():
    parser = argparse.ArgumentParser(description="Populate PostgreSQL geolocation database")
    parser.add_argument('--database-url', 
                       default='postgresql://pixeluser:pixelpass@localhost:5432/pixeldb')
    parser.add_argument('--csv-path', type=Path, required=True)
    
    args = parser.parse_args()
    
    logger.info("Starting geolocation database population")
    
    if not args.csv_path.exists():
        logger.error(f"CSV file not found: {args.csv_path}")
        return 1
    
    try:
        await populate_database(args.database_url, args.csv_path)
        logger.info("Population complete!")
        return 0
    except Exception as e:
        logger.error(f"Population failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))