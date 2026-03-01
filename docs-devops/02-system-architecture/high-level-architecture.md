# High Level Architecture

This document provides a high-level view of the Nano DevOps Platform, showing how traffic, CI/CD, and observability components interact.

---

## 1. Runtime Request Flow

```text
Internet User
     │
     ▼
 [Reverse Proxy (Traefik)]
     │
     ▼
 [Application Services]
     │
     ▼
 [Database (PostgreSQL)]
```

All external traffic enters through the reverse proxy, which routes requests to application services that use a shared PostgreSQL database.

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
 [CD Layer]
     │
     ▼
 [Runtime (Docker on single-node VM)]
```

For details, see `ci-architecture.md`, `cd-strategy.md`, and `gitops-architecture.md`.

---

## 3. Observability Flow

```text
Services
   ├─► Metrics ─► Prometheus ─► Grafana ─► Alerts
   └─► Logs    ─► Loki       ─► Grafana (logs)
```

Observability is mandatory for all platform components; see `monitoring-architecture.md` and `sli-slo-sla.md` for more information.
