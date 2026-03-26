# Dev setup (Windows)

Mục tiêu: thiết lập môi trường để bắt đầu implement MVP theo docs (khi bạn muốn code).

## Prereqs

- Windows 10/11
- Python 3.11+ (hoặc Node.js nếu bạn chọn stack JS)
- Git (khuyến nghị, dù hiện repo chưa init)

## Suggested local structure (khi scaffold)

- `services/ingest/`
- `services/preprocess/`
- `services/orchestrator/` (LLM + validation)
- `services/delivery/`
- `shared/` (schemas, clients)
- `infra/` (docker, db, queues)

## Environment variables (baseline)

- `TEENCARE_ENV=dev`
- `LLM_PROVIDER=...`
- `LLM_API_KEY=...`
- `EMBEDDING_PROVIDER=...`
- `DB_URL=...`
- `PUSH_PROVIDER_KEY=...`

## Local run (concept)

Khi có code, ưu tiên:

- chạy từng step độc lập với sample transcript
- lưu output + validation logs vào local DB
- test “insufficient_data” và “hallucination detected” paths

## Golden samples

Tạo folder:

- `samples/raw/` (noisy)
- `samples/clean/` (expected clean turns)
- `samples/expected/` (expected final JSON)

## Next step

Nếu bạn muốn, mình có thể scaffold code MVP (Windows-friendly) dựa trên docs này:

- JSON schemas
- preprocess rule-based
- context assembly L1+L3
- single LLM call + validation (embedding-based)
- output renderer cho mobile push

