# System Design Documentation — HDTV-AI Platform

> Bộ tài liệu thiết kế hệ thống theo nhiều tầng abstraction.
> Đọc theo thứ tự từ L0 → L4 để có bức tranh đầy đủ.

---

## Tầng Abstraction

| File | Tầng | Audience | Mô tả |
|------|------|----------|-------|
| [00-overview.md](00-overview.md) | **L0** | CEO, tất cả | 10-second pitch, bài toán, 5 bước flow |
| [01-platform-topology.md](01-platform-topology.md) | **L1** | CTO, DevOps | 2-node topology, 9 services, network flow |
| [02-hdtv-ai-subsystem.md](02-hdtv-ai-subsystem.md) | **L2** | Backend Lead | Request lifecycle, LLM router, data models, WS events |
| [03-agent-orchestration.md](03-agent-orchestration.md) | **L3** | AI Engineer | State machine, memory hierarchy, HITL, prompts |
| [04-component-design.md](04-component-design.md) | **L4** | Developer | Context manager, memory scoring, confidence, tools |
| [05-frontend-architecture.md](05-frontend-architecture.md) | **L3** | FE Developer | Vue 3 structure, Pinia stores, WS, routing |

---

## Đọc nhanh theo vai trò

**CEO (5 phút):** `00-overview.md` → phần "Bài toán" và "Số liệu demo"

**CTO (15 phút):** `00-overview.md` → `01-platform-topology.md` → `../02-ai-agent-design/00-agent-level-assessment.md`

**Solution Architect (30 phút):** L0 → L1 → L2 → L3

**AI Engineer (thực hiện improvement):** L3 (`03-agent-orchestration.md`) + L4 (`04-component-design.md`)

**Frontend Dev:** `05-frontend-architecture.md`

**DevOps:** `01-platform-topology.md` + `../00-executive-summary/setup-and-seed.md`

---

## Liên kết tài liệu liên quan

- [Agent Level Assessment](../02-ai-agent-design/00-agent-level-assessment.md) — HDTV-AI đang ở Level 4.3/5.0
- [Setup & Seed Guide](../00-executive-summary/setup-and-seed.md) — COPY_PROJECT_DEVOPS=1, HDTV_AUTO_SEED
- [Demo Guide](../06-delivery-evidence/03-demo-guide.md) — 8 demo scenes cho CEO/CTO presentation
- [Delivery Proof](../00-executive-summary/delivery-proof.md) — checklist đã hoàn thành
