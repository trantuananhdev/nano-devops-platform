# Giai đoạn 1 — Baseline: Nano Platform (Hiện tại)

> **Audience:** CTO, Solution Architect
> **Mục đích:** Baseline rõ ràng để so sánh khi scale — nghiệp vụ, topology, constraints, và điểm sẵn sàng để mở rộng.

---

## 1. Nghiệp vụ hiện tại

**Bài toán:** Tự động hóa thẩm định hồ sơ mua sắm/đầu tư cho EVN (Tập đoàn Điện lực Việt Nam) thông qua AI Agent.

**Quy trình nghiệp vụ (as-is với HDTV AI):**

```
Cán bộ nộp hồ sơ (PDF + metadata)
        ↓
Hệ thống nhận, lưu MinIO + PostgreSQL
        ↓
AI Agent tự động thẩm định:
  1. Planner: Lập kế hoạch kiểm tra
  2. Executor: Gọi các tool (ERP, DOffice, PMIS, Legal RAG, OCR)
  3. Reflector: Đánh giá kết quả, quyết định tiếp theo
  4. Critic: Kiểm tra chất lượng báo cáo
        ↓
Kết quả: Báo cáo thẩm định + Risk Level (LOW/MEDIUM/HIGH)
        ↓
Lãnh đạo xem kết quả real-time qua WebSocket
        ↓
Feedback → AI học từ phản hồi (Feedback Learning Loop)
```

**Loại hồ sơ hỗ trợ hiện tại:**
- Hồ sơ mua sắm thiết bị (procurement)
- Hồ sơ dự án đầu tư
- Hồ sơ tài chính/ngân sách

**Tool tích hợp hiện tại:**

| Tool | Hệ thống tích hợp | Mục đích |
|------|-------------------|----------|
| `ErpBudgetCheck` | ERP (giả lập) | Kiểm tra ngân sách còn lại |
| `ErpInventoryCheck` | ERP (giả lập) | Kiểm tra tồn kho hiện có |
| `DOfficeLookup` | DOffice (giả lập) | Tra cứu văn bản, quy định nội bộ |
| `PmisProjectCheck` | PMIS (giả lập) | Kiểm tra trạng thái dự án |
| `LegalGraphRAG` | Chroma (Legal DB) | Tra cứu pháp luật, nghị định, thông tư |
| `EcoOcrExtract` | Gemini Flash | Trích xuất nội dung từ PDF scan |
| `SandboxShell` | Docker sandbox | Chạy script tính toán an toàn |

---

## 2. Topology hiện tại

```
┌─────────────────────────────────────┐
│  Ubuntu Node (Acer laptop/workstation)│
│  RAM: ~8GB available                │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  llama-server (Gemma 4)     │    │
│  │  Port: 8081 (nội bộ)        │    │
│  │  RAM: ~4-6GB                │    │
│  └─────────────────────────────┘    │
│  ┌────────────┐  ┌─────────────┐    │
│  │ Caddy      │  │node-exporter│    │
│  │ :8080      │  │ Promtail    │    │
│  └────────────┘  └─────────────┘    │
└─────────────────────────────────────┘
                ↕ HTTPS :8080
┌─────────────────────────────────────────────────────┐
│  Alpine VM (VMware Vagrant)                         │
│  RAM: 6GB total, ~2.5GB used                        │
│                                                     │
│  ┌─────────┐ ┌──────┐ ┌───────┐ ┌─────┐            │
│  │Postgres │ │Redis │ │Chroma │ │Meili│            │
│  │ 384MB   │ │128MB │ │ 400MB │ │256MB│            │
│  └─────────┘ └──────┘ └───────┘ └─────┘            │
│  ┌──────────┐ ┌────────┐ ┌──────┐ ┌───────┐        │
│  │FastAPI   │ │Celery  │ │Beat  │ │MinIO  │        │
│  │ 384MB    │ │ 512MB  │ │ 64MB │ │ 256MB │        │
│  └──────────┘ └────────┘ └──────┘ └───────┘        │
│  ┌──────────┐ ┌──────────────────────────────┐      │
│  │Frontend  │ │ Traefik (Edge Router)         │      │
│  │ Nginx    │ │ Prometheus + Grafana + Loki   │      │
│  └──────────┘ └──────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

---

## 3. Constraints hiện tại

| Constraint | Giá trị | Lý do |
|------------|---------|-------|
| RAM Alpine VM | 6GB total | Single-node dev/pilot |
| LLM | Gemma 4 (local) + Gemini Flash (internet) | Pilot: chưa cần air-gapped |
| Concurrent users | ~5-10 | Demo/pilot scale |
| Dossier throughput | ~20-50 hồ sơ/ngày | Pilot 1 đơn vị |
| Tool integration | Mock/stub APIs | Chưa kết nối ERP thật |
| Storage | Local volumes | Chưa cần distributed storage |

---

## 4. Điểm mạnh kiến trúc — sẵn sàng để scale

```
✅ LLM Router: swap-able backend (Gemini → local model = đổi 1 config)
✅ MCP Server: standard protocol, thêm tool không đụng core
✅ Celery: horizontal scale bằng cách thêm worker container
✅ Chroma HTTP client: migrate lên Chroma Cloud hoặc dedicated server dễ dàng
✅ Traefik: đã có service discovery, TLS, routing rules
✅ Audit logs đầy đủ: plan_step_id, error_type, execution_ms → compliance ready
✅ GitOps: mọi thay đổi qua Git → deploy anywhere cùng flow
✅ Docker Compose: migrate lên K8s với minimal change (service definitions giữ nguyên)
```

---

## 5. Điểm cần giải quyết khi scale

| Vấn đề hiện tại | Giải pháp ở giai đoạn 2/3 |
|-----------------|---------------------------|
| Gemini API phụ thuộc internet | → Air-gapped LLM (xem `04-airgap-llm-strategy.md`) |
| Tool APIs là mock/stub | → Kết nối ERP/DOffice/PMIS thật |
| Single PostgreSQL cho tất cả | → Per-client schema isolation hoặc separate DB |
| Không có multi-tenant | → Tenant isolation ở application layer |
| No HA (single node) | → Active-passive hoặc K8s replicas |
| Manual RAG seed | → Auto ingestion pipeline đã có (T-27), cần mở rộng |
