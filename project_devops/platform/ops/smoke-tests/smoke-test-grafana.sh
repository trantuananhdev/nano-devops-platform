#!/usr/bin/env bash
# Smoke test — Grafana via Traefik HTTPS
set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-https://grafana.nano.platform}"
CURL_OPTS=(-sk --connect-timeout 5 --max-time 15)

echo "[smoke] Grafana HTTPS (${GRAFANA_URL})"
code=$(curl "${CURL_OPTS[@]}" -o /dev/null -w "%{http_code}" "${GRAFANA_URL}/login")
if [ "$code" != "200" ] && [ "$code" != "302" ]; then
  echo "[smoke] FAIL: expected 200/302, got HTTP ${code}"
  echo "Hint: Traefik router needs entrypoints=websecure + tls=true (see docker-compose.observability.yml)"
  exit 1
fi
echo "[smoke] Grafana login page OK (HTTP ${code})"

echo "[smoke] Container platform-grafana running?"
docker ps --format '{{.Names}}' | grep -q '^platform-grafana$' || {
  echo "[smoke] FAIL: platform-grafana not running — ./cli.sh up"
  exit 1
}
echo "[smoke] All checks passed"
