# System Architecture

> **Audience:** CTO, Solution Architect
> **Mục đích:** Toàn bộ bức tranh kiến trúc từ infrastructure đến AI layer — 3 levels of zoom.

| File | Mô tả |
|------|-------|
| `01-full-platform-diagram.md` | Nano Platform: 2-node topology, tất cả services |
| `02-hdtv-ai-system-diagram.md` | HDTV AI: FE→BE→Agent→LLM→Tools — chi tiết hơn |
| `03-end-to-end-flow.md` | Sequence diagram: user submit đến nhận kết quả |

## Design philosophy

**Layer 1 — Infrastructure:** Single-node constraints enforce discipline. Mọi service phải fit trong 6GB RAM → buộc phải thiết kế lean từ đầu.

**Layer 2 — Application:** FastAPI async + Celery worker tách biệt sync API khỏi async AI processing. API luôn responsive, dù agent đang chạy lâu.

**Layer 3 — AI Engine:** Plan→Execute→Reflect→Critic thay vì ReAct đơn giản — mỗi bước có chuyên gia riêng, output quality cao hơn đáng kể.
