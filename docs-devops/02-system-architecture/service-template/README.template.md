# [SERVICE_NAME] Service

[SERVICE_DESCRIPTION]

## Purpose

[Describe the purpose of this service and what it demonstrates]

## Features

- **Health Endpoint**: `/health` - Returns service health status
- **Metrics Endpoint**: `/metrics` - Prometheus metrics for observability
- **[Custom Endpoints]**: [Describe custom endpoints]
- **Root Endpoint**: `/` - Service information

## Resource Usage

- **Memory**: <[MEMORY_LIMIT]MB RAM (within 6GB constraint)
- **CPU**: Minimal (lightweight Flask application)
- **Storage**: Minimal (Alpine-based Python image)
[Add database/storage requirements if applicable]

## Environment Variables

[List environment variables with descriptions]

## Observability

- Exposes Prometheus metrics on `/metrics` endpoint
- Tracks request metrics: `[SERVICE_NAME]_api_requests_total`, `[SERVICE_NAME]_api_request_duration_seconds`
- Integrated with Prometheus scrape configuration
- Health checks configured in docker-compose.yml
- Logs collected by Loki (via Docker logging driver)

## Deployment

The service is deployed via:
1. CI pipeline builds and pushes image to ghcr.io
2. Deployment script (`deploy.sh`) pulls image and deploys
3. Traefik routes traffic to service via `[SERVICE_NAME].localhost`

## Monitoring

- **Prometheus Scrape**: Job `[SERVICE_NAME]`, target `[SERVICE_NAME]:8080`
- **Grafana Dashboard**: `[SERVICE_NAME]` (service-specific)
- **Prometheus Alerts**: [List alert names]

## Usage Examples

[Provide usage examples]

## Development

### Local Development

[Local development instructions]

### Docker Build

```bash
docker build -t [SERVICE_NAME]:latest .
```

### Docker Run

```bash
docker run -p 8080:8080 [SERVICE_NAME]:latest
```

## Smoke Tests

Run smoke tests after deployment:

```bash
./project_devops/scripts/smoke-test-[SERVICE_NAME].sh
```
