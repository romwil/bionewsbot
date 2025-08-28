# BioNewsBot Database Documentation

## Overview
The BioNewsBot database is designed to support a life sciences company intelligence platform that monitors companies for critical events, stores analysis results, and manages notifications. The schema uses PostgreSQL with JSONB for flexible storage of LLM outputs.

## Database Schema Version
Version: 1.0.0
Created: 2025-08-26

## Tables

### 1. users
**Purpose**: Stores user accounts for system access
**Key Fields**:
- `id` (UUID): Primary key
- `email`: Unique email address
- `username`: Unique username
- `password_hash`: Bcrypt hashed password
- `role`: User role (admin, analyst, viewer)
- `is_active`: Account status

### 2. sessions
**Purpose**: Manages user authentication sessions
**Key Fields**:
- `id` (UUID): Primary key
- `user_id`: Foreign key to users
- `token`: Unique session token
- `expires_at`: Session expiration timestamp
**Relationships**: Many-to-one with users

### 3. categories
**Purpose**: Hierarchical categorization of companies
**Key Fields**:
- `id` (UUID): Primary key
- `name`: Category name
- `parent_id`: Self-referential foreign key for hierarchy
**Features**: Supports nested categories (e.g., Pharmaceuticals > Oncology)

### 4. companies
**Purpose**: Core entity storing company information
**Key Fields**:
- `id` (UUID): Primary key
- `name`: Company name
- `ticker`: Stock ticker symbol
- `monitoring_status`: Current monitoring state (active, paused, inactive)
- `metadata` (JSONB): Flexible storage for additional data
- `monitoring_config` (JSONB): Company-specific monitoring settings
**Indexes**: 
- Unique on ticker
- Index on monitoring_status
- GIN index on metadata for JSONB queries

### 5. company_categories
**Purpose**: Many-to-many relationship between companies and categories
**Key Fields**:
- `company_id`: Foreign key to companies
- `category_id`: Foreign key to categories
**Constraints**: Composite primary key prevents duplicates

### 6. analysis_runs
**Purpose**: Tracks execution of analysis jobs
**Key Fields**:
- `id` (UUID): Primary key
- `run_type`: Type of run (scheduled, manual, triggered)
- `status`: Current status (pending, running, completed, failed)
- `started_at`: Run start timestamp
- `completed_at`: Run completion timestamp
**Indexes**: Index on status and started_at for job monitoring

### 7. raw_analysis_data
**Purpose**: Stores raw LLM analysis outputs
**Key Fields**:
- `id` (UUID): Primary key
- `company_id`: Foreign key to companies
- `analysis_run_id`: Foreign key to analysis_runs
- `llm_response` (JSONB): Complete LLM output
- `processing_time_ms`: Performance metric
- `token_count`: Usage tracking
- `cost_usd`: Cost tracking
**Indexes**: 
- Composite index on company_id and created_at
- GIN index on llm_response for JSONB queries

### 8. insights
**Purpose**: Extracted high-priority events and findings
**Key Fields**:
- `id` (UUID): Primary key
- `company_id`: Foreign key to companies
- `priority`: Priority level (low, medium, high, critical)
- `confidence_score`: AI confidence in the insight
- `impact_assessment` (JSONB): Structured impact analysis
- `is_actionable`: Whether action is required
- `tags` (TEXT[]): Array of searchable tags
**Indexes**: 
- Index on priority and created_at
- GIN index on tags for array searches

### 9. notifications
**Purpose**: Tracks sent notifications
**Key Fields**:
- `id` (UUID): Primary key
- `insight_id`: Foreign key to insights
- `channel`: Notification channel (slack, email, webhook)
- `status`: Delivery status (pending, sent, failed)
- `metadata` (JSONB): Channel-specific response data
**Indexes**: Index on status and created_at

### 10. configurations
**Purpose**: System-wide configuration storage
**Key Fields**:
- `key`: Configuration key (primary key)
- `value` (JSONB): Configuration value
- `is_sensitive`: Flag for sensitive data
**Features**: Supports complex configuration structures

### 11. watchlists
**Purpose**: User-created company watchlists
**Key Fields**:
- `id` (UUID): Primary key
- `user_id`: Foreign key to users
- `name`: Watchlist name
- `is_default`: Default watchlist flag
**Relationships**: Many-to-many with companies through watchlist_companies

### 12. watchlist_companies
**Purpose**: Links companies to watchlists
**Key Fields**:
- `watchlist_id`: Foreign key to watchlists
- `company_id`: Foreign key to companies
- `notes`: User notes about the company

### 13. audit_logs
**Purpose**: Tracks all data modifications
**Key Fields**:
- `id` (UUID): Primary key
- `table_name`: Modified table
- `operation`: SQL operation (INSERT, UPDATE, DELETE)
- `user_id`: User who made the change
- `old_data` (JSONB): Previous values
- `new_data` (JSONB): New values
**Features**: Automatic logging via triggers

## Key Design Decisions

### 1. UUID Primary Keys
- **Rationale**: Enables distributed ID generation, prevents enumeration attacks
- **Implementation**: Uses uuid_generate_v4() function

### 2. JSONB Storage
- **Use Cases**: LLM responses, metadata, configurations
- **Benefits**: Schema flexibility, powerful querying with GIN indexes
- **Trade-offs**: Slightly larger storage, requires careful index management

### 3. Soft Deletes
- **Implementation**: deleted_at timestamp field
- **Benefits**: Data recovery, audit trail preservation
- **Queries**: Use WHERE deleted_at IS NULL

### 4. Automatic Timestamps
- **Fields**: created_at, updated_at on all tables
- **Implementation**: Trigger-based updates
- **Benefits**: Consistent audit trail

### 5. Enum Types
- **Custom Types**: user_role, monitoring_status, analysis_status, etc.
- **Benefits**: Data integrity, clear constraints
- **Migration**: Can add new values without schema changes

## Relationships Diagram

```
users ----< sessions
  |  
  +------< watchlists ----< watchlist_companies >---- companies
  |                                                      |   |
  +------< audit_logs                                    |   |
                                                         |   |
categories (self-referential) <---- company_categories >-+   |
                                                             |
analysis_runs <---- raw_analysis_data >----------------------+
       |                    |
       +----< insights <----+
                 |
                 +----< notifications

configurations (standalone)
```

## Query Patterns and Indexes

### Common Query Patterns
1. **Latest insights by priority**
   ```sql
   SELECT * FROM insights 
   WHERE priority IN ('high', 'critical') 
   AND created_at > NOW() - INTERVAL '24 hours'
   ORDER BY created_at DESC;
   ```

2. **Company analysis history**
   ```sql
   SELECT c.name, r.* 
   FROM raw_analysis_data r
   JOIN companies c ON r.company_id = c.id
   WHERE c.ticker = 'MRNA'
   ORDER BY r.created_at DESC;
   ```

3. **JSONB metadata queries**
   ```sql
   SELECT * FROM companies
   WHERE metadata @> '{"market_cap": "$40B"}';
   ```

## Security Considerations

1. **Password Storage**: Uses bcrypt with cost factor 12
2. **Session Management**: Token-based with expiration
3. **Sensitive Data**: Marked with is_sensitive flag
4. **Row-Level Security**: Can be implemented per tenant
5. **Audit Trail**: Complete history in audit_logs

## Maintenance Tasks

1. **Regular VACUUM**: For JSONB and deleted rows
2. **Index Maintenance**: Monitor bloat, rebuild as needed
3. **Partition Considerations**: For large tables (raw_analysis_data)
4. **Backup Strategy**: Point-in-time recovery enabled
5. **Archive Old Data**: Move to cold storage after retention period
