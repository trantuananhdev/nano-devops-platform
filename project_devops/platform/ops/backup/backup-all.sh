#!/bin/bash
# Backup Orchestration Script for Nano DevOps Platform
# Runs backups for PostgreSQL and Redis, verifies success, and logs results.
#
# Configuration is managed via environment variables:
# - LOG_FILE:        Path to the log file (default: /opt/platform/logs/backup-all.log)
# - BACKUP_POSTGRES: Set to "true" or "false" to enable/disable PostgreSQL backup (default: true)
# - BACKUP_REDIS:    Set to "true" or "false" to enable/disable Redis backup (default: true)


set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${LOG_FILE:-/opt/platform/logs/backup-all.log}"
BACKUP_POSTGRES="${BACKUP_POSTGRES:-true}"
BACKUP_REDIS="${BACKUP_REDIS:-true}"

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

send_notification() {
    # Placeholder for notification logic (e.g., webhook, email)
    log_warn "Notification system not configured. Message: $1"
}

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

START_TIME=$(date +%s)
TIMESTAMP=$(date +%Y-%m-%d\ %H:%M:%S)

log_info "=========================================="
log_info "Backup orchestration started: $TIMESTAMP"
log_info "=========================================="

log_info "=========================================="

# --- Locking Mechanism ---
trap 'rm -f "$LOCK_FILE"' EXIT
if [ -f "$LOCK_FILE" ]; then
    log_error "Another operation is already in progress. Lock file exists: $LOCK_FILE"
    exit 1
else
    log_info "Acquiring backup lock..."
    touch "$LOCK_FILE"
fi
# --- End Locking Mechanism ---

EXIT_CODE=0

# Run PostgreSQL backup
if [ "$BACKUP_POSTGRES" = "true" ]; then
    log_info "Running PostgreSQL backup..."
    if ! output=$(bash "${SCRIPT_DIR}/backup-postgres.sh" 2>&1); then
        log_error "PostgreSQL backup failed. See details below:"
        log_error "$output"
        send_notification "PostgreSQL backup failed on $(hostname)"
        EXIT_CODE=1
    else
        log_info "PostgreSQL backup completed successfully"
        log_info "$output"
    fi
else
    log_info "PostgreSQL backup skipped (BACKUP_POSTGRES=false)"
fi

# Run Redis backup
if [ "$BACKUP_REDIS" = "true" ]; then
    log_info "Running Redis backup..."
    if ! output=$(bash "${SCRIPT_DIR}/backup-redis.sh" 2>&1); then
        log_error "Redis backup failed. See details below:"
        log_error "$output"
        send_notification "Redis backup failed on $(hostname)"
        EXIT_CODE=1
    else
        log_info "Redis backup completed successfully"
        log_info "$output"
    fi
else
    log_info "Redis backup skipped (BACKUP_REDIS=false)"
fi

# Summary
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
TIMESTAMP=$(date +%Y-%m-%d\ %H:%M:%S)

log_info "=========================================="
log_info "Backup orchestration completed: $TIMESTAMP"
log_info "Duration: ${DURATION} seconds"

if [ $EXIT_CODE -eq 0 ]; then
    log_info "Status: SUCCESS - All backups completed"
else
    log_error "Status: FAILURE - One or more backups failed"
fi
log_info "=========================================="

exit $EXIT_CODE
