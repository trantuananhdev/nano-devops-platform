# CONTEXT TRANSFER PROTOCOL
🔄 Handoff Between AI Instances & Accounts

This file is created when switching between AI instances (Cursor/GPT/Gemini) or Cursor accounts to ensure seamless continuity.

---

## WHEN TO CREATE THIS FILE

- Switching from Cursor to GPT/Gemini
- Switching from GPT/Gemini to Cursor
- Switching between Cursor accounts
- Resuming work after a break
- Handing off to another developer/AI

---

## TEMPLATE

```markdown
# Context Transfer - [YYYY-MM-DD HH:MM]

**From**: [Previous AI Instance/Account Name]
**To**: [New AI Instance/Account Name]
**Reason**: [Why switching - e.g., "Account rotation", "Tool preference", "Resuming work"]

---

## CURRENT STATE SNAPSHOT

### Project Phase
**Current Phase**: [Phase name from MASTER_PLAN.md]
**Phase Progress**: [X%]
**Next Milestone**: [Milestone name]

### Active Task
**Task**: [Task name from ACTIVE_TASK.md]
**Status**: [COMPLETED/IN_PROGRESS/BLOCKED]
**Started**: [Timestamp]
**Expected Completion**: [If known]

### System Completion Status
- Architecture: [X%]
- Infrastructure: [X%]
- Services: [X%]
- CI/CD: [X%]
- Observability: [X%]
- Documentation: [X%]

---

## RECENT WORK CONTEXT

### Last Completed Tasks
1. [Task 1] - [Date] - [Brief summary]
2. [Task 2] - [Date] - [Brief summary]
3. [Task 3] - [Date] - [Brief summary]

### Current Focus
[What the project is currently focused on]

### Recent Decisions
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]
- [Decision 3]: [Rationale]

### Current Challenges
- [Challenge 1]: [Status]
- [Challenge 2]: [Status]
- [Challenge 3]: [Status]

---

## KNOWLEDGE CONTEXT

### Recently Loaded Documentation
- `docs-ai-context/[file]`: [Why loaded]
- `docs-devops/[file]`: [Why loaded]
- `ai-system/[file]`: [Why loaded]

### Key Knowledge Domains Active
- [Domain 1]: [Why relevant]
- [Domain 2]: [Why relevant]

### Important Patterns in Use
- [Pattern 1]: [Where used]
- [Pattern 2]: [Where used]

---

## CODE CONTEXT

### Recently Modified Files
- `path/to/file1`: [What changed]
- `path/to/file2`: [What changed]

### Active Development Areas
- [Area 1]: [Status]
- [Area 2]: [Status]

### Pending Changes
- [Change 1]: [Status]
- [Change 2]: [Status]

---

## STATE FILES STATUS

### PROJECT_STATE.md
**Last Updated**: [Timestamp]
**Key Updates**: [Summary]

### ACTIVE_TASK.md
**Last Updated**: [Timestamp]
**Current Task**: [Task name]

### EXECUTION_HISTORY.md
**Last Entry**: [Date]
**Recent Activity**: [Summary]

### AI_CONTEXT_SNAPSHOT.md
**Last Updated**: [Timestamp]
**Snapshot Valid**: ✅/❌

---

## NEXT STEPS

### Immediate Actions Required
1. [Action 1]
2. [Action 2]
3. [Action 3]

### Short-term Goals (Next 1-3 Tasks)
1. [Goal 1]
2. [Goal 2]
3. [Goal 3]

### Medium-term Goals (Current Phase)
- [Goal 1]
- [Goal 2]
- [Goal 3]

---

## WARNINGS & CAUTIONS

### Known Issues
- [Issue 1]: [Impact] - [Mitigation]
- [Issue 2]: [Impact] - [Mitigation]

### Things to Watch
- [Thing 1]: [Why important]
- [Thing 2]: [Why important]

### Blockers
- [Blocker 1]: [Status]
- [Blocker 2]: [Status]

---

## VERIFICATION CHECKLIST

Before starting work, new instance should verify:

- [ ] PROJECT_STATE.md matches this snapshot
- [ ] ACTIVE_TASK.md is current
- [ ] EXECUTION_HISTORY.md is up to date
- [ ] All referenced files exist
- [ ] No conflicting work in progress
- [ ] Knowledge context is clear

---

## HANDOFF COMPLETION

**Handoff Created By**: [AI Instance/Account]
**Handoff Created At**: [Timestamp]
**Handoff Received By**: [AI Instance/Account]
**Handoff Received At**: [Timestamp]

**Verification**: ✅/❌
**Ready to Proceed**: ✅/❌

---

## NOTES FOR NEXT INSTANCE

[Any additional context, tips, or important information]

---

**IMPORTANT**: After reading this handoff, the new instance should:
1. Verify all state files match
2. Read EXECUTION_HISTORY.md for recent work
3. Load context per KNOWLEDGE_ROUTING.md
4. Update AI_CONTEXT_SNAPSHOT.md
5. Continue from ACTIVE_TASK.md

---

This file should be kept updated and referenced when resuming work.
