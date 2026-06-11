#!/bin/bash
# hdtv_auto_deploy.sh — Auto-deploy HDTV platform + LLM node
# Chạy idempotent mỗi lần vagrant up.
set -euo pipefail

LOG="/var/log/hdtv-auto-deploy.log"
PROJECT_DIR="/opt/platform/src/nano-project-devops"
READY_FILE="/opt/platform/.hdtv-ready"

log() {
    local ts
    ts=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$ts] $*" | tee -a "$LOG"
}

log "=== HDTV Auto-Deploy ==="

# ---------------------------------------------------------------------------
# 1. Prerequisites
# ---------------------------------------------------------------------------
log "1/6: Checking prerequisites..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    log "ERROR: .env not found at $PROJECT_DIR"
    exit 1
fi

set -a
. "$PROJECT_DIR/.env"
set +a
cd "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# 2. Teardown stale stacks
# ---------------------------------------------------------------------------
log "2/6: Teardown stale stacks..."
./cli.sh hdtv-down 2>&1 | tee -a "$LOG" || log "ℹ️ HDTV was not running"
./cli.sh obs-down  2>&1 | tee -a "$LOG" || true

# ---------------------------------------------------------------------------
# 3. Platform stack up
# ---------------------------------------------------------------------------
log "3/6: Starting platform stack..."
./cli.sh up || { log "ERROR: Platform stack failed"; exit 1; }

# ---------------------------------------------------------------------------
# 4. LLM node on Ubuntu (idempotent — skip if unreachable)
# ---------------------------------------------------------------------------
log "4/6: LLM node deployment..."
if [ -z "${ACER_HOST:-}" ]; then
    log "⚠️  ACER_HOST not set — skipping LLM deployment"
elif ! ping -c 1 -W 2 "$ACER_HOST" >/dev/null 2>&1; then
    log "⚠️  Ubuntu ($ACER_HOST) not reachable — skipping LLM deployment"
else
    log "Ubuntu reachable. Verifying SSH access..."
    if ./cli.sh ansible-ping 2>&1 | tee -a "$LOG" | grep -q "SUCCESS\|ok="; then
        log "✅ SSH OK"
        
        # Reset LLM node if RESET_UBUNTU_LLM is true
        if [ "${RESET_UBUNTU_LLM:-false}" = "true" ]; then
            log "🔄 RESET_UBUNTU_LLM=true — tearing down existing LLM stack first..."
            ./cli.sh ansible-teardown-llm 2>&1 | tee -a "$LOG"
            log "✅ LLM teardown complete"
        fi
        
        log "Running bootstrap + LLM deploy..."
        ./cli.sh ansible-bootstrap   2>&1 | tee -a "$LOG"
        ./cli.sh ansible-deploy-llm  2>&1 | tee -a "$LOG"
        log "✅ LLM node deployed"
    else
        log "❌ SSH to Ubuntu failed."
        log "   Đảm bảo prod_deployer.pub đã được inject vào /root/.ssh/authorized_keys trên Ubuntu ✅"
        log "   Test thủ công: ssh -i .ssh/prod_deployer root@${ACER_HOST}"
    fi
fi

# ---------------------------------------------------------------------------
# 5. HDTV platform (app stack on Alpine VM)
# ---------------------------------------------------------------------------
log "5/6: Deploying HDTV platform..."
./cli.sh hdtv-up      || { log "ERROR: hdtv-up failed"; exit 1; }
./cli.sh hdtv-migrate || { log "ERROR: hdtv-migrate failed"; exit 1; }
./cli.sh hdtv-seed    2>&1 | tee -a "$LOG" || log "⚠️ Seed may have already run (idempotent)"

# ---------------------------------------------------------------------------
# 6. Done
# ---------------------------------------------------------------------------
{
    echo "deployed_at=$(date -Iseconds)"
    echo "acer_host=${ACER_HOST:-not_set}"
    echo "hdtv_up=true"
} > "$READY_FILE"

log "=== HDTV Auto-Deploy Complete ==="
log "✅ FE:  http://localhost:3080 or https://hdtv.nano.platform"
log "✅ API: http://localhost:8000/docs"

# Post-deploy smoke test (non-blocking)
SMOKE_SCRIPT="/tmp/infra/scripts/vagrant/hdtv_smoke_test.sh"
if [ -f "$SMOKE_SCRIPT" ]; then
    log "Running smoke test..."
    chmod +x "$SMOKE_SCRIPT"
    "$SMOKE_SCRIPT" 2>&1 | tee -a "$LOG" && log "✅ Smoke test passed" || log "⚠️ Smoke test: some checks failed"
fi
