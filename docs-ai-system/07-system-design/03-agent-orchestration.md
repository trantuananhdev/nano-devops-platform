# Agent Orchestration Deep Dive — L3 System Design

> **Tầng L3: Nội tại AI Orchestrator**
> **Audience:** AI Engineer, Senior Backend Dev
> **Cập nhật:** 2026-06-13

---

## Plan → Execute → Reflect → Critic State Machine

```
                    ┌─────────────────────────────────────┐
                    │           ORCHESTRATOR               │
                    │                                      │
    START ──────────►  MEMORY_RETRIEVE                     │
                    │       │                              │
                    │       ▼                              │
                    │  PLAN (revision=0)                   │
                    │  LLM → ExecutionPlan JSON            │
                    │  Fallback: rule-based plan           │
                    │       │                              │
                    │       ▼                              │
                    │  EXECUTE                             │
                    │  Topological batches                 │
                    │  asyncio.gather(parallel_group)      │
                    │  Each step → save AgentMemory        │
                    │       │                              │
                    │       ▼                              │
                    │  REFLECT                             │
                    │  LLM analyzes observations           │
                    │       │                              │
                    │   ────┼────────────────────────────► ESCALATE → HITL
                    │   sufficient?                        │  (clarification)
                    │       │ no                           │
                    │       ▼ revise                       │
                    │  revision += 1                       │
                    │  if revision < max_revisions:        │
                    │    goto PLAN (with observations)     │
                    │  else: force summarize               │
                    │       │                              │
                    │       ▼                              │
                    │  SUMMARIZE                           │
                    │  LLM → Markdown report (tiếng Việt) │
                    │       │                              │
                    │       ▼                              │
                    │  CRITIC                              │
                    │  LLM quality check:                  │
                    │    approved? → save + done           │
                    │    rejected? → re-summarize (1x)     │
                    │       │                              │
                    │       ▼                              │
                    │    DONE ◄────────────────────────────│
                    │  save AppraisalResult                │
                    │  emit WS "appraisal_complete"        │
                    └─────────────────────────────────────┘
```

---

## Execution Batches — Topological Sort

**Ví dụ plan với dependencies:**
```json
{
  "steps": [
    {"id": "s1", "tool": "EcoOcrExtract",      "parallel_group": null,        "depends_on": []},
    {"id": "s2", "tool": "LegalGraphRAG",       "parallel_group": null,        "depends_on": ["s1"]},
    {"id": "s3", "tool": "ErpBudgetCheck",      "parallel_group": "financial", "depends_on": ["s2"]},
    {"id": "s4", "tool": "ErpInventoryCheck",   "parallel_group": "financial", "depends_on": ["s2"]},
    {"id": "s5", "tool": "TechnicalStandardCheck","parallel_group": null,      "depends_on": ["s2"]}
  ]
}
```

**Kết quả batch execution:**
```
Batch 1: [s1]                              ← no deps
Batch 2: [s2]                              ← depends on s1
Batch 3: [s3, s4] asyncio.gather()        ← same parallel_group, s2 done
Batch 4: [s5]                              ← depends on s2, not in financial group
```

**Code logic (`executor.py`):**
```python
def _build_execution_batches(steps, completed_ids):
    """Topological sort: batch = all steps where depends_on ⊆ completed."""
    batches = []
    remaining = list(steps)
    while remaining:
        batch = [
            s for s in remaining
            if all(dep in completed_ids for dep in s.get("depends_on", []))
        ]
        # Group by parallel_group within batch
        groups = group_by_parallel_group(batch)
        batches.append(groups)
        completed_ids.update(s["id"] for s in batch)
        remaining = [s for s in remaining if s not in batch]
    return batches
```

---

## Memory Hierarchy

```
┌────────────────────────────────────────────────────────────────────┐
│  HDTV-AI Memory Architecture                                        │
│                                                                     │
│  ┌─────────────────────┐   ┌──────────────────────────────────┐   │
│  │  SHORT-TERM MEMORY  │   │  LONG-TERM MEMORY                │   │
│  │  (per session)      │   │  (cross-session, cross-dossier)  │   │
│  │                     │   │                                  │   │
│  │  PostgreSQL         │   │  ChromaDB                        │   │
│  │  AgentMemory rows   │   │  Collection: hdtv_memories       │   │
│  │                     │   │  Collection: hdtv_feedback_lessons│  │
│  │  step: int          │   │                                  │   │
│  │  action: str        │   │  Metadata per vector:            │   │
│  │  tool_name: str     │   │    dossier_id, unit, risk_level  │   │
│  │  thought: str       │   │    step, tool_name, session_id   │   │
│  │  observation: str   │   │                                  │   │
│  │                     │   │  Query with WHERE filter:        │   │
│  │  Query: last N rows │   │    unit = "Ban Kỹ thuật"         │   │
│  │  per dossier_id     │   │    risk_level = "high"           │   │
│  └─────────────────────┘   └──────────────────────────────────┘   │
│                                        │                            │
│  ┌─────────────────────────────────────┴──────────────────────┐   │
│  │  RETRIEVAL SCORING                                          │   │
│  │                                                             │   │
│  │  score = relevance × 0.6 + recency × 0.3 + failure × 0.1  │   │
│  │                                                             │   │
│  │  relevance = 1 - (chroma_distance / 2.0)                   │   │
│  │  recency   = exp(-age_steps × 0.14)   [half-life ≈ 5]      │   │
│  │  failure   = 0.15 if contains error/fail keywords else 0.0 │   │
│  │                                                             │   │
│  │  Fetch: top k×3 candidates → re-rank → return top k        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │  CONTEXT WINDOW (in-flight LLM conversation)              │    │
│  │                                                           │    │
│  │  Priority-based eviction (context_manager.py):           │    │
│  │    CRITICAL: system prompt, first user message           │    │
│  │    HIGH:     failures, reflections, critic verdicts      │    │
│  │    MEDIUM:   planning messages, clarifications           │    │
│  │    LOW:      routine success observations                │    │
│  │    MINIMAL:  long verbose dumps (>2000 chars assistant)  │    │
│  │                                                           │    │
│  │  Drop order: MINIMAL → LOW → MEDIUM → never HIGH/CRIT    │    │
│  └───────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

---

## HITL — Human In The Loop Flow

```
ORCHESTRATOR EXECUTE
      │
      │  Tool returns conflict_detected: true
      │  OR reflector verdict = "escalate"
      │  OR confidence < threshold
      ▼
clarification_service.create_clarification()
  → DB: ClarificationRequest {question, dossier_id, status: "pending"}
  → Redis PUBLISH ws_channel:{assigned_user_id}
  → WS event "clarification_requested" → FE

                          FE: user sees inline question form
                          User types answer → POST /clarifications/{id}/answer
                          → DB: status = "answered", answer = "..."
                          → Redis PUBLISH clarification_answered:{session_id}

ORCHESTRATOR (blocking on clarification)
  → receives Redis message
  → resume execution with answer injected into context
  → continue Plan→Execute loop
```

**Use cases cho HITL:**
1. Nhà thầu không có trong whitelist → hỏi "Xác nhận nhà thầu X được phép tham gia?"
2. Ngân sách vượt threshold → hỏi "Đã có phê duyệt bổ sung ngân sách chưa?"
3. Mâu thuẫn giữa kết quả tools → hỏi "ERP và PMIS không khớp, dùng nguồn nào?"

---

## Prompt Architecture

**9 system prompts chuyên biệt (prompt_builder.py):**

```
PLANNER  ─── "Bạn là Chuyên gia Thẩm định tờ trình EVN.
              Phân tích dossier và tạo execution plan JSON.
              Tools có sẵn: [list]
              Memory từ hồ sơ tương tự: [memory_ctx]
              Bài học từ phản hồi trước: [feedback_lessons]"

EXECUTOR  ─── "Bạn là Tool Executor.
               Thực thi tool call theo plan step.
               Input: {tool_input}
               Trả về kết quả JSON thuần."

REFLECTOR ─── "Bạn là Chuyên gia Đánh giá.
               Xem xét observations từ tất cả tools.
               Verdict: sufficient | revise | escalate
               Nếu revise: liệt kê checks còn thiếu."

CRITIC ─────── "Bạn là Quality Reviewer cấp cao.
                Đọc báo cáo thẩm định.
                Kiểm tra: đầy đủ, chính xác, có evidence.
                Verdict: approved | rejected + notes."

SUMMARY ────── "Bạn là Chuyên viên viết Báo cáo.
                Tổng hợp observations thành báo cáo Markdown tiếng Việt.
                Format: tóm tắt → từng check → kết luận → kiến nghị."

LEGAL ──────── "Bạn là Luật sư chuyên về đấu thầu/mua sắm.
                Kiểm tra căn cứ pháp lý hồ sơ.
                Nghị định 24/2024, Luật Đấu thầu 22/2023."

FINANCIAL ──── "Bạn là Chuyên gia Tài chính EVN.
                Đối chiếu tổng mức đầu tư với ngân sách kế hoạch."

OCR ─────────── "Bạn là OCR Engine.
                 Trích xuất thông tin có cấu trúc từ nội dung PDF."

TOOL_MOCK ───── "Bạn là Mock Tool Server.
                 Trả về kết quả giả lập cho tool {tool_name}
                 dựa trên input. JSON format."
```

---

## Tool Chaining (T-21)

```
DB table: tool_chains
  source_tool: "EcoOcrExtract"
  target_tool: "LegalGraphRAG"
  output_mapping: {"extracted_text": "query"}

chain_executor.py:
  1. Execute source_tool → output
  2. Map output fields to target_tool input (via output_mapping)
  3. Execute target_tool với enriched input
  4. Return chained result
```

**Use case:** PDF upload → EcoOcrExtract trích text → text tự động làm input cho LegalGraphRAG query.

---

## Risk Rules Engine

```python
# DB: RiskRule {name, condition_expr, risk_level, message}
# condition_expr là Python expression an toàn (eval sandbox)

SAFE_BUILTINS = {"abs", "min", "max", "len", "round", "int", "float", "str", "bool"}

# Ví dụ rule:
# name: "Budget Overrun"
# condition_expr: "budget_exceeded_pct > 10"
# risk_level: "high"

# Evaluation:
context = {"budget_exceeded_pct": 18.5, "missing_docs": False, ...}
result = eval(rule.condition_expr, {"__builtins__": safe_builtins}, context)
# → True → rule triggered → dossier risk_level = max(current, rule.risk_level)
```

**6 rules hiện tại:**
1. Ngân sách vượt kế hoạch > 10% → high
2. Thiếu chứng chỉ năng lực nhà thầu → high  
3. Giá bất thường lệch > 15% thị trường → medium
4. Hồ sơ thiếu tài liệu bắt buộc → medium
5. Tiến độ trễ hơn kế hoạch → low
6. Chỉ có 1 nhà thầu tham gia → medium
