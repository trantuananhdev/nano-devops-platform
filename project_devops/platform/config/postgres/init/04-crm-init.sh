#!/bin/bash
set -euo pipefail

echo "[initdb] Creating CRM role 'crm_user' and database 'crm_db' (if missing)"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'crm_user') THEN
      CREATE ROLE crm_user LOGIN PASSWORD 'devadmin';
   ELSE
      ALTER ROLE crm_user WITH LOGIN PASSWORD 'devadmin';
   END IF;
END
\$do\$;
EOSQL

DB_EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='crm_db'" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" || echo "")
if [ "$DB_EXISTS" != "1" ]; then
  echo "[initdb] Creating database 'crm_db' owned by role 'crm_user'"
  createdb -O crm_user crm_db --username "$POSTGRES_USER" --maintenance-db "$POSTGRES_DB"
else
  echo "[initdb] Database 'crm_db' already exists, skipping"
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "crm_db" <<-EOSQL
    GRANT ALL ON SCHEMA public TO crm_user;

    CREATE TABLE IF NOT EXISTS leads (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        message_id VARCHAR(128) NOT NULL UNIQUE,
        channel VARCHAR(32) NOT NULL,
        raw_text TEXT NOT NULL,
        customer_name VARCHAR(255),
        phone VARCHAR(64),
        product_interest VARCHAR(512),
        urgency VARCHAR(16) NOT NULL DEFAULT 'medium',
        sentiment VARCHAR(16) NOT NULL DEFAULT 'neutral',
        intent VARCHAR(64) NOT NULL DEFAULT 'other',
        language VARCHAR(16),
        summary TEXT,
        alert_sent BOOLEAN NOT NULL DEFAULT false,
        alert_type VARCHAR(32),
        llm_model VARCHAR(64),
        processed_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS processing_log (
        id BIGSERIAL PRIMARY KEY,
        message_id VARCHAR(128) NOT NULL,
        stage VARCHAR(32) NOT NULL,
        status VARCHAR(16) NOT NULL,
        detail TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_leads_urgency ON leads (urgency)
        WHERE urgency IN ('high', 'critical');
    CREATE INDEX IF NOT EXISTS idx_leads_processed_at ON leads (processed_at DESC);

    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO crm_user;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO crm_user;
EOSQL

echo "[initdb] CRM schema ready"
