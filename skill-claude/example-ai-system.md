# Agent Patterns — HDTV-AI Orchestrator

## Luồng ReAct Agent (Plan → Execute → Critic → Reflect)

```
[Dossier submitted]
      │
      ▼
  react_agent.run_appraisal()
      │
      ├─► planner.create_plan()          → LLM tạo ExecutionPlan JSON
      │         └─ fallback_plan()       → nếu LLM fail
      │
      ├─► executor.execute_plan()        → chạy steps theo DAG
      │         ├─ parallel_group       → asyncio.gather() cho cùng group
      │         ├─ execute_tool()       → gọi tool thực/mock
      │         └─ AiAuditLog           → log mỗi tool call
      │
      ├─► critic.evaluate()             → LLM review báo cáo
      │         └─ CriticResult         → {approved, issues, suggestions}
      │
      └─► reflector.reflect()           → học từ feedback, update memory
                └─ AgentMemory         → lưu lessons learned
```

## Thêm specialist agent mới

### Bước 1: Thêm AgentRole

```python
# app/services/llm_router.py
class AgentRole(str, Enum):
    # ... existing ...
    PROCUREMENT = "procurement"  # Chuyên gia đấu thầu
```

### Bước 2: Thêm vào ROLE_BACKENDS

```python
ROLE_BACKENDS: dict[str, dict] = {
    # ... existing ...
    AgentRole.PROCUREMENT: {
        "backend": "gemini",           # hoặc "local" cho Ubuntu
        "model": settings.gemini_model,
        "temperature": 0.1,            # thấp hơn = chính xác hơn với pháp quy
    },
}
```

### Bước 3: Tạo system prompt

```python
# app/services/orchestrator/prompts/procurement.py
PROCUREMENT_SYSTEM = """
Bạn là chuyên gia đấu thầu EVN, chuyên về Luật Đấu thầu 2023 và Nghị định 24/2024/NĐ-CP.
Nhiệm vụ: thẩm định tính hợp lệ của quy trình lựa chọn nhà thầu.

Đánh giá các yếu tố:
1. Hình thức lựa chọn nhà thầu có phù hợp với giá trị gói thầu không?
2. Hồ sơ mời thầu có đầy đủ theo Mẫu số 01 Thông tư 06/2024 không?
3. Thời gian phát hành HSMT có đảm bảo tối thiểu 5 ngày làm việc không?

Trả về JSON:
{
    "status": "pass|fail",
    "issues": ["..."],
    "recommendation": "..."
}
"""
```

### Bước 4: Đăng ký Tool

```python
# app/services/tools/base.py
TOOL_REGISTRY["ProcurementAudit"] = {
    "name": "ProcurementAudit",
    "description": "Kiểm tra quy trình đấu thầu theo Luật Đấu thầu 2023",
    "parameters": {"dossier_id": "int", "doc_no": "str", "title": "str"},
}
```

---

## Memory & Personalization Pattern

```python
# Lưu kết quả học được sau mỗi appraisal
async def _save_memory(session: AsyncSession, dossier: Dossier, lesson: str):
    memory = AgentMemory(
        dossier_id=dossier.id,
        content=lesson,
        embedding_vector=None,  # vector_store sẽ update sau
        meta_json={"dossier_doc_no": dossier.doc_no, "unit": dossier.unit},
    )
    session.add(memory)
    await session.commit()
    # Index vào vector store cho retrieval
    await mem_store.upsert_memory(memory.id, lesson)


# Retrieve relevant memories khi plan mới
async def _get_relevant_memories(dossier: Dossier) -> str:
    query = f"{dossier.title} {dossier.unit}"
    memories = await mem_retriever.retrieve(query, top_k=3)
    if not memories:
        return ""
    return "Bài học từ hồ sơ tương tự:\n" + "\n".join(
        f"- {m['content']}" for m in memories
    )
```

---

## PubSub Events — tất cả events hiện có

```python
# Dùng trong router/service sau mutations
await publish_event(event_type, data_dict)

# Events chuẩn:
"dossier_created"         → {"dossier_id", "doc_no"}
"dossier_status_changed"  → {"dossier_id", "from_status", "to_status", "changed_by"}
"appraisal_started"       → {"dossier_id", "task_id"}
"appraisal_completed"     → {"dossier_id", "risk_level", "overall_status"}
"appraisal_failed"        → {"dossier_id", "error"}
"clarification_requested" → {"dossier_id", "task_id", "clarification_id", "question", "options"}
"clarification_answered"  → {"dossier_id", "clarification_id", "answer"}
"alert_created"           → {"alert_id", "severity", "source"}
"document_uploaded"       → {"dossier_id", "file_name", "file_key"}
"notification_sent"       → {"user_id", "notification_id", "type"}

# Thêm event mới: chỉ cần gọi publish_event() với type mới
# FE Vue store subscribe qua WebSocket ws.js → tự update store
```

---

## Notification Pattern — gửi thông báo cho user

```python
# app/services/notification_service.py
async def notify_user(
    session: AsyncSession,
    user_id: int,
    notif_type: NotificationType,
    title: str,
    message: str,
    dossier_id: int | None = None,
    extra_data: dict | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        dossier_id=dossier_id,
        type=notif_type,
        title=title,
        message=message,
        extra_data=extra_data or {},
    )
    session.add(notif)
    await session.commit()
    await session.refresh(notif)

    # Broadcast real-time
    await publish_event("notification_sent", {
        "user_id": user_id,
        "notification_id": notif.id,
        "type": notif_type.value,
        "title": title,
    })
    return notif


# Gọi khi status dossier thay đổi:
await notify_user(
    session,
    user_id=dossier_owner_id,
    notif_type=NotificationType.status_change,
    title=f"Hồ sơ {dossier.doc_no} đã cập nhật trạng thái",
    message=f"Trạng thái mới: {new_status.value}",
    dossier_id=dossier.id,
)
```

---

## AuditLog Pattern — ghi nhật ký mọi hành động quan trọng

```python
# Trong router sau mỗi mutation quan trọng
from app.services.audit_service import log_action

await log_action(
    session=session,
    action="create_dossier",            # snake_case, ngắn gọn
    description=f"Tạo hồ sơ {doc_no}",
    dossier_id=dossier.id,
    user_id=current_user_id,            # None nếu system action
    extra_data={"doc_no": doc_no, "unit": unit},
    ip_address=request.client.host,
)
```

---

## Tool Chaining Pattern — tools phụ thuộc nhau

```python
# Trong plan JSON (từ planner):
{
    "steps": [
        {
            "id": "step-1",
            "tool": "OcrExtractor",
            "parallel_group": null,
            "depends_on": [],
            "tool_input": {"dossier_id": 42}
        },
        {
            "id": "step-2",
            "tool": "LegalGraphRAG",
            "parallel_group": null,
            "depends_on": ["step-1"],        # ← chờ OCR xong mới chạy
            "tool_input": {"dossier_id": 42}
        },
        {
            "id": "step-3",
            "tool": "ErpBudgetCheck",
            "parallel_group": "financial",   # ← chạy song song với step-4
            "depends_on": ["step-1"],
            "tool_input": {"dossier_id": 42}
        },
        {
            "id": "step-4",
            "tool": "ErpInventoryCheck",
            "parallel_group": "financial",   # ← cùng group → asyncio.gather()
            "depends_on": ["step-1"],
            "tool_input": {"dossier_id": 42}
        }
    ]
}
```

Executor tự resolve DAG: nhóm `parallel_group` chạy `asyncio.gather()`, steps có `depends_on` chờ đủ deps mới chạy.