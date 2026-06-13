# HDTV AI Platform — Tài liệu Thiết kế Hệ thống

![AI Agents Coverage](https://img.shields.io/badge/AI_Agents_Roadmap_Coverage-85%25-green)
![MCP](https://img.shields.io/badge/MCP-Supported-blue)
![RAG](https://img.shields.io/badge/RAG-Implemented-orange)
![Multi-Agent](https://img.shields.io/badge/Multi_Agent-Level_4-purple)
![Seed Data](https://img.shields.io/badge/Seed_Data-Real_EVN_Docs-orange)

> **Cập nhật:** 2026-06-13
> **Demo:** `COPY_PROJECT_DEVOPS=1 vagrant up` → `http://192.168.157.10:3080`
> **Login:** `admin@evnhanoi.vn` / `EVN@2024!`

---

## Overview

Tài liệu thiết kế hệ thống **HDTV AI Platform** — nền tảng số hóa quy trình phê duyệt tờ trình HĐTV EVN Hà Nội bằng AI Agent. Được cấu trúc để phục vụ 2 nhóm đọc chính: CEO (business value + delivery proof) và CTO (technical depth + production readiness).

**Điểm đặc biệt:** Seed data demo lấy từ 4 tờ trình thật của EVN Hà Nội — hồ sơ mua sắm UAV 198/TTr-EVNHANOI, bao gồm tên người thật, nội dung kỹ thuật thật, và kết quả thẩm tra thật.

---

## Cấu trúc thư mục

| Thư mục | Audience | Mục đích |
|---------|----------|----------|
| [`00-executive-summary/`](./00-executive-summary/) | **CEO + CTO** | Bức tranh tổng quan — đọc đầu tiên. Gồm platform overview, setup & seed guide, delivery proof. |
| [`01-system-architecture/`](./01-system-architecture/) | **CTO** | Biểu đồ kiến trúc 3 layers: Platform hạ tầng, HDTV AI System, End-to-End flow. |
| [`02-ai-agent-design/`](./02-ai-agent-design/) | **CTO** | AI Engine: Agent loop (Plan→Execute→Reflect→Critic), LLM Router, Memory, Human-in-the-Loop. |
| [`03-component-deep-dive/`](./03-component-deep-dive/) | **CTO** | Từng component: Execution Harness, MCP Server, Legal RAG, Frontend Architecture. |
| [`04-platform-engineering/`](./04-platform-engineering/) | **CTO** | DevOps: 2-node topology, CI/CD Pipeline, resource constraints 6GB. |
| [`05-security-and-reliability/`](./05-security-and-reliability/) | **CTO** | Bảo mật + Resilience: sandbox, circuit breaker, 14 alert rules, observability. |
| [`06-delivery-evidence/`](./06-delivery-evidence/) | **CEO** | Bằng chứng bàn giao: Sprint T-01→T-66, API coverage, Demo guide (data thật), Roadmap. |
| [`99-appendix/`](./99-appendix/) | **Internal** | Reference cũ + Scaling Roadmap (Nano → Medium → Enterprise → Air-gapped LLM). |

---

## Đọc nhanh theo vai trò

### CEO (15 phút)
1. [`00-executive-summary/README.md`](./00-executive-summary/README.md) — Tổng quan + business value
2. [`00-executive-summary/platform-at-a-glance.md`](./00-executive-summary/platform-at-a-glance.md) — Diagram + key numbers
3. [`00-executive-summary/setup-and-seed.md`](./00-executive-summary/setup-and-seed.md) — Cơ chế khởi tạo data thật
4. [`06-delivery-evidence/03-demo-guide.md`](./06-delivery-evidence/03-demo-guide.md) — Kịch bản demo 10 phút
5. [`00-executive-summary/delivery-proof.md`](./00-executive-summary/delivery-proof.md) — Timeline + milestone

### CTO (45 phút)
1. [`01-system-architecture/`](./01-system-architecture/README.md) — Kiến trúc tổng thể
2. [`02-ai-agent-design/`](./02-ai-agent-design/README.md) — AI Engine chiều sâu
3. [`05-security-and-reliability/`](./05-security-and-reliability/README.md) — Production readiness
4. [`03-component-deep-dive/`](./03-component-deep-dive/README.md) — Component internals

---

## Điểm công nghệ nổi bật

* ✅ **Real EVN Data**: Seed data từ 4 tờ trình thật (198/TTr-EVNHANOI UAV) — 8 users, 16 dossiers, BPMN quy trình thật
* ✅ **MCP (Model Context Protocol)**: SSE streaming, bảo mật, audit log đầy đủ
* ✅ **Plan-Execute-Reflect-Critic Loop**: Agent Level 4 — tự sửa lỗi, parallel tool execution
* ✅ **Memory phân tầng**: Short-term (PG) + Long-term Vector (Chroma) + Feedback learning
* ✅ **LLM Circuit Breaker**: Local llama-server → Gemini fallback, không bao giờ bị kẹt
* ✅ **Observability**: Prometheus + Grafana + Loki + Jaeger + 14 alert rules LLMOps
* ✅ **Auto-seed**: `HDTV_AUTO_SEED=true` → migrations + seed tự động khi deploy
* ✅ **18 DB migrations**: Zero manual SQL, Alembic quản lý toàn bộ schema
