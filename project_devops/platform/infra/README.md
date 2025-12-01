# Infrastructure Directory

## Purpose

This directory contains Infrastructure as Code (IaC) definitions and infrastructure-related configurations for the Nano DevOps Platform.

## Repository vs Runtime Mapping

- **Repository**: `project_devops/infra/`
- **Runtime**: Infrastructure definitions are used to configure `/opt/platform/` runtime

## Contents

### Scripts (`scripts/`)

Alpine Linux setup scripts for automating VM configuration:

- `setup-alpine-base.sh` - Install Docker, Git, and essential tools
- `setup-alpine-zram.sh` - Configure zram swap for memory optimization
- `setup-alpine-filesystem.sh` - Create `/opt/platform` directory structure
- `setup-alpine-sysctl.sh` - Configure kernel parameters (optional)
- `setup-alpine-complete.sh` - Run all setup scripts in sequence

See `scripts/README.md` for detailed usage instructions.

### Other Infrastructure

- Infrastructure service definitions
- Network configurations
- Storage/volume definitions
- Infrastructure monitoring configs
- Infrastructure deployment scripts

## Quick Start

### Option A – Use Vagrant (Alpine VM on your Windows + VMware Workstation Pro)

From `project_devops/infra` directory on your Windows host:

```bash
vagrant up --provider=vmware_desktop
```

This will:
- Create an Alpine Linux VM via Vagrant + VMware Workstation Pro
- Allocate **3.5GB RAM** and **2 vCPU**
- Use **bridged networking** (public network)
- Run `scripts/setup-alpine-complete.sh` inside the VM to:
  - Install Docker, Git, tools
  - Enable and configure zram (effective ~6–7GB RAM)
  - Create `/opt/platform` layout
  - Optionally apply kernel tuning

Then SSH into the VM:

```bash
vagrant ssh
```

You can work either in `/vagrant` (synced repo) hoặc clone repo sạch vào `/opt/platform/src`.

### Option B – Manual VM + Scripts

After creating and installing Alpine Linux VM manually (any hypervisor):

```bash
# On Alpine VM
cd project_devops/infra/scripts
chmod +x *.sh
sudo ./setup-alpine-complete.sh
```

### Clone Repository and Start Platform

```bash
cd /opt/platform/src
git clone <REPO_URL> nano-project-devops
cd nano-project-devops/project_devops/platform
docker compose up -d
```

## Guidelines

- Infrastructure must be immutable
- Infrastructure must be idempotent
- All infrastructure changes go through Git
- Follow GitOps principles
- Infrastructure definitions should be versioned

## References

- `docs-devops/04-environment-and-infrastructure/infra-setup-alpine.md` - Complete Alpine setup guide
- `docs-devops/04-environment-and-infrastructure/runtime-environment.md` - Runtime requirements
- `docs-devops/04-environment-and-infrastructure/filesystem-layout.md` - Filesystem structure
