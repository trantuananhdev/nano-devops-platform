# ADR-0001: Single LLM call + mandatory validation

## Status

Accepted

## Context

Hệ thống cần tạo insight/action cho phụ huynh trong bối cảnh high-stakes (tâm lý thiếu niên).
Naive chaining nhiều LLM calls tăng latency/cost và tạo “error chain”. Đồng thời LLM có thể hallucinate nên cần safety net.

## Decision

- Dùng **1 structured LLM call** (temp=0, JSON schema bắt buộc).
- Sau đó chạy **Validation & Guardrails** (semantic grounding check; judge cho high-risk).
- Nếu không đủ evidence: **return empty + flag**, ưu tiên an toàn hơn completeness.

## Consequences

- (+) Giảm latency/cost, đơn giản hóa vận hành
- (+) Dễ quan sát và audit (1 output + validation log)
- (-) Prompt phải được thiết kế rất chặt (schema + grounding constraints)
- (-) Validation cần embeddings/judge (tăng complexity vừa phải) nhưng bắt buộc

