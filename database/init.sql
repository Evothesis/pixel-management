-- database/init.sql
-- Evothesis Pixel Management Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core clients table
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    
    -- Infrastructure configuration
    deployment_type VARCHAR(20) DEFAULT 'shared' NOT NULL CHECK (deployment_type IN ('shared', 'dedicated')),
    vm_hostname VARCHAR(255),
    
    -- Privacy & compliance configuration
    privacy_level VARCHAR(20) DEFAULT 'standard' NOT NULL CHECK (privacy_level IN ('standard', 'gdpr', 'hipaa')),
    ip_collection_enabled BOOLEAN DEFAULT true NOT NULL,
    ip_salt VARCHAR(128),
    consent_required BOOLEAN DEFAULT false NOT NULL,
    
    -- Tracking features as JSON
    features JSONB DEFAULT '{}' NOT NULL,
    
    -- Billing configuration
    monthly_event_limit INTEGER,
    billing_rate_per_1k DECIMAL(6,4) DEFAULT 0.01 NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true NOT NULL
);

-- Tracking domains - which domains belong to which client
CREATE TABLE IF NOT EXISTS tracking_domains (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL UNIQUE, -- Each domain can only belong to one client
    is_primary BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Configuration change audit log
CREATE TABLE IF NOT EXISTS configuration_changes (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    changed_by VARCHAR(100) NOT NULL,
    change_description TEXT NOT NULL,
    old_config JSONB,
    new_config JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_clients_client_id ON clients(client_id);
CREATE INDEX IF NOT EXISTS idx_clients_active ON clients(is_active);
CREATE INDEX IF NOT EXISTS idx_tracking_domains_domain ON tracking_domains(domain);
CREATE INDEX IF NOT EXISTS idx_tracking_domains_client_id ON tracking_domains(client_id);
CREATE INDEX IF NOT EXISTS idx_config_changes_client_id ON configuration_changes(client_id);
CREATE INDEX IF NOT EXISTS idx_config_changes_timestamp ON configuration_changes(timestamp);

-- Insert default test client for development
INSERT INTO clients (client_id, name, email, privacy_level, features) 
VALUES (
    'client_development', 
    'Development Test Client', 
    'dev@evothesis.com', 
    'standard',
    '{"scroll_tracking": true, "form_tracking": true, "copy_tracking": true}'
) ON CONFLICT (client_id) DO NOTHING;

-- Add localhost domain for development client
INSERT INTO tracking_domains (client_id, domain, is_primary)
VALUES ('client_development', 'localhost', true)
ON CONFLICT (domain) DO NOTHING;