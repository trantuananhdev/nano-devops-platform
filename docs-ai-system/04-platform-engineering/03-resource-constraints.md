# Resource Constraints — 6GB RAM Budget

> **Audience:** CTO
> **Mục đích:** Tại sao constraint là discipline, không phải limitation.

---

## RAM Budget

| Service | Limit | Actual (idle) | Notes |
|---------|-------|---------------|-------|
| hdtv-postgres | 384 MB | ~200 MB | Primary DB |
| hdtv-redis | 128 MB | ~30 MB | Queue + cache |
| hdtv-api | 384 MB | ~150 MB | FastAPI async |
| hdtv-worker | 512 MB | ~200 MB | Celery + agent |
| hdtv-beat | 64 MB | ~50 MB | Scheduler |
| hdtv-chroma | 400 MB | ~300 MB | Vector DB |
| hdtv-minio | 256 MB | ~100 MB | Object store |
| hdtv-meilisearch | 256 MB | ~150 MB | Search |
| hdtv-frontend | 64 MB | ~30 MB | Nginx |
| **Total HDTV** | **~2.45 GB** | **~1.2 GB idle** | |
| Observability stack | ~1.5 GB | ~800 MB idle | Prometheus+Grafana+Loki |
| **Total** | **~4 GB** | **~2 GB idle** | Fits in 6GB VM |

---

## Constraints as Discipline

Thiết kế trong 6GB RAM buộc team:

| Buộc phải | Kết quả |
|-----------|---------|
| Mỗi service có memory limit rõ ràng | Không có service "bloat" theo thời gian |
| Không thể thêm service nặng tùy tiện | Mọi service đều có justification |
| Tối ưu code path | Không có N+1 queries ẩn |
| Share infra (1 PG cho tất cả app) | Không over-provision per-service DB |

**Hệ quả tốt:** Khi scale lên enterprise (32GB+ RAM), team đã biết cách thiết kế lean. Không phải refactor vì quá phụ thuộc tài nguyên.
