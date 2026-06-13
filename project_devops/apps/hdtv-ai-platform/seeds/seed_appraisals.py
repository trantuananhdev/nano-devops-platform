"""Seed appraisal results — 4 kết quả thẩm định AI.

Idempotent: kiểm tra dossier_id trước khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AppraisalResult, RiskLevel

logger = logging.getLogger(__name__)

APPRAISALS_DATA = [
    # === UAV 198/TTr-EVNHANOI — medium risk, đề nghị thông qua sau khi hiệu chỉnh ===
    # Dựa trên Báo cáo thẩm tra của Ban Tổng hợp ngày 24/01/2025 (Hà Tuấn Minh thẩm tra,
    # Đoàn Đức Tiến ký). Kết luận: đề nghị HĐTV thông qua với 2 kiến nghị hiệu chỉnh.
    {
        "doc_no": "198/TTr-EVNHANOI",
        "overall_risk": RiskLevel.medium,
        "report_md": (
            "## Kết quả Thẩm định AI — Hồ sơ 198/TTr-EVNHANOI\n\n"
            "**Hồ sơ:** 198/TTr-EVNHANOI — Phê duyệt TCKT UAV phục vụ kiểm tra đường dây 220/110kV  \n"
            "**Ngày thẩm định:** 24/01/2025  \n"
            "**Kết luận:** ⚠️ ĐỀ NGHỊ THÔNG QUA — có 2 kiến nghị hiệu chỉnh (Rủi ro TRUNG BÌNH)\n\n"
            "---\n\n"
            "### 1. Kiểm tra Pháp lý và Thẩm quyền (LegalGraphRAG)\n"
            "| Hạng mục | Kết quả |\n"
            "|---------|----------|\n"
            "| Hồ sơ trình đúng thẩm quyền HĐTV EVNHANOI | ✅ ĐẠT |\n"
            "| Căn cứ pháp lý đầy đủ (QĐ 8594, NQ 180/NQ-HĐTV, Điều lệ EVNHANOI) | ✅ ĐẠT |\n"
            "| Tờ trình 07/KT đã có chữ ký PTGĐ Kỹ thuật phê duyệt | ✅ ĐẠT |\n"
            "| Tờ trình 198/TTr-EVNHANOI có chữ ký TGĐ | ✅ ĐẠT |\n\n"
            "**Nhận xét:** Hồ sơ đủ thẩm quyền HĐTV. Trình tự Ban KT → PTGĐ KT → TGĐ → HĐTV đúng quy trình.\n\n"
            "### 2. Kiểm tra Tiêu chuẩn Kỹ thuật (TechnicalStandardCheck)\n"
            "| Hạng mục | Kết quả |\n"
            "|---------|----------|\n"
            "| Tiêu chuẩn thiết bị bay (trọng lượng, thời gian, tốc độ) | ✅ ĐẠT |\n"
            "| GNSS ≥4 hệ thống + RTK tích hợp | ✅ ĐẠT |\n"
            "| Camera nhiệt 640×512px, LIDAR ≥480.000 điểm/giây | ✅ ĐẠT |\n"
            "| Nhất quán thuật ngữ giữa các phần | ⚠️ CẦN HIỆU CHỈNH |\n\n"
            "**Phát hiện:** Trong Phụ lục I xuất hiện cả 'máy bay không người lái' và 'thiết bị bay "
            "không người lái' cho cùng một đối tượng. Cần thống nhất một cụm từ xuyên suốt tài liệu.\n\n"
            "### 3. Kiểm tra Quy trình Mua sắm (ProcurementCheck)\n"
            "| Hạng mục | Kết quả |\n"
            "|---------|----------|\n"
            "| Khảo sát thị trường (4 nhà phân phối) | ✅ ĐẠT |\n"
            "| 2/4 đơn vị phúc đáp (Apex Tech VN + MAJ) | ⚠️ CHÚ Ý |\n"
            "| Tiêu chuẩn kỹ thuật không chứa yếu tố đấu thầu | ⚠️ CẦN HIỆU CHỈNH |\n\n"
            "**Phát hiện:** Phụ lục I còn sử dụng các cụm từ 'Nhà thầu', 'Hồ sơ dự thầu' — đây là tiêu "
            "chuẩn kỹ thuật, không phải hồ sơ mời thầu. Cần loại bỏ các yếu tố đấu thầu để tránh "
            "nhầm lẫn về bản chất pháp lý của văn bản.\n\n"
            "---\n\n"
            "### Tổng kết\n"
            "- **Pháp lý:** ĐẠT ✅ — hồ sơ đúng thẩm quyền, đủ căn cứ pháp lý\n"
            "- **Kỹ thuật:** ĐẠT có điều kiện ⚠️ — nội dung đáp ứng, cần thống nhất thuật ngữ\n"
            "- **Mua sắm:** ĐẠT có điều kiện ⚠️ — cần loại bỏ ngôn ngữ đấu thầu\n\n"
            "> *Tổng hợp từ phân tích AI dựa trên Báo cáo thẩm tra Ban Tổng hợp ngày 24/01/2025, "
            "người thẩm tra: Hà Tuấn Minh; Trưởng ban: Đoàn Đức Tiến.*"
        ),
        "resolution_md": (
            "**Đề nghị HĐTV EVNHANOI thông qua** Tờ trình 198/TTr-EVNHANOI với điều kiện "
            "Ban Kỹ thuật thực hiện 2 kiến nghị hiệu chỉnh sau trước khi ban hành tiêu chuẩn:\n\n"
            "1. **Thống nhất thuật ngữ:** Dùng nhất quán cụm từ 'thiết bị bay không người lái' "
            "hoặc 'máy bay không người lái' xuyên suốt Phụ lục I và các tài liệu đính kèm.\n\n"
            "2. **Loại bỏ yếu tố đấu thầu:** Xóa các cụm từ 'Nhà thầu', 'Hồ sơ dự thầu' khỏi "
            "tiêu chuẩn kỹ thuật — đây là văn bản phê duyệt tiêu chuẩn, không phải hồ sơ mời thầu.\n\n"
            "Sau khi hiệu chỉnh, tiêu chuẩn kỹ thuật sẽ được áp dụng cho việc mua sắm 04 bộ UAV "
            "tại Công ty Lưới điện Cao thế TP Hà Nội."
        ),
        "checks": [
            {"tool": "LegalGraphRAG", "status": "pass", "score": 0.96,
             "detail": "Đúng thẩm quyền HĐTV; căn cứ pháp lý đầy đủ; trình tự phê duyệt đúng"},
            {"tool": "TechnicalStandardCheck", "status": "warning", "score": 0.71,
             "detail": "Tiêu chuẩn kỹ thuật đáp ứng yêu cầu vận hành; cần thống nhất thuật ngữ"},
            {"tool": "ProcurementCheck", "status": "warning", "score": 0.68,
             "detail": "2/4 nhà phân phối phúc đáp; còn ngôn ngữ đấu thầu trong TCKT"},
        ],
        "critic_verdict": {
            "approved": True,
            "confidence": 0.87,
            "comments": (
                "Hồ sơ đủ điều kiện thông qua HĐTV sau khi thực hiện 2 kiến nghị hiệu chỉnh. "
                "Tiêu chuẩn kỹ thuật UAV phù hợp yêu cầu vận hành kiểm tra đường dây 220/110kV. "
                "Không có rủi ro pháp lý hoặc tài chính nghiêm trọng."
            ),
        },
    },
    # === SCADA — approved, low risk ===
    {
        "doc_no": "EVNHANOI-SCADA-2024-007",
        "overall_risk": RiskLevel.low,
        "report_md": (
            "## Kết quả Thẩm định AI\n\n"
            "**Hồ sơ:** EVNHANOI-SCADA-2024-007 — Nâng cấp hệ thống SCADA/DMS\n"
            "**Kết luận:** ✅ Đủ điều kiện phê duyệt — Rủi ro THẤP\n\n"
            "### 1. Kiểm tra Pháp lý (LegalGraphRAG)\n"
            "Hợp đồng nguyên tắc Siemens VN ✅ | Giấy phép nhập khẩu ✅ | "
            "IEC 61850-1:2013 ✅ | TCVN 11862:2017 ✅\n\n"
            "### 2. Kiểm tra Tài chính (ErpBudgetCheck)\n"
            "Dự toán 4.250.000.000 VND — trong ngưỡng 5 tỷ; chênh kế hoạch -2.1% ✅\n\n"
            "### 3. Kiểm tra Kỹ thuật\n"
            "Siemens SINAUT MD720-3 phù hợp đặc tính kỹ thuật ✅ | WinCC OA v3.19 tương thích ✅ | "
            "Bảo hành 36 tháng ✅"
        ),
        "resolution_md": (
            "Đề nghị phê duyệt. Điều kiện: nhà thầu cam kết bảo hành 36 tháng và đào tạo "
            "≥5 kỹ sư điều độ trong 30 ngày sau nghiệm thu."
        ),
        "checks": [
            {"tool": "LegalGraphRAG", "status": "pass", "score": 0.94},
            {"tool": "ErpBudgetCheck", "status": "pass", "score": 0.91},
            {"tool": "ErpInventoryCheck", "status": "pass", "score": 0.88},
        ],
        "critic_verdict": {
            "approved": True,
            "confidence": 0.92,
            "comments": "Hồ sơ đầy đủ, minh bạch. Không có điểm cần làm rõ.",
        },
    },
    # === MBA — dept_approved, high risk (giá vượt) ===
    {
        "doc_no": "EVNHANOI-MBA-2024-021",
        "overall_risk": RiskLevel.high,
        "report_md": (
            "## Kết quả Thẩm định AI\n\n"
            "**Hồ sơ:** EVNHANOI-MBA-2024-021 — Mua sắm MBA 250kVA (50 bộ)\n"
            "**Kết luận:** ⚠️ CẦN XEM XÉT — Rủi ro CAO (giá vượt khung)\n\n"
            "### Kiểm tra Tài chính (ErpBudgetCheck)\n"
            "| Hạng mục | Giá trị |\n"
            "|---------|----------|\n"
            "| Đơn giá đề xuất (ABB 250kVA) | 185.000.000 VND/bộ |\n"
            "| Khung giá EVN 2024 | 150.000.000 VND/bộ |\n"
            "| Chênh lệch | **+23.3%** ❌ |\n"
            "| Tổng chênh (50 bộ) | **1.750.000.000 VND** |\n"
        ),
        "resolution_md": (
            "Yêu cầu giải trình chênh lệch giá hoặc đề xuất nhà cung cấp thay thế "
            "(Siemens Energy hoặc THIBIDI: 148-155 triệu/bộ). Hoàn thiện trong 15 ngày."
        ),
        "checks": [
            {"tool": "LegalGraphRAG", "status": "pass", "score": 0.89},
            {"tool": "ErpBudgetCheck", "status": "fail", "score": 0.23, "price_anomaly": True},
        ],
        "critic_verdict": {
            "approved": False,
            "confidence": 0.88,
            "comments": "Giá vượt 23.3% khung EVN. Cần đàm phán hoặc đổi nhà cung cấp.",
        },
    },
    # === KT — rejected (thiếu hồ sơ) ===
    {
        "doc_no": "EVNHANOI-KT-2024-018",
        "overall_risk": RiskLevel.high,
        "report_md": (
            "## Kết quả Thẩm định AI\n\n"
            "**Hồ sơ:** EVNHANOI-KT-2024-018 — Thí nghiệm thiết bị điện cao áp 2024\n"
            "**Kết luận:** ❌ KHÔNG ĐỦ ĐIỀU KIỆN — Thiếu tài liệu bắt buộc\n\n"
            "### Kiểm tra Pháp lý (LegalGraphRAG)\n"
            "Năng lực đơn vị thí nghiệm ✅ | Biên bản nghiệm thu 2023 ❌ THIẾU | "
            "Báo cáo kỹ thuật lần trước ❌ THIẾU\n\n"
            "Theo Quy trình thí nghiệm EVN-QT-KT-07, biên bản nghiệm thu kỳ trước là tài liệu "
            "bắt buộc để so sánh xu hướng suy giảm cách điện."
        ),
        "resolution_md": (
            "Trả lại hồ sơ. Yêu cầu bổ sung: (1) Biên bản nghiệm thu 2023 có ký xác nhận "
            "Trưởng phòng KT; (2) Báo cáo phân tích xu hướng cách điện 3 năm. Hạn: 20 ngày."
        ),
        "checks": [
            {"tool": "LegalGraphRAG", "status": "fail", "score": 0.12,
             "missing_docs": ["bien_ban_nghiem_thu_2023", "bao_cao_ky_thuat"]},
        ],
        "critic_verdict": {
            "approved": False,
            "confidence": 0.97,
            "comments": "Thiếu tài liệu baseline bắt buộc. Không thể thẩm định khi thiếu kỳ trước.",
        },
    },
]


async def seed_appraisals(session: AsyncSession, dossier_id_map: dict[str, int]) -> None:
    """Seed appraisal results."""
    for a in APPRAISALS_DATA:
        doc_no = a["doc_no"]
        dossier_id = dossier_id_map.get(doc_no)
        if not dossier_id:
            logger.warning("Dossier not found for appraisal: %s", doc_no)
            continue

        existing = (
            await session.execute(
                select(AppraisalResult).where(AppraisalResult.dossier_id == dossier_id)
            )
        ).scalar_one_or_none()

        if existing:
            logger.info("Appraisal already exists for dossier: %s", doc_no)
            continue

        result = AppraisalResult(
            dossier_id=dossier_id,
            overall_risk=a["overall_risk"],
            report_md=a["report_md"],
            resolution_md=a["resolution_md"],
            checks=a["checks"],
            critic_verdict=a["critic_verdict"],
        )
        session.add(result)
        logger.info("Seeded appraisal for %s — risk: %s", doc_no, a["overall_risk"].value)

    await session.commit()
