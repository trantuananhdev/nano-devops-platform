#!/bin/sh
# Entrypoint script for postgres-exporter
# Reads PostgreSQL password from Docker secret and sets DATA_SOURCE_NAME

if [ -f /run/secrets/postgres_password ]; then
  export POSTGRES_PASSWORD=$(cat /run/secrets/postgres_password)
  export DATA_SOURCE_NAME="postgresql://platform_user:${POSTGRES_PASSWORD}@platform-postgres:5432/platform_db?sslmode=disable"
else
  echo "ERROR: PostgreSQL password secret not found at /run/secrets/postgres_password"
  exit 1
fi

# Execute the original postgres_exporter command
exec /bin/postgres_exporter "$@"