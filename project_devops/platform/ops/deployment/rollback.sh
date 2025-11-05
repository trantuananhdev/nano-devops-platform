#!/bin/bash
# Rollback Script for Nano DevOps Platform
# GitOps-compliant rollback: re-deploy previous image from registry
# Supports fast rollback by re-deploying previous image tag
# Enhanced with automatic previous tag detection from deployment state

set -euo pipefail

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-project_devops/platform/docker-compose.yml}"
SERVICE_NAME="${SERVICE_NAME:-}"
PREVIOUS_IMAGE_TAG="${PREVIOUS_IMAGE_TAG:-}"
REGISTRY="${REGISTRY:-ghcr.io}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-60}"
DEPLOYMENT_STATE_FILE="${DEPLOYMENT_STATE_FILE:-$(dirname "$0")/.deployment-state}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get previous image tag from deployment state
get_previous_tag() {
    local service=$1
    if [ -f "$DEPLOYMENT_STATE_FILE" ]; then
        grep "^${service}=" "$DEPLOYMENT_STATE_FILE" | cut -d'=' -f2 | cut -d':' -f2 || echo ""
    else
        echo ""
    fi
}

# Function to get current image tag from deployment state
get_current_tag() {
    local service=$1
    if [ -f "$DEPLOYMENT_STATE_FILE" ]; then
        grep "^${service}=" "$DEPLOYMENT_STATE_FILE" | cut -d'=' -f2 | cut -d':' -f1 || echo ""
    else
        echo ""
    fi
}

# Validate inputs
if [ -z "$SERVICE_NAME" ]; then
    log_error "SERVICE_NAME environment variable is required"
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Auto-detect previous tag if not provided
if [ -z "$PREVIOUS_IMAGE_TAG" ]; then
    PREVIOUS_IMAGE_TAG=$(get_previous_tag "$SERVICE_NAME")
    if [ -z "$PREVIOUS_IMAGE_TAG" ] || [ "$PREVIOUS_IMAGE_TAG" = "none" ]; then
        log_error "PREVIOUS_IMAGE_TAG not provided and could not be auto-detected from deployment state"
        log_error "Please set PREVIOUS_IMAGE_TAG environment variable or ensure deployment state exists"
        log_error "Deployment state file: $DEPLOYMENT_STATE_FILE"
        exit 1
    fi
    log_info "Auto-detected previous image tag: $PREVIOUS_IMAGE_TAG"
else
    log_info "Using provided previous image tag: $PREVIOUS_IMAGE_TAG"
fi

# Get current tag for logging
CURRENT_TAG=$(get_current_tag "$SERVICE_NAME")
if [ -n "$CURRENT_TAG" ]; then
    log_info "Current image tag: $CURRENT_TAG"
fi

log_warn "Starting rollback for service: $SERVICE_NAME"
log_info "Rolling back to image tag: $PREVIOUS_IMAGE_TAG"
log_info "Registry: $REGISTRY"
log_info "Compose file: $COMPOSE_FILE"

# Step 1: Set IMAGE_TAG to previous tag for docker-compose
log_info "Step 1: Configuring previous image tag..."
export IMAGE_TAG="$PREVIOUS_IMAGE_TAG"

# Step 2: Pull previous image from registry
log_info "Step 2: Pulling previous image from registry ($REGISTRY)..."
docker-compose -f "$COMPOSE_FILE" pull "$SERVICE_NAME" || {
    log_error "Failed to pull previous image for $SERVICE_NAME"
    log_error "Ensure docker-compose.yml references registry image with IMAGE_TAG variable"
    exit 1
}

# Step 3: Restart service with previous image
log_info "Step 3: Restarting service with previous image..."
docker-compose -f "$COMPOSE_FILE" up -d --no-deps "$SERVICE_NAME" || {
    log_error "Failed to restart service with previous image"
    exit 1
}

# Step 4: Wait for health check
log_info "Step 4: Waiting for health check (timeout: ${HEALTH_CHECK_TIMEOUT}s)..."
timeout=$HEALTH_CHECK_TIMEOUT
elapsed=0
while [ $elapsed -lt $timeout ]; do
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "${SERVICE_NAME}" 2>/dev/null || echo "none")
    
    if [ "$health_status" = "healthy" ]; then
        log_info "Health check passed!"
        break
    fi
    
    if [ "$health_status" = "unhealthy" ]; then
        log_error "Health check failed! Rollback may not be successful."
        log_warn "Service is running but unhealthy. Manual intervention may be required."
        break
    fi
    
    sleep 5
    elapsed=$((elapsed + 5))
    log_info "Waiting for health check... (${elapsed}s/${timeout}s)"
done

if [ "$health_status" = "healthy" ]; then
    # Update deployment state after successful rollback
    log_info "Updating deployment state..."
    if [ -f "$DEPLOYMENT_STATE_FILE" ]; then
        # Remove old entry if exists
        if grep -q "^${SERVICE_NAME}=" "$DEPLOYMENT_STATE_FILE"; then
            sed -i.bak "/^${SERVICE_NAME}=/d" "$DEPLOYMENT_STATE_FILE"
        fi
        # Add new entry (previous becomes current, current becomes previous)
        echo "${SERVICE_NAME}=${PREVIOUS_IMAGE_TAG}:${CURRENT_TAG:-none}" >> "$DEPLOYMENT_STATE_FILE"
    fi
    
    # Log rollback history
    DEPLOYMENT_LOG="${DEPLOYMENT_LOG:-$(dirname "$0")/.deployment-history}"
    echo "$(date -u +"%Y-%m-%d %H:%M:%S UTC") | $SERVICE_NAME | $PREVIOUS_IMAGE_TAG | ROLLBACK | From: ${CURRENT_TAG:-unknown}" >> "$DEPLOYMENT_LOG"
    
    log_info "✅ Rollback completed successfully for $SERVICE_NAME"
    log_info "Deployment state updated"
else
    log_warn "⚠️  Rollback completed, but health check status: $health_status"
    log_warn "Please verify service manually"
    
    # Show diagnostics
    log_warn "Container status:"
    docker inspect --format='{{.State.Status}}' "${SERVICE_NAME}" 2>/dev/null || echo "unknown"
    log_warn "Recent logs:"
    docker logs --tail 20 "$SERVICE_NAME" 2>&1 || true
fi
