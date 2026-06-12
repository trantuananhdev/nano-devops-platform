# Execution Harness — Tool Dispatch Layer

> **Audience:** CTO
> **Mục đích:** Thiết kế lớp dispatch giữa Agent và Tools — đây là "safety net" đảm bảo mọi tool call clean, reliable, auditable.

---

## Vấn đề nếu không có Harness

```python
# Naive tool call — không có harness
result = await erp_budget_check(params)
# Vấn đề:
# 1. params có thể thiếu field → crash không rõ lý do
# 2. Không có timeout → Gemini treo 10 phút → agent bị blocked
# 3. Network blip → task fail hoàn toàn dù retry 1 lần là xong
# 4. Không biết "lỗi này là do gì?" → agent không tự fix được
# 5. Không audit → không biết agent đã làm gì
```

---

## Harness Architecture

```
Agent calls execute_tool("ErpBudgetCheck", {"dossier_id": 1, "doc_no": "MX-2025-001"})
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: Schema Validation                                 │
│  _validate_tool_input(name, params)                         │
│  • Check required fields per tool                           │
│  • Check field types                                        │
│  → If fail: return {error_type: BAD_INPUT, hint: "..."} FAST│
└─────────────────────────────────────────────────────────────┘
                              ↓ (if valid)
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 2: Domain Validation (Handler)                       │
│  handler = get_handler(name)  → ErpBudgetHandler            │
│  handler.validate_input(params)                             │
│  • Check doc_no format (VD: "MX-YYYY-NNN")                  │
│  • Check dossier_id > 0                                     │
│  • Check amount trong VND range                             │
│  → If fail: return {error_type: BAD_INPUT, hint: "..."}     │
└─────────────────────────────────────────────────────────────┘
                              ↓ (if valid)
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 3: Execute with Timeout                              │
│  asyncio.wait_for(fn(params), timeout=30s)                  │
│  → If timeout: return {error_type: TRANSIENT, error: "timeout"} │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 4: Error Taxonomy + Audit                            │
│  Classify exception → ToolErrorType                         │
│  AiAuditLog.insert(tool_name, inputs, outputs,              │
│                    plan_step_id, error_type, execution_ms)  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 5: Retry (in BatchExecutor)                          │
│  if error_type in {TRANSIENT, UNKNOWN}: retry 1x, sleep 2s  │
│  if error_type in {BAD_INPUT, UNAVAILABLE}: no retry        │
└─────────────────────────────────────────────────────────────┘
                              ↓
                     Return result to Agent
```

---

## Error Taxonomy

| Type | Ý nghĩa | Agent action | Retry? |
|------|---------|-------------|--------|
| `TRANSIENT` | Network/timeout tạm thời | Wait và retry | ✅ 1x |
| `BAD_INPUT` | Params sai/thiếu | Sửa params (từ Planner) | ❌ |
| `UNAVAILABLE` | Tool/service down | Dùng fallback response | ❌ |
| `UNKNOWN` | Lỗi không xác định | Retry 1x, sau đó escalate | ✅ 1x |

**Tại sao phân loại quan trọng?** Agent cần biết error type để quyết định tiếp theo — retry, sửa plan, hay escalate. Error string `"connection refused"` không đủ thông tin.

---

## Tool Registry

```python
# tools/base.py
_TOOL_INPUT_REQUIRED_FIELDS = {
    "LegalGraphRAG":     ["query"],
    "ErpBudgetCheck":    ["dossier_id", "doc_no"],
    "ErpInventoryCheck": ["dossier_id"],
    "DOfficeLookup":     ["query"],
    "PmisProjectCheck":  ["dossier_id"],
    "EcoOcrExtract":     ["dossier_id"],
    "SandboxShell":      ["command"],
}

STATIC_TOOL_IMPLS: dict[str, Callable] = {
    "LegalGraphRAG":     legal_graph_rag,
    "ErpBudgetCheck":    erp_budget_check,
    "ErpInventoryCheck": erp_inventory_check,
    "DOfficeLookup":     doffice_lookup,
    "PmisProjectCheck":  pmis_project_check,
    "EcoOcrExtract":     eco_ocr_extract,
    "SandboxShell":      sandbox_shell,
}
```

---

## Tool Chaining

```python
# Tool A output → Tool B input (không cần LLM để map)
TOOL_CHAINS = {
    "EcoOcrExtract": {
        "chains_to": "LegalGraphRAG",
        "output_mapping": {"extracted_text": "query"}
    }
}

# chain_executor.py
async def execute_with_chain(tool_name, params, observations):
    result = await execute_tool(tool_name, params)

    chain_config = TOOL_CHAINS.get(tool_name)
    if chain_config and result.get("extracted_text"):
        chained_tool = chain_config["chains_to"]
        chained_params = {
            chain_config["output_mapping"]["extracted_text"]: result["extracted_text"]
        }
        chained_result = await execute_tool(chained_tool, chained_params)
        result["chained_result"] = chained_result

    return result
```

**Benefit:** Tiết kiệm 1 LLM round-trip cho mỗi chain. Nếu có 3 chains, tiết kiệm 3 LLM calls.

---

## Metrics

```python
TOOL_CALLS = Counter("hdtv_tool_calls_total", ["tool_name", "status"])
TOOL_RETRIES = Counter("hdtv_tool_retries_total", ["tool_name", "error_type"])
TOOL_TIMEOUTS = Counter("hdtv_tool_timeouts_total", ["tool_name"])
TOOL_INPUT_VALIDATION_ERRORS = Counter(
    "hdtv_tool_input_validation_errors_total", ["tool_name"])
```
