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
        email VARCHAR(255),
        product_interest VARCHAR(512),
        property_type VARCHAR(64),
        location VARCHAR(255),
        transaction_type VARCHAR(32),
        budget_range VARCHAR(255),
        bedroom_count VARCHAR(32),
        urgency VARCHAR(16) NOT NULL DEFAULT 'medium',
        sentiment VARCHAR(16) NOT NULL DEFAULT 'neutral',
        intent VARCHAR(64) NOT NULL DEFAULT 'other',
        language VARCHAR(16),
        summary TEXT,
        alert_sent BOOLEAN NOT NULL DEFAULT false,
        alert_type VARCHAR(32),
        auto_reply_sent BOOLEAN NOT NULL DEFAULT false,
        auto_reply_content TEXT,
        auto_reply_at TIMESTAMPTZ,
        order_id VARCHAR(128),
        shop_id VARCHAR(128),
        locale VARCHAR(16),
        llm_model VARCHAR(64),
        processed_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        kanban_stage VARCHAR(32) NOT NULL DEFAULT 'new',
        chat_history JSONB,
        ai_manager_note TEXT,
        tags JSONB DEFAULT '[]'::jsonb,
        notes JSONB DEFAULT '[]'::jsonb,
        assigned_to VARCHAR(128),
        source VARCHAR(128),
        company VARCHAR(255),
        website VARCHAR(255),
        address TEXT,
        city VARCHAR(128),
        country VARCHAR(128),
        description TEXT,
        last_contacted_at TIMESTAMPTZ
    );

    -- Add missing columns if they don't exist
    DO \$do\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'email') THEN
            ALTER TABLE leads ADD COLUMN email VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'transaction_type') THEN
            ALTER TABLE leads ADD COLUMN transaction_type VARCHAR(32);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'budget_range') THEN
            ALTER TABLE leads ADD COLUMN budget_range VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'bedroom_count') THEN
            ALTER TABLE leads ADD COLUMN bedroom_count VARCHAR(32);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'auto_reply_sent') THEN
            ALTER TABLE leads ADD COLUMN auto_reply_sent BOOLEAN NOT NULL DEFAULT false;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'auto_reply_content') THEN
            ALTER TABLE leads ADD COLUMN auto_reply_content TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'auto_reply_at') THEN
            ALTER TABLE leads ADD COLUMN auto_reply_at TIMESTAMPTZ;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'order_id') THEN
            ALTER TABLE leads ADD COLUMN order_id VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'shop_id') THEN
            ALTER TABLE leads ADD COLUMN shop_id VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'locale') THEN
            ALTER TABLE leads ADD COLUMN locale VARCHAR(16);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'updated_at') THEN
            ALTER TABLE leads ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'kanban_stage') THEN
            ALTER TABLE leads ADD COLUMN kanban_stage VARCHAR(32) NOT NULL DEFAULT 'new';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'chat_history') THEN
            ALTER TABLE leads ADD COLUMN chat_history JSONB;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'ai_manager_note') THEN
            ALTER TABLE leads ADD COLUMN ai_manager_note TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'tags') THEN
            ALTER TABLE leads ADD COLUMN tags JSONB DEFAULT '[]'::jsonb;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'notes') THEN
            ALTER TABLE leads ADD COLUMN notes JSONB DEFAULT '[]'::jsonb;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'assigned_to') THEN
            ALTER TABLE leads ADD COLUMN assigned_to VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'source') THEN
            ALTER TABLE leads ADD COLUMN source VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'company') THEN
            ALTER TABLE leads ADD COLUMN company VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'website') THEN
            ALTER TABLE leads ADD COLUMN website VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'address') THEN
            ALTER TABLE leads ADD COLUMN address TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'city') THEN
            ALTER TABLE leads ADD COLUMN city VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'country') THEN
            ALTER TABLE leads ADD COLUMN country VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'description') THEN
            ALTER TABLE leads ADD COLUMN description TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'last_contacted_at') THEN
            ALTER TABLE leads ADD COLUMN last_contacted_at TIMESTAMPTZ;
        END IF;
    END
    \$do\$;

    CREATE TABLE IF NOT EXISTS processing_log (
        id BIGSERIAL PRIMARY KEY,
        message_id VARCHAR(128) NOT NULL,
        stage VARCHAR(32) NOT NULL,
        status VARCHAR(16) NOT NULL,
        detail TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS lead_activities (
        id VARCHAR(64) PRIMARY KEY,
        lead_id VARCHAR(128) NOT NULL REFERENCES leads(message_id) ON DELETE CASCADE,
        type VARCHAR(32) NOT NULL,
        title VARCHAR(256) NOT NULL,
        content TEXT,
        created_at TIMESTAMPTZ NOT NULL,
        due_date TIMESTAMPTZ,
        completed BOOLEAN NOT NULL DEFAULT false,
        created_by VARCHAR(128) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS deals (
        id VARCHAR(64) PRIMARY KEY,
        lead_id VARCHAR(128) NOT NULL REFERENCES leads(message_id) ON DELETE CASCADE,
        name VARCHAR(256) NOT NULL,
        amount NUMERIC,
        currency VARCHAR(16) NOT NULL DEFAULT 'VND',
        probability NUMERIC NOT NULL DEFAULT 50,
        close_date TIMESTAMPTZ,
        description TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_leads_urgency ON leads (urgency)
        WHERE urgency IN ('high', 'critical');
    CREATE INDEX IF NOT EXISTS idx_leads_processed_at ON leads (processed_at DESC);
    CREATE INDEX IF NOT EXISTS idx_leads_kanban_stage ON leads (kanban_stage);
    CREATE INDEX IF NOT EXISTS idx_lead_activities_lead_id ON lead_activities(lead_id);
    CREATE INDEX IF NOT EXISTS idx_deals_lead_id ON deals(lead_id);

    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO crm_user;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO crm_user;
EOSQL

echo "[initdb] CRM schema ready"
