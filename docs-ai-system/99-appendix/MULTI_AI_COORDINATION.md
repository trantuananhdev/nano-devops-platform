# MULTI-AI COORDINATION SYSTEM
🤖 Cursor + GPT + Gemini Coordination Protocol

This system enables seamless coordination between multiple AI instances (Cursor, GPT, Gemini) working on the same project, ensuring continuity, knowledge sharing, and consistent quality.

---

## 1. CORE PRINCIPLE

**All AI instances share the same knowledge base and state.**

Every AI instance must:
- Read current state before starting
- Update state after completing work
- Share knowledge through persistent files
- Maintain consistency across sessions

---

## 2. AI INSTANCE IDENTIFICATION

Each AI instance must identify itself:

```markdown
**AI Instance**: [Cursor/GPT/Gemini]
**Session ID**: [Timestamp or unique ID]
**Account**: [If switching Cursor accounts]
**Previous Session**: [Last session ID if resuming]
```

This is logged in EXECUTION_HISTORY.md for each task.

---

## 3. STATE SYNCHRONIZATION PROTOCOL

### 3.1 ON STARTUP (Every AI Instance)

**MANDATORY READING ORDER:**

1. **PROJECT_STATE.md** - Current project status
2. **ACTIVE_TASK.md** - Current active task
3. **EXECUTION_HISTORY.md** - Recent work history
4. **AI_CONTEXT_SNAPSHOT.md** - Last known context state
5. **KNOWLEDGE_PERSISTENCE.md** - Accumulated knowledge

**Purpose**: Understand where project is and what needs to be done next.

### 3.2 BEFORE TASK EXECUTION

**Check for conflicts:**
- Is ACTIVE_TASK.md already assigned to another instance?
- Are there uncommitted changes in EXECUTION_HISTORY.md?
- Is there a lock file indicating work in progress?

**If conflict detected:**
- Read EXECUTION_HISTORY.md to see what's happening
- Wait or coordinate via comments
- Never overwrite another instance's work

### 3.3 DURING TASK EXECUTION

**Update progress:**
- Mark task as IN_PROGRESS in ACTIVE_TASK.md
- Log start time in EXECUTION_HISTORY.md
- Create lock file if long-running task

**Format:**
```markdown
**Status**: IN_PROGRESS
**Started**: [ISO 8601 timestamp]
**AI Instance**: [Cursor/GPT/Gemini]
**Estimated Duration**: [if known]
```

### 3.4 AFTER TASK COMPLETION

**MANDATORY UPDATES:**

1. **EXECUTION_HISTORY.md**:
   - Log completion
   - Record what was done
   - Include self-critique results
   - Note any issues or improvements

2. **PROJECT_STATE.md**:
   - Update completion status
   - Update phase progress
   - Update system metrics

3. **ACTIVE_TASK.md**:
   - Mark task as COMPLETED
   - Generate next task (if autonomous mode)
   - Or mark as PENDING_USER_INPUT

4. **AI_CONTEXT_SNAPSHOT.md**:
   - Update with current context state
   - Record key decisions made
   - Note knowledge loaded

5. **KNOWLEDGE_PERSISTENCE.md**:
   - Add new learnings
   - Update patterns
   - Record solutions to problems

---

## 4. KNOWLEDGE SHARING PROTOCOL

### 4.1 KNOWLEDGE PERSISTENCE

All AI instances contribute to KNOWLEDGE_PERSISTENCE.md:

**When to add:**
- Discovered a better pattern
- Solved a recurring problem
- Found important context
- Learned from mistakes

**Format:**
```markdown
## [Date] - [AI Instance] - [Topic]

**Context**: [What was the situation]
**Learning**: [What was learned]
**Application**: [How to apply this]
**Related Files**: [Files that contain this knowledge]
```

### 4.2 CONTEXT TRANSFER

When switching AI instances or accounts:

**Create CONTEXT_TRANSFER.md:**
```markdown
# Context Transfer - [Date]

**From**: [Previous AI Instance/Account]
**To**: [New AI Instance/Account]
**Reason**: [Why switching]

## Current State
- **Phase**: [Current phase]
- **Active Task**: [Current task]
- **Progress**: [% complete]

## Key Context
- **Recent Decisions**: [List]
- **Current Challenges**: [List]
- **Next Steps**: [List]

## Knowledge Loaded
- [List of docs that were loaded]

## Warnings
- [Any issues to be aware of]
```

---

## 5. COORDINATION PATTERNS

### 5.1 PARALLEL WORK (Different Tasks)

**Allowed when:**
- Tasks are independent
- No shared files modified
- Clear boundaries defined

**Protocol:**
- Each instance works on separate task
- Update separate sections in PROJECT_STATE.md
- Merge results carefully
- Review for conflicts

### 5.2 SEQUENTIAL WORK (Same Task)

**When one instance finishes, next continues:**

**Protocol:**
1. First instance completes and logs
2. Second instance reads EXECUTION_HISTORY.md
3. Second instance continues from checkpoint
4. Maintain continuity in approach

### 5.3 COLLABORATIVE WORK (Same Task)

**When multiple instances work together:**

**Protocol:**
- Use EXECUTION_HISTORY.md as coordination point
- Each instance logs its contribution
- Review each other's work via self-critique
- Merge changes carefully

---

## 6. CONFLICT RESOLUTION

### 6.1 FILE CONFLICTS

**If multiple instances modify same file:**

**Resolution:**
1. Read both versions
2. Understand intent of each
3. Merge intelligently
4. Document merge in EXECUTION_HISTORY.md
5. Run self-critique on merged result

### 6.2 STATE CONFLICTS

**If PROJECT_STATE.md conflicts:**

**Resolution:**
1. Read EXECUTION_HISTORY.md to understand timeline
2. Merge state updates chronologically
3. Resolve contradictions based on latest work
4. Document resolution

### 6.3 TASK CONFLICTS

**If ACTIVE_TASK.md conflicts:**

**Resolution:**
1. Check EXECUTION_HISTORY.md for task status
2. If task completed → generate next task
3. If task in progress → wait or coordinate
4. If task abandoned → mark and create new

---

## 7. QUALITY CONSISTENCY

### 7.1 SHARED STANDARDS

All AI instances must:
- Follow same platform laws
- Use same self-critique system
- Maintain same code quality
- Update same documentation

### 7.2 QUALITY CHECKS

Before completing work:
- Run self-critique (AI_SELF_CRITIC.md)
- Verify platform law compliance
- Check documentation updates
- Ensure state consistency

### 7.3 KNOWLEDGE VALIDATION

When reading others' work:
- Verify it follows standards
- Check for issues via critique
- Document concerns if found
- Suggest improvements

---

## 8. ACCOUNT SWITCHING PROTOCOL

### 8.1 BEFORE SWITCHING CURSOR ACCOUNTS

**Create handoff document:**
```markdown
# Handoff - [Date]

**From Account**: [Account name]
**To Account**: [Account name]

## Current Status
[Copy from PROJECT_STATE.md]

## Active Work
[Copy from ACTIVE_TASK.md]

## Recent Context
[Copy from AI_CONTEXT_SNAPSHOT.md]

## Important Notes
[Any warnings or important info]
```

### 8.2 AFTER SWITCHING

**New account must:**
1. Read handoff document
2. Read PROJECT_STATE.md
3. Read EXECUTION_HISTORY.md
4. Verify state consistency
5. Continue from checkpoint

---

## 9. EXECUTION HISTORY FORMAT

EXECUTION_HISTORY.md structure:

```markdown
# Execution History

## [Date] - [Task Name]

**AI Instance**: [Cursor/GPT/Gemini]
**Session ID**: [ID]
**Status**: [COMPLETED/IN_PROGRESS/FAILED]

### Execution
[What was done]

### Self-Critique
[Critique results]

### State Updates
[What changed in PROJECT_STATE.md]

### Knowledge Added
[What was learned]

### Next Steps
[What should happen next]

### Handoff Notes
[If switching instances]
```

---

## 10. CHECKPOINT SYSTEM

### 10.1 CHECKPOINT CREATION

Create checkpoints at:
- End of each phase
- After major milestones
- Before switching instances
- After critical decisions

### 10.2 CHECKPOINT FORMAT

```markdown
# Checkpoint - [Date] - [Milestone]

**AI Instance**: [Instance]
**Phase**: [Current phase]
**Progress**: [%]

## State Snapshot
[Key state information]

## Knowledge Snapshot
[Key knowledge at this point]

## Decisions Made
[Important decisions]

## Next Phase
[What comes next]

## Files Changed
[List of files]

## Verification
✅ All checks passed
```

### 10.3 CHECKPOINT RESTORATION

When resuming from checkpoint:
1. Read checkpoint document
2. Verify files match checkpoint state
3. Load knowledge from checkpoint
4. Continue from checkpoint point

---

## 11. COMMUNICATION PROTOCOL

### 11.1 ASYNCHRONOUS COMMUNICATION

AI instances communicate via files:
- EXECUTION_HISTORY.md: Task logs
- KNOWLEDGE_PERSISTENCE.md: Learnings
- AI_CONTEXT_SNAPSHOT.md: Context state
- Comments in code: Inline notes

### 11.2 SYNCHRONIZATION POINTS

Synchronize at:
- Task completion
- Phase completion
- Checkpoint creation
- Account switching

---

## 12. BEST PRACTICES

### For All AI Instances:
✅ Always read state before starting
✅ Always update state after completing
✅ Always log in EXECUTION_HISTORY.md
✅ Always run self-critique
✅ Always document learnings

### For Parallel Work:
✅ Work on independent tasks
✅ Avoid modifying same files
✅ Coordinate via EXECUTION_HISTORY.md
✅ Review for conflicts

### For Sequential Work:
✅ Read previous work thoroughly
✅ Maintain continuity
✅ Build on previous work
✅ Document handoffs

---

## 13. FAILURE MODES

### 13.1 LOST STATE

**If state seems inconsistent:**
1. Read all EXECUTION_HISTORY.md entries
2. Reconstruct state from history
3. Update PROJECT_STATE.md
4. Document reconstruction

### 13.2 MISSING CONTEXT

**If context seems missing:**
1. Read AI_CONTEXT_SNAPSHOT.md
2. Read KNOWLEDGE_PERSISTENCE.md
3. Load relevant docs per KNOWLEDGE_ROUTING.md
4. Update AI_CONTEXT_SNAPSHOT.md

### 13.3 CONFLICTING WORK

**If work conflicts:**
1. Stop immediately
2. Read EXECUTION_HISTORY.md
3. Understand both versions
4. Resolve intelligently
5. Document resolution

---

## 14. SUCCESS METRICS

Track over time:
- **Coordination Success Rate**: % of seamless handoffs
- **Conflict Rate**: Frequency of conflicts
- **Knowledge Sharing**: Amount of knowledge persisted
- **State Consistency**: Accuracy of state across instances

---

This system ensures that multiple AI instances can work together seamlessly, maintaining continuity and quality throughout the project lifecycle.
