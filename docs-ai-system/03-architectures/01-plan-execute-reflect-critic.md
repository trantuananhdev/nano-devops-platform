# Architecture: Plan-Execute-Reflect-Critic Loop

## Tổng quan

Đây là luồng chính của HDTV AI Agent, thay vì ReAct đơn thuần, chúng tôi chia thành các chuyên gia:

```
User Request
     ↓
[Planner] → Tạo Execution Plan (JSON)
     ↓
[Executor] → Chạy tools (parallel batches)
     ↓
[Reflector] → Phân tích kết quả, quyết định revise/continue/escalate
     ↓
[Critic] → Kiểm tra chất lượng báo cáo
     ↓
Final Result
```

## Components

### 1. Planner Agent (`planner.py`)
- **Purpose:** Tạo structured execution plan
- **Input:** Dossier + Memory + RAG + Feedback Lessons
- **Output:** JSON plan with `goal`, `max_revisions`, `steps[]`
- **Steps have:** `id`, `tool`, `parallel_group`, `depends_on`, `tool_input`

### 2. Executor Agent (`executor.py`)
- **Purpose:** Chạy tools theo plan
- **Features:**
  - Parallel execution (same `parallel_group`)
  - Sequential execution (via `depends_on`)
  - Update agent memory each step
  - Emit WebSocket events

### 3. Reflector Agent (`reflector.py`)
- **Purpose:** Phân tích tool results
- **Decisions:**
  - `sufficient`: Done, proceed to Critic
  - `revise`: Need more tools, revise plan
  - `escalate`: Need human input

### 4. Critic Agent (`critic.py`)
- **Purpose:** Quality control trước khi final report
- **Checks:**
  - Risk level consistency
  - Failed checks mentioned
  - Report completeness
- **Fallback:** Rule-based critic if LLM fails

## Human-in-the-Loop

Khi Reflector returns `escalate` or low confidence:
1. Tạo `clarification` record
2. Gửi event qua WebSocket
3. User trả lời
4. Resume appraisal with new context
- **File:** `app/services/clarification_service.py`

## File References

| Component | File |
|-----------|------|
| Planner | `app/services/orchestrator/planner.py` |
| Executor | `app/services/orchestrator/executor.py` |
| Reflector | `app/services/orchestrator/reflector.py` |
| Critic | `app/services/orchestrator/critic.py` |
| Main Agent | `app/services/orchestrator/react_agent.py` |
