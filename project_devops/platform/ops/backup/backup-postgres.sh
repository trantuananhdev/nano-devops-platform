#!/bin/bash
# PostgreSQL Backup Script using pg_dump
# Creates a compressed SQL dump of the database.
#
# Configuration is managed via environment variables:
# - BACKUP_DIR:     Directory to store backups (default: /opt/platform/backups/postgres)
# - CONTAINER_NAME: Name of the PostgreSQL container (default: platform-postgres)
# - DB_NAME:        Database name to back up (default: platform_db)
# - DB_USER:        Database user (default: platform_user)
# - RETENTION_DAYS: How long to keep backups (default: 7)


set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/platform/backups/postgres}"
CONTAINER_NAME="${CONTAINER_NAME:-platform-postgres}"
DB_NAME="${DB_NAME:-platform_db}"
DB_USER="${DB_USER:-platform_user}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Define backup file name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[INFO] Starting PostgreSQL backup for database '$DB_NAME'..."
echo "[INFO] Backup file: $BACKUP_FILE"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[ERROR] Container '$CONTAINER_NAME' is not running. Aborting backup."
    exit 1
fi

# Execute pg_dump inside the container and compress the output
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"

# Verify that the backup file was created and is not empty
if [ -s "$BACKUP_FILE" ]; then
    echo "[INFO] Backup created successfully: $BACKUP_FILE"
    echo "[INFO] Size: $(du -h "$BACKUP_FILE" | awk '{print $1}')"
else
    echo "[ERROR] Backup failed. File is empty or was not created."
    # Clean up empty file
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Prune old backups
echo "[INFO] Pruning backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +$RETENTION_DAYS -print -delete

echo "[INFO] PostgreSQL backup process completed."
