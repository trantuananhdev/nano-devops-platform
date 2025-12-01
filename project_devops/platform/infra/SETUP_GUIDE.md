# Infrastructure Setup Guide

Complete guide for setting up the Nano DevOps Platform infrastructure using setup scripts.

## Overview

This guide covers the infrastructure setup process:
1. **VM Creation** - Create Alpine Linux VM manually (VMware Workstation Pro or your preferred method)
2. **Alpine Installation** - Install Alpine Linux on the VM
3. **VM Configuration** - Run setup scripts to configure the VM
4. **Platform Deployment** - Clone repository and start the platform

## Prerequisites

### Host (Windows 10 + VMware Workstation Pro)
- Windows 10
- VMware Workstation Pro installed
- Vagrant installed
- `vagrant-vmware-desktop` (hoặc plugin tương đương cho VMware) đã được cài và license

### VM Requirements (trong Vagrantfile)
- Base box: Alpine Linux 3.18+ (ví dụ `generic/alpine318`)
- RAM vật lý: **3.5GB** (3584MB) – phần còn lại được bù bởi **zram** trong guest
- vCPU: **2**
- Disk: **≥ 60GB**
- Network: **bridged** (public network) để CI/dev truy cập VM

## Step-by-Step Setup

### Step 1: Bring up VM via Vagrant (Recommended Path)

Trên Windows host:

```bash
cd project_devops/infra
vagrant up --provider=vmware_desktop
```

Vagrant sẽ:
- Tạo Alpine VM trên VMware Workstation Pro
- Gán 3.5GB RAM + 2 vCPU
- Bridge network
- Mount repo vào `/vagrant` trong VM
- Chạy `/vagrant/scripts/setup-alpine-complete.sh` để:
  - Cài Docker, Git, tools
  - Bật và cấu hình zram (swap ~3GB) → effective ~6–7GB RAM
  - Tạo `/opt/platform/{apps,data,monitoring,ci,scripts,src}`
  - (Optional) áp dụng kernel tuning

Sau khi `vagrant up` thành công:

```bash
vagrant ssh
uname -a
cat /etc/alpine-release
```

### Step 2: (Alternative) Tự tạo VM + Cài Alpine thủ công

Nếu không dùng Vagrant, bạn có thể tự tạo VM (vẫn nên bám RAM 3.5GB + zram như trên) và cài Alpine bằng wizard chuẩn, sau đó làm tiếp bước cấu hình bằng scripts:

Copy the setup scripts to the VM (or clone the repository):

**Option A: Clone Repository (Recommended)**
```bash
# On Alpine VM
apk add --no-cache git
cd /tmp
git clone <REPO_URL> nano-project-devops
cd nano-project-devops/project_devops/infra/scripts
```

**Option B: Copy Scripts via SCP**
```powershell
# On Windows host
scp -r project_devops/infra/scripts root@<vm-ip>:/tmp/setup-scripts
```

**Run Complete Setup:**
```bash
# On Alpine VM
cd /tmp/nano-project-devops/project_devops/infra/scripts
# Or: cd /tmp/setup-scripts

chmod +x *.sh
sudo ./setup-alpine-complete.sh
```

**What the script does:**
1. Installs Docker, Git, and essential tools
2. Configures zram swap (3GB)
3. Creates `/opt/platform` directory structure
4. Optionally applies kernel tuning

**Verification:**
```bash
# Check Docker
docker info
docker run --rm hello-world

# Check zram
swapon --show
free -h

# Check filesystem
ls -la /opt/platform/
```

### Step 3: Clone Repository and Start Platform

```bash
# Clone repository to platform directory
cd /opt/platform/src
git clone <REPO_URL> nano-project-devops

# Start the platform
cd nano-project-devops/project_devops/platform
docker compose up -d

# Verify services
docker compose ps
docker stats
```

### Step 4: Verify Platform

Access monitoring dashboards:
- Grafana: `http://<vm-ip>:3000`
- Prometheus: `http://<vm-ip>:9090`
- Loki: `http://<vm-ip>:3100`

Follow the onboarding guide:
- `docs-devops/00-overview/platform-onboarding-and-validation.md`

## Script Reference

### Alpine Setup Scripts (`scripts/`)

- **`setup-alpine-complete.sh`** - Run all setup scripts (recommended)
- **`setup-alpine-base.sh`** - Install Docker, Git, tools
- **`setup-alpine-zram.sh`** - Configure zram swap
- **`setup-alpine-filesystem.sh`** - Create `/opt/platform` structure
- **`setup-alpine-sysctl.sh`** - Kernel tuning (optional)

See `scripts/README.md` for detailed documentation.

## Troubleshooting

### Alpine Setup Issues

**Docker fails to start:**
```bash
service docker status
journalctl -u docker
```

**zram not working:**
```bash
lsmod | grep zram
modprobe zram
```

**Permission denied:**
```bash
chmod +x *.sh
sudo ./setup-alpine-complete.sh
```

## Quick Reference

### Complete Setup Command Sequence

**Alpine VM (after installation):**
```bash
apk add --no-cache git
cd /tmp
git clone <REPO_URL> nano-project-devops
cd nano-project-devops/project_devops/infra/scripts
chmod +x *.sh
sudo ./setup-alpine-complete.sh

cd /opt/platform/src
git clone <REPO_URL> nano-project-devops
cd nano-project-devops/project_devops/platform
docker compose up -d
```

## References

- `docs-devops/04-environment-and-infrastructure/infra-setup-alpine.md` - Complete Alpine setup guide
- `docs-devops/04-environment-and-infrastructure/runtime-environment.md` - Runtime requirements
- `docs-devops/04-environment-and-infrastructure/filesystem-layout.md` - Filesystem structure
- `docs-devops/00-overview/platform-onboarding-and-validation.md` - Platform onboarding guide
- `project_devops/infra/scripts/README.md` - Alpine setup scripts documentation
