# KẾ HOẠCH TRIỂN KHAI DEMO — HDTV AI PLATFORM
### Bộ hồ sơ thật làm Mock Data: Tờ trình 198/TTr-EVNHANOI – "Phê duyệt Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV)"

> Tài liệu này dùng để brief cho Cursor (AI coding agent) tiếp tục hoàn thiện prototype Vue 3 hiện có (`hdtv-ai-prototype`) thành một demo full-stack (FastAPI + Celery + Postgres + Redis + Chroma + MinIO + Meilisearch) **bám đúng System Design đã thiết kế** (xem `system-design-hdtv-ai.md`). Khi gửi cho Cursor, kèm theo:
> 1. File này.
> 2. File system design (mermaid) đã có.
> 3. Folder `Mẫu phê duyệt tờ trình của KT (đơn giản)` (đặt theo cấu trúc ở Mục 8).
> 4. Source code prototype `hdtv-ai-prototype/`.

---

## 1. Mục tiêu của Demo

Biến 1 bộ hồ sơ **thật** (đã có sẵn: Tờ trình, Phiếu trình, Báo cáo thẩm tra, Phụ lục so sánh kỹ thuật, Ý kiến góp ý nhà cung cấp, Quyết định căn cứ pháp lý) thành **Dossier mẫu #198/TTr-EVNHANOI** trong hệ thống, để:

- Chứng minh toàn bộ luồng "AI Agentic Appraisal" (Planner → Executor → Reflector → Critic) chạy được trên dữ liệu thật, không phải dữ liệu bịa.
- Có ít nhất **2 dossier demo** với mức rủi ro khác nhau để Lãnh đạo HĐTV thấy sự đa dạng:
  - Dossier #1 (đã có trong prototype): `124/TTr-B02` – Cáp ngầm Ba Đình – **Rủi ro cao** (vượt TMĐT, do dữ liệu giả định).
  - Dossier mới `198/TTr-EVNHANOI` – Tiêu chuẩn kỹ thuật UAV – **Rủi ro trung bình** (phát hiện đề xuất hạ tiêu chuẩn kỹ thuật từ nhà cung cấp tư vấn).
- Mọi tab, mọi panel trong `SplitViewWorkspace.vue` đều có nội dung thật tương ứng với dossier UAV (không còn placeholder "Lorem").
- Toàn bộ pipeline Agent (Planner/Executor/Reflector/Critic), Audit Log, MCP Audit Log, Knowledge Graph, Alerts, Schedule... đều có ít nhất 1 bản ghi sinh ra từ dossier UAV này.

---

## 2. Phân tích bộ tài liệu gốc & vai trò trong hệ thống

Thư mục `Mẫu phê duyệt tờ trình của KT (đơn giản)` chứa đúng một "luồng hồ sơ thật" của EVNHANOI về việc ban hành **Tiêu chuẩn kỹ thuật UAV** (drone) phục vụ kiểm tra đường dây 220/110kV. Đây là bối cảnh hoàn hảo cho demo vì:

- Có **căn cứ pháp lý rõ ràng** (QĐ 8594, NQ 180, QĐ 153) → phục vụ module Legal RAG / GraphRAG.
- Có **bảng so sánh kỹ thuật định lượng** giữa "Yêu cầu của EVN" và 5 sản phẩm thị trường (CN01/MAJ, M300 RTK/DJI, HERA/RTR, IF1200A/Inspired Flight, ALTA X/Freefly) → phục vụ module Đối chiếu kỹ thuật (giống ERP check trong demo cáp ngầm, nhưng ở đây là đối chiếu **tiêu chuẩn vs catalogue**).
- Có **ý kiến góp ý từ 2 nhà cung cấp tư vấn** (Apex Tech, MAJ) đề xuất **hạ một số chỉ tiêu kỹ thuật** so với yêu cầu gốc của EVN → đây chính là "rủi ro" mà AI cần phát hiện và cảnh báo.
- Có **Phiếu trình với ý kiến 5 thành viên HĐTV** (đều "Tôi đồng ý") → dữ liệu thật cho tab "Ý kiến Thành viên".

### Bảng mapping file gốc → vai trò trong hệ thống

| # | Tên file gốc | Vai trò trong Dossier #198 | Hiển thị tại |
|---|---|---|---|
| 1 | `02. Tờ trình xin duyệt HĐTV (B4 ký TGĐ trình HĐTV).pdf` (= Tờ trình 198/TTr-EVNHANOI, 08/01/2025) | **Văn bản chính** — TGĐ trình HĐTV phê duyệt tiêu chuẩn kỹ thuật UAV | Tab trái "Tờ trình" |
| 2 | `01. tài liệu kèm tờ trình/Tờ trình B4 trình PTGĐ.pdf` (= Tờ trình 07/KT, 07/01/2025) | Văn bản căn cứ — Ban Kỹ thuật trình PTGĐ trước đó (đã được PTGĐ duyệt) | Tab trái "Tài liệu Khác" + nguồn cho Legal RAG |
| 3 | `03. Báo cáo thẩm tra.pdf` (Ban Tổng hợp, 24/01/2025) | Báo cáo thẩm tra **mẫu tham khảo** — dùng làm "ground truth" để AI học cấu trúc báo cáo thẩm định, đồng thời là output mẫu cho Phiên bản 1.0 của "Báo cáo Thẩm định" | Seed cho `Skill Builder` (mẫu output) + Tab "Báo cáo Thẩm định" v1.0 |
| 4 | `03. 1phiếu trình.pdf` / `phiếu trình.pdf` (Phiếu trình 10/02/2025, 5 ý kiến HĐTV "Tôi đồng ý") | Phiếu trình + ý kiến 5 thành viên HĐTV | Tab phải "Ý kiến Thành viên" |
| 5 | `01. tài liệu kèm tờ trình/Tiêu_chí_kỹ_thuật_so_sánh_3_sản_phẩm_final_chot 240914.xlsx` | **Phụ lục kỹ thuật** — Bảng "Yêu cầu của EVN" vs 5 sản phẩm (CN01, M300 RTK, HERA, IF1200A, ALTA X) trên 4 nhóm: (4.1) Yêu cầu chung, (4.2.1) UAV cơ bản, (4.2.2) Lidar, (4.2.3) Pin, (4.2.4) Sạc pin | Tab trái "Phụ lục" (PL01–PL04) |
| 6 | `01. tài liệu kèm tờ trình/Ý kiến góp ý của máy bay không người lái của tư vấn ngoài.pdf` (Apex Tech, CV 8472/EVNHANOI-KT, 15/10/2024) | Ý kiến nhà cung cấp Apex đề xuất **giảm 3 chỉ tiêu**: Tốc độ bay tối đa 220→215 m/s; Quãng đường bay tối đa 40→35 km; Bộ nhớ trong 64→16GB | Nguồn cho AI check "Đối chiếu đề xuất NCC" — Reference Docs |
| 7 | `01. tài liệu kèm tờ trình/pdf2lop Ý kiến góp ý ... 2.pdf` (MAJ, CV 1010/CVAM41/2024, 10/10/2024) | Ý kiến nhà cung cấp MAJ — đề xuất bổ sung yêu cầu hồ sơ năng lực + hỗ trợ pháp lý cấp phép bay | Reference Docs |
| 8 | `01. tài liệu kèm tờ trình/BC góp ý các nhà cung cấp 3.xlsx` | Bảng tổng hợp ý kiến 2/4 nhà cung cấp được hỏi (Apex, MAJ) — 2 đơn vị không phản hồi (VJO, Thắng Lợi) | Nguồn cho AI check "Khảo sát thị trường" |
| 9 | `Tài liệu căn cứ tham khảo/8594_QĐ-EVNHANOI/QĐ giao danh mục MSTS X06 2024.pdf` (+.doc, +PL X06 đợt 2.xlsx) | **Căn cứ pháp lý gốc** — QĐ 8594/QĐ-EVNHANOI ngày 06/12/2023: giao danh mục mua sắm tài sản 2024 đợt 2 cho Công ty Lưới điện Cao thế TP Hà Nội (trong đó có "Mua sắm và vận hành thí điểm 04 bộ UAV") | Legal RAG / Knowledge Graph — node căn cứ pháp lý |

> **Ghi chú đặt tên file:** tên file gốc có dấu tiếng Việt + khoảng trắng gây lỗi encoding khi unzip trên Linux (`#U1ec7t...`). Khi copy vào repo, **đổi tên không dấu, không khoảng trắng** theo Mục 8.

---

## 3. Dossier mới trong hệ thống

### 3.1 Bản ghi Dossier (bảng `dossiers`)

```json
{
  "id": "5",
  "doc_no": "198/TTr-EVNHANOI",
  "title": "Phê duyệt Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV) phục vụ kiểm tra đường dây 220/110kV",
  "unit": "Ban Kỹ thuật (KT)",
  "submitted_by": "Tổng Giám đốc",
  "date": "08/01/2025",
  "risk": "medium",
  "status": "Chờ duyệt",
  "dossier_type": "Tờ trình Phê duyệt Tiêu chuẩn kỹ thuật"
}
```

Thêm vào `DossierListView.vue` (mảng `dossiers`) và vào danh sách `notableDossiers` của `DashboardView.vue` (để xuất hiện trên Dashboard tổng quan).

### 3.2 Loại Tờ trình mới trong `DossierSettingsView.vue`

Thêm `dossierTypes`:
```js
{ id: 6, name: 'Tờ trình Phê duyệt Tiêu chuẩn kỹ thuật Vật tư/Thiết bị', active: false }
```

Checklist riêng cho loại này (bảng `checklists`, gắn `dossier_type_id = 6`):
1. Đối chiếu căn cứ pháp lý (QĐ giao danh mục mua sắm còn hiệu lực) — `auto`, required
2. Kiểm tra thẩm quyền phê duyệt theo phân cấp HĐTV/TGĐ — `auto`, required
3. Đối chiếu Tiêu chuẩn kỹ thuật dự thảo với ý kiến góp ý của nhà cung cấp/tư vấn (phát hiện đề xuất hạ tiêu chuẩn) — `auto`, required
4. Kiểm tra số lượng nhà cung cấp đã phản hồi khảo sát thị trường (tối thiểu 2/4) — `auto`, optional
5. Kiểm tra cấu trúc hồ sơ: Tờ trình + Phiếu trình + Báo cáo thẩm tra + Phụ lục kỹ thuật — `auto`, required

---

## 4. Kịch bản AI Appraisal cho Dossier #198 (5 bước Planner → Critic)

Đây là nội dung sẽ điền vào `aiChecks` trong `SplitViewWorkspace.vue` khi `dossierId === '5'`, và đồng thời là **kế hoạch (Agent Plan)** mà Celery worker thực thi thật ở backend.

### Check 1 — Kiểm tra căn cứ pháp lý (`legal_basis_check`)
- **status:** `pass`
- **desc:** "Căn cứ pháp lý đầy đủ, còn hiệu lực: QĐ 8594/QĐ-EVNHANOI (06/12/2023) và NQ 180/NQ-HĐTV (22/11/2023)."
- **details:**
  ```
  Hệ thống GraphRAG truy xuất và xác minh các căn cứ pháp lý được trích trong
  Tờ trình 198/TTr-EVNHANOI và Báo cáo thẩm tra:
  1. QĐ 8594/QĐ-EVNHANOI (06/12/2023) — Giao danh mục mua sắm tài sản 2024 đợt 2
     cho Công ty Lưới điện Cao thế TP Hà Nội, trong đó có hạng mục "Mua sắm và
     vận hành thí điểm 04 bộ UAV phục vụ kiểm tra đường dây 220/110kV".
     => Còn hiệu lực, đúng đối tượng.
  2. NQ 180/NQ-HĐTV (22/11/2023) — Thông qua chủ trương giao danh mục chuẩn bị
     đầu tư đợt 2 năm 2024. => Còn hiệu lực.
  3. Tờ trình 07/KT (07/01/2025) — đã được Phó Tổng Giám đốc Kỹ thuật phê duyệt
     trước khi trình HĐTV. => Đúng trình tự nội bộ.

  Kết luận: Cơ sở pháp lý hợp lệ, đầy đủ.
  ```

### Check 2 — Đối chiếu thẩm quyền phê duyệt (`authority_check`)
- **status:** `pass`
- **desc:** "Thuộc thẩm quyền HĐTV theo Khoản 1, Điều 33, Chương VI – QĐ 153/QĐ-HĐTV."
- **details:**
  ```
  Đối chiếu nội dung Tờ trình (ban hành Tiêu chuẩn kỹ thuật vật tư/thiết bị) với
  QĐ 153/QĐ-HĐTV (16/5/2023) — Quy định làm việc, phân cấp giữa HĐTV và TGĐ:
  - Khoản 1, Điều 33, Chương VI "Phân cấp trong công tác quản lý kỹ thuật, an
    toàn": việc ban hành/ thông qua tiêu chuẩn kỹ thuật thiết bị thuộc thẩm
    quyền HĐTV.
  Kết luận: Tờ trình trình đúng cấp thẩm quyền.
  ```

### Check 3 — Đối chiếu Tiêu chuẩn kỹ thuật với ý kiến Nhà cung cấp/Tư vấn (`spec_vs_supplier_feedback_check`) ⚠️ **TRỌNG TÂM DEMO**
- **status:** `fail` (cảnh báo, không phải lỗi nghiêm trọng — mức "cần giải trình")
- **desc:** "Phát hiện 3 chỉ tiêu kỹ thuật trong góp ý của NCC Apex Tech thấp hơn yêu cầu gốc do Ban Kỹ thuật đề xuất."
- **details:**
  ```
  AI đối chiếu "Phụ lục I – Yêu cầu đặc tính kỹ thuật UAV" (do Ban Kỹ thuật dự
  thảo) với Công văn phúc đáp số 8472/EVNHANOI-KT (15/10/2024) của Công ty
  TNHH Apex Tech Việt Nam. Phát hiện 3 đề xuất sửa đổi theo chiều HẠ THẤP tiêu
  chuẩn:

  | Chỉ tiêu                  | Yêu cầu gốc (EVN) | Đề xuất Apex Tech | Đánh giá        |
  |---------------------------|-------------------|-------------------|-----------------|
  | Quãng đường bay tối đa    | 40 km             | 35 km             | Giảm 12.5%      |
  | Tốc độ bay tối đa         | 220 m/s           | 215 m/s           | Giảm nhẹ        |
  | Bộ nhớ trong bộ điều khiển| 64 GB             | 16 GB             | Giảm 75%        |

  Đối chiếu với Phụ lục so sánh 5 sản phẩm thị trường (CN01/MAJ, M300 RTK/DJI,
  HERA/RTR, IF1200A/Inspired Flight, ALTA X/Freefly): các sản phẩm IF1200A và
  ALTA X (Mỹ) đáp ứng tốt tiêu chí trọng lượng/tải, nhưng cần kiểm tra lại
  tiêu chí bộ nhớ trong & quãng đường bay theo đúng yêu cầu gốc, tránh việc hạ
  chuẩn theo đề xuất của 1 nhà cung cấp làm thu hẹp khả năng lựa chọn sản phẩm
  đạt chuẩn cao hơn.

  Khuyến nghị: Ban Kỹ thuật giải trình rõ lý do nếu chấp thuận đề xuất hạ chỉ
  tiêu "Bộ nhớ trong" từ 64GB xuống 16GB trước khi HĐTV thông qua tiêu chuẩn
  chính thức.
  ```

### Check 4 — Kiểm tra khảo sát thị trường / tính cạnh tranh (`market_survey_check`)
- **status:** `pass` (nhưng có lưu ý — hiển thị icon "info" nếu UI hỗ trợ, hoặc giữ `pass` kèm desc cảnh báo nhẹ)
- **desc:** "Đã gửi công văn lấy ý kiến 4 nhà cung cấp, có 2/4 đơn vị phản hồi (Apex Tech, MAJ)."
- **details:**
  ```
  Ban Kỹ thuật đã gửi công văn lấy ý kiến tiêu chuẩn kỹ thuật UAV tới 4 đơn vị:
  - Công ty CP Thương mại VJO Việt Nam — không phản hồi
  - Công ty TNHH Apex Tech Việt Nam — đã phản hồi (CV 8472/EVNHANOI-KT)
  - Công ty CP Dịch vụ Nông nghiệp MAJ — đã phản hồi (CV 1010/CVAM41/2024)
  - Công ty CP Thiết bị Thắng Lợi — không phản hồi

  Tỷ lệ phản hồi: 2/4 (50%). Mức tối thiểu theo Checklist nội bộ: 2/4 → ĐẠT.
  Khuyến nghị: nên đôn đốc 2 đơn vị còn lại để tăng tính cạnh tranh khi tổ chức
  đấu thầu mua sắm thực tế.
  ```

### Check 5 — Kiểm tra cấu trúc hồ sơ (`document_structure_check`)
- **status:** `pass`
- **desc:** "Hồ sơ đầy đủ: Tờ trình, Phiếu trình, Báo cáo thẩm tra, Phụ lục so sánh kỹ thuật."
- **details:**
  ```
  Kiểm tra cấu trúc hồ sơ (Document Structure Check):
  - Tờ trình 198/TTr-EVNHANOI (08/01/2025): Có
  - Tờ trình 07/KT đã được PTGĐ duyệt (07/01/2025): Có
  - Báo cáo thẩm tra của Ban Tổng hợp (24/01/2025): Có
  - Phiếu trình kèm ý kiến HĐTV (10/02/2025): Có
  - Phụ lục so sánh kỹ thuật 5 sản phẩm (Excel): Có
  - Ý kiến góp ý nhà cung cấp (Apex, MAJ): Có

  Kết luận: Hồ sơ đầy đủ thành phần theo quy định nội bộ.
  ```

### Verdict của Critic Agent
- **Verdict:** `Needs Revision` (Cần giải trình bổ sung)
- **Lý do:** Check 3 phát hiện đề xuất hạ tiêu chuẩn kỹ thuật cần Ban Kỹ thuật giải trình trước khi HĐTV ban hành Nghị quyết chính thức.
- Đây là khác biệt có chủ đích với Dossier #1 (verdict `Escalate` do vượt vốn) — giúp demo thể hiện đủ 3 nhánh rẽ trong sequence diagram: Approved / Needs Revision / Escalate.

---

## 5. Nội dung các Tab trong `SplitViewWorkspace.vue` cho `dossierId === '5'`

### 5.1 Tab trái "Tờ trình" (`leftTab = 'main'`)
Trích đoạn từ Tờ trình 198/TTr-EVNHANOI (giữ đúng văn phong gốc, rút gọn):
```
TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI
TỜ TRÌNH
Số: 198/TTr-EVNHANOI — Hà Nội, ngày 08 tháng 01 năm 2025
V/v: Phê duyệt tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV)
Kính gửi: Hội đồng Thành viên - EVNHANOI

Căn cứ Quyết định số 8594/QĐ-EVNHANOI ngày 06/12/2023 về việc giao danh mục
mua sắm tài sản năm 2024 đợt 2 cho Công ty Lưới điện Cao thế TP Hà Nội;
Xét Tờ trình số 07/KT ngày 07/01/2025 của Ban Kỹ thuật đã được Phó Tổng Giám
đốc Kỹ thuật phê duyệt;

Tổng Giám đốc kính trình Hội đồng Thành viên phê duyệt Tiêu chuẩn kỹ thuật
thiết bị bay không người lái (UAV) với các nội dung: (1) Yêu cầu chung về
nhà sản xuất, (2) Yêu cầu kỹ thuật chung — UAV cơ bản kèm Camera ảnh màu &
Camera ảnh nhiệt, Bộ điều khiển UAV, Hệ thống chống rung, Bộ nhớ lưu trữ...
(Chi tiết tại Phụ lục kèm theo).
```

### 5.2 Tab trái "Phụ lục" (`leftTab = 'appendix'`)
Dropdown chọn phụ lục — map sang các sheet trong file Excel `Tiêu_chí_kỹ_thuật_so_sánh_3_sản_phẩm`:
- `PL01: Yêu cầu kỹ thuật chung (Mục 4.1)`
- `PL02: Bảng so sánh UAV cơ bản — EVN vs 5 sản phẩm (Mục 4.2.1)`
- `PL03: Bảng so sánh Camera Lidar (Mục 4.2.2)`
- `PL04: Bảng so sánh Pin & Sạc pin (Mục 4.2.3 – 4.2.4)`

Bảng mẫu cho PL02 (rút gọn, đủ để demo highlight):

| Hạng mục | Đơn vị | Yêu cầu EVN | CN01 (MAJ) | M300 RTK (DJI) | HERA (RTR) | IF1200A (Inspired Flight) | ALTA X (Freefly) |
|---|---|---|---|---|---|---|---|
| Trọng lượng cất cánh (không camera) | kg | ≤ 9 | 3.45 | 3.6–6.3 | 8.5–15.5 | 7.9–16.3 | 10.86–19 |
| Trọng lượng cất cánh tối đa | kg | ≤ 16 | 6 | 9 | 30.5 | 25 | 34.86 |
| Hãng sản xuất / Xuất xứ | — | Nhà thầu nêu rõ | MAJ / Việt Nam | DJI / Trung Quốc | RTR / Việt Nam | Inspired Flight / USA | Freefly Systems / USA |

> Highlight (giống style `<mark class="highlight-warn">` trong prototype) ô **"Bộ nhớ trong: 64GB"** ở PL01 và liên kết sang Check 3.

### 5.3 Tab trái "Tài liệu Khác" (`leftTab = 'reference'`)
`referenceDocs` ban đầu (đã upload sẵn, AI dùng làm nguồn đối chiếu):
```js
[
  { id: 1, name: 'QĐ 8594_QĐ-EVNHANOI - Giao danh mục mua sắm 2024 đợt 2.pdf', size: '1.8 MB' },
  { id: 2, name: 'To trinh 07-KT (PTGD da duyet).pdf', size: '0.6 MB' },
  { id: 3, name: 'Y kien gop y NCC Apex Tech (CV 8472).pdf', size: '1.1 MB' },
  { id: 4, name: 'Y kien gop y NCC MAJ (CV 1010).pdf', size: '0.9 MB' },
  { id: 5, name: 'BC gop y cac nha cung cap.xlsx', size: '45 KB' }
]
```

### 5.4 Tab trái "Báo cáo Thẩm định" (`leftTab = 'report'`)
Nội dung Phiên bản 1.1 (sau khi áp dụng kết quả thẩm định AI), dựa theo cấu trúc thật của `Báo cáo thẩm tra.pdf` (Ban Tổng hợp, 24/01/2025) nhưng bổ sung mục risk do AI phát hiện:
```
TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI
BÁO CÁO THẨM ĐỊNH
V/v: Thẩm định Tờ trình 198/TTr-EVNHANOI — Phê duyệt Tiêu chuẩn kỹ thuật UAV

1. Đánh giá chung: Hồ sơ trình duyệt đầy đủ căn cứ pháp lý và đúng thẩm
   quyền HĐTV theo Khoản 1 Điều 33 QĐ 153/QĐ-HĐTV.

2. Rủi ro phát hiện (AI Report):
   - Đề xuất của NCC Apex Tech (CV 8472/EVNHANOI-KT) hạ 3 chỉ tiêu kỹ thuật
     so với yêu cầu gốc của Ban Kỹ thuật, trong đó đáng chú ý là "Bộ nhớ
     trong" giảm từ 64GB xuống 16GB (-75%).
   - Tỷ lệ phản hồi khảo sát thị trường đạt 2/4 nhà cung cấp.

3. Đề xuất: Yêu cầu Ban Kỹ thuật giải trình và khẳng định lại 3 chỉ tiêu kỹ
   thuật (Quãng đường bay tối đa, Tốc độ bay tối đa, Bộ nhớ trong) trước khi
   HĐTV ban hành Nghị quyết phê duyệt tiêu chuẩn chính thức.
```

### 5.5 Tab trái "Nghị quyết" (`leftTab = 'resolution'`)
```
NGHỊ QUYẾT
HỘI ĐỒNG THÀNH VIÊN TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI
V/v: Thông qua Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV)

ĐIỀU 1: Về cơ bản thông qua Tiêu chuẩn kỹ thuật thiết bị bay không người lái
(UAV) theo Tờ trình số 198/TTr-EVNHANOI ngày 08/01/2025.

ĐIỀU 2: Giao Ban Kỹ thuật rà soát, giải trình 03 chỉ tiêu kỹ thuật (Quãng
đường bay tối đa, Tốc độ bay tối đa, Bộ nhớ trong bộ điều khiển) trên cơ sở
ý kiến góp ý của Công ty TNHH Apex Tech Việt Nam, hoàn thiện Phụ lục Tiêu
chuẩn kỹ thuật trước khi ban hành chính thức.

ĐIỀU 3: Giao Công ty Lưới điện Cao thế TP Hà Nội căn cứ Tiêu chuẩn kỹ thuật
sau khi hoàn thiện để tổ chức mua sắm 04 bộ UAV theo danh mục tại QĐ
8594/QĐ-EVNHANOI.

TM. HỘI ĐỒNG THÀNH VIÊN
CHỦ TỊCH
```

### 5.6 Tab phải "Ý kiến Thành viên" (`activeTab = 'chat'`)
Lấy thật từ Phiếu trình (10/02/2025) — 5 thành viên đều "Tôi đồng ý":
```js
[
  { id: 1, sender: 'Đ/c Đỗ Tuấn Anh (Thành viên HĐTV)', time: '10/02', content: 'Tôi đồng ý.', isMe: false },
  { id: 2, sender: 'Đ/c Nguyễn Xuân Thắng (Thành viên HĐTV)', time: '10/02', content: 'Tôi đồng ý.', isMe: false },
  { id: 3, sender: 'Đ/c Trần Văn Thương (Thành viên HĐTV)', time: '10/02', content: 'Tôi đồng ý.', isMe: false },
  { id: 4, sender: 'Đ/c Phạm Đại Nghĩa (Thành viên HĐTV)', time: '10/02', content: 'Tôi đồng ý.', isMe: false },
  { id: 5, sender: 'Đ/c Mã Hoài Nam (Thành viên HĐTV)', time: '10/02', content: 'Tôi đồng ý. Tuy nhiên đề nghị làm rõ thêm ý kiến của AI về đề xuất hạ chỉ tiêu bộ nhớ trong trước khi ký Nghị quyết.', isMe: false }
]
```
Ý kiến của thành viên #5 chính là "ngòi nổ" để Lãnh đạo HĐTV bấm vào tab "Kết quả Thẩm định" và mở chi tiết Check 3 — tạo mạch demo liên kết giữa các tab.

### 5.7 Tab phải "Hỏi đáp làm rõ Kết quả" (clarify chat trong tab `ai`)
```js
[
  { id: 1, sender: 'Lãnh đạo HĐTV', time: '10:30', content: 'Vì sao AI đánh giá đề xuất "Bộ nhớ trong 16GB" là rủi ro?', isMe: true },
  { id: 2, sender: 'Trợ lý AI', time: '10:30', content: 'Thưa sếp, yêu cầu gốc của Ban Kỹ thuật tại Phụ lục I là Bộ nhớ trong tối thiểu 64GB. Công văn 8472/EVNHANOI-KT của Apex Tech đề xuất giảm xuống 16GB (-75%), có thể ảnh hưởng đến khả năng lưu trữ dữ liệu kiểm tra đường dây trong các chuyến bay dài. Tôi đề xuất giữ nguyên 64GB hoặc yêu cầu Apex Tech giải trình khả năng đáp ứng.', isAI: true }
]
```

---

## 6. Danh sách Module hệ thống — Mô tả & Công việc cần làm

Bám theo 2 sơ đồ kiến trúc & sequence diagram đã có. Với mỗi module: **Mục đích**, **Trạng thái FE hiện tại**, **Việc BE cần làm**, **Liên kết dữ liệu Dossier #198**.

### 6.1 Dossier Management (FastAPI Business API + Postgres)
- **Mục đích:** CRUD hồ sơ, lưu metadata, version báo cáo/nghị quyết, trạng thái pipeline.
- **FE hiện tại:** `DossierListView.vue`, `SplitViewWorkspace.vue` — dữ liệu hardcode trong `<script setup>`.
- **BE cần làm:**
  - Bảng: `dossiers`, `dossier_documents`, `dossier_versions` (loại `report`/`resolution`), `dossier_checklist_items`.
  - Endpoints: `GET /api/v1/dossiers`, `GET /api/v1/dossiers/{id}`, `POST /api/v1/dossiers/{id}/appraise`, `POST /api/v1/dossiers/{id}/feedback`, `GET /api/v1/dossiers/{id}/versions`.
  - Seed dossier #198 + 6 file đính kèm (Mục 8) vào MinIO bucket `hdtv-dossiers/198-ttr-evnhanoi/`.
- **FE cần sửa:** thay mảng hardcode bằng `fetch`/`axios` tới các endpoint trên; giữ nguyên cấu trúc field (để không phải sửa lại template).

### 6.2 Document Storage (MinIO)
- **Mục đích:** lưu file gốc (PDF/XLSX), serve cho PDF viewer & Excel preview ở tab trái.
- **Việc cần làm:** tạo bucket `hdtv-dossiers`; script upload toàn bộ file ở Mục 8 theo path `198-ttr-evnhanoi/{original|appendix|reference|outputs}/...`; cấp presigned URL cho FE.

### 6.3 LLM Router
- **Mục đích:** điều phối agent role → backend phù hợp (Gemma local cho planner/executor/reflector/summary; Gemini Flash mock cho legal/financial/ocr/critic/tool_mock).
- **Việc cần làm cho demo (offline-friendly):**
  - Tạo interface `LLMRouter.call(role, prompt, context) -> response` với 2 backend: `llama_local` (gọi llama-server thật nếu có) và `mock_provider` (trả JSON xác định trước cho role `critic`, `legal`, theo template Mục 4).
  - Cấu hình `.env`: `LLM_MODE=mock|live`. Mặc định `mock` để demo chạy ổn định không phụ thuộc mạng/API key.
  - Với dossier #198, các response mock của từng role chính là nội dung 5 Check ở Mục 4 + Verdict.

### 6.4 Execution Harness / Tool Registry
- **Mục đích:** validate input, timeout 30s, retry transient errors, error taxonomy.
- **FE hiện tại:** `ToolRegistryView.vue` đã có danh sách tool (OCR, DOffice, ERP, Bidding...).
- **Việc cần làm:**
  - Thêm 2 tool mới phục vụ dossier #198:
    - `legal_doc_lookup(doc_no)` → trả nội dung QĐ 8594/QĐ-EVNHANOI (từ MinIO/Chroma).
    - `supplier_feedback_lookup(spec_item)` → trả đề xuất sửa đổi từ Apex/MAJ cho 1 chỉ tiêu kỹ thuật (đọc từ `BC góp ý các nhà cung cấp 3.xlsx` đã ingest).
  - Mỗi tool implement theo Error Taxonomy (TRANSIENT/BAD_INPUT/UNAVAILABLE/UNKNOWN) + ghi `ai_audit_logs`.

### 6.5 Agentic Pipeline (Planner / Executor / Reflector / Critic) — Celery
- **Mục đích:** thực thi sequence diagram Mục 3 của system design.
- **Việc cần làm:**
  - Celery task `appraise_dossier(dossier_id)`:
    1. Lấy Agent Memory (Chroma) + Feedback Lessons (Chroma) — với #198 thì memory rỗng (lần đầu), feedback lessons có thể seed sẵn 1 bài học từ dossier #1 ("luôn đối chiếu số liệu với ERP/Catalogue trước khi trình HĐTV").
    2. Query Legal RAG → trả về QĐ 8594, NQ 180, QĐ 153 (đã ingest ở 6.8).
    3. Gọi **Planner** (JSON mode) → sinh ra 5 plan step tương ứng Check 1–5 (Mục 4).
    4. Lưu `agent_plans`, `plan_steps`; bắn WS event `plan_created`.
    5. **Executor** chạy parallel batch các tool tương ứng từng step → ghi `ai_audit_logs` (kèm `plan_step_id`, `error_type`), bắn `tool_executing`/`tool_result`.
    6. **Reflector** tổng hợp → cập nhật Agent Memory (Chroma).
    7. **Critic** → verdict `Needs Revision` (Mục 4) → lưu `critic_verdicts`, bắn `critic_review`.
    8. Nếu `Needs Revision` → Planner re-run với "Revision Instructions" = nội dung Check 3 (yêu cầu Ban Kỹ thuật giải trình) — demo có thể dừng ở đây (hiển thị trạng thái "Chờ giải trình từ Ban Kỹ thuật").
- **FE cần làm:** nút "Chạy lại" (`rerunAppraisal`) gọi `POST /api/v1/dossiers/{id}/appraise`, lắng nghe WS để update từng `aiChecks[i].status` theo `tool_result`.

### 6.6 Agent Memory & Feedback Lessons (Chroma)
- **Mục đích:** lưu "bài học" từ các lần thẩm định trước, dùng lại cho lần sau.
- **Việc cần làm:**
  - Collection `agent_memory`: chunk nội dung 5 Check của dossier #198 (sau khi appraise) → embed → lưu kèm metadata `dossier_id=198`.
  - Collection `feedback_lessons`: seed 1 record mẫu: *"Khi tiêu chuẩn kỹ thuật có ý kiến góp ý từ nhà cung cấp, luôn đối chiếu chiều tăng/giảm so với yêu cầu gốc trước khi trình HĐTV."* — để Reflector ở dossier sau có thể truy xuất.

### 6.7 Legal RAG (Chroma) + Knowledge Graph
- **Mục đích:** truy vấn văn bản pháp lý liên quan, hiển thị đồ thị suy luận.
- **Việc cần làm:**
  - Ingest (chunk + embed) 3 file: QĐ 8594/QĐ-EVNHANOI (+ Phụ lục X06 đợt 2), NQ 180/NQ-HĐTV (trích trong Báo cáo thẩm tra), QĐ 153/QĐ-HĐTV (trích dẫn điều khoản).
  - `KnowledgeGraphView.vue`: thêm category mới `'Đồ thị Tiêu chuẩn kỹ thuật UAV (198/TTr-EVNHANOI)'` với node/edge:
    ```js
    nodes: [
      { id: 'tt198', label: 'Tờ trình 198', desc: 'Tiêu chuẩn KT UAV', type: 'dossier' },
      { id: 'qd8594', label: 'QĐ 8594/QĐ-EVNHANOI', desc: 'Giao danh mục mua sắm 2024 đợt 2', type: 'legal' },
      { id: 'nq180', label: 'NQ 180/NQ-HĐTV', desc: 'Chủ trương giao danh mục đầu tư', type: 'law' },
      { id: 'qd153', label: 'QĐ 153/QĐ-HĐTV Đ.33', desc: 'Phân cấp thẩm quyền KT-AT', type: 'law' },
      { id: 'pl_so_sanh', label: 'Phụ lục so sánh KT', desc: '5 sản phẩm UAV', type: 'data' },
      { id: 'apex_feedback', label: 'Góp ý Apex Tech', desc: 'Hạ 3 chỉ tiêu', type: 'data' },
      { id: 'risk_spec', label: 'Rủi ro hạ chuẩn KT', desc: 'Bộ nhớ trong 64→16GB', type: 'risk' }
    ],
    edges: [
      { source: 'tt198', target: 'qd8594', label: 'Căn cứ theo' },
      { source: 'tt198', target: 'nq180', label: 'Căn cứ theo' },
      { source: 'tt198', target: 'qd153', label: 'Đúng thẩm quyền theo' },
      { source: 'tt198', target: 'pl_so_sanh', label: 'Chứa Phụ lục' },
      { source: 'pl_so_sanh', target: 'apex_feedback', label: 'Đối chiếu' },
      { source: 'apex_feedback', target: 'risk_spec', label: 'Gây ra' }
    ]
    ```

### 6.8 MCP Server
- **Mục đích:** expose tool cho agent ngoài (`/mcp/manifest`, `/mcp/tools/list`, `/mcp/tools/call`, `/mcp/tools/call/stream`, `/mcp/audit-logs`).
- **Việc cần làm:**
  - Đăng ký 2 tool mới (6.4) vào `/mcp/tools/list`.
  - Seed `mcp_call_logs` với 1–2 record mẫu: gọi `legal_doc_lookup("8594/QĐ-EVNHANOI")` từ "AI Agent (Tờ trình 198)".
  - `SystemAdminView.vue` tab "Tool Audits" / Admin → MCP Audit Logs: thêm record tương ứng để demo có dữ liệu thật khi click vào.

### 6.9 Report & Resolution Generator
- **Mục đích:** sinh "Báo cáo Thẩm định" và "Nghị quyết" có version history.
- **Việc cần làm:**
  - `dossier_versions` cho #198:
    - Report v1.0: "Dự thảo ban đầu" (dựa cấu trúc `Báo cáo thẩm tra.pdf` gốc, chưa có phần Rủi ro AI).
    - Report v1.1: bản đã chèn phần "2. Rủi ro phát hiện (AI Report)" (Mục 5.4).
    - Resolution v1.0: nội dung Mục 5.5 (đã có Điều 2 yêu cầu giải trình).
  - FE: `reportVersions`/`resolutionVersions` trong `SplitViewWorkspace.vue` set theo dossier id (tách thành computed dựa trên `dossierId`).

### 6.10 Audit Logs (`ai_audit_logs`, `mcp_call_logs`)
- Mỗi Check 1–5 ở Mục 4 → 1 record `ai_audit_logs` với `plan_step_id` tương ứng (`step_1`..`step_5`), `tool_name`, `error_type` (NULL nếu thành công), `duration_ms`.
- `SystemAdminView.vue` → `toolAudits`: thêm các record `legal_doc_lookup`, `supplier_feedback_lookup` gắn `caller: 'AI Agent (Tờ trình 198)'`.

### 6.11 Alerts
- `AlertsView.vue` → thêm 1 alert mới:
  ```js
  {
    id: 'AL-1043',
    title: 'Đề xuất hạ tiêu chuẩn kỹ thuật từ nhà cung cấp tư vấn',
    severity: 'medium',
    source: 'AI Spec Cross-Check',
    dossier: 'Tờ trình 198/TTr-EVNHANOI — Tiêu chuẩn kỹ thuật UAV',
    dossierId: 'TT-198',
    date: 'Vài phút trước',
    status: 'open',
    description: 'AI phát hiện Công ty TNHH Apex Tech Việt Nam đề xuất giảm 3 chỉ tiêu kỹ thuật UAV (Quãng đường bay tối đa, Tốc độ bay tối đa, Bộ nhớ trong) so với yêu cầu gốc của Ban Kỹ thuật, trong đó Bộ nhớ trong giảm 75%.'
  }
  ```

### 6.12 Schedule Manager
- Có thể thêm 1 schedule minh họa: *"Quét định kỳ ý kiến góp ý nhà cung cấp cho các Tiêu chuẩn kỹ thuật đang dự thảo"* — không bắt buộc, optional nếu còn thời gian.

### 6.13 Advanced Chat / Skill Builder
- `SkillBuilderView.vue`: thêm 1 Skill mới *"Thẩm định Tiêu chuẩn kỹ thuật Vật tư/Thiết bị (đối chiếu góp ý NCC)"* với `markdownContent` mô tả System Prompt cho role `critic`/`legal`, risk rule: *"Nếu giá trị đề xuất của NCC < giá trị yêu cầu gốc đối với chỉ tiêu hiệu năng (capacity/range/speed) → Cờ Vàng (Medium Risk)."*
- `AdvancedChatView.vue`: thêm 1 thread mới *"Thẩm định Tờ trình 198 - UAV"* với 1 ví dụ gọi tool `legal_doc_lookup` (giống mẫu ERP Fetcher đã có).

---

## 7. WebSocket Events cho Dossier #198

Theo đúng sequence diagram, đảm bảo các event sau bắn đúng thứ tự khi gọi `POST /dossiers/198/appraise`:

1. `task_started`
2. `plan_created` (5 step, Mục 4)
3. Lặp 5 lần (có thể song song theo batch 2-2-1): `tool_executing` → `tool_result` cho từng step
4. `critic_review` (verdict = `Needs Revision`, kèm nội dung Check 3)
5. `escalation_required` — **KHÔNG** bắn cho #198 (chỉ #1 dùng nhánh Escalate); thay vào đó bắn 1 event tùy biến `revision_requested` (nếu muốn mở rộng sequence diagram thêm 1 nhánh) hoặc tái dùng `clarification_needed` để Lãnh đạo HĐTV thấy popup yêu cầu Ban Kỹ thuật giải trình.

> Việc thêm nhánh `revision_requested` là cải tiến nhỏ so với sequence diagram gốc — nếu Cursor thực hiện, cần cập nhật lại file `system-design-hdtv-ai.md` (mermaid sequence) để đồng bộ tài liệu.

---

## 8. Cấu trúc thư mục đặt dữ liệu mẫu trong repo

```
hdtv-ai-prototype/
└── data/
    └── seed/
        └── dossier_198_uav/
            ├── 01_to_trinh_198_TTr_EVNHANOI.pdf       (từ "02. Tờ trình xin duyệt HĐTV...pdf")
            ├── 02_to_trinh_07KT_da_PTGD_duyet.pdf     (từ "Tờ trình B4 trình PTGĐ.pdf")
            ├── 03_bao_cao_tham_tra.pdf                (từ "03. Báo cáo thẩm tra.pdf")
            ├── 04_phieu_trinh.pdf                     (từ "03. 1phiếu trình.pdf" / "phiếu trình.pdf")
            ├── 05_phu_luc_so_sanh_ky_thuat.xlsx        (từ "Tiêu_chí_kỹ_thuật_so_sánh_3_sản_phẩm_final_chot 240914.xlsx")
            ├── 06_y_kien_gop_y_apex_tech.pdf           (từ "Ý kiến góp ý của máy bay không người lái của tư vấn ngoài.pdf")
            ├── 07_y_kien_gop_y_maj.pdf                 (từ "pdf2lop Ý kiến góp ý ... 2.pdf")
            ├── 08_bc_gop_y_cac_nha_cung_cap.xlsx       (từ "BC góp ý các nhà cung cấp 3.xlsx")
            └── ref/
                ├── qd_8594_qd_evnhanoi.pdf             (từ "QĐ giao danh mục MSTS X06 2024.pdf")
                └── pl_x06_dot2_2024.xlsx               (từ "PL X06 đợt 2 2024.xlsx")
```

Script seed (`scripts/seed_dossier_198.py`) sẽ:
1. Đọc các file trên, upload vào MinIO theo path `198-ttr-evnhanoi/...`.
2. Insert bản ghi `dossiers`, `dossier_documents`.
3. Parse `05_phu_luc_so_sanh_ky_thuat.xlsx` (sheet `4.1`, `4.2.1`–`4.2.4`) → lưu dạng JSON vào `dossier_documents.extracted_data` để FE render bảng PL01–PL04 mà không cần xử lý Excel ở client.
4. Chunk + embed nội dung PDF căn cứ pháp lý vào Chroma (collection `legal_docs`).
5. Chunk + embed nội dung Check 1–5 (Mục 4, viết sẵn dạng text) vào Chroma (collection `agent_memory`) — coi như kết quả của lần appraise đầu tiên, để demo "Chạy lại" vẫn có Agent Memory để truy xuất.

---

## 9. Checklist công việc cho Cursor (theo thứ tự ưu tiên)

1. **Chuẩn bị data:** copy & đổi tên file theo Mục 8 vào `data/seed/dossier_198_uav/`.
2. **Backend skeleton:** tạo FastAPI app theo cấu trúc `app/{models,schemas,routers,services,workers,mcp}` nếu chưa có; cấu hình Postgres, Redis, MinIO, Chroma qua docker-compose (đúng node Alpine VM theo Topology Constraints).
3. **DB migrations:** tạo bảng `dossiers, dossier_documents, dossier_versions, dossier_checklist_items, agent_plans, plan_steps, ai_audit_logs, mcp_call_logs, critic_verdicts, feedback_lessons`.
4. **Seed script:** viết & chạy `scripts/seed_dossier_198.py` (Mục 8) — đồng thời seed lại dossier #1 (Cáp ngầm) nếu chưa có trong DB, để DossierList có ≥2 record.
5. **LLM Router (mock mode):** implement interface + mock provider trả đúng nội dung Mục 4 theo `dossier_id`.
6. **Tool Registry:** thêm 2 tool mới (6.4) + audit logging.
7. **Celery pipeline `appraise_dossier`:** implement đủ 8 bước ở Mục 6.5, bắn WS events đúng thứ tự Mục 7.
8. **API endpoints** (Mục 6.1) cho Dossier Management + MCP endpoints (6.8).
9. **Frontend — DossierListView & DashboardView:** thêm dossier #198 (Mục 3.1).
10. **Frontend — SplitViewWorkspace.vue:**
    - Refactor mock data thành object theo `dossierId` (`mockDataByDossier['5'] = {...}`) thay vì `if/else` rời rạc như hiện tại.
    - Điền đủ nội dung Mục 5.1–5.7 cho `dossierId === '5'`.
    - Kết nối `rerunAppraisal()` tới API thật + WS thay cho `setTimeout` giả lập.
11. **Frontend — các view phụ:** `KnowledgeGraphView` (6.7), `AlertsView` (6.11), `SystemAdminView` (6.10), `SkillBuilderView`/`AdvancedChatView` (6.13), `DossierSettingsView` (3.2).
12. **MCP audit logs demo:** đảm bảo Admin → MCP Audit Logs hiển thị record dossier #198.
13. **Kiểm thử end-to-end:** từ `DossierListView` → mở dossier #198 → bấm "Chạy lại" → quan sát 5 check chạy lần lượt qua WS → mở modal chi tiết Check 3 → xem tab "Báo cáo Thẩm định" v1.1 → xem tab "Nghị quyết" → xem "Ý kiến Thành viên" có câu hỏi của thành viên #5 → vào "Hỏi đáp làm rõ Kết quả" để hỏi AI về Check 3.

---

## 10. Lưu ý khi giao việc cho Cursor

- **Giữ nguyên design system hiện tại** (CSS variables `--color-*`, class `.glass-panel`, icon set `@lucide/vue`) — không đổi theme/layout, chỉ bổ sung dữ liệu + logic.
- **Tách mock data khỏi component**: nên đưa các object Mục 5 vào file riêng (`src/mocks/dossier_198.js`) để dễ thay bằng API call sau, đúng tinh thần "mock trước, nối API sau".
- **LLM calls phải qua interface** `LLMRouter` để chuyển `mock → live` (Gemini/Gemma) chỉ bằng đổi `.env`, không sửa code nghiệp vụ.
- **Tuân thủ Topology Constraints** đã có trong system design: LLM (Gemma) chỉ chạy trên Ubuntu Node qua HTTP; mọi service HDTV khác (Postgres/Redis/Chroma/Meili/MinIO/FastAPI/Celery) nằm trên Alpine VM; mọi tool call phải ghi `ai_audit_logs` với `plan_step_id` + `error_type`.
- **Tài liệu gốc tiếng Việt có dấu** — khi đưa vào code/seed script, dùng UTF-8, tránh lỗi như khi unzip trên môi trường không hỗ trợ Unicode filename (đã gặp khi giải nén bộ hồ sơ mẫu).
