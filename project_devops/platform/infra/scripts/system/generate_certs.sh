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
if [ ! -f "$CERT_DIR/nano.platform.key" ] || [ ! -f "$CERT_DIR/nano.platform.crt" ]; then
    echo "[certs] Generating wildcard certificate for *.nano.platform..."
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
DNS.3 = grafana.nano.platform
DNS.4 = prometheus.nano.platform
DNS.5 = crm-ingest.nano.platform
DNS.6 = crm-demo.nano.platform
EOF

    openssl req -new -key "$CERT_DIR/nano.platform.key" \
        -out "$CERT_DIR/nano.platform.csr" \
        -subj "/C=VN/ST=Hanoi/L=Hanoi/O=NanoDevOps/CN=*.nano.platform"

    openssl x509 -req -in "$CERT_DIR/nano.platform.csr" \
        -CA "$CERT_DIR/rootCA.crt" -CAkey "$CERT_DIR/rootCA.key" \
        -CAcreateserial -out "$CERT_DIR/nano.platform.crt" \
        -days 825 -sha256 -extfile "$CERT_DIR/nano.platform.ext"

    rm -f "$CERT_DIR/nano.platform.csr" "$CERT_DIR/nano.platform.ext"
fi

chmod 644 "$CERT_DIR"/*.crt 2>/dev/null || true
chmod 600 "$CERT_DIR"/*.key 2>/dev/null || true

echo "[certs] Traefik TLS ready: $CERT_DIR/nano.platform.crt"
echo "[certs] Trust on presenter PC: import $CERT_DIR/rootCA.crt"
