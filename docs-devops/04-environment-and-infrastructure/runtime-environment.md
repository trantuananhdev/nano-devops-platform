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

Reverse proxy: 200MB
CI runner: 1GB (burst)
Application: 1.5GB
Database: 1.5GB
Monitoring stack: 1GB
Buffer: 800MB

### Text Diagram: Resource Allocation

```text
6GB Total RAM

┌───────────────────────────────────────────┐
│ Reverse proxy        ≈ 200MB             │
├───────────────────────────────────────────┤
│ CI runner (burst)    ≈ 1GB               │
├───────────────────────────────────────────┤
│ Application services ≈ 1.5GB             │
├───────────────────────────────────────────┤
│ PostgreSQL DB        ≈ 1.5GB             │
├───────────────────────────────────────────┤
│ Monitoring stack     ≈ 1GB               │
├───────────────────────────────────────────┤
│ Buffer (headroom)    ≈ 800MB             │
└───────────────────────────────────────────┘
```

### Per-Service Considerations

- New always-on services should target **tens of MB**, not hundreds.
- Background/batch jobs should:
  - Run for limited durations,
  - Release memory after completion.
- If projected usage would exceed these budgets, the change must be redesigned or explicitly approved as a constraint change.