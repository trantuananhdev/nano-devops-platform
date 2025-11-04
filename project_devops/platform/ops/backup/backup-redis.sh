#!/bin/bash
# Redis Backup Script using RDB snapshot
# Copies the RDB file from the container to the host.

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/platform/backups/redis}"
CONTAINER_NAME="${CONTAINER_NAME:-platform-redis}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Define backup file name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dump_${TIMESTAMP}.rdb"

echo "[INFO] Starting Redis backup..."

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[ERROR] Container '$CONTAINER_NAME' is not running. Aborting backup."
    exit 1
fi

# Tell Redis to save the database to disk
echo "[INFO] Requesting Redis to save RDB snapshot..."
docker exec "$CONTAINER_NAME" redis-cli SAVE

# Copy the RDB file from the container
echo "[INFO] Copying RDB file from container..."
docker cp "$CONTAINER_NAME:/data/dump.rdb" "$BACKUP_FILE"

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
find "$BACKUP_DIR" -type f -name "*.rdb" -mtime +$RETENTION_DAYS -print -delete

echo "[INFO] Redis backup process completed."
