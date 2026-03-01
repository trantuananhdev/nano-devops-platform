# Contribution Guide

This document describes how to safely contribute changes to the Nano DevOps Platform while respecting **GitOps**, **immutable deployment**, and the **6GB single-node constraint**.

---

## Rules

- **All changes via Pull Request (PR)**
  - No direct pushes to `main`.
  - All PRs must pass CI before merge.
- **Small batch, trunk-based**
  - Ưu tiên PR nhỏ, tập trung, với tổng số dòng thay đổi khoảng **≤ 300 lines** (theo `delivery.small_batch.max_lines`).
  - Feature branch nên sống **< 24 giờ** trước khi merge vào `main` (theo `delivery.trunk_based.max_branch_lifetime_hours`). 
- **Update documentation**
  - Any behavioural or architectural change must be reflected in `/docs`.
  - New services must include architecture notes and, where relevant, runbook entries.
- **Follow folder structure**
  - Place application services, infra, and scripts in the appropriate directories as described in `system-context.md` and `filesystem-layout.md`.

---

## GitOps Workflow (Contributor View)

```text
Create small, focused branch (lifetime < 24h)
  ↓
Implement change (code + config + docs), keep diff ≈ ≤ 300 lines
  ↓
Push branch + open PR
  ↓
CI: lint → build → test → package → security & law checks
  ↓
Review & iterate
  ↓
Merge to main
  ↓
CD: deploy via scripts/pipelines
```

- Contributors must not modify runtime state on the VM by hand; if an emergency fix is performed, it must be:
  - Captured in a Git change,
  - Deployed via the normal pipeline as soon as possible.
  - Follow-up PRs vẫn phải tuân thủ luật small batch và trunk-based ở trên.

---

## Expectations for Changes

- **Respect constraints**
  - Any new component must fit within the 6GB RAM budget.
  - Avoid adding heavy dependencies without clear justification.
- **Keep the system observable**
  - New services should expose metrics and logs that integrate with the existing monitoring stack.
- **Keep operations automated**
  - Repetitive steps should be implemented as scripts or CI/CD jobs, not copied shell commands.

---

## AI-Assisted Contributions

- AI tools (e.g. Cursor) may help:
  - Generate code and configuration,
  - Draft documentation,
  - Propose CI/CD updates.
- They must follow:
  - `ai-coding-guidelines.md`,
  - `system-context.md`,
  - `gitops-architecture.md`.

Human reviewers remain responsible for ensuring that AI-generated changes comply with the platform strategy and constraints.
