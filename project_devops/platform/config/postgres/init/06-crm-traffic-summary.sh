#!/bin/bash
set -euo pipefail

echo "[initdb] CRM traffic summaries (Agent 1 — post burst)"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "crm_db" <<-EOSQL
    CREATE TABLE IF NOT EXISTS traffic_summaries (
        scenario_id VARCHAR(64) PRIMARY KEY,
        title_vi VARCHAR(255) NOT NULL DEFAULT '',
        summary_vi TEXT NOT NULL DEFAULT '',
        hot_leads INT NOT NULL DEFAULT 0,
        channels_json JSONB NOT NULL DEFAULT '{}',
        recommendations_json JSONB NOT NULL DEFAULT '[]',
        lead_count INT NOT NULL DEFAULT 0,
        raw_json JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    GRANT ALL PRIVILEGES ON TABLE traffic_summaries TO crm_user;
EOSQL

echo "[initdb] traffic_summaries ready"
