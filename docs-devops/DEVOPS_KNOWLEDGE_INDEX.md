# DevOps Knowledge Index
🏗️ Operational Intelligence Domain Map

**CRITICAL RULE**: AI MUST access this domain ONLY when:
- Implementing infrastructure
- Designing deployment
- Modifying runtime environment
- Handling operational concerns
- Debugging operational issues

**DO NOT** load this domain during pure feature implementation unless operational aspects are involved.

---

## 📋 SYSTEM OVERVIEW (Read First)

**Location**: `docs-devops/00-overview/`

**Files**:
- `system-overview.md` - High-level system overview
- `platform-master-strategy.md` - Platform strategy and constraints
- `platform-constraints.md` - Hard constraints (6GB, single-node, etc.)

**When to Use**: 
- Starting operational work
- Understanding system boundaries
- Making infrastructure decisions

**Purpose**: Build foundational operational understanding.

---

## 🎯 PHILOSOPHY & PRINCIPLES

**Location**: `docs-devops/01-vision-and-philosophy/`

**Files**:
- `engineering-philosophy.md` - Engineering principles
- `design-principles.md` - Design principles

**When to Use**:
- Making architectural decisions
- Evaluating trade-offs
- Establishing patterns

**Purpose**: Guide engineering decisions with consistent principles.

---

## 🏛️ ARCHITECTURE

**Location**: `docs-devops/02-system-architecture/`

**Files**:
- `high-level-architecture.md` - System structure and components
- `logical-architecture.md` - Logical design and layers
- `data-flow.md` - Data flow patterns and integration points

**When to Use**:
- Understanding system structure
- Adding new components
- Debugging integration issues
- Modifying data flows

**Purpose**: Ensure changes align with system architecture.

---

## 💻 TECH STACK

**Location**: `docs-devops/03-tech-stack/`

**Files**:
- `tech-stack.md` - Technology choices and versions
- `tech-stack-decision.md` - Decision rationale and trade-offs

**When to Use**:
- Selecting technologies
- Understanding technology constraints
- Evaluating alternatives

**Purpose**: Maintain technology consistency and understand constraints.

---

## 🏭 INFRASTRUCTURE & ENVIRONMENT

**Location**: `docs-devops/04-environment-and-infrastructure/`

**Files**:
- `filesystem-layout.md` - File structure on VM/runtime
- `runtime-environment.md` - Runtime configuration and setup

**When to Use**:
- Setting up environments
- Configuring runtime
- Understanding file structure
- Deployment planning

**Purpose**: Maintain reproducible infrastructure and clear structure.

---

## 🚀 CI/CD PIPELINES

**Location**: `docs-devops/05-ci-cd/`

**Files**:
- `ci-architecture.md` - CI pipeline design and stages
- `cd-strategy.md` - CD strategy and deployment approach
- `gitops-architecture.md` - GitOps workflow and principles

**When to Use**:
- Creating/modifying pipelines
- Understanding deployment flow
- Implementing GitOps
- Debugging pipeline issues

**Purpose**: Ensure automated, reliable delivery.

---

## 📦 DEPLOYMENT STRATEGY

**Location**: `docs-devops/06-deployment-strategy/`

**Files**:
- `deployment-pattern.md` - Deployment patterns and strategies

**When to Use**:
- Planning deployments
- Understanding release process
- Implementing deployment patterns

**Purpose**: Ensure safe, repeatable deployments.

---

## 📊 OBSERVABILITY

**Location**: `docs-devops/07-observability/`

**Files**:
- `monitoring-architecture.md` - Monitoring system design
- `sli-slo-sla.md` - SLI/SLO/SLA definitions and policies

**When to Use**:
- Setting up monitoring
- Defining SLIs/SLOs
- Debugging issues
- Analyzing system behavior

**Purpose**: Ensure system is observable and measurable.

---

## 🔒 SECURITY

**Location**: `docs-devops/08-security/`

**Files**:
- `security-baseline.md` - Security requirements and baseline

**When to Use**:
- Implementing security measures
- Security reviews
- Handling secrets
- Security incident response

**Purpose**: Maintain security standards.

---

## 🛡️ DISASTER RECOVERY

**Location**: `docs-devops/09-disaster-recovery/`

**Files**:
- `backup-restore-strategy.md` - Backup and restore procedures

**When to Use**:
- Planning backups
- Disaster recovery scenarios
- Restore procedures
- Testing recovery

**Purpose**: Ensure system can recover from failures.

---

## 🚨 RUNBOOKS & INCIDENTS

**Location**: `docs-devops/10-runbook/`

**Files**:
- `incident-response.md` - Incident response procedures

**When to Use**:
- Responding to incidents
- Creating runbooks
- Understanding operational procedures

**Purpose**: Enable effective incident response.

---

## 👨‍💻 DEVELOPMENT GUIDELINES

**Location**: `docs-devops/11-development-guide/`

**Files**:
- `local-development.md` - Local development setup
- `contribution-guide.md` - Contribution process and guidelines

**When to Use**:
- Setting up local environment
- Contributing code
- Understanding development workflow

**Purpose**: Maintain development consistency.

---

## 📚 APPENDIX

**Location**: `docs-devops/99-appendix/`

**Files**:
- `glossary.md` - Terminology and definitions

**When to Use**:
- Understanding terminology
- Clarifying concepts

**Purpose**: Provide reference for terms and concepts.

---

## 🎯 QUICK REFERENCE BY USE CASE

### Infrastructure Setup
→ System Overview + Infrastructure + Tech Stack

### Pipeline Creation
→ CI/CD + Deployment Strategy + Infrastructure

### Monitoring Setup
→ Observability + Architecture

### Incident Response
→ Runbooks + Disaster Recovery + Observability

### Security Implementation
→ Security + System Overview

### Debugging
→ Observability + Architecture + Runbooks

---

## ⚠️ IMPORTANT NOTES

1. **Load in Order**: Start with System Overview, then load domain-specific files
2. **Cross-Reference**: Architecture affects Infrastructure, CI/CD affects Deployment
3. **Constraints**: Always check platform-constraints.md for hard limits
4. **Philosophy**: Consult philosophy files when making trade-off decisions

---

**Remember**: This is operational intelligence. Load only when operational concerns are involved.