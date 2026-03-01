# Engineering Philosophy

This document defines the core engineering principles for the Nano DevOps Platform. All technical decisions, implementation details, and documentation must align with these principles and with `platform-master-strategy.md`.

---

## GitOps First

All system changes **must go through Git**:

- Configuration, code, and infrastructure are versioned in Git.
- Changes are applied only via:
  - Pull Requests,
  - CI pipelines,
  - CD scripts/pipelines (see `gitops-architecture.md`).
- Direct changes on the running VM (e.g. editing files under `/opt/platform` without Git) are not allowed except for emergency debugging, and must be followed by a Git change that restores consistency.

---

## Immutable Deployment

The platform uses **immutable containers**:

- No direct modification of running containers:
  - No `docker exec`-based hotfixes as permanent solutions.
  - No in-place package installation in running containers.
- Every change is delivered by:
  - Building a new container image,
  - Deploying it via CI/CD,
  - Rolling back by redeploying a previous image if needed.

Operational runbooks (e.g. incident response) must reference **deploy/rollback scripts or pipelines**, not ad-hoc container patching.

---

## Observability-Driven Operation

“No monitoring = no system”:

- All services must emit:
  - Metrics (latency, traffic, errors, saturation where applicable),
  - Logs that can be searched centrally.
- The platform must provide:
  - Dashboards for key flows,
  - Alerts for critical failures and saturation conditions.
- Changes are only considered **done** when:
  - They have adequate visibility in the observability stack,
  - They do not silently degrade existing SLIs (see `sli-slo-sla.md`).

---

## Automation First

Manual work should be:

- Eliminated where reasonable, or
- Turned into scripts and integrated into pipelines.

Concretely:

- Runbooks should point to **scripts in `/opt/platform/scripts`** or CI/CD jobs, not long shell command sequences.
- Common operations (deploy, rollback, backup, restore, log inspection helpers) must be automated and documented.

---

## Resource Efficiency

The platform is designed for a **resource-constrained environment**:

- Runs entirely on a **single VM with 6GB RAM**.
- Prefers:
  - Lightweight components,
  - Shared infrastructure (single PostgreSQL, single monitoring stack),
  - Bounded background jobs.
- Avoids:
  - Heavy service meshes,
  - Per-service databases by default,
  - Always-on components without a clear need.

Every new component must justify its memory and CPU usage in the context of the global budget (see `platform-constraints.md` and `runtime-environment.md`).

---

## Constraint-Driven Architecture

The system is intentionally constrained to:

- A single VM,
- 6GB RAM,
- No horizontal scaling.

Every architectural and technology choice must:

- Optimize memory footprint and idle CPU usage,
- Minimize operational complexity,
- Be aligned with the constraints defined in `platform-master-strategy.md`.

If a desired feature cannot be achieved within these constraints, this must be made explicit in the documentation as a trade-off or a future evolution path, not silently implemented in violation of the constraints.
