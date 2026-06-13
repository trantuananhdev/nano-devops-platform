# Requirements Document

## Introduction

HDTV AI Platform là hệ thống AI thẩm định hồ sơ cho EVNHANOI (Tổng Công ty Điện lực TP Hà Nội). Hệ thống vận hành theo kiến trúc Agentic (Planner → Executor → Reflector → Critic) trên nền stack FastAPI + Celery + PostgreSQL + Redis + ChromaDB + MinIO + Meilisearch, với FE Vue 3 + Pinia.

**Trạng thái hiện tại:** `PARTIAL` — stack chạy được 12/14 dịch vụ; luồng end-to-end trên VM chưa được verify. Còn tồn tại nhiều bug vặt về field mapping FE↔BE, route ordering, WebSocket race condition, hardcode data, và thiếu seed data cho Dossier #198 (UAV).

**Mục tiêu:** định nghĩa đầy đủ các yêu cầu để: (1) hoàn thiện 13 module FE không hardcode, (2) fix toàn bộ bug đã biết FE và BE, (3) đảm bảo field name nhất quán FE↔BE, (4) seed đủ dữ liệu demo Dossier #198 UAV, (5) WS events bắn đúng thứ tự, (6) mọi API call có error handling, (7) route guard không block nhầm.

---

## Glossary

- **HĐTV**: Hội đồng Thành viên — cơ quan quyết định cao nhất của EVNHANOI
- **Tờ trình**: Văn bản chính thức trình HĐTV để phê duyệt một quyết định/kế hoạch
- **Dossier**: Hồ sơ tờ trình trong hệ thống, đơn vị dữ liệu trung tâm
- **Thẩm định**: Quá trình AI phân tích, đối chiếu và đánh giá rủi ro của một Dossier
- **TMĐT**: Tổng mức đầu tư — giá trị tài chính của một dự án
- **Phiếu trình**: Văn bản xin ý kiến các thành viên HĐTV (thường kèm tờ trình)
- **Nghị quyết**: Văn bản kết luận của HĐTV sau khi xét duyệt tờ trình
- **Bao_cao_Tham_dinh**: Output của AI Agent — tổng hợp kết quả kiểm tra và khuyến nghị
- **DossierStatus**: Enum trạng thái hồ sơ: `draft`, `pending`, `appraising`, `submitted_to_dept`, `dept_approved`, `dept_rejected`, `submitted_to_board`, `board_reviewed`, `approved`, `rejected`, `needs_revision`
- **RiskLevel**: Enum mức rủi ro: `high`, `medium`, `low`
- **Appraisal_Pipeline**: Chuỗi Celery tasks: Planner → Executor → Reflector → Critic
- **WS_Event**: WebSocket event được BE emit về FE theo thứ tự: `task_started` → `plan_created` → `tool_executing`/`tool_result` (N lần) → `critic_review`
- **Dossier_198**: Tờ trình 198/TTr-EVNHANOI về "Phê duyệt Tiêu chuẩn kỹ thuật UAV phục vụ kiểm tra đường dây 220/110kV"
- **Knowledge_Graph**: Đồ thị suy luận biểu diễn quan hệ giữa Dossier, căn cứ pháp lý, rủi ro và các tool đã dùng
- **MCP**: Model Context Protocol — giao thức expose tool cho agent ngoài
- **Platform**: Toàn bộ hệ thống HDTV AI Platform (FastAPI API + FE Vue 3)
- **mapDossier**: Hàm FE trong `dossier.js` ánh xạ API response sang domain model FE

---

## Requirements

### Requirement 1: Dashboard Module — Wire Thực Tế và Hiển Thị Đúng Dữ Liệu

**User Story:** As a Lãnh đạo HĐTV, I want xem tổng quan toàn hệ thống ngay khi truy cập Dashboard, so that tôi nắm bắt tình trạng mà không cần vào từng module.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/dashboard`, THE Platform SHALL gọi `GET /api/v1/dashboard/summary` và render toàn bộ chỉ số từ response (không hardcode giá trị).
2. THE Dashboard SHALL hiển thị các chỉ số `pending_count`, `high_risk_count`, `approved_count`, `open_alerts` từ trường tương ứng trong `DashboardSummaryOut`.
3. THE Dashboard SHALL hiển thị danh sách `notable_dossiers` (tối đa 10 hồ sơ) với các trường `id`, `title`, `dept`, `date`, `risk`, `status`.
4. THE Dashboard SHALL hiển thị danh sách `newest_dossiers` (tối đa 5 hồ sơ) với các trường `doc_no`, `title`, `unit`, `date`, `risk_level`, `status`.
5. THE Dashboard SHALL hiển thị biểu đồ phân bổ nguồn cảnh báo `alert_sources` theo dữ liệu từ API, không dùng fallback hardcode khi API trả dữ liệu thật.
6. IF `GET /api/v1/dashboard/summary` trả lỗi HTTP, THEN THE Dashboard SHALL hiển thị thông báo lỗi thay vì màn hình trắng.
7. THE Dashboard SHALL gọi `GET /api/v1/agent/models` và hiển thị bảng AI Models với cặp `role → model_name` từ response.
8. WHEN dữ liệu Dashboard đã load, THE Dashboard SHALL hiển thị Dossier_198 trong `notable_dossiers` nếu bản ghi tồn tại trong database.

### Requirement 2: Dossier List Module — Pagination, Filter và Router Bug Fix

**User Story:** As a Chuyên viên, I want xem danh sách hồ sơ với phân trang vô hạn và lọc theo Ban/rủi ro, so that tôi tìm và xử lý hồ sơ nhanh chóng.

#### Acceptance Criteria

1. WHEN `DossierListView` khởi tạo, THE Platform SHALL gọi `GET /api/v1/dossiers?offset=0&limit=20` và render danh sách hồ sơ từ `DossierPage.items`.
2. THE Platform SHALL ánh xạ trường `risk_level` từ BE response sang trường `risk` trong mapDossier, vì `DossierOut` schema trả `risk_level` không phải `risk`.
3. WHEN người dùng kéo xuống cuối danh sách, THE Platform SHALL gọi `GET /api/v1/dossiers?offset=N&limit=20` và append hồ sơ vào danh sách hiện có.
4. THE Platform SHALL đăng ký route `GET /dossiers/units` TRƯỚC route `GET /dossiers/{dossier_id}` trong FastAPI router để tránh FastAPI nhầm chuỗi "units" là `dossier_id` integer và trả HTTP 422.
5. WHEN `DossierListView` khởi tạo, THE Platform SHALL gọi `GET /api/v1/dossiers/units` để lấy danh sách đơn vị cho dropdown lọc.
6. IF `GET /api/v1/dossiers/units` trả lỗi HTTP, THEN THE Platform SHALL tiếp tục hoạt động với dropdown lọc rỗng (non-critical).
7. THE Platform SHALL lọc danh sách hồ sơ theo `unit` và `risk` phía FE mà không gọi API mới.
8. WHEN người dùng hoàn thành wizard tạo Dossier (3 bước: Metadata → PDF Upload → Hoàn tất), THE Platform SHALL gọi `POST /api/v1/dossiers` và prepend hồ sơ mới vào đầu danh sách.
9. IF `POST /api/v1/dossiers` trả HTTP 409, THEN THE Platform SHALL hiển thị thông báo "Ký hiệu tờ trình đã tồn tại" thay vì lỗi generic.
10. IF file PDF vượt quá 20MB, THEN THE Platform SHALL từ chối file phía FE trước khi gọi `POST /api/v1/dossiers/{id}/upload`.

### Requirement 3: Workspace Module — Xóa Hardcode và Wire API Đầy Đủ

**User Story:** As a Lãnh đạo HĐTV, I want xem đầy đủ nội dung hồ sơ và theo dõi kết quả thẩm định AI real-time, so that tôi ra quyết định phê duyệt có cơ sở.

#### Acceptance Criteria

1. WHEN người dùng mở `/workspace/:id`, THE Platform SHALL gọi `GET /api/v1/dossiers/:id` và render metadata từ `DossierDetail` response mà không dùng hardcode.
2. THE Platform SHALL lấy danh sách kiểm tra AI từ `DossierDetail.appraisal.plan_steps` thay vì hardcode array `aiChecks` trong component.
3. THE Platform SHALL lấy danh sách phiên bản báo cáo từ `GET /api/v1/dossiers/:id/document-versions` thay vì hardcode `reportVersions`.
4. WHEN người dùng bấm "Chạy thẩm định", THE Platform SHALL gọi `POST /api/v1/dossiers/:id/appraise` và nhận `AppraiseResponse` với `status: "queued"`.
5. WHEN `POST /appraise` trả HTTP 202, THE Platform SHALL mở WebSocket `WS /ws/appraisal/:id` và lắng nghe events.
6. WHEN WS nhận event `plan_created`, THE Platform SHALL cập nhật `aiChecks` hiển thị các bước kế hoạch với trạng thái `pending`.
7. WHEN WS nhận event `tool_result`, THE Platform SHALL cập nhật trạng thái của step tương ứng (pass/fail/warning).
8. WHEN WS nhận event `critic_review`, THE Platform SHALL hiển thị verdict của Critic Agent và nội dung khuyến nghị.
9. THE Platform SHALL lấy `referenceDocs` từ `GET /api/v1/dossiers/:id/reference-documents` thay vì hardcode.
10. WHEN WS bị ngắt kết nối bất ngờ, THE Platform SHALL thử reconnect tối đa 3 lần với backoff 2s, 5s, 10s.
11. IF sau 3 lần reconnect vẫn thất bại, THEN THE Platform SHALL hiển thị thông báo lỗi kết nối.
12. THE Platform SHALL hiển thị Dossier_198 với đầy đủ nội dung 5 checks từ API, không placeholder "Lorem ipsum".

### Requirement 4: Advanced Chat Module — Lịch Sử Audit Log và WS Integration

**User Story:** As a Chuyên viên, I want chat với AI về hồ sơ và xem lịch sử tool AI đã dùng, so that tôi làm rõ các điểm chưa chắc chắn.

#### Acceptance Criteria

1. WHEN `AdvancedChatView` khởi tạo, THE Platform SHALL gọi `GET /api/v1/dossiers` để load danh sách sessions, mỗi session tương ứng một Dossier.
2. WHEN người dùng chọn một session, THE Platform SHALL gọi `GET /api/v1/dossiers/:id` và `GET /api/v1/audit-logs?limit=10` để load lịch sử công cụ AI.
3. THE Platform SHALL lọc audit-logs theo `dossier_id` phía FE: chỉ hiển thị logs có `inputs.dossier_id` khớp với Dossier đang active.
4. WHEN người dùng cuộn lên đầu danh sách tin nhắn, THE Platform SHALL tăng `limit` trong `GET /api/v1/audit-logs` để load thêm lịch sử.
5. WHEN người dùng gửi tin nhắn và bấm "Thẩm định", THE Platform SHALL gọi `POST /api/v1/dossiers/:id/appraise` và hiển thị phản hồi tức thì.
6. WHEN WS nhận `tool_result` cho session đang active, THE Platform SHALL append message mới vào chat history mà không reload toàn bộ list.
7. IF `GET /api/v1/audit-logs` trả lỗi HTTP, THEN THE Platform SHALL hiển thị thông báo lỗi trong panel chat và tiếp tục hoạt động.

### Requirement 5: Alerts Module — Wire API và Seed Alert AL-1043

**User Story:** As a Lãnh đạo HĐTV, I want xem và resolve cảnh báo rủi ro từ AI, so that tôi theo dõi và xử lý vấn đề kịp thời.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/alerts`, THE Platform SHALL gọi `GET /api/v1/alerts` và render danh sách alerts từ response.
2. THE Platform SHALL hiển thị cảnh báo với các trường `id`, `title`, `severity`, `source`, `status`, `description`, `created_at`.
3. WHEN người dùng bấm "Resolve" trên một cảnh báo, THE Platform SHALL gọi `PATCH /api/v1/alerts/:id/resolve`.
4. WHEN `PATCH /alerts/:id/resolve` thành công, THE Platform SHALL cập nhật trạng thái cảnh báo thành `resolved` trong UI mà không reload toàn bộ list.
5. IF `PATCH /alerts/:id/resolve` trả lỗi HTTP, THEN THE Platform SHALL hiển thị toast thông báo lỗi và giữ nguyên trạng thái cảnh báo.
6. THE Platform SHALL hiển thị cảnh báo AL-1043 (đề xuất hạ tiêu chuẩn kỹ thuật từ Apex Tech cho Dossier_198) sau khi seed data được chạy.
7. THE Platform SHALL hỗ trợ lọc alerts theo `severity` và `status` phía FE.

### Requirement 6: Knowledge Graph Module — Fix Mandatory dossier_id và Seed Dossier 198

**User Story:** As a Chuyên viên, I want xem đồ thị suy luận AI cho từng hồ sơ, so that tôi hiểu cơ sở ra quyết định của AI.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/graph`, THE Platform SHALL yêu cầu người dùng chọn Dossier trước khi gọi API.
2. WHEN người dùng đã chọn Dossier, THE Platform SHALL gọi `GET /api/v1/knowledge-graph?dossier_id={id}` và render đồ thị từ `KnowledgeGraphOut`.
3. IF `KnowledgeGraphView` được mở khi chưa có `dossier_id`, THEN THE Platform SHALL KHÔNG gọi `GET /knowledge-graph` để tránh lỗi HTTP 422 vì `dossier_id` là Query param bắt buộc (`ge=1`).
4. IF `GET /knowledge-graph` trả HTTP 404, THEN THE Platform SHALL hiển thị thông báo "Hồ sơ không tồn tại hoặc chưa có đồ thị tri thức".
5. THE Platform SHALL render Knowledge_Graph cho Dossier_198 với đủ 7 nodes và 6 edges đặc thù: `tt198`, `qd8594`, `nq180`, `qd153`, `pl_so_sanh`, `apex_feedback`, `risk_spec`.
6. THE `meta_service.build_knowledge_graph()` SHALL tạo nodes/edges đặc thù cho `dossier_id=5` thay vì chỉ dùng `LEGAL_FALLBACK` generic.
7. IF `GET /knowledge-graph` trả lỗi HTTP khác 404, THEN THE Platform SHALL hiển thị thông báo lỗi có mô tả.

### Requirement 7: Workflow Manager Module — BPMN Load và Save

**User Story:** As a Trưởng ban, I want xem và chỉnh sửa sơ đồ quy trình BPMN cho hồ sơ, so that tôi đảm bảo quy trình thẩm định đúng quy định.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/workflow`, THE Platform SHALL gọi `GET /api/v1/workflows` để load danh sách workflow đã lưu.
2. WHEN người dùng chọn một workflow, THE Platform SHALL gọi `GET /api/v1/workflows/{dossier_id}` và render BPMN XML vào editor bpmn-js.
3. WHEN người dùng lưu workflow, THE Platform SHALL gọi `PUT /api/v1/workflows/{dossier_id}` với `{bpmn_xml}`.
4. IF `GET /api/v1/workflows/{dossier_id}` trả HTTP 404, THEN THE Platform SHALL hiển thị BPMN template mặc định để người dùng tạo mới.
5. THE Platform SHALL lazy-load bpmn-js (~2MB) chỉ khi người dùng truy cập route `/workflow`, không load ở bundle chính.
6. IF `PUT /workflows/{dossier_id}` trả lỗi HTTP, THEN THE Platform SHALL hiển thị thông báo lỗi và giữ nguyên BPMN trên editor.

### Requirement 8: Skill Builder Module — Wire API và Thêm Skill UAV

**User Story:** As a Quản trị viên, I want xem và quản lý Skill template hướng dẫn AI, so that tôi cấu hình hành vi AI theo từng loại hồ sơ.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/skills`, THE Platform SHALL gọi `GET /api/v1/skills` và render danh sách `SkillTemplateOut` từ response.
2. THE Platform SHALL hiển thị skill với các trường `id`, `name`, `description`, `type`, `is_active`, `markdown_content`.
3. THE Platform SHALL hiển thị Skill id=3 "Thẩm định Tiêu chuẩn kỹ thuật Vật tư/Thiết bị" sau khi seed data được chạy.
4. IF `GET /api/v1/skills` trả lỗi HTTP, THEN THE Platform SHALL hiển thị thông báo lỗi và danh sách rỗng.
5. THE Platform SHALL render `markdown_content` của skill dưới dạng Markdown preview.

### Requirement 9: Tool Registry Module — Wire API và Xác Minh URL Prefix

**User Story:** As a Quản trị viên, I want xem toàn bộ công cụ AI đã đăng ký và số lần sử dụng, so that tôi giám sát sức khỏe của hệ thống tool.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/tools`, THE Platform SHALL gọi `GET /api/v1/tools` và render danh sách `ToolOut` từ response.
2. THE Platform SHALL hiển thị tool với các trường `name`, `description`, `category`, `status`, `usage_count`, `last_used_at`.
3. THE Platform SHALL xác minh `GET /api/v1/tools` khớp với route `GET /tools` trong `meta.router` (không prefix riêng) được include vào `api_router` không prefix — tổng path là `/api/v1/tools`, khớp với `api.js getTools()`.
4. IF `GET /api/v1/tools` trả lỗi HTTP, THEN THE Platform SHALL hiển thị thông báo lỗi và danh sách rỗng.
5. THE Platform SHALL hiển thị tool `legal_doc_lookup` và `supplier_feedback_lookup` sau khi được đăng ký vào `ToolConfig`.

### Requirement 10: Schedule Manager Module — Wire API Schedules

**User Story:** As a Quản trị viên, I want xem danh sách schedule job và trạng thái, so that tôi quản lý các tác vụ tự động của nền tảng.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/schedule`, THE Platform SHALL gọi `GET /api/v1/schedules` và render danh sách `ScheduleJobOut` từ response.
2. THE Platform SHALL hiển thị schedule với các trường `id`, `name`, `cron`, `schedule_text`, `tools`, `status`, `description`.
3. THE Platform SHALL hiển thị `schedule_text` bằng tiếng Việt (ví dụ: "Hàng giờ", "Hàng tuần (Thứ Hai, 08:00)").
4. IF `GET /api/v1/schedules` trả lỗi HTTP, THEN THE Platform SHALL hiển thị thông báo lỗi và danh sách rỗng.

### Requirement 11: Dossier Settings Module — Checklist và Loại Hồ Sơ UAV

**User Story:** As a Quản trị viên, I want xem và cấu hình checklist template thẩm định, so that tôi đảm bảo AI kiểm tra đúng tiêu chí cho từng loại tờ trình.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/settings`, THE Platform SHALL gọi `GET /api/v1/checklist-template` và render danh sách `ChecklistItemOut`.
2. THE Platform SHALL hiển thị checklist item với các trường `id`, `text`, `type` (auto/manual), `is_required`.
3. THE Platform SHALL hiển thị loại hồ sơ id=6 "Tờ trình Phê duyệt Tiêu chuẩn kỹ thuật Vật tư/Thiết bị" trong danh sách `dossierTypes`.
4. THE Platform SHALL hiển thị 5 checklist items cho loại hồ sơ id=6: Đối chiếu căn cứ pháp lý (auto, required), Kiểm tra thẩm quyền phê duyệt (auto, required), Đối chiếu Tiêu chuẩn kỹ thuật với ý kiến NCC (auto, required), Kiểm tra số NCC phản hồi >= 2/4 (auto, optional), Kiểm tra cấu trúc hồ sơ đầy đủ (auto, required).
5. IF `GET /api/v1/checklist-template` trả lỗi HTTP, THEN THE Platform SHALL hiển thị checklist fallback mặc định và thông báo lỗi.

### Requirement 12: System Admin Module — Multi-Tab Admin Panel

**User Story:** As a Quản trị viên, I want quản lý người dùng, xem system logs, giám sát metrics AI và quản lý API keys, so that tôi vận hành toàn bộ nền tảng.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/admin`, THE Platform SHALL gọi song song `GET /api/v1/users`, `GET /api/v1/roles`, `GET /api/v1/system-logs`, `GET /api/v1/agent/metrics`.
2. THE Platform SHALL hiển thị tab "Người dùng" với danh sách `UserOut{id, name, email, role, is_active}`.
3. THE Platform SHALL hiển thị tab "Vai trò" với danh sách `RoleOut{id, name, desc, users_count}`.
4. THE Platform SHALL hiển thị tab "System Logs" với danh sách `SystemLogOut{id, time, user, action, details, type}`.
5. THE Platform SHALL hiển thị tab "Agent Intelligence" với 4 KPI: `plan_revision_rate`, `critic_rejection_rate`, `feedback_total`, `memory_retrieval_count`.
6. WHEN người dùng mở tab "API Keys", THE Platform SHALL gọi `GET /api/v1/api-keys` và hiển thị danh sách keys với `name`, `key_type`, `key_prefix`, `is_active`.
7. WHEN người dùng tạo API key mới, THE Platform SHALL gọi `POST /api/v1/api-keys`.
8. WHEN người dùng xóa API key, THE Platform SHALL gọi `DELETE /api/v1/api-keys/:id` và xóa key khỏi danh sách.
9. WHEN người dùng mở tab "MCP Audit Logs", THE Platform SHALL gọi `GET /api/v1/mcp/audit-logs` và hiển thị `tool_name`, `api_key_prefix`, `execution_ms`, `is_error`, `created_at`.
10. IF `POST /api/v1/mcp/tools/list` hoặc `POST /api/v1/mcp/tools/call` trả HTTP 401, THEN THE Platform SHALL hiển thị thông báo "API key MCP chưa được cấu hình" thay vì crash.
11. THE Platform SHALL hiển thị ít nhất 2 records trong MCP Audit Logs sau khi seed data cho Dossier_198 được chạy.
12. IF `GET /api/v1/agent/metrics` trả lỗi HTTP, THEN THE Platform SHALL hiển thị "0" cho mọi KPI và thông báo lỗi.
13. THE Platform SHALL gọi `GET /api/v1/agent/models` và hiển thị bảng AI Models với cặp role-model từ response.

### Requirement 13: Notifications Module — Phân Trang và Đánh Dấu Đã Đọc

**User Story:** As a Chuyên viên, I want xem thông báo cá nhân, phân trang và đánh dấu đã đọc, so that tôi không bỏ lỡ tác vụ cần xử lý.

#### Acceptance Criteria

1. WHEN người dùng truy cập `/notifications`, THE Platform SHALL gọi `GET /api/v1/notifications/user/{userId}?offset=0&limit=20` với `userId` từ `authStore.currentUser.id`.
2. THE Platform SHALL hiển thị notifications với các trường `id`, `title`, `message`, `type`, `is_read`, `created_at`.
3. WHEN người dùng bấm vào một thông báo, THE Platform SHALL gọi `PATCH /api/v1/notifications/{id}` với `{is_read: true}` và cập nhật `unreadCount`.
4. WHEN người dùng bấm "Đánh dấu tất cả đã đọc", THE Platform SHALL gọi `PATCH /api/v1/notifications/user/{userId}/mark-all-read` và reset `unreadCount` về 0.
5. WHEN người dùng cuộn xuống cuối danh sách và `hasMore = true`, THE Platform SHALL gọi `GET /notifications/user/{userId}?offset=N&limit=20` và append thêm thông báo.
6. IF `authStore.currentUser` là null, THEN THE Platform SHALL KHÔNG gọi notification API và hiển thị thông báo "Vui lòng đăng nhập để xem thông báo".
7. IF `GET /notifications/user/{userId}` trả lỗi HTTP, THEN THE Platform SHALL hiển thị thông báo lỗi và danh sách rỗng.

### Requirement 14: Data Integrity — Field Name Consistency FE và BE

**User Story:** As a Developer, I want đảm bảo FE luôn đọc đúng field name từ BE, so that không có bug âm thầm do sai tên trường.

#### Acceptance Criteria

1. THE mapDossier function SHALL đọc `d.risk_level` (không phải `d.risk`) khi ánh xạ sang trường `risk` phía FE, khớp với `DossierOut` schema BE.
2. THE `DossierOut` schema SHALL luôn trả trường `risk_level` (không phải `risk`) trong mọi endpoint trả `DossierOut`.
3. THE `DashboardSummaryOut` schema SHALL dùng `risk_level` trong `notable_dossiers` và `newest_dossiers`, không dùng `risk`.
4. THE `GET /api/v1/agent/models` endpoint SHALL được đăng ký tại `/agent/models` trong `meta.py` không có prefix riêng, được include vào `api_router` không prefix, tổng path là `/api/v1/agent/models`, khớp với `api.js getAgentModels()`.
5. THE Platform SHALL dùng pagination shape nhất quán: tất cả paginated endpoints SHALL trả `{items, total, offset, limit, has_more}`.

### Requirement 15: Error Handling — API Error Boundaries

**User Story:** As a User, I want mọi lỗi API được xử lý gracefully, so that trải nghiệm không bị gián đoạn khi có sự cố.

#### Acceptance Criteria

1. THE Platform SHALL bao gồm `try/catch` hoặc `.catch()` cho mọi API call trong tất cả 13 module store.
2. WHEN một API call thất bại, THE Platform SHALL hiển thị thông báo lỗi rõ ràng trong UI (toast hoặc inline error), không để lỗi âm thầm.
3. IF BE trả HTTP 4xx, THEN THE Platform SHALL hiển thị trường `detail` từ response body thay vì error code generic.
4. IF BE trả HTTP 5xx, THEN THE Platform SHALL hiển thị "Lỗi máy chủ nội bộ. Vui lòng thử lại sau." và log lỗi ra console.
5. THE Platform SHALL KHÔNG để bất kỳ view nào crash hoàn toàn (màn hình trắng) khi API call thất bại.
6. THE `api.js` SHALL thiết lập Axios interceptor để tập trung xử lý lỗi HTTP 401 và HTTP 503.

### Requirement 16: Auth Guard — Route Access Control Nhất Quán

**User Story:** As a Admin, I want route `/admin` và `/notifications` được bảo vệ đúng cách, so that người dùng không có quyền không truy cập được.

#### Acceptance Criteria

1. THE `authStore` SHALL có `isAuthenticated` là `true` khi `currentUser` không null — mock authentication cho demo, không cần login flow thật.
2. THE `authStore` SHALL mặc định set `currentUser` là user `hdtv_leader` khi khởi động ứng dụng.
3. WHEN `currentUser.role` là `hdtv_leader`, `dept_head`, hoặc `specialist`, THE Platform SHALL redirect từ `/admin` về `/dashboard` và hiển thị thông báo "Không đủ quyền truy cập trang Quản trị".
4. WHEN `currentUser.role` là `admin`, THE Platform SHALL cho phép truy cập `/admin` mà không redirect.
5. THE Platform SHALL cung cấp cơ chế `loginAs(role)` visible trong UI để demo có thể switch giữa các vai trò.
6. THE Platform SHALL KHÔNG block `/notifications` route vì `isAuthenticated` luôn `true` khi `currentUser` là non-null (mock user mặc định `hdtv_leader` đã được set).

### Requirement 17: WebSocket Reliability — Events Đúng Thứ Tự và Không Race Condition

**User Story:** As a Chuyên viên, I want WS events bắn đúng thứ tự và không bị mất event, so that tiến trình thẩm định AI hiển thị real-time chính xác.

#### Acceptance Criteria

1. THE BE SHALL emit `task_started` WS event ngay sau khi `run_appraisal_task.delay(dossier_id)` được gọi thành công, không chờ Celery worker start, để FE không bỏ lỡ event đầu tiên.
2. THE BE SHALL emit WS events theo thứ tự: `task_started` → `plan_created` → (`tool_executing` → `tool_result`) lặp N lần → `critic_review` → (`revision_requested` hoặc `task_completed`).
3. THE Platform SHALL truyền `dossier_id` và `task_id` trong payload của mỗi WS event để FE correlate event với đúng Dossier.
4. WHEN Celery task gặp exception không mong đợi, THE BE SHALL emit WS event `task_failed` với `error_message`.
5. THE FE SHALL buffer WS events nhận được trước khi `plan_created` event đến, để tránh mất event khi kết nối WS chậm hơn Celery task start.
6. THE WS connection SHALL sử dụng heartbeat ping/pong mỗi 30 giây để phát hiện kết nối đứt im lặng.

### Requirement 18: Demo Data — Dossier 198 UAV Đầy Đủ

**User Story:** As a Demo Presenter, I want Dossier 198 UAV có đầy đủ dữ liệu thật trong hệ thống, so that tôi demo toàn bộ luồng thẩm định AI với dữ liệu hồ sơ thật của EVNHANOI.

#### Acceptance Criteria

1. THE Platform SHALL có Dossier_198 trong database với `doc_no="198/TTr-EVNHANOI"`, `title="Phê duyệt Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV)..."`, `unit="Ban Kỹ thuật (KT)"`, `risk_level=medium`, `status=pending`.
2. THE Platform SHALL có Knowledge_Graph nodes/edges đặc thù cho `dossier_id=5` bao gồm 7 nodes (`tt198`, `qd8594`, `nq180`, `qd153`, `pl_so_sanh`, `apex_feedback`, `risk_spec`) và 6 edges.
3. THE Platform SHALL có Alert AL-1043 trong database với `title="Đề xuất hạ tiêu chuẩn kỹ thuật từ nhà cung cấp tư vấn"`, `severity=medium`, `source="AI Spec Cross-Check"`, `status=open`, liên kết `dossier_id=5`.
4. THE Platform SHALL có ít nhất 2 records trong `mcp_call_logs` cho Dossier_198: một lần gọi `legal_doc_lookup` và một lần gọi `supplier_feedback_lookup`.
5. THE Platform SHALL có `agent_plans` cho Dossier_198 với 5 plan steps tương ứng 5 checks trong kịch bản demo.
6. THE Platform SHALL có ít nhất 2 `document_versions` cho Dossier_198: Report v1.0 (dự thảo ban đầu) và Report v1.1 (đã chèn phần Rủi ro AI).
7. THE Platform SHALL có Skill id=3 "Thẩm định Tiêu chuẩn kỹ thuật Vật tư/Thiết bị" trong `meta_service.list_skill_templates()`.
8. THE seed script `scripts/seed_dossier_198.py` SHALL upload đủ 8 files vào MinIO theo path `198-ttr-evnhanoi/`.
9. WHEN script seed chạy, THE Platform SHALL ingest nội dung 3 file căn cứ pháp lý (QD 8594, NQ 180, QD 153) vào ChromaDB collection `legal_docs`.
10. THE Platform SHALL seed 1 feedback lesson vào ChromaDB collection `feedback_lessons`: nội dung hướng dẫn đối chiếu đề xuất hạ tiêu chuẩn NCC với yêu cầu gốc trước khi trình HĐTV.

### Requirement 19: Database Migrations — Chạy Clean Không Lỗi

**User Story:** As a DevOps, I want toàn bộ migrations chạy clean không lỗi, so that deploy lên VM không bị gián đoạn.

#### Acceptance Criteria

1. THE Migration T-66 (raw SQL DDL cho `api_keys` table) SHALL chạy thành công mà không có `DuplicateObjectError` trên PostgreSQL clean.
2. THE Migrations 001 đến 012 SHALL chạy theo thứ tự sequential mà không xung đột với nhau.
3. WHEN `cli.sh hdtv-migrate` được gọi trên môi trường đã có database, THE Platform SHALL phát hiện và skip các migration đã chạy (idempotent).
4. IF bất kỳ migration nào thất bại, THE Platform SHALL rollback và log rõ migration ID và lỗi cụ thể.

### Requirement 20: Meilisearch Full-Text Search — Graceful Degrade và Index Dossier 198

**User Story:** As a Chuyên viên, I want tìm kiếm hồ sơ bằng Ctrl+K với full-text search, so that tôi tìm nhanh tờ trình mà không cần lọc thủ công.

#### Acceptance Criteria

1. WHEN người dùng nhấn Ctrl+K, THE Platform SHALL mở search overlay và gọi `GET /api/v1/search?q={query}` với debounce 300ms.
2. THE Platform SHALL hiển thị kết quả tìm kiếm với highlighting từ khóa từ Meilisearch response.
3. IF Meilisearch không available (HTTP 503), THEN THE Platform SHALL hiển thị "Tìm kiếm nhanh tạm thời không khả dụng" và vẫn cho phép điều hướng bình thường.
4. THE Platform SHALL index Dossier_198 vào Meilisearch ngay khi seed script chạy, để Ctrl+K tìm được "198" hoặc "UAV".
