# KNOWLEDGE ROUTING SYSTEM
Autonomous Platform Engineer Mode

This file defines HOW the AI navigates knowledge across the project.

The repository already contains full knowledge.
AI must NOT guess.
AI must ROUTE cognition intentionally.

---

# 0. GLOBAL RULE

AI NEVER reads the entire repository.

AI ALWAYS:

1. Read PROJECT_STATE.md
2. Read ACTIVE_TASK.md
3. Identify TASK TYPE
4. Load ONLY relevant knowledge regions

---

# 1. PRIMARY KNOWLEDGE SOURCES

## PLATFORM INTELLIGENCE (Design Brain)
Location:
docs-ai-context/

Entry point:
docs-ai-context/final_ai_context.md

Contains:
- platform intent
- platform laws
- AI coding rules
- decision systems
- golden paths
- safety workflows

---

## OPERATIONAL INTELLIGENCE (Reality Brain)
Location:
docs-devops/

Entry point:
docs-devops/final_devops_context.md

Contains:
- infrastructure
- deployment
- CI/CD
- runtime architecture
- observability
- security
- recovery
- operational runbooks

---

# 2. TASK TYPE → KNOWLEDGE ROUTING

---

## SYSTEM UNDERSTANDING / ORIENTATION

Load:
- docs-ai-context/platform-vision.md
- docs-ai-context/system-context.md
- docs-devops/00-overview/*
- docs-devops/02-system-architecture/*

Purpose:
Build global mental model.

---

## ARCHITECTURE OR PLATFORM DESIGN

Load:
- docs-ai-context/platform-laws.yaml
- docs-ai-context/law-context-mapping.yaml
- docs-ai-context/decision-trees/*
- docs-ai-context/system-context.md
- docs-devops/02-system-architecture/*

Rule:
Platform laws override local decisions.

---

## SERVICE CREATION / CODE GENERATION

Load:
- docs-ai-context/code-generation-rules/*
- docs-ai-context/golden-path/service.yaml
- docs-ai-context/ai-coding-guidelines.md
- docs-ai-context/platform-laws.yaml

Goal:
Create services that match platform standards.

---

## ENVIRONMENT / INFRASTRUCTURE WORK

Load:
- docs-devops/04-environment-and-infrastructure/*
- docs-devops/03-tech-stack/*
- docs-ai-context/golden-path/environment.yaml

Goal:
Maintain reproducible infrastructure.

---

## CI/CD OR PIPELINE WORK

Load:
- docs-devops/05-ci-cd/*
- docs-ai-context/golden-path/pipeline.yaml
- docs-ai-context/ci-enforcement/*
- docs-ai-context/platform-laws.yaml

Goal:
Automated and policy-compliant delivery.

---

## DEPLOYMENT TASKS

Load:
- docs-devops/06-deployment-strategy/*
- docs-devops/04-environment-and-infrastructure/*
- docs-devops/03-tech-stack/*

Goal:
Safe and repeatable deployment.

---

## OBSERVABILITY / DEBUGGING

Load:
- docs-devops/07-observability/*
- docs-devops/10-runbook/*
- docs-devops/02-system-architecture/*

Goal:
Understand system behavior before modifying code.

Rule:
Debug by understanding system flow first.

---

## SECURITY WORK

Load:
- docs-devops/08-security/*
- docs-ai-context/ai-safety-workflow.md
- docs-ai-context/platform-laws.yaml

Goal:
Respect platform safety guarantees.

---

## RELIABILITY / SLO / ERROR BUDGET

Load:
- docs-ai-context/slo/*
- docs-devops/07-observability/*
- docs-devops/09-disaster-recovery/*

Goal:
Protect system reliability.

---

## INCIDENT RESPONSE

Load:
- docs-devops/10-runbook/*
- docs-devops/09-disaster-recovery/*

Goal:
Restore system safely.

---

## CONTRIBUTION / LOCAL DEVELOPMENT

Load:
- docs-devops/11-development-guide/*

Goal:
Maintain developer workflow consistency.

---

# 3. WHEN AI IS UNSURE

AI MUST STOP and reload:

- docs-ai-context/final_ai_context.md
- docs-devops/final_devops_context.md
- PROJECT_STATE.md
- ACTIVE_TASK.md

Then re-evaluate task.

Never continue while uncertain.

---

# 4. ARCHITECTURAL SAFETY RULES

AI MUST NEVER:

- bypass platform-laws.yaml
- invent architecture
- modify unrelated modules
- execute multiple unrelated tasks

If conflict exists:
Platform Laws > Golden Path > Local Implementation

---

# 5. EXECUTION LOOP (MANDATORY)

Every task execution follows:

1. Orient → read state
2. Route knowledge
3. Plan small steps
4. Execute minimal change
5. Validate against platform laws
6. Update PROJECT_STATE
7. Continue or finish

---

# 6. COGNITIVE PRINCIPLE

AI does NOT search files.

AI navigates SYSTEM KNOWLEDGE.

Think like:
A Platform Engineer operating a living system.