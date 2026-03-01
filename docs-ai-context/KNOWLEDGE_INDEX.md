# AI KNOWLEDGE INDEX
🧭 Navigation System for AI Context Loading

**CRITICAL RULE**: AI MUST NOT read entire repository.

**MANDATORY WORKFLOW**:
1. Read `ai-system/PROJECT_STATE.md`
2. Read `ai-system/ACTIVE_TASK.md`
3. Use `ai-system/KNOWLEDGE_ROUTING.md` to identify task type
4. Load ONLY relevant knowledge regions listed below
5. Update `ai-system/AI_CONTEXT_SNAPSHOT.md` with loaded knowledge

---

## 🚀 STARTUP CONTEXT (Always Read First)

**When**: Starting any new task or session

**Files**:
- `docs-ai-context/platform-vision.md` - Platform goals and principles
- `docs-ai-context/system-context.md` - System overview and constraints
- `ai-system/AI_BOOT.md` - Autonomous mode instructions
- `ai-system/AI_BRAIN.md` - Cognitive rules

**Purpose**: Build foundational understanding of platform intent and constraints.

---

## 🏗️ ARCHITECTURE & DESIGN

**When**: 
- Changing system components
- Adding new services
- Modifying data flow
- Making architectural decisions

**Files**:
- `docs-devops/02-system-architecture/high-level-architecture.md` - System structure
- `docs-devops/02-system-architecture/logical-architecture.md` - Logical design
- `docs-devops/02-system-architecture/data-flow.md` - Data flow patterns
- `docs-ai-context/platform-laws.yaml` - Platform design laws
- `docs-ai-context/law-context-mapping.yaml` - Law application guide
- `docs-ai-context/decision-trees/*` - Decision frameworks

**Purpose**: Ensure changes align with architecture and platform laws.

---

## 🔧 CODE GENERATION & SERVICE CREATION

**When**:
- Creating new services
- Generating code
- Following golden paths

**Files**:
- `docs-ai-context/code-generation-rules/repo-structure.yaml` - Repository structure
- `docs-ai-context/code-generation-rules/service-scaffold.yaml` - Service templates
- `docs-ai-context/golden-path/service.yaml` - Service golden path
- `docs-ai-context/ai-coding-guidelines.md` - Coding standards
- `docs-ai-context/platform-laws.yaml` - Must comply with laws

**Purpose**: Generate code that matches platform standards.

---

## 🚢 CI/CD & DEPLOYMENT

**When**:
- Working on pipelines
- Deployment automation
- Release processes

**Files**:
- `docs-devops/05-ci-cd/ci-architecture.md` - CI pipeline design
- `docs-devops/05-ci-cd/cd-strategy.md` - CD strategy
- `docs-devops/05-ci-cd/gitops-architecture.md` - GitOps workflow
- `docs-ai-context/golden-path/pipeline.yaml` - Pipeline golden path
- `docs-ai-context/ci-enforcement/law-checks.yaml` - CI law enforcement

**Purpose**: Ensure automated delivery follows platform patterns.

---

## 🏭 INFRASTRUCTURE & ENVIRONMENT

**When**:
- Environment setup
- Runtime configuration
- Infrastructure changes

**Files**:
- `docs-devops/04-environment-and-infrastructure/filesystem-layout.md` - File structure
- `docs-devops/04-environment-and-infrastructure/runtime-environment.md` - Runtime setup
- `docs-devops/03-tech-stack/tech-stack.md` - Technology choices
- `docs-devops/03-tech-stack/tech-stack-decision.md` - Decision rationale
- `docs-ai-context/golden-path/environment.yaml` - Environment golden path

**Purpose**: Maintain reproducible infrastructure.

---

## 📊 OBSERVABILITY & MONITORING

**When**:
- Adding monitoring
- Debugging issues
- Setting up SLIs/SLOs

**Files**:
- `docs-devops/07-observability/monitoring-architecture.md` - Monitoring design
- `docs-devops/07-observability/sli-slo-sla.md` - SLO definitions
- `docs-ai-context/slo/slo-template.yaml` - SLO template
- `docs-ai-context/slo/error-budget-policy.yaml` - Error budget rules

**Purpose**: Ensure system is observable and measurable.

---

## 🔒 SAFETY & PLATFORM LAW (MANDATORY CHECK)

**When**: ALWAYS before making changes

**Files**:
- `docs-ai-context/platform-laws.yaml` - Platform laws (MUST READ)
- `docs-ai-context/ai-safety-workflow.md` - Safety workflow (MUST READ)
- `docs-ai-context/law-context-mapping.yaml` - Law application guide

**Purpose**: Ensure all changes comply with platform laws and safety requirements.

---

## 🛡️ SECURITY

**When**:
- Security-related work
- Adding authentication
- Handling secrets

**Files**:
- `docs-devops/08-security/security-baseline.md` - Security requirements
- `docs-ai-context/platform-laws.yaml` - Security laws section

**Purpose**: Maintain security standards.

---

## 🚨 INCIDENT & RECOVERY

**When**:
- Incident response
- Disaster recovery
- Failure handling

**Files**:
- `docs-devops/10-runbook/incident-response.md` - Incident procedures
- `docs-devops/09-disaster-recovery/backup-restore-strategy.md` - Recovery procedures

**Purpose**: Handle failures safely.

---

## 📚 DEVELOPMENT GUIDELINES

**When**:
- Local development
- Contributing code
- Understanding workflows

**Files**:
- `docs-devops/11-development-guide/local-development.md` - Local setup
- `docs-devops/11-development-guide/contribution-guide.md` - Contribution process

**Purpose**: Maintain development consistency.

---

## 🧠 AI SYSTEM FILES (Internal)

**When**: Understanding AI system behavior

**Files**:
- `ai-system/AI_BOOT.md` - Startup instructions
- `ai-system/AI_PLANNING_ENGINE.md` - Planning logic
- `ai-system/AI_EXECUTION_PROTOCOL.md` - Execution process
- `ai-system/AI_SELF_CRITIC.md` - Self-critique system
- `ai-system/KNOWLEDGE_ROUTING.md` - Knowledge routing logic
- `ai-system/MULTI_AI_COORDINATION.md` - Multi-AI coordination
- `ai-system/EXECUTION_HISTORY.md` - Work history
- `ai-system/KNOWLEDGE_PERSISTENCE.md` - Accumulated knowledge

**Purpose**: Understand how AI systems operate.

---

## 📖 FINAL CONTEXT FILES (Comprehensive)

**When**: Need comprehensive context (use sparingly)

**Files**:
- `docs-ai-context/final_ai_context.md` - Complete AI context (if exists)
- `docs-devops/final_devops_context.md` - Complete DevOps context (if exists)

**Purpose**: Comprehensive context when detailed understanding needed.

---

## 🎯 QUICK REFERENCE

### By Task Type:
- **System Understanding**: Startup Context + Architecture
- **Service Creation**: Code Generation + Golden Paths
- **Infrastructure**: Infrastructure + Environment
- **Pipeline Work**: CI/CD + Golden Paths
- **Debugging**: Observability + Architecture
- **Security**: Safety & Platform Law + Security

### By Priority:
1. **Always**: Safety & Platform Law
2. **Startup**: Startup Context
3. **Task-Specific**: Use KNOWLEDGE_ROUTING.md to identify

---

**Remember**: Load minimal knowledge. Use KNOWLEDGE_ROUTING.md to identify what's needed for your specific task type.