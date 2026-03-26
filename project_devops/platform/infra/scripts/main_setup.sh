#!/bin/sh
# Main setup script for the Alpine Linux VM (Idempotent & Secure)
# This script orchestrates the execution of all other setup scripts.

set -e

# Define script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Source common utilities
# Note: utils.sh is not present in the provided file list, assuming it exists.
if [ -f "$SCRIPT_DIR/common/utils.sh" ]; then
    . "$SCRIPT_DIR/common/utils.sh"
else
    log_info() { echo "INFO: $1"; }
    log_error() { echo "ERROR: $1"; exit 1; }
fi

log_info "=========================================="
log_info "Starting Nano DevOps Platform Main Setup"
log_info "=========================================="

if [ "$(id -u)" -ne 0 ]; then
    log_error "This script must be run as root."
fi

# --- Core System Provisioning ---
log_info "Step 1/8: Installing base packages..."
"$SCRIPT_DIR/system/base_packages.sh"

log_info "Step 2/8: Setting up Docker..."
"$SCRIPT_DIR/system/docker_setup.sh"

log_info "Step 3/8: Setting up filesystem and users..."
"$SCRIPT_DIR/system/filesystem_users.sh"

log_info "Step 4/8: Setting up User SSH and Sudo..."
"$SCRIPT_DIR/system/user_ssh_setup.sh"

log_info "Step 5/8: Applying kernel tuning..."
"$SCRIPT_DIR/system/sysctl_tuning.sh"

log_info "Step 6/8: Configuring zram..."
"$SCRIPT_DIR/system/zram_config.sh"

log_info "Step 7/8: Setting up mkcert and generating development certificates..."
"$SCRIPT_DIR/system/mkcert_setup.sh"

log_info "Step 8/8: Setting up platform system service..."
"$SCRIPT_DIR/system/platform_service_setup.sh"

log_info "Step 9/9: Updating /etc/hosts with platform domains..."
DOMAINS="odoo.nano.platform ai.nano.platform grafana.nano.platform prometheus.nano.platform aggregator.nano.platform user.nano.platform data.nano.platform health.nano.platform teencare.nano.platform teencare-lms-api.nano.platform teencare-lms-web.nano.platform"
for d in $DOMAINS; do
    if ! grep -q "$d" /etc/hosts; then
        echo "127.0.0.1 $d" >> /etc/hosts
    fi
done

log_info "✅ All core system setup steps completed!"

# --- Platform Application Bootstrap ---
log_info "=========================================="
log_info "Starting Platform Application Bootstrap"
log_info "=========================================="

DEPLOY_USER="deploy"
PLATFORM_COMPOSITION_PATH=""

# 1. Define candidate paths for the compose file
# The order defines priority: /workspace (dev) -> /opt/platform/src (prod-like)
CANDIDATE_PATHS="
/workspace/project_devops/platform/composition
/opt/platform/src/nano-project-devops/project_devops/platform/composition
"

# 2. Find the valid compose path
for path in $CANDIDATE_PATHS; do
    if [ -f "$path/docker-compose.yml" ]; then
        PLATFORM_COMPOSITION_PATH=$path
        log_info "Found platform composition at: $PLATFORM_COMPOSITION_PATH"
        break
    fi
done

# 3. If no path found, attempt to clone from REPO_URL as a last resort
if [ -z "$PLATFORM_COMPOSITION_PATH" ] && [ -n "${REPO_URL}" ]; then
    log_info "No local source found. Attempting to clone from REPO_URL..."
    CLONE_DIR="/opt/platform/src/nano-project-devops"
    mkdir -p "$(dirname "$CLONE_DIR")"
    chown "$DEPLOY_USER:$(id -gn "$DEPLOY_USER")" "$(dirname "$CLONE_DIR")"
    su - "$DEPLOY_USER" -c "git clone --depth 1 \"$REPO_URL\" \"$CLONE_DIR\""
    
    # Re-check for the compose path after cloning
    if [ -f "$CLONE_DIR/project_devops/platform/composition/docker-compose.yml" ]; then
        PLATFORM_COMPOSITION_PATH="$CLONE_DIR/project_devops/platform/composition"
        log_info "Clone successful. Found platform composition at: $PLATFORM_COMPOSITION_PATH"
    fi
fi

# 4. Generate secrets, certs and start the platform if a valid path was found
if [ -n "$PLATFORM_COMPOSITION_PATH" ]; then
    log_info "Generating missing secrets..."
    "$SCRIPT_DIR/system/setup_secrets.sh" "$PLATFORM_COMPOSITION_PATH"

    log_info "Generating development certificates..."
    # This script needs to know where the source is, assuming it finds it via /tmp/infra or similar
    "$SCRIPT_DIR/certs/generate_dev_certs.sh" "$PLATFORM_COMPOSITION_PATH"

  log_info "Attempting to restart platform services as user '$DEPLOY_USER' to pick up code changes..."
  rc-service nano-platform restart
  log_info "Platform services are restarting in the background."
else
    log_error "Could not find platform source. Bootstrap failed. Please mount the repo to /workspace or use COPY_PROJECT_DEVOPS=1."
fi

log_info "=========================================="
log_info "Platform bootstrap process finished."
log_info "Run 'docker compose ps' as user '$DEPLOY_USER' to check status."
log_info "=========================================="
