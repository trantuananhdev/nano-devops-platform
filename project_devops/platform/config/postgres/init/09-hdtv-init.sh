#!/bin/bash
set -euo pipefail

echo "[initdb] Creating dedicated role 'hdtv_user' and database 'hdtv_db' (if missing)"

# Priority: secret file → env var → default
# Secret file path (Docker secret mount in platform compose)
SECRET_FILE="/run/secrets/hdtv_postgres_password"

if [ -f "$SECRET_FILE" ] && [ -s "$SECRET_FILE" ]; then
  HDTV_PW=$(tr -d '[:space:]' < "$SECRET_FILE")
  echo "[initdb] Using password from secret file"
elif [ -n "${HDTV_POSTGRES_PASSWORD:-}" ]; then
  HDTV_PW="${HDTV_POSTGRES_PASSWORD}"
  echo "[initdb] Using password from HDTV_POSTGRES_PASSWORD env var"
else
  echo "[initdb] WARNING: No password source found, using default (dev only)"
  HDTV_PW="changeme_hdtv"
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hdtv_user') THEN
      CREATE ROLE hdtv_user LOGIN PASSWORD '${HDTV_PW}';
      RAISE NOTICE '[initdb] Created role hdtv_user';
   ELSE
      ALTER ROLE hdtv_user WITH LOGIN PASSWORD '${HDTV_PW}';
      RAISE NOTICE '[initdb] Updated password for existing role hdtv_user';
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

# Postgres 15+: public schema cần grant explicit
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "hdtv_db" <<-EOSQL
    GRANT ALL ON SCHEMA public TO hdtv_user;
    ALTER SCHEMA public OWNER TO hdtv_user;
EOSQL

echo "[initdb] hdtv_user + hdtv_db setup complete"
