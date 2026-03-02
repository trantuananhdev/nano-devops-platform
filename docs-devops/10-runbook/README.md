# Operational Runbooks

This directory contains operational runbooks for the Nano DevOps Platform. Runbooks provide step-by-step procedures for common operational tasks.

## Runbook Index

### Incident Response
**File**: `incident-response.md`

Procedures for handling incidents:
- Service down remediation
- Database full recovery
- Automated rollback procedures
- GitOps-based incident response

**When to Use**: When incidents occur, alerts fire, or services fail

---

### Deployment
**File**: `docs-devops/06-deployment-strategy/deployment-runbook.md`

Procedures for deploying services:
- Service deployment steps
- Rollback procedures
- Health check verification
- Smoke test procedures

**When to Use**: When deploying new services or updating existing services

---

### Backup and Restore
**File**: `backup-restore.md`

Procedures for backups and restores:
- Manual backup procedures
- PostgreSQL restore
- Redis restore
- Backup verification

**When to Use**: Before deployments, for disaster recovery, or data migration

---

### Maintenance
**File**: `maintenance.md`

Regular maintenance procedures:
- Log rotation and cleanup
- Database maintenance
- Monitoring maintenance
- System updates
- Resource cleanup

**When to Use**: Regular maintenance tasks, log cleanup, database optimization

---

### Troubleshooting
**File**: `troubleshooting.md`

Diagnostic procedures and solutions:
- Service health checks
- Network connectivity
- Resource usage analysis
- Common issues and solutions

**When to Use**: When diagnosing issues, investigating problems, or debugging services

---

### Service Management
**File**: `service-management.md`

Service lifecycle operations:
- Start/stop/restart services
- Service status checks
- Configuration updates
- Health verification

**When to Use**: When managing service lifecycle, updating configurations, or checking service status

---

## Quick Reference

### Common Operations

**Deploy Service**:
→ `deployment-runbook.md` → Deployment Procedure

**Rollback Service**:
→ `deployment-runbook.md` → Rollback Procedure

**Backup Data**:
→ `backup-restore.md` → Backup Procedures

**Restore Data**:
→ `backup-restore.md` → Restore Procedures

**Service Down**:
→ `incident-response.md` → Service Down

**Check Service Health**:
→ `service-management.md` → Service Health Verification

**Troubleshoot Issue**:
→ `troubleshooting.md` → Diagnostic Procedures

**Perform Maintenance**:
→ `maintenance.md` → Maintenance Procedures

## Runbook Principles

All runbooks follow these principles:

1. **Script-Based**: Use automated scripts when possible
2. **GitOps**: Changes via Git, not direct runtime modifications
3. **Actionable**: Clear step-by-step procedures
4. **Verifiable**: Include verification steps
5. **Documented**: Record all operations

## Related Documentation

- Deployment Strategy: `docs-devops/06-deployment-strategy/`
- Backup Strategy: `docs-devops/09-disaster-recovery/backup-restore-strategy.md`
- Monitoring: `docs-devops/07-observability/monitoring-architecture.md`
- Scripts: `project_devops/scripts/README.md`
