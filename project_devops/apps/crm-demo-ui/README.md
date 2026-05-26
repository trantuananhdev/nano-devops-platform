# TNT Shop — Trung tâm tiếp nhận CRM (Demo UI)

**Phase 4 frontend** — giao diện tiếng Việt, mô hình **một trang đổ traffic** + kịch bản đa ngôn ngữ SEA.

## Docs

- Kế hoạch: [../ai-crm-pipeline/docs/DEMO_PLATFORM_PLAN.md](../ai-crm-pipeline/docs/DEMO_PLATFORM_PLAN.md)
- Tasks: [../ai-crm-pipeline/docs/DEMO_PLATFORM_CHECKLIST.md](../ai-crm-pipeline/docs/DEMO_PLATFORM_CHECKLIST.md) Task **4.7**

## Stack (locked)

React 18 + Vite + TypeScript + Tailwind + TanStack Query + Recharts + SSE

## URL

`https://crm-demo.nano.platform` (Traefik HTTPS)

API demo gọi **cùng origin** (`/api/v1/*`) — nginx trong container proxy tới `crm-ingestion-api`.  
Presenter **chỉ cần** thêm `crm-demo.nano.platform` vào hosts (không bắt buộc `crm-ingest` cho UI).

## Nghiệp vụ demo

- Panel **Đổ traffic**: gọi `POST /api/v1/demo/traffic-burst` theo `scenarios.json`
- **Quy trình CRM** 5 bước + **AI giải quyết gì** (presenter)
- **Chi tiết khách**: tên, SĐT, đơn, tin gốc TL/ID/MY, tóm tắt AI

Kịch bản presenter: [../ai-crm-pipeline/docs/DEMO_RUNBOOK.md](../ai-crm-pipeline/docs/DEMO_RUNBOOK.md)

## Dev local

```bash
npm install
npm run dev
# VITE_CRM_API_BASE=https://crm-ingest.nano.platform
```

## Build / deploy

```bash
npm install && npm run build
docker build -t crm-demo-ui .
```

Compose service: `crm-demo-ui` in `docker-compose.apps.yml`.
