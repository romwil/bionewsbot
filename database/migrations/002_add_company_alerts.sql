-- Migration: 002_add_company_alerts.sql
-- Created: 2025-08-27
-- Description: Adds alert configuration for companies

-- Add alerts table for company-specific alert rules
CREATE TABLE company_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    alert_name VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'keyword', 'threshold', 'pattern'
    conditions JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    notification_channels TEXT[],
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add index for active alerts
CREATE INDEX idx_company_alerts_active ON company_alerts(company_id, is_active);

-- Add trigger for updated_at
CREATE TRIGGER update_company_alerts_updated_at BEFORE UPDATE ON company_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Record migration
INSERT INTO schema_migrations (version, applied_at, description) 
VALUES ('002_add_company_alerts', CURRENT_TIMESTAMP, 'Adds alert configuration for companies');
