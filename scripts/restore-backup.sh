#!/bin/bash

# BioNewsBot Database Restore Script
# This script restores a PostgreSQL database from a backup

set -e

# Configuration
BACKUP_FILE="$1"
DB_NAME="${POSTGRES_DB:-bionewsbot}"
DB_USER="${POSTGRES_USER:-bionewsbot}"

# Colors for output
GREEN='[0;32m'
RED='[0;31m'
YELLOW='[1;33m'
NC='[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check arguments
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    echo "Example: $0 /root/bionewsbot/backups/bionewsbot_backup_20240101_120000.sql.gz"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Confirm restoration
log_warning "This will restore the database from: $BACKUP_FILE"
log_warning "This will OVERWRITE the current database: $DB_NAME"
echo -n "Are you sure you want to continue? (yes/no): "
read -r response

if [ "$response" != "yes" ]; then
    log_info "Restoration cancelled"
    exit 0
fi

# Stop application services
log_info "Stopping application services..."
docker-compose stop backend scheduler notifications frontend

# Drop and recreate database
log_info "Recreating database..."
docker-compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

# Restore from backup
log_info "Restoring database from backup..."
if gunzip -c "$BACKUP_FILE" | docker-compose exec -T postgres psql -U "${DB_USER}" "${DB_NAME}"; then
    log_info "Database restored successfully"
else
    log_error "Database restoration failed"
    exit 1
fi

# Restart services
log_info "Restarting application services..."
docker-compose start backend scheduler notifications frontend

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 10

# Run health check
if [ -f "./health-check.py" ]; then
    log_info "Running health check..."
    python3 ./health-check.py
fi

log_info "Restoration process completed"
