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
Cron scheduler
    ↓
 backup-db.sh
    ↓
 Database dump + compression
    ↓
 Store in /opt/platform/data/backup (or configured backup location)
```

- **Frequency**
  - At least once per day.
- **Scope**
  - PostgreSQL database (full logical dump or physical backup as configured).
- **Location**
  - Stored on local disk and, optionally, synced to external storage (if configured).
- **Implementation**
  - Script example: `backup-db.sh` in `/opt/platform/scripts`.

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

- Periodically run **restore drills** in a controlled environment:
  - Measure time from “backup selection” to “service healthy again”.
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
