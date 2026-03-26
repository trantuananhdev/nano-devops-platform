#!/bin/bash
# CD Deployment Script for Nano DevOps Platform
# GitOps-compliant deployment: pull image → health check → switch traffic → remove old version
# Supports container image registry (ghcr.io) with versioned image tags
# Enhanced with reliability improvements: state tracking, pre-deployment validation, better error handling

set -euo pipefail

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-project_devops/platform/composition/docker-compose.yml}"
SERVICE_NAME="${SERVICE_NAME:-}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-ghcr.io}"
GITHUB_REPOSITORY_OWNER="${GITHUB_REPOSITORY_OWNER:-trantuananhdev}"
IMAGE_NAME="${IMAGE_NAME:-owner/repo}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-60}"
DEPLOYMENT_STATE_FILE="${DEPLOYMENT_STATE_FILE:-$(dirname "$0")/.deployment-state}"
SERVICE_CONTAINER_NAME="${SERVICE_CONTAINER_NAME:-$SERVICE_NAME}"

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

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    log_error "Docker Compose not available"
    exit 1
fi

# Function to get current image tag for a service
get_current_tag() {
    local service=$1
    if [ -f "$DEPLOYMENT_STATE_FILE" ]; then
        grep "^${service}=" "$DEPLOYMENT_STATE_FILE" | cut -d'=' -f2 | cut -d':' -f1 || echo ""
    else
        echo ""
    fi
}

# Function to update deployment state
update_deployment_state() {
    local service=$1
    local current_tag=$2
    local previous_tag=$3
    
    # Create state file if it doesn't exist
    touch "$DEPLOYMENT_STATE_FILE"
    
    # Remove old entry if exists
    if grep -q "^${service}=" "$DEPLOYMENT_STATE_FILE"; then
        sed -i.bak "/^${service}=/d" "$DEPLOYMENT_STATE_FILE"
    fi
    
    # Add new entry
    echo "${service}=${current_tag}:${previous_tag}" >> "$DEPLOYMENT_STATE_FILE"
}

# Function to perform rollback
perform_rollback() {
    local previous_tag=$1
    log_warn "Rolling back to previous image tag: $previous_tag"
    
    if [ -z "$previous_tag" ] || [ "$previous_tag" = "none" ]; then
        log_error "No previous image tag available for rollback"
        log_error "Manual intervention required"
        return 1
    fi
    
    # Restore previous tag
    export IMAGE_TAG="$previous_tag"
    $COMPOSE $COMPOSE_ARGS up -d --no-deps "$SERVICE_NAME" || {
        log_error "Failed to rollback to previous image"
        return 1
    }
    
    log_info "Rollback completed. Waiting for health check..."
    sleep 10
    
    # Check health after rollback
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "${SERVICE_NAME}" 2>/dev/null || echo "none")
    if [ "$health_status" = "healthy" ]; then
        log_info "Rollback successful - service is healthy"
        return 0
    else
        log_warn "Rollback completed but service health status: $health_status"
        log_warn "Manual verification required"
        return 1
    fi
}

# Validate inputs
if [ -z "$SERVICE_NAME" ]; then
    log_error "SERVICE_NAME environment variable is required"
    exit 1
fi

# Prepare COMPOSE_ARGS for multiple files
COMPOSE_ARGS=""
# Use a more portable way to split colon-separated paths
old_ifs="$IFS"
IFS=':'
for i in $COMPOSE_FILE; do
    if [ ! -f "$i" ]; then
        log_error "Docker Compose file not found: $i"
        IFS="$old_ifs"
        exit 1
    fi
    COMPOSE_ARGS="$COMPOSE_ARGS -f $i"
done
IFS="$old_ifs"

log_info "Starting deployment for service: $SERVICE_NAME"
log_info "Image tag: $IMAGE_TAG"
log_info "Registry: $REGISTRY"
log_info "Compose files: $COMPOSE_FILE"
log_info "Compose arguments: $COMPOSE_ARGS"

# Pre-deployment validation
log_info "Pre-deployment validation..."

# Check disk space (at least 1GB free)
available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$available_space" -lt 1 ]; then
    log_error "Insufficient disk space: ${available_space}GB available (need at least 1GB)"
    exit 1
fi
log_info "Disk space check passed: ${available_space}GB available"

# Check Docker is running
if ! docker ps > /dev/null 2>&1; then
    log_error "Docker is not running or not accessible"
    exit 1
fi
log_info "Docker connectivity check passed"

# Get current image tag before deployment (for rollback)
PREVIOUS_TAG=$(get_current_tag "$SERVICE_NAME")
if [ -z "$PREVIOUS_TAG" ]; then
    PREVIOUS_TAG="none"
    log_warn "No previous deployment found for $SERVICE_NAME (first deployment?)"
else
    log_info "Previous image tag: $PREVIOUS_TAG"
fi

# Step 1: Pull new image from registry
log_info "Step 1: Pulling new image from registry ($REGISTRY)..."
# Export variables for docker-compose to use
export IMAGE_TAG
export REGISTRY
export GITHUB_REPOSITORY_OWNER
$COMPOSE $COMPOSE_ARGS pull "$SERVICE_NAME" || {
    log_error "Failed to pull image for $SERVICE_NAME"
    log_error "Ensure docker-compose.yml references registry image with IMAGE_TAG variable"
    log_error "Example: image: ${REGISTRY}/owner/repo:\${IMAGE_TAG:-latest}"
    exit 1
}
log_info "Image pulled successfully"

# Step 2: Start new container with rolling update
log_info "Step 2: Starting new container (rolling update)..."
$COMPOSE $COMPOSE_ARGS up -d "$SERVICE_NAME" || {
    log_error "Failed to start new container for $SERVICE_NAME"
    log_error "Check container logs: docker logs $SERVICE_NAME"
    perform_rollback "$PREVIOUS_TAG" || true
    exit 1
}

# Resolve container name/ID for health check after container is started/recreated
if [ -z "${SERVICE_CONTAINER_NAME:-}" ] || [ "$SERVICE_CONTAINER_NAME" = "$SERVICE_NAME" ] || [ -n "${RESOLVED_ID:-}" ]; then
    log_info "Resolving container ID for $SERVICE_NAME after deployment..."
    RESOLVED_ID=$($COMPOSE $COMPOSE_ARGS ps -q "$SERVICE_NAME" 2>/dev/null || echo "")
    if [ -n "$RESOLVED_ID" ]; then
        SERVICE_CONTAINER_NAME="$RESOLVED_ID"
        log_info "Resolved $SERVICE_NAME to container ID: $SERVICE_CONTAINER_NAME"
    else
        log_warn "Could not resolve container ID for $SERVICE_NAME, falling back to name: $SERVICE_NAME"
        SERVICE_CONTAINER_NAME="$SERVICE_NAME"
    fi
fi

# Step 3: Wait for health check with enhanced diagnostics
log_info "Step 3: Waiting for health check (timeout: ${HEALTH_CHECK_TIMEOUT}s)..."
timeout=$HEALTH_CHECK_TIMEOUT
elapsed=0
health_status="none"
last_log_check=0

while [ $elapsed -lt $timeout ]; do
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "${SERVICE_CONTAINER_NAME}" 2>/dev/null || echo "none")
    container_status=$(docker inspect --format='{{.State.Status}}' "${SERVICE_CONTAINER_NAME}" 2>/dev/null || echo "unknown")
    
    if [ "$health_status" = "healthy" ]; then
        log_info "Health check passed!"
        break
    fi
    
    if [ "$health_status" = "unhealthy" ]; then
        log_error "Health check failed! Container is unhealthy."
        log_error "Container status: $container_status"
        
        # Show health check logs if available
        health_logs=$(docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' "${SERVICE_CONTAINER_NAME}" 2>/dev/null || echo "")
        if [ -n "$health_logs" ]; then
            log_error "Health check output: $health_logs"
        fi
        
        # Show recent container logs
        log_error "Recent container logs:"
        docker logs --tail 20 "$SERVICE_CONTAINER_NAME" 2>&1 | while IFS= read -r line; do
            log_error "  $line"
        done || true
        
        log_info "Attempting rollback..."
        if perform_rollback "$PREVIOUS_TAG"; then
            log_info "Rollback successful"
        else
            log_error "Rollback failed - manual intervention required"
        fi
        exit 1
    fi
    
    # Show diagnostics every 15 seconds
    if [ $((elapsed - last_log_check)) -ge 15 ]; then
        log_info "Waiting for health check... (${elapsed}s/${timeout}s) - Status: $health_status, Container: $container_status"
        last_log_check=$elapsed
    fi
    
    sleep 5
    elapsed=$((elapsed + 5))
done

if [ "$health_status" != "healthy" ]; then
    log_error "Health check timeout! Container did not become healthy within ${timeout}s"
    log_error "Final status: $health_status"
    
    # Show diagnostics
    container_status=$(docker inspect --format='{{.State.Status}}' "${SERVICE_CONTAINER_NAME}" 2>/dev/null || echo "unknown")
    log_error "Container status: $container_status"
    log_error "Recent logs:"
    docker logs --tail 30 "$SERVICE_CONTAINER_NAME" 2>&1 | while IFS= read -r line; do
        log_error "  $line"
    done || true
    
    log_info "Attempting rollback..."
    if perform_rollback "$PREVIOUS_TAG"; then
        log_info "Rollback successful"
    else
        log_error "Rollback failed - manual intervention required"
    fi
    exit 1
fi

# Step 4: Update deployment state
log_info "Step 4: Updating deployment state..."
update_deployment_state "$SERVICE_NAME" "$IMAGE_TAG" "$PREVIOUS_TAG"
log_info "Deployment state updated: $SERVICE_NAME=$IMAGE_TAG (previous: $PREVIOUS_TAG)"

# Step 5: Switch traffic (Traefik will automatically route to new container)
log_info "Step 5: Traffic switched (Traefik auto-routing)"

# Step 6: Log deployment history
DEPLOYMENT_LOG="${DEPLOYMENT_LOG:-$(dirname "$0")/.deployment-history}"
echo "$(date -u +"%Y-%m-%d %H:%M:%S UTC") | $SERVICE_NAME | $IMAGE_TAG | SUCCESS | Previous: $PREVIOUS_TAG" >> "$DEPLOYMENT_LOG"

log_info "✅ Deployment completed successfully for $SERVICE_NAME"
log_info "Deployment logged to: $DEPLOYMENT_LOG"
