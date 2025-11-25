# Backup and Restore Runbook

This runbook provides step-by-step procedures for performing backups and restores on the Nano DevOps Platform.

## Overview

Backups are automated via cron, but manual backups and restores may be needed for:
- Pre-deployment backups
- Point-in-time recovery
- Disaster recovery
- Data migration

## Prerequisites

- Access to platform VM
- Docker and Docker Compose installed
- Backup scripts available at `/opt/platform/scripts/`
- Sufficient disk space for backups

## Backup Procedures

### Manual Backup (All Services)

**When to Use**: Before major changes, deployments, or on-demand backup

**Procedure**:
```bash
# Navigate to scripts directory
cd /opt/platform/scripts

# Ensure scripts are executable
chmod +x backup-all.sh backup-postgres.sh backup-redis.sh

# Run all backups
./backup-all.sh
```

**Expected Output**:
```
[INFO] ==========================================
[INFO] Backup orchestration started: 2026-03-01 14:00:00
[INFO] ==========================================
[INFO] Running PostgreSQL backup...
[INFO] Starting PostgreSQL backup
[INFO] Backup completed successfully: /opt/platform/data/backup/postgres_20260301_140000.sql.gz (Size: 15M)
[INFO] Running Redis backup...
[INFO] Starting Redis backup
[INFO] Backup completed successfully: /opt/platform/data/backup/redis_20260301_140000.rdb.gz (Size: 2M)
[INFO] ==========================================
[INFO] Backup orchestration completed: 2026-03-01 14:00:15
[INFO] Duration: 15 seconds
[INFO] Status: SUCCESS - All backups completed
```

**Verification**:
```bash
# List recent backups
ls -lh /opt/platform/data/backup/

# Check backup logs
tail -f /opt/platform/logs/backup-all.log
```

### PostgreSQL Backup Only

**When to Use**: Database-specific backup needed

**Procedure**:
```bash
cd /opt/platform/scripts
./backup-postgres.sh
```

**Custom Configuration**:
```bash
# Custom backup directory
BACKUP_DIR=/custom/backup ./backup-postgres.sh

# Custom container name
POSTGRES_CONTAINER=my-postgres ./backup-postgres.sh
```

### Redis Backup Only

**When to Use**: Cache-specific backup needed

**Procedure**:
```bash
cd /opt/platform/scripts
./backup-redis.sh
```

**Custom Configuration**:
```bash
# Custom backup directory
BACKUP_DIR=/custom/backup ./backup-redis.sh
```

## Restore Procedures

### PostgreSQL Restore

**⚠️ WARNING**: Restore will overwrite existing database. Ensure backups are current.

**Procedure**:
```bash
# Step 1: List available backups
ls -lh /opt/platform/data/backup/postgres_*.sql.gz

# Step 2: Identify backup to restore
BACKUP_FILE=/opt/platform/data/backup/postgres_20260301_140000.sql.gz

# Step 3: Stop applications (optional, recommended)
docker compose -f /opt/platform/docker-compose.yml stop data-api user-api

# Step 4: Restore database
docker exec -i platform-postgres psql -U platform_user -d platform_db < <(gunzip -c "$BACKUP_FILE")

# Step 5: Verify restore
docker exec platform-postgres psql -U platform_user -d platform_db -c "SELECT COUNT(*) FROM information_schema.tables;"

# Step 6: Restart applications
docker compose -f /opt/platform/docker-compose.yml start data-api user-api

# Step 7: Verify application health
curl http://data-api.localhost/health
curl http://user-api.localhost/health
```

**Alternative: Using pg_restore** (for custom format):
```bash
# If backup was created with pg_dump -Fc (custom format)
gunzip -c "$BACKUP_FILE" | docker exec -i platform-postgres pg_restore -U platform_user -d platform_db --clean --if-exists
```

### Redis Restore

**⚠️ WARNING**: Restore will overwrite existing Redis data.

**Procedure**:
```bash
# Step 1: List available backups
ls -lh /opt/platform/data/backup/redis_*.rdb.gz

# Step 2: Identify backup to restore
BACKUP_FILE=/opt/platform/data/backup/redis_20260301_140000.rdb.gz

# Step 3: Stop Redis (required for restore)
docker compose -f /opt/platform/docker-compose.yml stop platform-redis

# Step 4: Get Redis data directory
REDIS_DATA_DIR=$(docker volume inspect platform_redis-data --format '{{.Mountpoint}}')

# Step 5: Restore backup
gunzip -c "$BACKUP_FILE" > "${REDIS_DATA_DIR}/dump.rdb"

# Step 6: Set correct permissions
chown 999:999 "${REDIS_DATA_DIR}/dump.rdb"

# Step 7: Start Redis
docker compose -f /opt/platform/docker-compose.yml start platform-redis

# Step 8: Verify restore
docker exec platform-redis redis-cli DBSIZE
```

## Backup Verification

### Verify Backup Integrity

**PostgreSQL Backup**:
```bash
# Test backup can be read
gunzip -c /opt/platform/data/backup/postgres_*.sql.gz | head -20

# Check backup size (should be > 0)
ls -lh /opt/platform/data/backup/postgres_*.sql.gz
```

**Redis Backup**:
```bash
# Check backup size (should be > 0)
ls -lh /opt/platform/data/backup/redis_*.rdb.gz

# Test backup can be decompressed
gunzip -t /opt/platform/data/backup/redis_*.rdb.gz
```

### Verify Backup Age

**Check Backup Freshness**:
```bash
# List backups with timestamps
ls -lht /opt/platform/data/backup/ | head -10

# Check if backup exists from last 24 hours
find /opt/platform/data/backup -name "postgres_*.sql.gz" -mtime -1
find /opt/platform/data/backup -name "redis_*.rdb.gz" -mtime -1
```

## Backup Management

### List Backups

```bash
# All PostgreSQL backups
ls -lh /opt/platform/data/backup/postgres_*.sql.gz

# All Redis backups
ls -lh /opt/platform/data/backup/redis_*.rdb.gz

# All backups sorted by date
ls -lht /opt/platform/data/backup/
```

### Clean Up Old Backups

**Automatic Cleanup**: Backups older than retention period are automatically deleted by backup scripts.

**Manual Cleanup**:
```bash
# Remove backups older than 7 days
find /opt/platform/data/backup -name "postgres_*.sql.gz" -mtime +7 -delete
find /opt/platform/data/backup -name "redis_*.rdb.gz" -mtime +7 -delete
```

### Backup Storage Management

**Check Backup Disk Usage**:
```bash
# Check backup directory size
du -sh /opt/platform/data/backup/

# Check available disk space
df -h /opt/platform/data/backup/
```

**Move Backups to External Storage** (if needed):
```bash
# Copy backups to external location
rsync -av /opt/platform/data/backup/ /external/backup/

# Or use tar for archive
tar -czf backups-$(date +%Y%m%d).tar.gz /opt/platform/data/backup/
```

## Troubleshooting

### Backup Fails: Container Not Running

**Error**: `PostgreSQL container 'platform-postgres' is not running`

**Solution**:
```bash
# Check container status
docker ps -a | grep postgres

# Start container if stopped
docker compose -f /opt/platform/docker-compose.yml start platform-postgres

# Wait for container to be healthy
docker compose -f /opt/platform/docker-compose.yml ps
```

### Backup Fails: Permission Denied

**Error**: `Permission denied` when writing backup

**Solution**:
```bash
# Check backup directory permissions
ls -ld /opt/platform/data/backup

# Fix permissions if needed
sudo chown -R $USER:$USER /opt/platform/data/backup
chmod 755 /opt/platform/data/backup
```

### Backup Fails: Disk Space

**Error**: `No space left on device`

**Solution**:
```bash
# Check disk space
df -h /opt/platform/data/backup

# Clean up old backups
find /opt/platform/data/backup -name "*.gz" -mtime +7 -delete

# Or reduce retention period
RETENTION_DAYS=3 ./backup-all.sh
```

### Restore Fails: Backup File Corrupted

**Error**: `gzip: invalid compressed data`

**Solution**:
```bash
# Test backup integrity
gunzip -t /opt/platform/data/backup/postgres_*.sql.gz

# If corrupted, use previous backup
ls -lht /opt/platform/data/backup/postgres_*.sql.gz | tail -1
```

### Restore Fails: Database Connection

**Error**: `could not connect to server`

**Solution**:
```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs platform-postgres

# Verify network connectivity
docker exec platform-postgres pg_isready -U platform_user
```

## Best Practices

1. **Regular Backups**: Ensure automated backups are running (check cron)
2. **Pre-Deployment**: Always backup before major deployments
3. **Verify Backups**: Regularly verify backup integrity
4. **Test Restores**: Periodically test restore procedures
5. **Document Restores**: Document all restore operations
6. **Monitor Storage**: Monitor backup disk usage
7. **External Storage**: Consider syncing backups to external storage

## Related Documentation

- Backup Automation: `docs-devops/09-disaster-recovery/backup-automation.md`
- Backup Strategy: `docs-devops/09-disaster-recovery/backup-restore-strategy.md`
- Incident Response: `incident-response.md`
