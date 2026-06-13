# HDTV AI Platform — Module Inventory
> Dùng làm checklist quét bug theo từng module. Mỗi module ghi rõ: file FE, store, backend router/service, API endpoints, trạng thái, và các điểm cần kiểm tra.

---

## Tổng quan kiến trúc

| Layer | Stack |
|---|---|
| Frontend | Vue 3 + Pinia + Vue Router (hdtv-ai-prototype) |
| Backend | FastAPI + SQLAlchemy async + PostgreSQL (hdtv-ai-platform) |
| AI Engine | Anthropic Claude qua orchestrator nội bộ |
| Search | Meilisearch |
| Storage | MinIO (PDF/file) |
| Realtime | WebSocket (ws.js ↔ ws.py) |
| Queue | Celery + Redis |
| Infra | Docker, Nginx, Alembic migrations |

---

## MODULE 01 — Dashboard

**Mục đích:** Trang tổng quan, hiển thị KPI, trạng thái hệ thống, alert nhanh.

| Thành phần | File |
|---|---|
| View | `src/views/DashboardView.vue` |
| Store | `src/stores/dashboard.js` |
| Backend Router | *(meta.py — `/dashboard/summary`)* |
| Backend Service | `app/services/meta_service.py` |
| API Endpoint | `GET /api/v1/dashboard/summary` |

**Điểm cần kiểm tra:**
- [ ] Data summary load đúng, không bị `undefined` khi API chậm
- [ ] Loading skeleton hiển thị trong lúc fetch
- [ ] Số liệu KPI (tổng hồ sơ, alert mở, pending) khớp với DB
- [ ] Test data đủ đa dạng trạng thái để demo chart

---

## MODULE 02 — Dossier (Hồ sơ)

**Mục đích:** Quản lý toàn bộ vòng đời hồ sơ: danh sách, tạo mới, upload PDF, xem chi tiết, chuyển trạng thái.

| Thành phần | File |
|---|---|
| View (danh sách) | `src/views/DossierListView.vue` |
| View (cài đặt/chi tiết) | `src/views/DossierSettingsView.vue` |
| Store | `src/stores/dossier.js` |
| Backend Router | `app/routers/dossiers.py` |
| Backend Service | `app/services/dossier_service.py` |
| API Endpoints | `GET /dossiers`, `POST /dossiers`, `GET /dossiers/{id}`, `POST /dossiers/{id}/upload`, `GET /dossiers/{id}/pdf-url`, `POST /dossiers/{id}/appraise`, `POST /dossiers/{id}/transition-status`, `GET /dossiers/{id}/status-history` |
| Migration | `001_initial.py`, `013_add_status_history.py` |

**Điểm cần kiểm tra:**
- [ ] Phân trang (offset/limit PAGE_SIZE=20) hoạt động đúng
- [ ] Filter theo `unit`, `status`, `risk_level` không bị lỗi khi kết hợp
- [ ] Upload PDF: multipart/form-data, timeout 60s, error handling nếu file quá lớn
- [ ] `pdf-url` presigned URL có expire không, FE xử lý hết hạn ra sao
- [ ] Status transition: validate đúng role (hdtv_leader/dept_head/admin), sai role phải báo lỗi
- [ ] Status history timeline hiển thị đúng thứ tự
- [ ] Test data: cần hồ sơ ở đủ 11 trạng thái cho demo

---

## MODULE 03 — AI Appraisal (Thẩm định AI)

**Mục đích:** Orchestrator AI tự động phân tích hồ sơ, sinh kết quả thẩm định, chạy critic/reflector.

| Thành phần | File |
|---|---|
| Trigger (FE) | `POST /dossiers/{id}/appraise` trong `DossierListView.vue` |
| Store | `src/stores/dossier.js` (appraiseDossier) |
| Backend Router | `app/routers/dossiers.py` → appraise endpoint |
| Orchestrator | `app/services/orchestrator/executor.py`, `planner.py`, `critic.py`, `reflector.py`, `react_agent.py` |
| Prompt System | `app/services/orchestrator/prompts/` (admin, dept_head, hdtv_leader, specialist) |
| Chain Executor | `app/services/orchestrator/chain_executor.py` |
| LLM Client | `app/services/llm_client.py`, `llm_router.py` |
| Model | `app/models/entities.py` → `AppraisalResult` |

**Điểm cần kiểm tra:**
- [ ] Circuit breaker hoạt động khi LLM timeout (`app/core/circuit_breaker.py`)
- [ ] Critic verdict được lưu đúng vào DB (migration `007_critic_verdict.py`)
- [ ] Tool chaining không bị treo vô hạn (`008_tool_chaining.py`)
- [ ] Agent plan được persist (`006_agent_plans.py`)
- [ ] Kết quả thẩm định hiển thị lên FE sau khi xong (WebSocket push hay polling?)
- [ ] Prompts theo role có đúng context không (hdtv_leader vs specialist)

---

## MODULE 04 — Workspace (Không gian làm việc)

**Mục đích:** Split-view xem PDF + chat AI song song, xem thông tin hồ sơ đầy đủ.

| Thành phần | File |
|---|---|
| View | `src/views/SplitViewWorkspace.vue` *(65KB — file lớn nhất)* |
| Route | `/workspace/:id?` |
| Store | `src/stores/dossier.js`, `src/stores/chat.js` |
| Backend | `GET /dossiers/{id}/pdf-url`, WebSocket `/ws` |

**Điểm cần kiểm tra:**
- [ ] PDF viewer load đúng presigned URL, không bị CORS
- [ ] Resize split-panel không bị layout vỡ trên màn hình nhỏ
- [ ] Chat trong workspace dùng đúng context dossier_id
- [ ] Lazy load view (~2MB nếu có bpmn-js) không block UI
- [ ] Khi không có `id` trong route (workspace mới), FE xử lý gracefully

---

## MODULE 05 — Advanced Chat (Chat AI)

**Mục đích:** Giao diện chat đa năng với AI, hỗ trợ clarification, tool use, streaming.

| Thành phần | File |
|---|---|
| View | `src/views/AdvancedChatView.vue` |
| Store | `src/stores/chat.js` |
| Component | `src/components/FloatingChat.vue` |
| WebSocket | `src/services/ws.js` ↔ `app/routers/ws.py` |
| Backend Service | `app/services/pubsub.py` |

**Điểm cần kiểm tra:**
- [ ] WebSocket reconnect khi mất kết nối
- [ ] Streaming response hiển thị từng token, không bị lag
- [ ] Clarification request từ AI hiển thị đúng dạng (form/button)
- [ ] Lịch sử chat giữ đúng `conversation_id` khi route thay đổi
- [ ] FloatingChat (chat nổi) không đè lên các element khác

---

## MODULE 06 — Human-in-the-Loop Clarifications

**Mục đích:** AI tạm dừng, yêu cầu người dùng xác nhận/bổ sung thông tin trước khi tiếp tục.

| Thành phần | File |
|---|---|
| View | *(tích hợp trong AdvancedChatView / Workspace)* |
| Backend Router | `app/routers/clarifications.py` |
| Backend Service | `app/services/clarification_service.py` |
| Schema | `app/schemas/clarification.py` |
| API Endpoints | `GET /clarifications/pending`, `POST /clarifications/{id}/answer` |
| Migration | `009_agent_clarifications.py` |

**Điểm cần kiểm tra:**
- [ ] Pending clarification hiển thị đúng cho đúng user/dossier
- [ ] Sau khi trả lời, agent tiếp tục đúng flow
- [ ] Nếu user bỏ qua clarification, hệ thống không bị treo
- [ ] Thông báo clarification qua Notification module

---

## MODULE 07 — Alerts (Cảnh báo)

**Mục đích:** Hiển thị và quản lý các cảnh báo rủi ro do AI sinh ra.

| Thành phần | File |
|---|---|
| View | `src/views/AlertsView.vue` |
| Store | `src/stores/alerts.js` |
| Backend Router | `app/routers/alerts.py` |
| API Endpoints | `GET /alerts`, `PATCH /alerts/{id}/resolve` |
| Migration | `018_add_alert_title.py` |

**Điểm cần kiểm tra:**
- [ ] Filter theo status (open/resolved), risk_level hoạt động
- [ ] `resolve` action cập nhật UI ngay (optimistic update hay refetch?)
- [ ] Alert có `title` field sau migration 018 — FE phải hiển thị
- [ ] Test data: cần alert với đủ mức risk (high/medium/low)

---

## MODULE 08 — Notifications (Thông báo)

**Mục đích:** Hệ thống thông báo realtime cho người dùng về các sự kiện quan trọng.

| Thành phần | File |
|---|---|
| View | `src/views/NotificationsView.vue` |
| Component | `src/components/NotificationBell.vue` |
| Store | `src/stores/notifications.js` |
| Backend Router | `app/routers/notifications.py` |
| Backend Service | `app/services/notification_service.py` |
| API Endpoints | `GET /notifications/user/{userId}`, `PATCH /notifications/{id}`, `PATCH /notifications/user/{userId}/mark-all-read`, `POST /notifications` |
| Migration | `017_add_notifications.py` |

**Điểm cần kiểm tra:**
- [ ] Badge số thông báo chưa đọc cập nhật realtime
- [ ] `mark-all-read` xóa badge, danh sách cập nhật đúng
- [ ] NotificationType đủ loại: status_change, appraisal_complete, clarification_requested...
- [ ] Phân trang thông báo nếu có nhiều
- [ ] Test data: seed đủ loại notification cho demo

---

## MODULE 09 — Knowledge Graph

**Mục đích:** Trực quan hóa mối liên hệ giữa các thực thể trong hồ sơ.

| Thành phần | File |
|---|---|
| View | `src/views/KnowledgeGraphView.vue` |
| Store | `src/stores/graph.js` |
| API Endpoint | `GET /knowledge-graph?dossier_id=` |

**Điểm cần kiểm tra:**
- [ ] Graph render đúng với thư viện đang dùng (d3/vis-network?)
- [ ] Filter theo dossier_id hoạt động
- [ ] Khi không có data, hiển thị empty state rõ ràng
- [ ] Performance với nhiều node (>100 nodes có lag không)

---

## MODULE 10 — Workflow Manager (BPMN)

**Mục đích:** Quản lý và vẽ quy trình làm việc bằng BPMN diagram.

| Thành phần | File |
|---|---|
| View | `src/views/WorkflowManager.vue` |
| Store | `src/stores/workflow.js` |
| Backend Router | `app/routers/workflow.py` |
| Backend Service | `app/services/workflow_service.py` |
| API Endpoints | `GET /workflows`, `GET /workflows/{dossierId}`, `PUT /workflows/{dossierId}` |
| Migration | `002_add_workflow_diagrams.py` |

**Điểm cần kiểm tra:**
- [ ] BPMN editor (bpmn-js ~2MB) lazy load đúng
- [ ] Save/load XML workflow không bị corrupt
- [ ] Liên kết đúng với dossier_id
- [ ] Khi bpmn-js init fail, FE không crash toàn trang

---

## MODULE 11 — Skill Builder

**Mục đích:** Xây dựng và quản lý các skill/prompt tùy chỉnh cho agent AI.

| Thành phần | File |
|---|---|
| View | `src/views/SkillBuilderView.vue` |
| Store | `src/stores/skills.js` |
| API Endpoint | `GET /skills` |

**Điểm cần kiểm tra:**
- [ ] CRUD skill (create/edit/delete) hoàn chỉnh hay chỉ có GET?
- [ ] Skill được agent sử dụng thực tế chưa hay chỉ là UI placeholder?
- [ ] Validate input skill (tên, prompt template) trước khi lưu

---

## MODULE 12 — Tool Registry

**Mục đích:** Đăng ký và quản lý các tool mà agent có thể sử dụng.

| Thành phần | File |
|---|---|
| View | `src/views/ToolRegistryView.vue` |
| Store | `src/stores/tools.js` |
| Backend | `app/services/tools/` (base, batch_executor, docker_sandbox, legal_rag, sandbox_executor) |
| API Endpoint | `GET /tools` |

**Điểm cần kiểm tra:**
- [ ] Danh sách tool hiển thị đúng (tên, mô tả, trạng thái)
- [ ] Docker sandbox tool có cần Docker daemon không — mock hay thật?
- [ ] `gemini_mock.py` — đây là mock, cần ghi chú rõ trong UI
- [ ] Tool enable/disable có backend support chưa?

---

## MODULE 13 — Schedule Manager (Lịch trình)

**Mục đích:** Quản lý lịch chạy tác vụ tự động (cron-like).

| Thành phần | File |
|---|---|
| View | `src/views/ScheduleManagerView.vue` |
| Store | `src/stores/schedule.js` |
| API Endpoint | `GET /schedules` |

**Điểm cần kiểm tra:**
- [ ] CRUD schedule hay chỉ xem?
- [ ] Liên kết với Celery worker (`app/workers/tasks.py`)?
- [ ] Timezone xử lý đúng (Hà Nội GMT+7)?

---

## MODULE 14 — MCP Integration

**Mục đích:** Kết nối và log các lời gọi tới MCP (Model Context Protocol) server bên ngoài.

| Thành phần | File |
|---|---|
| Backend Router | `app/routers/mcp.py` |
| API Endpoints | `GET /mcp/audit-logs` |
| Migration | `012_mcp_call_logs.py` |

**Điểm cần kiểm tra:**
- [ ] MCP audit log hiển thị đúng ở SystemAdminView
- [ ] MCP call có circuit breaker không?
- [ ] ERP handler (`app/tools/handlers/erp_handler.py`) — mock hay thật?

---

## MODULE 15 — API Key Management

**Mục đích:** Quản lý API keys cho tích hợp bên ngoài.

| Thành phần | File |
|---|---|
| View | *(trong SystemAdminView)* |
| Store | `src/stores/admin.js` |
| Backend Router | `app/routers/api_keys.py` |
| Backend Service | `app/services/api_key_service.py` |
| Schema | `app/schemas/api_key.py` |
| API Endpoints | `GET /api-keys`, `POST /api-keys`, `DELETE /api-keys/{id}` |
| Migration | `011_add_api_keys.py` |

**Điểm cần kiểm tra:**
- [ ] Key chỉ hiển thị 1 lần sau khi tạo (không lưu plaintext)
- [ ] Delete key cần confirm dialog
- [ ] Scope/permission của key có được validate ở middleware không?

---

## MODULE 16 — System Admin

**Mục đích:** Bảng điều khiển quản trị: users, roles, system logs, metrics, API keys, MCP logs.

| Thành phần | File |
|---|---|
| View | `src/views/SystemAdminView.vue` *(32KB)* |
| Store | `src/stores/admin.js` |
| Backend Router | `app/routers/meta.py` |
| API Endpoints | `GET /users`, `GET /roles`, `GET /system-logs`, `GET /agent/metrics`, `GET /agent/models`, `GET /feedback/stats`, `GET /audit-logs` |
| Backend Service | `app/services/agent_metrics_service.py` |

**Điểm cần kiểm tra:**
- [ ] Route guard đúng: chỉ role `admin` vào được (`meta: { requiresRole: ['admin'] }`)
- [ ] Agent metrics chart hiển thị đúng dữ liệu
- [ ] Multi-model registry (`GET /agent/models`) — hiển thị model nào đang active
- [ ] Feedback stats cho learning loop
- [ ] Test data: cần user với đủ 4 role

---

## MODULE 17 — Audit Trail

**Mục đích:** Ghi log toàn bộ hành động của agent và người dùng để truy vết.

| Thành phần | File |
|---|---|
| View | *(tích hợp trong SystemAdminView + DossierSettingsView)* |
| Backend Router | `app/routers/audit.py` |
| Backend Service | `app/services/audit_service.py` |
| API Endpoints | `GET /audit-logs`, `GET /audit-logs/{id}` (filter theo dossier_id) |
| Migration | `010_audit_log_harness.py`, `014_add_audit_logs.py` |

**Điểm cần kiểm tra:**
- [ ] Audit log có ghi đúng user_id, action, timestamp
- [ ] Filter theo dossier_id hoạt động
- [ ] AI audit log (`getAiAuditLogs`) vs user audit log — phân biệt rõ ràng trong UI?

---

## MODULE 18 — Reference Documents

**Mục đích:** Upload và quản lý tài liệu tham chiếu đính kèm hồ sơ.

| Thành phần | File |
|---|---|
| View | *(trong DossierSettingsView / SplitViewWorkspace)* |
| Backend Service | `app/services/reference_document_service.py` |
| API Endpoints | `GET /dossiers/{id}/reference-documents`, `POST /dossiers/{id}/reference-documents`, `DELETE /dossiers/{id}/reference-documents/{docId}` |
| Migration | `015_add_reference_documents.py` |

**Điểm cần kiểm tra:**
- [ ] Upload nhiều file cùng lúc có hỗ trợ không?
- [ ] MinIO lưu đúng bucket và path?
- [ ] Delete document có xóa khỏi MinIO không hay chỉ xóa DB record?

---

## MODULE 19 — Document Version Control

**Mục đích:** Lưu lịch sử phiên bản văn bản/nội dung của hồ sơ.

| Thành phần | File |
|---|---|
| Backend Service | `app/services/document_version_service.py` |
| API Endpoints | `GET /dossiers/{id}/document-versions`, `GET /dossiers/{id}/document-versions/latest`, `GET /dossiers/{id}/document-versions/{versionId}`, `POST /dossiers/{id}/document-versions` |
| Migration | `016_add_document_versions.py` |

**Điểm cần kiểm tra:**
- [ ] Version number tăng tự động, không bị conflict
- [ ] So sánh diff giữa 2 version có UI không?
- [ ] Latest version được cache hay query trực tiếp?

---

## MODULE 20 — Memory & RAG

**Mục đích:** Hệ thống bộ nhớ vector và RAG (Retrieval-Augmented Generation) cho agent.

| Thành phần | File |
|---|---|
| Memory Services | `app/services/memory/vector_store.py`, `retriever.py`, `preference_service.py` |
| RAG | `app/services/rag/pdf_extractor.py` |
| Worker | `app/workers/rag_pipeline.py` |
| Migration | `004_add_memory_embeddings.py`, `005_user_preferences.py` |

**Điểm cần kiểm tra:**
- [ ] PDF text extraction chạy async qua Celery worker
- [ ] Vector store (pgvector?) kết nối đúng
- [ ] Preference service lưu đúng user_id
- [ ] RAG retrieval có trả về context đúng hồ sơ không?

---

## MODULE 21 — Feedback & Learning Loop

**Mục đích:** Thu thập phản hồi về kết quả AI để cải thiện model.

| Thành phần | File |
|---|---|
| Backend Router | `app/routers/feedback.py` |
| Backend Service | `app/services/feedback_service.py` |
| Schema | `app/schemas/feedback.py` |
| API Endpoints | `POST /dossiers/{id}/feedback`, `GET /feedback/stats` |

**Điểm cần kiểm tra:**
- [ ] Feedback UI trong DossierSettingsView có đủ (rating + comment)?
- [ ] Stats aggregate đúng (accuracy rate, avg score)?
- [ ] Feedback có thực sự feed ngược vào prompt không hay chỉ lưu DB?

---

## MODULE 22 — Search (Tìm kiếm)

**Mục đích:** Full-text search hồ sơ qua Meilisearch.

| Thành phần | File |
|---|---|
| Component | `src/components/GlobalSearch.vue` |
| Store | `src/stores/search.js` |
| Backend Router | `app/routers/search.py` |
| Backend Service | `app/services/search_service.py` |
| API Endpoint | `GET /search` |

**Điểm cần kiểm tra:**
- [ ] Search history lưu vào localStorage (key: `hdtv_search_history`)
- [ ] Meilisearch index được warm-up khi startup (`_warmup_search`)
- [ ] Debounce input tránh quá nhiều request
- [ ] Kết quả highlight đúng keyword
- [ ] Search trả về đủ fields để render card kết quả

---

## MODULE 23 — Auth & RBAC

**Mục đích:** Xác thực và phân quyền theo role.

| Thành phần | File |
|---|---|
| Store | `src/stores/auth.js` |
| Backend | `app/core/permissions.py` |
| Router Guard | `src/router/index.js` |

**Roles:** `admin`, `hdtv_leader`, `dept_head`, `specialist`

**Điểm cần kiểm tra:**
- [ ] `auth.js` đang dùng `mockUsers` — chưa có real auth backend!
- [ ] Route guard (`requiresAuth`, `requiresRole`) hoạt động đúng
- [ ] Permission check ở backend (`permissions.py`) có khớp với FE không?
- [ ] JWT hay session-based? Hiện tại FE là mock hoàn toàn
- [ ] Demo cần 4 user account cho 4 role

---

## MODULE 24 — WebSocket & Realtime

**Mục đích:** Kênh realtime giữa FE và Backend cho streaming AI, thông báo tức thì.

| Thành phần | File |
|---|---|
| Frontend | `src/services/ws.js` |
| Backend Router | `app/routers/ws.py` |
| Pub/Sub | `app/services/pubsub.py` |

**Điểm cần kiểm tra:**
- [ ] Reconnect logic khi mất mạng
- [ ] Multiple tab cùng user có conflict không?
- [ ] Message format thống nhất giữa FE và BE
- [ ] Rate limiting áp dụng cho WS connection không?

---

## MODULE 25 — Infrastructure / Core

**Mục đích:** Các thành phần hạ tầng dùng chung toàn hệ thống.

| Thành phần | File |
|---|---|
| Config | `app/core/config.py` |
| Database | `app/core/database.py` |
| Rate Limiter | `app/core/rate_limiter.py` |
| Circuit Breaker | `app/core/circuit_breaker.py` |
| Metrics (Prometheus) | `app/core/metrics.py` |
| Tracing (OTel) | `app/core/tracing.py` |
| Context Manager | `app/core/context_manager.py` |
| Celery | `app/workers/celery_app.py` |

**Điểm cần kiểm tra:**
- [ ] `.env` có đủ biến: `DATABASE_URL`, `REDIS_URL`, `MINIO_*`, `ANTHROPIC_API_KEY`
- [ ] Rate limiter Redis connection fail thì app có start được không?
- [ ] Circuit breaker thresholds có phù hợp cho demo không?
- [ ] Alembic migrations chạy đủ 018 bước không bị lỗi

---

## Bảng tổng hợp nhanh

| # | Module | View FE | Store | Backend Router | Mức độ hoàn thiện |
|---|---|---|---|---|---|
| 01 | Dashboard | DashboardView | dashboard | meta | 🟡 Cần test data |
| 02 | Dossier | DossierListView, DossierSettingsView | dossier | dossiers | 🟡 Status transition cần test kỹ |
| 03 | AI Appraisal | *(trigger từ Dossier)* | dossier | dossiers | 🔴 Core — cần test end-to-end |
| 04 | Workspace | SplitViewWorkspace | dossier, chat | dossiers, ws | 🟡 File lớn 65KB |
| 05 | Advanced Chat | AdvancedChatView | chat | ws | 🟡 Streaming cần kiểm tra |
| 06 | Clarifications | *(embedded)* | chat | clarifications | 🔴 Flow phức tạp |
| 07 | Alerts | AlertsView | alerts | alerts | 🟢 Tương đối đơn giản |
| 08 | Notifications | NotificationsView | notifications | notifications | 🟡 Realtime badge |
| 09 | Knowledge Graph | KnowledgeGraphView | graph | *(meta)* | 🟡 Data source chưa rõ |
| 10 | Workflow BPMN | WorkflowManager | workflow | workflow | 🟡 bpmn-js nặng |
| 11 | Skill Builder | SkillBuilderView | skills | *(meta)* | 🔴 CRUD chưa rõ |
| 12 | Tool Registry | ToolRegistryView | tools | *(meta)* | 🟡 Mock tools |
| 13 | Schedule | ScheduleManagerView | schedule | *(meta)* | 🔴 Chưa rõ Celery link |
| 14 | MCP | *(admin)* | admin | mcp | 🟡 Audit log |
| 15 | API Keys | *(admin)* | admin | api_keys | 🟢 CRUD rõ ràng |
| 16 | System Admin | SystemAdminView | admin | meta | 🟡 Nhiều sub-section |
| 17 | Audit Trail | *(embedded)* | — | audit | 🟢 Đơn giản |
| 18 | Reference Docs | *(embedded)* | — | dossiers | 🟡 MinIO flow |
| 19 | Doc Versions | *(embedded)* | — | dossiers | 🟡 Version logic |
| 20 | Memory & RAG | — | — | *(internal)* | 🔴 Backend-only, cần verify |
| 21 | Feedback | *(embedded)* | — | feedback | 🟡 Stats display |
| 22 | Search | GlobalSearch | search | search | 🟢 Meilisearch warm-up |
| 23 | Auth & RBAC | — | auth | *(permissions)* | 🔴 Mock auth — cần real impl |
| 24 | WebSocket | — | — | ws | 🟡 Reconnect logic |
| 25 | Infrastructure | — | — | core/* | 🟡 Env config |

**Chú thích:** 🟢 Ổn định &nbsp; 🟡 Cần review/fix nhỏ &nbsp; 🔴 Rủi ro cao / chưa hoàn thiện

---

## Gợi ý thứ tự quét theo mức độ ưu tiên

**Ưu tiên 1 — Core flow (demo bị chết nếu module này lỗi):**
Module 02 Dossier → 03 AI Appraisal → 05 Chat → 23 Auth

**Ưu tiên 2 — UI hoàn thiện cho demo:**
Module 01 Dashboard → 07 Alerts → 08 Notifications → 04 Workspace

**Ưu tiên 3 — Tính năng nâng cao:**
Module 10 Workflow → 09 Graph → 06 Clarifications → 22 Search

**Ưu tiên 4 — Admin & Infrastructure:**
Module 16 System Admin → 15 API Keys → 25 Infrastructure → 20 Memory/RAG
