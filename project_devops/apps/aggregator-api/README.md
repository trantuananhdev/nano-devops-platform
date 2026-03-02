# Aggregator API Service

HTTP API service that aggregates data from other services (health-api, data-api), demonstrating service-to-service communication patterns.

## Purpose

This is the third application service added to the platform to:
- Demonstrate service-to-service communication patterns
- Establish reusable patterns for inter-service calls
- Validate multi-service interactions work correctly
- Provide an aggregator/gateway pattern example

## Features

- **Health Endpoint**: `/health` - Returns service health and downstream service status
- **Metrics Endpoint**: `/metrics` - Prometheus metrics for observability
- **Aggregate Endpoints**:
  - `GET /aggregate/status` - Aggregates status from all downstream services
  - `GET /aggregate/data/<key>` - Gets data from data-api with service status context
- **Root Endpoint**: `/` - Service information

## Service-to-Service Communication

This service demonstrates the **service-to-service communication pattern**:

### Pattern Overview

```python
# Service calls use HTTP requests to other services
# Services are addressed by Docker service name (e.g., health-api:8080)
# Timeouts and error handling are implemented
# Metrics track service call success/failure
```

### Communication Flow

```text
Client Request
    │
    ▼
[Traefik] → aggregator-api:8080
    │
    ├─► health-api:8080 (service call)
    └─► data-api:8080 (service call)
    │
    ▼
Aggregated Response
```

### Implementation Details

- **Service Discovery**: Uses Docker service names (health-api, data-api)
- **Protocol**: HTTP/REST
- **Error Handling**: Timeouts, connection errors, HTTP errors
- **Observability**: Metrics track service call success/failure and latency
- **Resilience**: Graceful degradation when downstream services unavailable

### Service Call Function

```python
def call_service(url, endpoint, timeout=SERVICE_TIMEOUT):
    """Call an external service endpoint"""
    # Implements timeout, error handling, metrics tracking
    # Returns structured response with success/error information
```

## Resource Usage

- **Memory**: <100MB RAM (within 6GB constraint)
- **CPU**: Minimal (lightweight Flask application)
- **Storage**: Minimal (Alpine-based Python image)
- **Network**: Makes HTTP calls to other services

## Environment Variables

- `HEALTH_API_URL`: Health API service URL (default: `http://health-api:8080`)
- `DATA_API_URL`: Data API service URL (default: `http://data-api:8080`)
- `SERVICE_TIMEOUT`: Timeout for service calls in seconds (default: `5.0`)

## Observability

- Exposes Prometheus metrics on `/metrics` endpoint
- Tracks service call metrics:
  - `aggregator_api_service_calls_total` - Service call count by target and status
  - `aggregator_api_service_call_duration_seconds` - Service call latency
- Integrated with Prometheus scrape configuration
- Health checks configured in docker-compose.yml
- Logs collected by Loki (via Docker logging driver)

## Deployment

The service is deployed via:
1. CI pipeline builds and pushes image to ghcr.io
2. Deployment script (`deploy.sh`) pulls image and deploys
3. Traefik routes traffic to service via `aggregator-api.localhost`

## Monitoring

- **Prometheus Scrape**:
  - Job: `aggregator-api`
  - Target: `aggregator-api:8080`
  - Metrics endpoint: `/metrics`

- **Grafana Dashboard**:
  - Dashboard: `Aggregator API` (service-specific)
  - Key panels:
    - Service status (`up{job="aggregator-api"}`)
    - Request rate (`aggregator_api_requests_total`)
    - Service call success rate (`aggregator_api_service_calls_total`)
    - Service call latency (`aggregator_api_service_call_duration_seconds`)

- **Prometheus Alerts**:
  - `AggregatorApiDown`: Service is down
  - `AggregatorApiHighLatency`: High latency detected
  - `AggregatorApiServiceCallFailures`: Downstream service call failures

## Usage Examples

### Get aggregated status
```bash
curl http://aggregator-api.localhost/aggregate/status
```

### Get aggregated data
```bash
curl http://aggregator-api.localhost/aggregate/data/test-key
```

### Health check
```bash
curl http://aggregator-api.localhost/health
```

## Service Communication Pattern Documentation

### Pattern: HTTP Service-to-Service Calls

**When to use**: When a service needs to call another service

**Implementation**:
1. Use Docker service names for service discovery (e.g., `health-api:8080`)
2. Implement timeout handling (default 5 seconds)
3. Handle connection errors gracefully
4. Track metrics for service calls (success/failure, latency)
5. Return structured responses with success/error information

**Example**:
```python
def call_service(url, endpoint, timeout=5.0):
    try:
        response = requests.get(f"{url}{endpoint}", timeout=timeout)
        return {'success': True, 'data': response.json()}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

**Best Practices**:
- Always set timeouts for service calls
- Track metrics for observability
- Handle errors gracefully (don't fail entire request)
- Use environment variables for service URLs
- Document service dependencies

## Development

### Local Development
```bash
# Set environment variables
export HEALTH_API_URL=http://localhost:8081
export DATA_API_URL=http://localhost:8082

# Run service
python src/app.py
```

### Docker Build
```bash
docker build -t aggregator-api:latest .
```

### Docker Run
```bash
docker run -p 8080:8080 \
  -e HEALTH_API_URL=http://health-api:8080 \
  -e DATA_API_URL=http://data-api:8080 \
  aggregator-api:latest
```
