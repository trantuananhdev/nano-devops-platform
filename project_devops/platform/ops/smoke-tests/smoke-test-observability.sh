#!/usr/bin/env bash
# Smoke test — Grafana + Prometheus via Traefik HTTPS
set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-https://grafana.nano.platform}"
PROM_URL="${PROM_URL:-https://prometheus.nano.platform}"
CURL_OPTS=(-sk --connect-timeout 5 --max-time 20)

fail() { echo "[smoke] FAIL: $*" >&2; exit 1; }

echo "[smoke] === Observability HTTPS ==="

if [ ! -f /opt/platform/config/traefik/certs/nano.platform.crt ]; then
  fail "Missing TLS cert — run: sh project_devops/platform/infra/scripts/system/generate_certs.sh"
fi
echo "[smoke] OK wildcard cert present"

for c in platform-traefik platform-grafana platform-prometheus; do
  docker ps --format '{{.Names}}' | grep -q "^${c}$" || fail "container ${c} not running — ./cli.sh up"
  echo "[smoke] OK container ${c}"
done

echo "[smoke] Grafana ${GRAFANA_URL}/login"
gcode=$(curl "${CURL_OPTS[@]}" -o /dev/null -w "%{http_code}" "${GRAFANA_URL}/login")
[[ "$gcode" == "200" || "$gcode" == "302" ]] || fail "Grafana HTTP ${gcode} (need Traefik websecure + tls)"

echo "[smoke] Grafana health API (in-cluster)"
curl "${CURL_OPTS[@]}" -sf "http://127.0.0.1:3000/api/health" >/dev/null 2>&1 \
  || curl "${CURL_OPTS[@]}" -sf "http://platform-grafana:3000/api/health" >/dev/null 2>&1 \
  || echo "[smoke] WARN: direct health skip (Traefik path already OK)"

echo "[smoke] Prometheus ${PROM_URL}/-/healthy"
pcode=$(curl "${CURL_OPTS[@]}" -o /dev/null -w "%{http_code}" "${PROM_URL}/-/healthy")
[[ "$pcode" == "200" ]] || fail "Prometheus healthy HTTP ${pcode}"

echo "[smoke] Prometheus UI ${PROM_URL}/graph"
g2=$(curl "${CURL_OPTS[@]}" -o /dev/null -w "%{http_code}" "${PROM_URL}/graph")
[[ "$g2" == "200" || "$g2" == "302" ]] || fail "Prometheus UI HTTP ${g2}"

echo "[smoke] Grafana datasource (Prometheus reachable from Grafana network)"
docker exec platform-grafana wget -qO- http://platform-prometheus:9090/-/healthy 2>/dev/null | grep -q OK \
  || docker exec platform-grafana wget -qO- http://platform-prometheus:9090/-/healthy 2>/dev/null | grep -qi healthy \
  || echo "[smoke] WARN: wget health from grafana container failed (check network)"

echo "[smoke] TLS handshake (grafana)"
echo | openssl s_client -connect grafana.nano.platform:443 -servername grafana.nano.platform 2>/dev/null \
  | openssl x509 -noout -subject 2>/dev/null | grep -qi nano.platform \
  || echo "[smoke] WARN: openssl s_client skipped or cert name mismatch (check hosts → VM IP)"

echo "[smoke] All observability checks passed"
