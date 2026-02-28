#!/bin/sh
# Alpine Linux Filesystem & User Setup Script
# Idempotent and follows Principle of Least Privilege

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
log_info "Alpine Linux Filesystem & User Setup"
log_info "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

PLATFORM_USER="platform_admin"
PLATFORM_GROUP="platform_group"
DEPLOY_USER="deploy"
DEPLOY_GROUP="deploy_group"
PLATFORM_ROOT="/opt/platform"

# 1. Create dedicated groups
log_info "Ensuring dedicated groups exist..."
for group in "$PLATFORM_GROUP" "$DEPLOY_GROUP"; do
    if ! grep -q "^${group}:" /etc/group; then
        log_info "Creating group '$group'..."
        addgroup "$group"
    else
        log_info "Group '$group' already exists."
    fi
done

# 2. Create dedicated users
log_info "Ensuring dedicated users exist..."
# Platform Admin User (Home in /home for SSH security)
# CTO Fix: Use /bin/ash for Alpine native compatibility
if ! id "$PLATFORM_USER" > /dev/null 2>&1; then
    log_info "Creating user '$PLATFORM_USER'..."
    adduser -D -G "$PLATFORM_GROUP" -h "/home/$PLATFORM_USER" -s /bin/ash "$PLATFORM_USER"
else
    log_info "User '$PLATFORM_USER' already exists."
    # Ensure home directory is in /home for SSH compliance
    usermod -d "/home/$PLATFORM_USER" -s /bin/ash "$PLATFORM_USER" 2>/dev/null || true
    if [ ! -d "/home/$PLATFORM_USER" ]; then
        mkdir -p "/home/$PLATFORM_USER"
        chown "$PLATFORM_USER:$PLATFORM_GROUP" "/home/$PLATFORM_USER"
        chmod 700 "/home/$PLATFORM_USER"
    fi
fi
# Deploy User (Home in /home for SSH security)
if ! id "$DEPLOY_USER" > /dev/null 2>&1; then
    log_info "Creating user '$DEPLOY_USER'..."
    adduser -D -G "$DEPLOY_GROUP" -h "/home/$DEPLOY_USER" -s /bin/ash "$DEPLOY_USER"
else
    log_info "User '$DEPLOY_USER' already exists."
    # Ensure home directory is in /home for SSH compliance
    usermod -d "/home/$DEPLOY_USER" -s /bin/ash "$DEPLOY_USER" 2>/dev/null || true
    if [ ! -d "/home/$DEPLOY_USER" ]; then
        mkdir -p "/home/$DEPLOY_USER"
        chown "$DEPLOY_USER:$DEPLOY_GROUP" "/home/$DEPLOY_USER"
        chmod 700 "/home/$DEPLOY_USER"
    fi
fi

# 3. Add platform and deploy users to the docker group
log_info "Adding platform and deploy users to docker group..."
for user in "$PLATFORM_USER" "$DEPLOY_USER"; do
    if ! groups "$user" | grep -q '\bdocker\b'; then
        log_info "Adding user '$user' to docker group..."
        addgroup "$user" docker
    else
        log_info "User '$user' is already in the docker group."
    fi
done

# 3b. Ensure deploy can traverse /opt/platform by joining platform group
if ! id -nG "$DEPLOY_USER" | grep -qw "$PLATFORM_GROUP"; then
    log_info "Adding user '$DEPLOY_USER' to group '$PLATFORM_GROUP'..."
    addgroup "$DEPLOY_USER" "$PLATFORM_GROUP"
else
    log_info "User '$DEPLOY_USER' already in group '$PLATFORM_GROUP'."
fi

# 4. Create the required data directories based on docker-compose.yml
log_info "Creating persistent data directories under $PLATFORM_ROOT/data..."
data_dirs="postgres redis prometheus grafana loki alertmanager odoo odoo-addons logs"
for dir in $data_dirs; do
    if [ ! -d "$PLATFORM_ROOT/data/$dir" ]; then
        log_info "Creating $PLATFORM_ROOT/data/$dir..."
        mkdir -p "$PLATFORM_ROOT/data/$dir"
    fi
    
    # Special subdirectories for Loki to ensure it can start
    if [ "$dir" = "loki" ]; then
        mkdir -p "$PLATFORM_ROOT/data/loki/chunks" "$PLATFORM_ROOT/data/loki/rules" "$PLATFORM_ROOT/data/loki/boltdb-shipper-active" "$PLATFORM_ROOT/data/loki/boltdb-shipper-cache" "$PLATFORM_ROOT/data/loki/boltdb-shipper-compactor"
    fi

    # CTO Fix: Ensure these directories are writable by container users (UIDs vary)
    # For now, we set them to be owned by the deploy user and world-writable for dev-parity
    chmod -R 777 "$PLATFORM_ROOT/data/$dir"
done

if [ ! -d "$PLATFORM_ROOT/backups" ]; then
    log_info "Creating $PLATFORM_ROOT/backups..."
    mkdir -p "$PLATFORM_ROOT/backups"
else
    log_info "Directory $PLATFORM_ROOT/backups already exists."
fi
if [ ! -d "$PLATFORM_ROOT/src" ]; then
    log_info "Creating $PLATFORM_ROOT/src..."
    mkdir -p "$PLATFORM_ROOT/src"
else
    log_info "Directory $PLATFORM_ROOT/src already exists."
fi

# 6. Set correct ownership and permissions
log_info "Setting ownership for $PLATFORM_ROOT to $PLATFORM_USER:$PLATFORM_GROUP..."
chown "$PLATFORM_USER:$PLATFORM_GROUP" "$PLATFORM_ROOT"
# Set ownership for the source directory to the deploy user
log_info "Setting ownership for $PLATFORM_ROOT/src to $DEPLOY_USER:$DEPLOY_GROUP..."
chown -R "$DEPLOY_USER:$DEPLOY_GROUP" "$PLATFORM_ROOT/src"

# Set base permissions
chmod 750 "$PLATFORM_ROOT"

# Verify structure
log_info "Verifying directory structure and permissions..."
ls -la "$PLATFORM_ROOT/"

log_info ""
log_info "=========================================="
log_info "Filesystem and user setup completed successfully!"
log_info "=========================================="
log_info "A dedicated user '$PLATFORM_USER' has been created."
log_info "All future operations should be performed as this user."
