-- BioNewsBot Seed Data
-- Test data for development and testing
-- Created: 2025-08-26

-- Clear existing data (be careful in production!)
TRUNCATE TABLE watchlist_companies, watchlists, notifications, insights, raw_analysis_data, 
         analysis_runs, company_categories, categories, companies, configurations, users CASCADE;

-- Insert test users
INSERT INTO users (id, email, username, password_hash, full_name, role, is_active) VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'admin@bionewsbot.com', 'admin', 
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1eSyaS5y', -- password: admin123
     'System Administrator', 'admin', true),
    ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'analyst@bionewsbot.com', 'analyst1',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1eSyaS5y', -- password: admin123
     'Sarah Johnson', 'analyst', true),
    ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'viewer@bionewsbot.com', 'viewer1',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1eSyaS5y', -- password: admin123
     'John Doe', 'viewer', true);

-- Insert categories
INSERT INTO categories (id, name, description) VALUES
    ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'Pharmaceuticals', 'Companies developing pharmaceutical drugs'),
    ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'Biotechnology', 'Biotech and genetic engineering companies'),
    ('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'Medical Devices', 'Medical device manufacturers'),
    ('10eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'Diagnostics', 'Diagnostic test developers'),
    ('11eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'Digital Health', 'Digital health and healthtech companies');

-- Insert sub-categories
INSERT INTO categories (id, name, description, parent_id) VALUES
    ('20eebc99-9c0b-4ef8-bb6d-6bb9bd380a19', 'Oncology', 'Cancer therapeutics', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14'),
    ('21eebc99-9c0b-4ef8-bb6d-6bb9bd380a20', 'Neurology', 'Neurological therapeutics', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14'),
    ('22eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'Gene Therapy', 'Gene therapy companies', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15'),
    ('23eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Cell Therapy', 'Cell therapy companies', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15');

-- Insert sample companies
INSERT INTO companies (id, name, ticker, description, website, industry, sub_industry, 
                      headquarters_location, employee_count, founded_year, monitoring_status,
                      metadata, monitoring_config) VALUES
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a23', 'Moderna Inc', 'MRNA', 
     'Biotechnology company pioneering messenger RNA (mRNA) therapeutics and vaccines',
     'https://www.modernatx.com', 'Biotechnology', 'mRNA Therapeutics',
     'Cambridge, MA, USA', 3900, 2010, 'active',
     '{"market_cap": "$40B", "therapeutic_areas": ["vaccines", "oncology", "rare_diseases"]}',
     '{"priority": "high", "check_frequency": "hourly", "sources": ["news", "sec_filings", "clinical_trials"]}'),
    ('31eebc99-9c0b-4ef8-bb6d-6bb9bd380a24', 'Illumina Inc', 'ILMN',
     'Leading developer of sequencing and array-based solutions for genetic analysis',
     'https://www.illumina.com', 'Biotechnology', 'Genomics',
     'San Diego, CA, USA', 7800, 1998, 'active',
     '{"market_cap": "$22B", "products": ["sequencing_systems", "microarrays", "informatics"]}',
     '{"priority": "high", "check_frequency": "daily", "sources": ["news", "press_releases"]}'),
    ('32eebc99-9c0b-4ef8-bb6d-6bb9bd380a25', 'Vertex Pharmaceuticals', 'VRTX',
     'Global biotechnology company investing in scientific innovation to create transformative medicines',
     'https://www.vrtx.com', 'Pharmaceuticals', 'Specialty Pharmaceuticals',
     'Boston, MA, USA', 3500, 1989, 'active',
     '{"market_cap": "$90B", "focus_areas": ["cystic_fibrosis", "sickle_cell", "beta_thalassemia"]}',
     '{"priority": "high", "check_frequency": "daily", "sources": ["news", "clinical_trials", "sec_filings"]}'),
    ('33eebc99-9c0b-4ef8-bb6d-6bb9bd380a26', 'CRISPR Therapeutics', 'CRSP',
     'Gene editing company focused on developing transformative gene-based medicines',
     'https://www.crisprtx.com', 'Biotechnology', 'Gene Editing',
     'Zug, Switzerland', 500, 2013, 'active',
     '{"market_cap": "$4B", "platforms": ["CRISPR/Cas9", "CAR-T"]}',
     '{"priority": "medium", "check_frequency": "daily", "sources": ["news", "clinical_trials"]}'),
    ('34eebc99-9c0b-4ef8-bb6d-6bb9bd380a27', 'Medtronic plc', 'MDT',
     'Global leader in medical technology, services, and solutions',
     'https://www.medtronic.com', 'Medical Devices', 'Medical Equipment',
     'Dublin, Ireland', 90000, 1949, 'active',
     '{"market_cap": "$85B", "divisions": ["cardiac", "diabetes", "neuro", "surgical"]}',
     '{"priority": "medium", "check_frequency": "daily", "sources": ["news", "regulatory_filings"]}');

-- Link companies to categories
INSERT INTO company_categories (company_id, category_id) VALUES
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a23', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15'), -- Moderna -> Biotech
    ('30eebc99-9c0b-4ef8-bb6d-6bb9bd380a23', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14'), -- Moderna -> Pharma
    ('31eebc99-9c0b-4ef8-bb6d-6bb9bd380a24', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15'), -- Illumina -> Biotech
    ('31eebc99-9c0b-4ef8-bb6d-6bb9bd380a24', '10eebc99-9c0b-4ef8-bb6d-6bb9bd380a17'), -- Illumina -> Diagnostics
    ('32eebc99-9c0b-4ef8-bb6d-6bb9bd380a25', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14'), -- Vertex -> Pharma
    ('33eebc99-9c0b-4ef8-bb6d-6bb9bd380a26', 'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15'), -- CRISPR -> Biotech
    ('33eebc99-9c0b-4ef8-bb6d-6bb9bd380a26', '22eebc99-9c0b-4ef8-bb6d-6bb9bd380a21'), -- CRISPR -> Gene Therapy
    ('34eebc99-9c0b-4ef8-bb6d-6bb9bd380a27', 'f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16'); -- Medtronic -> Medical Devices

-- Insert system configurations
INSERT INTO configurations (key, value, description, is_sensitive) VALUES
    ('slack_webhook_url', '"https://hooks.slack.com/services/YOUR/WEBHOOK/URL"', 'Slack webhook for notifications', true),
    ('openai_api_key', '"sk-YOUR-API-KEY"', 'OpenAI API key for analysis', true),
    ('analysis_schedule', '{"interval": "hourly", "start_time": "09:00", "end_time": "18:00", "timezone": "UTC"}', 
     'Schedule for automated analysis runs', false),
    ('notification_settings', '{"channels": ["slack", "email"], "priority_threshold": "high", "batch_notifications": true}',
     'Global notification settings', false),
    ('llm_settings', '{"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000}',
     'LLM configuration for analysis', false);

-- Create sample watchlists
INSERT INTO watchlists (id, user_id, name, description, is_default) VALUES
    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a28', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 
     'High Priority Biotechs', 'Top biotech companies to monitor closely', true),
    ('41eebc99-9c0b-4ef8-bb6d-6bb9bd380a29', 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12',
     'Gene Editing Leaders', 'Companies in gene editing space', false);

-- Add companies to watchlists
INSERT INTO watchlist_companies (watchlist_id, company_id, notes) VALUES
    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a28', '30eebc99-9c0b-4ef8-bb6d-6bb9bd380a23', 'Monitor mRNA pipeline updates'),
    ('40eebc99-9c0b-4ef8-bb6d-6bb9bd380a28', '32eebc99-9c0b-4ef8-bb6d-6bb9bd380a25', 'Watch for CF treatment news'),
    ('41eebc99-9c0b-4ef8-bb6d-6bb9bd380a29', '33eebc99-9c0b-4ef8-bb6d-6bb9bd380a26', 'Track CRISPR clinical trials');

-- Insert sample analysis run
INSERT INTO analysis_runs (id, run_type, status, started_at, completed_at) VALUES
    ('50eebc99-9c0b-4ef8-bb6d-6bb9bd380a30', 'scheduled', 'completed', 
     '2025-08-26 14:00:00+00', '2025-08-26 14:15:00+00');

-- Insert sample raw analysis data
INSERT INTO raw_analysis_data (id, company_id, analysis_run_id, source, source_url, 
                              source_date, llm_model, llm_response, processing_time_ms, 
                              token_count, cost_usd) VALUES
    ('60eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', '30eebc99-9c0b-4ef8-bb6d-6bb9bd380a23',
     '50eebc99-9c0b-4ef8-bb6d-6bb9bd380a30', 'news', 
     'https://example.com/moderna-trial-results',
     '2025-08-26 12:00:00+00', 'gpt-4',
     '{"summary": "Moderna announces positive Phase 3 results", "sentiment": "positive", "key_points": ["90% efficacy", "Well tolerated", "FDA submission planned"], "impact_score": 0.85}',
     1250, 850, 0.0255);

-- Insert sample insight
INSERT INTO insights (id, company_id, analysis_run_id, raw_analysis_id, title, summary,
                     detailed_analysis, insight_type, priority, confidence_score,
                     impact_assessment, tags, is_actionable, action_required) VALUES
    ('70eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', '30eebc99-9c0b-4ef8-bb6d-6bb9bd380a23',
     '50eebc99-9c0b-4ef8-bb6d-6bb9bd380a30', '60eebc99-9c0b-4ef8-bb6d-6bb9bd380a31',
     'Moderna Reports Positive Phase 3 Trial Results for New mRNA Vaccine',
     'Moderna announced positive Phase 3 results showing 90% efficacy for their new mRNA vaccine candidate',
     'Detailed analysis: The Phase 3 trial enrolled 30,000 participants and demonstrated strong efficacy with a favorable safety profile. The company plans to submit for FDA approval in Q4 2025.',
     'clinical_trial', 'high', 0.92,
     '{"market_impact": "high", "regulatory_impact": "medium", "competitive_impact": "high"}',
     '["clinical-trial", "phase-3", "vaccine", "mRNA", "FDA-submission"]',
     true, 'Monitor FDA submission timeline and prepare market analysis');

-- Insert sample notification
INSERT INTO notifications (id, insight_id, channel, recipient, status, message,
                          metadata, sent_at, error_message) VALUES
    ('80eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', '70eebc99-9c0b-4ef8-bb6d-6bb9bd380a32',
     'slack', '#biotech-alerts', 'sent',
     '🚨 HIGH PRIORITY: Moderna Reports Positive Phase 3 Trial Results\n\nModerna announced 90% efficacy for new mRNA vaccine. FDA submission planned for Q4 2025.\n\nView full analysis: https://bionewsbot.com/insights/70eebc99-9c0b-4ef8-bb6d-6bb9bd380a32',
     '{"webhook_response": "ok", "message_ts": "1234567890.123456"}',
     '2025-08-26 14:20:00+00', NULL);

-- End of seed data
-- To load this data, run: psql -U bionewsbot -d bionewsbot -f 001_initial_seed_data.sql
