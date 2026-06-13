# Platform at a Glance

> **Audience:** CEO, CTO
> **Format:** 1 trang tổng quan — biểu đồ + số liệu chính
> **Cập nhật:** 2026-06-13

---

## Full System Diagram

```mermaid
graph TB
    subgraph "Client"
        USER["👤 End Users\n(Cán bộ, Lãnh đạo EVNHANOI)"]
    end

    subgraph "Node 2: Alpine VM — Application Layer"
        TRAEFIK["🔀 Traefik\nEdge Router + TLS"]

        subgraph "HDTV AI Platform"
            FE["🖥️ Vue.js Frontend\nDashboard · Workspace · Workflow · Admin · Chat"]
            API["⚡ FastAPI Backend\nAsync REST API + WebSocket"]
            WORKER["⚙️ Celery Worker\nAI Agent Execution (Async)"]
            BEAT["⏰ Celery Beat\nRAG Pipeline Scheduler (6h)"]
        end

        subgraph "Data Layer"
            PG[("🗄️ PostgreSQL\nBusiness Data + Migrations")]
            REDIS[("⚡ Redis\nQueue + Pub/Sub + Cache")]
            CHROMA[("🔮 Chroma DB\nVector Memory + RAG")]
            MEILI[("🔍 Meilisearch\nFull-text Search")]
            MINIO[("📦 MinIO\nPDF Storage")]
        end

        subgraph "Observability"
            PROMETHEUS["📊 Prometheus"]
            GRAFANA["📈 Grafana\n14 alert rules"]
            LOKI["📋 Loki"]
            JAEGER["🔭 Jaeger"]
        end
    end

    subgraph "Node 1: Ubuntu — LLM Layer"
        CADDY["🔒 Caddy\nHTTPS Proxy"]
        LLAMA[("🤖 llama-server\nLocal LLM")]
    end

    subgraph "Fallback (khi LLM node offline)"
        GEMINI["☁️ Gemini Flash API\n9 keys, circuit breaker rotation\n⚠️ Giai đoạn pilot — sẽ loại bỏ ở Enterprise"]
    end

    USER -->|HTTPS| TRAEFIK
    TRAEFIK --> FE
    TRAEFIK --> API
    TRAEFIK --> GRAFANA

    FE <-->|WebSocket real-time| API
    API --> WORKER
    API --> PG
    API --> REDIS
    API --> CHROMA
    API --> MEILI
    API --> MINIO

    WORKER --> PG
    WORKER --> REDIS
    WORKER --> CHROMA
    WORKER -->|HTTP| CADDY
    BEAT --> CHROMA
    BEAT --> REDIS

    CADDY --> LLAMA
    WORKER -.->|Circuit breaker fallback| GEMINI

    API --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    LOKI --> GRAFANA
    JAEGER --> GRAFANA
```

---

## Key Numbers

| Metric | Value | Ghi chú |
|--------|-------|---------|
| **Total RAM used** | ~2.45 GB (VM 6GB) | 50% headroom cho peak load |
| **API endpoints** | 40+ (tất cả verified) | REST + WebSocket |
| **AI Agent level** | Level 4 | Plan → Execute → Reflect → Critic |
| **Tool integrations** | 7 tools | ERP, Legal, OCR, DOffice, PMIS, Sandbox, Budget |
| **LLM backends** | 2 | Local llama-server + Gemini Flash fallback |
| **Observability** | 4 systems + 14 alerts | Prometheus + Grafana + Loki + Jaeger |
| **Deploy time** | ~5 phút | `COPY_PROJECT_DEVOPS=1 vagrant up` → fully automated |
| **DB migrations** | 18 (001→018, all applied) | Alembic, zero manual SQL |
| **FE views** | 14 views | Tất cả wired to real API |
| **Seed data** | Thật từ 4 tờ trình EVN | 8 users + 16 dossiers + BPMN + alerts |
| **Demo login** | admin@evnhanoi.vn | Password: EVN@2024! |

---

## Tech Stack

```
Frontend:    Vue 3 + Pinia + Vue Router + Vite
Backend:     FastAPI (Python 3.11, full async)
Workers:     Celery 5 + Redis pub/sub
Databases:   PostgreSQL 15 + Redis + Chroma + Meilisearch + MinIO
LLM:         llama-server (local, any GGUF model) + Gemini Flash fallback
AI Agent:    Multi-role ReAct: Planner / Executor / Reflector / Critic
Memory:      Short-term (PG) + Long-term (Chroma) + Feedback lessons
Infra:       Docker Compose + Nginx + Vagrant (VMware/VirtualBox)
CI/CD:       GitHub Actions → GHCR (immutable images)
Automation:  Ansible (Ubuntu LLM node)
Monitoring:  Prometheus + Grafana + Loki + Jaeger + Alertmanager
Security:    JWT auth + bcrypt + non-root containers + resource limits
```

---

## Workflow nghiệp vụ EVNHANOI (hồ sơ UAV mẫu)

```
Tờ trình 07/KT           198/TTr-EVNHANOI        Phiếu trình HĐTV
(Ban Kỹ thuật)    →      (TGĐ ký, trình HĐTV) → (Đỗ Tuấn Anh ký)
       │                        │                        │
       │              AI Thẩm định (30-60s)              │
       │         ┌──────────────────────────┐            │
       │         │ LegalGraphRAG      ✅    │            │
       │         │ TechnicalStandCheck ⚠️   │            │
       │         │ ProcurementCheck    ⚠️   │            │
       │         │ Critic → approved=True  │            │
       │         └──────────────────────────┘            │
       │                        │                        │
       └────────────────────────┴────────────────────────┘
                    2 kiến nghị hiệu chỉnh
          (khớp chính xác Báo cáo thẩm tra Ban TH thật)
```
