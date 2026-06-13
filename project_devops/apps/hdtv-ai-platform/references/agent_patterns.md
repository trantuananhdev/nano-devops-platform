# Agent Patterns — HDTV-AI Orchestrator

## Luồng ReAct (Plan → Execute → Critic → Reflect)

```
[POST /dossiers/{id}/appraise]
        │
        ▼
  Celery task: run_appraisal_task(dossier_id)
        │
        ├─► react_agent.run_appraisal()
        │         ├─ planner.create_plan()      → LLM tạo JSON plan với steps + parallel_groups
        │         ├─ executor.execute_plan()    → chạy DAG, asyncio.gather() cho parallel groups
        │         │         └─ AiAuditLog       → log mỗi tool call (tool_name, inputs, outputs, ms)
        │         ├─ critic.evaluate()          → LLM review báo cáo → CriticResult
        │         └─ reflector.reflect()        → học từ feedback, lưu AgentMemory
        │
        └─► publish_event("appraisal_completed", {dossier_id, risk_level})
                  └─► WS broadcast → FE cập nhật
```

## Thêm Specialist Agent Mới

**Bước 1:** Thêm AgentRole enum (`app/services/llm_router.py`):
```python
class AgentRole(str, Enum):
    PROCUREMENT = "procurement"   # Chuyên gia đấu thầu
```

**Bước 2:** Thêm vào ROLE_BACKENDS:
```python
AgentRole.PROCUREMENT: {
    "backend": "gemini",
    "model": settings.gemini_model,
    "temperature": 0.1,
}
```

**Bước 3:** Tạo system prompt (`app/services/orchestrator/prompts/procurement.py`):
```python
PROCUREMENT_SYSTEM = """
Bạn là chuyên gia đấu thầu EVN, chuyên về Luật Đấu thầu 2023 và Nghị định 24/2024/NĐ-CP.
Đánh giá: hình thức lựa chọn nhà thầu, thời gian phát hành HSMT (≥5 ngày làm việc), tính hợp lệ hồ sơ.
Trả về JSON: {"status": "pass|fail", "issues": [...], "recommendation": "..."}
"""
```

**Bước 4:** Đăng ký Tool (`app/services/tools/base.py`):
```python
TOOL_REGISTRY["ProcurementAudit"] = {
    "name": "ProcurementAudit",
    "description": "Kiểm tra quy trình đấu thầu theo Luật Đấu thầu 2023",
    "parameters": {"dossier_id": "int"},
}
```

---

## PubSub Events — danh sách chuẩn

```python
await publish_event(event_type, data_dict)

# Format chuẩn: data PHẢI có dossier_id nếu liên quan hồ sơ
"dossier_created"         → {"dossier_id", "doc_no"}
"dossier_status_changed"  → {"dossier_id", "from_status", "to_status", "changed_by"}
"appraisal_started"       → {"dossier_id", "task_id"}
"appraisal_completed"     → {"dossier_id", "risk_level", "overall_status"}
"appraisal_failed"        → {"dossier_id", "error"}
"clarification_requested" → {"dossier_id", "task_id", "clarification_id", "question", "options"}
"clarification_answered"  → {"dossier_id", "clarification_id", "answer"}
"alert_created"           → {"alert_id", "severity", "source", "dossier_id"}
"document_uploaded"       → {"dossier_id", "file_name"}
"notification_sent"       → {"user_id", "notification_id", "type", "title"}
"stream_chunk"            → {"dossier_id", "task_id", "text"}   # streaming AI output
```

FE subscribe qua WebSocket `ws.js`:
```js
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data)
  // msg.type = event_type, msg.data = data_dict, msg.timestamp = ISO string
  if (msg.type === 'appraisal_completed') dossierStore.onAppraisalComplete(msg.data)
  if (msg.type === 'notification_sent') notifStore.onNewNotification(msg.data)
  if (msg.type === 'clarification_requested') chatStore.onClarification(msg.data)
  if (msg.type === 'stream_chunk') chatStore.appendStreamChunk(msg.data.text)
}
```

---

## Human-in-the-Loop Clarification

**BE — khi agent cần hỏi:**
```python
# Trong executor khi tool yêu cầu làm rõ
from app.services.clarification_service import create_clarification
from app.services.pubsub import publish_event

clarif = await create_clarification(
    session,
    dossier_id=dossier.id,
    task_id=current_task_id,
    question="Nhà thầu DJI Enterprise Vietnam có giấy phép bay thương mại UAV tại Việt Nam không?",
    options=["Có, đính kèm hồ sơ", "Chưa có, đang xin cấp", "Không áp dụng"],
    trigger_type="legal_check",
    resume_state={"step_id": step.id, "tool": "LegalGraphRAG"},
)
await publish_event("clarification_requested", {
    "dossier_id": dossier.id,
    "task_id": current_task_id,
    "clarification_id": clarif.id,
    "question": clarif.question,
    "options": clarif.options,
})
# Raise exception để executor tạm dừng
raise ClarificationPaused(clarification_id=clarif.id)
```

**BE — sau khi user trả lời (`POST /clarifications/{id}/answer`):**
```python
# clarification_service.answer_clarification() → set status=answered, answer=...
# Sau đó resume task từ resume_state
await celery_app.send_task("run_appraisal_task", args=[dossier_id], kwargs={"resume_from": clarif.resume_state})
```

**FE — khi nhận WS event:**
```js
// chatStore.js
onClarification(data) {
  this.pendingClarification = {
    id: data.clarification_id,
    question: data.question,
    options: data.options,
  }
  // UI hiện inline form trong chat với options dạng button
}
async answerClarification(clarificationId, answer) {
  await axios.post(`/clarifications/${clarificationId}/answer`, { answer })
  this.pendingClarification = null
}
```

---

## AuditLog Pattern

```python
from app.services.audit_service import log_action

# Trong router sau mutation quan trọng
await log_action(
    session=session,
    action="create_dossier",           # snake_case, ngắn gọn
    description=f"Tạo hồ sơ {doc_no}",
    dossier_id=dossier.id,
    user_id=current_user_id,           # None nếu system action
    extra_data={"doc_no": doc_no},
    ip_address=request.client.host if request.client else None,
)
```

---

## Tool Chaining (DAG)

```python
# Plan JSON từ planner — executor tự resolve DAG
{
  "steps": [
    {"id": "ocr", "tool": "OcrExtractor", "parallel_group": null, "depends_on": [], "tool_input": {"dossier_id": 42}},
    {"id": "legal", "tool": "LegalGraphRAG", "parallel_group": null, "depends_on": ["ocr"], "tool_input": {"dossier_id": 42}},
    {"id": "budget", "tool": "ErpBudgetCheck", "parallel_group": "finance", "depends_on": ["ocr"], "tool_input": {"dossier_id": 42}},
    {"id": "inv", "tool": "ErpInventoryCheck", "parallel_group": "finance", "depends_on": ["ocr"], "tool_input": {"dossier_id": 42}},
  ]
}
# Executor: ocr chạy trước → legal chạy tiếp → budget+inv asyncio.gather() cùng lúc
```

---

## Memory Pattern

```python
# Lưu kết quả học được
memory = AgentMemory(
    dossier_id=dossier.id,
    step=step_number,
    thought="Phân tích giá UAV so với tham chiếu thị trường...",
    action="tool_call",
    tool_name="ErpInventoryCheck",
    tool_input={"dossier_id": dossier.id},
    observation="Giá vượt 18%, đánh dấu risk_level=high",
)
session.add(memory)
await session.commit()
```
