# Agent Loop Architecture — Plan→Execute→Reflect→Critic

> **Audience:** CTO
> **Mục đích:** Giải thích tại sao chọn kiến trúc multi-agent pipeline thay vì ReAct đơn giản, và design decision đằng sau từng bước.

---

## Vấn đề với ReAct đơn thuần

ReAct (Reason→Act→Observe) là pattern phổ biến nhất nhưng có giới hạn rõ ràng với nghiệp vụ thẩm định:

```
ReAct thuần:                    Vấn đề:
─────────────                   ────────
Reason: Cần check ngân sách     ✅ OK
Act: Call ErpBudgetCheck        ✅ OK
Observe: Budget = 5 tỷ         ✅ OK
Reason: Cần check inventory     ✅ OK
Act: Call ErpInventoryCheck     ✅ OK
Observe: Inventory thiếu       ✅ OK
Reason: Cần check legal        ✅ OK
Act: Call LegalRAG              ✅ OK
...
Reason: Viết báo cáo           ⚠️  Agent tự viết, không ai kiểm tra
Act: Generate report            ⚠️  Không có quality gate
→ Risk: báo cáo sai, thiếu sót, không nhất quán
```

**3 vấn đề cốt lõi của ReAct:**
1. **Không có planning phase** → agent chọn tool theo từng bước, không thấy toàn bức tranh
2. **Sequential execution** → các tool độc lập không chạy song song, chậm
3. **No quality gate** → output cuối không được review độc lập

---

## Giải pháp: Plan→Execute→Reflect→Critic

```
┌─────────────────────────────────────────────────────────────────────┐
│  INPUT: Hồ sơ + Context (Memory + RAG + Feedback Lessons)           │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: PLANNER (llama-server, JSON mode)                          │
│                                                                     │
│  Input:  Dossier metadata + memory context + legal context          │
│  Output: Structured JSON plan                                       │
│  {                                                                  │
│    "goal": "Thẩm định hồ sơ mua sắm máy biến áp 110kV",            │
│    "max_revisions": 2,                                              │
│    "steps": [                                                       │
│      {"id": "s1", "tool": "ErpBudgetCheck",                         │
│       "parallel_group": "financial"},                               │
│      {"id": "s2", "tool": "ErpInventoryCheck",                      │
│       "parallel_group": "financial"},       ← Chạy song song s1+s2 │
│      {"id": "s3", "tool": "LegalGraphRAG",                          │
│       "parallel_group": "legal"},                                   │
│      {"id": "s4", "tool": "EcoOcrExtract",                          │
│       "parallel_group": "legal",                                    │
│       "depends_on": "s3"},                 ← s4 sau s3             │
│      ...                                                            │
│    ]                                                                │
│  }                                                                  │
│                                                                     │
│  Design rationale: JSON mode giảm hallucination, parallel_group     │
│  cho phép executor biết tool nào chạy đồng thời.                   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: EXECUTOR                                                   │
│                                                                     │
│  Group steps by parallel_group:                                     │
│  financial: [ErpBudgetCheck, ErpInventoryCheck] → asyncio.gather   │
│  legal:     [LegalGraphRAG] → then [EcoOcrExtract] (depends_on)    │
│                                                                     │
│  Per tool: Harness validates → timeout(30s) → retry(1x) → audit    │
│  Chain: EcoOcrExtract.extracted_text → LegalGraphRAG.query          │
│                                                                     │
│  WS events: tool_executing, tool_result, step_completed             │
│                                                                     │
│  Design rationale: parallel_group tăng throughput ~3x.             │
│  Chain executor loại bỏ round-trip LLM để map outputs.             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: REFLECTOR (llama-server)                                   │
│                                                                     │
│  Input:  All tool results + current observations                    │
│  Output: verdict + optional revised_steps                           │
│                                                                     │
│  Verdicts:                                                          │
│  - "sufficient": tất cả checks đủ → proceed to Critic              │
│  - "revise": thiếu check nào đó → revised_steps để re-execute      │
│  - "escalate": không chắc chắn → HITL clarification                │
│                                                                     │
│  Max revisions: 2 (prevent infinite loop)                           │
│  Fallback: rule-based (nếu LLM fail) → count failed checks          │
│                                                                     │
│  Design rationale: Reflector tách biệt khỏi Executor → có thể       │
│  nhìn toàn bộ kết quả một lần, không bị bias bởi từng bước.        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: CRITIC (Gemini Flash hoặc llama fallback)                  │
│                                                                     │
│  Input:  Draft report + checks list + risk_level                    │
│  Output: {approved: bool, issues: [], suggested_fixes: []}          │
│                                                                     │
│  Checks:                                                            │
│  - Risk level consistent với failed checks?                         │
│  - Failed checks được đề cập trong báo cáo?                         │
│  - Báo cáo có đủ thông tin cho lãnh đạo quyết định?                │
│                                                                     │
│  If rejected: re-execute missing tools → regenerate report (max 2x) │
│  Fallback: rule-based critic (kiểm tra regex patterns)              │
│                                                                     │
│  Design rationale: Critic là independent reviewer → không bị ảnh   │
│  hưởng bởi decision của Planner. Dùng Gemini (domain knowledge)    │
│  hoặc fine-tuned model ở giai đoạn sau.                            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  OUTPUT: AppraisalResult (saved to PostgreSQL)                      │
│  {resolution_md, risk_level, critic_verdict, plan_revision_count}   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Role-Based Prompt Profiles

Cùng một hồ sơ, nhưng output khác nhau tùy người xem:

| Role | user_id | System prompt style | Output |
|------|---------|---------------------|--------|
| `hdtv_leader` | 1 | Concise, risk-first | 1 trang tóm tắt cho lãnh đạo HĐTV |
| `dept_head` | 2 | Checklist + supplements | 2-3 trang với kiến nghị bổ sung |
| `admin` | 3 | Full audit, no summarization | Full raw output, không filter |
| `specialist` | 4 | Technical detail | Báo cáo kỹ thuật đầy đủ |

```python
# Sử dụng: POST /dossiers/{id}/appraise?user_id=1
# Planner, Executor, Reflector, Summary đều nhận role-specific prompt
prompt = prompt_builder.build_system_prompt(
    role="hdtv_leader",
    tools=available_tools,
    preferences=user_preferences
)
```

---

## So sánh ReAct vs Plan→Execute→Reflect→Critic

| Tiêu chí | ReAct đơn giản | Plan→Execute→Reflect→Critic |
|---------|----------------|------------------------------|
| Tool execution | Sequential | **Parallel batches** |
| Quality gate | Không có | **Critic independent reviewer** |
| Planning | Greedy step-by-step | **Full plan trước khi execute** |
| Revision | Không | **Max 2 revisions tự động** |
| Human intervention | Không | **HITL khi low confidence** |
| Output personalization | Không | **Role-based prompt profiles** |
| LLM cost | Thấp | Cao hơn (~4 LLM calls/appraisal) |
| Quality | Thấp-Trung | **Cao** |

**Trade-off chấp nhận được:** Tốn nhiều LLM calls hơn, nhưng output quality đủ để lãnh đạo quyết định mà không cần re-review thủ công.
