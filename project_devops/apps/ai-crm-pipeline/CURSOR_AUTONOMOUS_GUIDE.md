# CURSOR AUTONOMOUS GUIDE — AI CRM Pipeline

> **Dành cho Cursor AI.** User **không biết code**. Mọi output phải do Cursor tự sinh theo tài liệu này và `ai-system/`.

---

## Vai trò của bạn

Bạn là **Autonomous Platform Engineer** (xem `ai-system/AI_BOOT.md`), không phải chatbot hỏi ý kiến từng dòng.

**Bạn PHẢI:**
- Đọc `ai-system/PROJECT_STATE.md` → `ACTIVE_TASK.md` → tài liệu trong bảng README trước khi sửa file.
- Làm **đúng một** task Phase 3 (3.1 đã xong; tiếp theo 3.2, 3.3, …).
- Tự hoàn thành → self-critique → cập nhật `PROJECT_STATE`, `ACTIVE_TASK`, `EXECUTION_HISTORY`.
- Tự sinh task kế tiếp khi `AUTONOMOUS MODE: ENABLED`.

**Bạn KHÔNG ĐƯỢC:**
- Hỏi user “bạn muốn dùng thư viện gì?” — đã quyết trong ARCHITECTURE + DATA_MODEL.
- Nhảy task (ví dụ làm compose trước khi có ingestion code).
- Sửa file ngoài **ALLOWED ACTIONS** trong `ACTIVE_TASK.md`.
- Gộp nhiều task vào một PR lớn (>300 dòng/file nếu tránh được).

---

## Vòng lặp bắt buộc mỗi session

```
1. AI_BOOT.md (30 giây nhắc vai trò)
2. ACTIVE_TASK.md → biết task ID (vd: 3.2)
3. IMPLEMENTATION_CHECKLIST.md → mục tương ứng
4. KNOWLEDGE_ROUTING.md → block "AI-DRIVEN CRM DEMO"
5. Implement
6. AI_SELF_CRITIC.md → tự chấm
7. EXECUTION_HISTORY.md → log
8. ACTIVE_TASK.md → task tiếp (3.3...)
```

**Không chờ user gõ "tiếp tục".** Autonomous mode = tự chuyển task sau khi DONE WHEN đạt.

---

## Phase 4 Demo Platform

- Đọc `docs/DEMO_PLATFORM_PLAN.md` + `docs/DEMO_PLATFORM_CHECKLIST.md`
- FE riêng: `project_devops/apps/crm-demo-ui/`
- BE mở rộng: ingestion Read API, SSE, Shopee, worker auto-reply, simulator CLI

## Stack đã khóa (không đổi trừ khi MASTER_PLAN sửa)

| Thành phần | Công nghệ |
|------------|-----------|
| Ingestion | Python 3.11, **FastAPI**, uvicorn, asyncio |
| Queue | **Redis 7** (`platform-redis`) list `crm:queue:messages` |
| Worker | Python 3.11, asyncio + redis + httpx (Gemini) |
| LLM | **Google Gemini** (`gemini-2.5-flash`) |
| DB | **PostgreSQL 16** database `crm_db` |
| Alert | Telegram Bot API và/hoặc Lark webhook |
| Deploy | Docker + `docker-compose.apps.yml` + CI path-filter |

---

## Task map nhanh

| Task | Làm gì | File chính |
|------|--------|------------|
| 3.1 | Design | `docs/*`, `ARCHITECTURE.md` ✅ |
| 3.2 | Ingestion API | `crm-ingestion-api/*` |
| 3.3 | AI Worker | `crm-ai-worker/*` |
| 3.4 | DB init | `platform/config/postgres/init/04-crm-init.sh` |
| 3.5 | Alerts | logic trong worker + `ALERT_RULES.md` |
| 3.6 | Compose + Traefik | `docker-compose.apps.yml` |
| 3.7 | CI | `.github/workflows/ci.yml` |
| 3.8 | Monitoring | Grafana + alerts |
| 3.9 | Smoke + demo | `platform/ops/smoke-tests/` |
| 3.10 | Validation doc | `docs/PHASE3_VALIDATION.md` |

Chi tiết từng checkbox: [docs/IMPLEMENTATION_CHECKLIST.md](./docs/IMPLEMENTATION_CHECKLIST.md).

---

## Khi gặp lỗi

1. Đọc log container — không đoán.
2. Sửa **trong phạm vi task hiện tại**.
3. Nếu blocker kiến trúc → ghi `ACTIVE_TASK.md` BLOCKERS + dừng; **không** đổi ARCHITECTURE im lặng.

---

## Output user cần thấy (không cần biết code)

Sau Phase 3 xong, user chỉ cần:

```bash
vagrant ssh
./cli.sh up
# Theo DEMO_RUNBOOK.md — curl webhook → xem Grafana → nhận Telegram
```

Cursor phải đảm bảo runbook chạy được trên lab VM.

---

## Câu chốt cho self-critique

- [ ] Đúng task ID trong ACTIVE_TASK?
- [ ] Khớp API_CONTRACT + DATA_MODEL?
- [ ] Memory limits ≤ bảng ARCHITECTURE?
- [ ] Secrets qua env/file, không hardcode?
- [ ] State files đã cập nhật?

**Pass hết → COMPLETED → task tiếp theo tự động.**
