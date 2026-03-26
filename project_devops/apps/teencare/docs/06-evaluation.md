# Evaluation Strategy

## 3 lớp đánh giá

### Lớp 1 — Automated (mỗi output)

| Metric | Cách đo | Target |
|---|---|---|
| Grounding score | % insights có similarity > 0.75 | > 90% |
| Schema validity | JSON valid + đủ required fields | 100% |
| Specificity proxy | % recommendation > 15 tokens | > 80% |
| Hallucination flag | entity không có trong transcript | < 5% |
| Latency | end-to-end | < 5 giây |

### Lớp 2 — Human feedback (weekly)

- Mentor: `Accurate / Inaccurate / Partially`
- Parent: `Helpful / Irrelevant / Too generic`

Target: \<10% insights bị mentor mark `Inaccurate`.

### Lớp 3 — Outcome tracking (monthly) — North Star

**Parent Action Rate** = % phụ huynh thực sự làm theo recommendation trong tuần tiếp theo.

Nếu metric nội bộ tốt nhưng action rate thấp → output chưa actionable → phải iterate.

## Improvement loop

1) Bad output flagged (mentor/parent)  
2) Label + phân loại failure mode  
3) Update few-shot/prompt rules/threshold  
4) A/B test 20% traffic  
5) Deploy nếu improved, rollback nếu không

## Golden set (khuyến nghị)

Tạo bộ “golden sessions” (ẩn danh) gồm:

- transcript dài/ngắn
- dialect/noise
- các topic phổ biến (stress học, screen time, xung đột gia đình, peer pressure)

Mỗi golden sample có expected:

- insights grounded
- recommendation cụ thể
- risk level hợp lý

