# Incident Response

This runbook describes how to handle common incidents using **automated scripts and GitOps-based rollback**, consistent with immutable deployment and automation-first principles.

---

## 1. Overview Text Diagram

```text
Alert / User Report
        ↓
   Triage & Identify
        ↓
   Use scripts / CI jobs
        ↓
 Verify & close incident
        ↓
    Create postmortem (if needed)
```

All remediation should be performed via:

- Scripts in `/opt/platform/scripts`, or
- CI/CD jobs defined in the platform repo,

not by manually patching running containers.

---

## 2. Service Down

### 2.1 Diagnosis

- Check monitoring dashboards (see `monitoring-architecture.md`):
  - Confirm whether only one service is down or multiple.
- Check logs via Loki for the affected service.
- Confirm the last deployment status in CI/CD.

### 2.2 Remediation (Immutable and Automated)

1. **Attempt automated redeploy**
   - Run the service deployment script (example):
     - `deploy-service.sh <service-name>`
   - This will:
     - Pull the current image for the service,
     - Run health checks,
     - Switch traffic if healthy.
2. **Rollback if redeploy fails**
   - Trigger the rollback script (example):
     - `rollback-service.sh <service-name>`
   - Or trigger the corresponding CD pipeline job that re-deploys the previous known-good image.
3. **Escalate**
   - If both redeploy and rollback fail:
     - Capture logs and metrics snapshots,
     - Escalate to platform maintainers with detailed context.

At no point should you permanently fix issues by logging into containers and changing code or configuration in place.

---

## 3. Database Full

### 3.1 Diagnosis

- Confirm alert details:
  - Disk usage on the data volume,
  - Database size and largest tables.
- Use monitoring tools to identify growth trends.

### 3.2 Remediation (Scripted)

1. **Run data cleanup script**
   - Use a documented script, for example:
     - `cleanup-db-data.sh`
   - The script should:
     - Remove or archive old, non-critical data according to policy,
     - Log all actions taken.
2. **If volume extension is required**
   - Follow the documented storage expansion procedure (outside the scope of this runbook), then:
     - Update any relevant configuration in Git if mount points or sizes need to be reflected there.
3. **Verify**
   - Confirm free space is back within safe thresholds.
   - Ensure alerts are cleared and performance is normal.

Manual ad-hoc deletion of data from within the database without a script or well-defined SQL migration should be avoided. Any structural or policy changes must be captured in Git.
