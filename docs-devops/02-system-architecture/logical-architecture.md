# Logical Architecture

This document describes the logical layers of the Nano DevOps Platform.

---

## Layers

```text
         ┌───────────────────────────┐
         │       Edge Layer         │
         │   (Traefik reverse proxy)│
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │      Application Layer   │
         │     (Business services)  │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │        Data Layer        │
         │      (PostgreSQL DB)     │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │       Compute Layer      │
         │      (Docker runtime)    │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │        CI/CD Layer       │
         │   (Pipelines & scripts)  │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │    Observability Layer   │
         │ (Prometheus / Grafana /  │
         │          Loki)           │
         └──────────────────────────┘
```

### Edge Layer
Traefik reverse proxy.

### Compute Layer
Docker runtime on a single-node VM.

### Application Layer
Business services (stateless where possible).

### Data Layer
PostgreSQL as the main persistent data store.

### CI/CD Layer
Pipeline automation and deployment scripts that implement GitOps.

### Observability Layer
Metrics, logs, and alerting integrated with all other layers.
