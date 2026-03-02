# Scripts Directory

## Purpose

This directory contains operational automation scripts for platform management.

## Repository vs Runtime Mapping

- **Repository**: `project_devops/scripts/`
- **Runtime**: Scripts are deployed to `/opt/platform/scripts/` and executed there

## Contents

- **Deployment Scripts**:
  - `deploy.sh` - Deploy service from container registry (enhanced with reliability features)
  - `rollback.sh` - Rollback to previous service version (auto-detects previous tag)
  - `.deployment-state` - Deployment state tracking file (auto-generated)
  - `.deployment-history` - Deployment history log (auto-generated)

- **Backup Scripts**:
  - `backup-postgres.sh` - PostgreSQL database backup (pg_dump)
  - `backup-redis.sh` - Redis data backup (RDB snapshot)
  - `backup-all.sh` - Orchestrate all backups

- **Smoke Test Scripts**:
  - `smoke-test-health-api.sh` - Health API smoke tests
  - `smoke-test-data-api.sh` - Data API smoke tests
  - `smoke-test-aggregator-api.sh` - Aggregator API smoke tests
  - `smoke-test-user-api.sh` - User API smoke tests

## Guidelines

- Scripts must be executable and well-documented
- Use verb-noun naming convention (e.g., `deploy-service.sh`, `backup-db.sh`)
- Scripts must be idempotent where possible
- All scripts must have error handling
- Scripts should log their actions
- Follow platform laws (immutable deployment, GitOps)

## Deployment Reliability Features

The deployment scripts (`deploy.sh` and `rollback.sh`) include enhanced reliability features:

- **Automatic State Tracking**: Previous image tags are automatically tracked in `.deployment-state`
- **Pre-deployment Validation**: Checks disk space, Docker connectivity, and image existence
- **Enhanced Error Handling**: Better diagnostics and automatic rollback on failure
- **Improved Health Checks**: Enhanced diagnostics with detailed logging
- **Deployment History**: All deployments and rollbacks are logged to `.deployment-history`
- **Auto-rollback Detection**: Rollback script can auto-detect previous tag from state

See `docs-devops/06-deployment-strategy/deployment-runbook.md` for detailed usage.

## Structure Expectations

- Deployment automation
- Backup/restore procedures
- Maintenance tasks
- Health check utilities
