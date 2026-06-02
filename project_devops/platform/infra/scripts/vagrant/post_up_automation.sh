#!/bin/sh
# Runs on VM after main_setup (background). No manual steps on host except optional UAC.
set -eu

LOG=/var/log/nano-post-up.log
READY=/opt/platform/.platform-ready
VM_IP_FILE=/opt/platform/vm-service-ip

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

log "=== Nano post-up automation ==="

VM_IP="127.0.0.1"
[ -f "$VM_IP_FILE" ] && VM_IP=$(cat "$VM_IP_FILE")

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
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_DIR/docker-compose.yml" \
      -f "$COMPOSE_DIR/docker-compose.observability.yml" \
      -f "$COMPOSE_DIR/docker-compose.apps.yml" "$@"
  else
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" \
      -f "$COMPOSE_DIR/docker-compose.observability.yml" \
      -f "$COMPOSE_DIR/docker-compose.apps.yml" "$@"
  fi
}

wait_container_healthy() {
  name="$1"
  max="${2:-90}"
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

log "Waiting for core containers..."
wait_container_healthy platform-postgres 60 || true
wait_container_healthy platform-redis 40 || true
sleep 15

log "CRM DB migration (leads extended + traffic_summaries)..."
docker exec platform-postgres psql -U postgres -d crm_db -v ON_ERROR_STOP=0 <<-EOSQL 2>>"$LOG" || true
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS transaction_type VARCHAR(32);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS budget_range VARCHAR(128);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS bedroom_count VARCHAR(32);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS email VARCHAR(255);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb;
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS notes JSONB NOT NULL DEFAULT '[]'::jsonb;
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS activities JSONB NOT NULL DEFAULT '[]'::jsonb;
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS deals JSONB NOT NULL DEFAULT '[]'::jsonb;
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(128);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS source VARCHAR(64);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS company VARCHAR(255);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS website VARCHAR(512);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS address TEXT;
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS city VARCHAR(128);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS country VARCHAR(64);
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS description TEXT;
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMPTZ;
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS kanban_stage VARCHAR(32) NOT NULL DEFAULT 'new';
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS chat_history JSONB;
  ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_manager_note TEXT;
  CREATE TABLE IF NOT EXISTS traffic_summaries (
    scenario_id VARCHAR(64) PRIMARY KEY,
    title_vi VARCHAR(255) NOT NULL DEFAULT '',
    summary_vi TEXT NOT NULL DEFAULT '',
    hot_leads INT NOT NULL DEFAULT 0,
    channels_json JSONB NOT NULL DEFAULT '{}',
    recommendations_json JSONB NOT NULL DEFAULT '[]',
    lead_count INT NOT NULL DEFAULT 0,
    raw_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  );
  GRANT ALL PRIVILEGES ON TABLE traffic_summaries TO crm_user;
EOSQL

log "Waiting for Odoo..."
wait_container_healthy platform-odoo 120 || true

log "Installing Odoo module crm_real_estate (first run may take several minutes)..."
if docker ps --format '{{.Names}}' | grep -qx platform-odoo; then
  docker exec platform-odoo odoo -d odoo -i crm_real_estate --stop-after-init --without-demo=all >>"$LOG" 2>&1 \
    || log "WARN: Odoo module install returned non-zero (may already be installed)"
  docker start platform-odoo 2>/dev/null || compose up -d odoo 2>>"$LOG" || true
  wait_container_healthy platform-odoo 90 || true
fi

log "Waiting for CRM ingestion..."
wait_container_healthy platform-crm-ingestion 60 || true

{
  echo "ready_at=$(date -Iseconds)"
  echo "vm_ip=$VM_IP"
  echo "crm=https://crm-demo.nano.platform"
  echo "odoo=https://odoo.nano.platform"
} > "$READY"

log "=== Platform ready ($VM_IP) ==="
