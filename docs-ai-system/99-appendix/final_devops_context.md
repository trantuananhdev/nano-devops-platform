# Final DevOps Context — EVN HDTV 2-Machine Topology

## Machines

| Machine | Role | RAM |
|---------|------|-----|
| Windows Nitro 5 | Cursor IDE, Vagrant host | 8GB (4GB → VM) |
| Alpine VM `nano-devops` | App stack + Ansible control | 4GB + zram |
| Ubuntu Server 22.04 (Acer) | LLM node ONLY | 4GB + zram 6.5GB |

## Bootstrap

```bash
# Windows
set COPY_PROJECT_DEVOPS=1
set VM_MEM=4096
vagrant up

# Alpine VM
cd /opt/platform/src/nano-project-devops
./cli.sh ansible-ping
./cli.sh ansible-bootstrap      # once: zram, docker, UFW on Ubuntu
./cli.sh ansible-deploy-llm     # llama-server Gemma4 on Ubuntu
./cli.sh obs-down               # free RAM before demo
./cli.sh hdtv-up
./cli.sh hdtv-migrate
./cli.sh hdtv-seed
```

## CLI Commands

| Command | Action |
|---------|--------|
| `hdtv-up` | Start HDTV docker-compose on Alpine VM |
| `hdtv-down` | Stop HDTV stack |
| `hdtv-logs` | Follow logs |
| `hdtv-migrate` | Alembic upgrade |
| `hdtv-seed` | Seed DB + Chroma |
| `ansible-deploy-llm` | Deploy llama-server on Ubuntu |
| `obs-down` | Stop Grafana/Prometheus to save RAM |

## Environment Variables (root `.env`)

```env
ACER_HOST=192.168.100.26
ACER_USER=tutinhhao
ACER_SSH_PORT=22
LLM_BASE_URL=http://192.168.100.26:8080/v1
LLM_MODEL=gemma-4-2b-it
GEMINI_API_KEY=your_key
HDTV_POSTGRES_PASSWORD=changeme_hdtv
HDTV_POSTGRES_DB=hdtv_db
HDTV_POSTGRES_USER=hdtv_user
MINIO_ROOT_USER=hdtv_minio
MINIO_ROOT_PASSWORD=changeme_minio
VM_IP=192.168.157.10
```

## RAM Budget

### Ubuntu (LLM only)
- llama-server Gemma4-E2B Q4_K_M: ~2.5GB
- Context 4096: ~1GB
- No Docker app containers

### Alpine VM (App)
- postgres 384m, redis 128m, api 384m, worker 512m
- chroma 400m, minio 256m, nginx 64m
- Disable observability during demo (`obs-down`)

## Network

- Alpine → Ubuntu: `LLM_BASE_URL` port 8080 (UFW: LAN only)
- Browser → `http://<VM_IP>:3080` or `https://hdtv.nano.platform`
- Ansible runner SSH: Alpine VM → Ubuntu via `ACER_HOST`

## LLM Fallback

If Gemma4 E2B OOM on Ubuntu:
- Reduce context: `-c 4096`
- Use Q2_K quantization
- Last resort: point `LLM_BASE_URL` to Gemini API for demo

## Paths

- Backend: `project_devops/apps/hdtv-ai-platform/`
- Frontend: `project_devops/apps/hdtv-ai-prototype/`
- Ansible: `project_devops/apps/ansible-ubuntu/`
- Compose: `project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml`
