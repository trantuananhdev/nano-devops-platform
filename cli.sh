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
fi

# --- Helper Functions ---
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
    echo "  smoke-obs           Run Grafana + Prometheus HTTPS smoke tests."
    echo "  smoke-https         Probe all public app HTTPS endpoints."
    echo ""
    echo "EcoIT Trial Commands (→ Acer Ubuntu):"
    echo "  ansible-bootstrap   Bootstrap Acer Ubuntu (first time: Docker, zram, UFW)."
    echo "  ansible-deploy      Deploy EcoIT app to Acer Ubuntu."
    echo "  ansible-ping        Check SSH connectivity to Acer Ubuntu."
    echo "  ecoit-up            Start EcoIT app locally (dev mode)."
    echo "  ecoit-down          Stop local EcoIT dev stack."
    echo "  ecoit-logs          Follow EcoIT app logs (local dev)."
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

cmd_up() {
    cmd_certs
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
ECOIT_APP_COMPOSE="project_devops/apps/ecoit-app/docker-compose.ecoit.yml"

cmd_ansible_runner() {
    local PLAYBOOK="$1"; shift
    # Run ansible-runner container (profile: ops)
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES \
        run --rm ansible-runner \
        ansible-playbook -i inventory/hosts.ini "$PLAYBOOK" "$@"
}

cmd_ansible_bootstrap() {
    echo "[ECOIT] Bootstrapping Acer Ubuntu (one-time setup)..."
    cmd_ansible_runner site.yml
}

cmd_ansible_deploy() {
    local IMAGE_TAG="${1:-latest}"
    echo "[ECOIT] Deploying EcoIT app to Acer Ubuntu (tag: ${IMAGE_TAG})..."
    echo "[ECOIT] Pull image từ GHCR → Ansible compose up → health check"
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES \
        run --rm ansible-runner \
        ansible-playbook -i /tmp/inventory.ini deploy-ecoit.yml \
        -e "ecoit_image_tag=${IMAGE_TAG}"
}

cmd_ansible_ping() {
    echo "[ECOIT] Pinging Acer Ubuntu..."
    cmd_ansible_runner verify-ssh.yml
}

cmd_ecoit_up() {
    echo "[ECOIT] Starting local EcoIT dev stack..."
    $COMPOSE --env-file .env -f "$ECOIT_APP_COMPOSE" up -d --build
    echo "  Backend:  http://localhost:8000/docs"
    echo "  Frontend: http://localhost:3000"
}

cmd_ecoit_down() {
    echo "[ECOIT] Stopping local EcoIT dev stack..."
    $COMPOSE --env-file .env -f "$ECOIT_APP_COMPOSE" down
}

cmd_ecoit_logs() {
    $COMPOSE --env-file .env -f "$ECOIT_APP_COMPOSE" logs -f "${2:-}"
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
    smoke-obs)
        cmd_smoke_obs
        ;;
    smoke-https)
        cmd_smoke_https
        ;;
    ansible-bootstrap)
        cmd_ansible_bootstrap
        ;;
    ansible-deploy)
        cmd_ansible_deploy "${2:-}"
        ;;
    ansible-ping)
        cmd_ansible_ping
        ;;
    ecoit-up)
        cmd_ecoit_up
        ;;
    ecoit-down)
        cmd_ecoit_down
        ;;
    ecoit-logs)
        cmd_ecoit_logs "${2:-}"
        ;;
    *)
        echo "Error: Unknown command '$COMMAND'"
        print_usage
        exit 1
        ;;
esac
