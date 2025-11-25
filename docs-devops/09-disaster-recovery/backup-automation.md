# Backup Automation

This document describes the automated backup system for PostgreSQL and Redis.

## Overview

Backups are performed automatically via cron-scheduled scripts that create compressed backups of PostgreSQL databases and Redis data.

## Backup Scripts

### PostgreSQL Backup (`backup-postgres.sh`)

Creates logical backups of PostgreSQL databases using `pg_dump`.

**Features**:
- Uses `pg_dump` for logical backup
- Compresses backups with gzip
- Automatic retention policy (default: 7 days)
- Logs all operations
- Verifies backup success

**Usage**:
```bash
# Use defaults (container: platform-postgres, database: platform_db)
./backup-postgres.sh

# Custom configuration
BACKUP_DIR=/custom/path POSTGRES_CONTAINER=my-postgres ./backup-postgres.sh
```

**Configuration**:
- `BACKUP_DIR`: Backup storage directory (default: `/opt/platform/data/backup`)
- `POSTGRES_CONTAINER`: PostgreSQL container name (default: `platform-postgres`)
- `POSTGRES_DB`: Database name (default: `platform_db`)
- `POSTGRES_USER`: Database user (default: `platform_user`)
- `RETENTION_DAYS`: Days to keep backups (default: `7`)
- `LOG_FILE`: Log file path (default: `/opt/platform/logs/backup-postgres.log`)

**Backup Format**:
- Filename: `postgres_YYYYMMDD_HHMMSS.sql.gz`
- Location: `$BACKUP_DIR/postgres_*.sql.gz`

### Redis Backup (`backup-redis.sh`)

Creates backups of Redis data by copying RDB snapshots or AOF files.

**Features**:
- Triggers Redis SAVE command
- Copies RDB file (`dump.rdb`) or AOF file (`appendonly.aof`)
- Compresses backups with gzip
- Automatic retention policy (default: 7 days)
- Logs all operations
- Verifies backup success

**Usage**:
```bash
# Use defaults (container: platform-redis)
./backup-redis.sh

# Custom configuration
BACKUP_DIR=/custom/path REDIS_CONTAINER=my-redis ./backup-redis.sh
```

**Configuration**:
- `BACKUP_DIR`: Backup storage directory (default: `/opt/platform/data/backup`)
- `REDIS_CONTAINER`: Redis container name (default: `platform-redis`)
- `RETENTION_DAYS`: Days to keep backups (default: `7`)
- `LOG_FILE`: Log file path (default: `/opt/platform/logs/backup-redis.log`)

**Backup Format**:
- Filename: `redis_YYYYMMDD_HHMMSS.rdb.gz`
- Location: `$BACKUP_DIR/redis_*.rdb.gz`

### Backup Orchestration (`backup-all.sh`)

Runs all backup scripts and provides summary.

**Features**:
- Runs PostgreSQL and Redis backups sequentially
- Provides summary of backup status
- Logs total duration
- Exits with error code if any backup fails

**Usage**:
```bash
# Run all backups
./backup-all.sh

# Skip PostgreSQL backup
BACKUP_POSTGRES=false ./backup-all.sh

# Skip Redis backup
BACKUP_REDIS=false ./backup-all.sh
```

**Configuration**:
- `BACKUP_POSTGRES`: Enable PostgreSQL backup (default: `true`)
- `BACKUP_REDIS`: Enable Redis backup (default: `true`)
- `LOG_FILE`: Log file path (default: `/opt/platform/logs/backup-all.log`)

## Scheduling

### Cron Configuration

Add to crontab for daily backups at 2 AM:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/platform/scripts/backup-all.sh >> /opt/platform/logs/backup-cron.log 2>&1
```

### Systemd Timer (Alternative)

Create `/etc/systemd/system/platform-backup.service`:
```ini
[Unit]
Description=Platform Backup Service
After=docker.service

[Service]
Type=oneshot
ExecStart=/opt/platform/scripts/backup-all.sh
User=root
```

Create `/etc/systemd/system/platform-backup.timer`:
```ini
[Unit]
Description=Platform Backup Timer
Requires=platform-backup.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
systemctl enable platform-backup.timer
systemctl start platform-backup.timer
systemctl status platform-backup.timer
```

## Backup Storage

**Default Location**: `/opt/platform/data/backup`

**Directory Structure**:
```
/opt/platform/data/backup/
├── postgres_20260301_020000.sql.gz
├── postgres_20260302_020000.sql.gz
├── redis_20260301_020000.rdb.gz
└── redis_20260302_020000.rdb.gz
```

**Retention Policy**:
- Default: 7 days
- Configurable via `RETENTION_DAYS` environment variable
- Old backups automatically deleted by scripts

## Monitoring

### Backup Status Check

Check backup age and count:
```bash
# List recent backups
ls -lh /opt/platform/data/backup/

# Check backup age
find /opt/platform/data/backup -name "postgres_*.sql.gz" -mtime -1
find /opt/platform/data/backup -name "redis_*.rdb.gz" -mtime -1

# View backup logs
tail -f /opt/platform/logs/backup-all.log
tail -f /opt/platform/logs/backup-postgres.log
tail -f /opt/platform/logs/backup-redis.log
```

### Backup Verification

Verify backup integrity:
```bash
# Test PostgreSQL backup restore (dry-run)
gunzip -c /opt/platform/data/backup/postgres_*.sql.gz | head -20

# Check Redis backup size
ls -lh /opt/platform/data/backup/redis_*.rdb.gz
```

## Troubleshooting

### Backup Fails: Container Not Running
**Error**: `PostgreSQL container 'platform-postgres' is not running`
**Solution**: Ensure containers are running: `docker compose -f /opt/platform/docker-compose.yml ps`

### Backup Fails: Permission Denied
**Error**: `Permission denied` when writing backup
**Solution**: Ensure backup directory has write permissions:
```bash
sudo mkdir -p /opt/platform/data/backup
sudo chown -R $USER:$USER /opt/platform/data/backup
```

### Backup Fails: Disk Space
**Error**: `No space left on device`
**Solution**: Check disk space and adjust retention policy:
```bash
df -h /opt/platform/data/backup
# Reduce RETENTION_DAYS if needed
```

### Redis Backup Uses AOF Instead of RDB
**Warning**: `Using AOF file instead of RDB (Redis configured with appendonly yes)`
**Note**: This is expected if Redis is configured with `appendonly yes`. The backup will include the AOF file.

## Best Practices

1. **Test Restores Regularly**: Periodically test restore procedures to ensure backups are valid
2. **Monitor Backup Logs**: Check logs regularly for backup failures
3. **External Backup Storage**: Consider syncing backups to external storage (S3, NFS, etc.)
4. **Backup Before Major Changes**: Run manual backup before deployments or schema changes
5. **Verify Backup Size**: Monitor backup sizes for anomalies (too small may indicate failure)

## Manual Backup

Run backups manually:
```bash
# Single backup
/opt/platform/scripts/backup-postgres.sh
/opt/platform/scripts/backup-redis.sh

# All backups
/opt/platform/scripts/backup-all.sh
```

## Integration with Monitoring

Backup scripts log to files that can be monitored:
- Log files: `/opt/platform/logs/backup-*.log`
- Backup directory: `/opt/platform/data/backup/`

Consider adding Prometheus metrics or alerts for:
- Backup age (alert if no backup in 24 hours)
- Backup failures (alert on backup script exit code != 0)
- Backup disk usage (alert if backup directory full)
