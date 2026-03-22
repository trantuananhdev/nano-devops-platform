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

# --- Helper Functions ---
print_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  up              Start all services in development mode."
    echo "  down            Stop all services."
    echo "  ps              Show status of all services."
    echo "  logs [service]  Follow logs for a specific service (or all if not specified)."
    echo "  test            Run platform-level tests."
    echo "  migrate         Run database migrations to the latest version."
    echo "  deploy <svc> <tag> Deploy a new version of a service."
    echo ""
    echo "AI Platform Commands:"
    echo "  ai-up           Start Agentic-AI services."
    echo "  ai-logs         Follow logs for the Agentic-AI service."
    echo "  ai-migrate      Run database migrations for the Agentic-AI service."
}

# --- Command Implementation ---
cmd_up() {
    echo "Starting all services..."
    $COMPOSE $COMPOSE_FILES up -d --remove-orphans
}

cmd_down() {
    echo "Stopping all services..."
    $COMPOSE $COMPOSE_FILES down
}

cmd_ps() {
    $COMPOSE $COMPOSE_FILES ps
}

cmd_logs() {
    if [ -z "${1:-}" ]; then
        $COMPOSE $COMPOSE_FILES logs -f
    else
        $COMPOSE $COMPOSE_FILES logs -f "$1"
    fi
}

cmd_test() {
    echo "Running platform tests..."
    bash ./project_devops/ci/scripts/run-tests.sh
}

cmd_migrate() {
    echo "Running database migrations..."
    # CTO Fix: Mount alembic.ini and migrations from host to container
    $COMPOSE $COMPOSE_FILES run --rm \
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

# --- AI Platform Specific Commands ---
cmd_ai_up() {
    echo "Starting Agentic-AI services..."
    $COMPOSE $COMPOSE_FILES up -d agentic-ai-api
}

cmd_ai_logs() {
    echo "Following logs for Agentic-AI service..."
    $COMPOSE $COMPOSE_FILES logs -f agentic-ai-api
}

cmd_ai_migrate() {
    echo "Running database migrations for Agentic-AI..."
    # AI Platform migrations via node-pg-migrate or similar if needed
    # But for now, let's assume it's part of the standard flow
    $COMPOSE $COMPOSE_FILES exec agentic-ai-api npm run migrate || echo "Migration command failed or not configured in package.json."
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
