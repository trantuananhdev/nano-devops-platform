# MVP Implementation Notes (current scaffold)

## 1) Vì sao output demo_001 bị `insufficient_data`

Theo safety policy trong docs:

- Nếu `turns < 10` **hoặc** `quality_score < 0.5` → trả rỗng + `flag="insufficient_data"`

Bạn có thể override để debug bằng CLI:

```bash
python -m teencare_ai --input samples/raw/session_demo_001.json --min-turns 3
```

## 2) Grounding check trong MVP

Production design nói “semantic similarity”. MVP hiện dùng:

- **hard grounding**: nếu `evidence` xuất hiện verbatim trong transcript → score = 1.0
- **fallback**: trigram Jaccard cho `observation` vs từng dòng transcript

Điểm quan trọng: pipeline vẫn **không cho phép bịa evidence**; nếu evidence không có trong transcript, grounding sẽ tụt và bị block.

## 3) LLM thật

MVP chạy bằng `MockLLMClient` (deterministic). Khi bạn có gateway LLM structured-output:

- Implement endpoint nhận `{ context_text, temperature, strict, ... }`
- Trả JSON theo schema `src/teencare_ai/schemas/output.parent_copilot.schema.json`

Sau đó wire `HttpLLMClient` vào pipeline (đang để sẵn trong `src/teencare_ai/llm/client.py`).

## 4) Hybrid diarization (mới)

Step 1 hiện đã hỗ trợ cơ chế hybrid:

- Rule-based gán speaker + confidence cho từng turn
- Turn nào confidence thấp hơn ngưỡng (`diarization_unknown_threshold`) sẽ qua classifier lớp 2
- Kết quả classifier được cache theo `session_id + text` để không gọi lại

Artifacts:

- `src/teencare_ai/steps/step1_preprocess.py`
- `src/teencare_ai/llm/diarization_classifier.py`
- `src/teencare_ai/storage/diarization_cache.py`

## 5) stale_data fallback (mới)

Khi lỗi timeout ở bước LLM, pipeline có thể trả output gần nhất theo `teen_id`:

- Cache: `samples/runs/latest_output_by_teen.json`
- Flag output: `stale_data`

Điều này giúp giữ SLA delivery khi upstream model có sự cố ngắn hạn.

