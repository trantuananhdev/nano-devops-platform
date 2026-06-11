# Infrastructure: 2-Node Production Topology

## Tổng quan

HDTV chạy trên 2 node riêng biệt để tách biệt LLM (heavy resource) khỏi application layer:

```
┌─────────────────────────────────┐
│  Node 1: Ubuntu (LLM Only)      │
│  • llama-server (Gemma 4)       │
│  • Caddy (reverse proxy)        │
│  • Node exporter, Promtail      │
└─────────────────────────────────┘
              ↕ HTTPS
┌─────────────────────────────────────────────────────────┐
│  Node 2: Alpine (Everything Else)                       │
│  • Docker Compose stack                                  │
│    ├─ Postgres (HDTV DB)                                │
│    ├─ Redis (Queue + Cache)                             │
│    ├─ Chroma (Vector DB)                                │
│    ├─ Meilisearch (Full-text Search)                    │
│    ├─ MinIO (Object Storage)                            │
│    ├─ FastAPI Backend                                   │
│    ├─ Celery Worker                                     │
│    ├─ Celery Beat (Scheduler)                           │
│    ├─ Frontend (React)                                  │
│  • Traefik (Edge Router)                                │
│  • Prometheus + Grafana + Loki + Jaeger                 │
└─────────────────────────────────────────────────────────┘
```

## Node 1: Ubuntu (LLM Server)
- **OS:** Ubuntu 22.04/24.04
- **Purpose:** Chỉ chạy LLM inference
- **Components:**
  - llama-server (Gemma 4 via Ollama or llama.cpp)
  - Caddy (auto HTTPS, reverse proxy to llama-server)
  - Promtail (send logs to Loki on Alpine node)
  - Node exporter (metrics to Prometheus on Alpine node)
- **Ansible Playbook:** `project_devops/apps/ansible-ubuntu/deploy-llm.yml`

## Node 2: Alpine (Application Server)
- **OS:** Alpine Linux (lightweight, secure)
- **Purpose:** Everything except LLM
- **Docker Compose File:** `project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml`
- **Traefik:** Edge router, auto HTTPS, service discovery
- **Observability:**
  - Prometheus (metrics)
  - Grafana (dashboards)
  - Loki (logs)
  - Jaeger (tracing - optional)

## Resource Constraints
Memory limits strictly enforced:
- Postgres: 384 MB
- Redis: 128 MB
- Chroma: 400 MB
- Meilisearch: 256 MB
- API: 384 MB
- Worker: 512 MB
- Beat: 64 MB
- Frontend: 64 MB

## Networking
- Node 1 ↔ Node 2: HTTPS (via Caddy/Treafik)
- Internal Docker network: `hdtv-net`
- Platform network: `platform-network` (external, connects to Prometheus)

## Deployment
- **Ansible:** `ansible-ubuntu` playbooks
- **Docker Compose:** `docker-compose.hdtv.yml`
- **CI/CD:** `.github/workflows/`
