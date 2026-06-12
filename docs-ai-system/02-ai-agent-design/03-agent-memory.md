# Agent Memory — 3-Layer Memory Architecture

> **Audience:** CTO
> **Mục đích:** Thiết kế memory system cho AI Agent — tại sao cần 3 layers, trade-offs là gì.

---

## Vấn đề: LLM không có memory

```
Session 1: Agent thẩm định hồ sơ A, phát hiện nhà thầu X hay báo sai ngân sách
Session 2: Agent thẩm định hồ sơ B (cùng nhà thầu X) → KHÔNG biết lịch sử
```

Với memory system:
```
Session 2: Agent retrieve memory về nhà thầu X
           → "Lần trước: báo ngân sách 5 tỷ nhưng thực tế 7 tỷ"
           → Planner: thêm bước double-check ngân sách vào plan
```

---

## 3-Layer Memory Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: Short-term Memory (Working Memory)                    │
│  Storage: PostgreSQL (agent_memory table)                       │
│  Scope:   Current dossier session                               │
│  TTL:     Until appraisal complete                              │
│                                                                 │
│  Content: step-by-step thoughts, actions, observations          │
│  Usage:   Executor writes after each tool, Reflector reads all  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Upserted at end of session
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: Long-term Memory (Cross-session)                      │
│  Storage: Chroma DB (agent-memories collection)                 │
│  Scope:   Cross dossier, cross session                          │
│  TTL:     30 days (cleanup_stale_embeddings)                    │
│                                                                 │
│  Content: Key observations, patterns, entity behaviors          │
│  Query:   Top-K semantic similarity (embedding search)          │
│  Fallback: Full PG scan nếu Chroma unreachable (degraded mode)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Separate collection
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: Feedback Lessons (Learning Loop)                      │
│  Storage: Chroma DB (feedback-lessons collection)               │
│  Scope:   All users, all dossiers                               │
│  Source:  User 👍/👎 feedback                                    │
│                                                                 │
│  Content: "Khi X thì nên làm Y" (learned from human feedback)  │
│  Usage:   Injected into Planner prompt before planning          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Memory Flow trong Appraisal

```python
# BEFORE planning: load all memory layers
memories = await retriever.retrieve_relevant_memories(
    dossier_id=id,
    query=dossier_context,
    top_k=settings.memory_top_k  # default: 5
)
feedback_lessons = await retriever.retrieve_feedback_lessons(
    query=dossier_context,
    top_k=3
)
legal_context = await retriever.retrieve_legal_docs(query=..., top_k=5)

# Build enriched context for Planner
context = {
    "dossier": dossier_data,
    "past_observations": memories,      # Layer 2
    "lessons_learned": feedback_lessons,  # Layer 3
    "legal_precedents": legal_context,
    "user_preferences": user_prefs,      # User preferences (PG)
}

# AFTER each tool execution: update short-term
await memory_service.upsert_step(
    dossier_id=id,
    step=step_id,
    observation=tool_result
)

# AT END of session: upsert to long-term
await vector_store.upsert_memory(
    doc_id=f"{dossier_id}_{step_id}",
    text=observation_text,
    metadata={"unit": dossier.unit, "risk_level": result.risk_level}
)
```

---

## Cross-dossier Memory

Không chỉ nhớ trong 1 hồ sơ, còn nhớ theo **đơn vị và risk level**:

```python
# retriever.py — cross-dossier query
async def retrieve_cross_dossier_memories(
    unit: str,
    risk_level: str,
    query: str,
    top_k: int = 5
) -> list[str]:
    # Filter bằng metadata trong Chroma
    results = chroma_collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"unit": unit, "risk_level": risk_level}  # metadata filter
    )
    return results
```

**Use case:** Cùng đơn vị EVN Miền Nam, cùng loại risk HIGH → agent biết pattern lịch sử của đơn vị đó.

---

## User Preferences

Thêm personalization layer trên memory:

```python
# preference_service.py
USER_PREFERENCE_SEEDS = {
    1: {"report_style": "concise",  "language": "vi"},  # hdtv_leader
    2: {"report_style": "detailed", "language": "vi"},  # dept_head
    4: {"report_style": "technical","language": "vi"},  # specialist
}

# Injected into Planner prompt:
# "Người dùng này ưa thích báo cáo ngắn gọn, ưu tiên risk level đầu tiên"
```

---

## Degraded Mode Design

```python
# retriever.py — graceful degradation
async def retrieve_relevant_memories(...) -> list[str]:
    try:
        # Try Chroma first (fast semantic search)
        return await _query_chroma(query, top_k)
    except ChromaUnavailableError:
        logger.warning("Chroma unreachable, falling back to PG scan")
        # Fallback: full table scan, trim to top_k
        rows = await db.execute(
            "SELECT observation FROM agent_memory WHERE dossier_id = $1 LIMIT $2",
            dossier_id, settings.memory_top_k
        )
        return [r.observation for r in rows]
    # NO 500 error — agent continues with degraded memory
```

**Rationale:** Memory là best-effort — agent vẫn hoạt động tốt (80%) dù không có long-term memory. Đây là design philosophy: **resilience over perfection**.

---

## Storage Architecture

| Layer | Storage | Collection/Table | Size estimate |
|-------|---------|-----------------|---------------|
| Short-term | PostgreSQL | `agent_memory` | 1-10 rows/appraisal |
| Long-term | Chroma | `agent-memories` | Grows over time, 30-day TTL |
| Feedback | Chroma | `feedback-lessons` | 1 per negative feedback |
| Legal RAG | Chroma | `legal_docs` | ~1000 chunks (seeded + auto-ingest) |
| User Prefs | PostgreSQL | `user_preferences` | 1 row per user per key |
