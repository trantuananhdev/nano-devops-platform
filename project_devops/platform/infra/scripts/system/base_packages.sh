#!/bin/sh
# Alpine Linux Base Packages Setup Script (Idempotent)

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
log_info "Alpine Linux Base Packages Setup"
log_info "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Update package index
log_info "Updating package index..."
apk update

# Define packages to be installed
packages="docker docker-cli-compose git bash curl ca-certificates htop zram-init openssh sudo go shadow"
packages_to_install=""

# Check which packages are already installed
for pkg in $packages; do
    if ! apk -e info "$pkg" > /dev/null 2>&1; then
        packages_to_install="$packages_to_install $pkg"
    else
        log_info "Package '$pkg' is already installed."
    fi
done

# Install only the missing packages
if [ -n "$packages_to_install" ]; then
    log_info "Installing missing packages:$packages_to_install..."
    apk add --no-cache $packages_to_install
else
    log_info "All essential packages are already installed."
fi

log_info "=========================================="
log_info "Base packages setup completed successfully!"
log_info "=========================================="
