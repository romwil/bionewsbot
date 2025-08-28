# BioNewsBot Database

This directory contains the complete database architecture for the BioNewsBot life sciences intelligence platform.

## Contents

- `schema.sql` - Complete PostgreSQL database schema with all tables, indexes, and constraints
- `migrations/` - Database migration files for version control
  - `000_schema_migrations.sql` - Migration tracking table
  - `001_initial_schema.sql` - Initial schema creation
  - `002_add_company_alerts.sql` - Example feature migration
- `seeds/` - Test data for development
  - `001_initial_seed_data.sql` - Comprehensive test dataset
- `DATABASE_DOCUMENTATION.md` - Detailed documentation of all tables and relationships
- `PERFORMANCE_OPTIMIZATION.md` - Performance tuning guide and recommendations

## Quick Start

1. Create the database:
   ```bash
   createdb bionewsbot
   ```

2. Install extensions:
   ```bash
   psql -d bionewsbot -c "CREATE EXTENSION IF NOT EXISTS "uuid-ossp";"
   ```

3. Apply the schema:
   ```bash
   psql -d bionewsbot -f schema.sql
   ```

4. Load test data:
   ```bash
   psql -d bionewsbot -f seeds/001_initial_seed_data.sql
   ```

## Key Features

- UUID primary keys for distributed systems
- JSONB storage for flexible LLM data
- Comprehensive audit logging
- Optimized indexes for common queries
- Soft deletes for data recovery
- Automatic timestamp management

## Performance Considerations

- GIN indexes on JSONB columns
- Partial indexes for filtered queries
- Prepared statements for repeated queries
- Connection pooling recommended
- Regular VACUUM and ANALYZE scheduled

See `PERFORMANCE_OPTIMIZATION.md` for detailed tuning guide.
