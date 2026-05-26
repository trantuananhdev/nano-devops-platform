#!/bin/sh
# Docker registry login for deploy user — uses project .env (same GitHub account as ai-agent).
# - ghcr.io: GITHUB_TOKEN / BOOTSTRAP_GITHUB_TOKEN + owner from BOOTSTRAP_REPO_FULL_NAME
# - docker.io: authenticated pull (higher rate limit) + optional mirror in docker_setup.sh
#
# Usage: run as root after filesystem_users.sh (deploy user exists).

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../common/utils.sh" ]; then
    # shellcheck disable=SC1091
    . "$SCRIPT_DIR/../common/utils.sh"
else
    log_info() { echo "[registry-login] $1"; }
    log_error() { echo "[registry-login] ERROR: $1" >&2; }
fi

DEPLOY_USER="${DEPLOY_USER:-deploy}"

if [ "$(id -u)" -ne 0 ]; then
    log_error "Must run as root"
    exit 1
fi

if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
    log_error "User $DEPLOY_USER does not exist — run filesystem_users.sh first"
    exit 1
fi

# Locate repo root .env (Vagrant COPY or DEV sync)
DOTENV=""
for candidate in \
    /opt/platform/src/nano-project-devops/.env \
    /workspace/.env
do
    if [ -f "$candidate" ]; then
        DOTENV="$candidate"
        break
    fi
done

if [ -z "$DOTENV" ]; then
    log_info "No .env found — skip registry login (anonymous Docker Hub limits apply)"
    exit 0
fi

log_info "Loading environment from $DOTENV"

# shellcheck disable=SC1090
set -a
. "$DOTENV"
set +a

# Token: same sources as ai-agent (GITHUB_TOKEN, bootstrap fallback)
GITHUB_TOKEN="$(printf '%s' "${GITHUB_TOKEN:-}" | tr -d '"' | tr -d "'")"
if [ -z "$GITHUB_TOKEN" ]; then
    GITHUB_TOKEN="$(printf '%s' "${BOOTSTRAP_GITHUB_TOKEN:-}" | tr -d '"' | tr -d "'")"
fi

if [ -z "$GITHUB_TOKEN" ]; then
    log_info "GITHUB_TOKEN not set in .env — skip ghcr.io login"
else
    # Owner for ghcr.io (matches CI: ghcr.io/${GITHUB_REPOSITORY_OWNER}/...)
    GHCR_USER=""
    if [ -n "${BOOTSTRAP_REPO_FULL_NAME:-}" ]; then
        GHCR_USER="${BOOTSTRAP_REPO_FULL_NAME%%/*}"
    fi
    if [ -z "$GHCR_USER" ]; then
        GHCR_USER="$(printf '%s' "${GITHUB_REPOSITORY_OWNER:-}" | tr -d '"')"
    fi
    if [ -z "$GHCR_USER" ]; then
        GHCR_USER="$(printf '%s' "${GIT_USER_NAME:-}" | tr -d '"')"
    fi
    if [ -z "$GHCR_USER" ]; then
        GHCR_USER="trantuananhdev"
    fi

    log_info "Logging deploy user into ghcr.io as $GHCR_USER (GitHub PAT from .env)..."
    if printf '%s' "$GITHUB_TOKEN" | su - "$DEPLOY_USER" -c "docker login ghcr.io -u '$GHCR_USER' --password-stdin"; then
        log_info "ghcr.io login OK"
    else
        log_info "ghcr.io login failed (check GITHUB_TOKEN scopes: read:packages)"
    fi
fi

# Docker Hub: PAT does not replace Hub account, but login with any valid Hub cred raises limits.
# Try GitHub token on docker.io — works only if Hub account is linked; otherwise mirror helps.
if [ -n "$GITHUB_TOKEN" ] && [ -n "${GHCR_USER:-}" ]; then
    log_info "Attempting docker.io login (may increase pull limits if Hub linked)..."
    if printf '%s' "$GITHUB_TOKEN" | su - "$DEPLOY_USER" -c "docker login -u '$GHCR_USER' --password-stdin" 2>/dev/null; then
        log_info "docker.io login OK"
    else
        log_info "docker.io login skipped (use mirror.gcr.io in daemon.json for base images)"
    fi
fi

# Pre-pull all static images from platform compose (avoids "No such image" on first boot)
PLATFORM_IMAGES="
ghcr.io/tecnativa/docker-socket-proxy:0.2
tecnativa/docker-socket-proxy:0.2
traefik:v3.1
postgres:16-alpine
redis:7-alpine
prom/prometheus:v2.48.1
grafana/grafana:10.2.0
grafana/loki:2.9.2
jaegertracing/all-in-one:1.53
prom/alertmanager:v0.27.0
prometheuscommunity/postgres-exporter:v0.15.0
oliver006/redis_exporter:v1.58.0
gcr.io/cadvisor/cadvisor:v0.47.0
prom/node-exporter:v1.7.0
prom/blackbox-exporter:v0.25.0
python:3.11-alpine
node:20-slim
"

log_info "Pre-pulling platform images as $DEPLOY_USER..."
for img in $PLATFORM_IMAGES; do
    [ -z "$img" ] && continue
    if su - "$DEPLOY_USER" -c "docker pull '$img'" 2>/dev/null; then
        log_info "Pulled $img"
    else
        log_info "Pull failed (will retry via compose pull): $img"
    fi
done

# compose pull with .env (GHCR faulty-service, etc.)
COMPOSITION_PATH=""
for path in \
    /workspace/project_devops/platform/composition \
    /opt/platform/src/nano-project-devops/project_devops/platform/composition
do
    if [ -f "$path/docker-compose.yml" ]; then
        COMPOSITION_PATH="$path"
        break
    fi
done

if [ -n "$COMPOSITION_PATH" ]; then
    ENV_FILE_ARG=""
    for _ef in /workspace/.env /opt/platform/src/nano-project-devops/.env; do
        if [ -f "$_ef" ]; then
            ENV_FILE_ARG="--env-file $_ef"
            break
        fi
    done
    log_info "Running docker compose pull at $COMPOSITION_PATH ..."
    su - "$DEPLOY_USER" -c "cd '$COMPOSITION_PATH' && docker compose $ENV_FILE_ARG \
        -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.apps.yml \
        pull --ignore-pull-failures" 2>/dev/null || \
    su - "$DEPLOY_USER" -c "cd '$COMPOSITION_PATH' && docker compose $ENV_FILE_ARG \
        -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.apps.yml \
        pull" || log_info "compose pull had warnings (optional images may be missing)"
fi

# Sync GEMINI_API_KEY from .env into platform secret file for compose (optional)
GEMINI_KEY="$(printf '%s' "${GEMINI_API_KEY:-}" | tr -d '"' | tr -d "'")"
if [ -n "$GEMINI_KEY" ]; then
    for base in /opt/platform/src/nano-project-devops /workspace; do
        SECRETS="$base/project_devops/platform/secrets/agentic_ai_gemini_key.txt"
        if [ -d "$(dirname "$SECRETS")" ]; then
            if [ ! -s "$SECRETS" ] 2>/dev/null || [ ! -f "$SECRETS" ]; then
                printf '%s\n' "$GEMINI_KEY" > "$SECRETS"
                chmod 600 "$SECRETS"
                chown "$DEPLOY_USER":"$(id -gn "$DEPLOY_USER")" "$SECRETS" 2>/dev/null || true
                log_info "Synced GEMINI_API_KEY from .env to agentic_ai_gemini_key.txt"
            fi
            break
        fi
    done
fi

log_info "Registry login script finished"
