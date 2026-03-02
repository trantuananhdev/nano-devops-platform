#!/usr/bin/env bash
# Lightweight test runner for the Nano DevOps platform repository.
# This script is intentionally minimal and will be extended as services and tests are added.

set -euo pipefail

echo "[INFO] Running CI test stage for Nano DevOps platform..."

# Placeholder: repository currently has no concrete test suites.
# The structure below is designed to be extended as the platform grows.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

run_section() {
  local name="$1"
  echo "[INFO] ===== ${name} ====="
}

run_section "Sanity checks"
echo "[INFO] Repository root: ${ROOT_DIR}"
ls -1 "${ROOT_DIR}" || true

run_section "Application/service tests"
if [ -d "${ROOT_DIR}/project_devops/apps" ]; then
  echo "[INFO] No explicit app test runner defined yet. Add per-service tests here in the future."
else
  echo "[INFO] Apps directory not found (project_devops/apps). Skipping app tests."
fi

run_section "Infrastructure / config validation"
if [ -f "${ROOT_DIR}/project_devops/platform/docker-compose.yml" ]; then
  echo "[INFO] Validating docker-compose.yml configuration..."
  if command -v docker >/dev/null 2>&1; then
    docker compose -f "${ROOT_DIR}/project_devops/platform/docker-compose.yml" config >/dev/null || {
      echo "[ERROR] docker-compose.yml validation failed"
      exit 1
    }
    echo "[INFO] docker-compose.yml validation passed"
  else
    echo "[WARN] docker not available, skipping docker-compose validation"
  fi
else
  echo "[INFO] docker-compose.yml not found. Skipping compose validation."
fi

run_section "Scripts smoke tests"
if [ -d "${ROOT_DIR}/project_devops/scripts" ]; then
  # Run shellcheck if available
  if command -v shellcheck >/dev/null 2>&1; then
    echo "[INFO] Running shellcheck on deployment scripts..."
    shellcheck "${ROOT_DIR}/project_devops/scripts/deploy.sh" "${ROOT_DIR}/project_devops/scripts/rollback.sh" || {
      echo "[WARN] shellcheck found issues (non-blocking)"
    }
  else
    echo "[INFO] shellcheck not available, skipping static analysis"
  fi
  
  # Run integration tests for deployment scripts
  if [ -f "${ROOT_DIR}/project_devops/ci/tests/test-deployment-scripts.sh" ]; then
    echo "[INFO] Running integration tests for deployment scripts..."
    bash "${ROOT_DIR}/project_devops/ci/tests/test-deployment-scripts.sh" || {
      echo "[ERROR] Deployment script integration tests failed"
      exit 1
    }
  else
    echo "[WARN] Integration test script not found: test-deployment-scripts.sh"
  fi
else
  echo "[INFO] Scripts directory not found. Skipping script smoke tests."
fi

echo "[INFO] CI test stage completed (no blocking tests defined yet)."

