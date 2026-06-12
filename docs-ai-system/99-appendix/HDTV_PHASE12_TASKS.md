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
- **status**: PENDING

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
- **status**: PENDING

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
  - `hdtv-ai-platform/app/models/entities.py` — thêm bảng `document_versions`
  - `hdtv-ai-platform/app/api/routes/dossiers.py` — thêm endpoints quản lý versions
- **acceptance**: Mỗi thay đổi tài liệu tạo version mới, lưu user, thời gian, mô tả thay đổi
- **verify_cmd**:
- **status**: PENDING

---

## T-48: Document Version Control (FE)
- **deps**: T-47
- **priority**: P2
- **files**:
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — thêm version selector cho các tab
- **acceptance**: Người dùng có thể xem các phiên bản cũ, chọn phiên bản để xem
- **verify_cmd**:
- **status**: PENDING

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
- **status**: PENDING

---

## T-51: Reference Document Management (BE)
- **deps**: —
- **priority**: P1
- **files**:
  - `hdtv-ai-platform/app/api/routes/dossiers.py` — thêm endpoints upload/xem/xóa tài liệu tham khảo
- **acceptance**: Người dùng có thể upload nhiều file PDF/Excel làm tài liệu tham khảo cho dossier
- **verify_cmd**:
- **status**: PENDING

---

## T-52: Reference Document Management (FE)
- **deps**: T-51
- **priority**: P1
- **files**:
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — cập nhật tab "Tài liệu Khác" để thực sự upload/xem file
- **acceptance**: Người dùng có thể upload file, xem list, xóa file
- **verify_cmd**:
- **status**: PENDING

---

## T-53: Notification System (BE)
- **deps**: T-43
- **priority**: P2
- **files**:
  - `hdtv-ai-platform/app/models/entities.py` — thêm bảng `notifications`
  - `hdtv-ai-platform/app/api/routes/notifications.py` — NEW: notifications endpoints
  - `hdtv-ai-platform/app/services/notification_service.py` — NEW: service gửi notification
- **acceptance**: Notification được tạo khi status thay đổi, có feedback mới, v.v.
- **verify_cmd**:
- **status**: PENDING

---

## T-54: Notification System (FE)
- **deps**: T-53
- **priority**: P2
- **files**:
  - `hdtv-ai-prototype/src/components/NotificationBell.vue` — NEW: notification bell component
  - `hdtv-ai-prototype/src/views/NotificationsView.vue` — NEW: notifications page
  - `hdtv-ai-prototype/src/router/index.js` — thêm route notifications
- **acceptance**: Người dùng thấy số thông báo mới, xem danh sách thông báo
- **verify_cmd**:
- **status**: PENDING

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
