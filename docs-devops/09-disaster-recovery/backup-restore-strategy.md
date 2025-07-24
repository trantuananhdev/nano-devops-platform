# Backup & Restore Strategy

This document describes how the platform performs backups and restores in a way that is **automated**, **script-driven**, and aligned with the single-node resource constraints.

---

## 1. Objectives

- **RTO** (Recovery Time Objective): < 1 hour  
- **RPO** (Recovery Point Objective): < 24 hours

These targets apply to the primary PostgreSQL database and critical application data.

---

## 2. Backup Process

Backups are performed automatically via scripts scheduled on the VM.

```text
Cron scheduler (daily at 2 AM)
    ↓
 backup-all.sh (orchestration)
    ↓
 ├─► backup-postgres.sh ──► PostgreSQL dump + compression
 └─► backup-redis.sh ──► Redis RDB snapshot + compression
    ↓
 Store in /opt/platform/data/backup
```

- **Frequency**
  - At least once per day (default: 2 AM via cron).
- **Scope**
  - PostgreSQL database: Full logical dump using `pg_dump`
  - Redis data: RDB snapshot or AOF file copy
- **Location**
  - Stored on local disk: `/opt/platform/data/backup`
  - Optionally synced to external storage (if configured).
- **Implementation**
  - Scripts: `backup-postgres.sh`, `backup-redis.sh`, `backup-all.sh` in `/opt/platform/scripts`
  - See `backup-automation.md` for detailed documentation

**Backup Format**:
- PostgreSQL: `postgres_YYYYMMDD_HHMMSS.sql.gz` (compressed SQL dump)
- Redis: `redis_YYYYMMDD_HHMMSS.rdb.gz` (compressed RDB/AOF file)

**Retention Policy**:
- Default: 7 days
- Configurable via `RETENTION_DAYS` environment variable
- Old backups automatically cleaned up

Backups must be lightweight enough to fit within the storage and memory constraints of the single-node environment.

---

## 3. Restore Process

Restores are performed by **running a restore script**; no manual ad-hoc SQL is required for standard scenarios.

```text
Select backup snapshot
    ↓
 stop-apps.sh (optional: stop or drain traffic)
    ↓
 restore-db.sh <backup-id>
    ↓
 start-apps.sh (or deploy scripts)
    ↓
 Verify application & data
```

- **Script usage**
  - `restore-db.sh <backup-id>`:
    - Stops or isolates the database as needed.
    - Restores the selected backup.
    - Logs progress and results.
- **Post-restore validation**
  - Verify:
    - Applications can connect to the DB,
    - Critical workflows function correctly,
    - Monitoring shows normal behaviour.

Any change in restore procedures must be reflected in this document and in the scripts under `/opt/platform/scripts`.

---

## 4. Testing and Verification

To ensure RTO and RPO targets remain realistic:

- Periodically run **restore drills** in a controlled environment using the DR drill playbook:
  - See `docs-devops/09-disaster-recovery/drill-playbook.md` for detailed scenarios and procedures.
  - Measure time from “backup selection” to “service healthy again” (RTO).
  - Check that data aligns with expected point-in-time (RPO).
- Document test results and adjust:
  - Backup frequency,
  - Script implementation,
  - Storage allocation,
as needed.

---

## 5. Text Diagram: Backup & Restore Flows

```text
Backup Flow:

   [Cron] ──► [backup-db.sh] ──► [Compressed backup files]
                                      │
                                      ▼
                           [Local / External Storage]

Restore Flow:

  [Operator]
      │
      ▼
 [Choose backup]
      │
      ▼
 [restore-db.sh] ──► [PostgreSQL restored]
      │
      ▼
 [Apps (re)started via deploy scripts]
```
