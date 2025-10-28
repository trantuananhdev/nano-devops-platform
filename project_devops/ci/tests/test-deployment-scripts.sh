#!/usr/bin/env bash
# Integration tests for deployment scripts (deploy.sh and rollback.sh)
# Validates script syntax, environment variable handling, and error paths

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPTS_DIR="${ROOT_DIR}/project_devops/platform/ops/deployment"
DEPLOY_SCRIPT="${SCRIPTS_DIR}/deploy.sh"
ROLLBACK_SCRIPT="${SCRIPTS_DIR}/rollback.sh"
COMPOSE_FILE="${ROOT_DIR}/project_devops/platform/composition/docker-compose.yml"

test_count=0
pass_count=0
fail_count=0

test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((test_count++))
    ((pass_count++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((test_count++))
    ((fail_count++))
}

test_section() {
    echo ""
    echo -e "${YELLOW}===== $1 =====${NC}"
}

# Test 1: Script files exist
test_section "Script Existence"
if [ -f "$DEPLOY_SCRIPT" ]; then
    test_pass "deploy.sh exists"
else
    test_fail "deploy.sh not found"
fi

if [ -f "$ROLLBACK_SCRIPT" ]; then
    test_pass "rollback.sh exists"
else
    test_fail "rollback.sh not found"
fi

# Test 2: Scripts are executable
test_section "Script Permissions"
if [ -x "$DEPLOY_SCRIPT" ]; then
    test_pass "deploy.sh is executable"
else
    test_fail "deploy.sh is not executable"
fi

if [ -x "$ROLLBACK_SCRIPT" ]; then
    test_pass "rollback.sh is executable"
else
    test_fail "rollback.sh is not executable"
fi

# Test 3: Script syntax validation (bash -n)
test_section "Script Syntax Validation"
if bash -n "$DEPLOY_SCRIPT" 2>&1; then
    test_pass "deploy.sh syntax is valid"
else
    test_fail "deploy.sh has syntax errors"
fi

if bash -n "$ROLLBACK_SCRIPT" 2>&1; then
    test_pass "rollback.sh syntax is valid"
else
    test_fail "rollback.sh has syntax errors"
fi

# Test 4: Required environment variables validation
test_section "Environment Variable Validation"

# Check deploy.sh validates SERVICE_NAME
if grep -q 'if \[ -z "\$SERVICE_NAME" \]' "$DEPLOY_SCRIPT" || grep -q 'SERVICE_NAME.*required' "$DEPLOY_SCRIPT"; then
    test_pass "deploy.sh validates SERVICE_NAME is required"
else
    test_fail "deploy.sh should validate SERVICE_NAME is required"
fi

# Check deploy.sh validates COMPOSE_FILE exists
if grep -q 'if \[ ! -f "\$COMPOSE_FILE" \]' "$DEPLOY_SCRIPT" || grep -q 'Docker Compose file not found' "$DEPLOY_SCRIPT"; then
    test_pass "deploy.sh validates COMPOSE_FILE exists"
else
    test_fail "deploy.sh should validate COMPOSE_FILE exists"
fi

# Check rollback.sh validates SERVICE_NAME
if grep -q 'if \[ -z "\$SERVICE_NAME" \]' "$ROLLBACK_SCRIPT" || grep -q 'SERVICE_NAME.*required' "$ROLLBACK_SCRIPT"; then
    test_pass "rollback.sh validates SERVICE_NAME is required"
else
    test_fail "rollback.sh should validate SERVICE_NAME is required"
fi

# Check rollback.sh validates PREVIOUS_IMAGE_TAG
if grep -q 'if \[ -z "\$PREVIOUS_IMAGE_TAG" \]' "$ROLLBACK_SCRIPT" || grep -q 'PREVIOUS_IMAGE_TAG.*required' "$ROLLBACK_SCRIPT"; then
    test_pass "rollback.sh validates PREVIOUS_IMAGE_TAG is required"
else
    test_fail "rollback.sh should validate PREVIOUS_IMAGE_TAG is required"
fi

# Check rollback.sh validates COMPOSE_FILE exists
if grep -q 'if \[ ! -f "\$COMPOSE_FILE" \]' "$ROLLBACK_SCRIPT" || grep -q 'Docker Compose file not found' "$ROLLBACK_SCRIPT"; then
    test_pass "rollback.sh validates COMPOSE_FILE exists"
else
    test_fail "rollback.sh should validate COMPOSE_FILE exists"
fi

# Test 5: Docker Compose file validation
test_section "Docker Compose File Validation"
if [ -f "$COMPOSE_FILE" ]; then
    test_pass "docker-compose.yml exists"
    
# Validate docker compose syntax if available
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    if docker compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
            test_pass "docker-compose.yml syntax is valid"
        else
            test_fail "docker-compose.yml has syntax errors"
        fi
elif command -v docker-compose >/dev/null 2>&1; then
    if docker-compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
        test_pass "docker-compose.yml syntax is valid"
    else
        test_fail "docker-compose.yml has syntax errors"
    fi
    else
    echo -e "${YELLOW}⚠${NC} docker compose not available, skipping compose validation"
    fi
else
    test_fail "docker-compose.yml not found"
fi

# Test 6: Script structure validation
test_section "Script Structure Validation"

# Check deploy.sh has required functions
if grep -q "log_info\|log_error\|log_warn" "$DEPLOY_SCRIPT"; then
    test_pass "deploy.sh has logging functions"
else
    test_fail "deploy.sh missing logging functions"
fi

# Check deploy.sh has health check logic
if grep -q "health_status\|Health check" "$DEPLOY_SCRIPT"; then
    test_pass "deploy.sh has health check logic"
else
    test_fail "deploy.sh missing health check logic"
fi

# Check rollback.sh has required functions
if grep -q "log_info\|log_error\|log_warn" "$ROLLBACK_SCRIPT"; then
    test_pass "rollback.sh has logging functions"
else
    test_fail "rollback.sh missing logging functions"
fi

# Check rollback.sh has health check logic
if grep -q "health_status\|Health check" "$ROLLBACK_SCRIPT"; then
    test_pass "rollback.sh has health check logic"
else
    test_fail "rollback.sh missing health check logic"
fi

# Test 7: Default values validation
test_section "Default Values Validation"

# Check deploy.sh has default values
if grep -q 'COMPOSE_FILE="${COMPOSE_FILE:-' "$DEPLOY_SCRIPT"; then
    test_pass "deploy.sh has default COMPOSE_FILE"
else
    test_fail "deploy.sh missing default COMPOSE_FILE"
fi

if grep -q 'IMAGE_TAG="${IMAGE_TAG:-latest}"' "$DEPLOY_SCRIPT"; then
    test_pass "deploy.sh has default IMAGE_TAG"
else
    test_fail "deploy.sh missing default IMAGE_TAG"
fi

if grep -q 'REGISTRY="${REGISTRY:-ghcr.io}"' "$DEPLOY_SCRIPT"; then
    test_pass "deploy.sh has default REGISTRY"
else
    test_fail "deploy.sh missing default REGISTRY"
fi

# Check rollback.sh has default values
if grep -q 'COMPOSE_FILE="${COMPOSE_FILE:-' "$ROLLBACK_SCRIPT"; then
    test_pass "rollback.sh has default COMPOSE_FILE"
else
    test_fail "rollback.sh missing default COMPOSE_FILE"
fi

if grep -q 'REGISTRY="${REGISTRY:-ghcr.io}"' "$ROLLBACK_SCRIPT"; then
    test_pass "rollback.sh has default REGISTRY"
else
    test_fail "rollback.sh missing default REGISTRY"
fi

# Test 8: Error handling validation
test_section "Error Handling Validation"

# Check deploy.sh has error handling
if grep -q "set -euo pipefail" "$DEPLOY_SCRIPT"; then
    test_pass "deploy.sh uses strict error handling (set -euo pipefail)"
else
    test_fail "deploy.sh missing strict error handling"
fi

# Check rollback.sh has error handling
if grep -q "set -euo pipefail" "$ROLLBACK_SCRIPT"; then
    test_pass "rollback.sh uses strict error handling (set -euo pipefail)"
else
    test_fail "rollback.sh missing strict error handling"
fi

# Test 9: GitOps compliance validation
test_section "GitOps Compliance"

# Check scripts don't modify files directly (should use docker-compose)
if ! grep -q "docker.*commit\|docker.*tag.*push" "$DEPLOY_SCRIPT" 2>/dev/null; then
    test_pass "deploy.sh follows GitOps principles (no direct image manipulation)"
else
    test_fail "deploy.sh may violate GitOps principles"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total tests: $test_count"
echo -e "${GREEN}Passed: $pass_count${NC}"
if [ $fail_count -gt 0 ]; then
    echo -e "${RED}Failed: $fail_count${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: $fail_count${NC}"
    exit 0
fi
