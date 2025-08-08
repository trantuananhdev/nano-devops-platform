# Service Creation Golden Path

**Quick Reference**: Standardized workflow for creating new services on the Nano DevOps Platform.

---

## Overview

This golden path provides the fastest, most reliable way to create a new service that follows all platform patterns and integrates seamlessly with the platform infrastructure.

**Time Estimate**: 30-60 minutes for a basic service, 1-2 hours for a complex service with business logic.

---

## Golden Path Steps

### 1. Plan (5 minutes)

- [ ] Identify service type (basic, database, service-to-service, business logic)
- [ ] Define service endpoints
- [ ] Identify dependencies
- [ ] Estimate resource requirements

### 2. Scaffold (10 minutes)

```bash
# Create service directory
mkdir -p project_devops/apps/[service-name]/src

# Copy templates
cp docs-devops/02-system-architecture/service-template/Dockerfile.template \
   project_devops/apps/[service-name]/Dockerfile

cp docs-devops/02-system-architecture/service-template/app.py.template \
   project_devops/apps/[service-name]/src/app.py

cp docs-devops/02-system-architecture/service-template/README.template.md \
   project_devops/apps/[service-name]/README.md

cp docs-devops/02-system-architecture/service-template/smoke-test.template.sh \
   project_devops/scripts/smoke-test-[service-name].sh
```

### 3. Customize (15-30 minutes)

- [ ] Replace template variables in all files
- [ ] Add custom endpoints to `app.py`
- [ ] Add database functions (if needed)
- [ ] Add business logic (if needed)
- [ ] Complete `README.md` with service details

### 4. Integrate (15-20 minutes)

- [ ] Add service to `docker-compose.yml` (use template snippet)
- [ ] Add CI workflow steps (use template snippet)
- [ ] Add Prometheus scrape config (use template)
- [ ] Create Grafana dashboard (copy from similar service)
- [ ] Add Prometheus alerts (copy from similar service)

### 5. Test (5-10 minutes)

- [ ] Make smoke test executable: `chmod +x smoke-test-[service-name].sh`
- [ ] Review smoke test script
- [ ] Verify all integration points

### 6. Document (5 minutes)

- [ ] Complete README.md
- [ ] Verify all sections are filled
- [ ] Add usage examples

### 7. Validate (5 minutes)

- [ ] Run service creation checklist
- [ ] Verify resource limits
- [ ] Run self-critique

---

## Quick Reference: Template Locations

All templates are located in: `docs-devops/02-system-architecture/service-template/`

- **Dockerfile**: `Dockerfile.template`
- **Application Code**: `app.py.template`
- **Docker Compose**: `docker-compose-snippet.template`
- **CI Workflow**: `ci-workflow-snippet.template`
- **Prometheus**: `prometheus-scrape.template`
- **README**: `README.template.md`
- **Smoke Test**: `smoke-test.template.sh`

---

## Quick Reference: Integration Points

### Docker Compose

**Location**: `project_devops/platform/docker-compose.yml`

**Template**: `service-template/docker-compose-snippet.template`

**Key Variables**:
- `[SERVICE_NAME]`: Service name
- `[MEMORY_LIMIT]`: Memory limit (default: 100M)
- Environment variables
- Dependencies (depends_on)

### CI Workflow

**Location**: `.github/workflows/ci.yml`

**Template**: `service-template/ci-workflow-snippet.template`

**Steps to Add**:
1. Build step in `build` job
2. Package step in `package` job

### Monitoring

**Prometheus Scrape**: `project_devops/monitoring/prometheus/prometheus.yml`

**Grafana Dashboard**: `project_devops/monitoring/grafana/dashboards/[service-name].json`

**Prometheus Alerts**: `project_devops/monitoring/prometheus/alerts/platform-alerts.yml`

---

## Service Type Quick Reference

### Basic Service

**Pattern**: health-api

**Characteristics**:
- No external dependencies
- Simple HTTP endpoints
- <50MB RAM

**Template Variations**: Use basic templates (no database, no service calls)

### Database Service

**Pattern**: data-api, user-api

**Characteristics**:
- PostgreSQL integration
- Database schema initialization
- Database error handling
- <100MB RAM

**Template Variations**: Include database functions, DB_CONFIG, init_db()

### Service-to-Service

**Pattern**: aggregator-api

**Characteristics**:
- Calls other services
- Service discovery
- Timeout handling
- Graceful degradation
- <100MB RAM

**Template Variations**: Include call_service() function, service URLs

### Business Logic Service

**Pattern**: user-api

**Characteristics**:
- Input validation
- Business rules
- Error handling
- PostgreSQL integration
- <100MB RAM

**Template Variations**: Include validation functions, business rules, error handling

---

## Common Pitfalls to Avoid

❌ **Forgetting to add CI workflow steps** - Service won't be built/pushed  
❌ **Missing Prometheus scrape config** - Metrics won't be collected  
❌ **Incorrect Traefik labels** - Service won't be routable  
❌ **Missing health check** - Service won't be considered healthy  
❌ **Wrong resource limits** - May exceed 6GB constraint  
❌ **Incomplete README** - Future developers won't understand service  

---

## Validation Checklist

Before considering a service complete:

- [ ] Service directory structure created
- [ ] Dockerfile created and customized
- [ ] Application code created and customized
- [ ] Service added to docker-compose.yml
- [ ] CI workflow updated (build + package)
- [ ] Prometheus scrape config added
- [ ] Grafana dashboard created
- [ ] Prometheus alerts added
- [ ] Smoke test script created and executable
- [ ] README.md completed
- [ ] Resource limits verified (<100MB RAM)
- [ ] All template variables replaced
- [ ] Service follows platform patterns
- [ ] Self-critique passed

---

## Getting Help

- **Service Creation Guide**: `docs-devops/02-system-architecture/service-template/service-creation-guide.md`
- **Service Communication Patterns**: `docs-devops/02-system-architecture/service-communication-patterns.md`
- **Business Logic Patterns**: `docs-devops/02-system-architecture/business-logic-patterns.md`
- **Reference Services**: `project_devops/apps/` (health-api, data-api, aggregator-api, user-api)

---

## Success Criteria

A service is successfully created when:

✅ Service builds and runs in Docker  
✅ Service is accessible via Traefik routing  
✅ Service exposes `/health` and `/metrics` endpoints  
✅ Service metrics are collected by Prometheus  
✅ Service has Grafana dashboard  
✅ Service has Prometheus alerts  
✅ Smoke test script passes  
✅ Service follows all platform patterns  
✅ Service documentation is complete  

---

**Golden Path Version**: 1.0  
**Last Updated**: 2026-03-01  
**Maintained By**: Platform Engineering Team
