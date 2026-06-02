#!/bin/sh
# Nano DevOps Platform - TLS for Traefik (wildcard *.nano.platform)
# Output: /opt/platform/config/traefik/certs/ (bind-mounted by platform-traefik)

set -e

CERT_DIR="${CERT_DIR:-/opt/platform/config/traefik/certs}"
mkdir -p "$CERT_DIR"
chmod 755 "$CERT_DIR"

# Root CA (import rootCA.crt on presenter laptop — NOT used as Traefik server cert)
if [ ! -f "$CERT_DIR/rootCA.key" ]; then
    echo "[certs] Generating Root CA..."
    openssl genrsa -out "$CERT_DIR/rootCA.key" 4096
    openssl req -x509 -new -nodes -key "$CERT_DIR/rootCA.key" -sha256 -days 3650 \
        -out "$CERT_DIR/rootCA.crt" \
        -subj "/C=VN/ST=Hanoi/L=Hanoi/O=NanoDevOps/CN=NanoDevOps Root CA"
fi

# Wildcard server certificate for Traefik HTTPS
# Always regenerate server cert to ensure all domains are included
echo "[certs] Generating wildcard certificate for *.nano.platform..."
rm -f "$CERT_DIR/nano.platform.key" "$CERT_DIR/nano.platform.crt" "$CERT_DIR/nano.platform.csr" "$CERT_DIR/nano.platform.ext" "$CERT_DIR/rootCA.srl"
openssl genrsa -out "$CERT_DIR/nano.platform.key" 2048

cat <<EOF > "$CERT_DIR/nano.platform.ext"
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = nano.platform
DNS.2 = *.nano.platform
DNS.3 = odoo.nano.platform
DNS.4 = ai.nano.platform
DNS.5 = grafana.nano.platform
DNS.6 = prometheus.nano.platform
DNS.7 = aggregator.nano.platform
DNS.8 = faulty.nano.platform
DNS.9 = data.nano.platform
DNS.10 = health.nano.platform
DNS.11 = user.nano.platform
DNS.12 = crm-ingest.nano.platform
DNS.13 = crm-demo.nano.platform
DNS.14 = goclaw.nano.platform
DNS.15 = shopee-search.nano.platform
DNS.16 = shopee-api.nano.platform
EOF

openssl req -new -key "$CERT_DIR/nano.platform.key" \
    -out "$CERT_DIR/nano.platform.csr" \
    -subj "/C=VN/ST=Hanoi/L=Hanoi/O=NanoDevOps/CN=*.nano.platform"

openssl x509 -req -in "$CERT_DIR/nano.platform.csr" \
    -CA "$CERT_DIR/rootCA.crt" -CAkey "$CERT_DIR/rootCA.key" \
    -CAcreateserial -out "$CERT_DIR/nano.platform.crt" \
    -days 825 -sha256 -extfile "$CERT_DIR/nano.platform.ext"

rm -f "$CERT_DIR/nano.platform.csr" "$CERT_DIR/nano.platform.ext"

chmod 644 "$CERT_DIR"/*.crt 2>/dev/null || true
chmod 600 "$CERT_DIR"/*.key 2>/dev/null || true

echo "[certs] Traefik TLS ready: $CERT_DIR/nano.platform.crt"
echo "[certs] Trust on presenter PC: import $CERT_DIR/rootCA.crt"
