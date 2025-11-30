# Nano DevOps Platform – Alpine Linux Infrastructure Setup Guide

**Mục tiêu**: Hướng dẫn chuẩn để dựng **VM Alpine Linux 6GB RAM** làm host cho Nano DevOps Platform,  
tuân thủ chiến lược trong:

- `docs-devops/00-overview/platform-master-strategy.md`
- `docs-devops/04-environment-and-infrastructure/runtime-environment.md`
- `docs-devops/04-environment-and-infrastructure/filesystem-layout.md`

> Đây là guide cho **con người**. AI **không tự ý** SSH vào host hoặc chạy lệnh ngoài GitOps – AI chỉ tạo script/doc, con người review và thực thi.

---

## 1. Kiến trúc hạ tầng mục tiêu

- **Host**: Windows + VMware (hoặc hypervisor tương đương).
- **Guest VM**:
  - OS: Alpine Linux (khuyến nghị 3.18+).
  - RAM: **6GB** (theo `runtime-environment.md`, có thể bật zram để tối ưu).
  - CPU: ≥ 2 vCPU.
  - Disk: ≥ 40GB.
  - Network: **bridged** (để CI/CD hoặc dev machine có thể truy cập).
- **Layout** trên VM:
  - Root path: `/opt/platform`
    - `/opt/platform/apps` – volumes cho app services.
    - `/opt/platform/data` – PostgreSQL, Redis, Prometheus, Loki, Grafana data.
    - `/opt/platform/monitoring` – (nếu cần) dữ liệu monitoring bổ sung.
    - `/opt/platform/scripts` – (nếu bạn muốn copy script runtime ra ngoài repo).

Tham chiếu:

- `docs-devops/04-environment-and-infrastructure/runtime-environment.md`
- `docs-devops/04-environment-and-infrastructure/filesystem-layout.md`

---

## 2. Chuẩn bị VM Alpine

1. Tạo VM mới trên VMware:
   - Mount ISO Alpine (x86_64).  
   - RAM: 6GB, CPU: ≥ 2 vCPU, Disk: 40–60GB, network: bridged.
2. Cài Alpine:
   - Theo wizard `setup-alpine`.
   - Chọn disk install (không chạy từ ISO/live).  
   - Chọn timezone, keyboard, user, v.v.
3. Sau khi reboot:

```sh
ssh <user>@<vm-ip>
uname -a
cat /etc/alpine-release
```

Đảm bảo SSH hoạt động và Alpine version ổn định (3.18+).

---

## 3. Cài đặt Docker, Git và công cụ cần thiết

Chạy với quyền root (hoặc `doas` / `sudo` nếu đã cấu hình):

```sh
apk update
apk add --no-cache \
  docker docker-cli docker-compose-plugin \
  git bash curl ca-certificates \
  htop \
  zram-init

rc-update add docker default
service docker start
```

Kiểm tra:

```sh
docker info
docker run --rm hello-world
```

---

## 4. Bật zram để tối ưu RAM

Theo `runtime-environment.md`, VM 6GB nên bật **zram** để có thêm headroom trong budget.

### 4.1 Sử dụng gói `zram-init` (nếu Alpine hỗ trợ)

Gói `zram-init` thường tạo config mặc định; để bật:

```sh
rc-update add zram-init boot
/etc/init.d/zram-init start
```

Kiểm tra:

```sh
swapon --show
free -h
```

Bạn nên thấy một swap device loại `zram`. Dung lượng mặc định thường khoảng 50% RAM; có thể tinh chỉnh tùy nhu cầu.

### 4.2 (Tuỳ chọn) Thiết lập zram thủ công

Nếu muốn kiểm soát chi tiết hơn (ví dụ swap 2–3GB) có thể tạo script local:

1. Tạo file `/etc/local.d/zram.start`:

```sh
cat >/etc/local.d/zram.start <<'EOF'
#!/bin/sh

modprobe zram || exit 0

# Kích thước zram: 3GB (điều chỉnh nếu cần)
echo $((3 * 1024 * 1024 * 1024)) > /sys/block/zram0/disksize

mkswap /dev/zram0
swapon /dev/zram0
EOF

chmod +x /etc/local.d/zram.start
rc-update add local default
/etc/local.d/zram.start
```

2. Kiểm tra:

```sh
swapon --show
free -h
```

> Lưu ý: không nên lạm dụng swap để “vượt” giới hạn 6GB – swap chỉ là **lưới an toàn**, không phải để giấu over‑allocation.

---

## 5. Tạo layout `/opt/platform` và clone project

Tạo các thư mục cần thiết:

```sh
mkdir -p /opt/platform/{apps,data,monitoring,ci,scripts}
chown -R root:root /opt/platform
chmod 755 /opt/platform
```

Clone repo (vào home user hoặc thư mục riêng, ví dụ `/opt/platform/src`):

```sh
mkdir -p /opt/platform/src
cd /opt/platform/src
git clone <REPO_URL> nano-project-devops
cd nano-project-devops
```

Khi chạy Docker Compose, volumes trong `project_devops/platform/docker-compose.yml` sẽ map tới `/opt/platform/data/...` như đã cấu hình.

---

## 6. Khởi động platform trên Alpine

Từ thư mục repo:

```sh
cd /opt/platform/src/nano-project-devops/project_devops
docker compose up -d
```

Kiểm tra:

```sh
docker compose ps
```

Xem monitoring:

- Grafana: `http://<vm-ip>:3000` hoặc `http://grafana.localhost` (qua Traefik nếu dùng hosts).  
- Prometheus: `http://<vm-ip>:9090`.  
- Loki: `http://<vm-ip>:3100`.

Thực hiện onboarding/validation đầy đủ theo:  
`docs-devops/00-overview/platform-onboarding-and-validation.md`.

---

## 7. Tuning kernel & hệ thống cơ bản (tuỳ chọn, nâng cao)

Chỉ thực hiện nếu bạn hiểu rõ tác động:

- **sysctl** (ví dụ `/etc/sysctl.d/99-platform.conf`):

```conf
vm.swappiness = 10
vm.vfs_cache_pressure = 100
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 10240 65535
```

Áp dụng:

```sh
sysctl -p /etc/sysctl.d/99-platform.conf
```

- **limit open files / processes** nếu workload yêu cầu (sử dụng `/etc/security/limits.conf` tương đương Alpine).

Nhớ:

- Mọi thay đổi nên được **document lại** trong repo (ví dụ file này, hoặc một ADR),  
  tránh “snowflake server” khó tái hiện.

---

## 8. Đo lại resource usage để xác nhận 6GB đủ

Sau khi platform chạy ổn định trên VM Alpine:

1. Mở Grafana → Infrastructure Health dashboard:
   - Kiểm tra tổng RAM dùng (host + containers).  
   - Kiểm tra usage từng container (service nào “phình” ra khỏi budget).
2. Dùng `docker stats` để kiểm tra nhanh:

```sh
docker stats
```

3. Đảm bảo rằng:
   - Idle usage không vượt ~70–75% RAM.  
   - Dư headroom ≥ ~800MB ngay cả khi có CI burst (theo `runtime-environment.md`).

Nếu vượt:

- Quay lại `resource-optimization.md` và docs về alert/resource optimization để điều chỉnh limits.  
- Hoặc giảm số service/feature trên platform đó.

---

## 9. Tự động hoá với Scripts

Để tái tạo nhanh nhiều VM, project đã cung cấp các script tự động hoá cho phần cấu hình Alpine:

### 9.1 Alpine Setup Scripts

Sau khi cài Alpine Linux, chạy các script setup:

```bash
cd project_devops/infra/scripts
chmod +x *.sh
sudo ./setup-alpine-complete.sh
```

Script này sẽ tự động:
- Cài Docker, Git, và các công cụ cần thiết
- Cấu hình zram
- Tạo filesystem layout `/opt/platform`
- Tùy chọn: tuning kernel parameters

Hoặc chạy từng script riêng lẻ:
- `setup-alpine-base.sh` - Cài Docker, Git, tools
- `setup-alpine-zram.sh` - Cấu hình zram
- `setup-alpine-filesystem.sh` - Tạo directory structure
- `setup-alpine-sysctl.sh` - Kernel tuning (optional)

Xem `project_devops/infra/scripts/README.md` để biết chi tiết.

### 9.2 Quy trình hoàn chỉnh

1. **Tạo và cài Alpine Linux VM** (sử dụng phương pháp của bạn - VMware, VirtualBox, etc.)

2. **Setup Alpine** (trên VM):
   ```bash
   cd project_devops/infra/scripts
   chmod +x *.sh
   sudo ./setup-alpine-complete.sh
   ```

3. **Clone repo và khởi động platform**:
   ```bash
   cd /opt/platform/src
   git clone <REPO_URL> nano-project-devops
   cd nano-project-devops/project_devops/platform
   docker compose up -d
   ```

### 9.3 Nguyên tắc

Bất kể công cụ nào, hãy đảm bảo:
- Hạ tầng vẫn **immutable + idempotent** (theo `project_devops/infra/README.md`).  
- Mọi thay đổi được version hoá trong Git.
- Scripts có thể chạy lại nhiều lần mà không gây lỗi (idempotent).

File này mô tả "golden path" để dựng host Alpine cho Nano DevOps Platform; nếu OS khác (Ubuntu, Debian, v.v.), hãy giữ nguyên **budget 6GB** và các nguyên tắc, chỉ thay câu lệnh cài đặt tương đương.

