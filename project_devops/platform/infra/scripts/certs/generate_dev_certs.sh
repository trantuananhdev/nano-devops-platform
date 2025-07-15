#!/bin/sh
set -e

# Generate local TLS certificates for Traefik using mkcert if available, otherwise openssl.
# Output directory: project_devops/platform/config/traefik/certs/dev

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Try to determine the platform root from the composition path argument
COMPOSITION_PATH="$1"
if [ -n "$COMPOSITION_PATH" ]; then
    CERT_DIR="$(cd "$COMPOSITION_PATH/../config/traefik/certs/dev" 2>/dev/null || echo "")"
    if [ -z "$CERT_DIR" ]; then
        # Fallback if the path doesn't exist yet
        CERT_DIR="$(cd "$COMPOSITION_PATH/.." && pwd)/config/traefik/certs/dev"
    fi
else
    # Fallback to the old relative logic if no argument provided
    REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
    CERT_DIR="$REPO_ROOT/project_devops/platform/config/traefik/certs/dev"
fi
HOSTS="localhost odoo.localhost grafana.localhost prometheus.localhost jaeger.localhost alertmanager.localhost loki.localhost"

mkdir -p "$CERT_DIR"

if command -v mkcert >/dev/null 2>&1; then
  echo "[certs] Using mkcert"
  for h in $HOSTS; do
    if [ ! -f "$CERT_DIR/$h.crt" ] || [ ! -f "$CERT_DIR/$h.key" ]; then
      mkcert -cert-file "$CERT_DIR/$h.crt" -key-file "$CERT_DIR/$h.key" "$h"
    else
      echo "[certs] $h exists, skipping"
    fi
  done
else
  echo "[certs] mkcert not found, using openssl self-signed certs"
  for h in $HOSTS; do
    if [ ! -f "$CERT_DIR/$h.crt" ] || [ ! -f "$CERT_DIR/$h.key" ]; then
      openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$CERT_DIR/$h.key" -out "$CERT_DIR/$h.crt" \
        -subj "/CN=$h" -addext "subjectAltName=DNS:$h"
    else
      echo "[certs] $h exists, skipping"
    fi
  done
fi

echo "[certs] Certificates ready at $CERT_DIR"
