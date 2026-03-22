#!/bin/bash
# Smoke Test for AI-Powered Development (AI Agent)
# This script validates the basic health and authentication of the AI Agent.

API_URL="https://ai.nano.platform"

set -e

# Define root directory (relative to this script)
ROOT_DIR="$(cd "$(dirname "$0")/../../../../.." && pwd)"
APP_DIR="${ROOT_DIR}/project_devops/apps/digital-fte-platform/digital-fte-platform"

echo "[INFO] Running Smoke Test for Digital FTE Platform..."

if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    # Note: In a real CI environment, dependencies should be pre-installed
    # or run within a container. For local platform validation, we run npm directly.
    if command -v npm >/dev/null 2>&1; then
        npm install --no-audit --no-fund
        npm run smoke-test
    else
        echo "[WARN] npm not found, skipping smoke test execution."
    fi
else
    echo "[ERROR] Application directory not found: $APP_DIR"
    exit 1
fi
