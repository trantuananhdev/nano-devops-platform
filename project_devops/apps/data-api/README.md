# Data API Service

Simple HTTP API service for storing and retrieving key-value data using PostgreSQL.

## Purpose

This is the second application service added to the platform to validate:
- Multi-service deployment capability
- Infrastructure integration (PostgreSQL database)
- Service-to-database connectivity
- Resource management with multiple services running simultaneously
- CI/CD pipeline handling multiple services

## Features

- **Health Endpoint**: `/health` - Returns service health status and database connectivity
- **Metrics Endpoint**: `/metrics` - Prometheus metrics for observability
- **Data Endpoints**:
  - `GET /data/<key>` - Retrieve data by key
  - `POST /data` - Store or update data (requires JSON body with `key` and `value`)
  - `DELETE /data/<key>` - Delete data by key
- **Root Endpoint**: `/` - Service information

## Resource Usage

- **Memory**: <100MB RAM (within 6GB constraint)
- **CPU**: Minimal (lightweight Flask application)
- **Storage**: Minimal (Alpine-based Python image)
- **Database**: Uses shared PostgreSQL instance

## Infrastructure Integration

- **PostgreSQL**: Connects to `platform-postgres` service
- **Database Schema**: Auto-creates `data_store` table on startup
- **Connection**: Uses environment variables for database configuration

## Observability

- Exposes Prometheus metrics on `/metrics` endpoint
- Integrated with Prometheus scrape configuration
- Health checks configured in docker-compose.yml (includes database connectivity check)
- Logs collected by Loki (via Docker logging driver)
- Database error metrics tracked (`data_api_db_errors_total`)

## Deployment

The service is deployed via:
1. CI pipeline builds and pushes image to ghcr.io
2. Deployment script (`deploy.sh`) pulls image and deploys
3. Traefik routes traffic to service via `data-api.localhost`

## Environment Variables

- `POSTGRES_HOST`: PostgreSQL hostname (default: `platform-postgres`)
- `POSTGRES_PORT`: PostgreSQL port (default: `5432`)
- `POSTGRES_DB`: Database name (default: `platform_db`)
- `POSTGRES_USER`: Database user (default: `platform_user`)
- `POSTGRES_PASSWORD`: Database password (from Docker secrets)

## Monitoring

- **Prometheus Scrape**:
  - Job: `data-api`
  - Target: `data-api:8080`
  - Metrics endpoint: `/metrics`

- **Grafana Dashboard**:
  - Dashboard: `Data API` (service-specific)
  - Key panels:
    - Service status (`up{job="data-api"}`)
    - Overall request rate (`data_api_requests_total`)
    - Per-endpoint request rate and latency (P50, P95, P99 via `data_api_request_duration_seconds`)
    - Database errors (`data_api_db_errors_total`)

- **Prometheus Alerts**:
  - `DataApiDown`: Service is down
  - `DataApiHighLatency`: High latency detected
  - `DataApiDbErrors`: Database errors detected

## Usage Examples

### Store data
```bash
curl -X POST http://data-api.localhost/data \
  -H "Content-Type: application/json" \
  -d '{"key": "test-key", "value": "test-value"}'
```

### Retrieve data
```bash
curl http://data-api.localhost/data/test-key
```

### Delete data
```bash
curl -X DELETE http://data-api.localhost/data/test-key
```

### Health check
```bash
curl http://data-api.localhost/health
```

## Development

### Local Development
```bash
# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=platform_db
export POSTGRES_USER=platform_user
export POSTGRES_PASSWORD=your_password

# Run service
python src/app.py
```

### Docker Build
```bash
docker build -t data-api:latest .
```

### Docker Run
```bash
docker run -p 8080:8080 \
  -e POSTGRES_HOST=platform-postgres \
  -e POSTGRES_DB=platform_db \
  -e POSTGRES_USER=platform_user \
  -e POSTGRES_PASSWORD=your_password \
  data-api:latest
```
