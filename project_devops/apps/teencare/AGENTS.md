# Agent Playbook — TeenCare Parent Copilot

Tài liệu này mô tả cách một AI-agent (hoặc dev) “tự hành” trong repo: ưu tiên **an toàn**, **grounded**, và **ship nhanh** theo đúng hệ thống v1.0.

## Mission

- Xây dựng hệ thống tạo **insight + action cụ thể cho phụ huynh** sau mỗi session.
- Mọi claim/insight **phải grounded vào transcript**; thiếu dữ liệu thì **trả rỗng + flag**.

## Non-negotiables (Safety)

- Không “bịa” thông tin ngoài transcript / hồ sơ teen.
- Khi dữ liệu không đủ (transcript quá ngắn/noisy, `quality_score` thấp): **return empty** với `confidence="low_signal"` + `flag="insufficient_data"`.
- Với `risk_level="high"`: luôn có **double-check** (LLM-as-judge hoặc quy trình human review), và log đầy đủ cho audit.

## Repo workflow (Doc-first)

- Nếu chưa có code, **ưu tiên hoàn thiện docs** trong `docs/` trước khi scaffold service.
- Mọi thay đổi kiến trúc quan trọng phải thêm **ADR**: `docs/adr/ADR-xxxx-*.md`.

## Implementation milestones (khi bắt đầu code)

- **MVP (2 tuần)**:
  - Step 1: clean + rule-based diarization + `quality_score`
  - Step 2: context assembly Layer 1 + Layer 3 (History đơn giản theo date)
  - Step 3: single LLM call (temp=0) + JSON schema
  - Step 4: validation (semantic grounding check) + retry/fallback
  - Step 5: delivery (push)

## Logging & observability requirements

- Log theo `session_id`, gồm:
  - input stats: số turns, `quality_score`, token size context
  - output stats: schema validity, grounding scores, flags
  - latency: p50/p95/p99 từng bước
  - cost per session (ước tính)

## “Definition of done” cho mỗi module

- Có docs tương ứng trong `docs/`
- Có contract rõ ràng (I/O schema)
- Có metric + alert + fallback
- Có test plan tối thiểu (unit + golden samples)

