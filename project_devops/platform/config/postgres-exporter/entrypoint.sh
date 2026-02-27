#!/bin/sh
export DATA_SOURCE_NAME="postgresql://platform_user:$(cat /run/secrets/postgres_password)@platform-postgres:5432/platform_db?sslmode=disable"
/bin/postgres_exporter
