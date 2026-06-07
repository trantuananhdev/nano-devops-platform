# Acer — AI Data Layer Bootstrap

> **One command to rule them all.**  
> Edit `group_vars/acer.yml`, set your host IP in `inventory/hosts.ini`, then:

```bash
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory/hosts.ini site.yml
```

---

## Architecture

```
Ubuntu 22.04 (bare-metal · 4 GB RAM · ZRAM 6.5 GB)
└── Docker Engine (native, no VM overhead)
    ├── qdrant       — vector store       · :6333 / :6334
    ├── redis        — cache              · :6379 (loopback only)
    ├── minio        — object storage     · :9000 / :9001
    ├── embedder     — bge-m3 offline     · :8080  ← optional
    ├── portainer    — container UI       · :9443
    └── cadvisor     — CPU/RAM metrics    · :9090
```

### RAM Budget (ZRAM 6.5 GB virtual)

| Service   | Reserved | Limit  | Notes                          |
|-----------|----------|--------|--------------------------------|
| Qdrant    | 384 MB   | 512 MB | HNSW index on disk             |
| Redis     | 128 MB   | 160 MB | `allkeys-lru` eviction         |
| MinIO     | 256 MB   | 320 MB | S3-compatible                  |
| bge-m3    | 570 MB   | 700 MB | **Optional** — confidential only |
| Portainer | ~80 MB   | —      | Container management UI        |
| cAdvisor  | ~150 MB  | —      | Live metrics                   |
| Headroom  | ~1 GB    | —      | OS + Docker daemon             |

---

## Project Layout

```
ansible-ubuntu/
├── inventory/
│   └── hosts.ini            ← set ansible_host IP here
├── group_vars/
│   └── acer.yml             ← ALL tuneable parameters live here
├── roles/
│   ├── bootstrap/           ← base packages + UFW firewall
│   ├── zram/                ← ZRAM 6.5 GB + SSD swap + sysctl
│   ├── docker/              ← Docker CE + Compose V2
│   ├── ai_stack/            ← Docker Compose services
│   └── observability/       ← Portainer + cAdvisor
├── site.yml                 ← root playbook
└── requirements.yml
```

---

## Quick Start

### 1 — Prerequisites (local machine)

```bash
pip install ansible
ansible-galaxy collection install -r requirements.yml
```

### 2 — Set your host IP

```ini
# inventory/hosts.ini
[acer]
acer-host ansible_host=<YOUR_ACER_IP> ansible_user=ubuntu \
          ansible_ssh_private_key_file=../../.ssh/prod_key
```

### 3 — Step 0 (run ONCE on a fresh machine — uses password)

> The Acer must be reachable via SSH with password auth (default on a fresh
> Ubuntu install). This step injects `prod_key.pub` and then **disables**
> password auth so all future connections are key-only.

```bash
# Run from the ansible-ubuntu directory
ansible-playbook -i inventory/hosts.ini bootstrap-ssh.yml \
  --ask-pass --ask-become-pass
```

After this succeeds you will **never need a password again** for this host.

### 4 — Full deploy (key-based, all roles)

```bash
ansible-playbook -i inventory/hosts.ini site.yml
```

### 5 — Enable offline embedding (bge-m3)

```bash
ansible-playbook -i inventory/hosts.ini site.yml -e "embedding_enabled=true"
```

### 6 — Run a single role (by tag)

```bash
# Tags: bootstrap · zram · sysctl · swap · docker · ai_stack · observability
ansible-playbook -i inventory/hosts.ini site.yml --tags docker
```

---

## Day-2 Operations

| Task                    | Command                                      |
|-------------------------|----------------------------------------------|
| View running containers | `docker ps`                                  |
| Live RAM/CPU stats      | `docker stats`                               |
| Check ZRAM              | `zramctl` or `free -h`                       |
| Check swap layers       | `swapon --show`                              |
| Portainer UI            | `https://<host>:9443`                        |
| cAdvisor metrics        | `http://<host>:9090`                         |
| Wipe & redeploy stack   | `docker compose -f /opt/ai-stack/docker-compose.yml down -v` then re-run playbook |

---

## Idempotency

Every role is safe to re-run:

- **bootstrap** — `apt` and `ufw` are naturally idempotent.
- **zram** — guards `zramswap` config with `notify`, guards swap file with `stat`.
- **docker** — checks `docker --version` before touching apt.
- **ai_stack** — `docker_compose_v2` reconciles state declaratively.
- **observability** — `docker_container` reconciles state declaratively.
