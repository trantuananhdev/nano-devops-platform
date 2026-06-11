#!/usr/bin/env bash
# hdtv_smoke_test.sh — Post-deploy smoke checks for HDTV stack (Alpine VM)
# Usage: ./cli.sh hdtv-smoke
#        (or called from hdtv_auto_deploy.sh after migrate/seed)
set -uo pipefail

API_BASE="${HDTV_API_BASE:-http://localhost:8000/api/v1}"
CURL_OPTS=(-sf --connect-timeout 5 --max-time 15)

PASSED=0
FAILED=0
FAIL_MSG=""

log_check() {
    echo "[smoke] $*"
}

pass() {
    PASSED=$((PASSED + 1))
    log_check "✅ $1"
}

fail() {
    FAILED=$((FAILED + 1))
    FAIL_MSG="${FAIL_MSG}  • $1\n"
    log_check "❌ $1"
}

# ---------------------------------------------------------------------------
# 1/5 — Core containers running
# ---------------------------------------------------------------------------
REQUIRED_CONTAINERS=(
    hdtv-api
    hdtv-worker
    hdtv-beat
    platform-postgres
    platform-redis
)

missing=""
running=$(docker ps --format '{{.Names}}' 2>/dev/null || true)
for c in "${REQUIRED_CONTAINERS[@]}"; do
    if ! echo "$running" | grep -qx "$c"; then
        missing="${missing}${c} "
    fi
done

if [ -z "$missing" ]; then
    pass "containers running (${REQUIRED_CONTAINERS[*]})"
else
    fail "containers not running: ${missing}(run ./cli.sh hdtv-up)"
fi

# ---------------------------------------------------------------------------
# 2/5 — Health endpoint
# ---------------------------------------------------------------------------
if curl "${CURL_OPTS[@]}" -o /dev/null -w "" "${API_BASE}/health" 2>/dev/null; then
    pass "GET ${API_BASE}/health → 200"
else
    fail "GET ${API_BASE}/health failed (is hdtv-api up?)"
fi

# ---------------------------------------------------------------------------
# 3/5 — Dossiers list (T-40: paginated DossierPage with items[])
# ---------------------------------------------------------------------------
_dossiers_body=""
if _dossiers_body=$(curl "${CURL_OPTS[@]}" "${API_BASE}/dossiers" 2>/dev/null); then
    if echo "$_dossiers_body" | grep -q '"items"'; then
        pass "GET ${API_BASE}/dossiers → JSON with items"
    elif echo "$_dossiers_body" | grep -q '^\['; then
        pass "GET ${API_BASE}/dossiers → JSON array"
    else
        fail "GET ${API_BASE}/dossiers → unexpected JSON shape"
    fi
else
    fail "GET ${API_BASE}/dossiers failed"
fi

# ---------------------------------------------------------------------------
# 4/5 — Agent metrics
# ---------------------------------------------------------------------------
_metrics_body=""
if _metrics_body=$(curl "${CURL_OPTS[@]}" "${API_BASE}/agent/metrics" 2>/dev/null); then
    if echo "$_metrics_body" | grep -q 'plan_revision_rate'; then
        pass "GET ${API_BASE}/agent/metrics → plan_revision_rate present"
    else
        fail "GET ${API_BASE}/agent/metrics → missing plan_revision_rate"
    fi
else
    fail "GET ${API_BASE}/agent/metrics failed"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
TOTAL=$((PASSED + FAILED))
echo ""
if [ "$FAILED" -eq 0 ]; then
    echo "[smoke] ✅ ${PASSED}/${TOTAL} checks passed"
    exit 0
fi

echo "[smoke] ❌ ${PASSED}/${TOTAL} checks passed — failures:"
printf "$FAIL_MSG"
exit 1
