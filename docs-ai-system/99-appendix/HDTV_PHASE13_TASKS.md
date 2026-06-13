# Phase 13 — Module-by-Module Audit: FE → BE → AI

> **Mục tiêu:** Rà soát và hoàn thiện toàn bộ hệ thống bằng cách quét từng module từ FE (Vue 3 + Pinia) → truy ngược BE (FastAPI) → kiểm tra AI pipeline (Celery orchestrator).
>
> **Phương pháp:** Mỗi task = đọc file FE view + store → trace API call → kiểm tra BE router + service → fix bug + viết logic hoàn chỉnh.
>
> **Nguồn gốc:** Phân tích từ source code thực tế của `hdtv-ai-prototype` và `hdtv-ai-platform` (session June 2026).

---

## Status Legend: PENDING | IN_PROGRESS | DONE | BLOCKED

---

## Phase 13A — Frontend Module Audit

---

### T-55: Dashboard Module — Fix Field Inconsistency và Wire AI Models

- **deps:** —
- **priority:** P1
- **FE file:** `hdtv-ai-prototype/src/views/DashboardView.vue`
- **FE store:** `hdtv-ai-prototype/src/stores/dashboard.js`

**Bugs phát hiện từ code scan:**

1. `DashboardView.vue` render `d.risk` (string "Cao"/"Trung bình") từ `notable_dossiers` nhưng cũng so sánh `d.risk_level === 'high'` — hai hướng logic song song, dễ sai khi BE thay đổi format.
2. `openDossier(d)` dùng `d.dossier_id` fallback sang `d.id` — `notable_dossiers` trả `id = doc_no` (string), không phải integer ID → `router.push('/workspace/198/TTr-EVNHANOI')` sẽ fail.
3. `dashboard.js fetchSummary()` không có `try/catch` → khi API lỗi, `summary.value` = null → tất cả `computed` trả `—` nhưng không có error toast.
4. Không có AI Models panel — `api.js getAgentModels()` có nhưng Dashboard không gọi.

**Việc cần làm:**

- `dashboard.js`: Wrap `fetchSummary()` trong `try/catch`, set `error.value` khi thất bại.
- `meta_service.py` → `dashboard_summary()`: Đổi `notable_dossiers[].id = doc_no` thành trả đồng thời `doc_no` và `dossier_id = d.id` (integer). FE đã có `dossier_id` field riêng nhưng BE đang gán `"id": d.doc_no`.
- `DashboardView.vue`: `openDossier()` luôn dùng `d.dossier_id` (integer), không fallback sang `d.id`.
- `DashboardView.vue`: Thêm widget "AI Models" gọi `getAgentModels()` và render bảng role → model.
- `DashboardView.vue`: Thêm `v-if="store.error"` error banner.

**Acceptance:**
- `GET /dashboard/summary` → `notable_dossiers[0].dossier_id` là integer → `router.push('/workspace/1')` hoạt động.
- Click dossier bất kỳ từ Dashboard → mở đúng workspace.
- API fail → hiện error banner, không crash.

**verify_cmd:** `curl http://localhost:8000/api/v1/dashboard/summary | python -m json.tool`

**status:** DONE ✅

---

### T-56: Dossier List — Fix Route Ordering Bug và Field Mapping

- **deps:** —
- **priority:** P0 — bug P0 blocking
- **FE file:** `hdtv-ai-prototype/src/views/DossierListView.vue`
- **FE store:** `hdtv-ai-prototype/src/stores/dossier.js`
- **BE file:** `hdtv-ai-platform/app/routers/dossiers.py`

**Bugs phát hiện từ code scan:**

1. **BUG P0 — FastAPI Route Ordering:** `GET /dossiers/units` đăng ký SAU `GET /dossiers/{dossier_id}` trong `dossiers.py`. FastAPI sẽ match "units" như `dossier_id` integer → HTTP 422 "value is not a valid integer". Cần đặt `/units` TRƯỚC `/{dossier_id}`.
2. `_mapDossier()` trong `dossier.js` đọc `d.risk_level` — đúng với `DossierOut` schema. Nhưng `DossierPage.items` cần verify BE trả `risk_level` không phải `risk`.
3. `alerts.js fetchAlerts()` map `a.title = a.description.slice(0, 80)` — không có trường `title` riêng trong `AlertOut` schema → hiển thị mô tả cắt ngắn thay vì title thật.
4. `DossierListView.vue` không có error state khi `fetchDossiers()` fail.

**Việc cần làm:**

- `dossiers.py`: Di chuyển `@router.get("/units", ...)` lên TRƯỚC `@router.get("/{dossier_id}", ...)`. Đây là single-line fix nhưng critical.
- `dossier_service.py`: Verify `list_dossiers()` trả field `risk_level` (không rename thành `risk`).
- `Alert` entity: Thêm field `title` (String 200) vào model, migration `018_add_alert_title.py`. Seed alerts có `title` thật. `AlertOut` schema thêm `title`.
- `alerts.js`: Đọc `a.title` thay vì `a.description.slice(0, 80)`.
- `DossierListView.vue`: Thêm `v-if="store.error"` empty/error state.

**Acceptance:**
- `GET /api/v1/dossiers/units` trả `["Ban Kỹ thuật (KT)", ...]` không trả 422.
- Filter dropdown populate đúng.
- Alert cards hiển thị `title` ngắn gọn, không phải cắt description.

**verify_cmd:**
```bash
curl -sf http://localhost:8000/api/v1/dossiers/units
# Phải trả: ["Ban Kỹ thuật (KT)", ...], không phải 422
```

**status:** DONE ✅

---

### T-57: SplitViewWorkspace — Xóa Hardcode, Wire API Đầy Đủ, Fix WS Race Condition

- **deps:** T-56
- **priority:** P1
- **FE file:** `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue`
- **BE files:** `app/routers/dossiers.py`, `app/routers/ws.py`, `app/workers/tasks.py`

**Bugs phát hiện từ code scan:**

1. `ws.py`: Không emit `task_started` event khi Celery task được queue — FE kết nối WS sau khi gọi POST appraise, nhưng event đầu tiên `plan_created` có thể bắn trước khi WS kết nối xong → **race condition**. `ws.py` đã có `snapshot` event nhưng snapshot chỉ gửi status/risk hiện tại, không có plan steps.
2. `tasks.py`: Không emit `task_started` — Celery bắt đầu chạy rồi mới emit events, FE có thể miss 1-2 events đầu.
3. `SplitViewWorkspace` còn `aiChecks` hardcode array (cần verify từ `DossierDetail.appraisal`).
4. WS reconnect logic: FE không có retry mechanism khi WS bị ngắt.
5. Tab "Tài liệu Khác": `referenceDocs` cần lấy từ `GET /dossiers/:id/reference-documents` (đã implement ở T-52) nhưng cần verify wiring.
6. Tab "Phiên bản": `reportVersions` cần từ `GET /dossiers/:id/document-versions`.

**Việc cần làm:**

- `tasks.py` → `run_appraisal_task()`: Sau `run_appraisal_task.delay()` trong router (không phải trong task!), router `dossiers.py` nên emit `task_started` qua `publish_event()` trước khi return 202.
- `app/routers/dossiers.py` → `appraise_dossier()`: Thêm `await publish_event(dossier_id, {"type": "task_started", "task_id": task.id, "dossier_id": dossier_id})` sau `run_appraisal_task.delay(...)`.
- `SplitViewWorkspace.vue`: Thêm WS reconnect với exponential backoff (2s, 5s, 10s, max 3 lần).
- `SplitViewWorkspace.vue`: Khi mount, gọi `GET /dossiers/:id/reference-documents` và bind vào `referenceDocs`.
- `SplitViewWorkspace.vue`: Khi mount, gọi `GET /dossiers/:id/document-versions` và bind vào `reportVersions`.
- `SplitViewWorkspace.vue`: `aiChecks` phải load từ `DossierDetail.appraisal?.plan_steps` hoặc từ WS `plan_created` event — không hardcode.

**Acceptance:**
- POST appraise → WS nhận `task_started` trong vòng 500ms.
- WS disconnect → FE retry → reconnect thành công.
- Tab "Tài liệu Khác" hiển thị files từ API, không hardcode.
- Tab "Phiên bản" hiển thị versions từ API.

**status:** DONE ✅

---

### T-58: Alerts Module — Fix Fallback Hardcode và Alert Title

- **deps:** T-56
- **priority:** P1
- **FE file:** `hdtv-ai-prototype/src/views/AlertsView.vue`
- **FE store:** `hdtv-ai-prototype/src/stores/alerts.js`
- **BE file:** `app/routers/alerts.py`, `app/models/entities.py`

**Bugs phát hiện từ code scan:**

1. `AlertsView.vue` dùng `computed alerts = alertsStore.alerts.length ? alertsStore.alerts : [hardcode_array]` — khi API thành công nhưng DB empty (fresh deploy), vẫn hiện hardcode data. Đây là bug tinh vi.
2. `alerts.js resolve(id)`: Gọi `alertsStore.resolve(alert.rawId)` nhưng fallback alerts không có `rawId` → `undefined` → BE 404.
3. `AlertsView`: Comment và Assignment hoàn toàn local state (không persist) — acceptable nhưng cần document rõ.
4. Seed data chưa có alert AL-1043 cho Dossier #198.

**Việc cần làm:**

- `AlertsView.vue`: Bỏ hardcode fallback. Thay bằng proper empty state `v-if="alertsStore.alerts.length === 0 && !alertsStore.loading"`.
- `Alert` entity: Thêm field `title` (String 200, nullable) — dùng `description[:80]` khi không có title.
- `alerts.js`: Thêm `try/catch` trong `fetchAlerts()` và `resolve()`.
- `scripts/seed.py`: Seed alert AL-1043 với `title`, `severity=medium`, `source="AI Spec Cross-Check"`, `dossier_id=5` (Dossier #198 UAV).

**Acceptance:**
- Empty DB → hiện "Hệ thống an toàn" empty state (không hiện hardcode alerts).
- DB có alerts → hiển thị từ API.
- Resolve button hoạt động → gọi PATCH → cập nhật UI ngay.

**status:** DONE ✅

---

### T-59: Knowledge Graph — Fix Mandatory Param Bug

- **deps:** —
- **priority:** P1
- **FE file:** `hdtv-ai-prototype/src/views/KnowledgeGraphView.vue`
- **FE store:** `hdtv-ai-prototype/src/stores/graph.js`
- **BE file:** `app/routers/meta.py`, `app/services/meta_service.py`

**Bugs phát hiện từ code scan:**

1. `meta.py` khai báo `dossier_id: int = Query(..., ge=1)` — mandatory. Nhưng nếu `dossierStore.dossiers` empty khi mount (race condition với `fetchDossiers()`), code gọi `loadGraph(undefined)` → `GET /knowledge-graph?dossier_id=undefined` → **HTTP 422**.
2. `KnowledgeGraphView` gọi `dossierStore.fetchDossiers()` rồi lấy `dossiers[0].id` ngay — nếu fetch chưa xong, `dossiers[0]` = undefined → `loadGraph(undefined)`.
3. `build_knowledge_graph()` trong `meta_service.py` dùng generic `LEGAL_FALLBACK` cho MỌI dossier — không có node/edge đặc thù cho Dossier #198 UAV.
4. SVG edges dùng `nodes.find(n => n.id === edge.source).x` mà không guard null → crash nếu node không tìm thấy.

**Việc cần làm:**

- `KnowledgeGraphView.vue`: Wrap `loadGraph()` call trong `if (dossierStore.dossiers.length > 0)` sau khi `await fetchDossiers()` complete.
- `graph.js`: Thêm `try/catch` trong `fetchGraph()`.
- `meta_service.py` → `build_knowledge_graph()`: Thêm `if dossier_id == 5:` branch trả nodes/edges đặc thù cho Dossier #198 (7 nodes, 6 edges từ KE_HOACH_DEMO_HDTV_AI.md Mục 6.7).
- `KnowledgeGraphView.vue`: Guard SVG edges: `v-if="nodes.find(n => n.id === edge.source) && nodes.find(n => n.id === edge.target)"`.

**Acceptance:**
- Mount `/graph` khi dossier chưa load → không có HTTP 422.
- Chọn Dossier #198 → graph hiển thị 7 nodes đặc thù (tt198, qd8594, nq180, qd153, pl_so_sanh, apex_feedback, risk_spec).
- Không có JS crash khi edge source/target không tìm thấy.

**status:** DONE ✅

---

### T-60: SystemAdmin — Fix MCP Tab và loadMcpLogs Reference

- **deps:** —
- **priority:** P1
- **FE file:** `hdtv-ai-prototype/src/views/SystemAdminView.vue`
- **FE store:** `hdtv-ai-prototype/src/stores/admin.js`

**Bugs phát hiện từ code scan:**

1. `SystemAdminView.vue` template gọi `@click="loadMcpLogs"` nhưng `loadMcpLogs` không được import trong `<script setup>` từ store — chỉ có `storeToRefs` destructure các ref values, không có actions. Cần `const { loadMcpLogs } = adminStore` hoặc dùng `adminStore.loadMcpLogs`.
2. `admin.js fetchAll()` gọi tất cả 7 APIs parallel — nếu `getAgentModels()` fail (endpoint chưa có), sẽ throw và block toàn bộ `fetchAll`. Cần `Promise.allSettled`.
3. Tab "MCP Audit Logs": Khi `mcpLogs` empty (fresh deploy), hiện `"Chưa có MCP call nào"` — cần seed ít nhất 2 records cho demo.
4. `fetchAll()` không handle `getAgentModels` vì nó không được include trong `fetchAll()` list.
5. Roles tab: `r.usersCount` nhưng `admin.js` map `usersCount: r.users_count` — cần verify consistent.

**Việc cần làm:**

- `SystemAdminView.vue`: Thay `@click="loadMcpLogs"` bằng `@click="adminStore.loadMcpLogs()"`.
- `admin.js fetchAll()`: Dùng `Promise.allSettled(...)` thay vì `Promise.all(...)` để không block khi 1 API fail.
- `admin.js fetchAll()`: Thêm `getAgentModels()` vào list (nếu cần hiển thị models panel trong admin).
- `scripts/seed.py`: Seed 2 `McpCallLog` records cho demo: `legal_doc_lookup` và `supplier_feedback_lookup` từ "AI Agent (Tờ trình 198)".
- `admin.js`: Verify `r.users_count → usersCount` mapping đúng với `RoleOut` schema BE.

**Acceptance:**
- Nút "Làm mới" trong MCP Audit tab hoạt động không crash.
- `fetchAll()` fail 1 endpoint → các tab khác vẫn load.
- MCP Audit tab hiển thị ≥2 records sau seed.

**status:** DONE ✅

---

### T-61: Notifications Module — Fix Error Handling và Guard

- **deps:** —
- **priority:** P2
- **FE file:** `hdtv-ai-prototype/src/views/NotificationsView.vue`
- **FE store:** `hdtv-ai-prototype/src/stores/notifications.js`
- **BE file:** `app/routers/notifications.py`

**Bugs phát hiện từ code scan:**

1. `notifications.js markAsRead()` và `markAllAsRead()` dùng `console.error` nhưng không set `error` state → UI không biết thất bại.
2. `notifications.js loadNotifications()`: `unreadCount = response.data.unread_count` — nhưng `NotificationPage` schema BE chưa verify có field `unread_count`. Cần check `notification_service.py`.
3. `notifications.py GET /user/{user_id}`: Returns `NotificationPage` với `unread_count` — cần verify field có trong `get_user_notifications()` service.
4. Route guard: `/notifications` require `requiresAuth: true` — `auth.js` default user = `hdtv_leader` → `isAuthenticated = true` → OK. Nhưng cần document rõ mock auth behavior.

**Việc cần làm:**

- `notification_service.py` → `get_user_notifications()`: Verify trả `unread_count` (count rows where `is_read=False`).
- `notifications.js`: Thêm `error` ref, set khi API call fail, xóa khi thành công.
- `NotificationsView.vue`: Hiển thị error state khi `notificationsStore.error` truthy.
- `scripts/seed.py`: Seed ít nhất 3 notifications cho user_id=1 (demo leader user): 1 unread appraisal_result, 1 unread status_change, 1 read system_alert.

**Acceptance:**
- `/notifications` load → hiển thị list từ API.
- Mark as read → `unreadCount` giảm.
- `NotificationBell` hiển thị đúng số lượng unread.

**status:** DONE ✅

---

### T-62: Auth Store — Thêm Role Switcher UI cho Demo

- **deps:** —
- **priority:** P2
- **FE file:** `hdtv-ai-prototype/src/stores/auth.js`, `App.vue`

**Bugs phát hiện từ code scan:**

1. `auth.js loginAs(role)` tồn tại nhưng không có UI để gọi → Demo presenter không thể switch role để show `/admin` page.
2. Route guard `/admin` require `requiresRole: ['admin']` — default user `hdtv_leader` → bị redirect về dashboard. Demo không vào được admin page.
3. Không có feedback khi bị redirect do thiếu quyền.

**Việc cần làm:**

- `App.vue`: Thêm Role Switcher dropdown ở sidebar footer — dạng `<select>` hiện `currentUser.name (role)`, options = 4 mock users.
- Khi chọn role → gọi `authStore.loginAs(role)`.
- `router/index.js`: Khi redirect do `requiresRole` fail → hiện toast "Không đủ quyền, vui lòng chuyển sang vai trò Admin".

**Acceptance:**
- Sidebar có role switcher.
- Chuyển sang "admin" → có thể vào `/admin`.
- Chuyển lại "hdtv_leader" → bị redirect khỏi `/admin`.

**status:** DONE ✅

---

## Phase 13B — Backend Module Audit

---

### T-63: Dossier Service — Field Consistency và Missing Endpoints

- **deps:** T-56
- **priority:** P1
- **BE files:** `app/services/dossier_service.py`, `app/schemas/dossier.py`, `app/models/entities.py`

**Bugs phát hiện từ code scan:**

1. `DossierOut` schema cần verify field name: `risk_level` (không phải `risk`) để khớp với `_mapDossier()` FE.
2. `GET /dossiers` không support filter theo `unit` hay `risk_level` — FE filter phía client. Acceptable nhưng khi data nhiều → pagination sẽ lọc sai (page 1 có 20 items nhưng chỉ 3 match filter).
3. `dossier_service.py list_dossiers()` không có filter params → FE phải load toàn bộ rồi filter.
4. `DossierDetail` schema cần include `appraisal` object với `plan_steps` để Workspace có thể load aiChecks.

**Việc cần làm:**

- `dossier_service.py`: Thêm optional `unit: str | None` và `risk_level: str | None` filter params vào `list_dossiers()`.
- `dossiers.py router`: Thêm query params `unit` và `risk_level` vào `GET /dossiers`.
- `api.js getDossiers()`: Truyền filter params khi FE lọc (thay vì lọc hoàn toàn client-side).
- `DossierDetail`: Thêm `latest_appraisal: AppraisalSummary | None` field với `plan_steps`.
- `dossier_service.py get_dossier_detail()`: Join với `agent_plans` để trả latest plan.

**Acceptance:**
- `GET /dossiers?unit=Ban+Kỹ+thuật` → chỉ trả dossiers của Ban Kỹ thuật.
- `GET /dossiers/{id}` → response có `latest_appraisal.plan_steps` array.

**status:** DONE ✅

---

### T-64: Meta Service — Seed Data Dossier 198 và Knowledge Graph

- **deps:** T-59
- **priority:** P1
- **BE file:** `app/services/meta_service.py`, `scripts/seed.py`

**Bugs phát hiện từ code scan:**

1. `list_skill_templates()` chỉ có 2 skills — thiếu skill id=3 "Thẩm định Tiêu chuẩn kỹ thuật Vật tư/Thiết bị (đối chiếu góp ý NCC)" cho Dossier #198.
2. `SCHEDULE_TEMPLATES` không có schedule "Quét định kỳ ý kiến góp ý nhà cung cấp" — cần thêm cho demo UAV.
3. `build_knowledge_graph()` chỉ dùng generic LEGAL_FALLBACK nodes cho tất cả dossiers.
4. `DEFAULT_CHECKLIST` không có checklist riêng cho dossier_type_id=6 (UAV).
5. `dashboard_summary()` fallback `alert_sources` khi empty — hardcode data không phản ánh thực tế.

**Việc cần làm:**

- `meta_service.py list_skill_templates()`: Thêm Skill id=3 với markdown_content đầy đủ risk rules UAV.
- `meta_service.py SCHEDULE_TEMPLATES`: Thêm schedule id=4 "Quét định kỳ ý kiến góp ý NCC" (cron: `0 9 * * 1`, status: `active`).
- `meta_service.py build_knowledge_graph()`: Thêm `if dossier_id == 5:` branch trả 7 nodes + 6 edges UAV-specific.
- `meta_service.py default_checklist()`: Thêm checklist items cho dossier_type 6 (5 items UAV).
- `scripts/seed.py`: Seed dossier_id=5 (198/TTr-EVNHANOI) với đầy đủ data từ KE_HOACH_DEMO_HDTV_AI.md Mục 3.

**Acceptance:**
- `GET /api/v1/skills` trả 3 skills.
- `GET /api/v1/schedules` trả 4 schedules.
- `GET /api/v1/knowledge-graph?dossier_id=5` trả 7 nodes UAV.
- Seed script chạy → DB có dossier `198/TTr-EVNHANOI`.

**status:** PENDING

---

### T-65: WS Router — Fix Race Condition và Heartbeat

- **deps:** T-57
- **priority:** P1
- **BE file:** `app/routers/ws.py`, `app/routers/dossiers.py`, `app/services/pubsub.py`

**Bugs phát hiện từ code scan:**

1. `ws.py` có `snapshot` event nhưng chỉ trả `status` và `risk_level` hiện tại — không có `plan_steps` → FE phải gọi thêm REST API để lấy plan.
2. Không có heartbeat ping/pong → silent disconnect sau 60-90s idle.
3. `dossiers.py appraise_dossier()`: Gọi `run_appraisal_task.delay(dossier_id)` nhưng không emit `task_started` → FE có thể miss event đầu tiên nếu Celery bắt đầu nhanh hơn WS kết nối.
4. WS `while True` loop dùng `asyncio.sleep(0.05)` polling Redis — inefficient, cần event-driven.

**Việc cần làm:**

- `dossiers.py appraise_dossier()`: Sau `task = run_appraisal_task.delay(...)`, thêm `await publish_event(dossier_id, {"type": "task_started", "task_id": task.id})`.
- `ws.py`: Thêm heartbeat: mỗi 30s emit `{"type": "ping"}`, expect FE trả `{"type": "pong"}`. Nếu timeout 60s → close connection.
- `ws.py _get_dossier_snapshot()`: Thêm `latest_plan_steps` từ `agent_plans` table vào snapshot response.
- `ws.py`: Nâng timeout polling từ `1.0` lên `0.1` để giảm latency event delivery.

**Acceptance:**
- POST appraise → WS client nhận `task_started` trong <1s.
- WS idle 35s → nhận ping event.
- Snapshot khi reconnect có `plan_steps` array.

**status:** PENDING

---

### T-66: Migrations — Fix T-66 Raw SQL và Verify Clean Run

- **deps:** —
- **priority:** P1
- **BE file:** `alembic/versions/`, `app/models/entities.py`

**Bugs phát hiện từ code scan:**

1. Migration T-66 (api_keys table) dùng raw SQL DDL để bypass SQLAlchemy `_on_table_create` event — cần verify không có `DuplicateObjectError` khi chạy trên fresh DB.
2. Migration `018_add_alert_title.py` cần tạo để add `title` column vào `alerts` table (từ T-56).
3. Không có migration cho `notification.unread_count` computed field — nhưng đây là computed trong service không phải DB column → OK.
4. Cần verify tất cả 017 migrations chạy đúng thứ tự không conflict.

**Việc cần làm:**

- Tạo `018_add_alert_title.py`: `ADD COLUMN title VARCHAR(200)`.
- Chạy thử `./cli.sh hdtv-migrate` trên fresh DB container và verify không error.
- `entities.py Alert`: Thêm `title = Column(String(200), nullable=True)`.
- `AlertOut` schema: Thêm field `title: str | None`.
- `dossier_service.py list_alerts()`: Trả `title` từ entity.

**Acceptance:**
- `./cli.sh hdtv-migrate` chạy clean trên fresh DB.
- `GET /api/v1/alerts` response có `title` field.

**status:** PENDING

---

### T-67: API Error Handling Pass — Tất cả BE Endpoints

- **deps:** T-63, T-64, T-65
- **priority:** P2
- **BE files:** Tất cả routers

**Bugs phát hiện từ code scan:**

1. `alerts.py resolve_alert()` trả 404 khi not found — nhưng FE `alerts.js` không handle 404 riêng.
2. `notifications.py mark_notification_read_endpoint()` không validate `notification_id` integer.
3. `meta.py get_knowledge_graph()` raise 404 nhưng FE `graph.js` chỉ `finally { loading = false }` không log error.
4. `mcp.py` `_require_mcp_key()` trả 401 — FE `admin.js loadMcpLogs()` không handle 401 riêng.
5. Tất cả routers thiếu `logging.exception()` cho unexpected errors.

**Việc cần làm:**

- Mỗi router critical (dossiers, alerts, meta, mcp): Thêm `logger.exception()` trong exception handler.
- `graph.js fetchGraph()`: Thêm `error.value = e.response?.data?.detail || e.message`.
- `KnowledgeGraphView.vue`: Hiển thị error message khi `graphStore.error`.
- `admin.js loadMcpLogs()`: Catch 401 → set `error.value = "MCP API key chưa cấu hình"`.
- `SystemAdminView.vue` MCP tab: Hiển thị error warning khi `adminStore.error`.

**Acceptance:**
- Mọi API call trong FE có error handling visible (không silent fail).
- BE log mọi unexpected 5xx.

**status:** PENDING

---

## Phase 13C — AI Pipeline Audit

---

### T-68: Planner — Fix Dossier 198 Plan Không Đúng Tools

- **deps:** T-64
- **priority:** P1
- **BE file:** `app/services/orchestrator/planner.py`, `app/services/tools/base.py`

**Bugs phát hiện từ code scan:**

1. `build_fallback_plan()` dùng tất cả active tools từ DB — Dossier #198 UAV cần tools đặc thù: `legal_doc_lookup` và `supplier_feedback_lookup` thay vì `ErpBudgetCheck` / `ErpInventoryCheck`.
2. `_FINANCIAL_PARALLEL_TOOLS` hardcode `{"ErpBudgetCheck", "ErpInventoryCheck"}` — cần thêm parallel group cho UAV tools.
3. Không có 2 tool mới: `legal_doc_lookup` và `supplier_feedback_lookup` trong tool registry.
4. `_TOOL_INPUT_REQUIRED_FIELDS` trong `base.py` chưa có entry cho 2 tools mới.

**Việc cần làm:**

- `app/services/tools/`: Tạo `legal_doc_lookup.py` và `supplier_feedback_lookup.py` implement interface tool (validate input, gọi Chroma/mock, trả JSON output).
- `base.py _TOOL_INPUT_REQUIRED_FIELDS`: Thêm `"legal_doc_lookup": ["doc_no"]` và `"supplier_feedback_lookup": ["spec_item"]`.
- `scripts/seed.py`: Seed 2 `ToolConfig` records cho tools mới.
- `gemini_mock.py`: Thêm mock responses cho 2 tools mới theo nội dung Check 1 và Check 3 từ KE_HOACH_DEMO_HDTV_AI.md Mục 4.
- `planner.py`: Khi dossier_type = "Tờ trình Phê duyệt Tiêu chuẩn kỹ thuật", suggest `legal_doc_lookup` + `supplier_feedback_lookup` trong plan prompt.

**Acceptance:**
- `GET /api/v1/tools` trả 8+ tools bao gồm 2 tools mới.
- POST appraise Dossier #198 → plan có steps dùng `legal_doc_lookup` và `supplier_feedback_lookup`.
- `_validate_tool_input("legal_doc_lookup", {"doc_no": "8594/QĐ-EVNHANOI"})` → không raise error.

**status:** PENDING

---

### T-69: Critic — Fix Mock Response cho Dossier 198

- **deps:** T-68
- **priority:** P1
- **BE file:** `app/services/orchestrator/critic.py`, `app/services/tools/gemini_mock.py`

**Bugs phát hiện từ code scan:**

1. `critic.py` dùng LLM hoặc rule fallback để review — với `LLM_MODE=mock`, cần mock response cụ thể cho Dossier #198 trả `verdict: "Needs Revision"` và detail Check 3.
2. `gemini_mock.py` hiện mock generic responses, không có case cho `critic` role + dossier_id=5.
3. WS event `revision_requested` chưa được emit — sequence diagram mô tả nhánh này nhưng code chỉ có `critic_review`.
4. Sau `critic_review` với `Needs Revision`, agent không gửi `revision_requested` event tới FE.

**Việc cần làm:**

- `gemini_mock.py`: Thêm mock cho role `critic` khi context chứa "198/TTr-EVNHANOI" → trả JSON với `verdict: "Needs Revision"`, `issues: ["Đề xuất hạ chỉ tiêu Bộ nhớ trong 64GB→16GB (-75%)"]`.
- `react_agent.py` / `critic.py`: Sau `critic_review` emit, nếu verdict = `Needs Revision` → emit thêm `revision_requested` event với details.
- `pubsub.py`: Verify `publish_event()` có thể emit `revision_requested` type.
- `SplitViewWorkspace.vue`: Handle `revision_requested` WS event → hiển thị banner "Ban Kỹ thuật cần giải trình".

**Acceptance:**
- POST appraise Dossier #198 → WS nhận `critic_review` với `verdict: "Needs Revision"`.
- Sau `critic_review` → WS nhận `revision_requested` event.
- FE Workspace hiển thị revision banner.

**status:** PENDING

---

### T-70: Seed Script Dossier 198 — Full Data Pipeline

- **deps:** T-64, T-68
- **priority:** P1
- **BE file:** `scripts/seed.py`, `scripts/seed_dossier_198.py` (NEW)

**Bugs phát hiện từ code scan:**

1. `scripts/seed.py` chưa có Dossier #198.
2. Không có script seed document_versions cho Dossier #198 (v1.0 và v1.1).
3. Không có seed agent_plans với 5 steps cho Dossier #198.
4. ChromaDB chưa có legal docs cho QĐ 8594, NQ 180, QĐ 153.

**Việc cần làm:**

Tạo `scripts/seed_dossier_198.py` với các steps:
1. Insert `Dossier` record (id=5, doc_no="198/TTr-EVNHANOI", risk_level=medium, status=pending).
2. Insert `Alert` AL-1043 (title, severity=medium, dossier_id=5).
3. Insert 2 `DocumentVersion` records cho dossier_id=5 (v1.0 draft, v1.1 với AI risk section).
4. Insert `AgentPlan` với 5 plan steps tương ứng 5 checks.
5. Insert 5 `AiAuditLog` records (mỗi check 1 log với plan_step_id).
6. Insert 2 `McpCallLog` records (legal_doc_lookup, supplier_feedback_lookup).
7. Upsert 3 chunks vào ChromaDB `legal_docs` collection (QĐ 8594, NQ 180, QĐ 153).
8. Upsert 1 record vào ChromaDB `feedback_lessons` (lesson về NCC hạ tiêu chuẩn).
9. Index dossier vào Meilisearch.

Cập nhật `scripts/seed.py` để gọi `seed_dossier_198()` sau existing seed.

**Acceptance:**
- `./cli.sh hdtv-seed` chạy clean.
- `GET /api/v1/dossiers` trả 5+ dossiers bao gồm "198/TTr-EVNHANOI".
- `GET /api/v1/knowledge-graph?dossier_id=5` trả 7 nodes UAV.
- `GET /api/v1/alerts` trả AL-1043.
- `GET /api/v1/mcp/audit-logs` trả 2 logs cho Dossier #198.

**verify_cmd:**
```bash
./cli.sh hdtv-seed
curl -sf http://localhost:8000/api/v1/dossiers | python -m json.tool | grep "198/TTr"
curl -sf "http://localhost:8000/api/v1/knowledge-graph?dossier_id=5" | python -m json.tool | grep "tt198"
```

**status:** PENDING

---

### T-71: LLM Router — Fix Mock Mode Stability

- **deps:** —
- **priority:** P1
- **BE file:** `app/services/llm_router.py`, `app/services/tools/gemini_mock.py`

**Bugs phát hiện từ code scan:**

1. `LLM_MODE=mock` trong `.env` nhưng `llm_router.py` ưu tiên live Gemini nếu `GEMINI_API_KEY` set → demo có thể dùng live API thay vì mock.
2. `gemini_mock.py` trả generic responses — không đủ để demo flow 5 checks cho Dossier #198.
3. Circuit breaker sẽ open nếu mock mode trả error quá nhiều lần.
4. `_next_gemini_key()` query DB cho active Gemini keys — trong mock mode không cần.

**Việc cần làm:**

- `llm_router.py`: Khi `settings.llm_mode == "mock"`, skip DB key lookup và Gemini call → direct route sang `gemini_mock`.
- `gemini_mock.py`: Thêm mock handlers đặc thù theo `AgentRole`:
  - `PLANNER` + dossier "198" → trả plan JSON với 5 steps (legal_doc_lookup, authority_check, spec_vs_supplier_feedback, market_survey, document_structure).
  - `CRITIC` + dossier "198" → trả `Needs Revision` verdict.
  - `REFLECTOR` → trả `sufficient` sau 2 tool calls.
- `config.py`: Thêm `llm_mode: str = "mock"` với comment.

**Acceptance:**
- `LLM_MODE=mock` → POST appraise → không có HTTP calls tới Google API.
- Mock planner trả plan với 5 steps đúng chuẩn Dossier #198.

**status:** PENDING

---

### T-72: Full E2E Demo Run Verification

- **deps:** T-55 → T-71
- **priority:** P1
- **scope:** Integration test toàn bộ luồng demo

**Kịch bản test:**

1. Fresh start: `./cli.sh hdtv-up && ./cli.sh hdtv-migrate && ./cli.sh hdtv-seed`
2. Mở FE: `http://<VM_IP>:3080`
3. Dashboard: Verify 3 KPI cards có số thật, notable_dossiers có "198/TTr-EVNHANOI".
4. Dossier List: Verify "198/TTr-EVNHANOI" xuất hiện, filter "Ban Kỹ thuật" hoạt động.
5. Click Dossier #198 → Workspace: Verify tabs load không crash.
6. Bấm "Chạy thẩm định" → WS: Verify nhận `task_started` → `plan_created` → 5× `tool_result` → `critic_review` → `revision_requested`.
7. Alerts: Verify AL-1043 xuất hiện, severity = medium.
8. Knowledge Graph → chọn Dossier #198: Verify 7 nodes UAV.
9. Admin → MCP Audit: Verify 2 records cho Dossier #198.
10. Switch role sang "admin" → vào /admin thành công.

**Acceptance:** Tất cả 10 bước trên pass không error.

**verify_cmd:**
```bash
./cli.sh hdtv-smoke
# Smoke test: health + dossiers + agent/metrics + WS connect
```

**status:** PENDING

---

## Phase 13 Dependency Graph

| Task | Blocked by | Priority | Layer |
|------|------------|----------|-------|
| T-55 | — | P1 | FE |
| T-56 | — | P0 | FE+BE |
| T-57 | T-56 | P1 | FE+BE |
| T-58 | T-56 | P1 | FE+BE |
| T-59 | — | P1 | FE+BE |
| T-60 | — | P1 | FE |
| T-61 | — | P2 | FE+BE |
| T-62 | — | P2 | FE |
| T-63 | T-56 | P1 | BE |
| T-64 | T-59 | P1 | BE |
| T-65 | T-57 | P1 | BE |
| T-66 | — | P1 | BE |
| T-67 | T-63,T-64 | P2 | BE |
| T-68 | T-64 | P1 | AI |
| T-69 | T-68 | P1 | AI |
| T-70 | T-64,T-68 | P1 | AI+Seed |
| T-71 | — | P1 | AI |
| T-72 | T-55→T-71 | P1 | E2E |

**Thứ tự thực hiện (theo priority và deps):**

```
Batch 1 (P0):  T-56 (route ordering bug)
Batch 2 (P1):  T-71 (mock mode) → T-64 (meta/seed) → T-59 (graph)
Batch 3 (P1):  T-55, T-57, T-58, T-60, T-65 (song song)
Batch 4 (P1):  T-63, T-66, T-68, T-69, T-70
Batch 5 (P1):  T-72 (E2E verification)
Batch 6 (P2):  T-61, T-62, T-67
```

---

## Prompt Templates — Copy để dùng với Cursor/Kiro

> **Cách dùng:** Copy prompt tương ứng với task bạn muốn làm, paste vào Cursor/Kiro chat.

---

### Prompt T-56: Fix Route Ordering Bug

```
Đọc file `project_devops/apps/hdtv-ai-platform/app/routers/dossiers.py`.

Bug P0: Route `GET /dossiers/units` đăng ký SAU `GET /dossiers/{dossier_id}`. 
FastAPI match "units" như integer dossier_id → HTTP 422.

Việc cần làm:
1. Di chuyển `@router.get("/units", ...)` endpoint lên TRƯỚC `@router.get("/{dossier_id}", ...)`.
2. Đọc `app/models/entities.py` và `app/schemas/dossier.py` → verify `DossierOut` trả field `risk_level` (không phải `risk`).
3. Đọc `app/services/dossier_service.py` → verify `list_dossiers()` trả `risk_level`.
4. Đọc `app/models/entities.py Alert` class → thêm field `title = Column(String(200), nullable=True)`.
5. Tạo `alembic/versions/018_add_alert_title.py` migration: ADD COLUMN title VARCHAR(200) to alerts table.
6. Update `app/schemas/dossier.py AlertOut` → thêm `title: str | None = None`.
7. Update `app/services/dossier_service.py list_alerts()` → include title.

Verify: `curl -sf http://localhost:8000/api/v1/dossiers/units` phải trả list strings, không 422.
```

---

### Prompt T-57: Fix WS Race Condition + task_started Event

```
Đọc các file:
- `project_devops/apps/hdtv-ai-platform/app/routers/dossiers.py` (appraise_dossier endpoint)
- `project_devops/apps/hdtv-ai-platform/app/routers/ws.py`
- `project_devops/apps/hdtv-ai-platform/app/services/pubsub.py`
- `project_devops/apps/hdtv-ai-prototype/src/views/SplitViewWorkspace.vue`

Bug: POST /appraise không emit `task_started` WS event → FE có thể miss events đầu.

Việc cần làm BE:
1. `dossiers.py` trong `appraise_dossier()`, sau `task = run_appraisal_task.delay(...)`:
   Thêm: `await publish_event(dossier_id, {"type": "task_started", "task_id": task.id, "dossier_id": dossier_id})`
2. `ws.py`: Thêm heartbeat ping mỗi 30s. Trong loop: nếu 30s không có message → send `{"type": "ping"}`.
3. `ws.py _get_dossier_snapshot()`: Join với agent_plans → thêm `latest_plan_steps` vào snapshot.

Việc cần làm FE `SplitViewWorkspace.vue`:
1. Thêm WS reconnect logic: khi disconnect → retry sau 2s, 5s, 10s (max 3 lần).
2. Handle WS event `revision_requested` → hiển thị banner "Cần giải trình bổ sung".
3. Khi mount: gọi `GET /api/v1/dossiers/:id/reference-documents` → bind vào referenceDocs.
4. Khi mount: gọi `GET /api/v1/dossiers/:id/document-versions` → bind vào reportVersions.
5. `aiChecks` load từ WS `plan_created` event.plan_steps, không hardcode.
```

---

### Prompt T-59: Fix Knowledge Graph Mandatory Param + Dossier 198 Nodes

```
Đọc các file:
- `project_devops/apps/hdtv-ai-prototype/src/views/KnowledgeGraphView.vue`
- `project_devops/apps/hdtv-ai-prototype/src/stores/graph.js`
- `project_devops/apps/hdtv-ai-platform/app/routers/meta.py`
- `project_devops/apps/hdtv-ai-platform/app/services/meta_service.py`

Bugs:
1. KnowledgeGraphView: `await dossierStore.fetchDossiers()` async nhưng code gọi `loadGraph(dossiers[0].id)` đồng thời → có thể undefined.
2. SVG edges không guard null khi node không tìm thấy → JS crash.
3. `build_knowledge_graph()` dùng generic LEGAL_FALLBACK cho tất cả dossiers.

Việc cần làm FE:
1. `KnowledgeGraphView.vue onMounted()`: Await fetchDossiers trước, guard `if (dossierStore.dossiers.length > 0)`.
2. SVG edge render: Thêm `v-if="nodes.find(n=>n.id===edge.source) && nodes.find(n=>n.id===edge.target)"`.
3. `graph.js fetchGraph()`: Thêm `try/catch`, set `error.value`.
4. View hiển thị error message khi `graphStore.error`.

Việc cần làm BE `meta_service.py build_knowledge_graph()`:
Thêm branch cho dossier_id == 5 (198/TTr-EVNHANOI) với 7 nodes và 6 edges đặc thù:
Nodes: tt198 (dossier), qd8594 (legal), nq180 (law), qd153 (law), pl_so_sanh (data), apex_feedback (data), risk_spec (risk)
Edges: tt198→qd8594 "Căn cứ theo", tt198→nq180 "Căn cứ theo", tt198→qd153 "Đúng thẩm quyền theo", tt198→pl_so_sanh "Chứa Phụ lục", pl_so_sanh→apex_feedback "Đối chiếu", apex_feedback→risk_spec "Gây ra"
Tọa độ: tt198(400,300), qd8594(150,150), nq180(280,120), qd153(410,100), pl_so_sanh(600,200), apex_feedback(720,320), risk_spec(820,200)
```

---

### Prompt T-64 + T-70: Seed Dossier 198 UAV

```
Tạo file `project_devops/apps/hdtv-ai-platform/scripts/seed_dossier_198.py`.

Đọc trước:
- `project_devops/apps/hdtv-ai-platform/scripts/seed.py` (để biết pattern)
- `project_devops/apps/hdtv-ai-platform/app/models/entities.py` (để biết models)
- File KE_HOACH_DEMO_HDTV_AI.md Mục 3, 4, 6 (context dossier 198)

Script cần làm theo thứ tự (idempotent - check trước khi insert):
1. Insert Dossier(id=5, doc_no="198/TTr-EVNHANOI", title="Phê duyệt Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV) phục vụ kiểm tra đường dây 220/110kV", unit="Ban Kỹ thuật (KT)", submitted_by="Tổng Giám đốc", risk_level=RiskLevel.medium, status=DossierStatus.pending)
2. Insert Alert(title="Đề xuất hạ tiêu chuẩn kỹ thuật từ nhà cung cấp tư vấn", severity="medium", source="AI Spec Cross-Check", description="AI phát hiện Apex Tech đề xuất giảm 3 chỉ tiêu UAV...", dossier_id=5, status=AlertStatus.open)
3. Insert 2 DocumentVersion(dossier_id=5): v1.0 "Dự thảo ban đầu", v1.1 "Đã chèn phần Rủi ro AI"
4. Insert AgentPlan(dossier_id=5, plan_json={goal, steps: 5 steps}, revision=0, status="completed")
5. Insert 5 AiAuditLog(task_id="demo-198", tool_name=[5 tool names], plan_step_id=...)
6. Insert 2 McpCallLog(tool_name="legal_doc_lookup"/"supplier_feedback_lookup", api_key_prefix="demo", execution_ms=250/380, is_error=False)
7. Upsert ChromaDB collection "legal_docs": 3 docs (QĐ 8594, NQ 180, QĐ 153)
8. Upsert ChromaDB collection "feedback_lessons": 1 lesson về NCC hạ tiêu chuẩn
9. Index Meilisearch với dossier record

Update `scripts/seed.py` cuối file: `from scripts.seed_dossier_198 import seed_dossier_198; seed_dossier_198(session)`
```

---

### Prompt T-68: Thêm Tools legal_doc_lookup và supplier_feedback_lookup

```
Đọc các file:
- `project_devops/apps/hdtv-ai-platform/app/services/tools/base.py` (tool execution pattern)
- `project_devops/apps/hdtv-ai-platform/app/services/tools/gemini_mock.py` (mock pattern)
- `project_devops/apps/hdtv-ai-platform/app/services/tools/legal_rag.py` (legal tool mẫu)

Tạo 2 tool files mới:

1. `app/services/tools/legal_doc_lookup.py`:
   - Function `legal_doc_lookup(params: dict) -> dict`
   - Validate: require `doc_no` field (format regex: `\\d+/[A-Z-]+`)
   - Logic: query ChromaDB collection "legal_docs" với `doc_no` → trả matches
   - Fallback mock: nếu không tìm thấy → trả mock content từ LEGAL_FALLBACK dict
   - Output: `{"doc_no": ..., "title": ..., "content": ..., "still_effective": true}`

2. `app/services/tools/supplier_feedback_lookup.py`:
   - Function `supplier_feedback_lookup(params: dict) -> dict`
   - Validate: require `spec_item` field (string)
   - Logic: search ChromaDB "legal_docs" cho supplier feedback về spec_item
   - Mock: nếu spec_item contains "bộ nhớ" hoặc "quãng đường" → trả mock Apex Tech feedback
   - Output: `{"spec_item": ..., "suppliers": [...], "proposals": [...], "risk_detected": true/false}`

Update `base.py _TOOL_INPUT_REQUIRED_FIELDS`:
```python
"legal_doc_lookup": ["doc_no"],
"supplier_feedback_lookup": ["spec_item"],
```

Update `gemini_mock.py`: Thêm cases cho 2 tools mới với mock responses đầy đủ.

Update `scripts/seed.py`: Seed 2 ToolConfig records cho tools mới.
```

---

*End of Phase 13 Tasks*
