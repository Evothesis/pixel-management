-- PostgreSQL geolocation database initialization script
-- Stage 1: Creates table structure without indexes for optimal bulk loading
-- Indexes are created AFTER data population for maximum performance

-- Create the main geolocation table
CREATE TABLE IF NOT EXISTS ip_geolocation (
    id SERIAL PRIMARY KEY,
    start_ip INET NOT NULL,
    end_ip INET NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    country_name VARCHAR(100),
    region_name VARCHAR(100),
    city_name VARCHAR(100),
    postal_code VARCHAR(20),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    is_eu BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes are created AFTER data population for optimal performance
-- Use create_geolocation_indexes.sql after bulk data import

-- Create a function for optimized IP lookup
CREATE OR REPLACE FUNCTION lookup_ip_location(ip_addr INET)
RETURNS TABLE(
    country_code VARCHAR(2),
    country_name VARCHAR(100),
    region_name VARCHAR(100),
    city_name VARCHAR(100),
    postal_code VARCHAR(20),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    is_eu BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        g.country_code,
        g.country_name,
        g.region_name,
        g.city_name,
        g.postal_code,
        g.latitude,
        g.longitude,
        g.is_eu
    FROM ip_geolocation g
    WHERE g.start_ip <= ip_addr AND g.end_ip >= ip_addr
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function indexes will be created AFTER data population for optimal performance

-- Table for tracking database updates
CREATE TABLE IF NOT EXISTS geolocation_metadata (
    id SERIAL PRIMARY KEY,
    database_version VARCHAR(50),
    source_name VARCHAR(100),
    record_count INTEGER,
    build_date TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW(),
    checksum VARCHAR(64)
);

-- Insert initial metadata
INSERT INTO geolocation_metadata (
    database_version, 
    source_name, 
    record_count, 
    build_date
) VALUES (
    '1.0.0',
    'DB-IP Lite',
    0,
    NOW()
) ON CONFLICT DO NOTHING;

-- Performance monitoring view
CREATE OR REPLACE VIEW geolocation_stats AS
SELECT 
    COUNT(*) as total_ranges,
    COUNT(DISTINCT country_code) as unique_countries,
    COUNT(DISTINCT region_name) as unique_regions,
    MIN(start_ip) as min_ip,
    MAX(end_ip) as max_ip,
    pg_size_pretty(pg_total_relation_size('ip_geolocation')) as table_size,
    pg_size_pretty(pg_indexes_size('ip_geolocation')) as index_size
FROM ip_geolocation;

-- Grant permissions for the application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ip_geolocation TO pixeluser;
GRANT SELECT, INSERT, UPDATE, DELETE ON geolocation_metadata TO pixeluser;
GRANT SELECT ON geolocation_stats TO pixeluser;
GRANT USAGE ON SEQUENCE ip_geolocation_id_seq TO pixeluser;
GRANT USAGE ON SEQUENCE geolocation_metadata_id_seq TO pixeluser;

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'IP geolocation database schema initialized successfully';
    RAISE NOTICE 'Created table: ip_geolocation (indexes will be added after data population)';
    RAISE NOTICE 'Created function: lookup_ip_location() for fast queries';
    RAISE NOTICE 'Ready for DB-IP data population via PostgreSQL COPY FROM';
    RAISE NOTICE 'Use populate_geolocation_db.py for optimized bulk data loading';
END $$;