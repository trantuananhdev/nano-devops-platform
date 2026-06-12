# Full Platform Diagram — Nano DevOps Platform

> **Audience:** CTO
> **Mục đích:** Bức tranh toàn bộ hệ thống — 2 nodes, tất cả services, tất cả flows.

---

## Tổng quan 2-Node Topology

```
┌──────────────────────────────────────────────────────────────────┐
│  NODE 1: Ubuntu (LLM Inference Server)                           │
│  Hardware: Laptop/Workstation với RAM ≥ 8GB                      │
│  Role: ONLY LLM — không chạy bất kỳ app service nào khác        │
│                                                                  │
│  ┌─────────────────────────────────────────┐                     │
│  │  llama-server (Gemma 4 via llama.cpp)   │  Port: 8081 (local) │
│  │  RAM: ~4-6GB                            │                     │
│  └─────────────────────────────────────────┘                     │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐  │
│  │  Caddy               │  │  Observability agents            │  │
│  │  :8080 → :8081 HTTPS │  │  node-exporter :9100             │  │
│  │  TLS termination      │  │  Promtail → Loki (Alpine)        │  │
│  └──────────────────────┘  └──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                          ↕ HTTPS :8080
                    (internal network only)
┌──────────────────────────────────────────────────────────────────┐
│  NODE 2: Alpine Linux VM (Application Server)                    │
│  Hardware: VMware Vagrant VM, 6GB RAM                            │
│  Role: Everything except LLM                                     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  EDGE LAYER                                             │     │
│  │  Traefik :80/:443 — Reverse proxy, TLS, service routing │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  APPLICATION LAYER                                         │  │
│  │  ┌──────────────┐  ┌───────────────────┐  ┌────────────┐  │  │
│  │  │  HDTV        │  │  Celery Worker    │  │  Celery    │  │  │
│  │  │  Frontend    │  │  (AI Agent runs   │  │  Beat      │  │  │
│  │  │  Vue.js/Nginx│  │   here, 512MB)    │  │  Scheduler │  │  │
│  │  │  64MB        │  │                   │  │  64MB      │  │  │
│  │  └──────────────┘  └───────────────────┘  └────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  FastAPI Backend (384MB)                             │  │  │
│  │  │  Async REST API + WebSocket                          │  │  │
│  │  │  Port: 8000                                          │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  DATA LAYER                                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │Postgres  │  │  Redis   │  │  Chroma  │  │Meilisearch│  │  │
│  │  │  384MB   │  │  128MB   │  │  400MB   │  │  256MB   │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  MinIO (Object Storage) — 256MB                      │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  OBSERVABILITY LAYER                                       │  │
│  │  Prometheus → Grafana    Loki (logs)    Jaeger (traces)    │  │
│  │  Alertmanager → alerts to users                            │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Full Mermaid Architecture Diagram

```mermaid
graph TB
    USER["👤 End Users"]
    TRAEFIK["🔀 Traefik\nEdge Router + TLS"]

    subgraph "Node 2: Alpine VM"
        FE["🖥️ HDTV Frontend\nVue.js + Nginx (64MB)"]
        API["⚡ FastAPI\n(384MB)"]
        WORKER["⚙️ Celery Worker\n(512MB)"]
        BEAT["⏰ Celery Beat\n(64MB)"]

        PG[("🗄️ PostgreSQL\n(384MB)")]
        REDIS[("⚡ Redis\n(128MB)")]
        CHROMA[("🔮 Chroma\n(400MB)")]
        MEILI[("🔍 Meilisearch\n(256MB)")]
        MINIO[("📦 MinIO\n(256MB)")]

        PROMETHEUS["📊 Prometheus"]
        GRAFANA["📈 Grafana"]
        LOKI["📋 Loki"]
        JAEGER["🔭 Jaeger"]
        ALERTMANAGER["🚨 Alertmanager"]
    end

    subgraph "Node 1: Ubuntu"
        CADDY["🔒 Caddy :8080"]
        LLAMA[("🤖 llama-server\nGemma 4")]
        NODE_EXP["node-exporter"]
        PROMTAIL["Promtail"]
    end

    GEMINI["☁️ Gemini Flash API\n(internet — pilot only)"]

    USER -->|HTTPS| TRAEFIK
    TRAEFIK --> FE
    TRAEFIK --> API
    TRAEFIK --> GRAFANA
    TRAEFIK --> PROMETHEUS

    FE <-->|WebSocket| API
    API -->|Enqueue task| REDIS
    REDIS -->|Dequeue| WORKER
    API --> PG & CHROMA & MEILI & MINIO
    WORKER --> PG & REDIS & CHROMA & MINIO
    WORKER -->|LLM calls| CADDY
    BEAT -->|Scheduled tasks| REDIS & CHROMA
    CADDY --> LLAMA
    WORKER -.->|OCR/pilot| GEMINI

    NODE_EXP -->|metrics| PROMETHEUS
    PROMTAIL -->|logs| LOKI
    API -->|metrics| PROMETHEUS
    PROMETHEUS --> GRAFANA & ALERTMANAGER
    LOKI --> GRAFANA
    JAEGER --> GRAFANA
    ALERTMANAGER -->|alerts| USER
```

---

## RAM Budget

| Service | Limit | Actual |
|---------|-------|--------|
| hdtv-postgres | 384 MB | ~200MB idle |
| hdtv-redis | 128 MB | ~30MB idle |
| hdtv-api | 384 MB | ~150MB idle |
| hdtv-worker | 512 MB | ~200MB idle |
| hdtv-beat | 64 MB | ~50MB idle |
| hdtv-chroma | 400 MB | ~300MB idle |
| hdtv-minio | 256 MB | ~100MB idle |
| hdtv-meilisearch | 256 MB | ~150MB idle |
| hdtv-frontend | 64 MB | ~30MB idle |
| **Total** | **~2.45 GB** | fits comfortably in 6GB VM |

---

## Tại sao tách LLM ra node riêng?

| Lý do | Giải thích |
|-------|-----------|
| **Resource isolation** | Gemma 4 cần 4-6GB RAM riêng. Chung VM sẽ không còn tài nguyên cho app. |
| **Swap model independently** | Thay model mới trên Ubuntu không ảnh hưởng app stack. |
| **Scale independently** | Node 1 scale theo GPU/RAM. Node 2 scale theo CPU/concurrency. |
| **Security boundary** | LLM node không có access vào database hoặc business data. |
| **Future air-gap** | Khi chuyển sang enterprise, LLM cluster có thể có firewall riêng. |
