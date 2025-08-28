#!/bin/bash

# BioNewsBot Database Backup Script
# This script creates timestamped backups of the PostgreSQL database

set -e

# Configuration
BACKUP_DIR="/root/bionewsbot/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_NAME="${POSTGRES_DB:-bionewsbot}"
DB_USER="${POSTGRES_USER:-bionewsbot}"
BACKUP_FILE="${BACKUP_DIR}/bionewsbot_backup_${DATE}.sql.gz"
RETENTION_DAYS=30

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

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if running inside Docker or on host
if [ -f /.dockerenv ]; then
    log_error "This script should be run from the host, not inside a container"
    exit 1
fi

# Perform backup
log_info "Starting database backup..."
log_info "Database: ${DB_NAME}"
log_info "Backup file: ${BACKUP_FILE}"

# Use docker-compose to execute pg_dump
if docker-compose exec -T postgres pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"; then
    log_info "Backup completed successfully"

    # Get backup size
    BACKUP_SIZE=$(ls -lh "${BACKUP_FILE}" | awk '{print $5}')
    log_info "Backup size: ${BACKUP_SIZE}"
else
    log_error "Backup failed"
    exit 1
fi

# Clean up old backups
log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "bionewsbot_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

# List recent backups
log_info "Recent backups:"
ls -lht "${BACKUP_DIR}" | head -n 6

# Optional: Upload to cloud storage
# Uncomment and configure as needed
# if command -v aws &> /dev/null; then
#     log_info "Uploading to S3..."
#     aws s3 cp "${BACKUP_FILE}" "s3://your-bucket/backups/"
# fi

log_info "Backup process completed"
