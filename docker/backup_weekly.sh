#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-/opt/backups}"
TIMESTAMP="$(date +%F_%H-%M-%S)"
OUTPUT_FILE="${BACKUP_DIR}/smartstock_${TIMESTAMP}.sql"

mkdir -p "${BACKUP_DIR}"

docker exec -t smartstock_db pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > "${OUTPUT_FILE}"

# Keep only 8 latest weekly backups (~2 months)
ls -1t "${BACKUP_DIR}"/smartstock_*.sql 2>/dev/null | awk 'NR>8' | xargs -r rm -f
