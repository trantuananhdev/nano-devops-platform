# Tổng quan — TeenCare AI System (Parent Copilot)

## Mục tiêu sản phẩm

Sau mỗi buổi coaching 1-on-1 (30–60 phút), hệ thống tự động tạo:

- **Insights grounded**: quan sát tin cậy, có quote làm bằng chứng
- **Recommendations actionable**: hành động cụ thể + thời điểm + kỳ vọng
- **Delivery**: gửi cho phụ huynh trong **\<5 phút** sau session

## Vấn đề cần giải

- Không có tóm tắt sau buổi học → phụ huynh mất kết nối với thực tế ở nhà
- Mentor ghi chú thủ công → không scale
- AI output không ổn định / hallucination → mất trust (high-stakes)
- Đề xuất quá chung chung → phụ huynh không biết làm gì
- Transcript thô noisy → downstream analysis sai

## Nguyên tắc thiết kế cốt lõi

- **Simple first, extend later**: Phase 1 ship nhanh, không over-engineer
- **Single LLM call**: giảm latency/cost, tránh error chain
- **Validation bắt buộc**: không tin LLM 100%
- **Failure \> Hallucination**: sai nguy hiểm hơn thiếu insight → trả rỗng khi thiếu evidence
- **Feedback loop**: optimize theo “parent action rate” (outcome), không chỉ metric nội bộ

## Pipeline (high level)

1) Step 1 — Pre-processing & Speaker Diarization  
2) Step 2 — Context Assembly (3-layer RAG)  
3) Step 3 — Single Structured LLM Call (temp=0, JSON schema)  
4) Step 4 — Validation & Guardrails (semantic grounding check, judge for high-risk)  
5) Step 5 — Delivery (push/mobile)

Chi tiết: `docs/01-architecture.md`.

