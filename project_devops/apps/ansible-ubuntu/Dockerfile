# =============================================================================
# Dockerfile — Ansible Runner for Acer AI Host
# =============================================================================
# SSH key: prod_deployer (ed25519) — baked pub key for reference only.
# Private key provided at runtime via Docker secret /run/secrets/prod_deployer.
#
# Usage (via docker-compose):
#   docker compose run --rm ansible-runner site.yml
#   docker compose run --rm ansible-runner verify-ssh.yml
#   docker compose run --rm ansible-runner deploy-llm.yml
#
# Usage (standalone):
#   docker build -t ansible-runner .
#   docker run --rm -it \
#     -v $(pwd):/ansible \
#     -v /path/to/.ssh:/ansible/.ssh:ro \
#     ansible-runner site.yml
# =============================================================================

FROM python:3.12-slim AS base

# ---------- system deps -------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-client \
        sshpass \
        gcc \
        libssl-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------- python deps -------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------- galaxy collections ------------------------------------------------
COPY requirements.yml /tmp/requirements.yml
RUN ansible-galaxy collection install -r /tmp/requirements.yml

# ---------- workspace ---------------------------------------------------------
WORKDIR /ansible
COPY . /ansible

# prod_deployer.pub is baked in (public key only — safe to embed).
# prod_deployer (private) excluded via .dockerignore — provided at runtime
# via Docker secret /run/secrets/prod_deployer.
RUN mkdir -p /ansible/.ssh /root/.ssh \
 && chmod 700 /ansible/.ssh /root/.ssh \
 && if [ -f /ansible/.ssh/prod_deployer.pub ]; then chmod 644 /ansible/.ssh/prod_deployer.pub; fi

# ---------- entrypoint --------------------------------------------------------
COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["site.yml"]
