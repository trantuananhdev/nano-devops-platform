# Phase 12 — EVN Production Feature Complete

> **Mục tiêu:** Hoàn thiện đầy đủ các tính năng cho quy trình nghiệp vụ thực tế của EVN, bao gồm BE, FE, roles/permissions, status transitions, version control, audit trail, v.v.

---

## Status Legend: PENDING | IN_PROGRESS | DONE | BLOCKED

---

## T-43: User Roles & Permissions (BE)
- **deps**: —
- **priority**: P1 — cốt lõi cho quy trình
- **files**:
  - `hdtv-ai-platform/app/schemas/meta.py`: updated UserOut to match real User entity
  - `hdtv-ai-platform/app/services/meta_service.py`: updated list_users and list_roles to use real DB data
  - `hdtv-ai-platform/app/routers/meta.py`: updated /users and /roles endpoints to use DB
  - `hdtv-ai-platform/app/core/permissions.py`: NEW module with role-based permission checks
- **roles list**:
  1. `admin`: Quản trị viên, users
  2. `specialist`: Chuyên viên, tạo tờ trình, chỉnh sửa
  3. `dept_head`: Trưởng Ban, duyệt tờ trình trước khi lên HĐTV
  4. `hdtv_leader`: Lãnh đạo HĐTV, phê duyệt cuối cùng
- **acceptance**: Users and roles are fetched from DB; permission check utilities are available
- **verify cmd**: 
- **status**: DONE ✅

## T-44: User Roles & Permissions (FE)
- **deps**: T-43
- **priority**: P1
- **files**:
  - `hdtv-ai-prototype/src/views/SystemAdminView.vue`: updated to remove dept column, add ROLE_LABELS mapping, update status display using is_active
  - `hdtv-ai-prototype/src/stores/auth.js`: NEW — Pinia store for auth state and role checks
- **acceptance**: FE displays correct users/roles from API
- **verify cmd**: 
- **status**: DONE ✅

## T-45: Formal Status Transitions & Workflow (BE)
- **deps**: T-43
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/models/entities.py`: updated DossierStatus enum, added StatusHistory entity, added status_history relationship to Dossier
  - `hdtv-ai-platform/app/services/workflow_service.py`: NEW — service to handle status transitions and history
  - `hdtv-ai-platform/app/schemas/dossier.py`: added StatusTransitionRequest and StatusHistoryOut schemas
  - `hdtv-ai-platform/app/routers/dossiers.py`: added transition-status and status-history endpoints
  - `hdtv-ai-platform/scripts/seed.py`: updated DOSSIERS list with new status values
  - `hdtv-ai-platform/alembic/versions/013_add_status_history.py`: NEW — migration to create status_history table
- **acceptance**: Dossier status transitions follow valid workflow, history is tracked, permissions enforced
- **verify cmd**: 
- **status**: DONE ✅

---

## T-44: User Roles & Permissions (FE)
- **deps**: T-43
- **priority**: P1
- **files**:
  - `hdtv-ai-prototype/src/stores/auth.js` — thêm state roles
  - `hdtv-ai-prototype/src/router/index.js` — thêm route guards
  - `hdtv-ai-prototype/src/components/` — thêm role-based conditional rendering
- **acceptance**: Người dùng chỉ thấy/ làm được chức năng phù hợp với vai trò
- **verify_cmd**:
- **status**: DONE ✅

---

## T-45: Formal Status Transitions & Workflow (BE)
- **deps**: T-43
- **priority**: P1 — quy trình nghiệp vụ
- **status flow**: `DRAFT` → `SUBMITTED_TO_DEPT` → `DEPT_APPROVED` / `DEPT_REJECTED` → `SUBMITTED_TO_BOARD` → `BOARD_REVIEWED` → `APPROVED` / `REJECTED`
- **files**:
  - `hdtv-ai-platform/app/models/entities.py` — thêm trường `status` với enum, trường `status_history`
  - `hdtv-ai-platform/app/api/routes/dossiers.py` — thêm endpoints thay đổi status
  - `hdtv-ai-platform/app/services/workflow_service.py` — NEW: quản lý transitions
- **acceptance**: Status chỉ được thay đổi theo đúng luồng và role; status history được lưu lại
- **verify_cmd**:
- **status**: DONE ✅

---

## T-46: Formal Status Transitions & Workflow (FE)
- **deps**: T-45
- **priority**: P1
- **files**:
  - `hdtv-ai-prototype/src/views/DossierListView.vue` - cập nhật status badges
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` - thêm action buttons phù hợp status/role, thêm status history tab
  - `hdtv-ai-prototype/src/services/api.js` - thêm status transition API calls
  - `hdtv-ai-prototype/src/assets/main.css` - thêm btn-success/btn-danger styles
- **acceptance**: Action buttons (Trình lên Trưởng Ban, Trình lên HĐTV, Yêu cầu chỉnh sửa, Phê duyệt, Từ chối) hiển thị đúng role/status
- **verify_cmd**:
- **status**: DONE ✅

---

## T-47: Document Version Control (BE)
- **deps**: —
- **priority**: P2 — quan trọng cho kiểm toán
- **files**:
  - `hdtv-ai-platform/app/models/entities.py` — thêm bảng `document_versions` và relationship với Dossier
  - `hdtv-ai-platform/alembic/versions/016_add_document_versions.py` — new migration
  - `hdtv-ai-platform/app/schemas/dossier.py` — thêm DocumentVersion schemas
  - `hdtv-ai-platform/app/services/document_version_service.py` — new service
  - `hdtv-ai-platform/app/routers/dossiers.py` — thêm endpoints quản lý versions
- **acceptance**: Mỗi thay đổi tài liệu tạo version mới, lưu user, thời gian, mô tả thay đổi
- **verify_cmd**:
- **status**: DONE ✅

---

## T-48: Document Version Control (FE)
- **deps**: T-47
- **priority**: P2
- **files**:
  - `hdtv-ai-prototype/src/services/api.js` — thêm các API calls cho document versions
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — thêm tab "Phiên bản" để xem và tạo versions
- **acceptance**: Người dùng có thể xem các phiên bản cũ, chọn phiên bản để xem
- **verify_cmd**:
- **status**: DONE ✅

---

## T-49: Audit Trail (BE)
- **deps**: T-43
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/models/entities.py` — thêm bảng `audit_logs` (dossier_id, user_id, action, timestamp, metadata, ip_address)
  - `hdtv-ai-platform/app/services/audit_service.py` — NEW: audit log service
  - `hdtv-ai-platform/app/routers/audit.py` — NEW: audit endpoints
  - `hdtv-ai-platform/alembic/versions/014_add_audit_logs.py` — NEW: migration
  - `hdtv-ai-platform/app/schemas/dossier.py` — thêm audit schemas
- **acceptance**: Audit endpoints are available; audit log entity is defined
- **verify_cmd**:
- **status**: DONE ✅

---

## T-50: Audit Trail (FE)
- **deps**: T-49
- **priority**: P2
- **files**:
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — thêm tab "Lịch sử"
- **acceptance**: Người dùng có thể xem toàn bộ lịch sử hoạt động trên dossier
- **verify_cmd**:
- **status**: DONE ✅

---

## T-51: Reference Document Management (BE)
- **deps**: —
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/models/entities.py` — thêm bảng reference_documents và relationship với Dossier
  - `hdtv-ai-platform/alembic/versions/015_add_reference_documents.py` — new migration
  - `hdtv-ai-platform/app/schemas/dossier.py` — thêm ReferenceDocument schemas
  - `hdtv-ai-platform/app/services/reference_document_service.py` — new service
  - `hdtv-ai-platform/app/routers/dossiers.py` — thêm endpoints upload/xem/xóa tài liệu tham khảo
- **acceptance**: Người dùng có thể upload nhiều file PDF/Excel làm tài liệu tham khảo cho dossier
- **verify_cmd**:
- **status**: DONE ✅

---

## T-52: Reference Document Management (FE)
- **deps**: T-51
- **priority**: P1
- **files**:
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — cập nhật tab "Tài liệu Khác" để thực sự upload/xem file
  - `hdtv-ai-prototype/src/services/api.js` — thêm các API calls cho reference documents
- **acceptance**: Người dùng có thể upload file, xem list, xóa file
- **verify_cmd**:
- **status**: DONE ✅

---

## T-53: Notification System (BE)
- **deps**: T-43
- **priority**: P2
- **files**:
  - `hdtv-ai-platform/app/models/entities.py` — thêm bảng `notifications`
  - `hdtv-ai-platform/app/schemas/dossier.py` — thêm notification schemas
  - `hdtv-ai-platform/app/routers/notifications.py` — NEW: notifications endpoints
  - `hdtv-ai-platform/app/services/notification_service.py` — NEW: service gửi notification
  - `hdtv-ai-platform/app/services/workflow_service.py` — thêm trigger notification khi status thay đổi
  - `hdtv-ai-platform/app/routers/__init__.py` — register notifications router
  - `hdtv-ai-platform/alembic/versions/017_add_notifications.py` — NEW: migration
- **acceptance**: Notification được tạo khi status thay đổi, có feedback mới, v.v.
- **verify_cmd**:
- **status**: DONE ✅

---

## T-54: Notification System (FE)
- **deps**: T-53
- **priority**: P2
- **files**:
  - `hdtv-ai-prototype/src/components/NotificationBell.vue` — NEW: notification bell component
  - `hdtv-ai-prototype/src/views/NotificationsView.vue` — NEW: notifications page
  - `hdtv-ai-prototype/src/stores/notifications.js` — NEW: Pinia store for notifications state
  - `hdtv-ai-prototype/src/services/api.js` — added notification API calls
  - `hdtv-ai-prototype/src/router/index.js` — added notifications route
  - `hdtv-ai-prototype/src/App.vue` — integrated notification bell in sidebar
- **acceptance**: Người dùng thấy số thông báo mới, xem danh sách thông báo
- **verify_cmd**:
- **status**: DONE ✅

---

## Phase 12 Dependency Graph

| Task | Blocked by | Priority |
|------|------------|----------|
| T-43 | — | P1 |
| T-44 | T-43 | P1 |
| T-45 | T-43 | P1 |
| T-46 | T-45 | P1 |
| T-47 | — | P2 |
| T-48 | T-47 | P2 |
| T-49 | T-43 | P1 |
| T-50 | T-49 | P2 |
| T-51 | — | P1 |
| T-52 | T-51 | P1 |
| T-53 | T-43 | P2 |
| T-54 | T-53 | P2 |

**Thứ tự ưu tiên thực hiện:** T-43 → T-45 → T-49 → T-51 → T-44 → T-46 → T-52 → T-47 → T-48 → T-50 → T-53 → T-54

---

# Phase 13 — System-wide Module Audit & Optimization

> **Mục tiêu:** Rà soát, kiểm tra và tối ưu hóa từng module theo thứ tự: FE → BE → AI để đảm bảo chất lượng, nhất quán và sẵn sàng cho môi trường sản xuất.
>
> **Phương pháp:** Xem xét từng module một, kiểm tra:
> - Tính nhất quán với quy tắc code hiện tại
> - Thông tin đầy đủ trong PROJECT_STATE.md
> - Tích hợp giữa các module (FE <-> BE <-> AI)
> - Lỗi tiềm ẩn và case edge
> - Logging, error handling
> - Document (nếu cần)

---

## 1. Phần Frontend (FE) - Module by Module

### T-55: Audit DashboardView.vue
- **deps**: —
- **priority**: P1
- **files**: `hdtv-ai-prototype/src/views/DashboardView.vue`
- **checklist**:
  - Hiển thị đúng dữ liệu từ /api/v1/dashboard/summary
  - Tabs/navigation hoạt động đúng
  - Status badges hiển thị chính xác
  - Responsive trên các màn hình khác nhau
  - Loading states xử lý đúng
  - Error handling khi API trả về lỗi
- **acceptance**: Dashboard hoạt động ổn định, hiển thị đúng dữ liệu, xử lý lỗi tốt
- **status**: DONE ✅

### T-56: Audit DossierListView.vue
- **deps**: T-55
- **priority**: P1
- **files**: `hdtv-ai-prototype/src/views/DossierListView.vue`
- **checklist**:
  - Hiển thị danh sách tờ trình chính xác
  - Filter/sort hoạt động đúng
  - Status badges hiển thị đúng
  - Navigation đến Workspace hoạt động
  - Create new dossier button/flow
  - Error handling khi API lỗi
- **acceptance**: Dossier list hiển thị đầy đủ, hoạt động ổn định
- **status**: PENDING

### T-57: Audit SplitViewWorkspace.vue - Toàn bộ tab
- **deps**: T-56
- **priority**: P1
- **files**: `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue`
- **checklist**:
  - Tab "Tờ trình": PDF viewer tải đúng, presigned URL hoạt động
  - Tab "Phụ lục": (nếu có) hoạt động đúng
  - Tab "Tài liệu Khác": upload, xem, xóa reference documents
  - Tab "Phiên bản": xem, tạo document versions
  - Tab "Báo cáo Thẩm định": hiển thị đúng
  - Tab "Nghị quyết": hiển thị đúng
  - Tab AI (kết quả thẩm định): hiển thị đầy đủ, các tool calls
  - Tab Chat (ý kiến): gửi/nhận tin nhắn
  - Tab "Lịch sử Trạng thái": hiển thị status history
  - Tab "Lịch sử Hoạt động": hiển thị audit logs với user info
  - Action buttons thay đổi status hiển thị đúng theo role
- **acceptance**: Tất cả tab trong Workspace hoạt động đầy đủ và đúng chức năng
- **status**: PENDING

### T-58: Audit SystemAdminView.vue - Toàn bộ tab
- **deps**: T-57
- **priority**: P1
- **files**: `hdtv-ai-prototype/src/views/SystemAdminView.vue`
- **checklist**:
  - Tab Users/Roles: hiển thị đúng users/roles
  - Tab System Logs: hiển thị logs
  - Tab Agent Intelligence: hiển thị đúng metrics
  - Tab API Keys Management: create/delete API keys
  - Tab MCP Audit Logs: hiển thị logs
- **acceptance**: Tất cả tab Admin hoạt động đúng chức năng
- **status**: PENDING

### T-59: Audit NotificationsView.vue & NotificationBell.vue
- **deps**: T-58
- **priority**: P2
- **files**:
  - `hdtv-ai-prototype/src/views/NotificationsView.vue`
  - `hdtv-ai-prototype/src/components/NotificationBell.vue`
- **checklist**:
  - Notification bell hiển thị số lượng thông báo chưa đọc
  - Dropdown hiển thị thông báo
  - Mark as read / Mark all as read hoạt động
  - NotificationsView hiển thị đầy đủ, phân trang (nếu có)
- **acceptance**: Hệ thống thông báo hoạt động ổn định
- **status**: PENDING

### T-60: Audit Pinia Stores
- **deps**: T-59
- **priority**: P2
- **files**:
  - `hdtv-ai-prototype/src/stores/auth.js`
  - `hdtv-ai-prototype/src/stores/dossier.js`
  - `hdtv-ai-prototype/src/stores/notifications.js`
- **checklist**:
  - State được quản lý đúng
  - Actions gọi API đúng
  - Getters tính toán đúng
  - Error handling trong stores
- **acceptance**: Pinia stores hoạt động ổn định, nhất quán
- **status**: PENDING

### T-61: Audit api.js & API Calls
- **deps**: T-60
- **priority**: P2
- **files**: `hdtv-ai-prototype/src/services/api.js`
- **checklist**:
  - Tất cả endpoints có API calls
  - Error handling cho các calls
  - Auth headers/nếu cần
  - Response parsing đúng
  - Timeout/retry (nếu có)
- **acceptance**: Tất cả API calls hoạt động đúng
- **status**: PENDING

### T-62: Audit Router & Route Guards
- **deps**: T-61
- **priority**: P2
- **files**: `hdtv-ai-prototype/src/router/index.js`
- **checklist**:
  - Tất cả routes được định nghĩa đúng
  - Route guards kiểm tra role/permissions (nếu có)
  - Navigation giữa các pages hoạt động
- **acceptance**: Router hoạt động đúng, route guards hoạt động
- **status**: PENDING

---

## 2. Phần Backend (BE) - Module by Module

### T-63: Audit Entities & Database Models
- **deps**: —
- **priority**: P1
- **files**: `hdtv-ai-platform/app/models/entities.py`
- **checklist**:
  - Tất cả entities được định nghĩa đúng (Dossier, User, StatusHistory, AuditLog, ReferenceDocument, DocumentVersion, Notification, ...)
  - Relationships giữa entities đúng
  - Indexes được tạo đúng
  - Enum values đầy đủ và chính xác
  - Alembic migrations đầy đủ
- **acceptance**: Database models đầy đủ, chính xác
- **status**: PENDING

### T-64: Audit Schemas (Pydantic)
- **deps**: T-63
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/schemas/dossier.py`
  - `hdtv-ai-platform/app/schemas/meta.py`
  - `hdtv-ai-platform/app/schemas/feedback.py`
  - `hdtv-ai-platform/app/schemas/clarification.py`
  - `hdtv-ai-platform/app/schemas/api_key.py`
- **checklist**:
  - Tất cả schemas có đủ fields
  - Validation rules (nếu có) chính xác
  - From_attributes đúng cho tất cả schemas
- **acceptance**: Pydantic schemas đầy đủ, chính xác
- **status**: PENDING

### T-65: Audit Routers (FastAPI)
- **deps**: T-64
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/routers/dossiers.py`
  - `hdtv-ai-platform/app/routers/meta.py`
  - `hdtv-ai-platform/app/routers/audit.py`
  - `hdtv-ai-platform/app/routers/notifications.py`
  - `hdtv-ai-platform/app/routers/api_keys.py`
  - `hdtv-ai-platform/app/routers/mcp.py`
  - `hdtv-ai-platform/app/routers/feedback.py`
  - `hdtv-ai-platform/app/routers/clarifications.py`
  - `hdtv-ai-platform/app/routers/alerts.py`
  - `hdtv-ai-platform/app/routers/search.py`
  - `hdtv-ai-platform/app/routers/workflow.py`
  - `hdtv-ai-platform/app/routers/skills.py`
  - `hdtv-ai-platform/app/routers/knowledge_graph.py`
- **checklist**:
  - Tất cả endpoints có trong routers
  - Response models đúng
  - Error handling (HTTPException) đầy đủ
  - Depends đúng (get_db, permissions, ...)
  - Tags đúng cho OpenAPI docs
- **acceptance**: Tất cả FastAPI routers hoạt động đúng
- **status**: PENDING

### T-66: Audit Services (Business Logic)
- **deps**: T-65
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/services/meta_service.py`
  - `hdtv-ai-platform/app/services/audit_service.py`
  - `hdtv-ai-platform/app/services/workflow_service.py`
  - `hdtv-ai-platform/app/services/reference_document_service.py`
  - `hdtv-ai-platform/app/services/document_version_service.py`
  - `hdtv-ai-platform/app/services/notification_service.py`
  - `hdtv-ai-platform/app/services/minio_service.py`
- **checklist**:
  - Logic nghiệp vụ đúng
  - Error handling đầy đủ
  - Logging đầy đủ
  - Transactions đúng (nếu có)
- **acceptance**: Tất cả services hoạt động đúng
- **status**: PENDING

### T-67: Audit Core Modules
- **deps**: T-66
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/core/config.py`
  - `hdtv-ai-platform/app/core/permissions.py`
  - `hdtv-ai-platform/app/core/database.py`
  - `hdtv-ai-platform/app/core/circuit_breaker.py` (nếu có)
- **checklist**:
  - Config đúng, đầy đủ
  - Permissions logic đúng
  - Database connection đúng
  - Circuit breaker logic đúng
- **acceptance**: Core modules hoạt động đúng
- **status**: PENDING

### T-68: Audit Workers (Celery)
- **deps**: T-67
- **priority**: P2
- **files**:
  - `hdtv-ai-platform/app/workers/tasks.py`
  - `hdtv-ai-platform/app/workers/rag_pipeline.py` (nếu có)
  - `hdtv-ai-platform/app/workers/celery_app.py`
- **checklist**:
  - Tasks được định nghĩa đúng
  - Task queue đúng
  - Error handling trong tasks
  - RAG pipeline đúng (nếu có)
- **acceptance**: Celery workers hoạt động đúng
- **status**: PENDING

### T-69: Audit RAG & Vector Store
- **deps**: T-68
- **priority**: P2
- **files**:
  - `hdtv-ai-platform/app/services/memory/vector_store.py`
  - `hdtv-ai-platform/app/services/memory/retriever.py`
  - `hdtv-ai-platform/app/services/legal_rag.py` (nếu có)
  - `hdtv-ai-platform/app/services/rag/pdf_extractor.py`
- **checklist**:
  - Chroma connection đúng
  - Vector upsert/query đúng
  - PDF extract đúng
  - Text chunking đúng
- **acceptance**: RAG & Vector Store hoạt động đúng
- **status**: PENDING

### T-70: Audit Seed Script & Seed Data
- **deps**: T-69
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/scripts/seed.py`
  - `hdtv-ai-platform/data/seed/` (nếu có)
- **checklist**:
  - Seed script kiểm tra dữ liệu cũ trước khi insert
  - Tất cả seed data đúng
  - Dossier 198 được seed đầy đủ
  - Reference documents được upload đúng
  - Legal docs được ingest vào Chroma
- **acceptance**: Seed script chạy đầy đủ, không duplicate
- **status**: PENDING

---

## 3. Phần AI Agent - Module by Module

### T-71: Audit Orchestrator (Plan-Execute-Reflect-Critic)
- **deps**: —
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/services/orchestrator/planner.py`
  - `hdtv-ai-platform/app/services/orchestrator/executor.py`
  - `hdtv-ai-platform/app/services/orchestrator/reflector.py`
  - `hdtv-ai-platform/app/services/orchestrator/critic.py`
  - `hdtv-ai-platform/app/services/orchestrator/helpers.py`
  - `hdtv-ai-platform/app/services/orchestrator/batch_executor.py`
  - `hdtv-ai-platform/app/services/orchestrator/chain_executor.py`
  - `hdtv-ai-platform/app/services/orchestrator/prompt_builder.py`
- **checklist**:
  - Planner tạo plan đúng
  - Executor thực hiện plan đúng (song song, tuần tự, chain)
  - Reflector phản ánh đúng kết quả
  - Critic kiểm tra đúng
  - Role-specific prompts đúng
  - Memory retrieval đúng
- **acceptance**: Orchestrator hoạt động đúng, Plan-Execute-Reflect-Critic loop ổn định
- **status**: PENDING

### T-72: Audit Tools & Tool Handlers
- **deps**: T-71
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/tools/base.py`
  - `hdtv-ai-platform/app/tools/handlers/`
  - `hdtv-ai-platform/app/tools/registry.py` (nếu có)
- **checklist**:
  - Tất cả tools được định nghĩa đúng (ErpBudgetCheck, ErpInventoryCheck, DOfficeLookup, PmisProjectCheck, LegalGraphRAG, EcoOcrExtract, ...)
  - Input validation đúng
  - Output validation đúng
  - Error handling đúng
  - Retry logic đúng
  - Tool calls logged to ai_audit_logs
- **acceptance**: Tất cả AI tools hoạt động đúng
- **status**: PENDING

### T-73: Audit LLM Router & LLM Client
- **deps**: T-72
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/services/llm_router.py`
  - `hdtv-ai-platform/app/services/llm_client.py`
- **checklist**:
  - LLM router chọn đúng model/key
  - Key rotation đúng
  - Circuit breaker đúng
  - Error handling cho LLM calls
  - Prompt templating đúng
- **acceptance**: LLM Router & Client hoạt động đúng, ổn định
- **status**: PENDING

### T-74: Audit Human-in-the-Loop (HITL)
- **deps**: T-73
- **priority**: P2
- **files**:
  - `hdtv-ai-platform/app/services/orchestrator/clarification_service.py`
  - `hdtv-ai-platform/app/routers/clarifications.py`
- **checklist**:
  - Clarifications được tạo đúng khi cần
  - Answer clarification endpoint đúng
  - Resume appraisal đúng sau khi được answer
  - WS events đúng (clarification_needed, clarification_answered)
- **acceptance**: HITL hoạt động đúng
- **status**: PENDING

### T-75: Audit Feedback Loop & Learning
- **deps**: T-74
- **priority**: P2
- **files**:
  - `hdtv-ai-platform/app/routers/feedback.py`
  - `hdtv-ai-platform/app/services/feedback_service.py` (nếu có)
- **checklist**:
  - Submit feedback endpoint đúng
  - Feedback được lưu đúng
  - Feedback stats đúng
  - Feedback được retrieve để planner sử dụng
- **acceptance**: Feedback Loop hoạt động đúng
- **status**: PENDING

---

## Phase 13 Thứ tự ưu tiên thực hiện:
FE → BE → AI:
1. T-55 (DashboardView)
2. T-56 (DossierListView)
3. T-57 (SplitViewWorkspace)
4. T-58 (SystemAdminView)
5. T-59 (Notifications)
6. T-60 (Stores)
7. T-61 (api.js)
8. T-62 (Router)
9. T-63 (Entities/DB)
10. T-64 (Schemas)
11. T-65 (Routers)
12. T-66 (Services)
13. T-67 (Core)
14. T-68 (Workers)
15. T-69 (RAG/Vector)
16. T-70 (Seed)
17. T-71 (Orchestrator)
18. T-72 (Tools)
19. T-73 (LLM Router)
20. T-74 (HITL)
21. T-75 (Feedback)
