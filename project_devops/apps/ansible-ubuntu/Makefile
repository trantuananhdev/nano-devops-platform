# =============================================================================
# Makefile — Acer AI Host Operations
# =============================================================================
# One-command interface for all Ansible operations.
# All values (host, user, port) are read from .env — nothing hardcoded here.
#
# Prerequisites:
#   pip install ansible
#   ansible-galaxy collection install -r requirements.yml
#
# Or use Docker Compose (no local Ansible install needed):
#   make docker-deploy
# =============================================================================

# ---------------------------------------------------------------------------
# Load .env (from repo root, two levels up)
# ---------------------------------------------------------------------------
ENV_FILE := ../../.env
ifneq (,$(wildcard $(ENV_FILE)))
  include $(ENV_FILE)
  export
endif

# ---------------------------------------------------------------------------
# Derived config — override via: make deploy ACER_HOST=x.x.x.x
# ---------------------------------------------------------------------------
INVENTORY  := inventory/hosts.ini
PLAYBOOK   := ansible-playbook -i $(INVENTORY)
COMPOSE    := docker compose \
                --env-file $(ENV_FILE) \
                -f ../../platform/composition/docker-compose.apps.yml

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
.PHONY: help
help:
	@echo ""
	@echo "  Acer AI Host — Ansible Operations"
	@echo "  ══════════════════════════════════"
	@echo ""
	@echo "  Direct (requires local Ansible):"
	@echo "    make ssh-bootstrap   Step 0: inject SSH key (runs once, needs password)"
	@echo "    make verify          Verify SSH key access & print host diagnostics"
	@echo "    make deploy          Full AI stack deploy / reconcile"
	@echo "    make teardown        Remove AI stack (keep OS tuning & Docker)"
	@echo "    make redeploy        Teardown → deploy (clean reinstall)"
	@echo "    make nuclear         Remove AI stack + Docker Engine (full wipe)"
	@echo ""
	@echo "  Via Docker Compose (no local Ansible needed):"
	@echo "    make docker-build    Build the ansible-runner image"
	@echo "    make docker-deploy   Deploy full AI stack via container"
	@echo "    make docker-verify   Verify SSH via container"
	@echo "    make docker-teardown Teardown via container"
	@echo ""
	@echo "  Single role (skip others):"
	@echo "    make tag TAG=docker"
	@echo "    make tag TAG=zram"
	@echo ""

# ---------------------------------------------------------------------------
# Step 0 — one-time SSH bootstrap (password auth)
# ---------------------------------------------------------------------------
.PHONY: ssh-bootstrap
ssh-bootstrap:
	@echo "▶  Injecting SSH key (you will be prompted for password)..."
	$(PLAYBOOK) bootstrap-ssh.yml --ask-pass --ask-become-pass

# ---------------------------------------------------------------------------
# Verify SSH key access
# ---------------------------------------------------------------------------
.PHONY: verify
verify:
	$(PLAYBOOK) verify-ssh.yml

# ---------------------------------------------------------------------------
# Deploy / reconcile full stack
# ---------------------------------------------------------------------------
.PHONY: deploy
deploy:
	$(PLAYBOOK) site.yml

# ---------------------------------------------------------------------------
# Deploy with offline embedding enabled
# ---------------------------------------------------------------------------
.PHONY: deploy-with-embedding
deploy-with-embedding:
	$(PLAYBOOK) site.yml -e "embedding_enabled=true"

# ---------------------------------------------------------------------------
# Teardown AI stack layer (keep OS-level config intact)
# ---------------------------------------------------------------------------
.PHONY: teardown
teardown:
	$(PLAYBOOK) teardown.yml

# ---------------------------------------------------------------------------
# Clean reinstall: teardown → deploy
# ---------------------------------------------------------------------------
.PHONY: redeploy
redeploy: teardown deploy

# ---------------------------------------------------------------------------
# Nuclear: wipe everything including Docker Engine
# ---------------------------------------------------------------------------
.PHONY: nuclear
nuclear:
	@echo "⚠️   This will remove Docker Engine entirely. Ctrl-C to abort."
	@sleep 3
	$(PLAYBOOK) teardown.yml -e "wipe_docker=true"

# ---------------------------------------------------------------------------
# Run a single role by tag
# ---------------------------------------------------------------------------
.PHONY: tag
tag:
	$(PLAYBOOK) site.yml --tags $(TAG)

# ---------------------------------------------------------------------------
# Dry-run (check mode — no changes applied)
# ---------------------------------------------------------------------------
.PHONY: check
check:
	$(PLAYBOOK) site.yml --check --diff

# ---------------------------------------------------------------------------
# Docker Compose targets (no local Ansible install required)
# ---------------------------------------------------------------------------
.PHONY: docker-build
docker-build:
	$(COMPOSE) build ansible-runner

.PHONY: docker-deploy
docker-deploy:
	$(COMPOSE) run --rm ansible-runner site.yml

.PHONY: docker-verify
docker-verify:
	$(COMPOSE) run --rm ansible-runner verify-ssh.yml

.PHONY: docker-teardown
docker-teardown:
	$(COMPOSE) run --rm ansible-runner teardown.yml

.PHONY: docker-ssh-bootstrap
docker-ssh-bootstrap:
	$(COMPOSE) run --rm -it ansible-runner bootstrap-ssh.yml \
		--ask-pass --ask-become-pass

.PHONY: docker-embed
docker-embed:
	$(COMPOSE) run --rm ansible-runner site.yml -e "embedding_enabled=true"
