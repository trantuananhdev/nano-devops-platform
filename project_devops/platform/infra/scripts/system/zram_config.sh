#!/bin/sh
# Alpine Linux zram Setup Script
# Purpose: Configure zram swap for memory optimization
# Usage: Run as root on Alpine Linux VM
# Reference: docs-devops/04-environment-and-infrastructure/infra-setup-alpine.md

set -e

echo "=========================================="
echo "Alpine Linux zram Configuration"
echo "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Method: Use zram-init package (preferred)
echo "Configuring zram using zram-init package..."

# Check if zram-init is installed
if ! apk info -e zram-init > /dev/null 2>&1; then
    echo "Installing zram-init..."
    apk add --no-cache zram-init
fi

# Enable zram-init service
echo "Enabling zram-init service..."
rc-update add zram-init boot

# Apply configuration to zram-init
echo "Configuring zram-init for 3GB..."
cat > /etc/conf.d/zram-init <<'EOF'
load_on_start=yes
unload_on_stop=yes
num_devices=1
type0=swap
size0=3072
EOF

# Restart zram-init service to apply changes, handling potential stop failures
echo "Applying zram-init configuration..."
if rc-service zram-init status > /dev/null 2>&1; then
    echo "zram-init is already running, attempting to restart..."
    # If restart fails (often due to swapoff issues), we try to start it just in case
    rc-service zram-init restart || {
        echo "Warning: zram-init restart failed, trying to ensure it is started..."
        rc-service zram-init start || true
    }
else
    echo "zram-init is not running, starting it..."
    rc-service zram-init start
fi

# Wait a moment for zram to initialize
sleep 2

# Verify zram is active
echo "Verifying zram configuration..."
if swapon --show | grep -q zram; then
    echo "zram is active:"
    swapon --show
    echo ""
    echo "Memory status:"
    free -h
    echo ""
    echo "=========================================="
    echo "zram configuration completed successfully!"
    echo "=========================================="
else
    echo "Error: zram device not found after configuration."
    exit 1
fi
