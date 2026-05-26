#!/usr/bin/env bash
# Smoke test — Phase 4 CRM demo UI + read API
set -euo pipefail

INGEST_URL="${CRM_INGEST_URL:-https://crm-ingest.nano.platform}"
DEMO_URL="${CRM_DEMO_URL:-https://crm-demo.nano.platform}"
CURL_OPTS=(-sk --connect-timeout 5 --max-time 20)

echo "[smoke] Demo UI reachable"
curl "${CURL_OPTS[@]}" "${DEMO_URL}/" | head -1 | grep -qiE 'html|<!DOCTYPE' 

echo "[smoke] Read API metrics"
curl "${CURL_OPTS[@]}" "${INGEST_URL}/api/v1/metrics/summary" | grep -q 'processed_24h'

echo "[smoke] Demo send proxy"
MSG=$(curl "${CURL_OPTS[@]}" -X POST "${INGEST_URL}/api/v1/demo/send" \
  -H "Content-Type: application/json" \
  -d '{"channel":"shopee","template_id":"shopee_delay_ms"}')
echo "$MSG" | grep -q accepted

echo "[smoke] Phase 4 demo checks passed"
