# Validation & Guardrails

## Tại sao bắt buộc

LLM có thể hallucinate kể cả prompt tốt. Trong context tâm lý thiếu niên, **insight sai → hành động sai** của phụ huynh. Do đó validation là safety net bắt buộc.

## 6.2 Semantic Grounding Check

Không dùng string-match đơn giản vì tiếng Việt hay paraphrase. Dùng semantic similarity giữa insight và các chunk transcript.

Pseudo-code:

```python
def validate_grounding(insight, transcript_chunks, threshold=0.75):
    insight_vec = embed(insight["observation"])
    max_sim = max(cosine_sim(insight_vec, embed(c)) for c in transcript_chunks)
    if max_sim < threshold:
        raise HallucinationError(insight)
    return max_sim
```

### Grounding policy

- Nếu insight fail grounding: **retry 1 lần** với constraint chặt hơn.
- Nếu vẫn fail: loại insight đó, hoặc block delivery tùy mức độ.

## 6.3 LLM-as-Judge (high-stakes)

Khi `risk_level="high"`:

- Gửi **insight + transcript** cho judge prompt:
  - “Insight này có được support bởi transcript không? Trả lời YES/NO + reason.”
- Log verdict + reason.
- Chỉ bật cho high-risk (~20%) để kiểm soát cost.

## 6.4 Retry & Fallback Strategy (chuẩn hóa)

| Tình huống | Action | Fallback |
|---|---|---|
| Hallucination detected | Retry 1 (temp=0, “DO NOT invent”) | Return partial + `flag="needs_review"` |
| Schema invalid | Retry với schema reminder | Return empty insights |
| Timeout > 5s | Trả cached last session summary | `flag="stale_data"` |
| Grounding score thấp | Hạ confidence, giữ insight + flag | Mentor review |

## Circuit breaker (hallucination burst)

Nếu hallucination rate > 10%/ngày:

- Tắt auto-delivery → chuyển sang mentor review
- Phân tích pattern trigger (transcript ngắn, topic mới, dialect)
- Update prompt/threshold
- Shadow mode chạy song song trước khi bật lại

