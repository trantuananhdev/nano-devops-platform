# API Contract — Input/Output

Tài liệu này là “source of truth” cho contract giữa các service trong pipeline.

## 9.1 Input Schema (Ingest)

```json
{
  "session_id": "uuid",
  "teen_id": "uuid",
  "raw_transcript": "string (noisy, from audio-to-text)",
  "session_date": "ISO8601",
  "family_goals": ["cải thiện kỷ luật", "giảm screen time"]
}
```

### Notes

- `session_id`: nếu client không có, ingest service tạo và trả lại.
- `raw_transcript`: có thể chứa filler, câu đứt, không có speaker labels.

## Step 1 Output (Preprocess + Diarization)

```json
{
  "session_id": "uuid",
  "turns": [
    { "speaker": "TEEN", "text": "vướng ba lịch một lúc luôn", "index": 3 },
    { "speaker": "MENTOR", "text": "Con có bao giờ chia sẻ với mẹ không?", "index": 4 }
  ],
  "quality_score": 0.87
}
```

## Step 2 Output (Context Assembly)

```json
{
  "session_id": "uuid",
  "context": {
    "layer_1_profile": "string (<= ~100 tokens)",
    "layer_2_history": ["string chunk", "string chunk"],
    "layer_3_session": ["[TEEN] ...", "[MENTOR] ..."]
  },
  "token_budget": {
    "profile_tokens": 100,
    "history_tokens": 300,
    "session_tokens": 800
  }
}
```

## 9.2 Final Output Schema (Parent Copilot)

```json
{
  "session_id": "uuid",
  "insights": [
    {
      "observation": "Teen bị overload lịch học gây cảm xúc tiêu cực",
      "evidence": "[TEEN: 'vướng ba lịch một lúc luôn']",
      "pattern_match": "Lặp lại từ tuần 1-2: stress học tập"
    }
  ],
  "risk_level": "low",
  "risk_reasoning": "string",
  "recommendations": [
    {
      "action": "Hỏi con về lịch học trước bữa tối",
      "timing": "Tối nay",
      "expected_outcome": "Tạo habit con tự chia sẻ thay vì giữ trong lòng"
    }
  ],
  "confidence": "high"
}
```

### Contract rules (hard)

- `insights[].evidence`: **bắt buộc** là quote từ transcript (đã clean).
- `risk_reasoning`: **bắt buộc**.
- `confidence`:
  - `high`: transcript đủ dài + grounding tốt
  - `medium`: có insight nhưng evidence yếu/ít
  - `low_signal`: không đủ dữ liệu hoặc chất lượng thấp

## Failure output (insufficient data)

Khi `turns < 10` hoặc `quality_score < 0.5`:

```json
{
  "session_id": "uuid",
  "insights": [],
  "risk_level": "low",
  "risk_reasoning": "insufficient data",
  "recommendations": [],
  "confidence": "low_signal",
  "flag": "insufficient_data"
}
```

