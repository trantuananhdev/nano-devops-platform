# Service Template Directory

This directory contains templates and documentation for creating new services on the Nano DevOps Platform.

---

## Contents

### Templates

- **Dockerfile.template** - Dockerfile template for services
- **app.py.template** - Python Flask application template
- **docker-compose-snippet.template** - Docker Compose service configuration snippet
- **ci-workflow-snippet.template** - CI workflow build/package steps
- **prometheus-scrape.template** - Prometheus scrape configuration
- **grafana-dashboard.template.json** - Grafana dashboard template
- **prometheus-alerts.template.yml** - Prometheus alert rules template
- **README.template.md** - Service README template
- **smoke-test.template.sh** - Smoke test script template

### Documentation

- **service-creation-guide.md** - Comprehensive step-by-step guide for creating services
- **README.md** - This file

---

## Quick Start

1. Read the [Service Golden Path](../service-golden-path.md) for a quick overview
2. Follow the [Service Creation Guide](service-creation-guide.md) for detailed instructions
3. Use templates as starting points for new services
4. Reference existing services in `project_devops/apps/` for examples

---

## Template Usage

Templates use placeholder variables that should be replaced:

- `[SERVICE_NAME]` - Service name (lowercase, hyphen-separated)
- `[SERVICE_NAME_UPPER]` - Uppercase service name (for alerts)
- `[SERVICE_DESCRIPTION]` - Brief service description
- `[METRIC_PREFIX]` - Metric prefix (e.g., `my_api`)
- `[MEMORY_LIMIT]` - Memory limit in MB

---

## Reference Services

Study these existing services to understand patterns:

- **health-api** - Basic service pattern (no dependencies)
- **data-api** - Database integration pattern
- **aggregator-api** - Service-to-service communication pattern
- **user-api** - Business logic pattern

---

## Related Documentation

- [Service Communication Patterns](../service-communication-patterns.md)
- [Business Logic Patterns](../business-logic-patterns.md)
- [Service Golden Path](../service-golden-path.md)

---

**Last Updated**: 2026-03-01
