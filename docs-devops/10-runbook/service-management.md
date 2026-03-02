# Service Management Runbook

This runbook provides procedures for managing services on the Nano DevOps Platform.

## Overview

Service management includes:
- Starting and stopping services
- Restarting services
- Checking service status
- Updating service configuration
- Service health verification

## Prerequisites

- Access to platform VM
- Docker and Docker Compose installed
- Appropriate permissions

## Service Lifecycle Operations

### Start Service

**Start Single Service**:
```bash
# Start specific service
docker compose -f /opt/platform/docker-compose.yml start <service-name>

# Example: Start health-api
docker compose -f /opt/platform/docker-compose.yml start health-api
```

**Start All Services**:
```bash
# Start all services
docker compose -f /opt/platform/docker-compose.yml start

# Or use up command (creates if not exists)
docker compose -f /opt/platform/docker-compose.yml up -d
```

**Start Service with Dependencies**:
```bash
# Start service and dependencies
docker compose -f /opt/platform/docker-compose.yml up -d <service-name>

# Example: Start data-api (will start PostgreSQL if needed)
docker compose -f /opt/platform/docker-compose.yml up -d data-api
```

### Stop Service

**Stop Single Service**:
```bash
# Stop specific service
docker compose -f /opt/platform/docker-compose.yml stop <service-name>

# Example: Stop health-api
docker compose -f /opt/platform/docker-compose.yml stop health-api
```

**Stop All Services**:
```bash
# Stop all services
docker compose -f /opt/platform/docker-compose.yml stop
```

**Stop Service Gracefully**:
```bash
# Stop with timeout (default 10s)
docker compose -f /opt/platform/docker-compose.yml stop -t 30 <service-name>
```

### Restart Service

**Restart Single Service**:
```bash
# Restart specific service
docker compose -f /opt/platform/docker-compose.yml restart <service-name>

# Example: Restart health-api
docker compose -f /opt/platform/docker-compose.yml restart health-api
```

**Restart All Services**:
```bash
# Restart all services
docker compose -f /opt/platform/docker-compose.yml restart
```

**Restart Service with Recreate**:
```bash
# Recreate container (useful after config changes)
docker compose -f /opt/platform/docker-compose.yml up -d --force-recreate <service-name>
```

### Remove Service

**Remove Service Container**:
```bash
# Stop and remove container
docker compose -f /opt/platform/docker-compose.yml rm -f <service-name>

# Remove with volumes (⚠️ deletes data)
docker compose -f /opt/platform/docker-compose.yml rm -f -v <service-name>
```

## Service Status Checks

### Check Service Status

**List All Services**:
```bash
# List all services with status
docker compose -f /opt/platform/docker-compose.yml ps

# Detailed status
docker compose -f /opt/platform/docker-compose.yml ps -a
```

**Check Specific Service**:
```bash
# Check service status
docker ps | grep <service-name>

# Check health status
docker inspect --format='{{.State.Health.Status}}' <service-name>

# Check service details
docker inspect <service-name>
```

### Check Service Health

**Health Endpoint Check**:
```bash
# Check health endpoint
curl http://<service-name>.localhost/health

# Check from within container
docker exec <service-name> wget -qO- http://localhost:8080/health
```

**Health Check Status**:
```bash
# Check Docker health check status
docker inspect --format='{{json .State.Health}}' <service-name> | jq

# Check health check logs
docker inspect <service-name> | grep -A 20 Health
```

### Check Service Logs

**View Logs**:
```bash
# View logs
docker logs <service-name>

# Follow logs
docker logs -f <service-name>

# Last N lines
docker logs --tail 100 <service-name>

# Logs since timestamp
docker logs --since 2026-03-01T10:00:00 <service-name>
```

## Service Configuration Updates

### Update Service Configuration

**⚠️ IMPORTANT**: Configuration changes must be made in Git (docker-compose.yml), not directly in running containers.

**Procedure**:
```bash
# Step 1: Update docker-compose.yml in Git
# Edit: project_devops/platform/docker-compose.yml

# Step 2: Pull changes to VM
cd /opt/platform
git pull

# Step 3: Validate configuration
docker compose -f docker-compose.yml config

# Step 4: Apply changes
docker compose -f docker-compose.yml up -d <service-name>

# Step 5: Verify service
docker compose -f docker-compose.yml ps <service-name>
```

### Update Environment Variables

**For Application Services**:
```bash
# Update in docker-compose.yml (GitOps)
# Then redeploy service
export SERVICE_NAME=<service-name>
export IMAGE_TAG=<current-tag>
./project_devops/scripts/deploy.sh
```

**For Infrastructure Services**:
```bash
# Update in docker-compose.yml (GitOps)
# Then recreate service
docker compose -f /opt/platform/docker-compose.yml up -d --force-recreate <service-name>
```

### Update Resource Limits

**Procedure**:
```bash
# Step 1: Update limits in docker-compose.yml (GitOps)

# Step 2: Apply changes
docker compose -f /opt/platform/docker-compose.yml up -d <service-name>

# Step 3: Verify limits
docker inspect <service-name> | grep -A 5 Memory
```

## Service Health Verification

### Post-Start Verification

**Checklist**:
```bash
# 1. Service is running
docker ps | grep <service-name>

# 2. Service is healthy
docker inspect --format='{{.State.Health.Status}}' <service-name>

# 3. Health endpoint responds
curl -f http://<service-name>.localhost/health

# 4. Metrics endpoint responds
curl -f http://<service-name>.localhost/metrics

# 5. Service accessible via Traefik
curl -f http://<service-name>.localhost/health
```

### Smoke Tests

**Run Smoke Test Script**:
```bash
# Use service-specific smoke test
./project_devops/scripts/smoke-test-<service-name>.sh

# Example
./project_devops/scripts/smoke-test-health-api.sh
```

**Manual Smoke Test**:
```bash
# Health check
curl -f http://<service-name>.localhost/health

# Metrics check
curl -f http://<service-name>.localhost/metrics

# Functional test (service-specific)
# Example for data-api:
curl -X POST http://data-api.localhost/data -H "Content-Type: application/json" -d '{"key":"test","value":"test"}'
curl http://data-api.localhost/data/test
```

## Service Dependencies

### Check Dependencies

**List Service Dependencies**:
```bash
# Check depends_on in docker-compose.yml
grep -A 5 "depends_on:" project_devops/platform/docker-compose.yml

# Check actual dependencies
docker inspect <service-name> | grep -A 10 DependsOn
```

### Start Dependencies First

**Start Order**:
1. Infrastructure services (PostgreSQL, Redis)
2. Monitoring services (Prometheus, Grafana, Loki)
3. Application services

**Example**:
```bash
# Start infrastructure
docker compose -f /opt/platform/docker-compose.yml up -d platform-postgres platform-redis

# Wait for health
docker compose -f /opt/platform/docker-compose.yml ps

# Start applications
docker compose -f /opt/platform/docker-compose.yml up -d health-api data-api
```

## Service Scaling

### Current Limitations

- Single-node platform
- No horizontal scaling
- Resource-constrained (6GB RAM)

### Vertical Scaling

**Adjust Resource Limits**:
```bash
# Update memory limits in docker-compose.yml
# Then recreate service
docker compose -f /opt/platform/docker-compose.yml up -d --force-recreate <service-name>
```

**⚠️ Note**: Total resources must stay within 6GB constraint.

## Service Monitoring

### Check Service Metrics

**Prometheus Metrics**:
```bash
# View service metrics
curl http://<service-name>:8080/metrics

# Check Prometheus targets
curl http://prometheus.localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="<service-name>")'
```

**Grafana Dashboards**:
- Navigate to: `http://grafana.localhost:3000`
- View service-specific dashboard
- Check service health and performance

### Service Alerts

**Check Active Alerts**:
```bash
# View Prometheus alerts
curl http://prometheus.localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.service=="<service-name>")'
```

**Common Service Alerts**:
- ServiceDown: Service not running
- HighLatency: Service response time high
- HighErrorRate: Service error rate high

## Troubleshooting Service Issues

### Service Won't Start

**Diagnosis**:
```bash
# Check logs
docker logs <service-name>

# Check exit code
docker inspect --format='{{.State.ExitCode}}' <service-name>

# Check configuration
docker compose -f /opt/platform/docker-compose.yml config
```

**Common Causes**:
- Configuration error
- Missing dependencies
- Resource constraints
- Port conflicts

### Service Unhealthy

**Diagnosis**:
```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' <service-name>

# Check health check logs
docker inspect <service-name> | grep -A 20 Health

# Test health endpoint
curl http://<service-name>.localhost/health
```

**Common Causes**:
- Health endpoint not responding
- Dependencies unavailable
- Resource constraints
- Application errors

## Best Practices

1. **Always use GitOps**: Make changes in Git, not directly
2. **Verify health**: Check service health after operations
3. **Monitor during changes**: Watch logs and metrics
4. **Test changes**: Use smoke tests after updates
5. **Document changes**: Record all service operations
6. **Respect dependencies**: Start dependencies first
7. **Check resources**: Verify resource availability

## Related Documentation

- Deployment Runbook: `docs-devops/06-deployment-strategy/deployment-runbook.md`
- Troubleshooting: `troubleshooting.md`
- Incident Response: `incident-response.md`
