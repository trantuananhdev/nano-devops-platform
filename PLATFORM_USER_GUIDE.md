# Nano DevOps Platform – Hướng dẫn Vận hành & Sử dụng (User Guide)

**Mục tiêu**: Tài liệu này hướng dẫn cách sử dụng, quản lý và vận hành hệ thống Nano DevOps Platform dành cho Kỹ sư Vận hành và Quản trị viên.

---

## 1. Tổng quan Hệ thống (Mental Model)

Nano DevOps Platform là một nền tảng vận hành Microservices theo tiêu chuẩn Production-ready, được tối ưu hóa để chạy trên một máy chủ duy nhất (Single-node) với tài nguyên giới hạn (6GB RAM).

**Kiến trúc lõi:**
- **Runtime:** Docker Engine chạy trên nền Alpine Linux.
- **Network & Security:** Traefik làm Reverse Proxy & SSL; Socket Proxy bảo vệ Docker Engine.
- **Data:** PostgreSQL 16 & Redis 7.
- **Observability:** Prometheus, Grafana, Loki & Jaeger.

---

## 2. Bắt đầu nhanh (Quick Start)

### 2.1 Khởi tạo Hạ tầng
Sử dụng Vagrant để tự động hóa việc dựng máy ảo và cài đặt hạ tầng:
```bash
# Từ thư mục gốc dự án
vagrant up
```
*Lưu ý: Quá trình này mất khoảng 5-10 phút để cài đặt Docker, User và Security.*

### 2.2 Quản lý dịch vụ qua CLI
Sau khi máy ảo đã lên, hãy truy cập vào máy ảo và sử dụng công cụ `cli.sh` tại thư mục gốc:
```bash
vagrant ssh
./cli.sh up      # Khởi động toàn bộ dịch vụ (App + Monitoring)
./cli.sh ps      # Kiểm tra trạng thái các container
./cli.sh logs    # Xem log thời gian thực
```

---

## 3. Các địa chỉ truy cập quan trọng
Sau khi hệ thống khởi động thành công, bạn có thể truy cập các dịch vụ qua trình duyệt (đảm bảo file hosts đã trỏ về IP máy ảo):

- **Hệ thống ERP (Odoo):** `https://odoo.localhost`
- **Giám sát (Grafana):** `https://grafana.localhost` (User: admin / Pass: xem trong secrets)
- **Quản lý Metrics (Prometheus):** `https://prometheus.localhost`
- **Truy vết (Jaeger):** `https://jaeger.localhost`
- **Cửa ngõ (Traefik Dashboard):** `http://localhost:8080`

---

## 4. Quy trình Triển khai (CI/CD)

Hệ thống hỗ trợ triển khai theo phong cách GitOps thông qua script `deploy.sh`:
```bash
# Cú pháp
./cli.sh deploy <service_name> <tag>
```
**Cơ chế an toàn:**
1. Pull image mới từ Registry.
2. Chạy container mới.
3. Kiểm tra Health-check (30-60s).
4. Nếu thất bại -> Tự động Rollback về phiên bản trước đó.

---

## 5. Sao lưu & Khôi phục (Backup & DR)

Hệ thống sao lưu tự động được đặt trong `project_devops/platform/ops/backup/`.
- **Sao lưu ngay:** `./project_devops/platform/ops/backup/backup-all.sh`
- **Dữ liệu sao lưu:** Được lưu tại `/opt/platform/backups/`.
- **Chiến lược:** Retention 7 ngày, nén gzip để tiết kiệm đĩa.

---

## 6. Xử lý sự cố thường gặp (Troubleshooting)

1. **Dịch vụ không truy cập được:** Kiểm tra logs của Traefik và Socket Proxy.
2. **Tràn bộ nhớ (Out of Memory):** Kiểm tra Dashboard Grafana (Infrastructure Health) để xem container nào đang vượt giới hạn RAM.
3. **Lỗi kết nối Database:** Chạy `./cli.sh logs data-api` để kiểm tra thông tin đăng nhập Postgres.

---

## 7. Ghi chú cho Người quản trị (Admin Only)

Mọi thay đổi về kiến trúc hoặc cấu hình hạ tầng phải được thực hiện thông qua các file trong thư mục `project_devops/platform/`. Tuyệt đối không thay đổi trực tiếp (hot-fix) trên các container đang chạy để đảm bảo tính **Immutable Infrastructure**.

*(Tài liệu này được bảo mật và chỉ dành cho người quản trị hệ thống)*
