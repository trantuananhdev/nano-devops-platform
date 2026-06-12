# AI Agent Design

> **Audience:** CTO, AI/ML Engineer
> **Mục đích:** Giải thích tư duy thiết kế AI Engine — tại sao chọn kiến trúc này, trade-offs là gì.

| File | Nội dung |
|------|----------|
| `01-agent-loop-architecture.md` | Plan→Execute→Reflect→Critic: tại sao không dùng ReAct đơn thuần |
| `02-llm-router.md` | Circuit breaker, key rotation, role→backend mapping |
| `03-agent-memory.md` | 3-layer memory: short-term, long-term, feedback |
| `04-human-in-the-loop.md` | HITL: khi nào pause, khi nào resume, design rationale |

## Core Design Decision

**Vấn đề với ReAct thuần túy** (Reason→Act→Observe loop đơn giản):
- Agent tự plan và tự execute → dễ lạc hướng sau nhiều bước
- Không có quality gate → output không kiểm soát được
- Không học từ feedback → lặp lại lỗi tương tự

**Giải pháp: Specialized Agents Pipeline**
- Mỗi bước có LLM role riêng → prompt được optimize cho từng nhiệm vụ
- Critic là quality gate độc lập → không bị bias bởi việc đã execute
- Feedback loop → agent cải thiện theo thời gian
