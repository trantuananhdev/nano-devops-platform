# Troubleshooting Runbook

This runbook provides diagnostic procedures and solutions for common platform issues.

## Overview

This runbook covers troubleshooting procedures for:
- Service issues
- Database problems
- Network connectivity
- Resource exhaustion
- Monitoring issues

## Diagnostic Procedures

### Service Health Check

**Quick Health Check**:
```bash
# Check all services status
docker compose -f /opt/platform/docker-compose.yml ps

# Check specific service
docker ps | grep <service-name>

# Check service health status
docker inspect --format='{{.State.Health.Status}}' <service-name>
```

**Service Logs**:
```bash
# View service logs
docker logs <service-name>

# Follow logs in real-time
docker logs -f <service-name>

# View last 100 lines
docker logs --tail 100 <service-name>
```

### Network Connectivity

**Check Service Connectivity**:
```bash
# Test service endpoint
curl http://<service-name>.localhost/health

# Test from within container
docker exec <service-name> wget -qO- http://localhost:8080/health

# Check DNS resolution
docker exec <service-name> nslookup platform-postgres
```

**Check Network Configuration**:
```bash
# List networks
docker network ls

# Inspect platform network
docker network inspect platform-network

# Check service network membership
docker inspect <service-name> | grep -A 10 Networks
```

### Resource Usage

**Check Memory Usage**:
```bash
# Overall memory usage
free -h

# Per-container memory
docker stats --no-stream

# Container memory details
docker stats <service-name>
```

**Check CPU Usage**:
```bash
# Overall CPU usage
top

# Per-container CPU
docker stats --no-stream

# Container CPU details
docker stats <service-name>
```

**Check Disk Usage**:
```bash
# Overall disk usage
df -h

# Directory sizes
du -sh /opt/platform/data/*

# Container disk usage
docker system df
```

## Common Issues and Solutions

### Issue: Service Not Starting

**Symptoms**: Service container exits immediately or fails to start

**Diagnosis**:
```bash
# Check container status
docker ps -a | grep <service-name>

# Check logs
docker logs <service-name>

# Check exit code
docker inspect --format='{{.State.ExitCode}}' <service-name>
```

**Common Causes**:
- Configuration error
- Missing dependencies
- Resource constraints
- Port conflicts

**Solutions**:
1. Check logs for error messages
2. Verify configuration in docker-compose.yml
3. Check resource limits
4. Verify dependencies are running
5. Check for port conflicts: `netstat -tulpn | grep <port>`

### Issue: Service Unhealthy

**Symptoms**: Service running but health check failing

**Diagnosis**:
```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' <service-name>

# Check health check logs
docker inspect <service-name> | grep -A 20 Health

# Test health endpoint manually
curl http://<service-name>.localhost/health
```

**Common Causes**:
- Health endpoint not responding
- Service dependencies unavailable
- Resource constraints
- Application errors

**Solutions**:
1. Check service logs for errors
2. Verify health endpoint responds
3. Check service dependencies (database, cache)
4. Verify resource availability
5. Review health check configuration

### Issue: Database Connection Failed

**Symptoms**: Applications cannot connect to PostgreSQL

**Diagnosis**:
```bash
# Check PostgreSQL status
docker ps | grep postgres

# Check PostgreSQL logs
docker logs platform-postgres

# Test connection
docker exec platform-postgres pg_isready -U platform_user

# Test from application container
docker exec <app-service> psql -h platform-postgres -U platform_user -d platform_db -c "SELECT 1;"
```

**Common Causes**:
- PostgreSQL not running
- Network connectivity issue
- Authentication failure
- Database doesn't exist

**Solutions**:
1. Start PostgreSQL if stopped
2. Verify network connectivity
3. Check credentials/secrets
4. Verify database exists
5. Check PostgreSQL logs for errors

### Issue: High Memory Usage

**Symptoms**: Memory usage alerts, services being killed

**Diagnosis**:
```bash
# Check total memory usage
free -h

# Check per-service usage
docker stats --no-stream

# Check memory limits
docker inspect <service-name> | grep -A 5 Memory
```

**Common Causes**:
- Memory leak in application
- Too many services
- Insufficient limits
- Resource pressure

**Solutions**:
1. Identify high-usage services
2. Check for memory leaks (growing usage over time)
3. Optimize resource limits
4. Restart problematic services
5. Consider resource optimization

### Issue: Disk Full

**Symptoms**: Disk usage alerts, write failures

**Diagnosis**:
```bash
# Check disk usage
df -h

# Find large directories
du -sh /opt/platform/data/* | sort -h

# Find large files
find /opt/platform -type f -size +100M
```

**Common Causes**:
- Too many backups
- Large log files
- Database growth
- Prometheus data growth

**Solutions**:
1. Clean old backups
2. Rotate/clean logs
3. Optimize database (VACUUM)
4. Adjust Prometheus retention
5. Clean Docker resources

### Issue: Service Not Accessible via Traefik

**Symptoms**: Cannot access service at `http://<service>.localhost`

**Diagnosis**:
```bash
# Check Traefik status
docker ps | grep traefik

# Check Traefik logs
docker logs platform-traefik

# Check Traefik dashboard
curl http://localhost:8080/api/http/routers

# Verify service labels
docker inspect <service-name> | grep -A 10 Labels
```

**Common Causes**:
- Traefik not running
- Missing Traefik labels
- Network configuration issue
- DNS/hosts file issue

**Solutions**:
1. Start Traefik if stopped
2. Verify Traefik labels in docker-compose.yml
3. Check service is on platform-network
4. Verify /etc/hosts entry
5. Check Traefik dashboard for routes

### Issue: Metrics Not Appearing

**Symptoms**: Prometheus not scraping metrics, Grafana shows no data

**Diagnosis**:
```bash
# Check Prometheus status
docker ps | grep prometheus

# Check Prometheus targets
curl http://prometheus.localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'

# Test metrics endpoint
curl http://<service-name>:8080/metrics

# Check Prometheus config
docker exec platform-prometheus cat /etc/prometheus/prometheus.yml
```

**Common Causes**:
- Prometheus not running
- Scrape config missing
- Network connectivity issue
- Metrics endpoint not responding

**Solutions**:
1. Start Prometheus if stopped
2. Verify scrape config includes service
3. Check network connectivity
4. Verify metrics endpoint responds
5. Check Prometheus logs

## Diagnostic Tools

### Container Inspection

```bash
# Inspect container configuration
docker inspect <service-name>

# Check container resources
docker stats <service-name>

# Check container processes
docker top <service-name>

# Check container environment
docker exec <service-name> env
```

### Log Analysis

```bash
# Search logs for errors
docker logs <service-name> 2>&1 | grep -i error

# Search logs for specific pattern
docker logs <service-name> 2>&1 | grep "pattern"

# Export logs to file
docker logs <service-name> > service.log
```

### Network Diagnostics

```bash
# Test connectivity
docker exec <service-name> ping platform-postgres

# Check DNS resolution
docker exec <service-name> nslookup platform-postgres

# Test port connectivity
docker exec <service-name> nc -zv platform-postgres 5432
```

### Database Diagnostics

```bash
# PostgreSQL connection test
docker exec platform-postgres psql -U platform_user -d platform_db -c "SELECT version();"

# Check active connections
docker exec platform-postgres psql -U platform_user -d platform_db -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker exec platform-postgres psql -U platform_user -d platform_db -c "SELECT pg_size_pretty(pg_database_size('platform_db'));"
```

## Escalation Procedures

### When to Escalate

- Issue persists after troubleshooting
- Data loss or corruption
- Security incident
- System-wide outage
- Unknown root cause

### Information to Collect

Before escalating, collect:
- Service logs
- Error messages
- Metrics snapshots
- Configuration files
- Steps taken
- Timeline of events

### Escalation Steps

1. Document issue and troubleshooting steps
2. Collect diagnostic information
3. Create incident report
4. Contact platform maintainers
5. Provide all collected information

## Related Documentation

- Incident Response: `incident-response.md`
- Service Management: `service-management.md`
- Maintenance: `maintenance.md`
- Monitoring Architecture: `docs-devops/07-observability/monitoring-architecture.md`
