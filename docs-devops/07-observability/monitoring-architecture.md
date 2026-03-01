# Monitoring Architecture

This document describes how metrics, logs, and alerts are implemented for the Nano DevOps Platform.

---

## 1. Components

- **Metrics**
  - Prometheus
- **Visualization**
  - Grafana
- **Logs**
  - Loki
- **Alerting**
  - Prometheus alert rules and/or Grafana alerting
 - **Traces (future-ready)**
   - Lightweight tracing or span export can be added for critical flows when resources allow

All application and platform services must integrate with this stack.

---

## 2. Data Flows (Text Diagram)

```text
Metrics Flow:

 [Services] ──► [Prometheus] ──► [Grafana Dashboards] ──► [Alerts]

Logging Flow:

 [Services] ──► [Loki] ──► [Grafana Log Explorer]

Resource Monitoring:

 [Node / Docker] ──► [Prometheus node/container exporters] ──► [Grafana]
```

---

## 3. What We Monitor

- **Platform health**
  - Service up/down status (Traefik, app services, PostgreSQL, monitoring stack itself).
  - Node-level metrics: CPU, memory, disk usage.
- **Application health**
  - Request rate, error rate, latency.
  - Business-specific metrics where defined.
- **Deployment health**
  - Deployment success/failure counts.
  - Rollback events.

Alerts should be defined for, at minimum:

- Service down (critical services),
- High CPU (sustained),
- High memory (sustained),
- Disk nearly full,
- SLO/SLA breaches (see `sli-slo-sla.md`).

---

## 4. Resource-Aware Observability

Given the 6GB RAM constraint:

- **Retention**
  - Keep metrics and logs only for as long as is useful for debugging and SLO tracking.
  - Use short to moderate retention windows and, if needed, sampling or label restrictions.
- **Scrape intervals**
  - Balance freshness with overhead (e.g. 15–30s for most services).
- **Dashboards**
  - Focus on a small set of **high-value** dashboards:
    - Platform overview,
    - Per-critical-service dashboard,
    - Resource (CPU/RAM/disk) dashboard.

If resource pressure arises, prefer to **tune retention and scrape settings** before adding new heavy observability components.

Even though `platform-laws` yêu cầu **logs, metrics, traces**, bản Nano này ưu tiên logs + metrics để phù hợp constraint 6GB RAM; traces được coi là tùy chọn, tập trung trước cho các luồng thực sự quan trọng nếu được bật.
