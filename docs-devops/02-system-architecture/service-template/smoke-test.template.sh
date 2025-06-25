#!/bin/bash
# Smoke test script for [SERVICE_NAME] service
# [DESCRIPTION]

set -e

SERVICE_URL="${[SERVICE_NAME_UPPER]_API_URL:-http://[SERVICE_NAME].localhost}"
TIMEOUT="${TIMEOUT:-5}"

echo "=========================================="
echo "[SERVICE_NAME] API Smoke Test"
echo "=========================================="
echo "Service URL: $SERVICE_URL"
echo ""

# Test 1: Health check
echo "[TEST 1] Health check..."
health_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$SERVICE_URL/health" || echo -e "\n000")
health_body=$(echo "$health_response" | head -n -1)
health_code=$(echo "$health_response" | tail -n 1)

if [ "$health_code" != "200" ]; then
    echo "❌ FAILED: Health check returned status $health_code"
    echo "Response: $health_body"
    exit 1
fi

echo "✅ Health check passed"
echo "Response: $health_body"
echo ""

# Test 2: Metrics endpoint
echo "[TEST 2] Metrics endpoint..."
metrics_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$SERVICE_URL/metrics" || echo "000")

if [ "$metrics_code" != "200" ]; then
    echo "❌ FAILED: Metrics endpoint returned status $metrics_code"
    exit 1
fi

echo "✅ Metrics endpoint accessible"
echo ""

# Add custom tests here
# [CUSTOM_TESTS]

echo "=========================================="
echo "✅ All smoke tests passed!"
echo "=========================================="
