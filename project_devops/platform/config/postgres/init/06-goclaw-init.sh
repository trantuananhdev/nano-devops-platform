#!/bin/bash
set -e

# Create goclaw database and user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER IF NOT EXISTS goclaw WITH PASSWORD 'devadmin';
    CREATE DATABASE IF NOT EXISTS goclaw_db;
    GRANT ALL PRIVILEGES ON DATABASE goclaw_db TO goclaw;
    \c goclaw_db
    GRANT ALL ON SCHEMA public TO goclaw;
EOSQL

echo "Goclaw database and user created successfully"
