#!/bin/bash
# =============================================================================
# deploy.sh — Local CD script (chạy từ Alpine VM hoặc Windows Git Bash)
# =============================================================================
# Thay thế GitHub Actions CD (vì Acer Ubuntu trên LAN — không SSH được từ cloud)
#
# Usage:
#   ./deploy.sh                    # Deploy image tag: latest
#   ./deploy.sh abc1234            # Deploy image tag: git sha cụ thể
#   ./deploy.sh latest --check     # Dry run
#
# Pre-requisites:
#   - vagrant up đã chạy
#   - .ssh/prod_deployer đã có (key đã inject lên Ubuntu server)
#   - vagrant ssh vào VM, cd /opt/platform/src/nano-project-devops
# =============================================================================
set -euo pipefail

IMAGE_TAG="${1:-latest}"
EXTRA_ARGS="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
ANSIBLE_DIR="$SCRIPT_DIR"

echo "================================================================"
echo "🚀 EcoIT Deploy → Acer Ubuntu"
echo "   Image tag: $IMAGE_TAG"
echo "   Ansible dir: $ANSIBLE_DIR"
echo "================================================================"

# Load ACER_HOST from .env (T-55: Ansible connects as tutinhhao by default)
ENV_FILE="$REPO_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
  export $(grep -E '^(ACER_HOST|ACER_SSH_PORT)=' "$ENV_FILE" | xargs)
fi

ACER_HOST="${ACER_HOST:-}"
ACER_USER="tutinhhao"   # T-55: Connect as tutinhhao, privilege escalation via become: true
ACER_SSH_PORT="${ACER_SSH_PORT:-22}"

if [ -z "$ACER_HOST" ]; then
  echo "❌ ACER_HOST phải được set trong .env"
  exit 1
fi

echo "▶  Target: ${ACER_USER}@${ACER_HOST}:${ACER_SSH_PORT} (become root via sudo)"
echo ""

# SSH key — prod_deployer (ed25519)
SSH_KEY="$REPO_ROOT/.ssh/prod_deployer"
if [ ! -f "$SSH_KEY" ]; then
  echo "❌ SSH key không tìm thấy: $SSH_KEY"
  echo "   Copy prod_deployer vào .ssh/ (key đã inject vào cả root và tutinhhao)"
  exit 1
fi

# Pre-scan host key
ssh-keyscan -p "$ACER_SSH_PORT" -H "$ACER_HOST" >> ~/.ssh/known_hosts 2>/dev/null || true

# Run deploy playbook
cd "$ANSIBLE_DIR"
ansible-playbook \
  -i inventory/hosts.ini \
  deploy-ecoit.yml \
  --private-key="$SSH_KEY" \
  -e "ansible_host=$ACER_HOST" \
  -e "ansible_user=$ACER_USER" \
  -e "ansible_port=$ACER_SSH_PORT" \
  -e "ecoit_image_tag=$IMAGE_TAG" \
  $EXTRA_ARGS

echo ""
echo "✅ Deploy complete. Verify: http://${ACER_HOST}:8000/health"
