#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)"

cd "$ROOT_DIR/platform/composition"

docker compose -f docker-compose.apps.yml up -d --build teencare-lms-api teencare-lms-web

echo "TeenCare LMS API: http://<host-ip>:8008/docs"
echo "TeenCare LMS Web: http://<host-ip>:5173"
