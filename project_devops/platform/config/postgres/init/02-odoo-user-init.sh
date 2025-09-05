#!/bin/bash
set -euo pipefail

echo "[initdb] Creating dedicated role 'odoo' and database 'odoo' (if missing)"

ODOO_PW_FILE="/run/secrets/odoo_db_password"
if [ -f "$ODOO_PW_FILE" ]; then
  ODOO_PW="$(cat "$ODOO_PW_FILE")"
else
  echo "[initdb] WARNING: odoo_db_password secret not found; using fallback password for dev only"
  ODOO_PW="devadmin"
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'odoo') THEN
      CREATE ROLE odoo LOGIN PASSWORD '${ODOO_PW}';
   ELSE
      ALTER ROLE odoo WITH LOGIN PASSWORD '${ODOO_PW}';
   END IF;
END
\$do\$;
EOSQL

DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='odoo'" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" || echo "")
if [ "$DB_EXISTS" != "1" ]; then
  echo "[initdb] Creating database 'odoo' owned by role 'odoo'"
  createdb -O odoo odoo --username "$POSTGRES_USER" --maintenance-db "$POSTGRES_DB"
else
  echo "[initdb] Database 'odoo' already exists, skipping"
fi
