# Platform Topology — L1 System Design

> **Tầng L1: Toàn cảnh platform**
> **Audience:** CTO, DevOps, Solution Architect
> **Cập nhật:** 2026-06-13

---

## 2-Node Deployment Topology

```
┌─────────────────────────────────────────────────────────────────┐
│  NODE 1: Windows 11 + WSL2 / Vagrant VM (4 GB RAM)             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Docker Compose — 9 services                            │   │
│  │                                                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │   │
│  │  │  FE      │  │  API     │  │  Celery Worker       │  │   │
│  │  │  Vue 3   │  │  FastAPI │  │  (async AI tasks)    │  │   │
│  │  │  :3080   │  │  :8000   │  │                      │  │   │
│  │  └──────────┘  └──────────┘  └──────────────────────┘  │   │
│  │                    │                                     │   │
│  │  ┌─────────────────┼──────────────────────────────┐    │   │
│  │  │                 ▼                               │    │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │    │   │
│  │  │  │PostgreSQL│  │ Redis    │  │ ChromaDB    │  │    │   │
│  │  │  │  :5432   │  │  :6379   │  │  :8800      │  │    │   │
│  │  │  └──────────┘  └──────────┘  └─────────────┘  │    │   │
│  │  │  ┌──────────┐  ┌──────────┐                    │    │   │
│  │  │  │  MinIO   │  │Prometheus│                    │    │   │
│  │  │  │  :9000   │  │  :9090   │                    │    │   │
│  │  │  └──────────┘  └──────────┘                    │    │   │
│  │  └────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          │ (future — Ansible provisioned)
          ▼
┌─────────────────────────────────────────────────────────────────┐
│  NODE 2: Ubuntu Server Physical (4 GB RAM)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  llama.cpp server — local LLM                            │  │
│  │  model: gemma-4-8b-it (Q4 quantized, fits 4GB)          │  │
│  │  :8080 HTTP inference                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                           Cloud fallback
                                │
                    ┌───────────────────────┐
                    │  Google Gemini API    │
                    │  (LEGAL/OCR/CRITIC)   │
                    └───────────────────────┘
```

---

## 9 Docker Services

| Service | Image | Port | Role |
|---------|-------|------|------|
| `hdtv-fe` | node:20-alpine (Vite build) | 3080 | Vue 3 SPA |
| `hdtv-api` | python:3.12-slim (FastAPI) | 8000 | REST API + WebSocket |
| `hdtv-worker` | python:3.12-slim (Celery) | — | Background AI tasks |
| `hdtv-db` | postgres:16 | 5432 | Primary data store |
| `hdtv-redis` | redis:7 | 6379 | Task queue + WS pub/sub |
| `hdtv-chroma` | chromadb/chroma:latest | 8800 | Vector memory store |
| `hdtv-minio` | minio/minio:latest | 9000/9001 | PDF + file storage |
| `hdtv-prometheus` | prom/prometheus | 9090 | Metrics scraping |
| `hdtv-grafana` | grafana/grafana | 3000 | Metrics dashboard |

---

## Network & Data Flow

```
Browser
  │  HTTPS (Nginx proxy in prod)
  ▼
hdtv-fe :3080
  │  Axios REST calls → /api/v1/*
  │  WebSocket → /ws/{user_id}
  ▼
hdtv-api :8000 (FastAPI)
  │
  ├── PostgreSQL (SQLAlchemy async)
  │     Tables: users, dossiers, agent_memories, appraisals, alerts,
  │             notifications, workflow_diagrams, ai_audit_logs,
  │             ai_tools, tool_chains, risk_rules, agent_feedback
  │
  ├── Redis (aioredis)
  │     Keys: ws_channel:{user_id}   (pub/sub)
  │           celery_broker          (task queue)
  │
  ├── ChromaDB (httpx)
  │     Collections: hdtv_memories, hdtv_feedback_lessons
  │
  ├── MinIO (boto3 S3 compat)
  │     Bucket: hdtv-docs  (PDF upload + presigned URL)
  │
  └── LLM Router
        ├── Local llama.cpp :8080  (PLANNER, EXECUTOR, REFLECTOR, SUMMARY)
        └── Gemini API            (LEGAL, FINANCIAL, OCR, CRITIC, TOOL_MOCK)

hdtv-worker (Celery)
  │  Shares code với hdtv-api
  │  Runs: async appraisal tasks, memory consolidation
  └── Same DB/Redis/Chroma connections as API
```

---

## Startup Sequence

```
1. PostgreSQL healthy (pg_isready)
2. Redis ready (PING)
3. ChromaDB ready (GET /api/v1/heartbeat)
4. MinIO ready + bucket created
5. API: Alembic migrate (18 migrations) → startup
6. API: if HDTV_AUTO_SEED=true → python -m seeds.seed_all
7. Worker: connect + register tasks
8. FE: serve static (nginx / vite preview)
```

---

## Environment Variables (critical)

| Variable | Node 1 | Note |
|----------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://hdtv:hdtv@hdtv-db:5432/hdtv` | |
| `REDIS_URL` | `redis://hdtv-redis:6379/0` | |
| `CHROMA_HOST` | `hdtv-chroma` | |
| `MINIO_ENDPOINT` | `hdtv-minio:9000` | |
| `LLM_BASE_URL` | `http://192.168.x.x:8080` | Node 2 IP |
| `GEMINI_API_KEY` | secret | Fallback LLM |
| `JWT_SECRET` | secret | Auth tokens |
| `HDTV_AUTO_SEED` | `true` (dev) / `false` (prod) | One-time seed |

---

## Resource Budget (4 GB Node 1)

| Service | RAM | Disk |
|---------|-----|------|
| PostgreSQL | ~400 MB | ~500 MB (data) |
| Redis | ~50 MB | — |
| ChromaDB | ~200 MB | ~100 MB (vectors) |
| MinIO | ~150 MB | ~200 MB (PDFs) |
| API | ~250 MB | — |
| Worker | ~200 MB | — |
| FE | ~50 MB | — |
| Prometheus + Grafana | ~200 MB | — |
| **Total** | **~1.5 GB** | **~800 MB** |

Node 2 (LLM): gemma-4-8b-it Q4 = ~4.5 GB → fits in 4 GB với swap.
