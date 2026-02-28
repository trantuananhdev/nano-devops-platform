#!/bin/sh
# Nano DevOps Platform - TLS Certificate Generator (Self-Signed for Dev)
# This script generates a Root CA and a Wildcard certificate for *.nano.platform

set -e

CERT_DIR="/opt/platform/config/traefik/certs"
mkdir -p "$CERT_DIR"

# Root CA
if [ ! -f "$CERT_DIR/rootCA.key" ]; then
    echo "Generating Root CA..."
    openssl genrsa -out "$CERT_DIR/rootCA.key" 4096
    openssl req -x509 -new -nodes -key "$CERT_DIR/rootCA.key" -sha256 -days 3650 \
        -out "$CERT_DIR/rootCA.crt" \
        -subj "/C=VN/ST=Hanoi/L=Hanoi/O=NanoDevOps/CN=NanoDevOps Root CA"
fi

# Wildcard Certificate for *.nano.platform
if [ ! -f "$CERT_DIR/nano.platform.key" ]; then
    echo "Generating Wildcard Certificate for *.nano.platform..."
    openssl genrsa -out "$CERT_DIR/nano.platform.key" 2048
    
    cat <<EOF > "$CERT_DIR/nano.platform.ext"
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = nano.platform
DNS.2 = *.nano.platform
EOF

    openssl req -new -key "$CERT_DIR/nano.platform.key" \
        -out "$CERT_DIR/nano.platform.csr" \
        -subj "/C=VN/ST=Hanoi/L=Hanoi/O=NanoDevOps/CN=*.nano.platform"

    openssl x509 -req -in "$CERT_DIR/nano.platform.csr" \
        -CA "$CERT_DIR/rootCA.crt" -CAkey "$CERT_DIR/rootCA.key" \
        -CAcreateserial -out "$CERT_DIR/nano.platform.crt" \
        -days 825 -sha256 -extfile "$CERT_DIR/nano.platform.ext"
    
    rm "$CERT_DIR/nano.platform.csr" "$CERT_DIR/nano.platform.ext"
fi

echo "TLS Certificates generated successfully in $CERT_DIR"
