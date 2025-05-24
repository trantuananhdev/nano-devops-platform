#!/bin/sh
# Alpine Linux Kernel Tuning Script
# Purpose: Configure kernel parameters for optimal performance
# Usage: Run as root on Alpine Linux VM (optional, advanced)
# Reference: docs-devops/04-environment-and-infrastructure/infra-setup-alpine.md

set -e

echo "=========================================="
echo "Alpine Linux Kernel Tuning"
echo "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Create sysctl configuration directory if it doesn't exist
mkdir -p /etc/sysctl.d

# Create platform-specific sysctl configuration
echo "Creating kernel tuning configuration..."
cat > /etc/sysctl.d/99-platform.conf <<'EOF'
# Nano DevOps Platform Kernel Tuning
# Optimized for single-node VM with 6GB RAM

# Virtual memory settings
vm.swappiness = 80
vm.vfs_cache_pressure = 100

# Network settings
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 10240 65535

# File descriptor limits (handled by limits.conf)
# These are set via /etc/security/limits.conf or systemd
EOF

# Apply sysctl settings
echo "Applying kernel tuning settings..."
sysctl -p /etc/sysctl.d/99-platform.conf

# Verify settings
echo "Verifying applied settings..."
sysctl vm.swappiness vm.vfs_cache_pressure net.ipv4.tcp_tw_reuse net.ipv4.ip_local_port_range

echo ""
echo "=========================================="
echo "Kernel tuning completed successfully!"
echo "=========================================="
echo "Note: These settings will persist across reboots"
echo "To modify, edit /etc/sysctl.d/99-platform.conf"
