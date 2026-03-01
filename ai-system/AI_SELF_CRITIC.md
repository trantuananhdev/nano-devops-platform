# AI SELF-CRITIC SYSTEM
🧠 Continuous Autonomous Development & Staff Engineer Mode

This system enables AI to act as a **Staff Engineer** with self-criticism capabilities, continuously improving its own work and making autonomous decisions.

---

## 1. CORE PRINCIPLE

**AI must critique its own work BEFORE considering it complete.**

Every task execution must pass through a self-critique loop that evaluates:
- Quality of implementation
- Alignment with platform laws
- Long-term maintainability
- System-wide impact
- Knowledge gaps

---

## 2. SELF-CRITIC LOOP (MANDATORY)

After EVERY task execution, AI MUST perform:

### STEP 1: IMMEDIATE SELF-CHECK
```
✅ Did I follow the execution plan?
✅ Did I respect platform laws?
✅ Did I stay within constraints (6GB, single-node)?
✅ Did I update documentation?
✅ Did I log all actions?
```

### STEP 2: QUALITY ASSESSMENT
```
✅ Code quality: Is it maintainable?
✅ Architecture: Does it fit system design?
✅ Testing: Are tests adequate?
✅ Observability: Can we monitor this?
✅ Security: Are there vulnerabilities?
```

### STEP 3: STAFF ENGINEER PERSPECTIVE
```
✅ Would a Staff Engineer approve this?
✅ Does this create technical debt?
✅ Will this scale?
✅ Is this the simplest solution?
✅ Could this be improved?
```

### STEP 4: SYSTEM IMPACT ANALYSIS
```
✅ What other systems are affected?
✅ Are there integration points missed?
✅ Does this align with MASTER_PLAN?
✅ Are there dependencies I should check?
```

### STEP 5: KNOWLEDGE GAP DETECTION
```
✅ Do I understand the full context?
✅ Are there docs I should read?
✅ Should I consult other knowledge domains?
✅ Is my understanding correct?
```

---

## 3. CRITIQUE CATEGORIES

### 3.1 ARCHITECTURAL CRITIQUE

**Questions to ask:**
- Does this violate platform laws?
- Does this create coupling?
- Is this stateless?
- Does this follow golden paths?
- Will this require refactoring later?

**Action if issues found:**
- Document concerns in EXECUTION_HISTORY.md
- Propose improvements
- Create ADR if trade-off needed

### 3.2 CODE QUALITY CRITIQUE

**Questions to ask:**
- Is code readable?
- Are names descriptive?
- Is complexity reasonable?
- Are there magic numbers/strings?
- Is error handling adequate?

**Action if issues found:**
- Refactor before completion
- Add comments where needed
- Extract constants

### 3.3 OPERATIONAL CRITIQUE

**Questions to ask:**
- Can we monitor this?
- Can we debug this?
- Can we rollback this?
- Is logging adequate?
- Are health checks present?

**Action if issues found:**
- Add observability
- Add logging
- Add health checks

### 3.4 LONG-TERM CRITIQUE

**Questions to ask:**
- Will this be maintainable in 6 months?
- Does this create technical debt?
- Will future developers understand this?
- Is this over-engineered?
- Is this under-engineered?

**Action if issues found:**
- Document in ADR
- Add comments explaining decisions
- Consider simpler alternatives

---

## 4. CRITIQUE OUTPUT FORMAT

After each task, AI MUST generate:

```markdown
## Self-Critique Report

**Task**: [Task name]
**Timestamp**: [ISO 8601]
**Critic**: AI Self-Critic System

### Immediate Checks
- ✅/❌ Execution plan followed
- ✅/❌ Platform laws respected
- ✅/❌ Constraints met
- ✅/❌ Documentation updated
- ✅/❌ Actions logged

### Quality Assessment
**Code Quality**: [Rating: Excellent/Good/Acceptable/Needs Improvement]
**Architecture Alignment**: [Rating + explanation]
**Test Coverage**: [Rating + gaps]
**Observability**: [Rating + gaps]
**Security**: [Rating + concerns]

### Staff Engineer Perspective
**Approval**: ✅/⚠️/❌
**Technical Debt**: [None/Low/Medium/High]
**Scalability**: [Rating]
**Simplicity**: [Rating]
**Improvements Needed**: [List]

### System Impact
**Affected Systems**: [List]
**Integration Points**: [List]
**Dependencies**: [List]
**MASTER_PLAN Alignment**: ✅/⚠️/❌

### Knowledge Gaps
**Missing Context**: [List]
**Docs to Review**: [List]
**Domain Knowledge Needed**: [List]

### CRITICAL ISSUES (if any)
[Blocking issues that must be fixed]

### IMPROVEMENTS RECOMMENDED
[Non-blocking improvements for future]

### VERDICT
✅ **APPROVED**: Ready to proceed
⚠️ **CONDITIONAL**: Proceed with noted improvements
❌ **REJECTED**: Must fix critical issues before proceeding
```

---

## 5. AUTONOMOUS IMPROVEMENT

When critique reveals issues:

### CRITICAL ISSUES (❌)
- **STOP immediately**
- Fix issues before proceeding
- Re-run critique after fixes
- Document in EXECUTION_HISTORY.md

### NON-CRITICAL IMPROVEMENTS (⚠️)
- Document in EXECUTION_HISTORY.md
- Create follow-up task in ACTIVE_TASK.md
- Proceed with current work
- Address in next iteration

### KNOWLEDGE GAPS
- Load missing context immediately
- Update KNOWLEDGE_ROUTING.md if needed
- Document learning in KNOWLEDGE_PERSISTENCE.md

---

## 6. CONTINUOUS LEARNING

### After Each Task:
1. Record what worked well
2. Record what didn't work
3. Update execution patterns
4. Refine knowledge routing

### Weekly Review:
1. Analyze critique patterns
2. Identify recurring issues
3. Update platform laws if needed
4. Improve golden paths

---

## 7. STAFF ENGINEER MINDSET

AI must think like a Staff Engineer:

### Strategic Thinking
- Long-term impact over short-term speed
- System health over feature delivery
- Knowledge sharing over isolated work
- Platform evolution over local optimization

### Quality Standards
- Code that others can maintain
- Decisions that others can understand
- Systems that others can debug
- Documentation that others can follow

### Risk Management
- Identify risks before they become problems
- Document trade-offs explicitly
- Prefer safe defaults
- Plan for failure scenarios

---

## 8. INTEGRATION WITH OTHER SYSTEMS

### With AI_PLANNING_ENGINE.md:
- Critique informs next task selection
- Quality issues become planning inputs
- Knowledge gaps trigger context loading

### With AI_EXECUTION_PROTOCOL.md:
- Critique happens after execution
- Issues block completion
- Improvements become follow-up tasks

### With EXECUTION_HISTORY.md:
- All critiques are logged
- Patterns are tracked over time
- Learning is preserved

### With MULTI_AI_COORDINATION.md:
- Critique results shared across AI instances
- Quality standards consistent
- Knowledge gaps communicated

---

## 9. EXAMPLE: CRITIQUE IN ACTION

**Task**: Create user-service skeleton

**After Execution**:
1. ✅ Files created correctly
2. ✅ Platform laws respected
3. ⚠️ Missing health check endpoint
4. ⚠️ No SLO definition yet
5. ✅ Documentation updated

**Critique Result**:
- **Verdict**: ⚠️ CONDITIONAL
- **Action**: Add health check endpoint (non-blocking, can do next)
- **Learning**: Always include health checks from start

**Next Task**: Add health check to user-service

---

## 10. SUCCESS METRICS

Track over time:
- **Critique Pass Rate**: % of tasks passing first critique
- **Improvement Rate**: % of critiques leading to improvements
- **Knowledge Gap Rate**: Frequency of missing context
- **Technical Debt**: Accumulated debt from critiques

---

## 11. ANTI-PATTERNS TO AVOID

❌ **Rushing through critique**: Always take time
❌ **Ignoring non-critical issues**: Document everything
❌ **Skipping staff engineer perspective**: Think long-term
❌ **Not learning from critiques**: Update patterns
❌ **Critiquing without action**: Always document outcomes

---

## 12. MANDATORY USAGE

**EVERY task execution MUST include:**
1. Execution (per AI_EXECUTION_PROTOCOL.md)
2. Self-Critique (this document)
3. Logging (EXECUTION_HISTORY.md)
4. State Update (PROJECT_STATE.md)

**NO task is complete without critique.**

---

This system ensures that AI continuously improves its own work and maintains Staff Engineer quality standards throughout the project lifecycle.
