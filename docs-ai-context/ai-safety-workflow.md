# AI Safety Workflow

This document defines the **safety workflow** for AI-assisted development on the Nano DevOps Platform. It ensures that AI-generated changes are **logged, verified, and reviewed** before affecting production, while clearly separating **AI responsibilities** from **human decision-making**.

---

## 1. Core Safety Principles

- **AI executes, humans decide**: AI performs tasks, logs actions, and verifies results. Humans control Git operations (branching, merging, deployment).
- **Nothing touches production without review**: All changes go through a reviewable branch and explicit human approval.
- **Full audit trail**: Every AI action must be logged and traceable.
- **Fail-safe defaults**: If verification fails, AI must stop and report, not proceed.

---

## 2. Workflow Overview

```text
Human: Select task from ai-platform-build-plan.md
  ↓
Human: Create feature branch (e.g., feat/phase1-task1)
  ↓
AI: Read context (platform-laws, final_devops_context, etc.)
  ↓
AI: Execute task (create/modify files)
  ↓
AI: Log all actions (what was changed, why, which laws applied)
  ↓
AI: Self-verify (constraints, laws, small batch)
  ↓
AI: Generate summary report
  ↓
Human: Review changes (diff, logs, summary)
  ↓
Human: Run local tests (if applicable)
  ↓
Human: Merge to main (if approved)
  ↓
CI/CD: Automated validation & deployment
```

---

## 3. AI Responsibilities (What AI Must Do)

### 3.1 Before Starting Any Task

AI **must**:

1. **Load required context** (in order):
   - `ai-context/platform-vision.md`
   - `ai-context/platform-laws.yaml`
   - `ai-context/law-context-mapping.yaml`
   - `final_devops_context.md` (relevant sections)
   - Domain-specific docs as needed

2. **Identify affected sections**:
   - Which `final_devops_context` section(s) are impacted
   - Which platform laws apply (delivery, reliability, observability, security, infra)

3. **Propose execution plan** (3–5 steps, ≤ 300 lines total):
   - List files to create/modify
   - Explain why each change is needed
   - Confirm small batch compliance

### 3.2 During Execution

AI **must**:

1. **Execute changes**:
   - Create/modify files as planned
   - Follow golden-path templates when applicable
   - Respect platform laws and constraints

2. **Log every action**:
   - What file was created/modified
   - What content was added/changed (brief summary)
   - Which platform law(s) this change enforces
   - Estimated resource impact (if applicable)

3. **Self-verify before completion**:
   - ✅ Constraint fit (6GB RAM, single-node)
   - ✅ GitOps compliance (all changes in Git, no manual-only steps)
   - ✅ Immutable deployment (no runtime patching)
   - ✅ Observability coverage (metrics/logs if new service)
   - ✅ Documentation updated (if needed)
   - ✅ Small batch (≤ 300 lines changed)

### 3.3 After Execution

AI **must**:

1. **Generate execution summary**:
   - List all files changed (with paths)
   - Summary of changes (what was done)
   - Laws applied and verified
   - Resource impact assessment (if applicable)
   - Any warnings or trade-offs

2. **Report verification status**:
   - ✅ All checks passed, or
   - ⚠️ Warnings (non-blocking), or
   - ❌ Blocking issues (must stop)

3. **Never**:
   - Checkout branches
   - Commit changes
   - Push to remote
   - Merge branches
   - Deploy to production

---

## 4. Human Responsibilities (What Humans Must Do)

### 4.1 Before AI Execution

Human **must**:

1. **Select task** from `ai-platform-build-plan.md`
2. **Create feature branch**:
   ```bash
   git checkout -b feat/phase1-task1
   ```
3. **Provide clear prompt** to AI:
   - Reference the task from build plan
   - Specify any additional context or constraints
   - Confirm AI should proceed

### 4.2 After AI Execution

Human **must**:

1. **Review AI-generated summary**:
   - Check execution log
   - Verify files changed match expectations
   - Confirm laws were applied correctly

2. **Inspect changes**:
   ```bash
   git status
   git diff
   ```
   - Review file-by-file changes
   - Verify no unintended modifications
   - Check for hardcoded secrets, resource violations, etc.

3. **Run local verification** (if applicable):
   - Lint/format checks
   - Local tests
   - Docker Compose validation (if infra changes)

4. **Decide on merge**:
   - ✅ **Approve**: Commit and prepare for merge
   - ⚠️ **Request changes**: Ask AI to fix issues
   - ❌ **Reject**: Discard branch, start over

5. **Commit and merge** (if approved):
   ```bash
   git add .
   git commit -m "feat: [task description]"
   git push origin feat/phase1-task1
   # Create PR, review, merge to main
   ```

---

## 5. Execution Log Format

AI must generate a log in this format for every task:

```markdown
## AI Execution Log

**Task**: [Task name from build plan]
**Branch**: [Current branch name - AI reads from git, does not create]
**Timestamp**: [ISO 8601 format]

### Context Loaded
- ✅ ai-context/platform-vision.md
- ✅ ai-context/platform-laws.yaml
- ✅ final_devops_context.md (sections: [list])

### Laws Applied
- delivery.small_batch (max_lines: 300)
- [other applicable laws]

### Execution Plan
1. [Step 1]
2. [Step 2]
...

### Files Changed
- `path/to/file1`: Created/Modified - [brief description]
- `path/to/file2`: Modified - [brief description]

### Verification Results
- ✅ Constraint fit: [explanation]
- ✅ GitOps compliance: [explanation]
- ✅ Immutable deployment: [explanation]
- ✅ Observability: [explanation if applicable]
- ✅ Small batch: [X lines changed, ≤ 300]

### Resource Impact
- Memory: [estimate if applicable]
- CPU: [estimate if applicable]

### Warnings
- [Any non-blocking warnings]

### Blocking Issues
- [Any issues that prevent merge - if none, state "None"]

### Summary
[2-3 sentence summary of what was done and why it's safe]
```

---

## 6. Safety Checks (AI Must Verify)

Before reporting completion, AI must verify:

### 6.1 Constraint Compliance
- ✅ Total memory impact ≤ 6GB (if adding services)
- ✅ No Kubernetes/service mesh introduced
- ✅ No per-service databases (unless justified)
- ✅ Single-node compatible

### 6.2 Law Compliance
- ✅ Small batch (≤ 300 lines changed)
- ✅ Trunk-based (branch lifetime < 24h - human responsibility, but AI notes)
- ✅ Unit tests present (if code changes)
- ✅ SLO/telemetry configured (if new service)
- ✅ Security scans pass (if CI changes)

### 6.3 GitOps Compliance
- ✅ All changes represented in Git
- ✅ No manual-only configuration paths
- ✅ No direct VM edits suggested
- ✅ Rollback path exists (previous image version)

### 6.4 Documentation
- ✅ Relevant docs updated (if behavior changes)
- ✅ Architecture diagrams updated (if structure changes)
- ✅ Runbooks updated (if operational changes)

---

## 7. Failure Modes and Responses

### 7.1 AI Detects Blocking Issue

**AI must**:
- Stop execution immediately
- Report the issue in execution log
- Explain why it's blocking
- Suggest remediation (if possible)

**Human must**:
- Review the blocking issue
- Decide: fix, workaround, or abandon task

### 7.2 Verification Fails

**AI must**:
- Report which check(s) failed
- Explain impact
- Suggest fixes

**Human must**:
- Review failures
- Request AI to fix, or fix manually
- Re-run verification

### 7.3 Resource Budget Exceeded

**AI must**:
- Stop before creating resource-heavy components
- Report estimated usage vs. budget
- Suggest alternatives or ADR

**Human must**:
- Review resource analysis
- Approve constraint change (via ADR), or request redesign

---

## 8. Integration with CI/CD

After human merges to `main`:

1. **CI pipeline runs**:
   - Lint, build, test, package
   - Security & law checks
   - If any stage fails → human must fix

2. **CD pipeline runs** (if CI passes):
   - Deploy to single-node VM
   - Health checks
   - Rollback if health checks fail

3. **AI is not involved** in CI/CD execution (automated)

---

## 9. Example: Complete Workflow

### Step 1: Human Creates Branch
```bash
git checkout -b feat/phase1-task1-skeleton-repo
```

### Step 2: Human Provides Prompt
```
Execute Phase 1 - Task 1 from ai-platform-build-plan.md:
- Create repo skeleton (apps/, infra/, scripts/, etc.)
- Follow repo-structure.yaml and filesystem-layout.md
- Keep changes ≤ 300 lines
- Generate execution log
```

### Step 3: AI Executes
- Loads context
- Creates directories and stub files
- Generates execution log
- Self-verifies
- Reports completion

### Step 4: Human Reviews
```bash
git status
git diff
# Review execution log
# Verify no violations
```

### Step 5: Human Commits (if approved)
```bash
git add .
git commit -m "feat: init platform skeleton (phase1-task1)"
git push origin feat/phase1-task1-skeleton-repo
```

### Step 6: Human Creates PR
- Review PR diff
- CI runs automatically
- Merge if CI passes

### Step 7: CD Deploys (automated)
- CD pipeline runs
- Deploys to VM
- Health checks verify

---

## 10. Best Practices

### For Humans
- **Always review execution log** before committing
- **Test locally** before merging (if applicable)
- **Keep branches short-lived** (< 24h per platform laws)
- **One task per branch** (small batch principle)

### For AI
- **Never skip verification steps**
- **Always log actions** (even if trivial)
- **Report warnings** (don't hide issues)
- **Stop on blocking issues** (don't proceed hoping human will catch it)

---

## 11. Emergency Procedures

### If AI Makes Unintended Changes

1. **Human stops AI** (if still running)
2. **Review git diff**:
   ```bash
   git diff
   git status
   ```
3. **Discard unwanted changes**:
   ```bash
   git checkout -- <file>
   # or
   git reset --hard HEAD
   ```
4. **Restart task** with clearer prompt

### If Changes Are Merged but Cause Issues

1. **Rollback via GitOps**:
   ```bash
   git revert <commit-hash>
   git push
   ```
2. **CD automatically redeploys** previous version
3. **Investigate** root cause (was it AI error or missing context?)

---

## 12. Continuous Improvement

- **After each task**: Review execution log quality
- **After each phase**: Assess if workflow needs adjustment
- **Update this workflow** if patterns emerge (via PR, following same workflow)

---

This workflow ensures that **AI assists safely** while **humans maintain control** over all Git operations and production deployments.
