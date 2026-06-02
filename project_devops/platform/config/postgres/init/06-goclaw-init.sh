#!/bin/bash
set -euo pipefail

echo "[initdb] Creating goclaw role and database 'goclaw_db' (if missing)"

# Create role idempotently (DO block — same pattern as 04-crm-init.sh)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'goclaw') THEN
      CREATE ROLE goclaw LOGIN PASSWORD 'devadmin';
   ELSE
      ALTER ROLE goclaw WITH LOGIN PASSWORD 'devadmin';
   END IF;
END
\$do\$;
EOSQL

# Create database only if it doesn't already exist
DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='goclaw_db'" \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" || echo "")
if [ "$DB_EXISTS" != "1" ]; then
  echo "[initdb] Creating database 'goclaw_db' owned by role 'goclaw'"
  createdb -O goclaw goclaw_db --username "$POSTGRES_USER" --maintenance-db "$POSTGRES_DB"
else
  echo "[initdb] Database 'goclaw_db' already exists, skipping"
fi

# Grant schema privileges — connect directly to goclaw_db
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "goclaw_db" <<-EOSQL
    GRANT ALL ON SCHEMA public TO goclaw;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO goclaw;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO goclaw;
EOSQL

echo "[initdb] goclaw database ready"
