#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)"

cd "$ROOT_DIR/platform/composition"

docker compose -f docker-compose.apps.yml stop teencare-lms-web teencare-lms-api
docker compose -f docker-compose.apps.yml rm -f teencare-lms-web teencare-lms-api
