# Data Model — Storage & Entities

Mục tiêu data model: (1) audit được, (2) hỗ trợ RAG/rolling summary, (3) phục vụ eval + feedback loop.

## Entities

### `teens`

- `teen_id` (uuid, PK)
- `created_at`
- `display_name` (optional)
- `age` (optional)
- `timezone` (optional)
- `profile_summary` (text) — Layer 1 context (<= ~100 tokens)
- `profile_updated_at`

### `families`

- `family_id` (uuid, PK)
- `created_at`
- `goals` (json array of strings)

### `sessions`

- `session_id` (uuid, PK)
- `teen_id` (FK)
- `family_id` (FK)
- `session_date` (datetime)
- `source` (enum: `upload`, `zoom`, `phone_recording`, ...)
- `status` (enum: `ingested`, `processed`, `delivered`, `needs_review`, `failed`)

### `raw_transcripts`

- `session_id` (PK/FK)
- `raw_text` (long text)
- `language` (default `vi`)
- `ingested_at`
- `redaction_applied` (bool)

### `clean_turns`

- `session_id` (FK)
- `turn_index` (int)
- `speaker` (enum: `TEEN`, `MENTOR`, `PARENT`, `UNKNOWN`)
- `text` (text)
- `primary key`: (`session_id`, `turn_index`)

### `diarization_results`

- `session_id` (PK/FK)
- `quality_score` (float 0..1)
- `method` (enum: `rule_based`, `llm_assisted`)
- `meta` (json: confidence per turn, heuristics hits, etc.)

### `rolling_summaries`

Sau mỗi session, lưu summary 3–4 bullet cho lịch sử.

- `teen_id` (FK)
- `session_id` (FK)
- `summary_bullets` (json array of strings)
- `created_at`

### `ai_outputs`

- `session_id` (PK/FK)
- `output_json` (json)
- `model_id` (string)
- `prompt_version` (string)
- `temperature` (float; Phase 1 luôn 0)
- `created_at`

### `validation_results`

- `session_id` (FK)
- `schema_valid` (bool)
- `grounding_scores` (json: per-insight score)
- `hallucination_flag` (bool)
- `judge_verdict` (optional: `YES`/`NO`)
- `judge_reason` (optional)
- `final_decision` (enum: `deliver`, `deliver_partial`, `block_needs_review`)
- `created_at`

### `parent_feedback`

- `session_id` (FK)
- `parent_id` (optional)
- `recommendation_rating` (enum: `helpful`, `irrelevant`, `too_generic`)
- `notes` (text, optional)
- `created_at`

### `mentor_feedback`

- `session_id` (FK)
- `mentor_id` (optional)
- `insight_rating` (enum: `accurate`, `partially`, `inaccurate`)
- `notes` (text, optional)
- `created_at`

## Indexing (gợi ý)

- `sessions(teen_id, session_date desc)`
- `clean_turns(session_id, turn_index)`
- `rolling_summaries(teen_id, created_at desc)`

## Data retention (gợi ý)

- Raw transcript: lưu dài hạn cho audit (có thể mã hóa/segmented retention)
- Logs: tách PII, lưu theo policy (xem `docs/08-security-privacy.md`)

