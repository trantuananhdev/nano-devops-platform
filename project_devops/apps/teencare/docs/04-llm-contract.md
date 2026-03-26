# LLM Contract — Prompting + Output Schema

## Design goal

- Output **không chung chung** và **grounded**.
- 1 call duy nhất, `temperature=0`, JSON schema “hard”.

## Output Schema (bắt buộc)

```json
{
  "insights": [
    {
      "observation": "string",
      "evidence": "string",
      "pattern_match": "string"
    }
  ],
  "risk_level": "low",
  "risk_reasoning": "string",
  "recommendations": [
    {
      "action": "string",
      "timing": "string",
      "expected_outcome": "string"
    }
  ],
  "confidence": "high"
}
```

## Hard constraints (prompt rules)

- Mỗi `insights[].observation` phải có `evidence` là **quote trực tiếp** từ Layer 3 (transcript hôm nay).
- Không thêm entity/sự kiện không xuất hiện trong transcript hoặc profile.
- Recommendations phải **cụ thể**:
  - bắt đầu bằng động từ hành động (VD: “Hỏi…”, “Nhắn…”, “Thống nhất…”)
  - có **timing** (VD: “tối nay”, “trước bữa tối”, “cuối tuần này”)
  - mô tả outcome quan sát được

## Example good vs bad (chuẩn hóa)

- Bad:
  - Insight: “Teen có vẻ bị stress”
  - Rec: “Hãy tạo không gian cởi mở”

- Good:
  - Insight: “Teen overload lịch → khó chịu”: evidence: `[TEEN: 'vướng ba lịch một lúc luôn... khó chịu chứ']`
  - Rec: “Tối nay trước bữa tối hỏi con: ‘Tuần này lịch có thay đổi gì không?’”

## Model configuration (Phase 1)

- `temperature`: 0
- `max_output_tokens`: đủ cho JSON (không quá dài)
- `stop`: không cần nếu model hỗ trợ structured JSON mode

## Prompt versioning

Mỗi lần cập nhật prompt/schema:

- bump `prompt_version`
- log kèm output + validation result
- A/B test 20% traffic trước khi rollout toàn phần

