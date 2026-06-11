# Agent Memory System

## Tổng quan

Memory system của HDTV có 3 lớp chính:
1. **Short-term (Working Memory):** Postgres, current session
2. **Long-term Memory:** Chroma vector DB, cross-session
3. **Feedback Lessons:** Past user feedback learned via RAG

## Components

### 1. Short-term Memory
- **Table:** `agent_memory`
- **Fields:** `dossier_id`, `step`, `thought`, `action`, `tool_name`, `tool_input`, `observation`, `embedding_id`
- **File:** `app/models/entities.py`

### 2. Long-term Memory (Vector DB)
- **Vector DB:** Chroma
- **Collection:** `agent-memories`
- **Functions:**
  - `vector_store.upsert_memory()`
  - `retriever.retrieve_relevant_memories()`
  - `retriever.retrieve_cross_dossier_memories()`
- **Files:** 
  - `app/services/memory/vector_store.py`
  - `app/services/memory/retriever.py`

### 3. Feedback Lessons
- **Table:** `agent_feedback`
- **Vector Collection:** `feedback-lessons`
- **Purpose:** Learn from past user feedback to avoid mistakes
- **Functions:** `retriever.retrieve_feedback_lessons()`

### 4. User Preferences
- **Table:** `user_preferences`
- **Purpose:** Personalize agent behavior
- **Fields:** `user_id`, `report_style`, `language`, `risk_focus`
- **File:** `app/services/memory/preference_service.py`

## Degraded Mode

If Chroma is unavailable:
- Fallback to full-table scans from PostgreSQL
- Trimmed to `settings.memory_top_k` items

## Quick Example (Retrieval)

```python
from app.services.memory import retriever

memory_chunks = await retriever.retrieve_relevant_memories(
    session=db_session,
    dossier_id=123,
    query="Thẩm định hồ sơ ngân sách",
    top_k=5
)
```
