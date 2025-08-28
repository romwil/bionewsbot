# BioNewsBot Database Performance Optimization Guide

## Overview
This document provides comprehensive performance optimization recommendations for the BioNewsBot PostgreSQL database, focusing on query performance, indexing strategies, and scalability.

## 1. Indexing Strategy

### Primary Indexes (Already Implemented)
```sql
-- High-frequency query patterns
CREATE INDEX idx_companies_monitoring_status ON companies(monitoring_status) WHERE deleted_at IS NULL;
CREATE INDEX idx_insights_priority_created ON insights(priority, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_raw_analysis_company_created ON raw_analysis_data(company_id, created_at DESC);
```

### Recommended Additional Indexes
```sql
-- For frequent company lookups by name
CREATE INDEX idx_companies_name_trgm ON companies USING gin(name gin_trgm_ops);

-- For tag-based insight searches
CREATE INDEX idx_insights_tags_gin ON insights USING gin(tags);

-- For time-based analysis queries
CREATE INDEX idx_analysis_runs_date ON analysis_runs(date(started_at));

-- For notification delivery monitoring
CREATE INDEX idx_notifications_pending ON notifications(created_at) 
WHERE status = 'pending';

-- For JSONB query performance
CREATE INDEX idx_companies_metadata_gin ON companies USING gin(metadata jsonb_path_ops);
CREATE INDEX idx_raw_analysis_llm_response_gin ON raw_analysis_data USING gin(llm_response jsonb_path_ops);
```

## 2. Query Optimization Techniques

### Use Materialized Views for Complex Aggregations
```sql
-- Daily company activity summary
CREATE MATERIALIZED VIEW mv_daily_company_activity AS
SELECT 
    c.id,
    c.name,
    c.ticker,
    DATE(r.created_at) as activity_date,
    COUNT(DISTINCT r.id) as analysis_count,
    COUNT(DISTINCT i.id) as insight_count,
    MAX(i.priority) as max_priority
FROM companies c
LEFT JOIN raw_analysis_data r ON c.id = r.company_id
LEFT JOIN insights i ON c.id = i.company_id AND DATE(i.created_at) = DATE(r.created_at)
WHERE c.deleted_at IS NULL
GROUP BY c.id, c.name, c.ticker, DATE(r.created_at);

CREATE INDEX idx_mv_daily_activity ON mv_daily_company_activity(activity_date, ticker);

-- Refresh strategy
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_company_activity;
```

### Optimize JSONB Queries
```sql
-- Instead of:
SELECT * FROM companies WHERE metadata->>'market_cap' = '$40B';

-- Use:
SELECT * FROM companies WHERE metadata @> '{"market_cap": "$40B"}';

-- For nested JSONB queries, create specific indexes:
CREATE INDEX idx_companies_market_cap ON companies((metadata->>'market_cap'));
```

## 3. Partitioning Strategy

### Partition Large Tables by Time
```sql
-- Partition raw_analysis_data by month
CREATE TABLE raw_analysis_data_partitioned (
    LIKE raw_analysis_data INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE raw_analysis_data_2025_01 PARTITION OF raw_analysis_data_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE raw_analysis_data_2025_02 PARTITION OF raw_analysis_data_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Automated partition creation
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE + interval '1 month');
    end_date := start_date + interval '1 month';
    partition_name := 'raw_analysis_data_' || to_char(start_date, 'YYYY_MM');

    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF raw_analysis_data_partitioned
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

## 4. Connection Pooling

### PgBouncer Configuration
```ini
[databases]
bionewsbot = host=localhost port=5432 dbname=bionewsbot

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
server_lifetime = 3600
server_idle_timeout = 600
```

## 5. PostgreSQL Configuration Tuning

### Memory Settings
```sql
-- For 32GB RAM server
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 64MB
maintenance_work_mem = 2GB

-- JSONB specific
jsonb_path_ops = on
```

### Write Performance
```sql
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
min_wal_size = 1GB
```

### Query Planning
```sql
random_page_cost = 1.1  -- For SSD storage
effective_io_concurrency = 200
default_statistics_target = 100
```

## 6. Monitoring and Maintenance

### Key Metrics to Monitor
```sql
-- Query performance
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top slow queries
SELECT 
    query,
    mean_exec_time,
    calls,
    total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table bloat monitoring
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS external_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Automated Maintenance Tasks
```sql
-- Daily VACUUM ANALYZE
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule('daily-vacuum', '0 2 * * *', $$
    VACUUM ANALYZE companies;
    VACUUM ANALYZE raw_analysis_data;
    VACUUM ANALYZE insights;
$$);

-- Weekly REINDEX for heavily updated tables
SELECT cron.schedule('weekly-reindex', '0 3 * * 0', $$
    REINDEX TABLE CONCURRENTLY insights;
    REINDEX TABLE CONCURRENTLY notifications;
$$);
```

## 7. Caching Strategy

### Application-Level Caching
```python
# Redis configuration for frequently accessed data
CACHE_CONFIG = {
    'company_details': {'ttl': 3600},  # 1 hour
    'category_tree': {'ttl': 86400},   # 24 hours
    'user_watchlists': {'ttl': 300},   # 5 minutes
    'latest_insights': {'ttl': 60}     # 1 minute
}
```

### Database Result Caching
```sql
-- Use prepared statements for repeated queries
PREPARE get_company_insights AS
SELECT * FROM insights 
WHERE company_id = $1 
AND created_at > NOW() - INTERVAL '7 days'
ORDER BY priority DESC, created_at DESC;

EXECUTE get_company_insights('company-uuid-here');
```

## 8. Scaling Strategies

### Read Replica Configuration
```sql
-- On primary
CREATE PUBLICATION bionewsbot_pub FOR ALL TABLES;

-- On replica
CREATE SUBSCRIPTION bionewsbot_sub
CONNECTION 'host=primary_host dbname=bionewsbot'
PUBLICATION bionewsbot_pub;
```

### Sharding Considerations
- Shard by company_id for even distribution
- Use consistent hashing for shard selection
- Implement cross-shard query federation

## 9. Performance Testing

### Load Testing Queries
```sql
-- Simulate concurrent analysis queries
CREATE OR REPLACE FUNCTION load_test_analysis()
RETURNS TABLE(execution_time interval) AS $$
BEGIN
    RETURN QUERY
    SELECT clock_timestamp() - start_time
    FROM (
        SELECT clock_timestamp() as start_time,
               (SELECT COUNT(*) FROM raw_analysis_data 
                WHERE created_at > NOW() - INTERVAL '1 hour') as cnt
    ) t;
END;
$$ LANGUAGE plpgsql;
```

## 10. Emergency Performance Fixes

### Quick Wins
```sql
-- Kill long-running queries
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '5 minutes'
  AND query NOT LIKE '%pg_stat_activity%';

-- Emergency index creation
CREATE INDEX CONCURRENTLY emergency_idx ON table_name(column_name);

-- Disable expensive triggers temporarily
ALTER TABLE insights DISABLE TRIGGER audit_trigger;
-- Run batch operation
ALTER TABLE insights ENABLE TRIGGER audit_trigger;
```

## Performance Checklist

- [ ] All foreign keys have indexes
- [ ] JSONB columns use GIN indexes with jsonb_path_ops
- [ ] Partial indexes used for filtered queries
- [ ] Materialized views for complex aggregations
- [ ] Connection pooling configured
- [ ] Monitoring alerts set up
- [ ] Backup and recovery tested
- [ ] Query timeout configured
- [ ] Statement timeout set
- [ ] Autovacuum tuned for workload
