-- BioNewsBot Initial Seed Data
-- This file contains initial data for testing and development

BEGIN;

-- Insert default categories
INSERT INTO categories (id, name, description) VALUES
    (gen_random_uuid(), 'Oncology', 'Cancer research and therapeutics'),
    (gen_random_uuid(), 'Immunology', 'Immune system and immunotherapies'),
    (gen_random_uuid(), 'Neurology', 'Neurological disorders and treatments'),
    (gen_random_uuid(), 'Cardiology', 'Cardiovascular diseases and therapies'),
    (gen_random_uuid(), 'Rare Diseases', 'Orphan drugs and rare disease treatments')
ON CONFLICT (name) DO NOTHING;

-- Insert default users (for development/testing)
INSERT INTO users (id, email, username, full_name, is_active, is_admin) VALUES
    (gen_random_uuid(), 'admin@bionewsbot.com', 'admin', 'System Administrator', true, true),
    (gen_random_uuid(), 'analyst@bionewsbot.com', 'analyst', 'Data Analyst', true, false),
    (gen_random_uuid(), 'viewer@bionewsbot.com', 'viewer', 'Read-only User', true, false)
ON CONFLICT (email) DO NOTHING;

-- Insert sample companies (for demonstration)
INSERT INTO companies (id, name, description, website, focus_areas, metadata) VALUES
    (
        gen_random_uuid(),
        'Moderna',
        'mRNA therapeutics and vaccine development company',
        'https://www.modernatx.com',
        ARRAY['mRNA technology', 'vaccines', 'rare diseases'],
        '{
            "founded": "2010",
            "headquarters": "Cambridge, MA",
            "employees": "3900+",
            "stock_symbol": "MRNA"
        }'::jsonb
    ),
    (
        gen_random_uuid(),
        'BioNTech',
        'Biotechnology company developing immunotherapies',
        'https://www.biontech.de',
        ARRAY['immunotherapy', 'mRNA vaccines', 'oncology'],
        '{
            "founded": "2008",
            "headquarters": "Mainz, Germany",
            "employees": "3000+",
            "stock_symbol": "BNTX"
        }'::jsonb
    ),
    (
        gen_random_uuid(),
        'Gilead Sciences',
        'Biopharmaceutical company focused on antiviral drugs',
        'https://www.gilead.com',
        ARRAY['antivirals', 'oncology', 'inflammatory diseases'],
        '{
            "founded": "1987",
            "headquarters": "Foster City, CA",
            "employees": "14000+",
            "stock_symbol": "GILD"
        }'::jsonb
    )
ON CONFLICT (name) DO NOTHING;

-- Insert notification preferences for admin user
INSERT INTO notification_preferences (id, user_id, channel, event_types, is_enabled, settings)
SELECT 
    gen_random_uuid(),
    id,
    'slack',
    ARRAY['analysis_complete', 'insight_generated', 'error_occurred'],
    true,
    '{
        "slack_channel": "#bionewsbot-alerts",
        "mention_on_error": true,
        "daily_summary": true
    }'::jsonb
FROM users WHERE email = 'admin@bionewsbot.com'
ON CONFLICT DO NOTHING;

COMMIT;

-- Verify seed data
SELECT 'Categories' as table_name, COUNT(*) as count FROM categories
UNION ALL
SELECT 'Users', COUNT(*) FROM users
UNION ALL
SELECT 'Companies', COUNT(*) FROM companies
UNION ALL
SELECT 'Notification Preferences', COUNT(*) FROM notification_preferences;
