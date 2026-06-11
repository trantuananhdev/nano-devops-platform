# LLM Router

## Tổng quan

LLM Router điều phối các agent role đến backend phù hợp dựa trên task, chi phí và tính khả dụng.

- **File:** `app/services/llm_router.py`
- **Backends:**
  - 🟢 **Ubuntu llama-server (Gemma 4) (local):** Chỉ chứa model local, không phụ thuộc mạng
  - 🔵 **Gemini 2.5 Flash API (remote):** Dùng cho các task cần domain knowledge chính xác

## Agent Roles & Backends

| Role | Backend | Purpose |
|------|---------|---------|
| `PLANNER` | 🟢 Ubuntu llama-server (Gemma 4) | Lập kế hoạch thực thi thẩm định (JSON) |
| `EXECUTOR` | 🟢 Ubuntu llama-server (Gemma 4) | Điều phối ReAct loop và tool calls |
| `REFLECTOR` | 🟢 Ubuntu llama-server (Gemma 4) | Phân tích kết quả và quyết định bước tiếp theo |
| `SUMMARY` | 🟢 Ubuntu llama-server (Gemma 4) | Tổng hợp báo cáo cuối cùng |
| `LEGAL` | 🔵 Gemini Flash API | Chuyên gia pháp lý EVN |
| `FINANCIAL` | 🔵 Gemini Flash API | Chuyên gia tài chính ERP |
| `OCR` | 🔵 Gemini Flash API | Trích xuất văn bản từ PDF |
| `CRITIC` | 🔵 Gemini Flash API | Kiểm duyệt bản thảo báo cáo |
| `TOOL_MOCK` | 🔵 Gemini Flash API | Giả lập phản hồi tool ERP/DOffice/PMIS |

## Features

1. **Circuit Breaker**
   - Trips if LLM API fails repeatedly
   - Auto-recovers after cool-down period
   - File: `app/core/circuit_breaker.py`

2. **API Key Rotation**
   - Multiple Gemini API keys
   - Load balance + cooldown on 429
   - File: `app/services/llm_router.py` + `config.py`

3. **Fallback Strategy**
   - If primary model fails, use secondary
   - Rule-based fallbacks for degraded mode
   - File: `app/services/orchestrator/critic.py` (rule-based fallback)

4. **JSON Mode**
   - Force structured JSON output for Planner
   - Reduces hallucinations
   - File: `app/services/orchestrator/planner.py`
