#!/bin/sh
# Alpine Linux mkcert Setup Script (Idempotent)

set -e

echo "=========================================="
echo "Alpine Linux mkcert Setup"
echo "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Install mkcert if not already installed
if ! command -v mkcert > /dev/null 2>&1; then
    echo "Installing mkcert..."
    # Ensure GOPATH is set for go install
    export GOPATH=$(go env GOPATH)
    if [ -z "$GOPATH" ]; then
        export GOPATH="$HOME/go"
        mkdir -p "$GOPATH"
    fi
    export PATH="$PATH:$GOPATH/bin"

    go install filippo.io/mkcert@latest || { echo "Error: Failed to install mkcert."; exit 1; }
    
    # Ensure mkcert binary is in a standard PATH location
    if [ -f "$GOPATH/bin/mkcert" ]; then
        cp "$GOPATH/bin/mkcert" /usr/local/bin/mkcert || { echo "Error: Failed to copy mkcert to /usr/local/bin."; exit 1; }
    else
        echo "Error: mkcert binary not found after go install."
        exit 1
    fi

    mkcert -install || { echo "Error: Failed to install mkcert root CA."; exit 1; }
    echo "mkcert installed and root CA created."
else
    echo "mkcert is already installed."
    # Ensure root CA is installed if mkcert exists but CA isn't installed
    if ! mkcert -check-install > /dev/null 2>&1; then
        echo "Installing mkcert root CA..."
        mkcert -install || { echo "Error: Failed to install mkcert root CA."; exit 1; }
        echo "mkcert root CA created."
    else
        echo "mkcert root CA is already installed."
    fi
fi

echo "=========================================="
echo "mkcert setup completed successfully!"
echo "=========================================="
