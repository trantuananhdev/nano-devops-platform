# SLI / SLO / SLA

This document defines basic Service Level Indicators (SLIs) and Service Level Objectives (SLOs) for the Nano DevOps Platform, consistent with the **observability-first** principle.

---

## 1. Core SLIs

- **Platform availability**
  - SLI: Percentage of successful HTTP requests (2xx/3xx) at the edge (Traefik).
  - SLO: **99%** over a rolling 30-day period.
- **Deployment success rate**
  - SLI: Ratio of successful deployments to total deployments over a period.
  - SLO: **> 95%** successful deployments per 30 days.
- **Service latency**
  - SLI: P95 response time for key APIs.
  - SLO: P95 < 500ms for normal load for critical endpoints.
- **Error rate**
  - SLI: Percentage of 5xx responses for key services.
  - SLO: Error rate < 1% for normal operation.

---

## 2. Alerting Guidelines

Alerts should fire when SLOs are at risk, not for every minor fluctuation.

- **Availability / Error rate**
  - Trigger an alert if:
    - Error rate > 5% for 5 minutes, or
    - Projected SLO burn rate indicates a violation within 1 day.
- **Latency**
  - Trigger an alert if:
    - P95 latency > 1s for 10 minutes on critical endpoints.
- **Deployment failures**
  - Alert when:
    - A deployment fails and rollback is triggered,
    - Deployment success rate drops below the objective over a rolling window.

These alerts integrate with `incident-response.md`, which describes how to diagnose and remediate issues using scripts and rollback mechanisms.

---

## 3. Text Diagram: SLO Flow

```text
Traffic ─► Metrics (Prometheus)
             │
             ▼
         SLI calculations
             │
             ▼
      Compare to SLO targets
             │
             ├─► Within bounds  ─► Dashboards only
             │
             └─► Breach / at risk ─► Alerts ─► Incident Response
```
