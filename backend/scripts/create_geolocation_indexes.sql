-- Create indexes AFTER data population for optimal performance
-- This script should be run after bulk data insertion

-- Critical: GIST index for fast IP range queries
-- This index enables sub-millisecond IP lookups using PostgreSQL's inet operators
CREATE INDEX IF NOT EXISTS idx_ip_geolocation_range 
ON ip_geolocation USING GIST (
    INET_RANGE(start_ip, end_ip, '[]')
);

-- Additional indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_ip_geolocation_country 
ON ip_geolocation(country_code);

CREATE INDEX IF NOT EXISTS idx_ip_geolocation_start_ip 
ON ip_geolocation(start_ip);

CREATE INDEX IF NOT EXISTS idx_ip_geolocation_end_ip 
ON ip_geolocation(end_ip);

-- Composite index for EU countries (GDPR compliance queries)
CREATE INDEX IF NOT EXISTS idx_ip_geolocation_eu_country 
ON ip_geolocation(is_eu, country_code) 
WHERE is_eu = TRUE;

-- Create index on the function for even faster lookups
CREATE INDEX IF NOT EXISTS idx_ip_geolocation_lookup_function
ON ip_geolocation(start_ip, end_ip) 
WHERE start_ip IS NOT NULL AND end_ip IS NOT NULL;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Geolocation indexes created successfully';
END $$;