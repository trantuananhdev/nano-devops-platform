# Roadmap Coverage — 85% of roadmap.sh/ai-agents

> **Audience:** CTO
> **Mục đích:** So sánh với industry standard AI agents roadmap để chứng minh độ phủ kỹ thuật.

---

## Tổng quan

| Domain | Coverage | Ghi chú |
|--------|----------|---------|
| LLM Fundamentals | 90% | Router, circuit breaker, token optimization |
| Agent Loop | 95% | Plan→Execute→Reflect→Critic hoàn chỉnh |
| Prompt Engineering | 80% | Role-based, JSON mode, context engineering |
| Tools & Function Calling | 90% | Harness, validation, parallel, chain |
| Model Context Protocol | 90% | Full spec: manifest, list, call, SSE, audit |
| Agent Memory | 85% | Short/Long-term, RAG, feedback, preferences |
| Agent Architectures | 90% | ReAct + Plan-Execute-Reflect-Critic |
| Evaluation & Testing | 65% | Audit logs đầy đủ, cần thêm unit tests |
| Security | 85% | API keys, sandbox, circuit breaker, RBAC |
| **Overall** | **85%** | Tốt cho production pilot |

---

## Highlights — Vượt trội so với tiêu chuẩn

**✅ MCP Full Implementation** — Nhiều hệ thống chỉ support sync call. HDTV có:
- Sync + **SSE Streaming**
- DB-backed API Key auth (không chỉ .env)
- Audit logs per call
- Output schema validation

**✅ Memory Hierarchy** — Không chỉ short-term:
- Long-term Chroma với vector search
- Cross-dossier memory (metadata filter)
- Feedback learning loop (separate collection)
- User preferences per role

**✅ Circuit Breaker** — Production-grade:
- CLOSED/OPEN/HALF_OPEN state machine
- Separate breakers per backend
- Metrics + Grafana alert

**✅ Parallel Tool Execution** — asyncio.gather với parallel_group trong plan:
- Throughput ~3x so với sequential
- Separate audit log per tool trong batch
- Wall time logged

---

## Gap Analysis — Còn thiếu gì?

| Gap | Priority | Ghi chú |
|-----|----------|---------|
| Unit test coverage | Medium | Có static pytest, cần thêm integration tests |
| Few-shot examples trong prompts | Low | Cải thiện output quality theo thời gian |
| Red teaming / adversarial testing | Medium | Cần khi deploy production |
| Evaluation framework (LLM-as-judge) | Medium | Giai đoạn 2 |
| LangChain / framework | N/A | Quyết định không dùng để full control |

---

## Quyết định không dùng LangChain

**Tại sao không dùng LangChain/LlamaIndex?**

| | LangChain | HDTV (custom) |
|--|----------|---------------|
| Control | Black box | ✅ Full control |
| Debugging | Khó trace | ✅ Custom audit logs |
| Cost | Overhead | ✅ Lean |
| Flexibility | Framework constraints | ✅ Design to fit nghiệp vụ |
| Vendor lock-in | Có | ✅ Không |

**Kết quả:** Team hiểu 100% mọi dòng code trong agent pipeline. Không bị surprise khi LangChain update breaking change.
