#!/usr/bin/env bash
# Burst smoke — multi-channel scenario (3 messages)
set -euo pipefail

INGEST_URL="${CRM_INGEST_URL:-https://crm-ingest.nano.platform}"
CURL_OPTS=(-sk --connect-timeout 5 --max-time 60)

echo "[burst] POST multi_channel_mix"
resp=$(curl "${CURL_OPTS[@]}" -X POST "${INGEST_URL}/api/v1/demo/traffic-burst" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"multi_channel_mix"}')
echo "$resp" | grep -q burst_started
count=$(echo "$resp" | grep -o '"accepted_count":[0-9]*' | grep -o '[0-9]*')
echo "[burst] accepted_count=${count:-0}"
[ "${count:-0}" -ge 3 ] || { echo "[burst] FAIL: expected 3 accepted"; exit 1; }
echo "[burst] OK"
