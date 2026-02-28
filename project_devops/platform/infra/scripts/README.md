# Alpine Linux Setup Scripts

This directory contains scripts for automating Alpine Linux VM setup for the Nano DevOps Platform.

## Overview

These scripts automate the setup process described in `docs-devops/04-environment-and-infrastructure/infra-setup-alpine.md`. They are designed to be run on a fresh Alpine Linux installation.

## Scripts

### `setup-alpine-base.sh`

Installs essential packages: Docker, Git, and system tools.

**What it does:**
- Updates package index
- Installs Docker, Docker CLI, Docker Compose plugin
- Installs Git, Bash, curl, ca-certificates, htop, zram-init, openssh, sudo
- Enables and starts Docker service
- Verifies Docker installation with hello-world

**Usage:**
```bash
chmod +x setup-alpine-base.sh
sudo ./setup-alpine-base.sh
```

### `setup-alpine-zram.sh`

Configures zram swap for memory optimization (recommended for 6GB RAM VM).

**What it does:**
- Installs zram-init package if needed
- Enables zram-init service
- Configures zram swap (3GB default)
- Falls back to manual configuration if zram-init fails
- Verifies zram is active

**Usage:**
```bash
chmod +x setup-alpine-zram.sh
sudo ./setup-alpine-zram.sh
```

### `setup-alpine-filesystem.sh`

Creates the `/opt/platform` directory structure.

**What it does:**
- Creates `/opt/platform/apps` - Application service volumes
- Creates `/opt/platform/data` - PostgreSQL, Redis, Prometheus, Loki, Grafana data
- Creates `/opt/platform/monitoring` - Additional monitoring data
- Creates `/opt/platform/ci` - CI/CD runner and scripts
- Creates `/opt/platform/scripts` - Operational automation scripts
- Creates `/opt/platform/src` - Source code repository
- Sets proper ownership and permissions

**Usage:**
```bash
chmod +x setup-alpine-filesystem.sh
sudo ./setup-alpine-filesystem.sh
```

### `setup-alpine-sysctl.sh`

Configures kernel parameters for optimal performance (optional, advanced).

**What it does:**
- Configures VM swappiness (10)
- Configures VFS cache pressure (100)
- Configures TCP time-wait reuse
- Configures local port range
- Creates persistent configuration in `/etc/sysctl.d/99-platform.conf`

**Usage:**
```bash
chmod +x setup-alpine-sysctl.sh
sudo ./setup-alpine-sysctl.sh
```

### `setup-alpine-complete.sh`

Runs all setup scripts in sequence (recommended for first-time setup).

**What it does:**
- Runs base setup
- Configures zram
- Creates filesystem layout
- Optionally applies kernel tuning (prompts for confirmation)

**Usage:**
```bash
chmod +x setup-alpine-complete.sh
sudo ./setup-alpine-complete.sh
```

## Quick Start

### On Fresh Alpine Linux VM:

1. **Copy scripts to VM** (or clone repository):
   ```bash
   # Option 1: Clone repository
   cd /tmp
   git clone <REPO_URL> nano-project-devops
   cd nano-project-devops/project_devops/infra/scripts
   
   # Option 2: Copy scripts manually via SCP
   ```

2. **Make scripts executable:**
   ```bash
   chmod +x *.sh
   ```

3. **Run complete setup:**
   ```bash
   sudo ./setup-alpine-complete.sh
   ```

4. **Clone repository to platform directory:**
   ```bash
   cd /opt/platform/src
   git clone <REPO_URL> nano-project-devops
   ```

5. **Start the platform:**
   ```bash
   cd /opt/platform/src/nano-project-devops/project_devops/platform
   docker compose up -d
   ```

## Individual Script Execution

If you prefer to run scripts individually:

```bash
# 1. Base setup
sudo ./setup-alpine-base.sh

# 2. zram configuration
sudo ./setup-alpine-zram.sh

# 3. Filesystem layout
sudo ./setup-alpine-filesystem.sh

# 4. Kernel tuning (optional)
sudo ./setup-alpine-sysctl.sh
```

## Verification

After running the scripts, verify the setup:

```bash
# Check Docker
docker info
docker run --rm hello-world

# Check zram
swapon --show
free -h

# Check filesystem
ls -la /opt/platform/

# Check kernel settings (if applied)
sysctl vm.swappiness vm.vfs_cache_pressure
```

## Integration with VMware VM Creation

These scripts work together with the VMware VM creation script:

1. **Create VM** (on Windows host):
   ```powershell
   cd project_devops/infra/vmware
   .\create-vm-alpine.ps1 -AlpineISO "C:\path\to\alpine.iso"
   ```

2. **Install Alpine Linux** (manual step in VMware)

3. **Run setup scripts** (on Alpine VM):
   ```bash
   cd project_devops/infra/scripts
   sudo ./setup-alpine-complete.sh
   ```

## Requirements

- Alpine Linux 3.18+ installed
- Root access (or sudo)
- Internet connection (for package installation)
- At least 40GB disk space

## Troubleshooting

### Docker fails to start

Check Docker service status:
```bash
service docker status
journalctl -u docker
```

### zram not working

Check if zram module is loaded:
```bash
lsmod | grep zram
modprobe zram
```

### Permission denied

Ensure scripts are executable and run with sudo:
```bash
chmod +x *.sh
sudo ./setup-alpine-complete.sh
```

## References

- `docs-devops/04-environment-and-infrastructure/infra-setup-alpine.md` - Complete setup guide
- `project_devops/infra/vmware/` - VMware VM creation scripts
- `docs-devops/04-environment-and-infrastructure/runtime-environment.md` - Runtime requirements
- `docs-devops/04-environment-and-infrastructure/filesystem-layout.md` - Filesystem structure
