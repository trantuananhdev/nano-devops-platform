# =============================================================================
# Dockerfile — Ansible Runner for Acer AI Host
# =============================================================================
# Produces a lean, reproducible execution environment for all Ansible
# playbooks targeting the Acer physical server (Ubuntu 22.04).
#
# Usage (via docker-compose):
#   docker compose run --rm ansible-runner site.yml
#   docker compose run --rm ansible-runner bootstrap-ssh.yml --ask-pass --ask-become-pass
#   docker compose run --rm ansible-runner verify-ssh.yml
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

# Bake .ssh/ into image (fallback when Docker secret is not mounted)
# Priority: Docker secret /run/secrets/prod_key > baked .ssh/prod_key
RUN mkdir -p /ansible/.ssh /root/.ssh \
 && chmod 700 /ansible/.ssh /root/.ssh \
 && if [ -f /ansible/.ssh/prod_key ]; then chmod 600 /ansible/.ssh/prod_key; fi

# ---------- entrypoint --------------------------------------------------------
COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["site.yml"]
