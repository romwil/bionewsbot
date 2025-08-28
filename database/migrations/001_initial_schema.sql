-- Initial migration: Create database schema
-- Migration: 001_initial_schema.sql
-- Created: 2025-08-26
-- Description: Creates the initial BioNewsBot database schema

-- This migration creates all the base tables, indexes, and triggers
-- Run the main schema.sql file to apply this migration
\i /root/bionewsbot/database/schema.sql

-- Record migration
INSERT INTO schema_migrations (version, applied_at) 
VALUES ('001_initial_schema', CURRENT_TIMESTAMP);
