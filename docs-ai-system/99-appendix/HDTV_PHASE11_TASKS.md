# Phase 11 — Real Data & UX Optimization

> **Mục tiêu:** Tối ưu hóa nghiệp vụ và UI/UX, thêm dữ liệu thực từ folder mẫu để có được demo thật.
> **Nguồn dữ liệu:** `C:\TA-work\project-table\nano-project-devops\Mẫu phê duyệt tờ trình của KT (đơn giản)`

---

## Status Legend: PENDING | IN_PROGRESS | DONE | BLOCKED

---

### T-38: Data Folder Structure & File Renaming
- **deps:** T-37
- **priority:** P1 — chuẩn bị dữ liệu thật
- **files:**
  - `hdtv-ai-platform/data/seed/dossier_198_uav/` — tạo thư mục
  - copy & rename files từ mẫu theo cấu trúc:
    - `01_to_trinh_198_TTr_EVNHANOI.pdf`
    - `02_to_trinh_07KT_da_PTGD_duyet.pdf`
    - `03_bao_cao_tham_tra.pdf`
    - `04_phieu_trinh.pdf`
    - `05_phu_luc_so_sanh_ky_thuat.xlsx`
    - `06_y_kien_gop_y_apex_tech.pdf`
    - `07_y_kien_gop_y_maj.pdf`
    - `08_bc_gop_y_cac_nha_cung_cap.xlsx`
    - `ref/qd_8594_qd_evnhanoi.pdf`
    - `ref/pl_x06_dot2_2024.xlsx`
- **acceptance:** Tất cả file được copy đúng tên và thư mục
- **verify_cmd:** `ls -la project_devops/apps/hdtv-ai-platform/data/seed/dossier_198_uav/`
- **status:** DONE ✅

---

### T-39: Seed Script Upgrade — Real Dossier + MinIO Upload
- **deps:** T-38
- **priority:** P1
- **files:**
  - `hdtv-ai-platform/scripts/seed.py` — nâng cấp để upload PDF thật lên MinIO
  - thêm function `seed_dossier_198_pdfs()`
  - seed dossier 198/TTr-EVNHANOI vào DB
- **acceptance:** Dossier 198 tồn tại trong DB; PDF upload lên MinIO thành công
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE ✅

---

### T-40: OCR PDF & Legal RAG Ingestion
- **deps:** T-39
- **priority:** P1 — extract text từ PDF thật
- **files:**
  - `requirements.txt` — thêm `PyMuPDF==1.24.13`
  - `app/services/rag/pdf_extractor.py` — NEW: extract text từ PDF
  - `scripts/seed.py` — thêm `seed_real_legal_docs()`
- **acceptance:** Text từ PDF được extract và ingest vào Chroma; LegalGraphRAG có thể truy vấn được
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE ✅

---

### T-41: UX/UI Optimization
- **deps**: T-40
- **priority**: P2 — cải thiện trải nghiệm người dùng
- **files**:
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — tối ưu PDF viewer, loading states
  - `hdtv-ai-prototype/src/views/DossierListView.vue` — thêm badge risk level
  - `hdtv-ai-prototype/src/views/DashboardView.vue` — thêm widget dossier mới nhất
  - `hdtv-ai-prototype/src/assets/main.css` — cải thiện responsive design
- **acceptance**: UI/UX trông chuyên nghiệp hơn; loading states rõ ràng
- **verify_cmd**: `npm run build` in hdtv-ai-prototype
- **status**: DONE ✅

---

### T-42: Demo Preparation & Documentation
- **deps:** T-41
- **priority:** P2
- **files:**
  - `HDTV_DEMO_GUIDE.md` — NEW: tài liệu hướng dẫn demo từ A-Z
  - cập nhật `PROJECT_STATE.md`
- **acceptance:** Tài liệu hướng dẫn đầy đủ, rõ ràng
- **verify_cmd:** —
- **status:** DONE ✅

---

## Phase 11 Dependency Graph

| Task | Blocked by | Priority |
|------|------------|----------|
| T-38 | — | P1 |
| T-39 | T-38 | P1 |
| T-40 | T-39 | P1 |
| T-41 | T-40 | P2 |
| T-42 | T-41 | P2 |

**Thứ tự thực hiện:** T-38 → T-39 → T-40 → T-41 → T-42
