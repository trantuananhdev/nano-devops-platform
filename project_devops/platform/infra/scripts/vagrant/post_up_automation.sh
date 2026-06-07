#!/bin/sh
# post_up_automation.sh — EcoIT Platform readiness check
# Runs on VM after main_setup (background, non-blocking).
set -eu

LOG=/var/log/nano-post-up.log
READY=/opt/platform/.platform-ready
VM_IP_FILE=/opt/platform/vm-service-ip

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

log "=== Nano DevOps — EcoIT Platform post-up ==="

VM_IP="127.0.0.1"
[ -f "$VM_IP_FILE" ] && VM_IP=$(cat "$VM_IP_FILE")

# ----------------------------------------------------------------
# Find compose dir
# ----------------------------------------------------------------
COMPOSE_DIR=""
for p in \
  /opt/platform/src/nano-project-devops/project_devops/platform/composition \
  /workspace/project_devops/platform/composition; do
  if [ -f "$p/docker-compose.yml" ]; then
    COMPOSE_DIR="$p"
    break
  fi
done

if [ -z "$COMPOSE_DIR" ]; then
  log "ERROR: compose dir not found"
  exit 1
fi

ENV_FILE=""
for ef in /opt/platform/src/nano-project-devops/.env /workspace/.env; do
  if [ -f "$ef" ]; then
    ENV_FILE="$ef"
    break
  fi
done

compose() {
  if [ -n "$ENV_FILE" ]; then
    docker compose --env-file "$ENV_FILE" \
      -f "$COMPOSE_DIR/docker-compose.yml" \
      -f "$COMPOSE_DIR/docker-compose.observability.yml" \
      -f "$COMPOSE_DIR/docker-compose.apps.yml" "$@"
  else
    docker compose \
      -f "$COMPOSE_DIR/docker-compose.yml" \
      -f "$COMPOSE_DIR/docker-compose.observability.yml" \
      -f "$COMPOSE_DIR/docker-compose.apps.yml" "$@"
  fi
}

wait_container_healthy() {
  name="$1"
  max="${2:-60}"
  n=0
  while [ "$n" -lt "$max" ]; do
    st=$(docker inspect -f '{{.State.Health.Status}}' "$name" 2>/dev/null || echo "none")
    if [ "$st" = "healthy" ]; then
      log "$name is healthy"
      return 0
    fi
    if docker ps --format '{{.Names}}' | grep -qx "$name"; then
      running=$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null)
      if [ "$st" = "none" ] && [ "$running" = "true" ]; then
        log "$name running (no healthcheck)"
        return 0
      fi
    fi
    n=$((n + 1))
    sleep 10
  done
  log "WARN: timeout waiting for $name"
  return 1
}

# ----------------------------------------------------------------
# Wait for core platform containers
# ----------------------------------------------------------------
log "Waiting for core containers (Postgres, Redis, Traefik)..."
wait_container_healthy platform-postgres 30 || true
wait_container_healthy platform-redis 20 || true
sleep 5

# ----------------------------------------------------------------
# Verify Acer Ubuntu reachability
# ----------------------------------------------------------------
ACER_IP=""
[ -n "$ENV_FILE" ] && ACER_IP=$(grep "^ACER_HOST=" "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d '"' || true)

if [ -n "$ACER_IP" ]; then
  log "Checking Acer Ubuntu connectivity ($ACER_IP)..."
  if ping -c 2 -W 3 "$ACER_IP" > /dev/null 2>&1; then
    log "✅ Acer Ubuntu reachable at $ACER_IP"
    log "   Next: vagrant ssh → cd /opt/platform/src/nano-project-devops"
    log "         ./cli.sh ansible-bootstrap   # First time only"
    log "         ./cli.sh ansible-deploy      # Deploy EcoIT app"
  else
    log "⚠️  Acer $ACER_IP not reachable — ensure both machines on same WiFi/LAN"
  fi
else
  log "WARN: ACER_HOST not set in .env"
fi

# ----------------------------------------------------------------
# Write ready file
# ----------------------------------------------------------------
{
  echo "ready_at=$(date -Iseconds)"
  echo "vm_ip=$VM_IP"
  echo "grafana=https://grafana.nano.platform"
  echo "prometheus=https://prometheus.nano.platform"
  echo "acer_host=${ACER_IP:-not_set}"
  echo "mode=ecoit_trial"
} > "$READY"

log "=== Platform ready ($VM_IP) ==="
log "    EcoIT docs: ai-system/AI_BOOT.md | ai-system/ECOIT_TASK.md"
