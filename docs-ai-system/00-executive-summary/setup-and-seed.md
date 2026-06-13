# Setup & Seed — Khởi tạo Dữ liệu Thật từ Tờ trình EVN

> **Audience:** DevOps, Demo Engineer, CTO
> **Mục đích:** Giải thích cơ chế auto-seed — tại sao dữ liệu demo là dữ liệu thật, không phải dummy.

---

## Triết lý thiết kế Seed

**Dữ liệu demo = dữ liệu nghiệp vụ thật.**

Thay vì tạo dữ liệu giả ("Hồ sơ test 1", "Hồ sơ test 2"), toàn bộ seed data được xây dựng từ 4 file PDF tờ trình thật của EVN Hà Nội:

| File PDF | Nội dung |
|----------|----------|
| `07/KT` | Tờ trình Ban Kỹ thuật đề xuất tiêu chuẩn UAV |
| `198/TTr-EVNHANOI` | Tờ trình TGĐ trình HĐTV phê duyệt tiêu chuẩn UAV |
| Báo cáo thẩm tra | Ban Tổng hợp thẩm tra — 2 kiến nghị hiệu chỉnh cụ thể |
| Phiếu trình HĐTV (10/02/2025) | Phiếu trình chính thức lên HĐTV |

**Lý do quan trọng:** Platform này giải quyết bài toán thật — giúp EVN Hà Nội số hóa quy trình phê duyệt tờ trình HĐTV. Seed data phải phản ánh đúng luồng nghiệp vụ thật để demo có giá trị thuyết phục.

---

## Cơ chế Auto-Seed

### Biến điều khiển

| Biến | Vị trí | Giá trị | Tác dụng |
|------|--------|---------|----------|
| `HDTV_AUTO_SEED` | `.env` | `true` | Chạy seed tự động khi API khởi động |
| `COPY_PROJECT_DEVOPS` | Shell env | `1` | Vagrant tự copy toàn bộ `project_devops/` vào VM |

### Luồng khi `COPY_PROJECT_DEVOPS=1 vagrant up`

```
COPY_PROJECT_DEVOPS=1 vagrant up
        │
        ▼
Vagrant provision script
        │
        ├── Copy project_devops/ → VM /opt/hdtv/
        ├── Copy .env → VM /opt/hdtv/.env
        │
        ▼
Docker Compose up (9 services)
        │
        ├── postgres (healthy) ──────────┐
        ├── redis (healthy) ─────────────┤
        ├── chroma (healthy) ────────────┤
        ├── meilisearch (healthy) ───────┤
        └── minio (healthy) ────────────►│
                                         ▼
                                    hdtv-api starts
                                         │
                              HDTV_AUTO_SEED=true?
                                    YES  │
                                         ▼
                              python -m seeds.seed_all
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                        18 migrations          7 seed scripts
                        applied                run in order
```

### Thứ tự chạy seed (tất cả idempotent)

```
[1/7] seed_users.py         → 8 users (tên thật từ tờ trình EVN)
[2/7] seed_risk_rules.py    → 5 risk rules (dựa trên NĐ 24/2024)
[3/7] seed_dossiers.py      → 12 hồ sơ (đủ 11 trạng thái workflow)
[4/7] seed_workflow_diagrams.py → 3 BPMN XML (quy trình HĐTV thật)
[5/7] seed_alerts.py        → 8 alerts (2 từ Báo cáo thẩm tra thật)
[6/7] seed_appraisals.py    → 4 kết quả AI (báo cáo tiếng Việt đầy đủ)
[7/7] seed_notifications.py → 15 notifications (phân bổ theo vai trò)
```

**Idempotent:** Chạy lại bao nhiêu lần cũng được — không tạo dữ liệu trùng.

---

## Dữ liệu được seed — Chi tiết

### 8 Users (tên thật từ tờ trình)

| Email | Họ tên | Vai trò | Ghi chú |
|-------|--------|---------|---------|
| admin@evnhanoi.vn | Quản trị viên | admin | Quản trị hệ thống |
| dtanh@evnhanoi.vn | Đỗ Tuấn Anh | hdtv_leader | Ký Phiếu trình HĐTV |
| ddtien@evnhanoi.vn | Đoàn Đức Tiến | dept_head | Trưởng Ban TH, ký Báo cáo thẩm tra |
| nadung@evnhanoi.vn | Nguyễn Anh Dũng | dept_head | Phó TGĐ Kỹ thuật, ký tờ trình 07/KT |
| htminh@evnhanoi.vn | Hà Tuấn Minh | specialist | Người thẩm tra trong Báo cáo thẩm tra |
| dnchung@evnhanoi.vn | Đào Ngọc Chung | specialist | Ban Kỹ thuật |
| tvthuong@evnhanoi.vn | Trần Văn Thương | specialist | Thành viên HĐTV |
| pdnghia@evnhanoi.vn | Phạm Đại Nghĩa | specialist | Thành viên HĐTV |

**Mật khẩu:** `EVN@2024!`

### 12 Dossiers — Đủ 11 trạng thái

| doc_no | Trạng thái | Mô tả |
|--------|-----------|-------|
| 198/TTr-EVNHANOI | needs_revision | UAV — Hồ sơ trọng tâm, data thật |
| EVNHANOI-MBA-2024-021 | dept_approved | Máy biến áp 250kVA (50 bộ) |
| EVNHANOI-SCADA-2024-007 | approved | Nâng cấp SCADA/DMS |
| EVNHANOI-KT-2024-018 | rejected | Thí nghiệm thiết bị điện cao áp |
| EVNHANOI-CAP-2024-033 | pending | Cáp ngầm 22kV Quận Hoàn Kiếm |
| EVNHANOI-IT-2024-044 | draft | Máy tính xách tay IT |
| EVNHANOI-XL-2024-015 | submitted_to_dept | Trạm 110kV Tây Hồ giai đoạn 2 |
| EVNHANOI-TU-2024-028 | dept_rejected | Tư vấn giám sát 110kV Đông Anh |
| EVNHANOI-BT-2024-009 | submitted_to_board | Bảo trì đo đếm 110kV |
| EVNHANOI-VT-2024-052 | board_reviewed | Vật tư sửa chữa thường xuyên |
| EVNHANOI-NL-2024-061 | needs_revision | Phần mềm Smart Grid |
| EVNHANOI-AN-2024-006 | pending | Dụng cụ an toàn lao động |

### 3 BPMN Diagrams (quy trình thật)

| Diagram | Mô tả |
|---------|-------|
| Quy trình HĐTV 9 bước (198/TTr-EVNHANOI) | Ban KT → PTGĐ KT → TGĐ → Ban TH → Phiếu trình HĐTV → 5 TV HĐTV → CH HĐTV |
| Quy trình AI có làm rõ (MBA) | Có exclusive gateway: Cần làm rõ? Yes→Clarification / No→tiếp tục |
| Quy trình thẩm định cơ bản (SCADA) | 5 bước tuyến tính |

### 2 Alerts thật (từ Báo cáo thẩm tra 24/01/2025)

```
Alert 1: "Chưa thống nhất thuật ngữ trong Tiêu chuẩn kỹ thuật UAV"
  → Severity: medium | Tool: TechnicalStandardCheck | Status: open
  → Đây là Kiến nghị 1 từ Báo cáo thẩm tra thật của Ban Tổng hợp

Alert 2: "Tiêu chuẩn kỹ thuật còn chứa yếu tố đấu thầu không phù hợp"
  → Severity: medium | Tool: ProcurementCheck | Status: open
  → Đây là Kiến nghị 2 từ Báo cáo thẩm tra thật của Ban Tổng hợp
```

---

## Môi trường không có LLM Server

Nếu LLM server (llama-server) không chạy:

```
LLM_BASE_URL / ACER_HOST không kết nối được
        │
        ▼
LLM Router → Circuit Breaker OPEN
        │
        ▼
Fallback: Gemini Flash API (9 keys configured trong .env)
        │
        ▼
Nếu không có Gemini key → AI trả về "unavailable"
Các tính năng không dùng LLM vẫn hoạt động bình thường
(Dashboard, Dossiers, Alerts, Notifications, BPMN Viewer...)
```

**Cho buổi demo:** Seed data đã đầy đủ — không cần LLM chạy để xem hồ sơ, kết quả thẩm định (từ seed), alerts, workflow, dashboard.

---

## Chạy seed thủ công

```bash
# Trong container (không cần rebuild)
wsl docker exec hdtv-api python -m seeds.seed_all

# Xem log đầy đủ
wsl docker exec hdtv-api python -m seeds.seed_all 2>&1

# Reset và seed lại từ đầu
wsl docker exec hdtv-postgres psql -U hdtv_user -d hdtv_db \
  -c "TRUNCATE users, dossiers, alerts, appraisal_results, notifications, workflow_diagrams CASCADE;"
wsl docker exec hdtv-api python -m seeds.seed_all
```
