# 1. Mission

Xây dựng một self-hosted DevOps platform chạy trên single-node (6GB RAM) nhưng vẫn đạt tiêu chuẩn production về:

- CI/CD
- Deployment reliability
- Observability
- Disaster recovery
- Security baseline

System đóng vai trò:

- Production-like lab
- Platform engineering showcase
- AI-operable infrastructure

---

# 2. Core Philosophy

## 2.1 Constraint-Driven Design

Hard constraints:

- Single VM
- 6GB RAM
- No horizontal scaling

Mọi quyết định kỹ thuật phải tối ưu:

- Memory footprint
- Idle resource usage
- Operational simplicity

## 2.2 GitOps First

- Git là source of truth
- Không thay đổi trực tiếp trên runtime

## 2.3 Immutable Deployment

- Không patch container đang chạy
- Mọi thay đổi = build version mới

## 2.4 Observability First

System không có monitoring = system không tồn tại.

## 2.5 Automation First

Manual operation phải:

- script hóa
- hoặc pipeline hóa

---

# 3. Platform Goals

## 3.1 Technical Goals

- Zero-downtime deployment
- Rollback < 1 minute
- Fully containerized runtime
- Reproducible environment
- Fast disaster recovery

## 3.2 Resource Goals

Total RAM: 6GB

Phân bổ:

- Reverse proxy
- CI runner (burst)
- Application
- Database
- Monitoring
- Buffer

## 3.3 Operational Goals

- Onboard dev mới < 1 ngày
- AI có thể đọc docs và generate service đúng chuẩn
- Debug trong < 15 phút

---

# 4. Non-Goals

System này KHÔNG nhằm:

- Build HA cluster
- Multi-region deployment
- Cloud managed services

---

# 5. Architecture Principles

## 5.1 Single-node optimized

Không dùng:

- Kubernetes
- Service mesh
- Heavy sidecar

## 5.2 Stateless application layer

State nằm ở:

- Database
- Volume

## 5.3 Externalized configuration

Config tách khỏi image.

## 5.4 Health-check driven deployment

Chỉ switch traffic khi service healthy.

---

# 6. Logical Architecture

Platform gồm các layer:

1. Edge Layer
2. Compute Layer
3. Application Layer
4. Data Layer
5. CI/CD Layer
6. Observability Layer

---

# 7. CI/CD Strategy

Pipeline phải:

- Declarative
- Reproducible
- Artifact-based

Flow:

Code → Build → Test → Package → Release → Deploy → Verify

Rollback:

- Redeploy previous artifact

---

# 8. Deployment Strategy

Pattern:

Rolling update with health check.

Goals:

- Zero downtime
- Fast rollback
- Minimal resource spike

---

# 9. Observability Strategy

## 9.1 Metrics

Phải monitor:

- CPU
- Memory
- Disk
- Container health
- Application latency

## 9.2 Logs

- Centralized
- Searchable

## 9.3 Alerts

Alert khi:

- Service down
- Resource saturation
- Deployment failure

---

# 10. Disaster Recovery Strategy

## 10.1 Backup

- Automated
- Versioned

## 10.2 Restore

Restore phải:

- Scriptable
- Tested

Targets:

- RTO < 1h
- RPO < 24h

---

# 11. Security Baseline

- Non-root container
- Secrets không hard-code
- Minimal exposed ports
- Internal network isolation

---

# 12. AI-Operable Platform

Docs phải đủ để AI:

Hiểu:

- System structure
- Deployment flow
- Service dependency

AI phải bị cấm:

- Thêm service vượt resource budget
- Sửa core runtime

---

# 13. Documentation Standards

Docs phải:

- Là source of truth
- Up-to-date với runtime
- Có diagram cho mọi flow quan trọng

---

# 14. Definition of Done (Platform Level)

Platform được coi là hoàn thiện khi:

- Deploy không downtime
- Rollback < 1 phút
- Monitoring đầy đủ
- Backup restore test thành công
- Dev mới onboard theo docs chạy được system
- AI generate service đúng chuẩn

---

# 15. Target Outcome

Platform thể hiện năng lực:

- DevOps Engineer (automation & CI/CD)
- Platform Engineer (system design)
- SRE mindset (reliability & observability)
- FinOps mindset (resource efficiency)