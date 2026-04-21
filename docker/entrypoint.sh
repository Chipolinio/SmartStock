#!/bin/sh
set -e

CERTS_DIR="/app/certs"
PRIVATE_KEY="${CERTS_DIR}/private.pem"
PUBLIC_KEY="${CERTS_DIR}/public.pem"

mkdir -p "${CERTS_DIR}"

if [ ! -f "${PRIVATE_KEY}" ] || [ ! -f "${PUBLIC_KEY}" ]; then
  echo "JWT keys not found, generating new RSA key pair..."
  openssl genrsa -out "${PRIVATE_KEY}" 2048
  openssl rsa -in "${PRIVATE_KEY}" -pubout -out "${PUBLIC_KEY}"
  chmod 600 "${PRIVATE_KEY}"
  chmod 644 "${PUBLIC_KEY}"
fi

exec "$@"
