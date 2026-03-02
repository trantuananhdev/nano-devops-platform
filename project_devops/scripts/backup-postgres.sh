#!/bin/bash
# PostgreSQL Backup Script for Nano DevOps Platform
# Creates logical backup using pg_dump, compresses, and manages retention

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/platform/data/backup}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-platform-postgres}"
POSTGRES_DB="${POSTGRES_DB:-platform_db}"
POSTGRES_USER="${POSTGRES_USER:-platform_user}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
LOG_FILE="${LOG_FILE:-/opt/platform/logs/backup-postgres.log}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/postgres_${TIMESTAMP}.sql.gz"

log_info "Starting PostgreSQL backup"
log_info "Container: $POSTGRES_CONTAINER"
log_info "Database: $POSTGRES_DB"
log_info "Backup file: $BACKUP_FILE"

# Check if PostgreSQL container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    log_error "PostgreSQL container '$POSTGRES_CONTAINER' is not running"
    exit 1
fi

# Perform backup using pg_dump inside container, pipe to gzip
log_info "Creating database dump..."
if docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl 2>/dev/null | gzip > "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Backup completed successfully: $BACKUP_FILE (Size: $BACKUP_SIZE)"
else
    log_error "Backup failed"
    exit 1
fi

# Verify backup file exists and is not empty
if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    log_error "Backup file is missing or empty"
    exit 1
fi

# Clean up old backups (retention policy)
log_info "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "postgres_*.sql.gz" -type f | wc -l)
log_info "Retention cleanup completed. Remaining backups: $REMAINING_BACKUPS"

log_info "PostgreSQL backup process completed successfully"
