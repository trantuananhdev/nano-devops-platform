#!/bin/bash
# Redis Backup Script for Nano DevOps Platform
# Creates RDB snapshot backup from Redis container

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/platform/data/backup}"
REDIS_CONTAINER="${REDIS_CONTAINER:-platform-redis}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
LOG_FILE="${LOG_FILE:-/opt/platform/logs/backup-redis.log}"

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
BACKUP_FILE="${BACKUP_DIR}/redis_${TIMESTAMP}.rdb.gz"

log_info "Starting Redis backup"
log_info "Container: $REDIS_CONTAINER"
log_info "Backup file: $BACKUP_FILE"

# Check if Redis container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
    log_error "Redis container '$REDIS_CONTAINER' is not running"
    exit 1
fi

# Get Redis data directory from container
REDIS_DATA_DIR=$(docker inspect "$REDIS_CONTAINER" --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}')

if [ -z "$REDIS_DATA_DIR" ]; then
    log_error "Could not determine Redis data directory"
    exit 1
fi

log_info "Redis data directory: $REDIS_DATA_DIR"

# Trigger Redis SAVE command to create RDB snapshot
log_info "Triggering Redis SAVE command..."
if ! docker exec "$REDIS_CONTAINER" redis-cli SAVE >/dev/null 2>&1; then
    log_error "Failed to trigger Redis SAVE"
    exit 1
fi

# Wait a moment for SAVE to complete
sleep 2

# Find the RDB file (usually dump.rdb or appendonly.aof)
RDB_FILE=""
if [ -f "${REDIS_DATA_DIR}/dump.rdb" ]; then
    RDB_FILE="${REDIS_DATA_DIR}/dump.rdb"
elif [ -f "${REDIS_DATA_DIR}/appendonly.aof" ]; then
    RDB_FILE="${REDIS_DATA_DIR}/appendonly.aof"
    log_warn "Using AOF file instead of RDB (Redis configured with appendonly yes)"
else
    log_error "Could not find Redis data file (dump.rdb or appendonly.aof)"
    exit 1
fi

log_info "Found Redis data file: $RDB_FILE"

# Copy and compress the RDB file
log_info "Copying and compressing Redis data..."
if gzip -c "$RDB_FILE" > "$BACKUP_FILE"; then
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
find "$BACKUP_DIR" -name "redis_*.rdb.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "redis_*.rdb.gz" -type f | wc -l)
log_info "Retention cleanup completed. Remaining backups: $REMAINING_BACKUPS"

log_info "Redis backup process completed successfully"
