#!/bin/bash
set -euo pipefail

echo "[initdb] Creating dedicated role 'hdtv_user' and database 'hdtv_db' (if missing)"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hdtv_user') THEN
      CREATE ROLE hdtv_user LOGIN PASSWORD 'changeme_hdtv';
   ELSE
      ALTER ROLE hdtv_user WITH LOGIN PASSWORD 'changeme_hdtv';
   END IF;
END
\$do\$;
EOSQL

DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='hdtv_db'" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" || echo "")
if [ "$DB_EXISTS" != "1" ]; then
  echo "[initdb] Creating database 'hdtv_db' owned by role 'hdtv_user'"
  createdb -O hdtv_user hdtv_db --username "$POSTGRES_USER" --maintenance-db "$POSTGRES_DB"
else
  echo "[initdb] Database 'hdtv_db' already exists, skipping"
fi

# In Postgres 15+, the public schema no longer has default CREATE permissions for everyone.
# Granting CREATE on public to the owner is often needed for extensions like pgcrypto.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "hdtv_db" <<-EOSQL
    GRANT ALL ON SCHEMA public TO hdtv_user;
    ALTER SCHEMA public OWNER TO hdtv_user;
EOSQL