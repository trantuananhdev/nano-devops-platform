# Apps Directory

## Purpose

This directory contains application services that run on the platform.

## Repository vs Runtime Mapping

- **Repository**: `project_devops/apps/`
- **Runtime**: `/opt/platform/apps/`

Each application service should have its own subdirectory:
```
apps/
  ├── service-name/
  │   ├── Dockerfile
  │   ├── docker-compose.yml (service definition)
  │   ├── src/ (application code)
  │   └── tests/
```

## Guidelines

- Services must be stateless where possible
- Each service must include health checks
- Services must export metrics and logs
- Follow naming convention: lowercase, hyphen-separated (e.g., `user-service`, `billing-api`)
- Services use shared PostgreSQL database (no per-service DB by default)

## Structure Expectations

- Service code and Dockerfiles
- Service-specific docker-compose service definitions
- Tests for each service
- Service documentation
