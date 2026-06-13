# 07 — Scaling Roadmap

> **Audience:** CTO, CEO, Solution Architect
> **Mục đích:** Lộ trình scale hệ thống HDTV AI từ Nano/Pilot → Medium → Enterprise — dựa trên nghiệp vụ thực tế, có thời gian cụ thể, đặc biệt hướng tới **air-gapped LLM** (hoàn toàn không dùng mạng ngoài).

---

## Tại sao thiết kế hiện tại có thể scale?

Hệ thống được xây với **tư duy scale từ ngày đầu**, dù đang chạy trên single-node 6GB:

| Quyết định thiết kế | Lý do | Hỗ trợ scale như thế nào |
|---------------------|-------|--------------------------|
| LLM Router tách biệt hoàn toàn | Không hardcode model | Swap Gemini → local model không cần đổi code |
| MCP Server chuẩn protocol | Tool interface chuẩn hóa | Thêm tool mới mà không đụng agent core |
| Celery async worker | Background processing | Scale ngang bằng cách thêm worker |
| Chroma + PG tách biệt | Vector DB + relational DB độc lập | Migrate lên managed service dễ dàng |
| Traefik edge router | Service discovery + TLS | Thay bằng enterprise LB khi cần |
| GitOps + immutable deploy | Mọi thay đổi qua Git | Deploy lên K8s hay bare-metal cùng quy trình |
| Audit log tất cả tool calls | Observability từ đầu | Compliance + security khi scale enterprise |

---

## Lộ trình 3 giai đoạn

```
┌─────────────────────────┐     ┌──────────────────────────┐     ┌──────────────────────────┐
│   GIAI ĐOẠN 1: NANO     │────▶│   GIAI ĐOẠN 2: MEDIUM    │────▶│   GIAI ĐOẠN 3: ENTERPRISE│
│   (Hiện tại)            │     │   (2026 - 2027)           │     │   (2027+)                │
│                         │     │                           │     │                          │
│  • 1 client (EVN/HDTV)  │     │  • 3-5 clients            │     │  • 10+ clients           │
│  • 1 loại hồ sơ         │     │  • 5-10 loại hồ sơ        │     │  • N loại hồ sơ          │
│  • 2 nodes              │     │  • 5-10 nodes             │     │  • GPU cluster           │
│  • Gemini API (internet)│     │  • Hybrid LLM             │     │  • 100% Air-gapped LLM   │
│  • ~2.5GB RAM used      │     │  • ~16-32GB RAM           │     │  • Multi-tenant          │
└─────────────────────────┘     └──────────────────────────┘     └──────────────────────────┘
```

---

## Cấu trúc tài liệu

| File | Nội dung |
|------|----------|
| `01-current-state.md` | Baseline hiện tại: topology, nghiệp vụ, constraints |
| `02-medium-scale.md` | Scale vừa: multi-node, multi-client, multi-dossier-type |
| `03-enterprise-scale.md` | Scale lớn: air-gapped cluster, multi-tenant, fine-tuning |
| `04-airgap-llm-strategy.md` | **Chiến lược chuyển đổi hoàn toàn sang LLM nội bộ** |
