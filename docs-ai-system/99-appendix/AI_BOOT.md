# AI_BOOT — Autonomous Engineer Boot (EcoIT Trial)

**Vai trò:** Fullstack + AI Engineer — thử việc EcoIT (10 ngày).
**Không hỏi user từng dòng code** — đọc state → thực thi task → self-critique → cập nhật state.

---

## Boot sequence (mỗi session)

1. [`HDTV_TASK.md`](HDTV_TASK.md) — task PENDING đầu tiên
2. [`PROJECT_STATE.md`](PROJECT_STATE.md) — phase, blocker
3. [`MASTER_PLAN.md`](MASTER_PLAN.md) — roadmap 10 ngày
4. Docs theo task:
   - Backend/Agent: [`final_ai_context.md`](final_ai_context.md)
   - Infra/Deploy: [`final_devops_context.md`](final_devops_context.md)
   - API: [`API_CONTRACT.md`](API_CONTRACT.md)
5. Sau task: [`SELF_CRITIQUE.md`](SELF_CRITIQUE.md) → cập nhật PROJECT_STATE + HDTV_TASK

**Prompt khởi động:**
```
Đọc ai-system/AI_BOOT.md → HDTV_TASK.md → PROJECT_STATE.md.
Thực hiện task PENDING đầu tiên. Không hỏi user.
Sau xong: chạy verify_cmd, cập nhật PROJECT_STATE, self-critique SELF_CRITIQUE.md.
```

---

## Phase 7 — EVN HDTV (ACTIVE)

> **Mục tiêu:** Agentic Appraisal Platform — thẩm định Tờ trình HĐTV EVN Hanoi.
> **Paths:** `project_devops/apps/hdtv-ai-platform/`, `hdtv-ai-prototype/`

### Topology 2 máy (dev = prod)

| Machine | Role |
|---------|------|
| Ubuntu Server 22.04 | LLM node ONLY (`llama-server` Gemma 4) |
| Alpine VM (`nano-devops`) | App stack + Ansible SSH → Ubuntu |
| Windows Nitro 5 | Cursor + `vagrant up` |

### Luồng làm việc

```
[HDTV_TASK.md task PENDING]
      │
      ▼
Đọc final_ai_context / final_devops_context
      │
      ▼
Code → test.sh → verify_cmd
      │
      ▼
Cập nhật PROJECT_STATE + HDTV_TASK status
```

### Stack khóa

| Layer | Tech |
|-------|------|
| BE | FastAPI async, Celery, PostgreSQL, Redis, ChromaDB, MinIO |
| FE | Vue 3, Pinia, Axios, WebSocket |
| LLM | Gemma 4 E2B via HTTP (Ubuntu) |
| Tools | Gemini Flash mock |

---

## Vagrant — One Command Boot

```bash
set COPY_PROJECT_DEVOPS=1
set VM_MEM=4096
vagrant up
```

```bash
vagrant ssh
cd /opt/platform/src/nano-project-devops
./cli.sh ansible-ping
./cli.sh ansible-bootstrap
./cli.sh ansible-deploy-llm
./cli.sh obs-down
./cli.sh hdtv-up
./cli.sh hdtv-migrate
./cli.sh hdtv-seed
```

### URLs

| Service | URL |
|---------|-----|
| HDTV FE | `http://<VM_IP>:3080` or `https://hdtv.nano.platform` |
| HDTV API | `http://<VM_IP>:8000/docs` |
| Grafana | `https://grafana.nano.platform` |

### CLI shortcuts

```bash
./cli.sh hdtv-up / hdtv-down / hdtv-logs / hdtv-migrate / hdtv-seed
./cli.sh ansible-deploy-llm
./cli.sh obs-down
./cli.sh ansible-ping
```

---

## Luật thực thi

- **LLM luôn HTTP** — không embed model trong FastAPI
- **Mọi tool call → ai_audit_logs**
- **API contract trước code** — `API_CONTRACT.md`
- **Mọi config qua ENV**
- **Không đổi CSS** `.glass-panel` trên FE

---

*Sync: `MASTER_PLAN.md`, `PROJECT_STATE.md`, `HDTV_TASK.md`*
