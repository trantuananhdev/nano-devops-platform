#!/bin/sh
# =============================================================================
# setup_secrets.sh — Generate secrets for Nano DevOps Platform (dev/staging)
# =============================================================================
# Usage (repo root):
#   ./cli.sh secrets
#   bash project_devops/platform/infra/scripts/system/setup_secrets.sh \
#        project_devops/platform/composition
#
# Quy tắc:
#   - Chỉ generate nếu file CHƯA tồn tại (idempotent)
#   - Mỗi service có password riêng biệt (không dùng chung)
#   - Không hardcode giá trị — luôn random
#   - chmod 600 mọi secret file
# =============================================================================
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../common/utils.sh" ]; then
    . "$SCRIPT_DIR/../common/utils.sh"
else
    log_info()  { echo "INFO:  $1"; }
    log_warn()  { echo "WARN:  $1"; }
    log_error() { echo "ERROR: $1"; exit 1; }
fi

log_info "=========================================="
log_info "Nano DevOps Platform — Secrets Setup"
log_info "=========================================="

COMPOSE_PATH="$1"
if [ -z "$COMPOSE_PATH" ]; then
    log_error "Usage: $0 <compose_dir_path>  (e.g. project_devops/platform/composition)"
fi

SECRETS_DIR="$(cd "$COMPOSE_PATH/../secrets" 2>/dev/null && pwd)" || {
    log_info "Creating secrets directory..."
    mkdir -p "$(dirname "$COMPOSE_PATH")/secrets"
    SECRETS_DIR="$(cd "$COMPOSE_PATH/../secrets" && pwd)"
}

# ---------------------------------------------------------------------------
# _gen_secret <name> [length]
# Generate a secret only if the file does not already exist or is empty.
# ---------------------------------------------------------------------------
_gen_secret() {
    local name="$1"
    local length="${2:-32}"
    local file="${SECRETS_DIR}/${name}.txt"

    if [ -f "$file" ] && [ -s "$file" ]; then
        log_info "  ✓ ${name}  (already exists, skipping)"
        return 0
    fi

    log_info "  + Generating: ${name} (${length} chars)"
    if command -v openssl >/dev/null 2>&1; then
        # base64 output, strip newlines and special chars, truncate to length
        openssl rand -base64 48 | tr -dc 'a-zA-Z0-9_-' | head -c "$length" > "$file"
    else
        tr -dc 'a-zA-Z0-9_-' < /dev/urandom | head -c "$length" > "$file"
    fi
    # Ensure no trailing newline issues
    printf '\n' >> "$file"
    chmod 600 "$file"

    if [ "$(id -u)" -eq 0 ] && id deploy >/dev/null 2>&1; then
        chown deploy:"$(id -gn deploy)" "$file"
    fi
}

log_info ""
log_info "--- Platform secrets ---"
_gen_secret "postgres_password"        32
_gen_secret "grafana_password"         24
_gen_secret "odoo_db_password"         32
_gen_secret "agentic_ai_jwt_secret"    48
_gen_secret "agentic_ai_admin_key"     32
_gen_secret "agentic_ai_openai_key"    48
_gen_secret "agentic_ai_webhook_secret" 32
_gen_secret "agentic_ai_gemini_key"    48

log_info ""
log_info "--- HDTV AI Platform secrets ---"
_gen_secret "hdtv_postgres_password"   32
_gen_secret "minio_root_password"      32
_gen_secret "meili_master_key"         40

log_info ""
log_info "Secrets directory: ${SECRETS_DIR}"
log_info "=========================================="
log_info "Secrets setup completed!"
log_info ""
log_info "QUAN TRỌNG: Không commit thư mục secrets vào git."
log_info "  .gitignore đã có rule:  project_devops/platform/secrets/*"
log_info "=========================================="
