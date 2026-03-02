# Maintenance Runbook

This runbook provides procedures for regular maintenance tasks on the Nano DevOps Platform.

## Overview

Regular maintenance ensures platform health, performance, and reliability. This runbook covers:
- Log rotation and cleanup
- Database maintenance
- Monitoring maintenance
- System updates
- Resource cleanup

## Prerequisites

- Access to platform VM
- Docker and Docker Compose installed
- Appropriate permissions for maintenance tasks

## Log Management

### Log Rotation

**Current Log Locations**:
- Application logs: Container logs (via Docker)
- Backup logs: `/opt/platform/logs/backup-*.log`
- System logs: `/var/log/` (host system)

**Manual Log Cleanup**:
```bash
# Clean old backup logs (older than 30 days)
find /opt/platform/logs -name "*.log" -mtime +30 -delete

# Rotate large log files
logrotate /etc/logrotate.conf
```

**Docker Log Cleanup**:
```bash
# Clean Docker logs (older than 7 days)
docker system prune --logs --until 168h

# Clean unused Docker resources
docker system prune -a --volumes
```

### Log Analysis

**Check Log Sizes**:
```bash
# Check log directory size
du -sh /opt/platform/logs/

# Find large log files
find /opt/platform/logs -type f -size +100M

# Check container log sizes
docker ps --format "table {{.Names}}\t{{.Size}}"
```

## Database Maintenance

### PostgreSQL Maintenance

**Vacuum Database**:
```bash
# Run VACUUM ANALYZE
docker exec platform-postgres psql -U platform_user -d platform_db -c "VACUUM ANALYZE;"

# Check database size before/after
docker exec platform-postgres psql -U platform_user -d platform_db -c "SELECT pg_size_pretty(pg_database_size('platform_db'));"
```

**Check Database Health**:
```bash
# Check connection count
docker exec platform-postgres psql -U platform_user -d platform_db -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker exec platform-postgres psql -U platform_user -d platform_db -c "SELECT pg_size_pretty(pg_database_size('platform_db'));"

# Check table sizes
docker exec platform-postgres psql -U platform_user -d platform_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"
```

**Reindex Database** (if needed):
```bash
# Reindex all tables
docker exec platform-postgres psql -U platform_user -d platform_db -c "REINDEX DATABASE platform_db;"
```

### Redis Maintenance

**Check Redis Memory**:
```bash
# Check memory usage
docker exec platform-redis redis-cli INFO memory

# Check key count
docker exec platform-redis redis-cli DBSIZE

# Check largest keys
docker exec platform-redis redis-cli --bigkeys
```

**Flush Redis** (if needed, ⚠️ destructive):
```bash
# Flush all data (use with caution)
docker exec platform-redis redis-cli FLUSHALL
```

## Monitoring Maintenance

### Prometheus Maintenance

**Check Prometheus Storage**:
```bash
# Check Prometheus data directory size
du -sh /opt/platform/data/prometheus/

# Check series count
curl http://prometheus.localhost:9090/api/v1/status/tsdb | jq '.data.stats.numSeries'
```

**Prometheus Retention**:
- Current retention: 7 days (configured in docker-compose.yml)
- To adjust: Modify `--storage.tsdb.retention.time` in docker-compose.yml

**Clean Prometheus Data** (if needed):
```bash
# Stop Prometheus
docker compose -f /opt/platform/docker-compose.yml stop platform-prometheus

# Remove old data (older than retention)
# Prometheus handles this automatically, but manual cleanup possible:
rm -rf /opt/platform/data/prometheus/*

# Start Prometheus
docker compose -f /opt/platform/docker-compose.yml start platform-prometheus
```

### Grafana Maintenance

**Backup Grafana Configuration**:
```bash
# Backup dashboards and provisioning
tar -czf grafana-backup-$(date +%Y%m%d).tar.gz \
  /opt/platform/monitoring/grafana/dashboards \
  /opt/platform/monitoring/grafana/provisioning
```

**Clean Grafana Data** (if needed):
```bash
# Grafana data is in volume, usually doesn't need cleanup
# Check size
du -sh /opt/platform/data/grafana/
```

### Loki Maintenance

**Check Loki Storage**:
```bash
# Check Loki data directory size
du -sh /opt/platform/data/loki/

# Loki retention: 7 days (configured in loki-config.yml)
```

## System Updates

### Container Image Updates

**Update Base Images**:
```bash
# Pull latest images
docker compose -f /opt/platform/docker-compose.yml pull

# Review changes
docker compose -f /opt/platform/docker-compose.yml config

# Update services (one at a time, with health checks)
docker compose -f /opt/platform/docker-compose.yml up -d --no-deps <service-name>
```

**Update Application Images**:
```bash
# Use deployment script for application services
export SERVICE_NAME=health-api
export IMAGE_TAG=new-tag
./project_devops/scripts/deploy.sh
```

### System Package Updates

**Alpine Linux Updates**:
```bash
# Update package index
apk update

# Upgrade packages
apk upgrade

# Reboot if kernel updated
reboot
```

## Resource Cleanup

### Docker Cleanup

**Remove Unused Resources**:
```bash
# Remove unused containers, networks, images
docker system prune

# Remove unused volumes (⚠️ may remove data)
docker volume prune

# Full cleanup (⚠️ removes all unused resources)
docker system prune -a --volumes
```

**Check Docker Disk Usage**:
```bash
# Check Docker disk usage
docker system df

# Check per-container usage
docker stats --no-stream
```

### Disk Space Management

**Check Disk Usage**:
```bash
# Check overall disk usage
df -h

# Check directory sizes
du -sh /opt/platform/data/*

# Find large files
find /opt/platform -type f -size +100M
```

**Clean Up Old Data**:
```bash
# Clean old backups (if retention policy allows)
find /opt/platform/data/backup -name "*.gz" -mtime +7 -delete

# Clean old logs
find /opt/platform/logs -name "*.log" -mtime +30 -delete
```

## Regular Maintenance Schedule

### Daily

- [ ] Check backup logs for failures
- [ ] Monitor disk usage
- [ ] Review critical alerts

### Weekly

- [ ] Review log sizes and cleanup if needed
- [ ] Check database health
- [ ] Review resource usage trends
- [ ] Verify monitoring stack health

### Monthly

- [ ] Database VACUUM ANALYZE
- [ ] Review and optimize resource allocation
- [ ] Update container images (if needed)
- [ ] Review and clean up old backups
- [ ] System package updates

### Quarterly

- [ ] Full system health review
- [ ] Review and update documentation
- [ ] Test restore procedures
- [ ] Review security updates

## Maintenance Checklist

### Pre-Maintenance

- [ ] Review maintenance schedule
- [ ] Backup critical data
- [ ] Notify stakeholders (if maintenance affects availability)
- [ ] Prepare rollback plan

### During Maintenance

- [ ] Follow runbook procedures
- [ ] Monitor system health
- [ ] Document actions taken
- [ ] Verify changes

### Post-Maintenance

- [ ] Verify system health
- [ ] Check monitoring and alerts
- [ ] Document maintenance completion
- [ ] Update maintenance logs

## Troubleshooting

### Maintenance Causes Issues

**Symptoms**: System issues after maintenance

**Solution**:
1. Review maintenance logs
2. Check what changed
3. Rollback changes if needed
4. Document issue and resolution

### Disk Space Issues

**Symptoms**: Disk full, services failing

**Solution**:
1. Check disk usage: `df -h`
2. Identify large directories: `du -sh /opt/platform/data/*`
3. Clean up old data (backups, logs)
4. Consider increasing disk size if needed

### Database Performance Issues

**Symptoms**: Slow queries, high connection count

**Solution**:
1. Run VACUUM ANALYZE
2. Check for long-running queries
3. Review connection pool settings
4. Consider database optimization

## Related Documentation

- Resource Optimization: `docs-devops/04-environment-and-infrastructure/resource-optimization.md`
- Backup Procedures: `backup-restore.md`
- Incident Response: `incident-response.md`
