# TeenCare AI System (Parent Copilot) — Production Docs

Mục tiêu: **sau mỗi buổi học, tự động tạo insight tin cậy + action cụ thể cho phụ huynh** trong \<5 phút.

Repo này hiện tập trung vào **docs + vận hành** cho hệ thống “Parent Copilot”, theo bản mô tả TDD v1.0.

MVP hiện đã có:

- Pipeline end-to-end chạy local (Windows)
- Hybrid diarization (rule + classifier cho turn mơ hồ)
- Guardrails + fallback (`insufficient_data`, `needs_review`, `stale_data`)

## Quick start (Windows)

- Tài liệu tổng quan: `docs/00-overview.md`
- Kiến trúc pipeline: `docs/01-architecture.md`
- API contract (input/output JSON): `docs/02-api-contract.md`
- Data model (DB tables/objects): `docs/03-data-model.md`
- Prompt + schema output: `docs/04-llm-contract.md`
- Validation & guardrails: `docs/05-validation-guardrails.md`
- Evaluation & metrics: `docs/06-evaluation.md`
- Runbook production: `docs/07-runbook.md`
- Security & privacy (PII/consent/audit): `docs/08-security-privacy.md`
- Hướng dẫn dev trên Windows: `docs/09-dev-setup-windows.md`
- Chạy MVP demo end-to-end: `docs/10-mvp-how-to-run.md`

## “AI tự hành” trong repo này

- Quy ước để AI-agent làm việc ổn định: `.cursor/rules/teencare-parent-copilot.mdc`
- Hướng dẫn tác vụ cho agent (doc-first, safety-first): `AGENTS.md`

