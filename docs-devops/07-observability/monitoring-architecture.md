# Monitoring Architecture

This document describes how metrics, logs, and alerts are implemented for the Nano DevOps Platform.

---

## 1. Components

- **Metrics**
  - Prometheus
  - cAdvisor (container resource metrics)
  - node_exporter (host/disk metrics)
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

 [Docker Containers] ──► [cAdvisor] ──► [Prometheus] ──► [Grafana Infrastructure Health Dashboard]
 [Host System] ──► [node_exporter] ──► [Prometheus] ──► [Grafana Infrastructure Health Dashboard]
```

---

## 3. What We Monitor

- **Platform health**
  - Service up/down status (Traefik, app services, PostgreSQL, monitoring stack itself).
  - Container-level metrics: CPU, memory usage per service (via cAdvisor).
  - Total platform resource utilization (memory, CPU).
- **Application health**
  - Request rate, error rate, latency.
  - Business-specific metrics where defined.
- **Deployment health**
  - Deployment success/failure counts.
  - Rollback events.
- **Resource monitoring**
  - Memory usage per container/service.
  - CPU usage per container/service.
  - Total memory and CPU utilization across platform.
  - Service resource exhaustion warnings.
  - Disk usage by mount point.
  - Total disk usage percentage and trends.

Alerts should be defined for, at minimum:

- Service down (critical services),
- High CPU (sustained) - >80% for 10 minutes,
- High memory (sustained) - >85% of 6GB limit for 5 minutes,
- Critical memory usage - >95% of 6GB limit for 2 minutes,
- Service memory exhaustion - >90% of service limit for 5 minutes,
- Disk nearly full - >85% for 5 minutes (warning),
- Disk critical - >95% for 2 minutes (critical),
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
    - Infrastructure Health (resource utilization),
    - Per-critical-service dashboard,
    - Resource (CPU/RAM) dashboard.

## 5. Resource Monitoring

### cAdvisor Integration

cAdvisor provides container-level resource metrics:
- **Memory usage**: Per-container memory consumption
- **CPU usage**: Per-container CPU utilization
- **Resource limits**: Container memory and CPU limits

### node_exporter Integration

node_exporter provides host-level metrics:
- **Disk usage**: Disk space usage by mount point
- **Disk I/O**: Disk read/write operations
- **Filesystem metrics**: Available, used, and total disk space
- **Network metrics**: Network interface statistics

### Infrastructure Health Dashboard

The Infrastructure Health dashboard provides:
- Total memory usage (GB and percentage of 6GB limit)
- Total CPU usage percentage
- Memory usage by service
- CPU usage by service
- Service health status overview
- Resource utilization trends
- Disk usage percentage and available space
- Disk usage by mount point
- Disk usage trends

### Resource Alerts

Resource-based alerts configured:
- **HighMemoryUsage**: Total memory >85% of 6GB for 5 minutes (warning)
- **CriticalMemoryUsage**: Total memory >95% of 6GB for 2 minutes (critical)
- **HighCPUUsage**: Total CPU >80% for 10 minutes (warning)
- **ServiceMemoryExhaustion**: Individual service >90% of its limit for 5 minutes (warning)
- **DiskNearlyFull**: Disk usage >85% for 5 minutes (warning)
- **DiskCritical**: Disk usage >95% for 2 minutes (critical)

These alerts help ensure the platform stays within the 6GB RAM constraint and identify resource pressure (memory, CPU, disk) before it becomes critical.

If resource pressure arises, prefer to **tune retention and scrape settings** before adding new heavy observability components.

Even though `platform-laws` yêu cầu **logs, metrics, traces**, bản Nano này ưu tiên logs + metrics để phù hợp constraint 6GB RAM; traces được coi là tùy chọn, tập trung trước cho các luồng thực sự quan trọng nếu được bật.

---

## 6. Alert Tuning

Alerts should be tuned based on actual usage patterns to ensure they are actionable and reduce alert fatigue.

### Alert Tuning Process

1. **Evaluate Current Alerts**: Review alert frequency, false positive rate, and actionability
2. **Analyze Usage Patterns**: Use historical metrics to identify normal operating ranges
3. **Adjust Thresholds**: Modify alert thresholds based on actual usage data
4. **Validate Changes**: Monitor alert effectiveness after tuning
5. **Document Changes**: Record threshold adjustments and rationale

### Alert Tuning Best Practices

- **Base thresholds on actual data**: Use 7-30 days of historical metrics
- **Start conservative**: Begin with thresholds slightly above normal operation
- **Iterate**: Adjust based on alert effectiveness
- **Document**: Record all threshold changes and rationale
- **Review regularly**: Schedule periodic alert reviews (monthly/quarterly)

### Alert Effectiveness Metrics

Track these metrics to evaluate alert effectiveness:
- Alert frequency (alerts per day/week)
- False positive rate (target: < 10%)
- Mean time to acknowledge (MTTA)
- Mean time to resolve (MTTR)
- Alert resolution rate (target: > 90%)

### Alert Noise Reduction

Strategies to reduce alert noise:
- **Threshold tuning**: Adjust thresholds to match actual usage patterns
- **Duration adjustment**: Increase duration to reduce transient alerts
- **Alert grouping**: Group related alerts to reduce volume
- **Severity levels**: Use appropriate severity to prioritize alerts
- **Alert routing**: Route alerts to appropriate channels

See `alert-tuning.md` for comprehensive alert tuning guide and procedures.