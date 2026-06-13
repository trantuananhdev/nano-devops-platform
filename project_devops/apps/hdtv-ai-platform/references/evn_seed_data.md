# EVN Seed Data — Dữ liệu mẫu thực tế

Dữ liệu dựa trên hồ sơ thật EVNHANOI: **Mua sắm máy bay không người lái (UAV) phục vụ kiểm tra lưới điện** (số hiệu: EVNHANOI-UAV-198-2024, căn cứ QĐ 8594/QĐ-EVNHANOI, Danh mục MSTS X06 đợt 2/2024).

---

## Users (8 người, 4 roles)

| Email | Tên | Role | Đơn vị |
|-------|-----|------|--------|
| admin@evnhanoi.vn | Nguyễn Văn An | admin | Ban CNTT - EVNHANOI |
| tbich@evnhanoi.vn | Trần Thị Bích | hdtv_leader | Ban Hội đồng thẩm định vật tư (HDTV) |
| pvcuong@evnhanoi.vn | Phạm Văn Cường | dept_head | Trưởng Ban Kỹ thuật - Sản xuất |
| lvdung@evnhanoi.vn | Lê Văn Dũng | dept_head | Trưởng Ban Vật tư - Đầu tư |
| htem@evnhanoi.vn | Hoàng Thị Em | specialist | Chuyên viên pháp chế |
| vvphuc@evnhanoi.vn | Vũ Văn Phúc | specialist | Chuyên viên kỹ thuật UAV |
| dtgiang@evnhanoi.vn | Đỗ Thị Giang | specialist | Chuyên viên tài chính - kế hoạch |
| bvhung@evnhanoi.vn | Bùi Văn Hùng | specialist | Chuyên viên đấu thầu |

Password mặc định (bcrypt): `EVN@2024!`

---

## Dossiers (12 hồ sơ — đủ 11 trạng thái)

### Hồ sơ 1 — Hồ sơ chính (dữ liệu thật)
```
doc_no: EVNHANOI-UAV-198-2024
title: Mua sắm máy bay không người lái phục vụ kiểm tra lưới điện EVNHANOI
unit: Ban Kỹ thuật - Sản xuất / EVNHANOI
status: appraising
risk_level: medium
pdf_text: (trích từ Tờ trình HĐTV số 8594/QĐ-EVNHANOI)
  "Căn cứ Quyết định số 8594/QĐ-EVNHANOI ngày ... về việc giao danh mục
   mua sắm thường xuyên X06 đợt 2 năm 2024, Ban Kỹ thuật - Sản xuất đề nghị
   phê duyệt mua sắm 03 máy bay không người lái (UAV) loại đa rotor phục vụ
   kiểm tra, giám sát đường dây và trạm biến áp. Tổng dự toán: 1.855.000.000 VNĐ.
   Nhà cung cấp đề xuất: Công ty CP Công nghệ Thiên Vũ và DJI Enterprise Vietnam."
```

### Hồ sơ 2–12 (cover đủ trạng thái)
```
EVNHANOI-MBA-2024-021 | Mua sắm máy biến áp phân phối 3 pha 22/0.4kV | dept_approved | high
EVNHANOI-CAP-2024-033 | Mua sắm cáp ngầm 22kV XLPE phục vụ ngầm hóa lưới điện Q.Hoàn Kiếm | pending | medium
EVNHANOI-SCADA-2024-007 | Nâng cấp hệ thống SCADA/DMS điều độ lưới điện | approved | low
EVNHANOI-IT-2024-044 | Mua sắm máy tính xách tay phục vụ công tác vận hành | draft | low
EVNHANOI-XL-2024-015 | Thi công lắp đặt trạm biến áp 110kV Tây Hồ | submitted_to_dept | high
EVNHANOI-TU-2024-028 | Tư vấn giám sát xây dựng đường dây 110kV Đông Anh - Sóc Sơn | dept_rejected | medium
EVNHANOI-BT-2024-009 | Bảo trì thiết bị đo đếm điện năng 110kV trạm Thường Tín | submitted_to_board | low
EVNHANOI-VT-2024-052 | Mua sắm vật tư thiết bị điện cho sửa chữa thường xuyên | board_reviewed | medium
EVNHANOI-KT-2024-018 | Kiểm tra thí nghiệm thiết bị điện cao áp định kỳ 2024 | rejected | high
EVNHANOI-NL-2024-061 | Mua sắm phần mềm quản lý vận hành lưới điện thông minh | needs_revision | medium
EVNHANOI-AN-2024-006 | Mua sắm dụng cụ an toàn lao động làm việc điện | pending | low
```

---

## Risk Rules (6 quy tắc — Nghị định 24/2024/NĐ-CP)

| Tên | Điều kiện | Mức |
|-----|-----------|-----|
| Vượt ngưỡng ngân sách | `ErpBudgetCheck` fail | high |
| Thiếu hồ sơ năng lực nhà thầu | `LegalGraphRAG` → missing_docs | high |
| Thiếu chứng nhận tiêu chuẩn kỹ thuật | `technical_cert` trong missing_docs | high |
| Giá đơn vị cao bất thường >130% khung giá EVN | `ErpInventoryCheck` → price_anomaly | medium |
| Tiến độ cung cấp không khả thi | `ScheduleValidator` fail | medium |
| Đủ điều kiện thẩm định bình thường | Tất cả pass | low |

---

## Alerts (8 cảnh báo)

```
1. UAV: "Giá đề xuất DJI Matrice 300 RTK cao hơn 18% so với giá tham chiếu thị trường Q3/2024"
   severity: high | source: ErpInventoryCheck | status: open | dossier: EVNHANOI-UAV-198-2024

2. UAV: "Công ty CP Công nghệ Thiên Vũ chưa cung cấp chứng chỉ ISO 9001:2015 phiên bản mới nhất"
   severity: high | source: LegalGraphRAG | status: open | dossier: EVNHANOI-UAV-198-2024

3. MBA: "Giá máy biến áp ABB 250kVA vượt 23% khung giá EVN — cần đàm phán lại"
   severity: high | source: ErpBudgetCheck | status: open | dossier: EVNHANOI-MBA-2024-021

4. XL: "Tiến độ thi công trạm 110kV Tây Hồ có nguy cơ trễ 45 ngày do phụ thuộc GPMB"
   severity: medium | source: ScheduleValidator | status: open | dossier: EVNHANOI-XL-2024-015

5. CAP: "Hồ sơ thiếu bản vẽ thiết kế kỹ thuật hệ thống cáp ngầm theo TCVN 9208:2012"
   severity: medium | source: LegalGraphRAG | status: open | dossier: EVNHANOI-CAP-2024-033

6. TU: "Chỉ có 1 nhà thầu nộp hồ sơ dự thầu — không đảm bảo tính cạnh tranh theo ND24"
   severity: medium | source: ProcurementAudit | status: resolved | dossier: EVNHANOI-TU-2024-028

7. BT: "Phần mềm kiểm tra DIGSI 5 chưa có hợp đồng bản quyền phù hợp"
   severity: medium | source: LegalGraphRAG | status: open | dossier: EVNHANOI-BT-2024-009

8. SCADA: "Hệ thống SCADA đã hoàn tất thẩm định — không phát hiện rủi ro"
   severity: low | source: system | status: resolved | dossier: EVNHANOI-SCADA-2024-007
```

---

## Appraisal Results (3 kết quả thẩm định)

### Kết quả 1 — SCADA (approved, low risk)
```
overall_risk: low
report_md: |
  ## Kết quả thẩm định AI
  **Hồ sơ:** EVNHANOI-SCADA-2024-007
  **Kết luận:** ✅ Đủ điều kiện phê duyệt

  ### Kiểm tra pháp lý (LegalGraphRAG)
  - Hợp đồng nguyên tắc với Siemens Việt Nam: ĐẠT
  - Giấy phép nhập khẩu thiết bị điện tử: ĐẠT
  - Chứng nhận IEC 61850: ĐẠT

  ### Kiểm tra tài chính (ErpBudgetCheck)
  - Dự toán 4.250.000.000 VND — trong ngưỡng phê duyệt: ĐẠT

  ### Kiểm tra kỹ thuật (ErpInventoryCheck)
  - Giá thiết bị SCADA RTU phù hợp khung giá tham chiếu 2024: ĐẠT

resolution_md: "Đề nghị phê duyệt. Yêu cầu cam kết bảo hành 3 năm từ Siemens Việt Nam."
checks: [{tool: LegalGraphRAG, status: pass, score: 0.94}, {tool: ErpBudgetCheck, status: pass, score: 0.91}]
critic_verdict: {approved: true, confidence: 0.92, comments: "Hồ sơ đầy đủ, không cần làm rõ thêm."}
```

### Kết quả 2 — MBA (dept_approved, high risk — có cảnh báo giá)
```
overall_risk: high
report_md: |
  ## Kết quả thẩm định AI
  **Hồ sơ:** EVNHANOI-MBA-2024-021
  **Kết luận:** ⚠️ Đề nghị xem xét lại đơn giá

  ### Kiểm tra tài chính (ErpBudgetCheck)
  - Giá MBA ABB 250kVA đề xuất: 185.000.000 VND/bộ
  - Khung giá EVN 2024: 150.000.000 VND/bộ
  - Chênh lệch: 23.3% — KHÔNG ĐẠT (ngưỡng 130%)

resolution_md: "Yêu cầu nhà thầu giải trình chênh lệch giá hoặc thay thế nhà cung cấp."
checks: [{tool: LegalGraphRAG, status: pass, score: 0.89}, {tool: ErpBudgetCheck, status: fail, score: 0.23}]
critic_verdict: {approved: false, confidence: 0.88, comments: "Cần đàm phán giá trước khi phê duyệt."}
```

### Kết quả 3 — KT (rejected)
```
overall_risk: high
report_md: "Hồ sơ thiếu biên bản nghiệm thu kỳ trước. Đề nghị bổ sung và nộp lại."
resolution_md: "Trả lại hồ sơ. Yêu cầu bổ sung biên bản nghiệm thu thí nghiệm định kỳ 2023."
checks: [{tool: LegalGraphRAG, status: fail, score: 0.12}]
critic_verdict: {approved: false, confidence: 0.97, comments: "Thiếu tài liệu bắt buộc theo ND24."}
```

---

## Workflow BPMN (3 sơ đồ)

### Workflow 1 — Quy trình thẩm định cơ bản (5 bước)
```
Nhận hồ sơ → Kiểm tra đủ điều kiện → AI Thẩm định → Phê duyệt Trưởng phòng → Phê duyệt HĐTV
```

### Workflow 2 — Quy trình có clarification (7 bước)
```
Nhận hồ sơ → Kiểm tra đủ điều kiện → AI Thẩm định → [AI Yêu cầu làm rõ]
→ Chuyên viên trả lời → AI Hoàn thiện thẩm định → Phê duyệt Trưởng phòng → Phê duyệt HĐTV
```

### Workflow 3 — Quy trình phê duyệt HĐTV đầy đủ (theo Mẫu KT thật — 9 bước)
```
Phiếu trình B4 → PTGĐ xem xét → Ban Kỹ thuật thẩm tra
→ Báo cáo thẩm tra → Lấy ý kiến tư vấn ngoài → AI Tổng hợp ý kiến
→ Trình Tổng Giám đốc → HĐTV phê duyệt → Ban hành Quyết định
```
