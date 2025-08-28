-- Rollback: 002_add_company_alerts_rollback.sql
-- Created: 2025-08-27
-- Description: Rollback for 002_add_company_alerts migration

-- Drop the alerts table
DROP TABLE IF EXISTS company_alerts;

-- Remove migration record
DELETE FROM schema_migrations WHERE version = '002_add_company_alerts';
