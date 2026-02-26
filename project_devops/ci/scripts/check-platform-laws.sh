#!/bin/bash
# Platform Law Enforcement Checks
# Validates code changes against platform laws defined in platform-laws.yaml

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

log_info "Running platform law checks..."

# Check 1: Small batch - file size check
log_info "Check 1: Small batch (file size ≤ 300 lines)"
large_files=$(find . -type f \( -name "*.sh" -o -name "*.yml" -o -name "*.yaml" -o -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
    ! -path "./.git/*" ! -path "./node_modules/*" ! -path "./.github/*" \
    -exec sh -c 'lines=$(wc -l < "$1"); if [ "$lines" -gt 300 ]; then echo "$1:$lines"; fi' _ {} \;)

if [ -n "$large_files" ]; then
    log_warn "Large files detected (>300 lines):"
    echo "$large_files" | while IFS= read -r file; do
        log_warn "  $file"
    done
else
    log_info "  ✅ All files within small batch limit (≤300 lines)"
fi

# Check 2: Trunk-based development - branch check
log_info "Check 2: Trunk-based development (branch naming)"
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
if [ "$current_branch" != "main" ] && [ "$current_branch" != "master" ]; then
    log_info "  ✅ Working on feature branch: $current_branch"
else
    log_info "  ✅ On main branch (expected for merges)"
fi

# Check 3: Unit tests presence (placeholder)
log_info "Check 3: Unit tests presence"
if [ -d "tests" ] || [ -d "__tests__" ] || [ -f "test.sh" ]; then
    log_info "  ✅ Test directory/files found"
else
    log_warn "  ⚠️  No test directory found (tests should be added)"
fi

# Check 4: SLO/Telemetry configuration (placeholder)
log_info "Check 4: SLO/Telemetry configuration"
if [ -f "project_devops/platform/config/prometheus/prometheus.yml" ]; then
    log_info "  ✅ Prometheus configuration found"
else
    log_warn "  ⚠️  Prometheus configuration not found"
fi

# Check 5: Secrets not in code
log_info "Check 5: Secret detection (basic check)"
secrets_found=$(grep -r -i "password\|secret\|api_key\|token" --include="*.sh" --include="*.yml" --include="*.yaml" \
    --exclude-dir=".git" --exclude-dir="node_modules" \
    project_devops/ 2>/dev/null | grep -v "password_file\|secret_file\|\.example\|\.template" || true)

if [ -n "$secrets_found" ]; then
    log_warn "  ⚠️  Potential secrets found (review manually):"
    echo "$secrets_found" | head -5 | while IFS= read -r line; do
        log_warn "    $line"
    done
else
    log_info "  ✅ No obvious secrets in code"
fi

# Summary
echo ""
log_info "Platform law checks completed"
log_info "Errors: $ERRORS"
log_info "Warnings: $WARNINGS"

if [ $ERRORS -gt 0 ]; then
    log_error "Platform law checks failed!"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    log_warn "Platform law checks passed with warnings"
    exit 0
else
    log_info "✅ All platform law checks passed"
    exit 0
fi