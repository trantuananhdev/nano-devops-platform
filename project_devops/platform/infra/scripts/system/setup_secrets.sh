#!/bin/sh
# Secrets generation script for the Nano DevOps Platform (Dev only)
# Purpose: Generate random secrets for development environment if they don't exist.
# Usage: Run as root.

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
log_info "Nano DevOps Platform - Secrets Generation"
log_info "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# The secrets are expected at project_devops/platform/secrets/ relative to composition/
# We need to find where the secrets directory should be based on the composition path.

COMPOSITION_PATH="$1"
if [ -z "$COMPOSITION_PATH" ]; then
    log_error "No composition path provided to setup_secrets.sh"
fi

SECRETS_DIR="$(cd "$COMPOSITION_PATH/../secrets" && pwd)"

if [ ! -d "$SECRETS_DIR" ]; then
    log_info "Creating secrets directory at $SECRETS_DIR..."
    mkdir -p "$SECRETS_DIR"
fi

# Function to generate a secret if missing
generate_secret() {
    local name="$1"
    local file="$SECRETS_DIR/$name.txt"
    if [ ! -f "$file" ]; then
        log_info "Generating secret: $name..."
        # Using openssl for strong random generation if available, otherwise fallback to urandom
        if command -v openssl >/dev/null 2>&1; then
            openssl rand -base64 32 > "$file"
        else
            tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 32 > "$file"
        fi
        chmod 600 "$file"
        # Ensure correct ownership if we can determine the user (e.g., deploy)
        if id deploy >/dev/null 2>&1; then
            chown deploy:$(id -gn deploy) "$file"
        fi
    else
        log_info "Secret already exists: $name"
    fi
}

# List of required secrets
generate_secret "postgres_password"
generate_secret "grafana_password"
generate_secret "odoo_db_password"
generate_secret "agentic_ai_jwt_secret"
generate_secret "agentic_ai_admin_key"
generate_secret "agentic_ai_openai_key"
generate_secret "agentic_ai_webhook_secret"
generate_secret "agentic_ai_gemini_key"

log_info "=========================================="
log_info "Secrets generation completed successfully!"
log_info "=========================================="
