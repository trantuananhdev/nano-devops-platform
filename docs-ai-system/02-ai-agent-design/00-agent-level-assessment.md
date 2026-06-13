# Agent Level Assessment — HDTV-AI

> **Audience:** CTO
> **Mục đích:** Đánh giá khách quan HDTV-AI đang ở level nào trong thang đo agentic AI, và roadmap lên level cao hơn.
> **Cập nhật:** 2026-06-13

---

## Thang đo Agent Levels

| Level | Khả năng | Ví dụ |
|-------|----------|-------|
| **L1** — LLM Basic | Gọi LLM, trả lời câu hỏi | ChatGPT single turn |
| **L2** — Tool Use | Gọi external tools, chain of thought | LLM + search API |
| **L3** — Memory + Planning | Multi-step planning, nhớ context | Tác vụ phức tạp nhiều bước |
| **L4** — Reflect + Critic + HITL | Tự sửa lỗi, đánh giá chất lượng, human handoff | HDTV-AI hiện tại |
| **L5** — Multi-Agent + Autonomous | Agent gọi agent, tự cải thiện | AutoGPT, CrewAI |

---

## HDTV-AI: Level **4.3 / 5.0**

### ✅ Đã đạt (Level 4 core)

| Capability | Implementation | File |
|-----------|----------------|------|
| **Structured planning** | LLM tạo ExecutionPlan JSON với steps + parallel_group + depends_on | `planner.py` |
| **Parallel tool execution** | asyncio.gather theo parallel_group, topological sort dependencies | `executor.py` |
| **Tool chaining** | EcoOcrExtract → LegalGraphRAG tự động theo DB config | `chain_executor.py` |
| **Reflection** | LLM đánh giá kết quả: sufficient / revise / escalate | `reflector.py` |
| **Critic quality gate** | LLM review báo cáo cuối, tự re-execute nếu bị reject | `critic.py` |
| **Short-term memory** | AgentMemory rows trong PostgreSQL (step + thought + observation) | `entities.py` |
| **Long-term memory** | Chroma vector DB — semantic search cross-session | `vector_store.py` |
| **Cross-dossier memory** | Retrieve lessons từ hồ sơ tương tự (unit + risk_level filter) | `retriever.py` |
| **Feedback learning** | Negative feedback → Chroma → inject vào planner lần sau | `retriever.py` |
| **Human-in-the-Loop** | Pause khi tool conflict hoặc low confidence → resume với answer | `clarification_service.py` |
| **Role-based prompting** | 9 chuyên biệt: Planner/Executor/Legal/Financial/OCR/Reflector/Critic/Summary/ToolMock | `llm_router.py` |
| **LLM circuit breaker** | CLOSED → OPEN → HALF_OPEN với sliding window failure count | `circuit_breaker.py` |
| **Dual LLM backend** | Local llama-server (PLANNER/EXECUTOR/REFLECTOR/SUMMARY) + Gemini (LEGAL/FINANCIAL/OCR/CRITIC) | `llm_router.py` |
| **Context window management** | Priority-based eviction: giữ failures + plans, drop routine observations | `context_manager.py` |
| **Confidence scoring** | Mỗi check có confidence 0.0-1.0 để Critic đánh giá độ chắc chắn | `helpers.py` |
| **Configurable risk rules** | eval() sandbox với whitelist builtins, rules từ DB | `react_agent.py` |
| **Full audit trail** | AiAuditLog mọi tool call: tool_name, execution_ms, inputs, outputs, plan_step_id | `entities.py` |
| **Prometheus metrics** | LLM calls, tool duration, agent plans, critic rejections, context truncations | `metrics.py` |

### ⚠️ Cần cải thiện (để đạt Level 4.5+)

| Gap | Mô tả | Priority |
|-----|-------|----------|
| **RAG tool bridge** | LegalGraphRAG gọi Gemini mock, chưa query Chroma `legal_docs` collection thật | High |
| **Confidence calibration** | Confidence score hiện tại là heuristic, chưa được calibrate theo historical accuracy | Medium |
| **Memory consolidation** | Không có periodic summarization — memories accumulate indefinitely | Medium |
| **Working memory** | Không có in-loop scratchpad riêng biệt với long-term memory | Low |
| **Emergent planning** | Planner chưa học từ successful plan patterns (chỉ từ negative feedback) | Low |

### ❌ Chưa có (Level 5 territory)

| Capability | Lý do chưa cần | Roadmap |
|-----------|----------------|---------|
| **Multi-agent coordination** | 1 orchestrator đủ cho use case hiện tại | Medium scale (2026-27) |
| **Agent-spawning agents** | Overcomplicated for current problem scope | Enterprise (2027+) |
| **Self-improving prompts** | Cần labeled data và eval pipeline trước | Enterprise (2027+) |

---

## Tại sao chọn Level 4 architecture cho HDTV?

**Bài toán cụ thể:** Thẩm định tờ trình HĐTV — có quy trình rõ, có tiêu chí kiểm tra rõ, cần audit trail, không cần agent tự quyết mọi thứ.

Level 4 là đúng vì:
- **Plan → Execute**: Biết trước cần kiểm tra gì (pháp lý, tài chính, kỹ thuật)
- **Reflect**: Biết khi nào kết quả không đủ (missing checks)
- **Critic**: Đảm bảo báo cáo cuối đạt chất lượng trước khi gửi lãnh đạo
- **HITL**: Khi AI không chắc → hỏi người, không tự quyết
- **Audit trail**: Mọi bước đều có log — compliance requirement của EVN

Level 5 (fully autonomous) sẽ phản tác dụng — lãnh đạo cần kiểm soát, không cần AI tự quyết.

---

## Agent Level sau khi improvements (2026-06-13)

Sau 4 cải tiến đã thực hiện:

| Improvement | Before | After |
|------------|--------|-------|
| Context eviction | FIFO (mất reasoning quan trọng) | Priority-based (giữ failures + plans) |
| Memory retrieval | Pure cosine distance | Composite: relevance×0.6 + recency×0.3 + failure_boost×0.1 |
| Planner context | `title + doc_no + unit` only | + `pdf_excerpt` + `risk_level` + specific tool queries |
| Check confidence | Binary pass/fail | Confidence score 0.0-1.0 per check |

**Current level: 4.3/5.0** — solidly Level 4, approaching 4.5.
