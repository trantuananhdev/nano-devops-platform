# Nano DevOps Platform - Onboarding & Operational Validation Guide

**Last Updated**: 2026-03-03  
**Scope**: End-to-end onboarding and validation for the Nano DevOps Platform on a single-node 6GB VM.

---

## 1. Who This Guide Is For

- DevOps engineers cần một **lộ trình từ zero → platform chạy hoàn chỉnh**.
- Backend developers muốn hiểu **cách deploy và validate services** trên platform.
- AI agents cần một **kịch bản thực thi rõ ràng** để kiểm tra CI/CD, deploy, monitoring, backup, security.

> Đây là guide thực thi, không thay thế các tài liệu kiến trúc. Đọc kèm: `platform-master-strategy.md`, `platform-summary.md`, `system-overview.md`.

---

## 2. Prerequisites & Environment Setup

### 2.1 Hardware & OS

- Single-node VM (hoặc máy local) với:
  - **RAM**: 6GB (hard constraint)
  - **CPU**: ≥ 2 vCPU
  - **Disk**: ≥ 40GB
- OS: Linux (khuyến nghị Ubuntu Server 22.04) hoặc môi trường tương đương.

### 2.2 Required Tools

Trên node chạy platform:

- `git`
- `docker` + `docker compose` (v2)
- Quyền chạy shell scripts (`bash`).

Trên máy dev (hoặc cùng node):

- Truy cập repo `nano-project-devops`.
- Truy cập GitHub (đã cấu hình CI/CD workflow).

### 2.3 Clone & Layout

```bash
git clone <REPO_URL> nano-project-devops
cd nano-project-devops
ls
```

Các thư mục chính:

- `project_devops/apps/` – application services (health-api, data-api, aggregator-api, user-api)
- `project_devops/platform/` – platform-level configs
- `project_devops/monitoring/` – monitoring stack (Prometheus, Grafana, Loki, exporters, alerts)
- `project_devops/scripts/` – deploy, rollback, backup, helper scripts
- `docs-devops/` – platform documentation (overview, architecture, runbooks, etc.)

---

## 3. Bring-Up: Start the Full Platform Locally

Mục tiêu: chạy toàn bộ stack (reverse proxy, DB, cache, monitoring, services) trên single node.

1. Đảm bảo Docker daemon đang chạy.
2. Từ thư mục root repo:

```bash
cd project_devops
docker compose up -d
```

3. Kiểm tra container:

```bash
docker compose ps
```

Kỳ vọng:

- Traefik, PostgreSQL, Redis chạy.
- Monitoring stack (Prometheus, Grafana, Loki, exporters) chạy.
- Application services (health-api, data-api, aggregator-api, user-api) running.

Nếu có lỗi:

- Xem runbook `docs-devops/10-runbook/troubleshooting.md`.
- Kiểm tra `project_devops/monitoring/*.yml` nếu lỗi liên quan monitoring.

---

## 4. CI/CD & Deployment Flow Validation

Mục tiêu: chứng minh pipeline từ Git → CI → Registry → CD → Runtime hoạt động đúng.

### 4.1 Trigger CI Pipeline

1. Thực hiện một thay đổi nhỏ (ví dụ update README của một service).
2. Commit & push lên branch chính sách (trunk-based hoặc feature branch đã định).
3. Quan sát GitHub Actions workflow:
   - Lint → Build → Test → Package → Security.

Tham chiếu:

- `docs-devops/05-ci-cd/ci-architecture.md`
- `docs-devops/05-ci-cd/pipeline-validation.md`

### 4.2 Deploy Script Validation

Deployment sử dụng GitOps + scripts:

- `project_devops/scripts/deploy.sh`
- `project_devops/scripts/rollback.sh`

Thực hiện:

```bash
cd project_devops/scripts
./deploy.sh <service-or-stack>
```

Kiểm tra:

- Script thực hiện pre-deployment validation (disk space, Docker connectivity).
- Trạng thái deploy và previous tag được ghi vào:
  - `.deployment-state`
  - `.deployment-history`

Rollback test:

```bash
./rollback.sh <service-or-stack>
```

Xác nhận:

- Rollback dùng previous tag từ `.deployment-state`.
- Lịch sử được cập nhật trong `.deployment-history`.

Tham chiếu chi tiết:  
`docs-devops/06-deployment-strategy/deployment-runbook.md`

---

## 5. Service-Level Validation (Smoke Tests)

Mục tiêu: xác nhận 4 services chạy đúng và patterns hoạt động.

### 5.1 health-api

- Endpoint: `/health`, `/metrics`.
- Smoke test: xem script/README tương ứng trong `project_devops/apps/health-api/`.
- Kỳ vọng:
  - `/health` trả về trạng thái OK.
  - `/metrics` expose Prometheus metrics.

### 5.2 data-api (PostgreSQL Integration)

- Kiểm tra:
  - Service kết nối PostgreSQL thành công.
  - Các operations cơ bản (CRUD hoặc data flow được mô tả trong README).
- Tham chiếu:
  - `docs-devops/02-system-architecture/business-logic-patterns.md`
  - README trong `project_devops/apps/data-api/`.

### 5.3 aggregator-api (Service-to-Service Communication)

- Mục tiêu: xác nhận gọi `health-api` và `data-api` qua HTTP/REST bằng Docker service names.
- Tham chiếu:
  - `docs-devops/02-system-architecture/service-communication-patterns.md`
  - README trong `project_devops/apps/aggregator-api/`.

### 5.4 user-api (Business Logic)

- Mục tiêu: validate business rules:
  - Đăng ký user (validation username/email/password).
  - Uniqueness constraints, error handling.
- Tham chiếu:
  - `docs-devops/02-system-architecture/business-logic-patterns.md`
  - README trong `project_devops/apps/user-api/`.

---

## 6. Observability Validation

Mục tiêu: chứng minh monitoring stack phản ánh đúng trạng thái platform.

### 6.1 Metrics & Dashboards

1. Truy cập Grafana (URL cấu hình trong docs / Traefik).
2. Kiểm tra:
   - **Platform Overview dashboard**
   - **Service-specific dashboards** cho 4 services
   - **Infrastructure Health dashboard**
3. Gây tải nhẹ (gọi các API) và quan sát:
   - Request rate, latency, error rate.
   - CPU, memory, disk usage.

Docs liên quan:

- `docs-devops/07-observability/monitoring-architecture.md`
- `docs-devops/07-observability/alert-tuning.md`

### 6.2 Alerts

- Xác nhận các alert rules tồn tại trong cấu hình Prometheus/Alertmanager.
- Mô phỏng:
  - Tăng load hoặc giảm resource (nếu an toàn) để xem alert kích hoạt.
- Xem hướng dẫn:
  - `docs-devops/07-observability/alert-tuning.md`
  - `docs-devops/07-observability/sli-slo-sla.md`

### 6.3 Logging

- Truy cập Loki thông qua Grafana:
  - Xem logs của từng service.
  - Filter theo label (service, level, v.v.).

---

## 7. Backup & Disaster Recovery Validation

Mục tiêu: đảm bảo backup automation hoạt động và restore được test.

### 7.1 Backup Scripts

Trong `project_devops/scripts/`:

- `backup-postgres.sh`
- `backup-redis.sh`
- `backup-all.sh`

Thực hiện:

```bash
cd project_devops/scripts
./backup-all.sh
```

Kỳ vọng:

- Backups được tạo vào thư mục được cấu hình.
- Retention policy (mặc định ~7 ngày) hoạt động (xem docs).

Docs:

- `docs-devops/09-disaster-recovery/backup-restore-strategy.md`
- `docs-devops/10-runbook/backup-restore.md`

### 7.2 Restore Drill

- (Trong môi trường test) mô phỏng:
  - Xoá một phần dữ liệu hoặc dùng instance mới.
  - Thực hiện restore PostgreSQL & Redis theo runbook.

Mục tiêu:

- Xác nhận RTO/RPO mục tiêu khả thi (RTO < 1h, RPO < 24h như strategy).

---

## 8. Security Baseline Validation

Mục tiêu: kiểm tra các practice chính chứ không phải pentest toàn diện.

Checklist:

- Containers:
  - Chạy với non-root (theo docs).
  - Chỉ mở ports cần thiết.
- Secrets:
  - Không hard-code trong code.
  - Được truyền qua env/config theo docs.
- CI:
  - CodeQL, Semgrep, OWASP, Gitleaks chạy trong pipeline.

Docs:

- `docs-devops/08-security/security-baseline.md`
- `docs-devops/08-security/security-best-practices.md`
- `docs-devops/08-security/secrets-management.md`
- `docs-devops/08-security/network-policies.md`

---

## 9. Runbooks & Day‑2 Operations

Sau khi platform chạy ổn định, sử dụng các runbook:

- `docs-devops/10-runbook/backup-restore.md`
- `docs-devops/10-runbook/maintenance.md`
- `docs-devops/10-runbook/troubleshooting.md`
- `docs-devops/10-runbook/service-management.md`

Đảm bảo:

- Team có thể:
  - Deploy phiên bản mới.
  - Rollback khi lỗi.
  - Backup & restore.
  - Theo dõi và xử lý alerts.

---

## 10. Day‑1 Onboarding Checklist

Một dev/DevOps mới được coi là **onboarded** khi:

- [ ] Đọc `platform-summary.md` và `system-overview.md`.
- [ ] Hiểu constraint 6GB single-node và GitOps principles.
- [ ] Chạy được full stack bằng `docker compose up -d` trong `project_devops/`.
- [ ] Trigger được CI pipeline cho 1 service.
- [ ] Dùng `deploy.sh` để deploy một thay đổi nhỏ.
- [ ] Dùng `rollback.sh` để rollback về version trước.
- [ ] Truy cập Grafana, tìm được dashboards chính và đọc metrics cơ bản.
- [ ] Xem logs qua Loki/Grafana.
- [ ] Chạy `backup-all.sh` và xác nhận file backup được tạo.
- [ ] Đọc qua các runbook chính và hiểu flow backup/restore, maintenance, troubleshooting.

Khi tất cả checklist trên được tick, Nano DevOps Platform được coi là:

- **Đã sẵn sàng cho sử dụng thực tế** trên single-node.
- **Đủ tài liệu** để AI agent và engineer mới có thể vận hành.

---

## 11. Liên Kết Tài Liệu Chính

- Tổng quan & kiến trúc:
  - `docs-devops/00-overview/system-overview.md`
  - `docs-devops/00-overview/platform-master-strategy.md`
  - `docs-devops/00-overview/platform-summary.md`
- Kiến trúc chi tiết:
  - `docs-devops/02-system-architecture/high-level-architecture.md`
  - `docs-devops/02-system-architecture/logical-architecture.md`
- CI/CD:
  - `docs-devops/05-ci-cd/ci-architecture.md`
  - `docs-devops/05-ci-cd/gitops-architecture.md`
- Observability:
  - `docs-devops/07-observability/monitoring-architecture.md`
  - `docs-devops/07-observability/alert-tuning.md`
- Security:
  - `docs-devops/08-security/security-baseline.md`
  - `docs-devops/08-security/security-best-practices.md`

