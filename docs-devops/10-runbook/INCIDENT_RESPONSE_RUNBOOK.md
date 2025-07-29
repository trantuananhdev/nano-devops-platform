# Incident Response Runbook: Odoo Performance Degradation / OOM

**Target MTTR (Mean Time To Recovery):** < 5 Minutes

## 🚨 Scenario
An Alertmanager notification triggers: `High Memory Usage` on Odoo service or `Odoo Container Restarting`.

## 🔍 Phase 1: Detection (Grafana)
1. Open **Grafana Dashboard: Infrastructure Health**.
2. Identify the culprit:
   - Check **RAM Usage per Container** panel.
   - If Odoo RAM is hitting the **600MB hard limit**, it's an OOM (Out Of Memory) event.
3. Check **Prometheus Logs (Loki)**: Filter for `job="odoo"` and look for `Memory limit exceeded`.

## 🛠 Phase 2: Debugging (CLI)
Access the control plane via SSH:
```bash
vagrant ssh
```
Check the actual container status:
```bash
./cli.sh ps
# Look for 'platform-odoo' status. If 'restarting', check logs:
./cli.sh logs odoo --tail=100
```

## 🚑 Phase 3: Mitigation (The 5-Minute Fix)
**Action A: Soft Restart**
If it's a minor memory leak:
```bash
docker compose -f project_devops/platform/composition/docker-compose.apps.yml restart odoo
```

**Action B: Cache Clear (Redis)**
If Odoo is sluggish due to stale sessions:
```bash
docker exec -it platform-redis redis-cli FLUSHALL
```

**Action C: Emergency Resource Bump**
If the load is sustained and legitimate, temporarily increase limit in `docker-compose.override.yml` and apply:
```bash
# Edit override file to 800MB
./cli.sh up
```

## ✅ Phase 4: Verification
1. Confirm `/health` endpoint of Odoo returns `200 OK`.
2. Observe Grafana for 2 minutes to ensure the RAM sawtooth pattern is normalized.
3. Close the incident.

**Post-Mortem:** Analyze Odoo logs to identify the specific report or user action that triggered the spike.
