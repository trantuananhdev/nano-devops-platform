# Incident Response & Post‑Incident Review Runbook

**Scope**: End-to-end workflow for handling incidents on the Nano DevOps Platform (single-node, 6GB) from **detection → triage → mitigation → recovery → post‑incident review (PIR)**.  
This runbook connects monitoring, alerts, backup/restore, DR drills, and existing runbooks into a single operational flow.

---

## 1. When to Use This Runbook

Use this runbook when:

- Critical alerts fire (service down, resource exhaustion, database issues, disk nearly full, etc.).
- User-visible impact is suspected or confirmed (errors, timeouts, degraded performance).
- DR drills or chaos exercises intentionally simulate failures.

It **does not replace** specialized runbooks (e.g. `backup-restore.md`, `troubleshooting.md`), but orchestrates them.

---

## 2. Incident Lifecycle (High-Level)

```text
Detection → Triage → Mitigation/Containment → Recovery → Verification → Post‑Incident Review
```

- **Detection**: Alerts from Prometheus/Grafana or manual reports.
- **Triage**: Confirm incident, assess scope and severity, pick initial hypothesis.
- **Mitigation/Containment**: Stop the bleeding (rollback, scale down load, isolate components, enable maintenance mode if available).
- **Recovery**: Restore healthy service using deploy, backup/restore, or DR procedures.
- **Verification**: Confirm system health via dashboards, logs, and smoke tests.
- **Post‑Incident Review**: Record timeline, impact, root cause, and follow-up actions.

---

## 3. Roles (Conceptual)

These roles are **conceptual** for small teams / single-operator environments:

- **Incident Commander (IC)**:
  - Owns overall coordination and decisions.
  - Keeps track of timeline and current plan.
- **Operator**:
  - Executes commands and runbooks on the platform.
  - Reports results and observations to the IC.
- **Scribe (optional)**:
  - Records timestamps, actions, and outcomes.

In a one-person scenario, a single engineer may play all roles but should still **follow the structure**.

---

## 4. Step‑by‑Step Workflow

### 4.1 Detection & Initial Triage

1. **Acknowledge the alert / report**
   - Confirm that someone is actively handling the incident.
2. **Check monitoring & alerts**
   - Open Grafana dashboards:
     - Platform overview, service-specific dashboards, Infrastructure Health.
   - Review recent alerts (Prometheus / Grafana).
3. **Confirm incident scope**
   - Which services are affected? (health‑api, data‑api, aggregator‑api, user‑api, database, cache, monitoring).
   - Is user impact confirmed (errors/timeouts) or only potential?
4. **Classify severity (rough)**
   - **Critical**: User-visible outage or severe degradation.
   - **Warning**: Degradation, but system still functioning.
   - **Info**: No immediate impact; observation only.

If you suspect a platform issue but need more detail, jump to relevant sections of `troubleshooting.md`.

---

### 4.2 Deep Triage & Hypothesis

1. **Use troubleshooting runbook**
   - Follow `docs-devops/10-runbook/troubleshooting.md`:
     - Service health checks.
     - Logs.
     - Network connectivity.
     - Resource usage (CPU, memory, disk).
2. **Narrow down likely cause**
   - **Resource issues** → High memory/CPU/disk alerts; see Infrastructure Health dashboard and resource sections.
   - **Service issues** → Unhealthy containers, failing health checks, exceptions in logs.
   - **Database/cache issues** → PostgreSQL/Redis down, failing connections.
3. **Decide initial mitigation strategy**
   - Example options:
     - Roll back a recent deploy.
     - Restart a misbehaving service.
     - Free disk space (cleanup old backups/logs).
     - Initiate backup/restore runbook if data corruption/loss suspected.

Record the **current hypothesis** and chosen plan before executing high-impact actions.

---

### 4.3 Mitigation & Containment

Goal: **stop impact from getting worse**, even if root cause is not fully understood.

Possible actions (always via existing scripts/runbooks):

- **Rollback a deployment**
  - Use deployment runbook: `docs-devops/06-deployment-strategy/deployment-runbook.md`.
  - Use `deploy.sh` / `rollback.sh` as documented.
- **Restart or isolate services**
  - Use `service-management.md` for safe start/stop/restart procedures.
- **Address resource exhaustion**
  - Follow relevant sections in `troubleshooting.md` and resource optimization docs (memory, CPU, disk).
- **Prepare for backup/restore**
  - If data corruption or loss suspected, coordinate with `backup-restore.md` and DR strategy before executing restores.

Always:
- Prefer **reversible** actions (rollback, restart) before destructive ones.
- Keep notes of commands executed and their timestamps.

---

### 4.4 Recovery & DR Integration

If mitigation alone is insufficient and data or state is impacted:

1. **Consult DR strategy & runbook**
   - `docs-devops/09-disaster-recovery/backup-restore-strategy.md`
   - `docs-devops/10-runbook/backup-restore.md`
2. **If scenario matches DR drill playbook**
   - Use procedures in `docs-devops/09-disaster-recovery/drill-playbook.md` as guidance:
     - PostgreSQL data loss scenario.
     - Redis data loss scenario.
3. **Execute restore / rebuild**
   - Follow `backup-restore.md` strictly (no ad‑hoc SQL unless explicitly allowed).
   - Use documented scripts (`backup-all.sh`, `restore` scripts) rather than custom commands.
4. **Re-deploy / restart services**
   - Use deployment runbook to ensure services are brought back consistently.

Throughout recovery, maintain a simple **timeline log** (see template below).

---

### 4.5 Verification

After mitigation/recovery steps:

1. **Check platform health**
   - Grafana: Platform overview, Infrastructure Health, service dashboards.
   - Confirm key metrics back within normal ranges.
2. **Run smoke tests**
   - Use each service’s smoke test or README‑documented flows:
     - health‑api, data‑api, aggregator‑api, user‑api.
3. **Confirm alerts quiet down**
   - Previously firing alerts should resolve.
   - No new critical alerts should appear.
4. **Decide incident closure**
   - When system is stable and user impact is gone or acceptable.

Only close the incident after **both metrics and functional checks** look healthy.

---

## 5. Post‑Incident Review (PIR)

After the incident (ideally within 24–72h), run a short PIR focused on **learning**, not blame.

### 5.1 PIR Goals

- Understand what happened (timeline, root cause).
- Identify what worked well and what didn’t (detection, response, tools).
- Produce **concrete follow-up actions** (docs, observability, automation, runbooks, resource tuning).

### 5.2 PIR Template

Create a record (e.g. in docs, tickets, or wiki) using this structure:

```markdown
## [INCIDENT_ID] - [Short Title] - [Date]

**Severity**: [Critical/Warning/Info]  
**Services Affected**: [list]  
**Reporter**: [name/role]  
**Incident Commander**: [name/role]  

### Summary
- One-paragraph description of what happened and impact.

### Timeline (UTC)
- [HH:MM] Incident detected (alert / report)
- [HH:MM] Incident acknowledged
- [HH:MM] Mitigation action started (rollback/restart/etc.)
- [HH:MM] Recovery/restore started (if applicable)
- [HH:MM] Service healthy and impact resolved

### Impact
- User impact: [what users experienced]
- Duration: [total incident time]
- Data impact: [none / partial loss / corruption / etc.]

### Root Cause Analysis (RCA)
- **Technical root cause**: [description]
- **Contributing factors**: [configuration, deployment, resource constraints, etc.]
- **Detection quality**: How was it detected? Were alerts adequate?

### What Worked Well
- [ ] Monitoring and alerts
- [ ] Runbooks and scripts
- [ ] Communication and coordination

### What Didn’t Work / Gaps
- [ ] Missing or unclear runbooks
- [ ] Noisy or missing alerts
- [ ] Slow or manual steps that could be automated

### Follow-Up Actions
- [ ] Update runbooks: [link to changes]
- [ ] Tune alerts: [link to `alert-tuning.md` section / rules]
- [ ] Improve backups/DR: [link to DR docs if impacted]
- [ ] Other improvements: [resource optimization, scripts, documentation]

### Links & Artifacts
- Grafana dashboards / screenshots: [links]
- Logs or traces: [links]
- Related PRs / commits: [links]
```

---

## 6. Integration with Existing Docs

- **Monitoring & Alerts**
  - `docs-devops/07-observability/monitoring-architecture.md`
  - `docs-devops/07-observability/alert-tuning.md`

- **Backup & Disaster Recovery**
  - `docs-devops/09-disaster-recovery/backup-restore-strategy.md`
  - `docs-devops/09-disaster-recovery/drill-playbook.md`
  - `docs-devops/10-runbook/backup-restore.md`

- **Operational Runbooks**
  - `docs-devops/10-runbook/troubleshooting.md`
  - `docs-devops/10-runbook/service-management.md`
  - `docs-devops/10-runbook/maintenance.md`

When responding to an incident, **start here**, then jump to the specialized runbooks as needed.

---

## 7. Usage Notes for AI Agents

- Treat this file as the **primary incident-response playbook**.
- Never invent new ad‑hoc procedures when a documented runbook exists; instead:
  - Follow this workflow.
  - Call into the linked runbooks and DR playbook.
  - Respect GitOps and `delivery.small_batch` (no large, risky edits).
- After simulated or real incidents you handle, **ensure PIR outputs are persisted** (e.g. as docs or tickets) so future incidents get easier to manage.

