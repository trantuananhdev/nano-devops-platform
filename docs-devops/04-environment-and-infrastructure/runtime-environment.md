# Runtime Environment

## Host Machine

Windows + VMware

## VM

Alpine Linux

## Resource Allocation

RAM: 6GB (zram enabled)

## Network Model

Bridged networking

## Storage Layout

/opt/platform

## Resource Budget

Total RAM: 6GB

Allocation Strategy:

Core Infra (Proxy, DB, Cache): 1.5GB
Application services (Odoo + APIs): 1GB
Monitoring stack (Observability): 1.5GB
OS & Kernel (Alpine + ZRAM): 1GB
Buffer (headroom): 1GB

### Text Diagram: Resource Allocation

```text
6GB Total RAM

┌───────────────────────────────────────────┐
│ OS & Kernel (Alpine + ZRAM) ≈ 1GB         │
├───────────────────────────────────────────┤
│ Core Infra (Postgres, Redis) ≈ 1.5GB      │
├───────────────────────────────────────────┤
│ Applications (Odoo + APIs)   ≈ 1GB        │
├───────────────────────────────────────────┤
│ Observability Stack          ≈ 1.5GB      │
├───────────────────────────────────────────┤
│ Buffer (headroom)            ≈ 1GB        │
└───────────────────────────────────────────┘
```

## Orchestration Model

The platform uses a **Modular Docker Compose** architecture to manage complexity and resource isolation.

### Composition Structure

Located in `project_devops/platform/composition/`:

1.  **`docker-compose.yml`**: Core infrastructure (Network, Security, DB, Cache).
2.  **`docker-compose.observability.yml`**: Full monitoring and logging stack.
3.  **`docker-compose.apps.yml`**: Odoo ERP and custom Python Microservices.
4.  **`docker-compose.override.yml`**: Local development overrides.

### Management via CLI

All services are managed through the unified `cli.sh` tool, which orchestrates multiple compose files automatically.

```bash
./cli.sh up      # Starts all modules
./cli.sh down    # Stops all modules
```

### Per-Service Considerations

- New always-on services should target **tens of MB**, not hundreds.
- Background/batch jobs should:
  - Run for limited durations,
  - Release memory after completion.
- If projected usage would exceed these budgets, the change must be redesigned or explicitly approved as a constraint change.

---

## Resource Optimization

Resources should be optimized based on actual usage patterns to ensure efficient resource utilization while respecting the 6GB RAM constraint.

### Resource Optimization Process

1. **Analyze Usage**: Collect metrics on actual resource usage (7-30 days)
2. **Identify Opportunities**: Find over-allocated or under-allocated services
3. **Optimize Limits**: Adjust resource limits based on actual usage patterns
4. **Validate Changes**: Monitor resource usage after optimization
5. **Document Changes**: Record limit adjustments and rationale

### Resource Optimization Best Practices

- **Base limits on data**: Use historical metrics (P95 usage + buffer)
- **Start conservative**: Begin with limits slightly above actual usage
- **Monitor continuously**: Track resource usage after optimization
- **Iterate**: Adjust based on results
- **Document**: Record all limit changes and rationale

### Resource Monitoring

Monitor resource usage via:
- **Grafana Dashboards**: Infrastructure Health dashboard shows total and per-service usage
- **Prometheus Metrics**: `container_memory_usage_bytes`, `container_spec_memory_limit_bytes`
- **Resource Alerts**: HighMemoryUsage, CriticalMemoryUsage, ServiceMemoryExhaustion

### Optimization Goals

- **Efficiency**: Use resources effectively without waste
- **Headroom**: Maintain buffer for spikes and growth
- **Performance**: Ensure services have adequate resources
- **Capacity**: Free up resources for new services

See `resource-optimization.md` for comprehensive resource optimization guide and procedures.