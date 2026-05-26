#!/usr/bin/env bash
# Smoke test — all Traefik-routed apps over HTTPS
set -euo pipefail

CURL_OPTS=(-sk --connect-timeout 5 --max-time 20 -o /dev/null -w "%{http_code}")

fail() { echo "[smoke-https] FAIL: $*" >&2; exit 1; }

check() {
  local name="$1" url="$2" expect="${3:-200}"
  local code
  code=$(curl "${CURL_OPTS[@]}" "$url")
  if [ "$code" != "$expect" ] && [ "$expect" != "any" ]; then
    if [ "$expect" = "2xx" ] && [[ "$code" =~ ^2 ]]; then
      echo "[smoke-https] OK  ${name} (${code})"
      return 0
    fi
    fail "${name} ${url} → HTTP ${code} (expected ${expect})"
  fi
  echo "[smoke-https] OK  ${name} (${code})"
}

echo "[smoke-https] === Platform app HTTPS endpoints ==="

if [ ! -f /opt/platform/config/traefik/certs/nano.platform.crt ]; then
  fail "Missing TLS cert — run: ./cli.sh certs"
fi

declare -a TARGETS=(
  "health-api|https://health.nano.platform/health"
  "data-api|https://data.nano.platform/health"
  "aggregator-api|https://aggregator.nano.platform/health"
  "user-api|https://user.nano.platform/health"
  "faulty-service|https://faulty.nano.platform/status"
  "agentic-ai|https://ai.nano.platform/healthz"
  "crm-ingest|https://crm-ingest.nano.platform/health"
  "crm-demo-ui|https://crm-demo.nano.platform/|2xx"
  "grafana|https://grafana.nano.platform/login|2xx"
  "prometheus|https://prometheus.nano.platform/-/healthy|200"
)

for entry in "${TARGETS[@]}"; do
  IFS='|' read -r name url expect <<< "$entry"
  expect="${expect:-200}"
  check "$name" "$url" "$expect"
done

echo "[smoke-https] All HTTPS app checks passed"
