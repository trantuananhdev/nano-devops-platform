#!/bin/sh
# =============================================================================
# backup.sh — HDTV AI Platform: Automated Backup Script (T-35)
# =============================================================================
# Backs up:
#   1. PostgreSQL (HDTV DB) — pg_dump via docker exec
#   2. MinIO dossier PDFs — mc mirror
#   3. ChromaDB vector data — tar.gz of persistent volume mount
#
# All backups go to BACKUP_DIR (default: /opt/platform/backups/hdtv/<date>)
# Retention: keeps last KEEP_DAYS days of backups (default: 7)
#
# Usage:
#   ./backup.sh                         # full backup
#   ./backup.sh --postgres-only         # only postgres
#   BACKUP_DIR=/tmp/bak ./backup.sh     # custom output dir
#
# Called by:
#   - cli.sh hdtv-backup (manual)
#   - docker-compose hdtv-backup cron service (daily at 03:00)
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# Helper to read secret from file
# ---------------------------------------------------------------------------
read_secret() {
    local secret_file="$1"
    local default="$2"
    if [ -f "${secret_file}" ]; then
        cat "${secret_file}" | tr -d '\n'
    else
        echo "${default}"
    fi
}

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKUP_DIR="${BACKUP_DIR:-/opt/platform/backups}"
KEEP_DAYS="${KEEP_DAYS:-7}"
DATE="$(date +%Y%m%d_%H%M%S)"
HDTV_BACKUP_DIR="${BACKUP_DIR}/hdtv/${DATE}"

# PostgreSQL connection — matches platform-compose environment
PG_HOST="${POSTGRES_HOST:-platform-postgres}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_DB="${HDTV_POSTGRES_DB:-hdtv_db}"
PG_USER="${HDTV_POSTGRES_USER:-hdtv_user}"
PG_PASSWORD="$(read_secret "${HDTV_POSTGRES_PASSWORD_FILE:-}" "${HDTV_POSTGRES_PASSWORD:-changeme_hdtv}")"

# MinIO connection
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://hdtv-minio:9000}"
MINIO_ACCESS_KEY="${MINIO_ROOT_USER:-hdtv_minio}"
MINIO_SECRET_KEY="$(read_secret "${MINIO_ROOT_PASSWORD_FILE:-}" "${MINIO_ROOT_PASSWORD:-changeme_minio}")"
MINIO_BUCKET="${MINIO_BUCKET:-dossiers}"

# ChromaDB volume mount (inside backup container via volume mount)
CHROMA_DATA_DIR="${CHROMA_DATA_DIR:-/chroma-data}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

fail() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
    exit 1
}

check_mode() {
    POSTGRES_ONLY=0
    for arg in "$@"; do
        case "$arg" in
            --postgres-only) POSTGRES_ONLY=1 ;;
        esac
    done
}

check_mode "$@"

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
log "HDTV Backup starting — output: ${HDTV_BACKUP_DIR}"
mkdir -p "${HDTV_BACKUP_DIR}"

BACKUP_LOG="${HDTV_BACKUP_DIR}/backup.log"
exec > >(tee -a "${BACKUP_LOG}") 2>&1

# ---------------------------------------------------------------------------
# 1. PostgreSQL backup via pg_dump
# ---------------------------------------------------------------------------
log "--- PostgreSQL backup ---"
PG_DUMP_FILE="${HDTV_BACKUP_DIR}/hdtv_db_${DATE}.sql.gz"

PGPASSWORD="${PG_PASSWORD}" pg_dump \
    -h "${PG_HOST}" \
    -p "${PG_PORT}" \
    -U "${PG_USER}" \
    -d "${PG_DB}" \
    --no-owner \
    --no-acl \
    --format=custom \
    | gzip > "${PG_DUMP_FILE}"

PG_SIZE="$(du -sh "${PG_DUMP_FILE}" | cut -f1)"
log "PostgreSQL backup done: ${PG_DUMP_FILE} (${PG_SIZE})"

if [ "${POSTGRES_ONLY}" -eq 1 ]; then
    log "--postgres-only flag set — skipping MinIO and Chroma"
    log "Backup complete: ${HDTV_BACKUP_DIR}"
    exit 0
fi

# ---------------------------------------------------------------------------
# 2. MinIO dossier PDFs — mc mirror
# ---------------------------------------------------------------------------
log "--- MinIO backup ---"
MINIO_BACKUP_DIR="${HDTV_BACKUP_DIR}/minio"
mkdir -p "${MINIO_BACKUP_DIR}"

# Configure mc alias (idempotent)
mc alias set hdtv-minio "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" \
    --api S3v4 --quiet 2>/dev/null || true

# Mirror bucket to local backup dir
if mc ls "hdtv-minio/${MINIO_BUCKET}" >/dev/null 2>&1; then
    mc mirror --quiet "hdtv-minio/${MINIO_BUCKET}" "${MINIO_BACKUP_DIR}/"
    MINIO_COUNT="$(find "${MINIO_BACKUP_DIR}" -type f | wc -l)"
    MINIO_SIZE="$(du -sh "${MINIO_BACKUP_DIR}" | cut -f1)"
    log "MinIO backup done: ${MINIO_COUNT} files, ${MINIO_SIZE}"
else
    log "MinIO bucket '${MINIO_BUCKET}' empty or unreachable — skipping"
fi

# ---------------------------------------------------------------------------
# 3. ChromaDB vector data — tar.gz
# ---------------------------------------------------------------------------
log "--- ChromaDB backup ---"
CHROMA_BACKUP_FILE="${HDTV_BACKUP_DIR}/chroma_data_${DATE}.tar.gz"

if [ -d "${CHROMA_DATA_DIR}" ] && [ "$(ls -A "${CHROMA_DATA_DIR}" 2>/dev/null)" ]; then
    tar -czf "${CHROMA_BACKUP_FILE}" -C "${CHROMA_DATA_DIR}" .
    CHROMA_SIZE="$(du -sh "${CHROMA_BACKUP_FILE}" | cut -f1)"
    log "ChromaDB backup done: ${CHROMA_BACKUP_FILE} (${CHROMA_SIZE})"
else
    log "ChromaDB data dir empty or not mounted at ${CHROMA_DATA_DIR} — skipping"
fi

# ---------------------------------------------------------------------------
# 4. Backup summary
# ---------------------------------------------------------------------------
TOTAL_SIZE="$(du -sh "${HDTV_BACKUP_DIR}" | cut -f1)"
log "=== Backup Summary ==="
log "  Dir:      ${HDTV_BACKUP_DIR}"
log "  Postgres: ${PG_DUMP_FILE}"
log "  MinIO:    ${MINIO_BACKUP_DIR}"
log "  Chroma:   ${CHROMA_BACKUP_FILE:-skipped}"
log "  Total:    ${TOTAL_SIZE}"
log "=== Done ==="

# ---------------------------------------------------------------------------
# 5. Retention — remove backups older than KEEP_DAYS
# ---------------------------------------------------------------------------
log "Cleaning backups older than ${KEEP_DAYS} days..."
if [ -d "${BACKUP_DIR}/hdtv" ]; then
    find "${BACKUP_DIR}/hdtv" -maxdepth 1 -type d -mtime "+${KEEP_DAYS}" \
        -exec rm -rf {} + 2>/dev/null || true
    REMAINING="$(find "${BACKUP_DIR}/hdtv" -maxdepth 1 -mindepth 1 -type d | wc -l)"
    log "Remaining backup sets: ${REMAINING}"
fi

log "Backup complete: ${HDTV_BACKUP_DIR}"
