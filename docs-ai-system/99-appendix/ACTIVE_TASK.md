# ACTIVE_TASK

**Task ID:** 5.lab  
**Title:** Lab validation + presenter rehearsal (Shopee Top-10)  
**Status:** pending  

---

## Objective

Runtime trên Vagrant VM: build services, smoke pass, browser rehearsal theo `DEMO_RUNBOOK.md`.

---

## Steps

1. `COPY_PROJECT_DEVOPS=1 vagrant provision` (nếu cần) → `vagrant ssh` → `./cli.sh up`
2. Chạy migration DB nếu Postgres đã tồn tại trước init mới:
   `docker exec -i platform-postgres psql -U postgres -f - < project_devops/platform/config/postgres/init/06-shopee-search-init.sh`
3. `bash project_devops/platform/ops/smoke-tests/smoke-test-shopee-search.sh`
4. `bash project_devops/platform/ops/smoke-tests/smoke-test-https-apps.sh`
5. Mở `https://shopee-search.nano.platform` — keyword + Top 10 + link Shopee
6. Checklist `shope-search/DEMO_RUNBOOK.md`

---

## DONE WHEN

- [ ] smoke-test-shopee-search.sh exit 0
- [ ] UI demo 2 keywords (cache lần 2 nhanh hơn)
- [ ] Hosts + rootCA trên máy presenter

---

## Completed this session (code)

- ✅ 5.d1–5.d5 implementation (API, SSE, UI, compose, docs, smoke script)

---

## Blockers

Postgres `shopee_db` chỉ auto-init trên volume mới — VM cũ cần chạy `06-shopee-search-init.sh` thủ công.
