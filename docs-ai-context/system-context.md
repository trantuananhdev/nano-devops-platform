# AI System Context

This document defines the minimal context an AI agent (e.g. Cursor) needs to safely propose and implement changes on the Nano DevOps Platform while respecting the **single-node 6GB constraint**, **GitOps**, and **immutable deployment** principles defined in `platform-master-strategy.md`.

---

## 1. Repository and Filesystem Overview

### 1.1 Repositories

- **Platform repo (this repo)**:  
  - Contains:
    - Infrastructure as code (Docker / docker-compose, runtime scripts)
    - Platform services definitions
    - CI/CD definitions
    - Documentation (`/docs`)
  - **Git is the only source of truth** for platform state.

### 1.2 Filesystem Layout on VM

See `filesystem-layout.md` for details. High-level:

```text
/opt/platform
  ├── apps            # Application services (per-service folders)
  ├── data            # Persistent data (e.g. PostgreSQL volumes)
  ├── monitoring      # Prometheus / Grafana / Loki config & data
  ├── ci              # CI/CD runner and related scripts
  └── scripts         # Operational automation (deploy, backup, restore, etc.)
```

AI agents should **treat this structure as stable** and only modify files where explicitly allowed below.

---

## 2. Naming Conventions

- **Services**
  - Lowercase, hyphen-separated, short but descriptive.  
    - Examples: `user-service`, `billing-api`, `reporting-worker`.
- **Docker Compose service names**
  - Match application service names where possible, with suffixes for infrastructure when needed.  
    - Examples: `user-service`, `platform-postgres`, `platform-prometheus`.
- **Monitoring artifacts**
  - Prometheus job names follow `layer-service` style.  
    - Example: `app-user-service`, `infra-traefik`.
- **Scripts**
  - Use verb-noun form and be explicit about scope.  
    - Examples: `deploy-service.sh`, `rollback-service.sh`, `backup-db.sh`, `restore-db.sh`.

---

## 3. Deployment Flow (GitOps and Immutable)

The only safe way for AI to change the running system is through **Git → CI → CD → Runtime**.

```text
Developer / AI
    ↓ (1) Git commit + PR
Git repository
    ↓ (2) CI pipeline (lint → build → test → package)
Container registry
    ↓ (3) CD pipeline (pull image → health check → switch traffic)
Runtime (Docker on single-node VM)
```

- **Step 1 – Git change**
  - All configuration and code changes are committed to Git.
  - No direct modification of files on `/opt/platform` by hand.
- **Step 2 – CI**
  - Builds container images and runs tests.
  - Produces versioned artifacts (immutable images).
- **Step 3 – CD**
  - Pulls the new image, performs health checks, and switches traffic using rolling update (see `deployment-pattern.md`).
  - Old versions are removed only after successful verification.

AI proposals **must not** bypass this flow.

---

## 4. Service Dependency Map (Conceptual)

For full details see `high-level-architecture.md` and `logical-architecture.md`. Quick textual view:

```text
          Internet User
                │
                ▼
          [Traefik Edge]
                │
                ▼
         [App Services]*  ────►  [PostgreSQL]
                │
                └────────►  [Monitoring Exporters]

CI/CD:
Developer / AI
    │
    ▼
   [Git]
    │
    ▼
 [CI Pipeline] ──► [Image Registry] ──► [CD Scripts] ──► [Docker Runtime]

Observability:
Services ─► [Prometheus] ─► [Grafana]
Logs    ─► [Loki]
Alerts  ─► Alert rules (Prometheus / Grafana)
```

- All app services:
  - Receive traffic only via the reverse proxy.
  - Use **shared PostgreSQL** (no per-service DB by default).
  - Export metrics and logs into the shared monitoring stack.

---

## 5. Allowed Operations for AI

AI agents may:

- **Create or modify application services** under the designated app/service configuration areas:
  - Add/update service definitions in the appropriate Docker Compose file(s) **for application layer only**.
  - Add/update app code within `/opt/platform/apps/<service-name>` (via Git).
- **Extend observability for services**:
  - Add Prometheus scrape configs for new services.
  - Add/update dashboards for new services.
- **Update documentation**:
  - Extend `docs` to describe new services, flows, and runbooks.
- **Modify CI config for new services**:
  - Add jobs/stages so new services are built, tested, and packaged consistently with existing ones.

All changes must **respect resource constraints** and **follow GitOps**.

---

## 6. Forbidden Actions for AI

The following are strictly **forbidden** for AI agents:

- **Core runtime and infrastructure**
  - Do not modify:
    - Core Docker runtime configuration (e.g. base Docker daemon settings).
    - Core infrastructure compose/services for:
      - Traefik
      - PostgreSQL
      - Prometheus / Grafana / Loki
      - CI runner
  - Do not change network topology (ports, network modes) for core components.
- **Resource model violations**
  - Do not introduce:
    - New always-on services that would obviously exceed the **6GB RAM** budget.
    - Per-service databases by default (see `ai-coding-guidelines.md`).
    - Heavy sidecar patterns that duplicate functionality of existing shared infrastructure.
- **Bypassing GitOps**
  - Do not:
    - Directly edit files on `/opt/platform` outside of Git workflows.
    - Suggest manual `docker exec` or in-container changes as permanent fixes.
    - Apply ad-hoc configuration changes that are not represented in Git.
- **Modifying platform design fundamentals**
  - Do not:
    - Introduce Kubernetes or service mesh.
    - Change the single-node / 6GB constraint assumptions.
    - Modify global security baselines (non-root containers, secrets handling, network isolation).

If a required change appears to need any of the above, the AI must instead:

- Document the limitation,
- Propose a **human-reviewed design change** as a separate architectural decision, not an automated code change.

---

## 7. Safe Change Checklist for AI

Before proposing or applying a change, an AI agent should verify:

1. **Constraint fit**
   - Estimated memory impact keeps total usage within the budget in `runtime-environment.md`.
   - No new long-running processes that significantly increase idle resource usage.
2. **GitOps compliance**
   - All modifications are represented as Git changes.
   - No instruction requires out-of-band manual edits on the VM.
3. **Immutable deployment**
   - Changes are rolled out via new container images, not by mutating running containers.
4. **Observability coverage**
   - New services expose metrics/logs consistent with existing standards.
   - Dashboards and alerts are updated if needed.
5. **Documentation**
   - Relevant docs in `/docs` are updated to reflect new behaviour and dependencies.

Only when all the above are satisfied should an AI proceed to suggest or orchestrate changes.
