# Component Design — L4 System Design

> **Tầng L4: Chi tiết từng component quan trọng**
> **Audience:** Developer tự implement/maintain các component
> **Cập nhật:** 2026-06-13

---

## 1. Context Manager (`app/core/context_manager.py`)

### Vấn đề cần giải quyết
LLM có context limit (8192 tokens với gemma). Nếu session dài, conversation history vượt limit → LLM truncate hoặc trả 400 error.

FIFO naïve (drop oldest) gây mất reasoning quan trọng: failures, plan steps — những thứ LLM cần nhất để tránh lặp lỗi.

### Solution: Priority-based Eviction

```
MessagePriority Enum:
  CRITICAL (4) ── system prompt, first user message
  HIGH     (3) ── failures, reflections, critic verdicts
  MEDIUM   (2) ── planning, clarification exchanges
  LOW      (1) ── routine success observations
  MINIMAL  (0) ── long verbose dumps (>2000 chars assistant)

Scoring logic (score_message_priority):
  role==system          → CRITICAL
  role==user, index==0  → CRITICAL (task definition)
  content có fail/error → HIGH
  content có plan/step  → HIGH
  index >= 80% of total → MEDIUM (recency)
  content > 2000 chars  → MINIMAL (verbose)
  else                  → LOW

Eviction loop (fit_messages):
  1. Tính tokens hiện tại
  2. Nếu vượt limit: drop MINIMAL → LOW → MEDIUM (không bao giờ drop HIGH/CRITICAL)
  3. Nếu chỉ còn HIGH/CRITICAL mà vẫn vượt: truncate content message dài nhất
  4. Restore original order sau khi drop
```

### Metrics
```python
CONTEXT_TRUNCATIONS.labels(model=model).inc()  # Prometheus counter
```

---

## 2. Memory Retriever (`app/services/memory/retriever.py`)

### 3 loại retrieval

**a) Per-dossier (same session)**
```python
retrieve_relevant_memories(session, dossier_id, query, top_k, current_step)
  → Primary: ChromaDB query với WHERE dossier_id={id}
  → Fallback: PostgreSQL SELECT AgentMemory ORDER BY step DESC LIMIT k
```

**b) Cross-dossier (similar past dossiers)**
```python
retrieve_cross_dossier_memories(query, unit=None, risk_level=None, top_k, current_step)
  → ChromaDB query toàn collection, filter WHERE unit AND risk_level
  → Mục đích: học từ hồ sơ tương tự (cùng đơn vị, cùng mức rủi ro)
```

**c) Feedback lessons (negative learning)**
```python
retrieve_feedback_lessons(query, unit=None, top_k, session)
  → ChromaDB collection: hdtv_feedback_lessons
  → Fallback: PostgreSQL AgentFeedback WHERE feedback_type IN ('reject', 'adjust')
  → Inject vào planner: "Tránh các lỗi này trong kế hoạch"
```

### Composite Scoring Algorithm
```python
def _score_chunk(chunk, current_step):
    # Convert Chroma distance [0-2] to relevance [0-1]
    relevance = max(0.0, 1.0 - (distance / 2.0))
    
    # Exponential recency decay (half-life = 5 steps)
    age = current_step - chunk.step
    recency = math.exp(-age * 0.14)
    
    # Failure boost: failures are more informative
    failure = 0.15 if any keyword in document.lower() else 0.0
    
    return relevance * 0.6 + recency * 0.3 + failure * 0.1
```

**Tại sao các weights này?**
- `0.6` relevance: query semantic similarity vẫn là yếu tố quan trọng nhất
- `0.3` recency: context drift — memory từ 20 bước trước ít liên quan hơn
- `0.1` failure: tăng nhẹ, không muốn overweight (có thể false positive)

---

## 3. Check Builder & Confidence Scoring (`app/services/orchestrator/helpers.py`)

### build_check() Output Format
```python
{
    "tool": "LegalGraphRAG",
    "label": "Kiểm tra căn cứ pháp lý",
    "status": "pass" | "fail" | "warning",
    "desc": "Đã đính kèm văn bản, còn hiệu lực.",
    "details": '{"results": [...]}',  # JSON string
    "confidence": 0.75  # 0.0-1.0
}
```

### Status Logic
```python
if passed and confidence < 0.60:
    status = "warning"    # Passed nhưng không chắc (mock/sparse output)
elif not passed:
    status = "fail"
else:
    status = "pass"       # passed AND confidence >= 0.60
```

### Confidence Per Tool
| Tool | High confidence condition | Range |
|------|--------------------------|-------|
| LegalGraphRAG | results list không rỗng | 0.65-0.95 |
| ErpBudgetCheck | có budget_amount + requested_amount | 0.65-0.90 |
| ErpInventoryCheck | có inventory_items field | 0.60-0.85 |
| DOfficeLookup | có document_id | 0.60-0.92 |
| EcoOcrExtract | proportional to text length | 0.50-0.95 |
| Unknown tools | generic: field count + structure bonus | 0.30-0.94 |

**Generic confidence formula:**
```python
base = 0.70 if passed else 0.72
field_score = min(len(meaningful_fields) / 5, 0.25)  # max +0.25
structure_bonus = 0.10 if has nested lists/dicts else 0.0
mock_reduction: if output has "mock" flag → base 0.45-0.75
```

### Critic uses confidence
```
Critic prompt: "Xem xét báo cáo với confidence scores:
  LegalGraphRAG: 0.75 (medium) — verify thủ công nếu borderline
  ErpBudgetCheck: 0.90 (high) — tin cậy
  TechnicalStandardCheck: 0.55 (low/warning) — không đủ evidence"
```

---

## 4. Planner — Richer Context Injection (`app/services/orchestrator/planner.py`)

### Context Block injected vào user message
```
## Dossier to appraise
- Doc No: 198/TTr-EVNHANOI
- Title: Mua sắm máy bay không người lái phục vụ kiểm tra lưới điện EVNHANOI
- Unit: Ban Kỹ thuật - Sản xuất
- Current risk level: medium (may change after appraisal)

## Document excerpt (from uploaded PDF)
TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI
TỜ TRÌNH XIN Ý KIẾN HĐTV
Về việc mua sắm máy bay không người lái (UAV) phục vụ kiểm tra lưới điện EVNHANOI
Căn cứ Quyết định số 8594/QĐ-EVNHANOI ngày 26/12/2023...
[truncated ở 800 ký tự]
```

### Tool-Specific Queries
```python
{
    "LegalGraphRAG": f"căn cứ pháp lý thẩm quyền phê duyệt 198/TTr-EVNHANOI — Mua sắm UAV",
    "ErpBudgetCheck": f"kiểm tra ngân sách đầu tư mua sắm Mua sắm UAV",
    "TechnicalStandardCheck": f"tiêu chuẩn kỹ thuật Mua sắm UAV",
    "ProcurementCheck": f"quy trình mua sắm đấu thầu 198/TTr-EVNHANOI",
    "EcoOcrExtract": f"trích xuất nội dung hồ sơ PDF 198/TTr-EVNHANOI",
}
```

**Tại sao cần queries cụ thể?**
Generic query = `dossier.title` chỉ match được hồ sơ cùng loại.
Specific queries giúp LLM (local, knowledge limited) focus đúng domain cho từng tool.

---

## 5. Tools — 8 Implementations

### Cấu trúc mỗi tool

```python
# app/services/tools/legal_graph_rag.py

async def run_legal_graph_rag(input: dict) -> dict:
    """
    Input: {query, doc_no, unit, pdf_excerpt, risk_level}
    Output: {results: [...], citations: [...], status: "ok"|"error"}
    
    Strategy:
    1. Query Chroma collection "legal_docs" bằng input.query
    2. If Chroma empty/offline → LLM (LEGAL role) với pdf_excerpt
    3. Return normalized dict
    """
```

### Tool Registry (DB)
```sql
-- ai_tools table
INSERT INTO ai_tools (name, description, is_active) VALUES
  ('LegalGraphRAG',        'Kiểm tra căn cứ pháp lý',        true),
  ('ErpBudgetCheck',       'Đối chiếu ngân sách ERP',         true),
  ('ErpInventoryCheck',    'Kiểm tra tồn kho vật tư',         true),
  ('TechnicalStandardCheck','Kiểm tra tiêu chuẩn kỹ thuật',   true),
  ('ProcurementCheck',     'Kiểm tra quy trình mua sắm',      true),
  ('DOfficeLookup',        'Đối chiếu DOffice',               true),
  ('PmisProjectCheck',     'Checklist PMIS',                  true),
  ('EcoOcrExtract',        'Trích xuất nội dung PDF',         true);
```

### Tool Mock Pattern (when LLM = TOOL_MOCK)
```python
# Khi local LLM offline + tool backend unavailable
# TOOL_MOCK role → Gemini generates realistic fake output
gemini_prompt = f"""
You are a mock tool server for {tool_name}.
Given this input: {json.dumps(tool_input)}
Generate a realistic JSON output that a real {tool_name} would return.
For EVN procurement context. Keep mock=true in output.
"""
```

---

## 6. Prometheus Metrics (`app/core/metrics.py`)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hdtv_llm_calls_total` | Counter | role, backend, status | Tổng LLM calls |
| `hdtv_llm_duration_seconds` | Histogram | role, backend | Latency LLM calls |
| `hdtv_tool_duration_seconds` | Histogram | tool_name | Latency per tool |
| `hdtv_agent_plans_total` | Counter | dossier_unit | Số plan được tạo |
| `hdtv_critic_rejections_total` | Counter | — | Bao nhiêu lần Critic reject |
| `hdtv_context_truncations_total` | Counter | model | Priority eviction count |
| `hdtv_hitl_requests_total` | Counter | reason | HITL pause requests |
| `hdtv_circuit_breaker_state` | Gauge | backend | 0=CLOSED, 1=OPEN, 2=HALF_OPEN |

**Grafana dashboard:** `grafana.internal/d/api-latency`

---

## 7. API Migration History (18 migrations)

| Migration | Version | Change |
|-----------|---------|--------|
| 001 | init | users, dossiers, workflow_diagrams |
| 002-005 | core | alerts, notifications, ai_tools, appraisals |
| 006-010 | agent | agent_memory, ai_audit_log, tool_chains, feedback |
| 011-015 | T-tasks | clarifications, risk_rules, schedules, skills |
| 016-018 | latest | title field fix, notification refactor, T-53 notifications |

**Chạy migrations:**
```bash
wsl docker exec hdtv-api alembic upgrade head
```
