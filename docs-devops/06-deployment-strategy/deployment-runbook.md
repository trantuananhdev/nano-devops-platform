# Deployment Runbook

This runbook provides step-by-step instructions for deploying services to the Nano DevOps Platform using GitOps principles and the automated deployment scripts.

## Prerequisites

- Access to the platform repository
- Docker and Docker Compose installed on the deployment target
- Access to GitHub Container Registry (ghcr.io) for pulling images
- Required environment variables configured (see Environment Variables section)
- At least 1GB free disk space (validated automatically)

## Environment Variables

### Required Variables

The following environment variables must be set before deployment:

```bash
# Registry configuration
export REGISTRY=ghcr.io                                    # Container registry (default: ghcr.io)
export IMAGE_NAME=owner/repo-name                          # GitHub repository name (e.g., owner/nano-project-devops)
export IMAGE_TAG=abc123def456                             # Image tag (commit SHA or 'latest')

# Service configuration
export SERVICE_NAME=health-api                            # Name of service to deploy (must match docker-compose service name)
export COMPOSE_FILE=project_devops/platform/docker-compose.yml  # Path to docker-compose file

# Optional configuration
export HEALTH_CHECK_TIMEOUT=60                            # Health check timeout in seconds (default: 60)
```

### Finding Image Tags

**Option 1: Use Latest Tag**
```bash
export IMAGE_TAG=latest
```

**Option 2: Use Commit SHA**
```bash
# Get commit SHA from Git
export IMAGE_TAG=$(git rev-parse HEAD)

# Or use a specific commit SHA
export IMAGE_TAG=abc123def456789...
```

**Option 3: List Available Tags**
```bash
# View available tags in GitHub Container Registry
# Navigate to: https://github.com/{owner}/{repo}/pkgs/container/{service-name}/versions
```

## Deployment Procedure

### Step 1: Verify Prerequisites

```bash
# Verify Docker is running
docker ps

# Verify docker-compose is available
docker-compose --version

# Verify environment variables are set
echo "Registry: $REGISTRY"
echo "Image Name: $IMAGE_NAME"
echo "Image Tag: $IMAGE_TAG"
echo "Service Name: $SERVICE_NAME"
```

### Step 2: Verify Image Exists in Registry

```bash
# Check if image exists (requires authentication for private repos)
docker pull ${REGISTRY}/${IMAGE_NAME}/${SERVICE_NAME}:${IMAGE_TAG}
```

**Note**: For private repositories, you may need to authenticate first:
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

**Note**: The deployment script automatically validates disk space, Docker connectivity, and image existence before deployment.

### Step 3: Deploy Service

```bash
# Navigate to repository root
cd /path/to/nano-project-devops

# Make deployment script executable (if needed)
chmod +x project_devops/scripts/deploy.sh

# Execute deployment
./project_devops/scripts/deploy.sh
```

### Step 4: Verify Deployment

```bash
# Check service status
docker ps | grep ${SERVICE_NAME}

# Check health status
docker inspect --format='{{.State.Health.Status}}' ${SERVICE_NAME}

# Test service endpoint (if Traefik routing configured)
curl http://${SERVICE_NAME}.localhost/health

# Check logs
docker logs ${SERVICE_NAME}
```

### Step 5: Verify Observability

```bash
# Check Prometheus targets (if Prometheus accessible)
# Navigate to: http://prometheus.localhost:9090/targets

# Verify metrics endpoint
curl http://${SERVICE_NAME}.localhost/metrics

# Check Grafana dashboards (if Grafana accessible)
# Navigate to: http://grafana.localhost:3000
```

## Rollback Procedure

If deployment fails or service is unhealthy, rollback to previous version:

### Automatic Rollback

The deployment script automatically attempts rollback if deployment fails. The rollback script can also auto-detect the previous image tag from deployment state.

### Manual Rollback

#### Step 1: Identify Previous Image Tag

**Option 1: Auto-detect (Recommended)**
```bash
# Rollback script will auto-detect previous tag from deployment state
export SERVICE_NAME=health-api
export COMPOSE_FILE=project_devops/platform/docker-compose.yml
./project_devops/scripts/rollback.sh
```

**Option 2: Check Deployment State**
```bash
# View deployment state file
cat project_devops/scripts/.deployment-state

# Or check deployment history
cat project_devops/scripts/.deployment-history
```

**Option 3: Manual Specification**
```bash
# Use Git history to find previous commit SHA
git log --oneline -5

# Or use a known-good tag
export PREVIOUS_IMAGE_TAG=previous-sha-here
```

#### Step 2: Execute Rollback

```bash
# Set required variables
export SERVICE_NAME=health-api
# PREVIOUS_IMAGE_TAG is optional - will be auto-detected if not set
export COMPOSE_FILE=project_devops/platform/docker-compose.yml

# Make rollback script executable (if needed)
chmod +x project_devops/scripts/rollback.sh

# Execute rollback (auto-detects previous tag)
./project_devops/scripts/rollback.sh

# Or specify previous tag explicitly
export PREVIOUS_IMAGE_TAG=previous-sha-here
./project_devops/scripts/rollback.sh
```

### Step 3: Verify Rollback

```bash
# Check service status
docker ps | grep ${SERVICE_NAME}

# Verify health
docker inspect --format='{{.State.Health.Status}}' ${SERVICE_NAME}

# Test service endpoint
curl http://${SERVICE_NAME}.localhost/health
```

## Troubleshooting

### Issue: Image Pull Fails

**Symptoms**: `Failed to pull image for ${SERVICE_NAME}`

**Possible Causes**:
- Image doesn't exist in registry
- Registry authentication required (private repo)
- Network connectivity issues
- Incorrect image name or tag

**Solutions**:
1. Verify image exists: `docker pull ${REGISTRY}/${IMAGE_NAME}/${SERVICE_NAME}:${IMAGE_TAG}`
2. Authenticate with registry if private: `echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin`
3. Verify IMAGE_NAME matches GitHub repository: `owner/repo-name`
4. Check network connectivity: `ping ghcr.io`

### Issue: Health Check Fails

**Symptoms**: `Health check failed! Container is unhealthy.`

**Possible Causes**:
- Service not starting correctly
- Health check endpoint not responding
- Service dependencies not available
- Resource constraints

**Solutions**:
1. Check service logs: `docker logs ${SERVICE_NAME}`
2. Verify health endpoint: `curl http://localhost:8080/health` (adjust port as needed)
3. Check service dependencies (database, cache, etc.)
4. Verify resource limits: `docker stats ${SERVICE_NAME}`
5. Check docker-compose health check configuration

### Issue: Health Check Timeout

**Symptoms**: `Health check timeout! Container did not become healthy within ${timeout}s`

**Possible Causes**:
- Service takes longer to start than timeout allows
- Health check endpoint slow to respond
- Resource constraints causing slow startup

**Solutions**:
1. Increase timeout: `export HEALTH_CHECK_TIMEOUT=120`
2. Check service startup time in logs
3. Verify resource availability
4. Review health check configuration in docker-compose.yml

### Issue: Service Not Accessible via Traefik

**Symptoms**: Cannot access service at `http://${SERVICE_NAME}.localhost`

**Possible Causes**:
- Traefik labels missing or incorrect
- Traefik not running
- Network configuration issue
- DNS/hosts file not configured

**Solutions**:
1. Verify Traefik is running: `docker ps | grep traefik`
2. Check Traefik labels in docker-compose.yml
3. Verify service is on platform-network: `docker inspect ${SERVICE_NAME} | grep NetworkMode`
4. Check Traefik dashboard: `http://localhost:8080`
5. Verify /etc/hosts entry: `127.0.0.1 ${SERVICE_NAME}.localhost`

### Issue: Prometheus Not Scraping Metrics

**Symptoms**: Metrics not appearing in Prometheus/Grafana

**Possible Causes**:
- Prometheus scrape config missing
- Service metrics endpoint not responding
- Network connectivity issue
- Prometheus not running

**Solutions**:
1. Verify Prometheus is running: `docker ps | grep prometheus`
2. Check metrics endpoint: `curl http://${SERVICE_NAME}:8080/metrics`
3. Verify Prometheus scrape config includes service
4. Check Prometheus targets: `http://prometheus.localhost:9090/targets`
5. Verify service is on platform-network

## Deployment State Tracking

The deployment scripts automatically track deployment state:

- **State File**: `project_devops/scripts/.deployment-state`
  - Tracks current and previous image tags for each service
  - Format: `SERVICE_NAME=CURRENT_TAG:PREVIOUS_TAG`
  - Auto-updated by deploy.sh

- **History Log**: `project_devops/scripts/.deployment-history`
  - Logs all deployments and rollbacks with timestamps
  - Format: `TIMESTAMP | SERVICE_NAME | IMAGE_TAG | STATUS | Notes`
  - Useful for audit and troubleshooting

**Viewing State:**
```bash
# View current deployment state
cat project_devops/scripts/.deployment-state

# View deployment history
cat project_devops/scripts/.deployment-history
```

## Reliability Features

The enhanced deployment scripts include:

1. **Automatic Previous Tag Tracking**: Previous image tags are automatically saved before deployment
2. **Pre-deployment Validation**: Checks disk space, Docker connectivity, and image existence
3. **Enhanced Error Handling**: Better diagnostics and automatic rollback on failure
4. **Improved Health Checks**: Enhanced diagnostics with detailed logging on failures
5. **Deployment State Tracking**: Automatic tracking of current and previous deployments
6. **Rollback Auto-detection**: Rollback script can auto-detect previous tag from state

## Best Practices

1. **Always use versioned tags**: Prefer commit SHA over `latest` for production deployments
2. **Test in staging first**: Deploy to a test environment before production
3. **Monitor during deployment**: Watch logs and metrics during deployment
4. **Trust automatic rollback**: The script automatically tracks previous tags and can rollback
5. **Verify health checks**: Ensure health checks are properly configured
6. **Check resource usage**: Monitor memory and CPU during deployment
7. **Review deployment history**: Check `.deployment-history` for audit trail
8. **Keep deployment state**: Don't manually delete `.deployment-state` file

## Example: Complete Deployment Workflow

```bash
#!/bin/bash
# Example deployment workflow for health-api service

# Set environment variables
export REGISTRY=ghcr.io
export IMAGE_NAME=owner/nano-project-devops
export IMAGE_TAG=$(git rev-parse HEAD)  # Use current commit SHA
export SERVICE_NAME=health-api
export COMPOSE_FILE=project_devops/platform/docker-compose.yml
export HEALTH_CHECK_TIMEOUT=60

# Verify prerequisites
echo "Verifying prerequisites..."
docker ps > /dev/null || { echo "Docker not running"; exit 1; }
[ -z "$IMAGE_NAME" ] && { echo "IMAGE_NAME not set"; exit 1; }

# Deploy
echo "Deploying ${SERVICE_NAME}..."
./project_devops/scripts/deploy.sh

# Verify
echo "Verifying deployment..."
sleep 5
docker inspect --format='{{.State.Health.Status}}' ${SERVICE_NAME}
curl -f http://${SERVICE_NAME}.localhost/health || echo "Health check failed"

echo "Deployment complete!"
```

## Post-Deployment Smoke Tests

After a successful deployment, run a lightweight smoke test to verify that the `health-api` service is healthy and exposing metrics:

```bash
# Option 1: Use the smoke test script
export SERVICE_NAME=health-api
./project_devops/scripts/smoke-test-health-api.sh

# Option 2: Manual checks (equivalent)
curl -f http://health-api.localhost/health    # Expect HTTP 200 and 'healthy' status
curl -f http://health-api.localhost/metrics  # Expect Prometheus metrics including health_api_* series
```

If smoke tests fail:
- Inspect container logs for `health-api`
- Verify Prometheus targets and alerts for the service
- Consider rolling back using the documented rollback procedure

## Related Documentation

- [Deployment Pattern](deployment-pattern.md) - Deployment strategy overview
- [CD Strategy](../05-ci-cd/cd-strategy.md) - Continuous deployment strategy
- [Registry Configuration](../05-ci-cd/registry-configuration.md) - Image registry setup
- [Pipeline Validation](../05-ci-cd/pipeline-validation.md) - Pipeline validation guide
- [Incident Response](../10-runbook/incident-response.md) - Incident response procedures
