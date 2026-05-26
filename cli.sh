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
    echo "AI Platform Commands:"
    echo "  ai-up               Start Agentic-AI services."
    echo "  ai-logs             Follow logs for the Agentic-AI service."
    echo "  ai-migrate          Run database migrations for the Agentic-AI service."
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

# --- AI Platform Specific Commands ---
cmd_ai_up() {
    echo "Starting Agentic-AI services..."
    # shellcheck disable=SC2086
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES up -d agentic-ai-api
}

cmd_ai_logs() {
    echo "Following logs for Agentic-AI service..."
    # shellcheck disable=SC2086
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES logs -f agentic-ai-api
}

cmd_ai_migrate() {
    echo "Running database migrations for Agentic-AI..."
    # AI Platform migrations via node-pg-migrate or similar if needed
    # But for now, let's assume it's part of the standard flow
    # shellcheck disable=SC2086
    $COMPOSE $COMPOSE_ENV_FILE $COMPOSE_FILES exec agentic-ai-api npm run migrate || echo "Migration command failed or not configured in package.json."
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
    ai-up)
        cmd_ai_up
        ;;
    ai-logs)
        cmd_ai_logs
        ;;
    ai-migrate)
        cmd_ai_migrate
        ;;
    *)
        echo "Error: Unknown command '$COMMAND'"
        print_usage
        exit 1
        ;;
esac
