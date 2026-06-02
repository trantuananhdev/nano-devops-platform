# AI-Driven CRM Integration Pipeline

**Demo name**: Hệ sinh thái CRM Tự động hóa tích hợp AI  
**Platform**: Nano DevOps Platform (6GB RAM, single-node)  
**Audience**: TNT Group — Ban Giám đốc / CTO (E-commerce Đông Nam Á)

---

## Mục đích (không phải train model)

Chứng minh năng lực **Trưởng nhóm AI Engineer**:

1. Giải quyết pain kinh doanh — tự động hóa lead đa kênh (Facebook, TikTok).
2. Làm chủ hệ thống — ingest không chặn (HTTP 200 ngay), AI xử lý ngầm.
3. Vận hành thực — sentiment/intent → cảnh báo Telegram/Lark cho Leader.

---

## Tài liệu bắt buộc (đọc theo thứ tự)

| # | File | Ai đọc | Mục đích |
|---|------|--------|----------|
| 0 | **[CURSOR_AUTONOMOUS_GUIDE.md](./CURSOR_AUTONOMOUS_GUIDE.md)** | **Cursor AI** | Luật tự hành — KHÔNG hỏi user code |
| 1 | [ARCHITECTURE.md](./ARCHITECTURE.md) | Cursor + reviewer | Kiến trúc 3 tầng + tích hợp platform |
| 2 | [docs/API_CONTRACT.md](./docs/API_CONTRACT.md) | Cursor implement 3.2 | Webhook FastAPI |
| 3 | [docs/DATA_MODEL.md](./docs/DATA_MODEL.md) | Cursor implement 3.4 | Postgres + Redis |
| 4 | [docs/ALERT_RULES.md](./docs/ALERT_RULES.md) | Cursor implement 3.5 | Telegram/Lark |
| 5 | [docs/DEMO_RUNBOOK.md](./docs/DEMO_RUNBOOK.md) | Presenter | **Kịch bản 15 phút UI (Phase 4)** |
| 5b | [docs/PHASE4_VALIDATION.md](./docs/PHASE4_VALIDATION.md) | Cursor / lab | Phase 4 smoke + rehearsal |
| 6 | **[docs/DEMO_PLATFORM_PLAN.md](./docs/DEMO_PLATFORM_PLAN.md)** | **Cursor + TNT demo** | **Phase 4 — UI Command Center** |
| 7 | [docs/DEMO_PLATFORM_CHECKLIST.md](./docs/DEMO_PLATFORM_CHECKLIST.md) | Cursor | Task 4.1 → 4.10 |
| 8 | [docs/IMPLEMENTATION_CHECKLIST.md](./docs/IMPLEMENTATION_CHECKLIST.md) | Cursor | Task 3.2 → 3.10 từng bước |

**State machine (repo):** `ai-system/ACTIVE_TASK.md` — luôn chỉ **một** task đang mở.

---

## Cấu trúc code

```
ai-crm-pipeline/                   ← Backend (BE)
├── crm-ingestion-api/             ← Webhook + Read API + SSE
├── crm-ai-worker/                 ← Gemini + alerts + auto-reply
├── crm-demo-simulator/            ← Phase 4 — lead_simulator.py
└── docs/DEMO_PLATFORM_PLAN.md

crm-demo-ui/                       ← Frontend (FE) — tách folder sibling
└── (React + Vite Command Center)
```

---

## URL sau khi tích hợp (dự kiến)

| Service | Host (Traefik) | Port nội bộ |
|---------|----------------|-------------|
| Ingestion + API | `https://crm-ingest.nano.platform` | 8080 |
| **Demo UI** | `https://crm-demo.nano.platform` | 80 (nginx) |
| Worker | *(không public)* | — |
| Metrics | `/metrics` trên ingestion | 8080 |

---

## Liên kết platform

- Compose apps: `project_devops/platform/composition/docker-compose.apps.yml`
- Golden path: `docs-devops/02-system-architecture/service-golden-path.md`
- Master plan: `ai-system/MASTER_PLAN.md` (Phase 3 ✅, Phase 4 ✅ code)
- Lab task: `ai-system/ACTIVE_TASK.md` (4.lab validation)
- **Gemini 2.5 Flash:** `crm-ai-worker/src/geminiProvider.py` — cùng `GEMINI_API_KEY` / `LLM_PROVIDER` trong **`.env` gốc repo** (không cần `export`; `./cli.sh up` tự nạp).
- **Demo quota (mặc định):** `CRM_SKIP_GEMINI=true` — Agent 1–6 dùng rule-based/fallback, không đốt quota free tier. Bật lại LLM: `CRM_SKIP_GEMINI=false`.
- **Burst:** `DEMO_BURST_MAX_MESSAGES=3` — tối đa 3 tin mỗi lần bấm kịch bản.
- **Lỗi GET `/api/v1/leads` 500:** DB thiếu cột — chạy `project_devops/platform/ops/scripts/crm-db-migrate-leads.sh` rồi restart `platform-crm-ingestion`.

---

*Thiết kế hoàn tất Task 3.1 — implementation do Cursor tự hành theo IMPLEMENTATION_CHECKLIST.*
