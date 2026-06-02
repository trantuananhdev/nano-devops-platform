#!/bin/bash
set -euo pipefail

echo "[initdb] Migrating CRM schema - adding Kanban, chat history, and AI manager fields"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "crm_db" <<-EOSQL
    -- Add auto-reply fields first (already referenced in code)
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_sent BOOLEAN NOT NULL DEFAULT false;
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_content TEXT;
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_at TIMESTAMPTZ;
    
    -- Add order and shop fields
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS order_id VARCHAR(64);
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS shop_id VARCHAR(128);
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS locale VARCHAR(16);
    
    -- Add Kanban fields
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS kanban_stage VARCHAR(32) NOT NULL DEFAULT 'new';
    
    -- Add chat history (JSONB for flexibility)
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS chat_history JSONB;
    
    -- Add AI manager note
    ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_manager_note TEXT;
    
    -- Add indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_leads_kanban_stage ON leads (kanban_stage);
    CREATE INDEX IF NOT EXISTS idx_leads_channel ON leads (channel);
    
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO crm_user;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO crm_user;
EOSQL

echo "[initdb] CRM migration complete"
