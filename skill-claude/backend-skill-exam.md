---
name: hdtv-backend-module
description: >
  Thiết kế và phát triển backend cho hệ thống HDTV-AI phục vụ nhân viên EVN — bao gồm tạo module
  mới (router + service + schema + migration), review & fix lỗi module hiện có (type errors, async/await,
  logic ORM), seed dữ liệu thực tế vào PostgreSQL, và thiết kế hệ thống thiên hướng AI agent cao.
  Dùng khi người dùng muốn: thêm tính năng mới, fix bug backend, viết migration Alembic, tạo seed
  script, thiết kế orchestrator/ReAct agent mới, tích hợp tool mới, cải thiện schema JSONB, hoặc
  bất kỳ thay đổi nào liên quan đến hdtv-ai-platform (FastAPI, SQLAlchemy async, Alembic, Redis,
  MinIO, Meilisearch, Celery, LLM router, agent orchestrator).
---

# HDTV-AI Backend Module Skill

Skill này là "bộ não" cho việc phát triển backend `hdtv-ai-platform` — một hệ thống thẩm định hồ sơ
mua sắm/đấu thầu cho nhân viên EVN, được điều phối bởi AI agent multi-role.

---

## 1. Kiến trúc tổng quan

```
hdtv-ai-platform/
├── app/
│   ├── core/           # config, database, rate_limiter, circuit_breaker, metrics, tracing
│   ├── models/
│   │   └── entities.py # TẤT CẢ SQLAlchemy models — single file
│   ├── schemas/        # Pydantic v2 (model_validate, not from_orm)
│   ├── routers/        # FastAPI APIRouter, prefix /api/v1/<resource>
│   ├── services/
│   │   ├── orchestrator/   # planner → executor → critic → reflector
│   │   ├── memory/         # vector_store, retriever, preference_service
│   │   ├── tools/          # base.py (execute_tool, list_tools_dynamic), gemini_mock
│   │   └── llm_router.py   # AgentRole enum + llm_call()
│   └── workers/tasks.py    # Celery async tasks (run_appraisal_task, ...)
├── alembic/versions/       # Migrations — KHÔNG dùng create_all()
└── seeds/                  # Seed scripts thực tế cho EVN
```

### Stack cốt lõi
| Layer | Tech |
|---|---|
| Web | FastAPI async, lifespan context |
| ORM | SQLAlchemy 2.x async (`AsyncSession`, `Mapped`, `mapped_column`) |
| Migration | Alembic (async env.py) |
| DB | PostgreSQL + JSONB |
| Search | Meilisearch (`search_service`) |
| Storage | MinIO (`minio_service`) |
| Cache/Queue | Redis (rate limiter) + Celery (appraisal tasks) |
| LLM | Ubuntu llama-server (Gemma) + Gemini Flash (mock/specialist) |
| PubSub | `publish_event()` → WebSocket broadcast |

---

## 2. Quy tắc bắt buộc (không được vi phạm)

### 2a. SQLAlchemy Async
```python
# ✅ ĐÚNG
result = await session.execute(select(Dossier).where(Dossier.id == id))
dossier = result.scalar_one_or_none()

# ❌ SAI — không dùng session.query() trong async context
dossier = session.query(Dossier).filter_by(id=id).first()
```

- **Luôn** dùng `select()` + `await session.execute()`.
- Sau `session.add()` + `await session.commit()` → phải `await session.refresh(obj)` trước khi return.
- Dùng `selectinload()` cho relationship (tránh lazy load gây `MissingGreenlet`).
- Dependency injection: `session: AsyncSession = Depends(get_db)`.

### 2b. Pydantic v2
```python
# ✅ ĐÚNG
DossierOut.model_validate(dossier)  # thay cho from_orm()

class DossierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

- Không dùng `orm_mode = True` (deprecated Pydantic v1).
- Dùng `model_config = ConfigDict(from_attributes=True)` trong mọi schema đọc từ ORM.

### 2c. Entities — Single Source of Truth
- **TOÀN BỘ** models đặt trong `app/models/entities.py`.
- Thêm model mới → thêm vào file này, **không** tạo file model riêng.
- Enum dùng `(str, enum.Enum)` để JSON-serializable.
- JSONB default: `mapped_column(JSONB, default=dict)` hoặc `default=list`.

### 2d. Router pattern
```python
router = APIRouter()

@router.get("", response_model=MyPage)          # list
@router.get("/{id}", response_model=MyOut)       # detail
@router.post("", response_model=MyOut, status_code=201)  # create
@router.patch("/{id}", response_model=MyOut)     # update
@router.delete("/{id}", status_code=204)         # delete
```

- Đăng ký router trong `app/routers/__init__.py` → `api_router.include_router(...)`.
- Xử lý lỗi: `raise HTTPException(status_code=404, detail="...")` — không return None.

### 2e. Migration Alembic
- **KHÔNG** dùng `Base.metadata.create_all()` trong production.
- Mỗi migration có `revision`, `down_revision`, `upgrade()`, `downgrade()`.
- Tên file: `NNN_<mô_tả_ngắn>.py` (ví dụ: `019_add_procurement_items.py`).
- Khi thêm Enum mới: dùng `sa.Enum(..., name="enumname", create_type=True)` trong upgrade, `op.execute("DROP TYPE enumname")` trong downgrade.

### 2f. AI Agent — thiên hướng cao
- Mọi action quan trọng → emit `await publish_event(type, data)` để FE real-time.
- Tool mới → đăng ký trong `list_tools_dynamic()` ở `tools/base.py`.
- Planner nhận tool list → LLM tạo plan JSON → Executor chạy parallel groups → Critic review → Reflector học.
- Kết quả tool → lưu vào `AiAuditLog` (tool_name, inputs, outputs, latency_ms).
- Human-in-the-loop: dùng `ClarificationPaused` exception + `AgentClarification` model khi agent cần hỏi người dùng.

---

## 3. Workflow tạo module mới

Khi nhận yêu cầu thêm feature mới, thực hiện theo thứ tự:

```
Step 1: Model (entities.py)
  → Thêm class mới + Enum nếu cần
  → Thêm relationship vào parent model

Step 2: Migration
  → Tạo alembic/versions/NNN_add_<tên>.py
  → upgrade(): create_table + indexes
  → downgrade(): drop_table + drop enum types

Step 3: Schema (schemas/<tên>.py)
  → Base schema (Create, Update, Out)
  → ConfigDict(from_attributes=True) cho Out schemas

Step 4: Service (services/<tên>_service.py)
  → Pure async functions nhận AsyncSession
  → Không có side effects ngoài DB (pub/sub = caller's responsibility)

Step 5: Router (routers/<tên>.py)
  → CRUD endpoints
  → Gọi publish_event() sau mutations
  → Đăng ký vào routers/__init__.py

Step 6: Seed (seeds/seed_<tên>.py)
  → Dữ liệu thực tế EVN context
```

Đọc `references/patterns.md` để xem code mẫu đầy đủ cho mỗi bước.

---

## 4. Seed dữ liệu thực tế (EVN context)

Seed script chạy được độc lập, idempotent (có thể chạy lại không bị duplicate).

**Cấu trúc seed script:**
```python
# seeds/seed_<tên>.py
import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.entities import User, UserRole

async def seed():
    async with async_session_factory() as session:
        # Idempotency check
        existing = await session.execute(select(User).where(User.email == "..."))
        if existing.scalar_one_or_none():
            return
        # Insert
        session.add(User(...))
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed())
```

**Dữ liệu thực tế EVN cần seed:**
- Users: 4 roles (admin, hdtv_leader, dept_head, specialist) — tên và đơn vị theo EVN
- Dossiers: hồ sơ mua sắm vật tư điện, thiết bị lưới điện, IT, xây lắp — với `doc_no` chuẩn EVN
- RiskRules: các quy tắc thẩm định theo Nghị định 24/2024 và Thông tư EVN
- Alerts: một số cảnh báo mẫu (ngân sách vượt, thiếu tài liệu pháp lý)

Đọc `references/evn_seed_data.md` để xem data mẫu thực tế.

---

## 5. Review & Fix module hiện có

Khi review code, kiểm tra theo checklist:

**Async/Await:**
- [ ] Không có `session.query()` (dùng `select()`)
- [ ] `await session.refresh(obj)` sau commit
- [ ] Relationships load với `selectinload()` không lazy
- [ ] Không `asyncio.run()` bên trong async function

**Type Safety:**
- [ ] Return type annotations đầy đủ trên service functions
- [ ] `Mapped[T]` cho mọi column (không dùng `Column()` kiểu cũ)
- [ ] Pydantic schema dùng `model_validate()` không `from_orm()`
- [ ] Optional fields: `Mapped[str | None]` với `nullable=True`

**Agent AI:**
- [ ] Tool results được log vào `AiAuditLog`
- [ ] Lỗi tool không crash toàn bộ plan (graceful degrade)
- [ ] `publish_event()` được gọi sau status change

**Logic:**
- [ ] `doc_no` unique check trước khi insert
- [ ] Pagination: offset + limit với `has_more` flag
- [ ] Không return sensitive data (password hash, internal keys)

---

## 6. LLM Router & Agent Roles

```python
from app.services.llm_router import AgentRole, llm_call

# Gọi LLM theo role
result = await llm_call(AgentRole.PLANNER, messages, response_format_json=True)

# Roles:
# PLANNER    → Gemma local — lập kế hoạch tool execution
# EXECUTOR   → Gemma local — điều phối tools
# LEGAL      → Gemini Flash — thẩm định pháp lý Nghị định 24/2024
# FINANCIAL  → Gemini Flash — kiểm tra ngân sách ERP
# OCR        → Gemini Flash — trích xuất văn bản PDF
# REFLECTOR  → Gemma local — phân tích kết quả, học từ feedback
# CRITIC     → Gemini Flash — kiểm duyệt báo cáo thẩm định
# SUMMARY    → Gemma local — tổng hợp báo cáo cuối
# TOOL_MOCK  → Gemini Flash — simulate tool chưa có real backend
```

Khi thêm specialist agent mới: thêm `AgentRole.NEW_ROLE` vào enum, thêm entry trong `ROLE_BACKENDS` dict trong `llm_router.py`, tạo prompt trong `orchestrator/prompts/`.

---

## 7. Các lỗi thường gặp & cách fix

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `MissingGreenlet` | Lazy load relationship trong async | Dùng `selectinload()` |
| `DetachedInstanceError` | Access attribute sau session close | `await session.refresh()` hoặc eager load |
| `greenlet_spawn` trong Celery | Sync ORM trong async worker | Dùng `run_sync()` hoặc `asyncio.run()` riêng |
| Alembic `DuplicateObject` | Enum type đã tồn tại | `create_type=False` trong migration |
| Pydantic `ValidationError` | `from_orm()` thay vì `model_validate()` | Đổi sang `model_validate()` |
| `JSONB default mutable` | `default={}` dùng chung object | Dùng `default=dict` (callable) |
| Tool timeout | LLM call quá lâu | Circuit breaker + fallback trong `llm_router.py` |

---

## 8. Seed Data từ file thực tế

Khi seed dossier có file PDF thật (trong `data/seed/`), dùng MinIO upload rồi lưu `pdf_url`:
```python
from app.services.minio_service import upload_file_to_minio
import aiofiles

async def upload_seed_pdf(session, dossier_id: int, file_path: str, filename: str):
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
    object_key = f"dossiers/{dossier_id}/{filename}"
    await upload_file_to_minio(content, object_key, "application/pdf")
    return object_key
```

Nếu MinIO chưa chạy trong môi trường seed, fallback bằng cách lưu path local:
```python
pdf_url = f"file://data/seed/dossier_198_uav/{filename}"  # fallback khi không có MinIO
```

## 9. Directory Structure Cần Tạo

**Hiện tại CHƯA tồn tại — phải tạo trước khi dùng:**
- `project_devops/apps/hdtv-ai-platform/seeds/` — seed scripts
- `project_devops/apps/hdtv-ai-platform/references/` — reference docs cho skill

**Migration hiện tại:** 001 → **018** (018_add_alert_title.py là migration cuối cùng). Migration mới bắt đầu từ **019**.

## 10. References

- **`references/patterns.md`** — Code mẫu đầy đủ: model, migration, schema, service, router, seed
- **`references/evn_seed_data.md`** — Dữ liệu seed thực tế EVN (users, dossiers, risk rules) dựa trên dossier UAV EVNHANOI
- **`references/agent_patterns.md`** — Pattern thiết kế orchestrator, tool mới, clarification flow

Đọc reference file phù hợp **trước khi** viết code cho từng loại task.