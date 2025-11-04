#!/usr/bin/env bash
# Post-deployment smoke test for the health-api service
# Verifies basic service health and metrics endpoints via Traefik routing.
#
# This script is designed to be run AFTER a successful deployment of health-api.
# It does not mutate runtime state; it only issues HTTP requests.
#
# Expected environment (defaults provided for common cases):
#   SERVICE_NAME   - Logical service name (default: health-api)
#   BASE_URL       - Base URL for the service (default: http://$SERVICE_NAME.localhost)
#
# Exit codes:
#   0 - All smoke checks passed
#   1 - One or more checks failed

set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-health-api}"
BASE_URL="${BASE_URL:-http://${SERVICE_NAME}.localhost}"

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

fail=0

log_info "Starting smoke tests for service: ${SERVICE_NAME}"
log_info "Base URL: ${BASE_URL}"

###############################################################################
# 1. Health endpoint check
###############################################################################

log_info "Checking /health endpoint..."
if ! output="$(curl -fsS "${BASE_URL}/health" 2>&1)"; then
  log_error "Health endpoint check failed: ${output}"
  fail=1
else
  log_info "Health endpoint responded successfully"
  # Best-effort JSON content check without requiring jq
  if echo "${output}" | grep -q '"status"' && echo "${output}" | grep -qi 'healthy'; then
    log_info "Health payload indicates service is healthy"
  else
    log_warn "Health payload does not clearly indicate 'healthy' status; response: ${output}"
  fi
fi

###############################################################################
# 2. Metrics endpoint check
###############################################################################

log_info "Checking /metrics endpoint..."
if ! metrics_output="$(curl -fsS "${BASE_URL}/metrics" 2>&1 | head -n 50)"; then
  log_error "Metrics endpoint check failed: ${metrics_output}"
  fail=1
else
  log_info "Metrics endpoint responded successfully"
  if echo "${metrics_output}" | grep -q 'health_api_requests_total'; then
    log_info "Found health_api_requests_total metric"
  else
    log_warn "Did not find health_api_requests_total metric in first 50 lines of metrics output"
  fi
fi

###############################################################################
# 3. Summary
###############################################################################

if [ "${fail}" -ne 0 ]; then
  log_error "Smoke tests for ${SERVICE_NAME} FAILED"
  exit 1
fi

log_info "✅ Smoke tests for ${SERVICE_NAME} PASSED"
exit 0

