# Platform at a Glance

> **Audience:** CEO, CTO
> **Format:** 1 trang tổng quan — biểu đồ + số liệu chính

---

## Full System Diagram

```mermaid
graph TB
    subgraph "Client"
        USER["👤 End Users\n(Cán bộ, Lãnh đạo)"]
    end

    subgraph "Node 2: Alpine VM — Application Layer"
        TRAEFIK["🔀 Traefik\nEdge Router + TLS"]

        subgraph "HDTV AI Platform"
            FE["🖥️ Vue.js Frontend\nDashboard · Chat · Workflow · Admin"]
            API["⚡ FastAPI Backend\nAsync API + WebSocket"]
            WORKER["⚙️ Celery Worker\nAI Agent Execution"]
            BEAT["⏰ Celery Beat\nRAG Pipeline Scheduler"]
        end

        subgraph "Data Layer"
            PG[("🗄️ PostgreSQL\nBusiness Data")]
            REDIS[("⚡ Redis\nQueue + Cache")]
            CHROMA[("🔮 Chroma DB\nVector Memory")]
            MEILI[("🔍 Meilisearch\nFull-text Search")]
            MINIO[("📦 MinIO\nPDF Storage")]
        end

        subgraph "Observability"
            PROMETHEUS["📊 Prometheus"]
            GRAFANA["📈 Grafana"]
            LOKI["📋 Loki"]
            JAEGER["🔭 Jaeger"]
        end
    end

    subgraph "Node 1: Ubuntu — LLM Layer"
        CADDY["🔒 Caddy\nHTTPS Proxy"]
        LLAMA[("🤖 llama-server\nGemma 4 Local")]
    end

    subgraph "External (Pilot only)"
        GEMINI["☁️ Gemini Flash API\n⚠️ Sẽ bị loại bỏ\nở giai đoạn Enterprise"]
    end

    USER -->|HTTPS| TRAEFIK
    TRAEFIK --> FE
    TRAEFIK --> API
    TRAEFIK --> GRAFANA

    FE <-->|WebSocket| API
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
    WORKER -.->|OCR/Legal/Financial\nPilot only| GEMINI

    API --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    LOKI --> GRAFANA
    JAEGER --> GRAFANA
```

---

## Key Numbers

| Metric | Value |
|--------|-------|
| **Total RAM used** | ~2.45 GB (trên VM 6GB) |
| **API endpoints** | 40+ (tất cả verified) |
| **AI Agent level** | Level 4 (Plan→Execute→Reflect→Critic) |
| **Tool integrations** | 7 tools (ERP, Legal, OCR, DOffice, PMIS, Sandbox) |
| **LLM backends** | 2 (local Gemma 4 + Gemini Flash) |
| **Observability** | Prometheus + Grafana + Loki + Jaeger + 14 alerts |
| **Deploy time** | `vagrant up` → demo ready ~10 phút |
| **DB migrations** | 12 migrations (001→012), all applied |
| **FE views** | 14 views fully wired to API |
| **Test coverage** | test.sh (bash) + 13 pytest static cases |

---

## Tech Stack tóm tắt

```
Frontend:   Vue 3 + Pinia + Vite + Tailwind
Backend:    FastAPI (Python 3.12, async)
Workers:    Celery + Redis
Databases:  PostgreSQL + Redis + Chroma + Meilisearch + MinIO
LLM:        llama-server (Gemma 4) + Gemini Flash API
Infra:      Docker Compose + Traefik + Vagrant (VMware)
CI/CD:      GitHub Actions
Automation: Ansible (Ubuntu LLM node)
Monitoring: Prometheus + Grafana + Loki + Jaeger + Alertmanager
```
