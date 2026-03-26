# Project Checklist — TeenCare Parent Copilot

Quy ước trạng thái:

- `[ ]` todo
- `[~]` doing
- `[x]` done
- `[!]` blocked / needs decision

## Bạn đang ở đâu?

- Current milestone: **Phase 1 (MVP ~2 tuần)**
- Current focus (điền 1 dòng): `[x] Integrate Gemini Flash 2.5 + Dockerization`
- Next up (điền 1 dòng): `[ ] Evaluation & Fine-tuning prompts based on real usage`

---

## Phase 0 — Repo & docs baseline

- [x] Docs overview/architecture/contracts/guardrails/eval/runbook/security/windows setup
- [x] Agent playbook (`AGENTS.md`)
- [x] Cursor rules (`.cursor/rules/teencare-parent-copilot.mdc`)
- [x] Chọn stack implement MVP: **Python**
- [x] Chọn LLM provider + embeddings provider cho production: **Google Gemini Flash 2.5**

---

## Phase 1 — MVP (ship nhanh, reliable)

### Step 1 — Pre-processing & diarization (rule-based)

- [x] Define input/output types cho `turns[]` + `quality_score`
- [x] Implement cleaner: remove filler, normalize whitespace, fix broken sentences (heuristic)
- [x] Implement rule-based diarization:
  - [x] Detect turn separators (ví dụ: `>>`, pauses markers nếu có)
  - [x] Heuristic speaker classify (question -> mentor; colloquial short -> teen)
  - [x] Speaker fallback: `UNKNOWN`
- [x] Compute `quality_score` (coverage + ambiguity rate)
- [x] Golden samples cho step 1 (raw -> clean turns) (demo_001/002/003)

### Step 2 — Context assembly (Layer 1 + Layer 3)

- [x] Layer 1: teen `profile_summary` loader (<= ~100 tokens)
- [x] Layer 3: session turns formatter (speaker tags + turn index)
- [x] Token budget guard (hard cap; truncate safely)
- [ ] (Optional) History top-k by date (chưa cần embeddings)

### Step 3 — Single structured LLM call

- [x] Implement JSON schema enforcement (strict)
- [x] Prompt versioning (`prompt_version`)
- [x] temp=0 enforced (config)
- [x] Log request stats (MVP: `_meta`)
- [x] Integrate **Gemini Flash 2.5** as the primary LLM provider

### Step 4 — Validation & guardrails

- [x] JSON schema validation (required fields)
- [x] Semantic grounding check:
  - [ ] [!] Choose embedding model/provider (MVP dùng evidence-match + trigram fallback)
  - [x] Chunk transcript for grounding (MVP: per session line)
  - [x] Threshold baseline (start 0.75) + tuning plan
- [x] Retry/fallback behaviors theo `docs/05-validation-guardrails.md` (MVP: retry loop + block)
- [x] “Insufficient data” path:
  - [x] `turns < 10` OR `quality_score < 0.5` => empty + `flag="insufficient_data"`

### Step 5 — Delivery (parent)

- [x] Define delivery payload (title + bullets + actions) (MVP renderer)
- [x] Push/in-app integration stub (Noop provider)
- [~] SLA handling: queue + retries + fallback `stale_data` (MVP có `stale_data` cache; queue/retry service còn thiếu)

### Observability (MVP minimum)

- [x] Metrics: latency per step, schema validity, grounding pass rate, hallucination flags (MVP: `_meta` + dashboard script)
- [x] Logs correlated by `session_id` (MVP: `_meta` + `session_id`)
- [x] Basic dashboard query (local) (`scripts/local_dashboard.py`)

---

## Phase 2 — Quality & scale (sau 1 tháng)

### RAG improvements

- [ ] Rolling summary generator (3–4 bullets) + store
- [ ] Embedding index cho transcript/summary chunks
- [ ] Semantic retrieval (cosine similarity)

### Step 1 upgrade (LLM-assisted diarization)

- [x] Trigger rule: confidence thấp => send short snippet (~500 tokens) for classification only (MVP: ambiguous turn text classification)
- [x] Cache result by `session_id`

### High-risk handling

- [ ] LLM-as-judge cho `risk_level=high` (YES/NO + reason)
- [ ] Mentor review workflow cho `needs_review`

### Feedback loop

- [ ] Mentor feedback capture + weekly review
- [ ] Parent feedback capture (helpful/irrelevant/too generic)
- [ ] Update few-shot examples + A/B test 20% traffic

---

## Phase 3 — Optimization (sau 3 tháng)

- [ ] Topic clustering + recency weighting + rerank theo family goals
- [ ] Cost optimization (model routing, batching)
- [ ] Fine-tune nhỏ (nếu sustained high cost) + eval harness
- [ ] Advanced monitoring: drift detection by prompt/model fingerprint

---

## Open decisions (ghi rõ để unblock)

- [ ] LLM provider + model(s) cho structured output
- [ ] Embeddings provider + dimension + cost plan
- [ ] Data store lựa chọn (Postgres? Firestore? S3-compatible? Vector DB?)
- [ ] Delivery channel (FCM/APNs? SMS? email?) + UX format

