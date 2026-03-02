# Service Communication Patterns

This document describes the patterns for service-to-service communication in the Nano DevOps Platform.

---

## Overview

Services communicate with each other using **HTTP/REST** over the Docker network. Services are discovered using Docker service names.

---

## Communication Pattern

### Basic Pattern

```python
import requests

def call_service(service_name, endpoint, timeout=5.0):
    """Call another service by Docker service name"""
    url = f"http://{service_name}:8080{endpoint}"
    try:
        response = requests.get(url, timeout=timeout)
        return {'success': True, 'data': response.json()}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### Service Discovery

- **Method**: Docker service names
- **Format**: `http://<service-name>:<port>`
- **Example**: `http://health-api:8080`, `http://data-api:8080`

### Network

- All services are on the `platform-network` Docker network
- Services can communicate using Docker service names
- No external DNS or service mesh required

---

## Implementation Guidelines

### 1. Timeout Handling

**Always set timeouts** for service calls:

```python
SERVICE_TIMEOUT = 5.0  # seconds
response = requests.get(url, timeout=SERVICE_TIMEOUT)
```

**Rationale**: Prevents hanging requests and resource exhaustion.

### 2. Error Handling

**Handle common errors gracefully**:

```python
try:
    response = requests.get(url, timeout=timeout)
    if response.status_code == 200:
        return {'success': True, 'data': response.json()}
    else:
        return {'success': False, 'error': f'HTTP {response.status_code}'}
except requests.exceptions.Timeout:
    return {'success': False, 'error': 'Service call timeout'}
except requests.exceptions.ConnectionError:
    return {'success': False, 'error': 'Service connection error'}
except Exception as e:
    return {'success': False, 'error': str(e)}
```

### 3. Metrics Tracking

**Track service call metrics**:

```python
from prometheus_client import Counter, Histogram

service_call_count = Counter(
    'service_calls_total',
    'Total service calls',
    ['target_service', 'status']
)

service_call_duration = Histogram(
    'service_call_duration_seconds',
    'Service call duration',
    ['target_service']
)

# Track call
start_time = time.time()
result = call_service(...)
duration = time.time() - start_time

service_call_duration.labels(target_service='health-api').observe(duration)
service_call_count.labels(
    target_service='health-api',
    status=str(result.get('status_code', 'error'))
).inc()
```

### 4. Graceful Degradation

**Don't fail entire request if one service call fails**:

```python
# Get data from multiple services
health_result = call_service('health-api', '/health')
data_result = call_service('data-api', '/data/key')

# Return partial results if some calls fail
return {
    'health': health_result if health_result['success'] else None,
    'data': data_result if data_result['success'] else None,
    'status': 'partial' if not all(r['success'] for r in [health_result, data_result]) else 'complete'
}
```

---

## Example: Aggregator Service

The `aggregator-api` service demonstrates service-to-service communication:

### Service Calls

```python
# Call health-api
health_api_result = call_service(HEALTH_API_URL, '/health')

# Call data-api
data_api_result = call_service(DATA_API_URL, '/data/key')
```

### Health Check with Downstream Status

```python
@app.route('/health', methods=['GET'])
def health():
    # Check downstream services
    health_api_result = call_service(HEALTH_API_URL, '/health')
    data_api_result = call_service(DATA_API_URL, '/health')
    
    # Determine overall health
    all_healthy = health_api_result['success'] and data_api_result['success']
    
    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'downstream_services': {
            'health-api': {'available': health_api_result['success']},
            'data-api': {'available': data_api_result['success']}
        }
    }
```

---

## Best Practices

1. **Use environment variables** for service URLs:
   ```python
   HEALTH_API_URL = os.getenv('HEALTH_API_URL', 'http://health-api:8080')
   ```

2. **Set appropriate timeouts** (default 5 seconds)

3. **Track metrics** for observability

4. **Handle errors gracefully** - don't fail entire request

5. **Document service dependencies** in README

6. **Use structured responses** with success/error information

7. **Include downstream service status** in health checks

---

## Service Dependencies

### Declaring Dependencies

In `docker-compose.yml`:

```yaml
services:
  aggregator-api:
    depends_on:
      health-api:
        condition: service_healthy
      data-api:
        condition: service_healthy
```

This ensures services start in the correct order.

---

## Monitoring Service Calls

### Metrics to Track

- **Service call count**: `service_calls_total{target_service, status}`
- **Service call duration**: `service_call_duration_seconds{target_service}`
- **Service call success rate**: `rate(service_calls_total{status="200"}[5m]) / rate(service_calls_total[5m])`

### Alerts

- **Service call failures**: Alert when failure rate exceeds threshold
- **Service call latency**: Alert when latency exceeds threshold
- **Downstream service unavailable**: Alert when downstream service is down

---

## Anti-Patterns to Avoid

❌ **Hardcoding service URLs** - Use environment variables  
❌ **No timeout handling** - Always set timeouts  
❌ **Failing entire request on single service failure** - Use graceful degradation  
❌ **No metrics tracking** - Track all service calls  
❌ **Synchronous blocking calls** - Use timeouts and async patterns if needed  

---

## Future Enhancements

- **Circuit breaker pattern** - Prevent cascading failures
- **Retry logic** - Automatic retries for transient failures
- **Service mesh** - If needed for more complex scenarios (not required for single-node)

---

**Pattern Established By**: aggregator-api service (Phase 2 Task 1)  
**Last Updated**: 2026-03-01
