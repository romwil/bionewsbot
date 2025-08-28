-- BioNewsBot Database Schema
-- PostgreSQL database for life sciences company intelligence platform
-- Version: 1.0.0
-- Created: 2025-08-26

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE company_status AS ENUM ('active', 'inactive', 'pending', 'archived');
CREATE TYPE analysis_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE insight_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed', 'cancelled');
CREATE TYPE user_role AS ENUM ('admin', 'analyst', 'viewer');


-- Companies table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    ticker VARCHAR(20),
    description TEXT,
    website VARCHAR(500),
    industry VARCHAR(100),
    sub_industry VARCHAR(100),
    headquarters_location VARCHAR(255),
    employee_count INTEGER,
    founded_year INTEGER,
    metadata JSONB DEFAULT '{}',
    monitoring_status company_status DEFAULT 'active',
    monitoring_config JSONB DEFAULT '{}',
    last_analysis_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT companies_name_unique UNIQUE (name),
    CONSTRAINT companies_ticker_unique UNIQUE (ticker)
);


-- Company categories
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Company to category mapping (many-to-many)
CREATE TABLE company_categories (
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (company_id, category_id)
);


-- Analysis runs table
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_type VARCHAR(50) NOT NULL, -- 'scheduled', 'manual', 'triggered'
    status analysis_status DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw analysis data (stores LLM outputs)
CREATE TABLE raw_analysis_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    source VARCHAR(100) NOT NULL, -- 'news', 'sec_filing', 'press_release', etc.
    source_url TEXT,
    source_date TIMESTAMP WITH TIME ZONE,
    llm_model VARCHAR(50),
    llm_response JSONB NOT NULL,
    processing_time_ms INTEGER,
    token_count INTEGER,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insights table (extracted high-priority events)
CREATE TABLE insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    raw_analysis_id UUID REFERENCES raw_analysis_data(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    detailed_analysis TEXT,
    insight_type VARCHAR(100) NOT NULL, -- 'clinical_trial', 'regulatory', 'financial', etc.
    priority insight_priority DEFAULT 'medium',
    confidence_score DECIMAL(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    impact_assessment JSONB DEFAULT '{}',
    tags TEXT[],
    is_actionable BOOLEAN DEFAULT false,
    action_required TEXT,
    expiry_date TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);


-- Notification history
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    insight_id UUID REFERENCES insights(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL, -- 'slack', 'email', 'webhook'
    recipient VARCHAR(255) NOT NULL,
    status notification_status DEFAULT 'pending',
    subject VARCHAR(500),
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}',
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- User sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Configuration table
CREATE TABLE configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Watchlists (user-specific company lists)
CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT watchlists_user_name_unique UNIQUE (user_id, name)
);

-- Watchlist companies
CREATE TABLE watchlist_companies (
    watchlist_id UUID REFERENCES watchlists(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    PRIMARY KEY (watchlist_id, company_id)
);

-- Create indexes for performance
CREATE INDEX idx_companies_monitoring_status ON companies(monitoring_status) WHERE deleted_at IS NULL;
CREATE INDEX idx_companies_last_analysis ON companies(last_analysis_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_companies_ticker ON companies(ticker) WHERE ticker IS NOT NULL;
CREATE INDEX idx_companies_metadata ON companies USING GIN (metadata);

CREATE INDEX idx_categories_parent ON categories(parent_id);

CREATE INDEX idx_analysis_runs_status ON analysis_runs(status);
CREATE INDEX idx_analysis_runs_created ON analysis_runs(created_at);

CREATE INDEX idx_raw_analysis_company ON raw_analysis_data(company_id);
CREATE INDEX idx_raw_analysis_run ON raw_analysis_data(analysis_run_id);
CREATE INDEX idx_raw_analysis_source ON raw_analysis_data(source);
CREATE INDEX idx_raw_analysis_date ON raw_analysis_data(source_date);
CREATE INDEX idx_raw_analysis_llm_response ON raw_analysis_data USING GIN (llm_response);

CREATE INDEX idx_insights_company ON insights(company_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_insights_priority ON insights(priority) WHERE deleted_at IS NULL;
CREATE INDEX idx_insights_type ON insights(insight_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_insights_created ON insights(created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_insights_tags ON insights USING GIN (tags) WHERE deleted_at IS NULL;
CREATE INDEX idx_insights_metadata ON insights USING GIN (metadata);

CREATE INDEX idx_notifications_insight ON notifications(insight_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created ON notifications(created_at);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);


-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables with updated_at
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analysis_runs_updated_at BEFORE UPDATE ON analysis_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_raw_analysis_updated_at BEFORE UPDATE ON raw_analysis_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_insights_updated_at BEFORE UPDATE ON insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configurations_updated_at BEFORE UPDATE ON configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watchlists_updated_at BEFORE UPDATE ON watchlists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (action, entity_type, entity_id, new_values)
        VALUES (TG_OP, TG_TABLE_NAME, NEW.id, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (action, entity_type, entity_id, old_values, new_values)
        VALUES (TG_OP, TG_TABLE_NAME, NEW.id, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (action, entity_type, entity_id, old_values)
        VALUES (TG_OP, TG_TABLE_NAME, OLD.id, to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to critical tables
CREATE TRIGGER audit_companies AFTER INSERT OR UPDATE OR DELETE ON companies
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_insights AFTER INSERT OR UPDATE OR DELETE ON insights
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_configurations AFTER INSERT OR UPDATE OR DELETE ON configurations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
