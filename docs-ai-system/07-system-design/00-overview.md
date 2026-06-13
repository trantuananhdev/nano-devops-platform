# HDTV-AI Platform — System Design Overview

> **Tầng L0: 10-second pitch**
> **Audience:** CEO, CTO, mọi stakeholder
> **Cập nhật:** 2026-06-13

---

## Một câu mô tả hệ thống

**HDTV-AI** là nền tảng số hóa quy trình phê duyệt tờ trình Hội đồng thành viên EVN Hà Nội — thay thế nghiệp vụ thẩm định thủ công bằng AI Agent tự động kiểm tra pháp lý, tài chính, kỹ thuật và đưa ra báo cáo cho lãnh đạo.

---

## Bài toán

| Trạng thái cũ (manual) | Trạng thái mới (HDTV-AI) |
|------------------------|--------------------------|
| Chuyên viên đọc tờ trình → ghi chú thủ công | AI Agent tự chạy 8 loại kiểm tra song song |
| Mỗi hồ sơ mất 2-5 ngày để thẩm tra | Kết quả sơ bộ trong 3-10 phút |
| Lãnh đạo nhận bản giấy → không biết trạng thái | Dashboard realtime, notification push |
| Không có audit trail khi xảy ra tranh chấp | Mọi bước AI đều được log đầy đủ |
| Mỗi vụ xử lý khác nhau do kinh nghiệm cá nhân | Tiêu chuẩn hóa bằng risk rules từ văn bản pháp quy |

---

## Hệ thống làm gì — 5 bước

```
1. Nộp hồ sơ  →  2. AI phân tích  →  3. Báo cáo  →  4. Lãnh đạo duyệt  →  5. Lưu trữ
     PDF              8 tools              Markdown         HITL panel             Audit log
  + metadata          parallel            confidence        approve/reject          Chroma
```

### Bước 1 — Nộp hồ sơ
Cán bộ tạo dossier, upload PDF tờ trình (MINIO), điền metadata (đơn vị, loại hồ sơ). Hệ thống auto-extract text từ PDF bằng OCR tool.

### Bước 2 — AI phân tích (Level 4 Agentic)
AI Orchestrator chạy Plan → Execute → Reflect → Critic:
- LegalGraphRAG: kiểm tra căn cứ pháp lý
- ErpBudgetCheck: đối chiếu ngân sách
- ErpInventoryCheck: kiểm tra tồn kho
- TechnicalStandardCheck: tiêu chuẩn kỹ thuật
- ProcurementCheck: quy trình đấu thầu
- DOfficeLookup: kiểm tra DOffice
- PmisProjectCheck: tiến độ PMIS
- EcoOcrExtract: trích xuất PDF

### Bước 3 — Báo cáo
AI tổng hợp báo cáo Markdown tiếng Việt, kèm:
- Overall risk level (low/medium/high/critical)
- Mỗi check: pass/fail/warning + confidence score
- Khuyến nghị cụ thể

### Bước 4 — Lãnh đạo duyệt (HITL)
Panel phê duyệt trong webapp:
- Xem báo cáo AI
- Chat với AI để hỏi thêm
- Phê duyệt / từ chối / yêu cầu bổ sung

### Bước 5 — Lưu trữ
- PostgreSQL: toàn bộ quy trình, audit log
- Chroma: AI memories cross-session (học từ lịch sử)
- MinIO: PDF + tài liệu đính kèm

---

## Số liệu demo (EVN Hà Nội)

| Metric | Giá trị |
|--------|---------|
| Hồ sơ mẫu | 16 dossiers (hồ sơ thật: 198/TTr-EVNHANOI — UAV) |
| Người dùng | 8 (admin, hdtv_leader, dept_head×2, specialist×4) |
| DB migrations | 18 |
| AI tools | 8 |
| LLM roles | 9 |
| Risk rules | 6 (từ Nghị định 24/2024) |

---

## Stack tóm tắt

```
Frontend    Vue 3 + Vite + Pinia + TailwindCSS + BPMN.js
Backend     FastAPI (Python 3.12) + SQLAlchemy async + Alembic
AI          llama.cpp server (local) + Gemini API (cloud fallback)
Memory      PostgreSQL (short-term) + ChromaDB (long-term vector)
Queue       Redis + Celery (async tasks)
Storage     MinIO S3-compatible
Monitor     Prometheus + Grafana
Infra       Docker Compose (dev) → Vagrant (prod)
```
