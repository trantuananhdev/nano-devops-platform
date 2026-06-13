# Demo Guide — Từ Zero đến Demo CEO trong 10 Phút

> **Audience:** CEO, CTO, Demo Engineer
> **Cập nhật:** 2026-06-13
> **Dữ liệu:** Lấy thật từ 4 tờ trình EVN Hà Nội (198/TTr-EVNHANOI — UAV 220/110kV)

---

## Cách khởi động nhanh

### Option A — Vagrant (môi trường đầy đủ, production-like)

```bash
# 1. Set biến môi trường trước khi vagrant up
export COPY_PROJECT_DEVOPS=1       # Tự động copy toàn bộ project vào VM

# 2. Đảm bảo .env có HDTV_AUTO_SEED=true
# → Khi VM khởi động, hệ thống tự động:
#   - Apply 18 DB migrations
#   - Seed dữ liệu thật từ tờ trình EVN (xem chi tiết bên dưới)
#   - Khởi động toàn bộ 9 services

vagrant up                          # ~3-5 phút — tất cả tự động
```

**Mở browser:**
- Frontend: `http://192.168.157.10:3080`
- API Docs: `http://192.168.157.10:8000/docs`
- Grafana:  `http://192.168.157.10:3000`

### Option B — Docker trực tiếp (dev/WSL)

```bash
cd project_devops/apps/hdtv-ai-platform

# Khởi động stack
wsl docker compose -f docker-compose.hdtv.yml up -d

# Seed dữ liệu thật (chỉ cần chạy 1 lần — idempotent)
wsl docker exec hdtv-api python -m seeds.seed_all
```

**Mở browser:**
- Frontend: `http://localhost:3080`
- API Docs: `http://localhost:8000/docs`

### Verify nhanh

```bash
curl http://localhost:8000/api/v1/health   # → {"status": "healthy"}
```

---

## Tài khoản demo (thật từ tờ trình EVN)

| Email | Họ tên | Vai trò | Chức vụ thực tế |
|-------|--------|---------|-----------------|
| `admin@evnhanoi.vn` | Quản trị viên | admin | Quản trị hệ thống |
| `dtanh@evnhanoi.vn` | **Đỗ Tuấn Anh** | hdtv_leader | Thành viên HĐTV EVNHANOI |
| `ddtien@evnhanoi.vn` | **Đoàn Đức Tiến** | dept_head | Trưởng Ban Tổng hợp |
| `nadung@evnhanoi.vn` | **Nguyễn Anh Dũng** | dept_head | Phó Tổng Giám đốc Kỹ thuật |
| `htminh@evnhanoi.vn` | **Hà Tuấn Minh** | specialist | Ban Tổng hợp (người thẩm tra) |
| `dnchung@evnhanoi.vn` | **Đào Ngọc Chung** | specialist | Ban Kỹ thuật |
| `tvthuong@evnhanoi.vn` | **Trần Văn Thương** | specialist | Thành viên HĐTV |
| `pdnghia@evnhanoi.vn` | **Phạm Đại Nghĩa** | specialist | Thành viên HĐTV |

> **Mật khẩu chung:** `EVN@2024!`

---

## Dữ liệu demo — Nguồn gốc từ tờ trình thật

### Hồ sơ trọng tâm: 198/TTr-EVNHANOI

> Phê duyệt Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV)
> phục vụ kiểm tra đường dây 220/110kV — EVNHANOI, 2025

**Nguồn tài liệu (4 file PDF):**

| File PDF | Nội dung | Vai trò trong demo |
|----------|----------|-------------------|
| Tờ trình 07/KT | Ban Kỹ thuật đề xuất tiêu chuẩn UAV | Hồ sơ nguồn, điểm khởi đầu workflow |
| Tờ trình 198/TTr-EVNHANOI | TGĐ trình HĐTV phê duyệt | Tờ trình chính được AI thẩm định |
| Báo cáo thẩm tra (Ban TH) | Kết quả thẩm tra 2 kiến nghị hiệu chỉnh | Kết quả AI so sánh được với thẩm tra thật |
| Phiếu trình HĐTV (10/02/2025) | Phiếu trình chính thức lên HĐTV | Workflow điểm kết thúc |

**Nội dung kỹ thuật thật được seed:**
- Tiêu chuẩn: ≤16kg, ≥40 phút bay, IP45, RTK+GNSS ≥4 hệ thống
- Camera nhiệt 640×512px, LIDAR ≥480.000 điểm/giây
- 04 bộ UAV cho Công ty Lưới điện Cao thế TP Hà Nội
- Khảo sát 4 đơn vị — 2 phúc đáp: Apex Tech VN + MAJ

### Tổng số dữ liệu được seed

```
8 users (tên thật từ tờ trình EVN)
16 dossiers (đủ 11 trạng thái workflow)
3 BPMN diagrams (quy trình HĐTV 9 bước thật)
8 alerts (2 alert từ Báo cáo thẩm tra thật)
4 appraisal results (báo cáo AI tiếng Việt đầy đủ)
15 notifications (phân bổ theo workflow)
```

---

## Kịch bản demo 10 phút

### Scene 1 — Dashboard KPI (1 phút)

```
Login: admin@evnhanoi.vn / EVN@2024!
→ Dashboard hiện ngay:
  - 12 hồ sơ đang chờ xử lý
  - 7 alert đang mở
  - 5 hồ sơ rủi ro cao
  - Biểu đồ phân bổ theo đơn vị (Ban KT, Ban VT, Ban QLDA...)
```

**Thông điệp CEO:** *"Lãnh đạo thấy ngay toàn cảnh mà không cần hỏi ai."*

---

### Scene 2 — Hồ sơ UAV thật (1.5 phút)

```
Vào Dossiers → tìm "198/TTr-EVNHANOI"
→ Thấy: status "Cần chỉnh sửa", risk "Trung bình"
→ Bấm vào → Workspace hiện:
  - Trái: thông tin tờ trình đầy đủ (số hiệu, đơn vị, ngày)
  - Phải: kết quả thẩm định AI
  - Tab Appraisal: báo cáo chi tiết 3 phần (Pháp lý ✅ / Kỹ thuật ⚠️ / Mua sắm ⚠️)
  - 2 kiến nghị hiệu chỉnh (khớp với Báo cáo thẩm tra thật)
```

**Thông điệp CTO:** *"AI đọc tờ trình thật, phát hiện đúng 2 vấn đề mà Ban Tổng hợp cũng ghi trong báo cáo."*

---

### Scene 3 — Workflow BPMN thật (1 phút)

```
Vào tab Workflow → hiện BPMN diagram 9 bước:
  Ban KT (07/KT) → AI Thẩm định → PTGĐ Kỹ thuật
  → TGĐ (198/TTr-EVNHANOI) → Ban Tổng hợp thẩm tra
  → Phiếu trình HĐTV → 5 TV HĐTV xem xét
  → CH HĐTV ban hành Nghị quyết → Phê duyệt
```

**Thông điệp CEO:** *"Đây chính xác là quy trình phê duyệt HĐTV EVNHANOI — không phải ví dụ mẫu."*

---

### Scene 4 — AI Thẩm định Real-time (2 phút)

```
Chọn hồ sơ bất kỳ (pending) → bấm "Thẩm định"
→ WebSocket stream hiện real-time:
  "Lập kế hoạch thẩm định..." [plan_created]
  "Kiểm tra pháp lý..." [tool: LegalGraphRAG]
  "Kiểm tra ngân sách..." [tool: ErpBudgetCheck]
  "Kiểm tra tiêu chuẩn kỹ thuật..." [tool: TechnicalStandardCheck]
  "Phản tư kết quả..." [reflect]
  "Critic đánh giá chất lượng..." [critic_review]
  → 30-60 giây: "Thẩm định hoàn tất"
  → Risk badge: 🔴 CAO / 🟡 TRUNG BÌNH / 🟢 THẤP
```

**Thông điệp CEO:** *"2-3 ngày thẩm định thủ công → 30-60 giây. Mọi bước đều có log, không có hộp đen."*

---

### Scene 5 — Vai trò khác nhau, báo cáo khác nhau (1 phút)

```
Login dtanh@evnhanoi.vn (Đỗ Tuấn Anh — TV HĐTV)
→ Xem hồ sơ UAV → báo cáo: tóm tắt 1 trang, risk level nổi bật, kiến nghị hành động

Login htminh@evnhanoi.vn (Hà Tuấn Minh — Chuyên viên thẩm tra)
→ Xem cùng hồ sơ → báo cáo: đầy đủ kỹ thuật, tất cả checks, scoring từng tool
```

**Thông điệp CEO:** *"Lãnh đạo HĐTV đọc báo cáo điều hành. Chuyên viên thẩm tra đọc chi tiết kỹ thuật. Cùng 1 AI, 2 output khác nhau."*

---

### Scene 6 — Alerts từ thẩm tra thật (1 phút)

```
Vào Alerts:
→ Alert 1 (medium): "Chưa thống nhất thuật ngữ trong Tiêu chuẩn kỹ thuật UAV"
   → Nguồn: TechnicalStandardCheck | Kiến nghị 1 từ Báo cáo thẩm tra thật
→ Alert 2 (medium): "Tiêu chuẩn kỹ thuật còn chứa yếu tố đấu thầu không phù hợp"
   → Nguồn: ProcurementCheck | Kiến nghị 2 từ Báo cáo thẩm tra thật
→ Bấm "Resolve" → alert được đóng, ghi log ai giải quyết lúc nào
```

**Thông điệp CEO:** *"Alert này không phải AI bịa — chính xác là 2 điểm mà Ban Tổng hợp EVNHANOI đã ghi trong báo cáo thẩm tra thật."*

---

### Scene 7 — Audit Trail & Observability (CTO, 1.5 phút)

```
Admin > Audit Logs:
→ Mỗi tool call: tool_name, execution_ms, inputs, outputs, plan_step_id
→ Trace: từ báo cáo cuối → từng bước agent → từng tool call

Mở Grafana → Dashboard "HDTV AI Agent":
→ LLM health: circuit breaker state, latency histogram
→ Tool execution rate by tool name
→ Appraisal throughput (hồ sơ/giờ)
→ 14 alert rules active (LLM latency, error rate, circuit trips)
```

**Thông điệp CTO:** *"Toàn bộ hành vi AI có thể trace từ Grafana dashboard. Không có 'hộp đen' nào."*

---

### Scene 8 — Human-in-the-Loop (1 phút, optional)

```
Khi AI gặp hồ sơ thiếu thông tin:
→ WS event: "clarification_requested"
→ UI hiện inline form: "Nhà thầu Apex Tech VN có giấy phép bay không người lái không?"
→ User trả lời → agent tiếp tục từ điểm dừng
→ Không cần restart — state được lưu đầy đủ
```

**Thông điệp CEO:** *"AI không tự quyết khi chưa đủ thông tin. Con người vẫn là người quyết định."*

---

## Fallback nếu có sự cố

| Sự cố | Fix nhanh |
|-------|-----------|
| LLM server không bật | Gemini API tự động fallback (9 API keys) |
| Container chưa start | `wsl docker compose up -d` → đợi healthy |
| Seed bị lỗi | `wsl docker exec hdtv-api python -m seeds.seed_all` (idempotent, retry OK) |
| DB chưa có data | Kiểm tra `HDTV_AUTO_SEED=true` trong `.env` |
| Frontend không load | Check nginx container: `wsl docker logs hdtv-frontend` |

---

## Key messages cho CEO/CTO

> **Tốc độ:** 30-60 giây thay vì 2-3 ngày thẩm định thủ công.

> **Tin cậy:** AI đọc đúng tờ trình thật 198/TTr-EVNHANOI, phát hiện đúng 2 vấn đề mà Ban Tổng hợp cũng xác nhận.

> **Kiểm soát:** AI không tự quyết khi không chắc — Human-in-the-Loop, lãnh đạo phê duyệt cuối cùng.

> **Minh bạch:** Mọi hành động AI đều có audit trail, trace được từng bước, compliance hoàn chỉnh.

> **Học hỏi:** Hệ thống học từ phản hồi người dùng — càng dùng càng chính xác hơn.
