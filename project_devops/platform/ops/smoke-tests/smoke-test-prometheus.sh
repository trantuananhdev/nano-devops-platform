#!/usr/bin/env bash
# Smoke test — Prometheus via Traefik HTTPS
set -euo pipefail

PROM_URL="${PROM_URL:-https://prometheus.nano.platform}"
CURL_OPTS=(-sk --connect-timeout 5 --max-time 15)

echo "[smoke] Prometheus HTTPS (${PROM_URL})"
code=$(curl "${CURL_OPTS[@]}" -o /dev/null -w "%{http_code}" "${PROM_URL}/-/healthy")
[ "$code" = "200" ] || { echo "[smoke] FAIL: healthy endpoint HTTP ${code}"; exit 1; }
echo "[smoke] Healthy OK"

docker ps --format '{{.Names}}' | grep -q '^platform-prometheus$' || {
  echo "[smoke] FAIL: platform-prometheus not running"
  exit 1
}
echo "[smoke] All checks passed"
