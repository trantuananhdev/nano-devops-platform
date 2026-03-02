# Health API Service

Minimal HTTP API service for CI/CD pipeline validation.

## Purpose

This is the first application service added to the platform to validate:
- End-to-end CI/CD pipeline (Git → CI → Registry → CD → Runtime)
- Image registry integration
- Deployment scripts functionality
- Monitoring stack integration
- Health check and rollback flows

## Features

- **Health Endpoint**: `/health` - Returns service health status
- **Metrics Endpoint**: `/metrics` - Prometheus metrics for observability
- **Root Endpoint**: `/` - Service information

## Resource Usage

- **Memory**: <50MB RAM (within 6GB constraint)
- **CPU**: Minimal (lightweight Flask application)
- **Storage**: Minimal (Alpine-based Python image)

## Observability

- Exposes Prometheus metrics on `/metrics` endpoint
- Integrated with Prometheus scrape configuration
- Health checks configured in docker-compose.yml
- Logs collected by Loki (via Docker logging driver)

## Deployment

The service is deployed via:
1. CI pipeline builds and pushes image to ghcr.io
2. Deployment script (`deploy.sh`) pulls image and deploys
3. Traefik routes traffic to service via `health-api.localhost`

## Monitoring

- **Prometheus Scrape**:
  - Job: `health-api`
  - Target: `health-api:8080`
  - Metrics endpoint: `/metrics`

- **Grafana Dashboard**:
  - Dashboard: `Health API` (service-specific)
  - Key panels:
    - Service status (`up{job="health-api"}`)
    - Overall request rate (`health_api_requests_total`)
    - Per-endpoint request rate and latency (P50, P95, P99 via `health_api_request_duration_seconds`)

- **Prometheus Alerts**:
  - `HealthApiDown`:
    - Condition: `up{job="health-api"} == 0` for 1m
    - Severity: `critical`
  - `HealthApiHighLatency`:
    - Condition: P95 latency from `health_api_request_duration_seconds` > 1s for 10m
    - Severity: `warning`

These monitoring components help validate that the first application service is healthy and performing within expected SLOs.

## Usage

```bash
# Health check
curl http://health-api.localhost/health

# Metrics
curl http://health-api.localhost/metrics

# Service info
curl http://health-api.localhost/
```

## Post-Deployment Smoke Test

After deploying `health-api` via the platform deployment scripts, you can run a small smoke test to validate the service:

```bash
export SERVICE_NAME=health-api
./project_devops/scripts/smoke-test-health-api.sh
```

This script:
- Calls `http://health-api.localhost/health` and checks for a healthy status payload
- Calls `http://health-api.localhost/metrics` and verifies that Prometheus metrics are exposed (including `health_api_requests_total`)

## Development

```bash
# Build locally
docker build -t health-api:local ./project_devops/apps/health-api

# Run locally
docker run -p 8080:8080 health-api:local

# Test
curl http://localhost:8080/health
```
