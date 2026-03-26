# MVP How-to-run (Windows)

## 1) Cài dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

## 2) Chạy demo end-to-end

Demo “đủ turns” (không bị `insufficient_data`):

```bash
python -m teencare_ai --input samples/raw/session_demo_002.json
```

Demo “buổi thực tế” (JSON sample):

```bash
python -m teencare_ai --demo session_real_001
```

Demo “buổi thực tế” (import từ file `.txt`):

```bash
python -m teencare_ai --input samples/raw/session_real_001.txt --teen-id teen_demo_001 --family-goals "cải thiện giao tiếp với mẹ,giảm cáu kỉnh khi quá tải lịch"
```

Demo “buổi mẫu mới” (để so sánh 2 case):

```bash
python -m teencare_ai --demo session_sample_003
```

Demo “thiếu dữ liệu” (bị block theo safety policy `turns < 10`):

```bash
python -m teencare_ai --input samples/raw/session_demo_001.json
```

## 3) Ghi output ra file

```bash
python -m teencare_ai --input samples/raw/session_demo_002.json --output samples/expected/out.json
```

## 3.1) Lưu runs để xem dashboard local

```bash
python -m teencare_ai --input samples/raw/session_demo_002.json --output samples/runs/demo_002.json
python scripts/local_dashboard.py
```

## 4) Config knobs quan trọng (CLI)

- `--min-turns` (default 10)
- `--min-quality` (default 0.5)
- `--grounding-threshold` (default 0.75)

Ví dụ chạy “nới” min-turns để debug nhanh:

```bash
python -m teencare_ai --input samples/raw/session_demo_001.json --min-turns 3
```

## 5) LLM thật (tùy chọn)

MVP hiện dùng `MockLLMClient`. Nếu bạn có gateway LLM structured-output, bạn có thể wire `HttpLLMClient`
(xem `src/teencare_ai/llm/client.py`) và set:

- `TEENCARE_LLM_ENDPOINT`
- `TEENCARE_LLM_API_KEY` (optional)

