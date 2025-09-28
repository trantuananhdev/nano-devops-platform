# Data Flow

This document describes the main flows through the platform: CI, runtime traffic, and monitoring.

---

## CI Flow

```text
Developer / AI
      │
      ▼
     Git (push)
      │
      ▼
  CI Pipeline
      │
      ▼
 Build container image
      │
      ▼
  Push artifact (image registry)
      │
      ▼
   CD deploys new version
```

For more detail, see `ci-architecture.md` and `gitops-architecture.md`.

---

## Runtime Flow

```text
Client Request
      │
      ▼
 [Reverse Proxy]
      │
      ▼
 [Application Service]
      │
      ▼
 [PostgreSQL DB]
      │
      ▼
   Response
```

---

## Monitoring Flow

```text
Services
   ├─► Metrics ─► Prometheus ─► Dashboards (Grafana) ─► Alerts
   └─► Logs    ─► Loki       ─► Logs UI (Grafana)
```

These flows ensure that code changes, runtime behaviour, and observability remain consistent with the platform strategy.
