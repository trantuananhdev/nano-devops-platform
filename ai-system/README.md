# AI SYSTEM
🧠 Continuous Autonomous Development & Staff Engineer System

This directory contains the complete system for enabling AI to operate as an autonomous Platform Engineer with self-criticism capabilities, supporting multiple AI instances (Cursor, GPT, Gemini) working together seamlessly.

---

## 🎯 SYSTEM OVERVIEW

This system enables:
- **Autonomous Development**: AI continuously plans and executes tasks
- **Self-Criticism**: AI evaluates its own work before completion
- **Multi-AI Coordination**: Seamless handoff between Cursor, GPT, Gemini
- **Knowledge Persistence**: Learning and patterns are preserved
- **State Management**: Complete project state tracking
- **Context Transfer**: Smooth transitions between sessions/accounts

---

## 📁 FILE STRUCTURE

### Core System Files

#### `AI_BOOT.md`
**Purpose**: Startup instructions for AI instances
**When to Read**: First file to read when starting work
**Contains**: Autonomous mode instructions, role definition

#### `AI_BRAIN.md`
**Purpose**: Cognitive rules and knowledge sources
**When to Read**: Understanding how AI should think
**Contains**: Source of truth, cognitive rules

#### `AI_PLANNING_ENGINE.md`
**Purpose**: Autonomous task planning system
**When to Read**: When generating next tasks
**Contains**: Planning loop, task generation rules, priority order

#### `AI_EXECUTION_PROTOCOL.md`
**Purpose**: Standardized execution process
**When to Read**: Before executing any task
**Contains**: Pre-execution, execution, post-execution steps

#### `AI_SELF_CRITIC.md`
**Purpose**: Self-criticism and quality assurance system
**When to Read**: After completing any task
**Contains**: Critique loop, quality assessment, staff engineer perspective

### Knowledge & Routing

#### `KNOWLEDGE_ROUTING.md`
**Purpose**: How AI navigates knowledge
**When to Read**: Before loading context
**Contains**: Task type → knowledge mapping, routing rules

#### `KNOWLEDGE_PERSISTENCE.md`
**Purpose**: Accumulated knowledge and patterns
**When to Read**: When facing similar problems
**Contains**: Discovered patterns, solutions, learnings

### State Management

#### `PROJECT_STATE.md`
**Purpose**: Current project status
**When to Read**: Always before starting work
**Contains**: Phase, completion status, metrics, objectives

#### `ACTIVE_TASK.md`
**Purpose**: Current active task
**When to Read**: Always before starting work
**Contains**: Task description, status, execution plan

#### `MASTER_PLAN.md`
**Purpose**: Complete development roadmap
**When to Read**: When planning or understanding overall progress
**Contains**: Phases, tasks, milestones, success criteria

### History & Tracking

#### `EXECUTION_HISTORY.md`
**Purpose**: Complete log of all AI work
**When to Read**: Understanding recent work, resuming sessions
**Contains**: Chronological task logs, decisions, learnings

#### `AI_CONTEXT_SNAPSHOT.md`
**Purpose**: Current context state snapshot
**When to Read**: Understanding current AI context
**Contains**: Loaded knowledge, active decisions, current understanding

### Multi-AI Coordination

#### `MULTI_AI_COORDINATION.md`
**Purpose**: Coordination between AI instances
**When to Read**: When switching AI instances or accounts
**Contains**: State synchronization, conflict resolution, handoff protocol

#### `CONTEXT_TRANSFER.md`
**Purpose**: Handoff document template
**When to Read**: When switching instances/accounts
**Contains**: Current state snapshot, recent work, next steps

---

## 🚀 QUICK START

### For New AI Instance (First Time)

1. **Read Startup Files**:
   ```
   AI_BOOT.md → AI_BRAIN.md → KNOWLEDGE_ROUTING.md
   ```

2. **Understand Current State**:
   ```
   PROJECT_STATE.md → ACTIVE_TASK.md → EXECUTION_HISTORY.md (last 5 entries)
   ```

3. **Load Context**:
   ```
   Use KNOWLEDGE_ROUTING.md to identify task type
   Load relevant knowledge per KNOWLEDGE_INDEX.md
   Update AI_CONTEXT_SNAPSHOT.md
   ```

4. **Execute Task**:
   ```
   Follow AI_EXECUTION_PROTOCOL.md
   Run self-critique per AI_SELF_CRITIC.md
   Update all state files
   ```

### For Resuming Work

1. **Read State**:
   ```
   PROJECT_STATE.md → ACTIVE_TASK.md → EXECUTION_HISTORY.md
   ```

2. **Check Context**:
   ```
   AI_CONTEXT_SNAPSHOT.md → CONTEXT_TRANSFER.md (if exists)
   ```

3. **Continue**:
   ```
   Follow AI_EXECUTION_PROTOCOL.md
   ```

### For Switching AI Instances

1. **Before Switching**:
   ```
   Complete current work
   Update all state files
   Create CONTEXT_TRANSFER.md
   ```

2. **After Switching**:
   ```
   Read CONTEXT_TRANSFER.md
   Verify state files match
   Continue from ACTIVE_TASK.md
   ```

---

## 🔄 WORKFLOW

### Standard Task Execution

```
1. Read PROJECT_STATE.md + ACTIVE_TASK.md
2. Load context per KNOWLEDGE_ROUTING.md
3. Create execution plan
4. Execute per AI_EXECUTION_PROTOCOL.md
5. Self-critique per AI_SELF_CRITIC.md
6. Update PROJECT_STATE.md + ACTIVE_TASK.md
7. Log in EXECUTION_HISTORY.md
8. Persist knowledge if applicable
9. Generate next task (if autonomous)
```

### Autonomous Mode

```
1. Complete current task
2. Read MASTER_PLAN.md
3. Compare desired vs current state
4. Generate next task per AI_PLANNING_ENGINE.md
5. Update ACTIVE_TASK.md
6. Continue to execution
```

---

## 📊 STATE FILES RELATIONSHIP

```
MASTER_PLAN.md (Desired State)
    ↓
PROJECT_STATE.md (Current State)
    ↓
ACTIVE_TASK.md (Current Task)
    ↓
AI_EXECUTION_PROTOCOL.md (Execution)
    ↓
AI_SELF_CRITIC.md (Quality Check)
    ↓
EXECUTION_HISTORY.md (Logging)
    ↓
PROJECT_STATE.md (Update)
    ↓
(Repeat)
```

---

## 🎓 KEY CONCEPTS

### Autonomous Development
AI continuously plans and executes tasks without waiting for instructions, following MASTER_PLAN.md and updating state.

### Self-Criticism
AI evaluates its own work using Staff Engineer perspective before considering tasks complete.

### Knowledge Routing
AI loads only relevant knowledge based on task type, not reading entire repository.

### State Synchronization
All AI instances share same state files, ensuring continuity across sessions.

### Knowledge Persistence
Learnings and patterns are preserved in KNOWLEDGE_PERSISTENCE.md for future reference.

---

## ⚠️ IMPORTANT RULES

1. **Never read entire repository** - Use KNOWLEDGE_ROUTING.md
2. **Always read state files first** - PROJECT_STATE.md + ACTIVE_TASK.md
3. **Always run self-critique** - No task complete without critique
4. **Always update state** - After every task completion
5. **Always log work** - EXECUTION_HISTORY.md is the memory
6. **Always coordinate** - Check MULTI_AI_COORDINATION.md when switching

---

## 🔍 TROUBLESHOOTING

### State Seems Inconsistent
→ Read EXECUTION_HISTORY.md to reconstruct state

### Missing Context
→ Read AI_CONTEXT_SNAPSHOT.md + KNOWLEDGE_PERSISTENCE.md

### Task Unclear
→ Read MASTER_PLAN.md + PROJECT_STATE.md + ACTIVE_TASK.md

### Knowledge Gap
→ Use KNOWLEDGE_ROUTING.md to identify what to load

### Conflict with Other Instance
→ Read MULTI_AI_COORDINATION.md for resolution

---

## 📈 SUCCESS METRICS

Track over time:
- **Task Completion Rate**: % of tasks completed successfully
- **Self-Critique Pass Rate**: % passing first critique
- **Knowledge Reuse**: Frequency of using KNOWLEDGE_PERSISTENCE.md
- **State Consistency**: Accuracy across AI instances
- **Autonomous Progress**: Tasks generated and completed autonomously

---

## 🔗 RELATED DOCUMENTATION

- `docs-ai-context/KNOWLEDGE_INDEX.md` - AI context navigation
- `docs-devops/DEVOPS_KNOWLEDGE_INDEX.md` - DevOps knowledge navigation
- `docs-ai-context/cursor-system-promt.md` - Cursor-specific instructions
- `docs-ai-context/ai-safety-workflow.md` - Safety workflow

---

This system enables continuous, autonomous, high-quality development with seamless coordination across multiple AI instances.
