# Security & Privacy (PII / Safety)

## Data classification

- **PII/PHI-like**: tên, trường, địa chỉ, số điện thoại, thông tin sức khỏe tinh thần nhạy cảm
- **Transcript**: coi như dữ liệu nhạy cảm mặc định

## Consent & access

- Bảo đảm có **consent** hợp lệ cho ghi âm/transcribe và xử lý AI.
- Principle of least privilege:
  - Mentor chỉ truy cập sessions của teen họ phụ trách
  - Phụ huynh chỉ truy cập session của con họ

## Storage controls

- Encrypt at rest (DB + object storage)
- Encrypt in transit (TLS)
- Tách raw transcript và derived outputs để dễ kiểm soát retention

## Logging & redaction

- Không log raw transcript ở level info/debug trong production.
- Nếu cần log để debug:
  - redaction PII
  - sampling + access-controlled log store

## Auditability

Mọi output cần truy vết:

- `session_id`
- input stats (turn counts, quality_score)
- context layers used (hash/fingerprint)
- model_id + prompt_version
- validation results (grounding scores, judge verdict)

## Safety policy (high-stakes)

- Nếu output `risk_level="high"`:
  - judge +/or mentor review
  - delivery có thể “gated” (chỉ gửi sau confirm)

## Data retention (baseline)

- Raw transcript: lưu dài hạn cho audit theo policy nội bộ
- Derived outputs: lưu để tracking + eval
- Feedback: lưu để cải tiến prompt (ẩn danh nếu có thể)

