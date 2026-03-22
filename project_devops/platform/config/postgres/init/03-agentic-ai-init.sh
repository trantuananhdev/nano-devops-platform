#!/bin/bash
set -euo pipefail

echo "[initdb] Creating dedicated role 'agentic_ai' and database 'agentic_ai_db' (if missing)"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'agentic_ai') THEN
      CREATE ROLE agentic_ai LOGIN PASSWORD 'devadmin';
   ELSE
      ALTER ROLE agentic_ai WITH LOGIN PASSWORD 'devadmin';
   END IF;
END
\$do\$;
EOSQL

DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='agentic_ai_db'" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" || echo "")
if [ "$DB_EXISTS" != "1" ]; then
  echo "[initdb] Creating database 'agentic_ai_db' owned by role 'agentic_ai'"
  createdb -O agentic_ai agentic_ai_db --username "$POSTGRES_USER" --maintenance-db "$POSTGRES_DB"
else
  echo "[initdb] Database 'agentic_ai_db' already exists, skipping"
fi

# In Postgres 15+, the public schema no longer has default CREATE permissions for everyone.
# Granting CREATE on public to the owner is often needed for extensions like pgcrypto.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "agentic_ai_db" <<-EOSQL
    GRANT ALL ON SCHEMA public TO agentic_ai;
    ALTER SCHEMA public OWNER TO agentic_ai;
EOSQL
