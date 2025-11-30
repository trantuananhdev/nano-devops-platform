# High Level Architecture

This document provides a high-level view of the Nano DevOps Platform, showing how traffic, CI/CD, and observability components interact.

---

## 1. Runtime Request Flow

```text
Internet User
     │
     ▼
 [Edge Layer (Traefik)] <─── Modular Module: Core
     │
     ▼
 [Application Services] <─── Modular Module: Apps
     │
     ▼
 [Data Layer (DB/Cache)] <─── Modular Module: Core
```

All external traffic enters through the reverse proxy, which routes requests to application services that use a shared PostgreSQL database. The infrastructure is managed via **Modular Docker Compose** (Core, Observability, Apps).

---

## 2. CI/CD Flow

```text
Developer / AI
     │
     ▼
     Git
     │
     ▼
 [CI Pipeline]
     │
     ▼
 [Image Registry]
     │
     ▼
 [CD Layer (deploy.sh)]
     │
     ▼
 [Runtime (Modular Docker Compose)]
```

For details, see `ci-architecture.md`, `cd-strategy.md`, and `gitops-architecture.md`.

---

## 3. Observability Flow

```text
Services (Core/Apps)
   ├─► Metrics ─► [Observability Module (Prometheus)] ─► Grafana ─► Alerts
   └─► Logs    ─► [Observability Module (Loki)]       ─► Grafana (logs)
```

Observability is mandatory for all platform components; see `monitoring-architecture.md` and `sli-slo-sla.md` for more information.
