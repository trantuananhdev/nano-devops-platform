#!/bin/sh
# Alpine Linux Docker Setup Script (Idempotent)

set -eu

# Source common utilities for logging
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../common/utils.sh" ]; then
    . "$SCRIPT_DIR/../common/utils.sh"
else
    log_info() { echo "INFO: $1"; }
    log_error() { echo "ERROR: $1"; exit 1; }
fi

log_info "=========================================="
log_info "Alpine Linux Docker Setup"
log_info "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi



# Enable and start Docker if not already running
if ! rc-service -e docker; then
    log_info "Enabling Docker service..."
    rc-update add docker default
fi

log_info "Starting Docker service..."
rc-service docker start

log_info "Waiting for Docker daemon..."

MAX_RETRIES=20
RETRY_COUNT=0

until docker info >/dev/null 2>&1; do
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
        log_error "Error: Docker daemon failed to start"
    fi

    log_info "Docker not ready yet... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done

log_info "Docker is running correctly."

# Create external network if not exists
if ! docker network inspect platform-network >/dev/null 2>&1; then
    log_info "Creating external platform-network..."
    docker network create platform-network
else
    log_info "Platform-network already exists."
fi

# Install Loki Docker Driver plugin (Idempotent)
if ! docker plugin inspect loki >/dev/null 2>&1; then
    log_info "Installing Loki Docker logging plugin..."
    docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions || log_info "Warning: Failed to install Loki plugin. Logging might fail if driver is set to 'loki'."
else
    log_info "Loki Docker logging plugin is already installed."
fi

log_info "=========================================="
log_info "Docker setup completed successfully!"
log_info "=========================================="
