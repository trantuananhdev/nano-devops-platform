# AI Coding Guidelines

These guidelines define how an AI agent (e.g. Cursor) should design and implement changes so they remain safe, efficient, and aligned with the **Platform Master Strategy**.

---

## 1. Core Principles

- **Constraint-driven design**
  - Always assume a **single-node VM with 6GB RAM**.
  - Prefer low-memory components and reuse existing shared infrastructure.
- **GitOps only**
  - All changes must be made through Git, not by editing files directly on the VM.
- **Immutable deployment**
  - Never patch a running container; always build and deploy a new image.
- **Observability-first**
  - Every new or changed service must have metrics and logs integrated into the platform stack.
- **Automation-first**
  - Prefer scripts and pipelines over manual commands; keep runbooks script-oriented.

---

## 2. When Adding a New Service

When adding a new application service, the AI must follow this high-level flow:

```text
Read docs
  ↓
Design service (API, dependencies, resource estimate)
  ↓
Update app code + service config
  ↓
Wire into CI (build & test)
  ↓
Wire into CD (deploy & rollback)
  ↓
Add observability (metrics, logs, dashboards)
  ↓
Update documentation
```

### 2.1 Required Steps

1. **Update application code and service definition**
   - Add a new service under the designated apps area (following existing patterns).
   - Add or update entries in the Docker Compose configuration for the **application layer only**.
2. **Update CI**
   - Ensure the CI pipeline builds and tests the new service.
   - Reuse existing stages (lint, build, test, package) where possible.
3. **Update CD**
   - Ensure the deployment scripts/pipelines can:
     - Deploy the new service,
     - Perform health checks,
     - Support rollback using previous images.
4. **Update monitoring**
   - Add Prometheus scrape configuration for the new service.
   - Ensure logs are collected by Loki.
   - Optionally add/update Grafana dashboards.
5. **Update documentation**
   - Document:
     - Service purpose and responsibilities,
     - Dependencies,
     - Resource expectations,
     - Runbook entries relevant to this service.

---

## 3. Resource Awareness and Limits

- **Hard limit**: The total platform must fit into **6GB RAM**.
- AI must:
  - Estimate the memory footprint of any new long-running service.
  - Prefer:
    - **Multi-process containers** (one container running multiple simple workers) over many small containers.
    - **Shared infrastructure** (single PostgreSQL, single logging/metrics stack) over per-service instances.
  - Avoid:
    - Per-service databases by default.
    - Heavy sidecars for functionality that already exists (e.g. per-service log shippers if Loki is present).
  - Refuse to add a service if a reasonable estimate shows the memory budget would be exceeded without removing or tuning something else.

If the resource impact is uncertain, the AI should:

- Propose a lightweight design,
- Clearly document assumptions and ask for human validation rather than forcing the change.

---

## 4. Safe Patterns vs. Unsafe Patterns

### 4.1 Prefer (Safe)

- Reusing **existing PostgreSQL** for additional schemas or tables when needed.
- Adding lightweight HTTP services behind the existing reverse proxy.
- Exporting basic metrics (request count, latency, error rate, resource usage).
- Batch or cron-style jobs that:
  - Run infrequently,
  - Shut down after completion,
  - Have bounded runtime and memory.

### 4.2 Avoid (Unsafe)

- Creating new always-on databases for each service.
- Adding large, memory-heavy components (e.g. full-text search clusters, distributed queues) without:
  - A clear capacity analysis,
  - An explicit architectural decision.
- Introducing new orchestration layers (Kubernetes, service mesh).
- Modifying core runtime infra (reverse proxy, shared DB, monitoring stack) without human review.

---

## 5. Example: Adding a Simple HTTP Service

This example shows the **expected behaviour** from an AI agent when adding a new service called `report-service`.

1. **Design**
   - Stateless HTTP API that reads from PostgreSQL and returns reports.
   - Estimate memory usage to be small (tens of MB).
2. **Code & config**
   - Create `/apps/report-service` with application code.
   - Add a `report-service` entry in the application Docker Compose file:
     - Connect to the existing PostgreSQL instance.
     - Expose metrics endpoint.
3. **CI**
   - Reuse existing jobs:
     - Add `report-service` build and test steps to CI configuration.
4. **CD**
   - Ensure CD scripts:
     - Can deploy `report-service` using rolling update with health checks.
     - Tag and use versioned images for rollback.
5. **Observability**
   - Add Prometheus scrape job for `report-service`.
   - Ensure logs are sent to Loki with clear labels.
6. **Docs**
   - Update:
     - Architecture docs to include `report-service`.
     - Any relevant runbook entries.
     - AI context if `report-service` becomes a common dependency.

---

## 6. AI Self-Check Before Submitting Changes

**CRITICAL**: See `ai-safety-workflow.md` for the complete workflow. You **MUST** log all actions and generate an execution summary. You **MUST NOT** perform Git operations (checkout, commit, push, merge).

Before finalizing a change, the AI should verify:

1. **Constraints**
   - Memory and CPU usage are consistent with `platform-constraints.md` and `runtime-environment.md`.
2. **Consistency with master strategy**
   - No introduction of disallowed technologies (Kubernetes, service mesh, heavy sidecars).
3. **Deployment safety**
   - Changes are deployable via existing or extended CI/CD pipelines.
   - Rollback path is clear (previous image version).
4. **Observability**
   - New code exposes basic metrics and logs.
5. **Documentation**
   - All relevant documents in `/docs` have been updated to reflect the change.
6. **Logging and verification** (see `ai-safety-workflow.md`)
   - All actions logged
   - Execution summary generated
   - Verification status reported (✅/⚠️/❌)

If any of these checks fail, the AI should **stop**, explain the conflict in the execution log, and request human guidance instead of forcing a design that violates the platform strategy.
