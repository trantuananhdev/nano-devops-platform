# HDTV AI Platform — Demo Runbook (Full Auto Reset)

## Tổng quan
Từ giờ, mọi thứ **tự động hoàn toàn**! Chỉ cần bật Ubuntu server rồi chạy `vagrant up` — hệ thống sẽ:
1. **Reset toàn bộ** môi trường cũ (xóa containers, volumes, data)
2. **Tự động bootstrap Ubuntu** bằng password (nếu cần)
3. **Deploy toàn bộ stack** (HDTV + LLM node)
4. **Mỗi lần vagrant up đều reset sạch sẽ**

---

## Chuẩn bị (one-time)

### Bước 1: Chuẩn bị Ubuntu Server (chỉ làm 1 lần)
Trên máy Ubuntu (máy chủ LLM), đảm bảo:
```bash
# 1. Đảm bảo root có password (nếu chưa)
sudo passwd root
# Nhập mật khẩu: A07180295e

# 2. Cho phép root login bằng password tạm thời
sudo nano /etc/ssh/sshd_config
# Đổi các dòng sau:
# PermitRootLogin yes
# PasswordAuthentication yes

# 3. Khởi động lại sshd
sudo systemctl restart sshd

# 4. Cài python3 (nếu chưa)
sudo apt update && sudo apt install -y python3
```

### Bước 2: Chuẩn bị Windows host
1. Sao chép `.env.example` thành `.env`:
   ```powershell
   copy .env.example .env
   ```
2. Kiểm tra các biến trong `.env` (đặc biệt `ACER_HOST` và `ACER_ROOT_PASSWORD`)

---

## Chạy Demo (1 lệnh duy nhất!)
```powershell
set COPY_PROJECT_DEVOPS=1
set VM_MEM=4096
vagrant up
```

✨ Vagrant sẽ tự động làm tất cả!

---

## Sau khi chạy xong
### Truy cập giao diện
- **HDTV Frontend**: http://localhost:3080 hoặc https://hdtv.nano.platform
- **API Docs**: http://localhost:8000/docs
- **Grafana**: https://grafana.nano.platform

### Kiểm tra logs
Trong Alpine VM (`vagrant ssh`):
```bash
# Log deploy tự động
cat /var/log/hdtv-auto-deploy.log

# Log HDTV stack
cd /opt/platform/src/nano-project-devops
./cli.sh hdtv-logs
```

---

## Kịch bản demo 15 phút
### 1. CEO — Giá trị nghiệp vụ (3 phút)
1. Mở **Hòm thư Tờ trình** → chọn `124/TTr-B0295` (rủi ro cao)
2. Trong **Workspace** → bấm **Chạy lại thẩm định AI**
3. Quan sát checklist cập nhật real-time (WebSocket)
4. Mở **Cảnh báo** → thấy alert HIGH về ngân sách vượt ERP

**Thông điệp**: HĐTV thấy rủi ro ngay, không cần tra ERP thủ công.

### 2. CTO — Kiến trúc & audit (5 phút)
1. Mở **Quản trị Hệ thống** → tab **Tool Audit**
2. Chỉ từng dòng `ai_audit_logs`: tool name, JSON input/output, latency ms
3. Mở terminal: `curl -X POST http://localhost:8000/api/v1/dossiers/1/appraise` → `202 Accepted`
4. Giải thích: Celery worker + ReAct loop, LLM tách trên Ubuntu

**Thông điệp**: Mọi quyết định AI có audit trail; API async production-ready.

### 3. Architect — Topology 2 máy (4 phút)
```
Windows → Vagrant Alpine VM (App: FastAPI, Celery, PG, Chroma)
                ↓ Ansible SSH
         Ubuntu Server (llama-server Gemma 4 :8080)
                ↓ HTTP
         Gemini Flash (tool mocks ERP/DOffice/PMIS)
```
- Đổi model LLM không cần redeploy app
- Tool registry: mock → real API chỉ đổi adapter

### 4. DevOps — One-command path (3 phút)
```powershell
vagrant up
```
- Docker compose memory limits phù hợp 4GB VM
- Tự động reset hoàn toàn mỗi lần
- CI build 3 images → GHCR

---

## Troubleshooting
| Vấn đề | Cách xử lý |
|--------|------------|
| Ubuntu OOM khi load Gemma | Dùng Q4_K_M, ctx 4096; kiểm tra zram |
| VM RAM căng | `./cli.sh obs-down` rồi `./cli.sh hdtv-up` |
| LLM không phản hồi | Agent vẫn chạy với rule-based checks + Gemini fallback |
| FE không gọi API | Kiểm tra nginx proxy `/api` và `/ws` |
| Celery không chạy | `./cli.sh hdtv-logs worker` |
