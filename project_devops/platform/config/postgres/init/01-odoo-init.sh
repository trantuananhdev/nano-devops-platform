#!/bin/bash
set -euo pipefail

echo "[initdb] Ensuring platform_user has CREATEDB and database 'odoo' exists"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'EOSQL'
ALTER ROLE platform_user WITH CREATEDB;
EOSQL

DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='odoo'" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" || echo "")
if [ "$DB_EXISTS" != "1" ]; then
  echo "[initdb] Creating database 'odoo' owned by platform_user"
  createdb -O platform_user odoo --username "$POSTGRES_USER" --maintenance-db "$POSTGRES_DB"
else
  echo "[initdb] Database 'odoo' already exists, skipping"
fi
