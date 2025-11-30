# Nano DevOps Platform – DevOps Context Entrypoint

**Purpose**: This file is the **single entrypoint** for understanding and navigating the Nano DevOps Platform from a DevOps / operations perspective.  
It is optimized for **AI agents and engineers** who need a fast path to the right documents without scanning the entire repo.

---

## 1. Mission, Constraints & Strategy

- **Mission & strategy**: See `docs-devops/00-overview/platform-master-strategy.md`  
  - Single-node (6GB RAM) production-like DevOps platform  
  - GitOps-first, immutable deployment, observability-first, automation-first
- **System overview & scope**: See `docs-devops/00-overview/system-overview.md`
- **Platform summary & current state**: See `docs-devops/00-overview/platform-summary.md`
- **Platform constraints** (resources, non-goals, limits): See `docs-devops/00-overview/platform-constraints.md`

If you need a **guided tour from zero → full platform running and validated**, start with:  
- `docs-devops/00-overview/platform-onboarding-and-validation.md`

---

## 2. High-Level Architecture

Use these documents to understand how the platform is structured:

- **Logical & high-level architecture**:
  - `docs-devops/02-system-architecture/high-level-architecture.md`
  - `docs-devops/02-system-architecture/logical-architecture.md`
  - `docs-devops/02-system-architecture/data-flow.md`
- **Application service patterns**:
  - `docs-devops/02-system-architecture/service-communication-patterns.md`
  - `docs-devops/02-system-architecture/business-logic-patterns.md`
  - `docs-devops/02-system-architecture/service-golden-path.md`
  - `docs-devops/02-system-architecture/service-template/service-creation-guide.md`

These files define **how services are built, communicate, and are deployed** on the Nano DevOps Platform.

---

## 3. CI/CD & GitOps

For anything related to pipelines, builds, and GitOps:

- **CI architecture & pipeline**:
  - `docs-devops/05-ci-cd/ci-architecture.md`
  - `docs-devops/05-ci-cd/pipeline-validation.md`
- **CD & GitOps strategy**:
  - `docs-devops/05-ci-cd/gitops-architecture.md`
  - `docs-devops/05-ci-cd/cd-strategy.md`
- **Registry & environment variables**:
  - `docs-devops/05-ci-cd/registry-configuration.md`
  - `docs-devops/05-ci-cd/environment-variables.md`

When implementing or modifying CI/CD behavior, always align with these documents and the platform laws in `docs-ai-context/platform-laws.yaml`.

---

## 4. Deployment & Runtime Operations

Deployment, rollback, and runtime behavior are defined here:

- **Deployment strategy & runbooks**:
  - `docs-devops/06-deployment-strategy/deployment-strategy.md` (if present)
  - `docs-devops/06-deployment-strategy/deployment-runbook.md`
- **Environment & infrastructure**:
  - `docs-devops/04-environment-and-infrastructure/infra-overview.md` (and related files)
  - `project_devops/platform/` for platform-level configs
  - `project_devops/scripts/deploy.sh` and `rollback.sh` for operational scripts

For **how to execute deployments and rollbacks in practice**, prefer the runbooks in `docs-devops/06-deployment-strategy/` and the onboarding guide.

---

## 5. Observability & SLOs

To understand and operate the monitoring and alerting stack:

- **Monitoring architecture & dashboards**:
  - `docs-devops/07-observability/monitoring-architecture.md`
  - `docs-devops/07-observability/grafana-dashboards.md` (if present)
- **SLIs, SLOs, and alerting**:
  - `docs-devops/07-observability/sli-slo-sla.md`
  - `docs-devops/07-observability/alert-tuning.md`
- **Service-specific monitoring**:
  - References from each service’s README under `project_devops/apps/*/`

Use these to **debug issues, validate health, and tune alerts** before changing code or infrastructure.

---

## 6. Backup, Disaster Recovery & Resilience

Disaster recovery is strategy + automation + drills:

- **Strategy & objectives (RTO/RPO)**:
  - `docs-devops/09-disaster-recovery/backup-restore-strategy.md`
- **Operational runbooks**:
  - `docs-devops/10-runbook/backup-restore.md`
- **DR drills / game days**:
  - `docs-devops/09-disaster-recovery/drill-playbook.md`
- **Backup scripts**:
  - `project_devops/scripts/backup-postgres.sh`
  - `project_devops/scripts/backup-redis.sh`
  - `project_devops/scripts/backup-all.sh`

For any DR-related work, start with the **strategy**, then follow **runbooks and playbook**—never improvise ad-hoc procedures.

---

## 7. Security & Compliance

Security is documentation- and process-driven in this platform:

- **Security baseline & best practices**:
  - `docs-devops/08-security/security-baseline.md`
  - `docs-devops/08-security/security-best-practices.md`
- **Secrets & network**:
  - `docs-devops/08-security/secrets-management.md`
  - `docs-devops/08-security/network-policies.md`

Platform-level laws and safety workflows that influence security are defined in:

- `docs-ai-context/platform-laws.yaml`
- `docs-ai-context/ai-safety-workflow.md`

---

## 8. Runbooks & Operational Procedures

All day‑2 operations should use runbooks:

- **Runbook index & overview**:
  - `docs-devops/10-runbook/README.md`
- **Key runbooks**:
  - `docs-devops/10-runbook/backup-restore.md`
  - `docs-devops/10-runbook/maintenance.md`
  - `docs-devops/10-runbook/troubleshooting.md`
  - `docs-devops/10-runbook/service-management.md`

When in doubt about how to operate the platform, start from the **runbook index** and follow the documented procedures.

---

## 9. Development & Contribution Workflow

For local development and contribution guidelines:

- `docs-devops/11-development-guide/development-workflow.md` (and related files, if present)
- Service-specific READMEs under:
  - `project_devops/apps/health-api/`
  - `project_devops/apps/data-api/`
  - `project_devops/apps/aggregator-api/`
  - `project_devops/apps/user-api/`

These documents define how developers (and AI agents) should **create, extend, and validate services** on the platform while staying within constraints.

---

## 10. How AI Agents Should Use This File

When in **Autonomous Platform Engineer** mode:

1. Use this file as the **first stop** for any DevOps / operational task.  
2. From here, follow the links into the specific domain (CI/CD, deployment, observability, DR, security, runbooks, development).  
3. Respect `KNOWLEDGE_ROUTING.md`: this file is the **OPERATIONAL INTELLIGENCE entrypoint** (`docs-devops/final_devops_context.md`).  
4. Never scan the entire repo; instead, navigate via this context and the linked documents.  
5. Update state files (`ai-system/PROJECT_STATE.md`, `ai-system/AI_CONTEXT_SNAPSHOT.md`, `ai-system/EXECUTION_HISTORY.md`) after significant DevOps work.

This keeps cognition focused, reproducible, and aligned with platform laws and constraints.

