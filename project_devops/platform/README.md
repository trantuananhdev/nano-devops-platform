# Platform Directory

## Purpose

This directory contains platform core configurations and shared infrastructure definitions.

## Repository vs Runtime Mapping

- **Repository**: `project_devops/platform/`
- **Runtime**: Platform configurations are deployed to `/opt/platform/` via docker-compose

## Contents

- `docker-compose.yml` - Infrastructure services (PostgreSQL, Redis, Traefik, Prometheus, Grafana, Loki)
- `traefik/` - Traefik reverse proxy configuration
- `monitoring/` - Monitoring stack configurations
  - `prometheus/` - Prometheus configuration
  - `grafana/` - Grafana provisioning and dashboards
  - `loki/` - Loki configuration
- `secrets/` - Secret files (not committed to Git)

## Services

### Traefik (Edge Layer)
- Reverse proxy and load balancer
- SSL/TLS termination
- Service discovery via Docker
- Memory limit: 200MB
- Ports: 80, 443, 8080 (dashboard)

### PostgreSQL (Data Layer)
- Shared database for all application services
- Persistent storage: `/opt/platform/data/postgres`
- Memory limit: 1.5GB

### Redis (Cache Layer)
- Caching and session store
- Persistent storage: `/opt/platform/data/redis`
- Memory limit: 300MB

### Prometheus (Observability - Metrics)
- Metrics collection and storage
- Persistent storage: `/opt/platform/data/prometheus`
- Memory limit: 400MB
- Port: 9090
- Retention: 7 days

### Grafana (Observability - Visualization)
- Dashboards and visualization
- Persistent storage: `/opt/platform/data/grafana`
- Memory limit: 300MB
- Port: 3000
- Auto-provisioned datasources (Prometheus, Loki)

### Loki (Observability - Logs)
- Log aggregation and storage
- Persistent storage: `/opt/platform/data/loki`
- Memory limit: 300MB
- Port: 3100
- Retention: 7 days

## Resource Allocation

Total infrastructure: ~3GB RAM
- Traefik: 200MB
- PostgreSQL: 1.5GB
- Redis: 300MB
- Prometheus: 400MB
- Grafana: 300MB
- Loki: 300MB

Remaining for applications: ~3GB

## Usage

```bash
# Start infrastructure services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Monitoring Access

- **Grafana**: http://localhost:3000 (admin/admin by default, change password)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

All services are also accessible via Traefik:
- http://grafana.localhost
- http://prometheus.localhost
- http://loki.localhost

## Guidelines

- Core infrastructure services (Traefik, PostgreSQL, monitoring stack)
- Platform-wide settings
- Shared resources configuration
- Must respect 6GB RAM constraint
- Must be single-node compatible
- All secrets must be externalized (not hardcoded)
- Monitoring stack uses 7-day retention to manage storage