# RAG Pipeline — Legal Knowledge Base

> **Audience:** CTO
> **Mục đích:** Thiết kế RAG pipeline — từ ingest đến retrieval, tại sao dual-collection, và auto-pipeline.

---

## Vấn đề: Legal Knowledge thay đổi liên tục

```
Nghị định 15/2021 → sửa đổi → Nghị định 09/2024
Thông tư 10/2022 → hiệu lực → Thông tư 05/2025
```

Nếu seed một lần, agent dùng law lỗi thời → kết luận sai.

---

## Dual-Collection Architecture

```
Chroma DB:
  ├── Collection: "legal_docs"          ← Auto-ingested (RAG pipeline)
  │   • /opt/rag-docs/*.md, *.txt
  │   • Sliding window chunks (512 tokens, overlap 64)
  │   • Metadata: {source, chunk_idx, ingested_at}
  │   • Cleanup: ingested_at > 30 ngày
  │
  └── Collection: "agent-memories"      ← Manual seed + agent runtime
      • Seeded: Nghị định, Thông tư EVN (demo data)
      • Runtime: Agent upsert sau mỗi session
      • Metadata: {dossier_id, unit, risk_level, step}
```

**Tại sao 2 collections?**
- `legal_docs`: Auto-managed, TTL, version thay đổi theo thời gian
- `agent-memories`: Agent-managed, không có TTL, chứa observations

**Retrieval merge:**
```python
# legal_rag.py — query cả 2 collections
async def legal_graph_rag(query: str) -> dict:
    # Query collection 1: seeded legal docs
    seeded_results = await query_seeded_legal(query, top_k=3)

    # Query collection 2: auto-ingested pipeline docs
    pipeline_results = await query_legal_docs(query, top_k=3)

    # Merge + deduplicate by title
    all_results = seeded_results + pipeline_results
    unique_results = _deduplicate_results(all_results)

    return {"results": unique_results[:5]}  # Cap at 5
```

---

## Auto-ingestion Pipeline

```python
# workers/rag_pipeline.py
@celery_app.task
def ingest_legal_documents(source_dir: str = settings.rag_docs_dir):
    """Runs every 6 hours via Celery Beat"""
    docs = _scan_directory(source_dir)  # *.txt, *.md

    for doc in docs:
        chunks = _sliding_window_chunk(
            text=doc.content,
            chunk_size=512,    # tokens
            overlap=64         # tokens
        )
        for i, chunk in enumerate(chunks):
            vector_store.upsert_legal_doc(
                doc_id=f"{doc.filename}_{i}",
                text=chunk,
                metadata={
                    "source": doc.filename,
                    "chunk_idx": i,
                    "ingested_at": datetime.now().isoformat()
                }
            )

        # Audit log
        AiAuditLog.insert(tool_name="RagIngest", inputs={"source": doc.filename})

@celery_app.task
def cleanup_stale_embeddings():
    """Runs daily at 02:00 (Asia/Ho_Chi_Minh)"""
    cutoff = datetime.now() - timedelta(days=settings.rag_stale_days)
    # Delete Chroma docs where ingested_at < cutoff
```

**Celery Beat Schedule:**
```python
# celery_app.py
beat_schedule = {
    "ingest-legal-docs": {
        "task": "ingest_legal_documents",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    "cleanup-stale-embeddings": {
        "task": "cleanup_stale_embeddings",
        "schedule": crontab(minute=0, hour=2),  # Daily 02:00
    },
}
```

---

## Context Window Management

```python
# context_manager.py
def fit_messages(messages: list, max_tokens: int) -> list:
    """Trim messages to fit context window"""
    total = 0
    result = []
    for msg in reversed(messages):  # Keep newest
        tokens = estimate_tokens(msg)
        if total + tokens > max_tokens:
            CONTEXT_TRUNCATIONS.labels(model=current_model).inc()
            break
        result.insert(0, msg)
        total += tokens
    return result
```

**Metric:** `CONTEXT_TRUNCATIONS` → alert nếu spike (model context window quá nhỏ cho nghiệp vụ phức tạp hơn).

---

## Chunking Strategy

```
Sliding Window Chunking:
─────────────────────────────────────────────────────
Original: [............................] (2000 tokens)
Chunk 1:  [........] (512 tokens)
Chunk 2:       [........] (512 tokens, overlap 64)
Chunk 3:            [........]
Chunk 4:                 [........]

Tại sao overlap?
→ Legal text: nghĩa của câu đầu chunk N có thể phụ thuộc
  vào câu cuối chunk N-1 (cùng điều khoản)
→ Overlap 64 tokens đảm bảo không mất context tại boundary
```

---

## Volume mounts

```yaml
# docker-compose.hdtv.yml
volumes:
  hdtv_rag_docs:

services:
  hdtv-worker:
    volumes:
      - hdtv_rag_docs:/opt/rag-docs  # Shared với beat

  hdtv-beat:
    volumes:
      - hdtv_rag_docs:/opt/rag-docs  # Same volume
```

**Để thêm legal docs mới:** Copy file vào `/opt/rag-docs/` → pipeline tự ingest trong 6 giờ tiếp theo, hoặc trigger thủ công qua Celery.
