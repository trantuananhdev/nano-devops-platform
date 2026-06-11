#!/bin/bash
# Simple CLI Tool for Nano DevOps Platform
# This script provides a user-friendly interface for common operational tasks.

set -euo pipefail

# Change to the script's directory to ensure paths are correct
cd "$(dirname "$0")"

COMPOSE_DIR="project_devops/platform/composition"
COMPOSE_FILES="-f ${COMPOSE_DIR}/docker-compose.yml \
               -f ${COMPOSE_DIR}/docker-compose.observability.yml \
               -f ${COMPOSE_DIR}/docker-compose.apps.yml \
               -f ${COMPOSE_DIR}/docker-compose.override.yml"

# Detect Docker Compose command (support both v1 and v2)
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif docker-compose version >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "Error: Docker Compose not found."
    exit 1
fi

# Root .env (LLM_PROVIDER, GEMINI_API_KEY, TELEGRAM_*, etc.) — no manual export needed
COMPOSE_ENV_FILE=""
if [ -f ".env" ]; then
    COMPOSE_ENV_FILE="--env-file $(pwd)/.env"
    # Load env vars for target generation
    # shellcheck disable=SC2034,SC1090
    source "$(pwd)/.env"
    # Derive LLM_BASE_URL from ACER_HOST to ensure consistency
    LLM_BASE_URL="http://${ACER_HOST:-192.168.100.6}:8080/v1"
    export LLM_BASE_URL
fi

# --- Helper Functions ---
_generate_llm_node_targets() {
    local _platform_config_dir="./project_devops/platform/config/prometheus"
    local _targets_file="${_platform_config_dir}/llm-node-targets.yml"
    local _probe_targets_file="${_platform_config_dir}/llm-node-probe-targets.yml"

    if [ -z "${ACER_HOST:-}" ]; then
        echo "[cli] ACER_HOST not set in .env — skipping LLM node targets generation"
        return 0
    fi

    echo "[cli] Generating LLM node Prometheus targets for ${ACER_HOST}"
    mkdir -p "${_platform_config_dir}"

    cat > "${_targets_file}" <<EOF
- targets:
  - "${ACER_HOST}:9100"
  labels:
    job: "llm-node"
    host: "llm-node"
EOF

    cat > "${_probe_targets_file}" <<EOF
- targets:
  - "http://${ACER_HOST}:8080/health"
  labels:
    job: "llm-node-health"
    host: "llm-node"
EOF

    echo "[cli] Generated targets: ${_targets_file}, ${_probe_targets_file}"
}

print_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  up                  Start all services in development mode."
    echo "  down                Stop all services."
    echo "  ps                  Show status of all services."
    echo "  logs [service]      Follow logs for a specific service (or all if not specified)."
    echo "  test                Run platform-level tests."
    echo "  migrate             Run database migrations to the latest version."
    echo "  deploy <svc> <tag>  Deploy a new version of a service."
    echo "  redeploy [service]  Rebuild & restart one service (or all). Use after code changes."
    echo "  certs               Generate wildcard TLS for *.nano.platform (Traefik)."
    echo "  secrets             Generate secrets for the platform (if not already present)."
    echo "  smoke-obs           Run Grafana + Prometheus HTTPS smoke tests."
    echo "  smoke-https         Probe all public app HTTPS endpoints."
    echo ""
    echo "Acer Ubuntu (Ansible từ Alpine VM — T-55 dual-user):"
    echo "  ansible-ping          Verify SSH tutinhhao + sudo root (verify-ssh.yml)."
    echo "  ansible-test-users    Test SSH access cho CẢ 2 user root + tutinhhao."
    echo "  ansible-bootstrap     Bootstrap Ubuntu: Docker, zram, UFW, sudoers, SSH hardening."
    echo "  ansible-deploy-llm    Deploy Gemma 4 llama-server trên Ubuntu (LLM node)."
    echo "  ansible-teardown-llm  Reset LLM node (xóa containers/volumes/data)."
    echo "  ansible-teardown-full Full reset Ubuntu (xóa cả Docker)."
    echo ""
    echo "  Prerequisite: inject prod_deployer.pub vào CẢ 2 user (root + tutinhhao) trên Ubuntu ✅"
    echo "  Xem: project_devops/apps/ansible-ubuntu/inventory/hosts.ini"
    echo ""
    echo "HDTV AI Platform (App stack on Alpine VM):"
    echo "  hdtv-up             Start HDTV stack (FastAPI, Celery, PG, Chroma, FE)."
    echo "  hdtv-down           Stop HDTV stack."
    echo "  hdtv-logs [svc]     Follow HDTV logs."
    echo "  hdtv-migrate        Run Alembic migrations."
    echo "  hdtv-seed           Seed dossiers + Chroma legal docs."
    echo "  hdtv-backup         Run full backup (PostgreSQL, MinIO, Chroma)."
    echo "  hdtv-smoke          Run HDTV stack smoke tests (containers + API)."
    echo "  obs-down            Stop observability stack (free RAM for demo)."
    echo "  obs-alerts          Check Alertmanager active alerts (T-32)."
    echo "  validate-env        Validate .env required vars before deploy."
}

# --- Command Implementation ---
cmd_certs() {
    local CERT_SCRIPT="project_devops/platform/infra/scripts/system/generate_certs.sh"
    if [ ! -f "$CERT_SCRIPT" ]; then
        echo "Error: $CERT_SCRIPT not found"
        exit 1
    fi
    echo "Generating Traefik wildcard TLS (*.nano.platform)..."
    sh "$CERT_SCRIPT"
}

cmd_secrets() {
    local SECRETS_SCRIPT="project_devops/platform/infra/scripts/system/setup_secrets.sh"
    if [ ! -f "$SECRETS_SCRIPT" ]; then
        echo "Error: $SECRETS_SCRIPT not found"
        exit 1
    fi
    echo "Generating platform secrets..."
    sh "$SECRETS_SCRIPT" "$COMPOSE_DIR"
}

cmd_up() {
    cmd_certs
    _generate_llm_node_targets
    echo "Starting all services..."
    # shellcheck disable=SC2086
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES up -d --remove-orphans
}

cmd_smoke_obs() {
    bash ./project_devops/platform/ops/smoke-tests/smoke-test-observability.sh
}

cmd_smoke_https() {
    bash ./project_devops/platform/ops/smoke-tests/smoke-test-https-apps.sh
}

cmd_down() {
    echo "Stopping all services..."
    # shellcheck disable=SC2086
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES down
}

cmd_ps() {
    # shellcheck disable=SC2086
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES ps
}

cmd_logs() {
    if [ -z "${1:-}" ]; then
        # shellcheck disable=SC2086
        $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES logs -f
    else
        # shellcheck disable=SC2086
        $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES logs -f "$1"
    fi
}

cmd_test() {
    echo "Running platform tests..."
    bash ./project_devops/ci/scripts/run-tests.sh
}

cmd_migrate() {
    echo "Running database migrations..."
    # CTO Fix: Mount alembic.ini and migrations from host to container
    # shellcheck disable=SC2086
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES run --rm \
        -v "$(pwd)/alembic.ini:/app/alembic.ini" \
        -v "$(pwd)/project_devops/platform/migrations:/app/project_devops/platform/migrations" \
        data-api alembic upgrade head
}

cmd_deploy() {
    if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
        echo "Error: deploy command requires <service> and <tag> arguments."
        print_usage
        exit 1
    fi
    SERVICE_NAME=$1 IMAGE_TAG=$2 bash ./project_devops/platform/ops/deployment/deploy.sh
}

# Rebuild & restart one service (or all) after code changes on the host.
# Usage inside VM: ./cli.sh redeploy [service]
cmd_redeploy() {
    local SERVICE="${1:-}"
    if [ -n "$SERVICE" ]; then
        echo "Rebuilding & restarting service: ${SERVICE}..."
        # shellcheck disable=SC2086
        $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES up -d --build --pull missing --no-deps "$SERVICE"
    else
        echo "Rebuilding & restarting ALL services..."
        # shellcheck disable=SC2086
        $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES up -d --build --pull missing --remove-orphans
    fi
    echo "Done. Check logs: $0 logs ${SERVICE:-}"
}

# ----- EcoIT / Ansible Commands -----

ANSIBLE_DIR="project_devops/apps/ansible-ubuntu"
HDTV_COMPOSE="${COMPOSE_DIR}/docker-compose.hdtv.yml"

_check_ansible_prereqs() {
    if [ -z "${ACER_HOST:-}" ]; then
        echo "ERROR: ACER_HOST not set in .env"
        exit 1
    fi

    local ssh_key
    ssh_key="$(pwd)/.ssh/prod_deployer"
    if [ ! -f "$ssh_key" ]; then
        echo "ERROR: SSH key not found at $ssh_key"
        echo "       Copy prod_deployer vào .ssh/ trước khi chạy Ansible."
        exit 1
    fi
    if [ ! -s "$ssh_key" ]; then
        echo "ERROR: SSH key tại $ssh_key rỗng"
        exit 1
    fi
    # T-55: Ansible kết nối tutinhhao@${ACER_HOST} qua prod_deployer (ed25519).
    # Key đã inject vào CẢ root + tutinhhao trên Ubuntu ✅
    # become: true → sudo root khi cần.
}

cmd_ansible_runner() {
    local PLAYBOOK="$1"; shift
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES \
        run --rm ansible-runner \
        "$PLAYBOOK" "$@"
}

cmd_ansible_bootstrap() {
    _check_ansible_prereqs
    echo "[HDTV] Bootstrapping Acer Ubuntu (Docker, zram, UFW, observability)..."
    cmd_ansible_runner site.yml
}

cmd_ansible_ping() {
    _check_ansible_prereqs
    echo "[HDTV] Verifying SSH tutinhhao + sudo root access to Acer Ubuntu..."
    cmd_ansible_runner verify-ssh.yml
}

cmd_ansible_test_users() {
    _check_ansible_prereqs
    echo "[HDTV] Testing SSH access for BOTH users (root + tutinhhao)..."
    cmd_ansible_runner test-dual-users.yml
}

cmd_ansible_deploy_llm() {
    _check_ansible_prereqs
    echo "[HDTV] Deploying Gemma 4 llama-server on Ubuntu (LLM node)..."
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES \
        run --rm ansible-runner \
        deploy-llm.yml
}

cmd_ansible_teardown_llm() {
    echo "[HDTV] Resetting Ubuntu LLM node (remove containers/volumes/data)..."
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES \
        run --rm ansible-runner \
        teardown-llm.yml
}

cmd_ansible_teardown_full() {
    echo "[HDTV] FULL reset Ubuntu (including Docker)..."
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES \
        run --rm ansible-runner \
        teardown-llm.yml -e "wipe_docker=true"
}

cmd_obs_down() {
    echo "[HDTV] Stopping observability stack to free RAM..."
    $COMPOSE $COMPOSE_ENV_FILE \
        -f "${COMPOSE_DIR}/docker-compose.yml" \
        -f "${COMPOSE_DIR}/docker-compose.observability.yml" \
        down
}

cmd_obs_alerts() {
    echo "[OBS] Checking Alertmanager alert status..."
    local alertmanager_url="${ALERTMANAGER_URL:-http://localhost:9093}"
    if curl -sf "${alertmanager_url}/api/v2/alerts" | python3 -m json.tool 2>/dev/null; then
        echo ""
        echo "✅ Alertmanager reachable at ${alertmanager_url}"
    else
        echo "⚠️  Alertmanager not reachable at ${alertmanager_url}"
        echo "   Make sure obs stack is up: ./cli.sh up"
        exit 1
    fi
}

cmd_validate_env() {
    bash project_devops/platform/infra/scripts/validate_env.sh
}

cmd_hdtv_up() {
    cmd_validate_env
    echo "[HDTV] Starting HDTV AI platform stack..."
    $COMPOSE --env-file .env \
        -f "${COMPOSE_DIR}/docker-compose.yml" \
        -f "$HDTV_COMPOSE" up -d --build
    echo "  API:      http://localhost:8000/docs"
    echo "  Frontend: http://localhost:3080"
}

cmd_hdtv_down() {
    echo "[HDTV] Stopping HDTV stack..."
    $COMPOSE --env-file .env \
        -f "${COMPOSE_DIR}/docker-compose.yml" \
        -f "$HDTV_COMPOSE" down
}

cmd_hdtv_logs() {
    $COMPOSE --env-file .env \
        -f "${COMPOSE_DIR}/docker-compose.yml" \
        -f "$HDTV_COMPOSE" logs -f "${2:-}"
}

cmd_hdtv_migrate() {
    echo "[HDTV] Running Alembic migrations..."
    $COMPOSE --env-file .env \
        -f "${COMPOSE_DIR}/docker-compose.yml" \
        -f "$HDTV_COMPOSE" run --rm hdtv-api alembic upgrade head
}

cmd_hdtv_seed() {
    echo "[HDTV] Seeding database and Chroma..."
    $COMPOSE --env-file .env \
        -f "${COMPOSE_DIR}/docker-compose.yml" \
        -f "$HDTV_COMPOSE" run --rm hdtv-api python scripts/seed.py
}

cmd_hdtv_backup() {
    echo "[HDTV] Running backup (PostgreSQL, MinIO, Chroma)..."
    $COMPOSE --env-file .env \
        -f "${COMPOSE_DIR}/docker-compose.yml" \
        -f "$HDTV_COMPOSE" exec hdtv-backup /scripts/backup.sh
}

cmd_hdtv_smoke() {
    local SMOKE_SCRIPT="project_devops/platform/infra/scripts/vagrant/hdtv_smoke_test.sh"
    if [ ! -f "$SMOKE_SCRIPT" ]; then
        echo "Error: $SMOKE_SCRIPT not found"
        exit 1
    fi
    echo "[HDTV] Running smoke tests..."
    bash "$SMOKE_SCRIPT"
}

# --- Main Dispatcher ---
COMMAND="${1:-}"

if [ -z "$COMMAND" ]; then
    print_usage
    exit 1
fi

case "$COMMAND" in
    up)
        cmd_up
        ;;
    down)
        cmd_down
        ;;
    ps)
        cmd_ps
        ;;
    logs)
        cmd_logs "${2:-}"
        ;;
    test)
        cmd_test
        ;;
    migrate)
        cmd_migrate
        ;;
    deploy)
        cmd_deploy "${2:-}" "${3:-}"
        ;;
    redeploy)
        cmd_redeploy "${2:-}"
        ;;
    certs)
        cmd_certs
        ;;
    secrets)
        cmd_secrets
        ;;
    smoke-obs)
        cmd_smoke_obs
        ;;
    smoke-https)
        cmd_smoke_https
        ;;
    ansible-bootstrap)
        cmd_ansible_bootstrap
        ;;
    ansible-ping)
        cmd_ansible_ping
        ;;
    ansible-test-users)
        cmd_ansible_test_users
        ;;
    ansible-deploy-llm)
        cmd_ansible_deploy_llm
        ;;
    ansible-teardown-llm)
        cmd_ansible_teardown_llm
        ;;
    ansible-teardown-full)
        cmd_ansible_teardown_full
        ;;
    obs-down)
        cmd_obs_down
        ;;
    obs-alerts)
        cmd_obs_alerts
        ;;
    hdtv-up)
        cmd_hdtv_up
        ;;
    hdtv-down)
        cmd_hdtv_down
        ;;
    hdtv-logs)
        cmd_hdtv_logs "${2:-}"
        ;;
    hdtv-migrate)
        cmd_hdtv_migrate
        ;;
    hdtv-seed)
        cmd_hdtv_seed
        ;;
    hdtv-backup)
        cmd_hdtv_backup
        ;;
    hdtv-smoke)
        cmd_hdtv_smoke
        ;;
    validate-env)
        cmd_validate_env
        ;;
    *)
        echo "Error: Unknown command '$COMMAND'"
        print_usage
        exit 1
        ;;
esac
