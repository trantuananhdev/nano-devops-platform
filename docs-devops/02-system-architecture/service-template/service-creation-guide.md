# Service Creation Guide

This guide provides step-by-step instructions for creating a new service using the service template/golden path.

---

## Prerequisites

Before creating a new service, ensure you understand:
- [Service Communication Patterns](../service-communication-patterns.md)
- [Business Logic Patterns](../business-logic-patterns.md) (if applicable)
- Platform constraints (6GB RAM, single-node, GitOps)
- Service naming conventions (lowercase, hyphen-separated)

---

## Service Creation Checklist

Use this checklist when creating a new service:

### 1. Planning
- [ ] Determine service type (basic, database-integrated, service-to-service, business logic)
- [ ] Identify service dependencies (PostgreSQL, other services)
- [ ] Define service endpoints and functionality
- [ ] Estimate resource requirements (<100MB RAM)

### 2. Service Structure
- [ ] Create service directory: `project_devops/apps/[service-name]/`
- [ ] Create `src/` directory for application code
- [ ] Create `Dockerfile` using template
- [ ] Create `README.md` using template
- [ ] Create `src/app.py` using template

### 3. Docker Compose Integration
- [ ] Add service to `project_devops/platform/docker-compose.yml`
- [ ] Configure environment variables
- [ ] Configure secrets (if needed)
- [ ] Configure dependencies (depends_on)
- [ ] Configure Traefik labels for routing
- [ ] Set resource limits

### 4. CI/CD Integration
- [ ] Add build step to `.github/workflows/ci.yml` (build job)
- [ ] Add package step to `.github/workflows/ci.yml` (package job)
- [ ] Verify image tags use `${github.sha}` and `latest`

### 5. Monitoring Integration
- [ ] Add Prometheus scrape config to `project_devops/monitoring/prometheus/prometheus.yml`
- [ ] Create Grafana dashboard: `project_devops/monitoring/grafana/dashboards/[service-name].json`
- [ ] Add Prometheus alerts to `project_devops/monitoring/prometheus/alerts/platform-alerts.yml`
- [ ] Verify metrics are exposed on `/metrics` endpoint

### 6. Testing
- [ ] Create smoke test script: `project_devops/scripts/smoke-test-[service-name].sh`
- [ ] Make smoke test executable: `chmod +x smoke-test-[service-name].sh`
- [ ] Test smoke test script locally (if possible)

### 7. Documentation
- [ ] Complete `README.md` with service-specific information
- [ ] Document environment variables
- [ ] Document usage examples
- [ ] Document monitoring setup

### 8. Validation
- [ ] Verify service follows platform patterns
- [ ] Verify resource limits are appropriate
- [ ] Verify all integration points are configured
- [ ] Run self-critique per AI_SELF_CRITIC.md

---

## Step-by-Step Workflow

### Step 1: Choose Service Type

Determine which service type you're creating:

1. **Basic Service** (like health-api)
   - No external dependencies
   - Simple HTTP endpoints
   - Minimal resource usage

2. **Database-Integrated Service** (like data-api, user-api)
   - PostgreSQL integration
   - Database schema initialization
   - Database error handling

3. **Service-to-Service Service** (like aggregator-api)
   - Calls other services
   - Service discovery using Docker service names
   - Timeout and error handling

4. **Business Logic Service** (like user-api)
   - Input validation
   - Business rules
   - Error handling patterns

### Step 2: Create Service Directory Structure

```bash
mkdir -p project_devops/apps/[service-name]/src
```

### Step 3: Create Dockerfile

Copy and customize `Dockerfile.template`:
- Replace `{{SERVICE_NAME}}` with actual service name
- Add system dependencies if needed (e.g., PostgreSQL)
- Add Python dependencies
- Adjust memory limit comment

### Step 4: Create Application Code

Copy and customize `app.py.template`:
- Replace template variables with actual values
- Add custom endpoints
- Add database functions if needed
- Add business logic if needed
- Ensure metrics are tracked

### Step 5: Add to Docker Compose

Copy and customize `docker-compose-snippet.template`:
- Replace template variables
- Configure environment variables
- Configure secrets if needed
- Configure dependencies
- Set appropriate resource limits

### Step 6: Update CI Workflow

Copy and customize `ci-workflow-snippet.template`:
- Add build step to build job
- Add package step to package job
- Verify image tags are correct

### Step 7: Add Monitoring

1. **Prometheus Scrape**: Copy `prometheus-scrape.template` and add to `prometheus.yml`
2. **Grafana Dashboard**: Create dashboard JSON based on existing service dashboards
3. **Prometheus Alerts**: Add alerts based on existing service alerts

### Step 8: Create Smoke Test

Copy and customize `smoke-test.template.sh`:
- Replace template variables
- Add service-specific tests
- Make executable: `chmod +x smoke-test-[service-name].sh`

### Step 9: Create Documentation

Copy and customize `README.template.md`:
- Fill in all sections
- Add usage examples
- Document environment variables
- Document monitoring setup

### Step 10: Validate and Test

- Verify all files follow platform patterns
- Check resource limits are appropriate
- Test smoke test script
- Run self-critique

---

## Template Variables Reference

When using templates, replace these variables:

- `[SERVICE_NAME]`: Service name (lowercase, hyphen-separated, e.g., `my-api`)
- `[SERVICE_NAME_UPPER]`: Uppercase service name (e.g., `MY_API`)
- `[SERVICE_DESCRIPTION]`: Brief description of the service
- `[MEMORY_LIMIT]`: Expected memory limit (e.g., `100`)
- `[METRIC_PREFIX]`: Metric prefix (e.g., `my_api`)

---

## Pattern Selection Guide

### When to Use Basic Service Pattern

- Simple HTTP API with no external dependencies
- Health and metrics endpoints only
- Minimal resource usage (<50MB RAM)

**Example**: health-api

### When to Use Database-Integrated Pattern

- Service needs data persistence
- CRUD operations required
- Database schema initialization needed

**Example**: data-api, user-api

### When to Use Service-to-Service Pattern

- Service needs to call other services
- Aggregation or orchestration required
- Service discovery needed

**Example**: aggregator-api

### When to Use Business Logic Pattern

- Complex validation required
- Business rules enforcement needed
- Error handling patterns important

**Example**: user-api

---

## Common Patterns

### Database Connection Pattern

```python
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        app.logger.error(f"Database connection error: {e}")
        db_errors.labels(operation='connect').inc()
        return None
```

### Service Call Pattern

```python
def call_service(url, endpoint, timeout=5.0):
    """Call an external service endpoint"""
    try:
        response = requests.get(f"{url}{endpoint}", timeout=timeout)
        if response.status_code == 200:
            return {'success': True, 'data': response.json()}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Service call timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### Metrics Tracking Pattern

```python
@app.before_request
def before_request():
    """Track request start time"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Track request metrics"""
    request_count.labels(method=request.method, endpoint=request.endpoint or 'unknown').inc()
    duration = time.time() - request.start_time
    request_duration.labels(method=request.method, endpoint=request.endpoint or 'unknown').observe(duration)
    return response
```

---

## Troubleshooting

### Service Won't Start

- Check Docker logs: `docker logs platform-[service-name]`
- Verify health check endpoint is accessible
- Check database connectivity (if applicable)
- Verify environment variables are set correctly

### Metrics Not Appearing

- Verify `/metrics` endpoint is accessible
- Check Prometheus scrape configuration
- Verify service is in `platform-network`
- Check Prometheus logs for scrape errors

### CI Build Fails

- Verify Dockerfile syntax
- Check Python dependencies are correct
- Verify build context path is correct
- Check for missing files in service directory

---

## Best Practices

1. **Always follow the template structure** - Don't deviate from established patterns
2. **Keep services lightweight** - Respect 6GB RAM constraint
3. **Document everything** - Complete README.md with all details
4. **Test thoroughly** - Create comprehensive smoke tests
5. **Monitor everything** - Add metrics, dashboards, and alerts
6. **Follow GitOps** - All changes must be in Git
7. **Small batches** - Keep file changes ≤300 lines

---

**Last Updated**: 2026-03-01  
**Template Version**: 1.0
