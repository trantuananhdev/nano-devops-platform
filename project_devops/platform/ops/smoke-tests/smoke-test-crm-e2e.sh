#!/usr/bin/env bash
# E2E smoke — traffic burst + worker processing + auto-reply/alerts
set -euo pipefail

INGEST_URL="${CRM_INGEST_URL:-https://crm-ingest.nano.platform}"
CURL_OPTS=(-sk --connect-timeout 5 --max-time 60)

echo "[e2e] Traffic burst: single_hot_lead"
burst=$(curl "${CURL_OPTS[@]}" -X POST "${INGEST_URL}/api/v1/demo/traffic-burst" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"single_hot_lead"}')
echo "$burst" | grep -q burst_started
mid=$(echo "$burst" | grep -o '"message_ids":\["[^"]*"' | head -1 | sed 's/.*"\([^"]*\)".*/\1/' || true)
if [ -z "$mid" ]; then
  mid=$(echo "$burst" | grep -o '"message_id":"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)".*/\1/' || true)
fi
echo "[e2e] message_id=${mid:-unknown}"

echo "[e2e] Wait up to 90s for worker..."
for i in $(seq 1 30); do
  sleep 3
  if [ -n "${mid:-}" ]; then
    lead=$(curl "${CURL_OPTS[@]}" "${INGEST_URL}/api/v1/leads/${mid}" 2>/dev/null || echo '{}')
    if echo "$lead" | grep -q '"processed_at"'; then
      echo "[e2e] Lead processed after $((i * 3))s"
      echo "$lead" | head -c 500
      echo ""
      if echo "$lead" | grep -q '"alert_sent":true'; then
        echo "[e2e] Alert sent OK"
      fi
      if echo "$lead" | grep -q '"auto_reply_sent":true'; then
        echo "[e2e] Auto-reply sent OK"
      fi
      exit 0
    fi
  fi
done

echo "[e2e] FAIL: lead not processed in time"
exit 1
