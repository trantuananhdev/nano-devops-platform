# Nano DevOps Platform – Repository Documentation Root

**Purpose**: This file is the **root index for all major documentation** in this repository.  
It tells you, in one place, **where to start** depending on who you are (new engineer, experienced operator, AI agent) and what you want to do.

---

## 1. If You Are New to the Project

- **Understand the mission, constraints, and architecture at a high level**:
  - `docs-devops/00-overview/platform-master-strategy.md`
  - `docs-devops/00-overview/system-overview.md`
  - `docs-devops/00-overview/platform-summary.md`
  - `docs-devops/00-overview/platform-constraints.md`
- **Bring the whole platform up and validate it end‑to‑end**:
  - `docs-devops/00-overview/platform-onboarding-and-validation.md`

These documents give you:

- What the Nano DevOps Platform is.  
- Why it exists and which constraints (single‑node, 6GB RAM).  
- How to go from `git clone` → **full stack running and validated**.

---

## 2. DevOps / Operations Perspective (Runtime & Day‑2)

Use this when you care about **how the system runs in production‑like mode**:

- **DevOps / operational entrypoint**:
  - `docs-devops/final_devops_context.md`
- From there, you will find links to:
  - **Architecture**: `docs-devops/02-system-architecture/*`
  - **Environment & infra**: `docs-devops/04-environment-and-infrastructure/*`
  - **CI/CD & GitOps**: `docs-devops/05-ci-cd/*`
  - **Deployment strategy & scripts**:
    - `docs-devops/06-deployment-strategy/*`
    - `project_devops/scripts/deploy.sh`
    - `project_devops/scripts/rollback.sh`
  - **Observability & SLOs**: `docs-devops/07-observability/*`
  - **Security**: `docs-devops/08-security/*`
  - **Backup & DR**: `docs-devops/09-disaster-recovery/*`
  - **Runbooks (Day‑2 operations)**: `docs-devops/10-runbook/*`
  - **Development workflow**: `docs-devops/11-development-guide/*`

If you are an operator or SRE, start from `final_devops_context.md` and follow links into the domain you need.

---

## 3. AI / Architecture / Design Perspective

Use this when you are an **AI agent or architect** designing changes or reasoning about system‑level behaviour:

- **AI design & knowledge entrypoint**:
  - `docs-ai-context/final_ai_context.md`
- Key AI‑facing documents reachable from there:
  - **Vision & context**: `docs-ai-context/platform-vision.md`, `docs-ai-context/system-context.md`
  - **Platform laws & safety**:
    - `docs-ai-context/platform-laws.yaml`
    - `docs-ai-context/law-context-mapping.yaml`
    - `docs-ai-context/ai-safety-workflow.md`
  - **AI coding & golden paths**:
    - `docs-ai-context/ai-coding-guidelines.md`
    - `docs-ai-context/golden-path/*.yaml`
    - `docs-ai-context/code-generation-rules/*`
  - **Decision systems & SLOs**:
    - `docs-ai-context/decision-trees/*`
    - `docs-ai-context/slo/*`
  - **AI execution planning**:
    - `docs-ai-context/ai-platform-build-plan.md`

If you are an AI agent in **Autonomous Platform Engineer** mode, combine this with the `ai-system/` files below.

---

## 4. AI System State & Execution (ai-system/)

Use this when you want to understand **what the AI has done, is doing, and should do next**:

- **Startup & role definition**:
  - `ai-system/AI_BOOT.md`
- **State & tasks**:
  - `ai-system/PROJECT_STATE.md`
  - `ai-system/ACTIVE_TASK.md`
  - `ai-system/EXECUTION_HISTORY.md`
  - `ai-system/AI_CONTEXT_SNAPSHOT.md`
- **Execution & planning**:
  - `ai-system/AI_EXECUTION_PROTOCOL.md`
  - `ai-system/AI_SELF_CRITIC.md`
  - `ai-system/AI_PLANNING_ENGINE.md`
  - `ai-system/KNOWLEDGE_ROUTING.md`

These files define how an AI instance should:

- Orient on current state.  
- Route knowledge into `docs-ai-context/` and `docs-devops/`.  
- Plan, execute, self‑critique, and log work at **Staff Engineer** quality.

---

## 5. Code & Runtime Layout

To understand where actual code and configs live:

- **Top‑level runtime & services**:
  - `project_devops/apps/` – application services (health-api, data-api, aggregator-api, user-api, etc.).
  - `project_devops/platform/` – platform‑level docker-compose and configs.
  - `project_devops/monitoring/` – Prometheus, Grafana, Loki, exporters, alerts.
  - `project_devops/scripts/` – deploy, rollback, backup and helper scripts.
- **Per‑service READMEs**:
  - Under each `project_devops/apps/<service>/` directory.

When adding or extending services, always:

- Read the relevant service README.  
- Cross‑check with:
  - `docs-devops/02-system-architecture/*` for patterns.  
  - `docs-ai-context/ai-coding-guidelines.md` and `docs-ai-context/golden-path/service.yaml` for AI‑safe patterns.

---

## 6. Recommended Reading Paths

### 6.1 New Engineer (Quick Start)

1. `docs-devops/00-overview/platform-summary.md`  
2. `docs-devops/00-overview/platform-master-strategy.md`  
3. `docs-devops/00-overview/platform-onboarding-and-validation.md`  
4. `docs-devops/final_devops_context.md`

### 6.2 Experienced Operator / SRE

1. `docs-devops/final_devops_context.md`  
2. `docs-devops/07-observability/monitoring-architecture.md`  
3. `docs-devops/10-runbook/README.md`  
4. `docs-devops/09-disaster-recovery/backup-restore-strategy.md` and `drill-playbook.md`

### 6.3 AI Agent / Architect

1. `ai-system/AI_BOOT.md`  
2. `ai-system/PROJECT_STATE.md` and `ACTIVE_TASK.md`  
3. `ai-system/KNOWLEDGE_ROUTING.md`  
4. `docs-ai-context/final_ai_context.md`  
5. `docs-devops/final_devops_context.md`

This file (`docs-root-context.md`) should be the first stop when you need to **orient yourself in the documentation landscape** for the Nano DevOps Platform.

