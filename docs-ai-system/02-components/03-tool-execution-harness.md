# Tool Execution Harness

## Tổng quan

Execution harness là lớp đảm bảo mỗi tool call được validate, timeout, retry, và audit.

- **File:** `app/services/tools/base.py`

## Error Taxonomy

| Type | Mô tả | Hành động |
|------|-------|-----------|
| `TRANSIENT` | Lỗi mạng/timeout | Retry |
| `BAD_INPUT` | Input thiếu/hỏng | Không retry, fix input |
| `UNAVAILABLE` | Tool không tìm thấy | Skip hoặc fallback |
| `UNKNOWN` | Lỗi không xác định | Retry 1 lần rồi escalate |

## Features

1. **Input Validation**
   - Required fields (per tool)
   - Type checking
   - Domain-level validation via handlers

2. **Timeout**
   - Per-tool timeout (default: `settings.tool_execution_timeout_s`)
   - `TOOL_TIMEOUTS` metric

3. **Fallback Responses**
   - DB-configured via `ToolConfig.fallback_response`
   - Used when tool fails

4. **Audit Logs**
   - All calls logged to `ai_audit_logs`
   - Includes: `plan_step_id`, `tool_name`, `execution_ms`, `error_type`

## Tools List

| Tool | Mô tả | Category |
|------|-------|----------|
| `LegalGraphRAG` | Tra cứu pháp luật | legal |
| `ErpBudgetCheck` | Kiểm tra ngân sách ERP | financial |
| `ErpInventoryCheck` | Kiểm tra tồn kho ERP | financial |
| `DOfficeLookup` | Tra cứu văn bản DOffice | admin |
| `PmisProjectCheck` | Kiểm tra dự án PMIS | project |
| `EcoOcrExtract` | OCR trích xuất PDF | ocr |
| `SandboxShell` | Chạy shell trong sandbox | sandbox |

## Quick Example

```python
from app.services.tools import base

result, elapsed_ms = await base.execute_tool(
    "LegalGraphRAG",
    {"query": "Quy định thẩm định"}
)
```
