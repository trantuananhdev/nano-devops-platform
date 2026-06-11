# AI EXECUTION PROTOCOL
⚙️ Standardized Task Execution Process

This protocol defines the mandatory steps for executing any task, ensuring consistency, quality, and traceability.

---

## 1. PRE-EXECUTION PHASE

### 1.1 STATE ORIENTATION (MANDATORY)

**Read in order:**
1. `PROJECT_STATE.md` - Current project status
2. `ACTIVE_TASK.md` - Current task to execute
3. `EXECUTION_HISTORY.md` - Recent work (last 5 entries)
4. `AI_CONTEXT_SNAPSHOT.md` - Current context state

**Purpose**: Understand current state and what needs to be done.

### 1.2 KNOWLEDGE ROUTING (MANDATORY)

**Follow KNOWLEDGE_ROUTING.md:**
1. Identify task type
2. Load relevant knowledge domains
3. Verify context is sufficient
4. Update AI_CONTEXT_SNAPSHOT.md

**If context insufficient:**
- Load additional docs per KNOWLEDGE_ROUTING.md
- Document what was loaded
- Update AI_CONTEXT_SNAPSHOT.md

### 1.3 PLANNING (MANDATORY)

**Create execution plan:**
1. Break task into steps (max 5 steps)
2. Identify files to create/modify
3. Estimate lines of code (max 300 lines)
4. Identify platform laws to apply
5. Check for dependencies

**Document plan in ACTIVE_TASK.md:**
```markdown
### Execution Plan
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

### 1.4 PRE-FLIGHT CHECKS (MANDATORY)

**Verify:**
- ✅ Task is clear and understood
- ✅ Context is sufficient
- ✅ Plan is feasible
- ✅ Constraints are respected
- ✅ No conflicts with other work

**If any check fails:**
- Stop and resolve issue
- Update ACTIVE_TASK.md with blocker
- Document in EXECUTION_HISTORY.md

---

## 2. EXECUTION PHASE

### 2.1 EXECUTION LOGGING (MANDATORY)

**Start logging in EXECUTION_HISTORY.md:**
```markdown
## [Date] - [Time] - [Task Name]

**AI Instance**: [Instance]
**Session ID**: [ID]
**Status**: IN_PROGRESS
**Phase**: [Phase]

### Execution Plan
[Plan from ACTIVE_TASK.md]

### Execution Started
[Timestamp]
```

### 2.2 FILE OPERATIONS

**For each file operation:**
1. Read existing file (if modifying)
2. Understand current state
3. Make minimal necessary changes
4. Log change in EXECUTION_HISTORY.md
5. Verify change is correct

**Log format:**
```markdown
### Files Changed
- `path/to/file`: [CREATED/MODIFIED/DELETED] - [Brief description]
```

### 2.3 PLATFORM LAW COMPLIANCE

**For each change:**
1. Identify applicable platform laws
2. Verify compliance
3. Document compliance in log
4. Fix if non-compliant

**Log format:**
```markdown
### Platform Laws Applied
- delivery.small_batch: ✅ (150 lines changed)
- reliability.observability: ✅ (metrics added)
```

### 2.4 CONSTRAINTS VERIFICATION

**Continuously verify:**
- ✅ Memory constraint (6GB)
- ✅ Single-node constraint
- ✅ Small batch (≤300 lines)
- ✅ GitOps compliance
- ✅ Immutable deployment

**If constraint violated:**
- Stop immediately
- Document violation
- Propose solution
- Get approval before proceeding

---

## 3. POST-EXECUTION PHASE

### 3.1 SELF-CRITIQUE (MANDATORY)

**Follow AI_SELF_CRITIC.md:**
1. Run immediate self-check
2. Perform quality assessment
3. Apply staff engineer perspective
4. Analyze system impact
5. Detect knowledge gaps

**Document results in EXECUTION_HISTORY.md:**
```markdown
### Self-Critique Results
[Results from AI_SELF_CRITIC.md]
```

### 3.2 VERIFICATION (MANDATORY)

**Verify completion:**
- ✅ All planned steps completed
- ✅ Files changed as planned
- ✅ Platform laws complied
- ✅ Constraints respected
- ✅ Documentation updated
- ✅ Self-critique passed

**If verification fails:**
- Fix issues
- Re-run verification
- Document fixes

### 3.3 STATE UPDATES (MANDATORY)

**Update PROJECT_STATE.md:**
- Update phase progress
- Update completion status
- Update metrics
- Update next steps

**Update ACTIVE_TASK.md:**
- Mark task as COMPLETED
- Generate next task (if autonomous)
- Or mark as PENDING_USER_INPUT

**Update AI_CONTEXT_SNAPSHOT.md:**
- Update loaded knowledge
- Update active decisions
- Update current understanding

### 3.4 KNOWLEDGE PERSISTENCE (MANDATORY)

**Update KNOWLEDGE_PERSISTENCE.md if:**
- New pattern discovered
- Problem solved
- Important learning occurred
- Better approach found

**Format:**
```markdown
## [Date] - [Topic]

**Discovered By**: [AI Instance]
**Context**: [When/why]
**Category**: [Category]

### Knowledge
[What learned]

### Application
[How to apply]
```

### 3.5 EXECUTION LOG COMPLETION (MANDATORY)

**Complete EXECUTION_HISTORY.md entry:**
```markdown
### Execution Summary
[What was done]

### Files Changed
[Complete list]

### Self-Critique Results
[Results]

### Platform Laws Applied
[List]

### State Updates
[What changed]

### Knowledge Learned
[New learnings]

### Issues Encountered
[Problems and solutions]

### Next Steps
[What should happen next]

**Status**: COMPLETED
```

---

## 4. ERROR HANDLING

### 4.1 EXECUTION ERRORS

**If error during execution:**
1. Stop immediately
2. Document error in EXECUTION_HISTORY.md
3. Analyze root cause
4. Propose solution
5. Update ACTIVE_TASK.md with error status

### 4.2 VERIFICATION FAILURES

**If verification fails:**
1. Document failure
2. Identify root cause
3. Fix issues
4. Re-run verification
5. Document resolution

### 4.3 BLOCKERS

**If blocked:**
1. Document blocker
2. Identify resolution path
3. Update ACTIVE_TASK.md as BLOCKED
4. Create follow-up task if needed
5. Document in EXECUTION_HISTORY.md

---

## 5. QUALITY GATES

### 5.1 PRE-EXECUTION GATES

**Must pass before starting:**
- ✅ State understood
- ✅ Context sufficient
- ✅ Plan clear
- ✅ Constraints respected
- ✅ No conflicts

### 5.2 DURING EXECUTION GATES

**Must maintain during execution:**
- ✅ Platform laws complied
- ✅ Constraints respected
- ✅ Small batch maintained
- ✅ Quality standards met

### 5.3 POST-EXECUTION GATES

**Must pass before completion:**
- ✅ Self-critique passed
- ✅ Verification passed
- ✅ State updated
- ✅ Knowledge persisted
- ✅ Logs complete

---

## 6. AUTONOMOUS MODE

### 6.1 WHEN AUTONOMOUS

**If ACTIVE_TASK.md says "AUTONOMOUS":**
1. Complete current task
2. Run self-critique
3. Update state
4. Generate next task per AI_PLANNING_ENGINE.md
5. Update ACTIVE_TASK.md
6. Continue to next task

### 6.2 TASK GENERATION

**Follow AI_PLANNING_ENGINE.md:**
1. Read MASTER_PLAN.md
2. Compare desired vs current state
3. Identify gap
4. Generate smallest useful task
5. Update ACTIVE_TASK.md

---

## 7. MULTI-AI COORDINATION

### 7.1 BEFORE STARTING

**Check MULTI_AI_COORDINATION.md:**
1. Verify no conflicts
2. Check for locks
3. Read recent EXECUTION_HISTORY.md
4. Understand current state

### 7.2 DURING EXECUTION

**Coordinate via:**
- EXECUTION_HISTORY.md for logs
- ACTIVE_TASK.md for task status
- AI_CONTEXT_SNAPSHOT.md for context

### 7.3 AFTER COMPLETION

**Update for next instance:**
- Complete EXECUTION_HISTORY.md
- Update all state files
- Create CONTEXT_TRANSFER.md if switching

---

## 8. MANDATORY CHECKLIST

**Before starting ANY task:**
- [ ] Read PROJECT_STATE.md
- [ ] Read ACTIVE_TASK.md
- [ ] Read EXECUTION_HISTORY.md (last 5 entries)
- [ ] Load context per KNOWLEDGE_ROUTING.md
- [ ] Create execution plan
- [ ] Run pre-flight checks

**During execution:**
- [ ] Log every file change
- [ ] Verify platform law compliance
- [ ] Verify constraints continuously
- [ ] Maintain small batch

**After execution:**
- [ ] Run self-critique
- [ ] Verify completion
- [ ] Update PROJECT_STATE.md
- [ ] Update ACTIVE_TASK.md
- [ ] Update AI_CONTEXT_SNAPSHOT.md
- [ ] Update KNOWLEDGE_PERSISTENCE.md (if applicable)
- [ ] Complete EXECUTION_HISTORY.md
- [ ] Generate next task (if autonomous)

---

## 9. SUCCESS CRITERIA

**Task is complete when:**
- ✅ All execution steps done
- ✅ Self-critique passed
- ✅ Verification passed
- ✅ State files updated
- ✅ Logs complete
- ✅ Knowledge persisted (if applicable)

---

This protocol ensures consistent, high-quality execution across all tasks and AI instances.
