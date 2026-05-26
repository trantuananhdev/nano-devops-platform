#!/bin/bash
set -euo pipefail

echo "[initdb] Phase 4 CRM demo columns (auto-reply, Shopee, locale)"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "crm_db" <<-EOSQL
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_sent BOOLEAN NOT NULL DEFAULT false;
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_content TEXT NULL;
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_at TIMESTAMPTZ NULL;
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS order_id VARCHAR(64) NULL;
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS shop_id VARCHAR(128) NULL;
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS locale VARCHAR(16) NULL;

    CREATE INDEX IF NOT EXISTS idx_leads_channel_processed
        ON leads (channel, processed_at DESC);
EOSQL

echo "[initdb] Phase 4 CRM demo migration ready"
