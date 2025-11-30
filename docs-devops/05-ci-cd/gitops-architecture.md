# GitOps Architecture

This document specifies how **Git** controls the Nano DevOps Platform, and how changes flow from source control to the single-node runtime in a way that respects **immutable deployment** and **automation-first** principles.

---

## 1. Repositories and Scope

- **Platform repository (this repo)**
  - Contains:
    - Application service definitions and Docker Compose files
    - CI pipeline configuration
    - CD scripts and configuration
    - Monitoring configuration
    - Documentation (`/docs`)
  - Acts as the **single source of truth** for platform state.

---

## 2. Environments and Branching

- **Main branch**
  - Represents the desired state of the **single production-like environment**.
  - Only updated through Pull Requests (PRs) with review.
- **Feature branches**
  - Used for development and experimentation.
  - Must target `main` via PR.

Even in a single-node setup, **all changes** must go through this PR flow.

---

## 3. Change Flow (Git → CI → CD → Runtime)

High-level GitOps pipeline:

```text
Developer / AI
    │  (1) Commit & PR
    ▼
     Git (feature branch)
    │  (2) CI: lint → build → test → package → security & law checks
    ▼
  Image Registry (versioned images)
    │  (3) Merge to main (after review & green CI)
    ▼
   CD Scripts / Pipelines
    │  (4) Deploy: pull image → health check → switch traffic
    ▼
 Single-node Docker Runtime
```

- **Step 1 – Commit & PR**
  - All platform changes are committed to Git and proposed via PR.
  - No direct edits to the live VM are allowed.
- **Step 2 – CI**
  - Defined in `ci-architecture.md`.
  - Produces an immutable container image as the deployment artifact.
  - Enforces platform laws for:
    - Small batch changes và trunk-based development,
    - Presence of unit tests,
    - SLO/telemetry configuration,
    - Security scans (SAST, dependency scan, secret detection).
- **Step 3 – Merge to `main`**
  - Requires:
    - At least one human review (for human-driven changes).
    - Green CI (bao gồm security & law checks).
- **Step 4 – CD**
  - Implemented by scripts/pipelines in the platform repo.
  - Uses rolling update with health checks (see `deployment-pattern.md`).

---

## 4. Configuration Management

- **Application configuration**
  - Stored in:
    - Docker Compose files,
    - Per-service configuration files within the repo.
  - Externalized from container images (see `engineering-philosophy.md`).
- **Secrets**
  - Never committed in clear text.
  - Passed via environment variables or external secret stores.
- **Runtime configuration**
  - Any change that affects runtime behaviour must be:
    - Represented in Git,
    - Deployed via CI/CD.

There are **no "manual only" configuration paths**.

---

## 5. Rollback via GitOps

Rollback is performed by reverting Git state and redeploying:

```text
Problem detected
    │
    ▼
  Git revert / rollback commit
    │
    ▼
 Re-run CI (if needed) or reuse existing image
    │
    ▼
   CD re-deploys previous image
```

- Platform never patches containers in place.
- Operational docs (e.g. `incident-response.md`) must point to:
  - `rollback` scripts or CD pipeline jobs,
  - Not to ad-hoc manual shell commands.

---

## 6. Responsibilities and Ownership

- **Developers**
  - Propose changes via PR.
  - Keep service-level docs and configs consistent.
- **Platform maintainers**
  - Own CI/CD configuration, GitOps workflows, and core runtime definitions.
  - Guardrails:
    - Enforce non-root containers,
    - Enforce Git-only changes to runtime.
- **AI agents**
  - May author PRs that follow:
    - This GitOps architecture,
    - `ai-coding-guidelines.md`,
    - `system-context.md`.
  - Must never bypass Git or manipulate runtime state directly.

---

## 7. Text Diagram: End-to-End GitOps Loop

```text
          ┌────────────────────┐
          │   Developer / AI   │
          └─────────┬──────────┘
                    │  (1) PR with code+config changes
                    ▼
            ┌──────────────┐
            │     Git      │
            │ (feature br) │
            └──────┬───────┘
                   │  (2) CI: build & test
                   ▼
         ┌──────────────────────┐
         │   Image Registry     │
         │ (versioned images)   │
         └─────────┬────────────┘
                   │  (3) Merge to main
                   ▼
           ┌────────────────┐
           │    CD Layer    │
           │ (scripts/pipes)│
           └────────┬───────┘
                    │  (4) Deploy/rollback
                    ▼
         ┌──────────────────────┐
         │  Docker Runtime VM   │
         └──────────────────────┘
```

