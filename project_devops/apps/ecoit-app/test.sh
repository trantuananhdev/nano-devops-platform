#!/bin/bash
# test.sh — CI test script cho EcoIT App
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== EcoIT Backend — Syntax & Import Check ==="
cd "$SCRIPT_DIR/backend"

# Install deps
pip install -q fastapi uvicorn pydantic pydantic-settings structlog 2>/dev/null || true

# Syntax check all Python files
python -m py_compile main.py
python -m py_compile core/config.py
python -m py_compile api/v1/router.py
python -m py_compile api/v1/endpoints/hello.py
echo "✅ Syntax check passed"

# Quick import test (no DB/Redis needed)
python -c "
import sys
sys.path.insert(0, '.')
from core.config import settings
assert settings.APP_NAME, 'APP_NAME not set'
from api.v1.endpoints.hello import router
assert router, 'hello router not loaded'
print('✅ Import test passed')
print(f'   APP_NAME = {settings.APP_NAME}')
print(f'   APP_ENV  = {settings.APP_ENV}')
"

echo "=== EcoIT Frontend — File Check ==="
cd "$SCRIPT_DIR/frontend"
[ -f "index.html" ] && echo "✅ index.html exists" || (echo "❌ index.html missing"; exit 1)
[ -f "nginx.conf" ] && echo "✅ nginx.conf exists" || (echo "❌ nginx.conf missing"; exit 1)

echo ""
echo "✅ All checks passed — ready to build Docker image"
