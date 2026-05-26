#!/usr/bin/env bash
# Smoke test — CRM ingestion API (run inside lab VM after ./cli.sh up)
set -euo pipefail

BASE_URL="${CRM_INGEST_URL:-https://crm-ingest.nano.platform}"
CURL_OPTS=(-sk --connect-timeout 5 --max-time 15)

echo "[smoke] CRM ingestion health"
health=$(curl "${CURL_OPTS[@]}" "${BASE_URL}/health")
echo "$health" | grep -q '"status":"healthy"' || echo "$health" | grep -q '"status": "healthy"'
echo "[smoke] Health OK"

MSG_ID="smoke-$(date +%s)"
echo "[smoke] POST generic webhook message_id=${MSG_ID}"
resp=$(curl "${CURL_OPTS[@]}" -X POST "${BASE_URL}/webhook/generic" \
  -H "Content-Type: application/json" \
  -d "{\"message_id\":\"${MSG_ID}\",\"raw_text\":\"Smoke test inquiry serum price\",\"channel\":\"generic\"}")
echo "$resp" | grep -q '"status":"accepted"' || echo "$resp" | grep -q '"status": "accepted"'
echo "[smoke] Webhook accepted"

echo "[smoke] POST Shopee webhook"
sp_id="smoke-sp-$(date +%s)"
curl "${CURL_OPTS[@]}" -X POST "${BASE_URL}/webhook/shopee" \
  -H "Content-Type: application/json" \
  -d "{\"message_id\":\"${sp_id}\",\"raw_text\":\"Boleh check order status?\",\"channel\":\"shopee\",\"order_id\":\"241234567890\",\"locale\":\"ms-MY\"}" \
  | grep -q accepted

echo "[smoke] Read API metrics summary"
curl "${CURL_OPTS[@]}" "${BASE_URL}/api/v1/metrics/summary" | grep -q processed_24h

echo "[smoke] Metrics endpoint"
curl "${CURL_OPTS[@]}" "${BASE_URL}/metrics" 2>/dev/null | head -5 || true
echo "[smoke] All checks passed"
