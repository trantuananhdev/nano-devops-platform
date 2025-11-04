#!/bin/bash
# Pre-flight Check Script for Nano DevOps Platform
# Verifies that the environment is correctly configured before deployment or operations.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

error_count=0

check() {
    local description="$1"
    local command="${@:2}"

    printf "%-60s" "- $description"
    if eval "$command" >/dev/null 2>&1; then
        printf "[${GREEN}OK${NC}]\n"
    else
        printf "[${RED}FAIL${NC}]\n"
        error_count=$((error_count + 1))
    fi
}

echo "=========================================="
echo "Running Environment Pre-flight Checks..."
echo "=========================================="

# 1. Core Dependencies
echo "\n[+] Checking core dependencies..."
check "Docker is installed and accessible" "command -v docker"
check "Docker Compose is installed and accessible" "(docker compose version >/dev/null 2>&1) || (docker-compose version >/dev/null 2>&1)"

# 2. Configuration Files
echo "\n[+] Checking configuration files..."
check "Docker Compose configuration exists" "test -f project_devops/platform/composition/docker-compose.yml"

# 3. Backup Configuration
echo "\n[+] Checking backup script dependencies..."
check "PostgreSQL backup script exists" "test -f project_devops/platform/ops/backup/backup-postgres.sh"
check "Redis backup script exists" "test -f project_devops/platform/ops/backup/backup-redis.sh"
check "Backup orchestration script exists" "test -f project_devops/platform/ops/backup/backup-all.sh"

# Summary
echo "\n=========================================="
if [ $error_count -eq 0 ]; then
    echo "${GREEN}All pre-flight checks passed successfully!${NC}"
    exit 0
else
    echo "${RED}Found $error_count configuration issue(s). Please review the logs above.${NC}"
    exit 1
fi
