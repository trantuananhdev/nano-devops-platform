#!/usr/bin/env bash
# =============================================================================
# validate_env.sh — Pre-flight check for .env before vagrant / hdtv-up / Ansible
# =============================================================================
# Usage (repo root):
#   ./cli.sh validate-env
#   bash project_devops/platform/infra/scripts/validate_env.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"
SSH_KEY="${REPO_ROOT}/.ssh/prod_deployer"

MISSING=()
WARNINGS=()
ERRORS=0

_load_env() {
  if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Missing .env at ${ENV_FILE}"
    echo "   Copy from .env.example: cp .env.example .env"
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

SECRETS_DIR="${REPO_ROOT}/project_devops/platform/secrets"

_require_var() {
  local name="$1"
  local value="${!name:-}"
  if [ -z "$value" ]; then
    MISSING+=("$name")
    ERRORS=1
  fi
}

# Env var OR Docker secret file (matches docker-compose.hdtv.yml *_PASSWORD_FILE)
_require_var_or_secret() {
  local env_name="$1"
  local file_env_name="$2"
  local default_file="$3"
  local value="${!env_name:-}"
  local file_path="${!file_env_name:-$default_file}"

  if [ -n "$value" ]; then
    return 0
  fi
  if [ -f "$file_path" ] && [ -s "$file_path" ]; then
    return 0
  fi
  MISSING+=("${env_name} (or secret file: ${file_path})")
  ERRORS=1
}

_warn_if_empty() {
  local name="$1"
  local value="${!name:-}"
  if [ -z "$value" ]; then
    WARNINGS+=("$name")
  fi
}

_is_ipv4() {
  local ip="$1"
  [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

_load_env

# Derive LLM_BASE_URL when only ACER_HOST is set (matches cli.sh / config.py)
if [ -z "${LLM_BASE_URL:-}" ] && [ -n "${ACER_HOST:-}" ]; then
  LLM_BASE_URL="http://${ACER_HOST}:8080/v1"
  export LLM_BASE_URL
fi

_require_var ACER_HOST
_require_var LLM_BASE_URL
_require_var_or_secret HDTV_POSTGRES_PASSWORD HDTV_POSTGRES_PASSWORD_FILE \
  "${SECRETS_DIR}/hdtv_postgres_password.txt"
_require_var MINIO_ROOT_USER
_require_var_or_secret MINIO_ROOT_PASSWORD MINIO_ROOT_PASSWORD_FILE \
  "${SECRETS_DIR}/minio_root_password.txt"
_require_var VM_IP

_warn_if_empty GEMINI_API_KEY
_warn_if_empty TELEGRAM_BOT_TOKEN

# T-54: Ansible kết nối root@ACER_HOST qua prod_deployer (ed25519).
# Key: .ssh/prod_deployer — bạn đã inject pub key lên Ubuntu server ✅

if [ -n "${ACER_HOST:-}" ] && ! _is_ipv4 "$ACER_HOST"; then
  echo "❌ ACER_HOST must be a valid IPv4 address, got: ${ACER_HOST}"
  ERRORS=1
fi

if [ ! -f "$SSH_KEY" ]; then
  echo "❌ SSH key not found: ${SSH_KEY}"
  echo "   Copy prod_deployer private key under .ssh/ before Ansible / deploy."
  ERRORS=1
elif [ ! -s "$SSH_KEY" ]; then
  echo "❌ SSH key is empty: ${SSH_KEY}"
  ERRORS=1
fi

if [ "${#MISSING[@]}" -gt 0 ]; then
  for var in "${MISSING[@]}"; do
    echo "❌ Missing: ${var} — check .env.example"
  done
fi

if [ "${#WARNINGS[@]}" -gt 0 ]; then
  for var in "${WARNINGS[@]}"; do
    echo "⚠️  Optional not set: ${var} (tool mocks / alerts may be degraded)"
  done
fi

if [ "$ERRORS" -ne 0 ]; then
  exit 1
fi

echo "✅ ENV OK"
echo "   ACER_HOST=${ACER_HOST}"
echo "   LLM_BASE_URL=${LLM_BASE_URL}"
echo "   VM_IP=${VM_IP}"
exit 0
