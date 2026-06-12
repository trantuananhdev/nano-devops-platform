# HDTV AI Platform — Demo Guide

## Hướng dẫn chạy demo từ A-Z

---

## Bước 1: Chuẩn bị môi trường

### Yêu cầu hệ thống
- Windows/Linux/macOS với Vagrant + VirtualBox
- RAM: Ít nhất 8GB (4GB dành cho VM Alpine, 4GB cho host)
- Kho trống: Ít nhất 20GB

### Cấu hình trước khi chạy
```powershell
# Windows PowerShell
set COPY_PROJECT_DEVOPS=1
set VM_MEM=4096
```

---

## Bước 2: Khởi động VM Alpine

```powershell
# Khởi động VM (nếu chưa chạy)
vagrant up

# SSH vào VM
vagrant ssh
```

---

## Bước 3: Triển khai LLM Node (Ubuntu) — tùy chọn

Nếu bạn có máy Ubuntu riêng để chạy Gemma:

```bash
# Trên Alpine VM
cd /opt/platform/src/nano-project-devops
./cli.sh ansible-ping          # Kiểm tra kết nối
./cli.sh ansible-bootstrap     # Cấu hình ban đầu (nếu cần)
./cli.sh ansible-deploy-llm    # Triển khai llama-server + Caddy
```

---

## Bước 4: Khởi động HDTV Platform

```bash
# Trên Alpine VM
cd /opt/platform/src/nano-project-devops

# Tắt observability stack để tiết kiệm RAM (nếu cần)
./cli.sh obs-down

# Khởi động toàn bộ HDTV stack
./cli.sh hdtv-up
```

Đợi khoảng 1-2 phút cho tất cả container khởi động hoàn tất.

---

## Bước 5: Chạy database migrations

```bash
./cli.sh hdtv-migrate
```

Điều này sẽ chạy tất cả migrations từ 001 đến 012.

---

## Bước 6: Seed dữ liệu (bao gồm dossier 198 thật!)

```bash
./cli.sh hdtv-seed
```

Seed script sẽ tự động:
1. Tạo users (hdtv_leader, dept_head, admin, specialist)
2. Tạo 5 dossiers (bao gồm **198/TTr-EVNHANOI**)
3. Tạo risk rules & tool configs
4. Upload **PDF thật** của dossier 198 lên MinIO
5. Extract text từ PDFs và ingest vào Chroma RAG
6. Index tất cả vào Meilisearch
7. Tạo agent memories và user preferences

---

## Bước 7: Truy cập giao diện web

### URLs truy cập
- **Frontend HDTV**: `http://<VM_IP>:3080` hoặc `https://hdtv.nano.platform`
- **API Docs (Swagger)**: `http://<VM_IP>:8000/docs`
- **MinIO Console**: `http://<VM_IP>:9001` (user: hdtv_minio, pass: từ .env)
- **Grafana**: `https://grafana.nano.platform` (nếu observability đang chạy)

### Lấy IP của VM Alpine
Trên host Windows:
```powershell
vagrant ssh -c "ip addr show eth1"
```

Hoặc xem file `.env` có biến `VM_IP`.

---

## Bước 8: Demo features chính

### 1. Dashboard tổng quan
- Mở trang chính, xem danh sách dossiers nổi bật
- Thấy dossier **198/TTr-EVNHANOI** với risk level `medium`

### 2. Xem chi tiết dossier 198
- Click vào dossier **198/TTr-EVNHANOI — Tiêu chuẩn kỹ thuật UAV**
- Xem PDF gốc ngay trong trình duyệt (nếu đã upload thành công)
- Xem tab Tờ trình, Phụ lục, Tài liệu khác, Báo cáo thẩm định, Nghị quyết

### 3. Chạy AI Appraisal
- Click nút **"Chạy thẩm định AI"**
- Quan sát progress real-time qua WebSocket
- Xem kết quả: Plan → Execute → Reflect → Critic
- Xem audit logs chi tiết của từng tool

### 4. Legal RAG với dữ liệu thật
- Tìm kiếm văn bản pháp lý trong tab Knowledge Graph
- Query về "Quyết định 8594", "UAV", "tiêu chuẩn kỹ thuật"
- Xem kết quả từ Chroma với các chunk từ PDF thật

### 5. Admin Panel
- Vào trang System Admin
- Xem tab API Keys (quản lý Gemini/MCP keys)
- Xem tab MCP Audit Logs (lịch sử gọi tool)
- Xem tab Agent Intelligence (metrics về agent)

---

## Câu lệnh CLI hữu ích

### Quản lý HDTV stack
```bash
./cli.sh hdtv-up       # Khởi động
./cli.sh hdtv-down     # Dừng
./cli.sh hdtv-logs     # Xem logs
./cli.sh hdtv-migrate  # Run migrations
./cli.sh hdtv-seed     # Seed dữ liệu
./cli.sh hdtv-backup   # Backup dữ liệu
```

### Quản lý LLM Node
```bash
./cli.sh ansible-ping          # Kiểm tra kết nối Ubuntu
./cli.sh ansible-deploy-llm    # Triển khai llama-server
./cli.sh ansible-teardown-llm  # Gỡ bỏ LLM node
```

### Observability
```bash
./cli.sh obs-up    # Khởi động Grafana/Prometheus/Loki
./cli.sh obs-down  # Dừng observability
```

---

## Dữ liệu demo có sẵn

### Dossiers
1. **124/TTr-B02** — Cáp ngầm Ba Đình (high risk)
2. **89/TTr-B08** — Trạm biến áp 110kV (medium risk)
3. **45/TTr-B12** — Vật tư An toàn PCTT (high risk)
4. **210/TTr-B09** — Kinh doanh Q3 (low risk)
5. **198/TTr-EVNHANOI** — Tiêu chuẩn UAV (medium risk) ⭐ **REAL DATA!**

### Users & Roles
| User ID | Role | Mô tả |
|---------|------|-------|
| 1 | hdtv_leader | Lãnh đạo HĐTV - báo cáo ngắn gọn |
| 2 | dept_head | Trưởng ban - checklist chi tiết |
| 3 | admin | Quản trị viên - full audit |
| 4 | specialist | Chuyên gia - báo cáo kỹ thuật |

---

## Khắc phục sự cố

### Problem: Container không khởi động
```bash
./cli.sh hdtv-logs
# Kiểm tra logs của từng container
```

### Problem: Migration lỗi
```bash
# Reset DB và chạy lại
docker stop hdtv-postgres
docker rm hdtv-postgres
docker volume rm hdtv_postgres_data
./cli.sh hdtv-up
./cli.sh hdtv-migrate
./cli.sh hdtv-seed
```

### Problem: MinIO upload lỗi
- Kiểm tra MinIO container đang chạy: `docker ps | grep minio`
- Kiểm tra bucket đã được tạo: truy cập MinIO Console
- Kiểm tra `.env` có đúng MINIO credentials

### Problem: Chroma không kết nối
- Seed script tự degrade nếu Chroma không reachable
- Dữ liệu vẫn seed vào DB, chỉ phần vector bị skip
- Kiểm tra: `docker ps | grep chroma`

---

## Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────┐
│                     Windows Host                            │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Alpine VM (192.168.157.10)               │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │              HDTV Stack                        │  │ │
│  │  │  - FastAPI API               :8000             │  │ │
│  │  │  - Vue3 Frontend             :3080             │  │ │
│  │  │  - PostgreSQL                :5432             │  │ │
│  │  │  - Redis                     :6379             │  │ │
│  │  │  - Chroma DB                 :8000             │  │ │
│  │  │  - MinIO                     :9000             │  │ │
│  │  │  - Meilisearch               :7700             │  │ │
│  │  │  - Celery Worker + Beat                         │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                           │                                │
│                           ▼                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           Ubuntu Server (LLM Node)                    │ │
│  │  - llama-server (Gemma)         :8080                 │ │
│  │  - Caddy reverse proxy          :8443                 │ │
│  │  - Prometheus Node Exporter     :9100                 │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Liên hệ & Hỗ trợ

- Xem thêm: `docs-ai-system/` và `docs-devops/`
- File task: `docs-ai-system/99-appendix/HDTV_PHASE11_TASKS.md`
- Project state: `docs-ai-system/99-appendix/PROJECT_STATE.md`

---
**Chúc bạn demo thành công! 🎉**
