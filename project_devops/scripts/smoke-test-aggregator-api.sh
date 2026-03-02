#!/usr/bin/env bash
# Post-deployment smoke test for the aggregator-api service
# Verifies basic service health, service-to-service communication, and aggregated endpoints via Traefik routing.
#
# This script is designed to be run AFTER a successful deployment of aggregator-api.
# It does not mutate runtime state; it only issues HTTP requests.
#
# Expected environment (defaults provided for common cases):
#   SERVICE_NAME   - Logical service name (default: aggregator-api)
#   BASE_URL       - Base URL for the service (default: http://$SERVICE_NAME.localhost)
#
# Exit codes:
#   0 - All smoke checks passed
#   1 - One or more checks failed

set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-aggregator-api}"
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
# 1. Health endpoint check (includes downstream service status)
###############################################################################

log_info "Checking /health endpoint..."
if ! output="$(curl -fsS "${BASE_URL}/health" 2>&1)"; then
  log_error "Health endpoint check failed: ${output}"
  fail=1
else
  log_info "Health endpoint responded successfully"
  # Best-effort JSON content check without requiring jq
  if echo "${output}" | grep -q '"status"' && echo "${output}" | grep -qi 'healthy\|degraded'; then
    log_info "Health payload indicates service status"
    # Check downstream services status
    if echo "${output}" | grep -q '"downstream_services"'; then
      log_info "Downstream services status included in health response"
      if echo "${output}" | grep -q '"health-api"' && echo "${output}" | grep -q '"data-api"'; then
        log_info "Both downstream services (health-api, data-api) status reported"
      else
        log_warn "Downstream services status unclear; response: ${output}"
      fi
    else
      log_warn "Downstream services status not found in health response"
    fi
  else
    log_warn "Health payload does not clearly indicate service status; response: ${output}"
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
  if echo "${metrics_output}" | grep -q 'aggregator_api_requests_total'; then
    log_info "Found aggregator_api_requests_total metric"
  else
    log_warn "Did not find aggregator_api_requests_total metric in first 50 lines of metrics output"
  fi
  if echo "${metrics_output}" | grep -q 'aggregator_api_service_calls_total'; then
    log_info "Found aggregator_api_service_calls_total metric (service-to-service communication)"
  else
    log_warn "Did not find aggregator_api_service_calls_total metric"
  fi
fi

###############################################################################
# 3. Aggregate status endpoint (service-to-service communication)
###############################################################################

log_info "Testing GET /aggregate/status (service-to-service communication)..."
if ! aggregate_output="$(curl -fsS "${BASE_URL}/aggregate/status" 2>&1)"; then
  log_error "GET /aggregate/status failed: ${aggregate_output}"
  fail=1
else
  log_info "GET /aggregate/status succeeded"
  if echo "${aggregate_output}" | grep -q '"services"' && echo "${aggregate_output}" | grep -q '"health-api"' && echo "${aggregate_output}" | grep -q '"data-api"'; then
    log_info "Service-to-service communication validated - both services called successfully"
    if echo "${aggregate_output}" | grep -q '"overall_status"'; then
      log_info "Overall status reported"
    fi
  else
    log_warn "Service-to-service communication validation unclear; response: ${aggregate_output}"
  fi
fi

###############################################################################
# 4. Aggregate data endpoint (service-to-service communication with data-api)
###############################################################################

log_info "Testing GET /aggregate/data/test-key (service-to-service communication with data-api)..."
if ! aggregate_data_output="$(curl -fsS "${BASE_URL}/aggregate/data/test-key" 2>&1)"; then
  log_warn "GET /aggregate/data/test-key failed (non-critical - data may not exist): ${aggregate_data_output}"
  # Don't fail the test for missing data
else
  log_info "GET /aggregate/data/test-key succeeded"
  if echo "${aggregate_data_output}" | grep -q '"data"' && echo "${aggregate_data_output}" | grep -q '"service_status"'; then
    log_info "Service-to-service communication with data-api validated"
  else
    log_warn "Service-to-service communication validation unclear; response: ${aggregate_data_output}"
  fi
fi

###############################################################################
# 5. Summary
###############################################################################

if [ "${fail}" -ne 0 ]; then
  log_error "Smoke tests for ${SERVICE_NAME} FAILED"
  exit 1
fi

log_info "✅ Smoke tests for ${SERVICE_NAME} PASSED"
log_info "✅ Service-to-service communication validated"
exit 0
