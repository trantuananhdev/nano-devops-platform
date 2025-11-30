# Nano DevOps Platform – DevOps Context Entrypoint

**Purpose**: This file is the **single entrypoint** for understanding and navigating the Nano DevOps Platform from a DevOps / operations perspective.  
It is optimized for **AI agents and engineers** who need a fast path to the right documents without scanning the entire repo.

🏗️ **Operational Intelligence Domain Map**

**CRITICAL RULE**: AI MUST access this domain ONLY when:
- Implementing infrastructure
- Designing deployment
- Modifying runtime environment
- Handling operational concerns
- Debugging operational issues

---

## 1. Mission, Constraints & Strategy
**Purpose**: Build foundational operational understanding of system boundaries and strategy.
**When to Use**: Starting operational work, understanding system boundaries, or making infra decisions.

- **Mission & strategy**: See [platform-master-strategy.md](file:///c:/TA-work/nano-project-devops/docs-devops/00-overview/platform-master-strategy.md)
  - Single-node (6GB RAM) production-like DevOps platform
  - GitOps-first, immutable deployment, observability-first, automation-first
- **System overview & scope**: See [system-overview.md](file:///c:/TA-work/nano-project-devops/docs-devops/00-overview/system-overview.md)
- **Platform summary & current state**: See [platform-summary.md](file:///c:/TA-work/nano-project-devops/docs-devops/00-overview/platform-summary.md)
- **Platform constraints**: See [platform-constraints.md](file:///c:/TA-work/nano-project-devops/docs-devops/00-overview/platform-constraints.md)

---

## 2. High-Level Architecture
**Purpose**: Ensure changes align with the intended system structure and logical layers.
**When to Use**: Understanding system structure, adding new components, or debugging integration issues.

- **Logical & High-level Architecture**:
  - [high-level-architecture.md](file:///c:/TA-work/nano-project-devops/docs-devops/02-system-architecture/high-level-architecture.md)
  - [logical-architecture.md](file:///c:/TA-work/nano-project-devops/docs-devops/02-system-architecture/logical-architecture.md)
  - [data-flow.md](file:///c:/TA-work/nano-project-devops/docs-devops/02-system-architecture/data-flow.md)
- **Application Service Patterns**:
  - [service-communication-patterns.md](file:///c:/TA-work/nano-project-devops/docs-devops/02-system-architecture/service-communication-patterns.md)
  - [business-logic-patterns.md](file:///c:/TA-work/nano-project-devops/docs-devops/02-system-architecture/business-logic-patterns.md)
  - [service-golden-path.md](file:///c:/TA-work/nano-project-devops/docs-devops/02-system-architecture/service-golden-path.md)
  - [service-creation-guide.md](file:///c:/TA-work/nano-project-devops/docs-devops/02-system-architecture/service-template/service-creation-guide.md)

---

## 3. Infrastructure & Environment
**Purpose**: Maintain reproducible infrastructure and clear filesystem structure on Alpine Linux.
**When to Use**: Setting up environments, configuring runtime, or understanding file structure on the VM.

- **Infra Overview**: [infra-setup-alpine.md](file:///c:/TA-work/nano-project-devops/docs-devops/04-environment-and-infrastructure/infra-setup-alpine.md)
- **Runtime & Filesystem**: 
  - [runtime-environment.md](file:///c:/TA-work/nano-project-devops/docs-devops/04-environment-and-infrastructure/runtime-environment.md)
  - [filesystem-layout.md](file:///c:/TA-work/nano-project-devops/docs-devops/04-environment-and-infrastructure/filesystem-layout.md)
- **Platform Configs**: [project_devops/platform/](file:///c:/TA-work/nano-project-devops/project_devops/platform/)

---

## 4. CI/CD & GitOps
**Purpose**: Ensure automated, reliable, and immutable delivery of platform services.
**When to Use**: Creating/modifying pipelines, understanding deployment flow, or implementing GitOps.

- **CI Architecture**: [ci-architecture.md](file:///c:/TA-work/nano-project-devops/docs-devops/05-ci-cd/ci-architecture.md)
- **CD & GitOps strategy**:
  - [gitops-architecture.md](file:///c:/TA-work/nano-project-devops/docs-devops/05-ci-cd/gitops-architecture.md)
  - [cd-strategy.md](file:///c:/TA-work/nano-project-devops/docs-devops/05-ci-cd/cd-strategy.md)
- **Registry & Config**: [registry-configuration.md](file:///c:/TA-work/nano-project-devops/docs-devops/05-ci-cd/registry-configuration.md)

---

## 5. Deployment & Runtime Operations
**Purpose**: Ensure safe, repeatable, and automated deployments with rollback capabilities.
**When to Use**: Planning deployments, understanding release process, or executing maintenance.

- **Runbooks**: [deployment-runbook.md](file:///c:/TA-work/nano-project-devops/docs-devops/06-deployment-strategy/deployment-runbook.md)
- **Patterns**: [deployment-pattern.md](file:///c:/TA-work/nano-project-devops/docs-devops/06-deployment-strategy/deployment-pattern.md)
- **Scripts**: 
  - [deploy.sh](file:///c:/TA-work/nano-project-devops/project_devops/platform/ops/deployment/deploy.sh)
  - [rollback.sh](file:///c:/TA-work/nano-project-devops/project_devops/platform/ops/deployment/rollback.sh)

---

## 6. Observability & SLOs
**Purpose**: Ensure system is observable, measurable, and alerts when SLOs are at risk.
**When to Use**: Setting up monitoring, defining SLIs/SLOs, or debugging system behavior.

- **Architecture**: [monitoring-architecture.md](file:///c:/TA-work/nano-project-devops/docs-devops/07-observability/monitoring-architecture.md)
- **Policies**: [sli-slo-sla.md](file:///c:/TA-work/nano-project-devops/docs-devops/07-observability/sli-slo-sla.md)
- **Alerting**: [alert-tuning.md](file:///c:/TA-work/nano-project-devops/docs-devops/07-observability/alert-tuning.md)

---

## 7. Backup, Disaster Recovery & Resilience
**Purpose**: Ensure the platform can recover from failures and maintain data integrity.
**When to Use**: Planning backups, disaster recovery scenarios, or testing recovery procedures.

- **Strategy**: [backup-restore-strategy.md](file:///c:/TA-work/nano-project-devops/docs-devops/09-disaster-recovery/backup-restore-strategy.md)
- **Automation**: [backup-automation.md](file:///c:/TA-work/nano-project-devops/docs-devops/09-disaster-recovery/backup-automation.md)
- **Runbook**: [backup-restore.md](file:///c:/TA-work/nano-project-devops/docs-devops/10-runbook/backup-restore.md)

---

## 8. Security & Compliance
**Purpose**: Maintain high security standards and secret management best practices.
**When to Use**: Implementing security measures, secret rotation, or handling security incidents.

- **Baseline**: [security-baseline.md](file:///c:/TA-work/nano-project-devops/docs-devops/08-security/security-baseline.md)
- **Practices**: [security-best-practices.md](file:///c:/TA-work/nano-project-devops/docs-devops/08-security/security-best-practices.md)
- **Secrets & Network**: 
  - [secrets-management.md](file:///c:/TA-work/nano-project-devops/docs-devops/08-security/secrets-management.md)
  - [network-policies.md](file:///c:/TA-work/nano-project-devops/docs-devops/08-security/network-policies.md)

---

## 9. Runbooks & Operational Procedures
**Purpose**: Enable consistent, error-free execution of day-2 operations.
**When to Use**: Responding to incidents, maintenance, or troubleshooting.

- **Index**: [README.md](file:///c:/TA-work/nano-project-devops/docs-devops/10-runbook/README.md)
- **Incident Response**: [incident-response.md](file:///c:/TA-work/nano-project-devops/docs-devops/10-runbook/incident-response.md)
- **Troubleshooting**: [troubleshooting.md](file:///c:/TA-work/nano-project-devops/docs-devops/10-runbook/troubleshooting.md)

---

## 10. How AI Agents Should Use This File

1. Use this file as the **first stop** for any DevOps / operational task.
2. Follow the links into specific domains based on the **When to Use** guidance.
3. Update project state files after significant work.

---
**Remember**: This is operational intelligence. Load only when operational concerns are involved.
