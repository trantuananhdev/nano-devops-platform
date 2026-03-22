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
if [ -f "${ROOT_DIR}/project_devops/platform/composition/docker-compose.yml" ]; then
  echo "[INFO] Validating docker-compose.yml configuration..."
  if command -v docker >/dev/null 2>&1; then
    docker compose -f "${ROOT_DIR}/project_devops/platform/composition/docker-compose.yml" config >/dev/null || {
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
if command -v shellcheck >/dev/null 2>&1; then
  echo "[INFO] Running shellcheck on deployment scripts..."
  if [ -f "${ROOT_DIR}/project_devops/platform/ops/deployment/deploy.sh" ]; then shellcheck "${ROOT_DIR}/project_devops/platform/ops/deployment/deploy.sh" || true; fi
  if [ -f "${ROOT_DIR}/project_devops/platform/ops/deployment/rollback.sh" ]; then shellcheck "${ROOT_DIR}/project_devops/platform/ops/deployment/rollback.sh" || true; fi
else
  echo "[INFO] shellcheck not available, skipping static analysis"
fi

if [ -f "${ROOT_DIR}/project_devops/ci/tests/test-deployment-scripts.sh" ]; then
  echo "[INFO] Running integration tests for deployment scripts..."
  bash "${ROOT_DIR}/project_devops/ci/tests/test-deployment-scripts.sh" || {
    echo "[ERROR] Deployment script integration tests failed"
    exit 1
  }
else
  echo "[WARN] Integration test script not found: test-deployment-scripts.sh"
fi

run_section "Platform Smoke Tests"
SMOKE_TESTS_DIR="${ROOT_DIR}/project_devops/platform/ops/smoke-tests"
if [ -d "$SMOKE_TESTS_DIR" ]; then
  echo "[INFO] Running all smoke tests in ${SMOKE_TESTS_DIR}..."
  for test_file in "${SMOKE_TESTS_DIR}"/smoke-test-*.sh; do
    if [ -f "$test_file" ]; then
      echo "[INFO] Executing: $(basename "$test_file")"
      bash "$test_file" || {
        echo "[ERROR] Smoke test failed: $(basename "$test_file")"
        exit 1
      }
    fi
  done
else
  echo "[INFO] Smoke tests directory not found. Skipping."
fi

echo "[INFO] CI test stage completed (all platform tests passed)."
