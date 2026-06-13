# Model Context Protocol (MCP) Server

> **Audience:** CTO, Solution Architect
> **Mục đích:** Đặc tả kiến trúc, luồng chạy và thiết kế bảo mật của lớp MCP Server — giải pháp kết nối chuẩn hóa cho AI-to-AI tool calling.

---

## 1. Thiết kế Lightweight (FastAPI Native)

Thay vì sử dụng các thư viện SDK cồng kềnh thường thấy của MCP, hệ thống HDTV AI tự triển khai (native implementation) trực tiếp bằng **FastAPI** trong file `app/routers/mcp.py`.

### Lợi ích của thiết kế này:
* **Zero Overhead**: Tránh cài thêm packages nặng, giảm dung lượng build image.
* **Full Control**: Dễ dàng tùy biến luồng dữ liệu, tích hợp trực tiếp với database transaction và metrics Prometheus sẵn có của FastAPI.
* **Async Native**: Phù hợp hoàn hảo với mô hình concurrency của ứng dụng.

---

## 2. Luồng hoạt động (Data & Control Flow)

Dưới đây là sơ đồ tương tác giữa **MCP Client** (như Claude Desktop hoặc một Agent ngoài), **MCP Server**, **Execution Harness** và **Data Store**:

```
┌──────────────┐             ┌──────────────┐             ┌───────────────┐             ┌───────────────┐
│  MCP Client  │             │  MCP Server  │             │  Exec Harness │             │  Database /   │
│ (Claude, etc)│             │ (FastAPI Router)           │ (tools/base)  │             │  Audit Logs   │
└──────────────┘             └──────────────┘             └───────────────┘             └───────────────┘
       │                            │                             │                             │
       │─── 1. Call Tool (POST) ───▶│                             │                             │
       │    X-MCP-API-Key: xxx      │                             │                             │
       │                            │─── 2. Auth DB lookup ───────┼────────────────────────────▶│
       │                            │    (prefixed & hashed)      │                             │
       │                            │◀── 3. Token Valid ──────────┼─────────────────────────────│
       │                            │                             │                             │
       │                            │─── 4. execute_tool() ──────▶│                             │
       │                            │    (with params)            │                             │
       │                            │                             │─── 5. Run check/lookup ────▶│
       │                            │                             │◀── 6. Raw results ──────────│
       │                            │◀── 7. Return result ────────│                             │
       │                            │                             │                             │
       │                            │─── 8. Validate output ──────│                             │
       │                            │    (against schema)         │                             │
       │                            │                             │                             │
       │                            │─── 9. Fire-and-forget ──────┼────────────────────────────▶│
       │                            │    McpCallLog logging       │                             │
       │◀── 10. Standard Response ──│                             │                             │
       │    (MCP content envelope)  │                             │                             │
```

---

## 3. Đặc tả các Endpoints

Hệ thống hỗ trợ đầy đủ bộ endpoint theo chuẩn MCP (phiên bản `2025-03-26`):

### 🟢 `GET /mcp/manifest`
Trả về năng lực (capabilities) và thông tin định danh của server.
* **Capabilities**:
  * `tools`: hỗ trợ listChanged = False.
  * `streaming`: hỗ trợ SSE streaming cho các long-running tools.
  * `audit`: hỗ trợ ghi audit trail.

### 🟢 `POST /mcp/tools/list`
Trả về danh sách các tool được cấu hình kèm theo **JSON Schema** mô tả input parameter cụ thể của từng tool.

Các tools chính được export bao gồm:
* `ErpBudgetCheck` (Kiểm tra ngân sách ERP)
* `ErpInventoryCheck` (Kiểm tra tồn kho ERP)
* `DOfficeLookup` (Tra cứu văn bản DOffice)
* `PmisProjectCheck` (Kiểm tra dự án PMIS)
* `LegalGraphRAG` (Tra cứu luật EVN qua GraphRAG)
* `EcoOcrExtract` (Trích xuất text từ văn bản PDF)

### 🟢 `POST /mcp/tools/call`
Gọi thực thi một tool đồng bộ. Server nhận parameters, đẩy qua lớp *Execution Harness*, validate kết quả trả về, ghi log và đóng gói dữ liệu vào cấu trúc chuẩn của MCP.

### 🟢 `POST /mcp/tools/call/stream` (SSE Transport)
Đối với các tool chạy lâu (như `EcoOcrExtract` hoặc `LegalGraphRAG` với tập tài liệu lớn), client có thể yêu cầu streaming qua Server-Sent Events (SSE).
* Server liên tục yield các event `progress` hiển thị thời gian đã chạy (`elapsed`) và trạng thái (`started`, `running`).
* Khi hoàn thành, server yield event `result` chứa dữ liệu cuối hoặc event `error` nếu thất bại.

---

## 4. Cơ chế bảo mật và Phân quyền

### Xác thực hai tầng (Defense in Depth)
Mọi request đến MCP endpoints (ngoại trừ `/health`) bắt buộc phải đính kèm header `X-MCP-API-Key`.
1. **DB-first Verification**: Server truy vấn bảng `api_keys` tìm key có loại `ApiKeyType.mcp` và active. Key được so khớp an toàn bằng cách băm bcrypt (không lưu plaintext key).
2. **.env Fallback**: Nếu DB tạm thời không khả dụng, hệ thống tự động fallback kiểm tra key cấu hình ở biến `.env` `MCP_API_KEY` nhằm đảm bảo hệ thống không bị gián đoạn (zero-downtime).

---

## 5. Đảm bảo chất lượng & Kiểm toán (Validation & Audit)

### Kiểm thử Schema đầu ra (Output Validation)
Trước khi đóng gói dữ liệu trả về cho Client, MCP Server đối chiếu dữ liệu đầu ra với cấu trúc định nghĩa trong `_TOOL_OUTPUT_SCHEMAS`.
* **Ví dụ**: `ErpBudgetCheck` bắt buộc phải trả về hai thuộc tính `approved_budget` và `exceeded`.
* **Cơ chế degraded**: Nếu thiếu trường, server không ngắt kết nối mà đánh dấu cờ `output_incomplete: True` và đính kèm `validation_hint` để hướng dẫn AI Client tự sửa truy vấn hoặc fallback an toàn.

### Ghi nhật ký MCP (Audit Logging)
Sau mỗi lần thực thi tool (kể cả sync hay stream), hệ thống tạo một luồng chạy nền (fire-and-forget task) ghi chép chi tiết vào bảng `mcp_call_logs`:
* `api_key_prefix` (Chỉ lưu 8 ký tự đầu của key để truy vết, không bao giờ lưu raw key).
* `tool_name`, `inputs`, `outputs` (dữ liệu đầu vào và đầu ra).
* `is_error` và `is_streaming`.
* `execution_ms` (thời gian thực thi).
* `missing_fields` (danh sách trường bị thiếu nếu validate fail).
