"""Seed appraisal results — 3 kết quả thẩm định AI.

Idempotent: kiểm tra dossier_id trước khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AppraisalResult, RiskLevel

logger = logging.getLogger(__name__)

APPRAISALS_DATA = [
    # === SCADA — approved, low risk ===
    {
        "doc_no": "EVNHANOI-SCADA-2024-007",
        "overall_risk": RiskLevel.low,
        "report_md": """## Kết quả Thẩm định AI

**Hồ sơ:** EVNHANOI-SCADA-2024-007 — Nâng cấp hệ thống SCADA/DMS điều độ lưới điện Hà Nội
**Ngày thẩm định:** 13/06/2026
**Kết luận:** ✅ Đủ điều kiện phê duyệt — Rủi ro THẤP

---

### 1. Kiểm tra Pháp lý (LegalGraphRAG)
| Hạng mục | Kết quả |
|---------|---------|
| Hợp đồng nguyên tắc với Siemens Việt Nam | ✅ ĐẠT |
| Giấy phép nhập khẩu thiết bị điện tử | ✅ ĐẠT |
| Chứng nhận IEC 61850-1:2013 cho RTU | ✅ ĐẠT |
| Chứng nhận TCVN 11862:2017 cho SCADA server | ✅ ĐẠT |

**Nhận xét:** Tất cả chứng từ pháp lý hợp lệ, còn hiệu lực tối thiểu 12 tháng.

### 2. Kiểm tra Tài chính (ErpBudgetCheck)
| Hạng mục | Giá trị |
|---------|---------|
| Tổng dự toán đề xuất | 4.250.000.000 VND |
| Ngưỡng phê duyệt | 5.000.000.000 VND |
| Chênh lệch so với kế hoạch 2024 | -2.1% |

**Nhận xét:** Trong ngưỡng phê duyệt, giá thiết bị phù hợp tham chiếu thị trường Q2/2026.

### 3. Kiểm tra Kỹ thuật (ErpInventoryCheck)
- Thiết bị Siemens SINAUT MD720-3: phù hợp đặc tính kỹ thuật yêu cầu ✅
- Phần mềm WinCC OA v3.19: tương thích hạ tầng hiện tại ✅
- Thời gian bảo hành: 36 tháng — đáp ứng yêu cầu tối thiểu 24 tháng ✅
""",
        "resolution_md": (
            "Đề nghị phê duyệt hồ sơ. "
            "Điều kiện: nhà thầu phải cam kết bảo hành 36 tháng và cung cấp đào tạo vận hành "
            "cho ít nhất 5 kỹ sư điều độ trong vòng 30 ngày sau nghiệm thu."
        ),
        "checks": [
            {"tool": "LegalGraphRAG", "status": "pass", "score": 0.94},
            {"tool": "ErpBudgetCheck", "status": "pass", "score": 0.91},
            {"tool": "ErpInventoryCheck", "status": "pass", "score": 0.88},
        ],
        "critic_verdict": {
            "approved": True,
            "confidence": 0.92,
            "comments": "Hồ sơ đầy đủ, minh bạch. Không có điểm cần làm rõ thêm.",
        },
    },
    # === MBA — dept_approved, high risk (giá vượt) ===
    {
        "doc_no": "EVNHANOI-MBA-2024-021",
        "overall_risk": RiskLevel.high,
        "report_md": """## Kết quả Thẩm định AI

**Hồ sơ:** EVNHANOI-MBA-2024-021 — Mua sắm máy biến áp phân phối 250kVA (50 bộ)
**Ngày thẩm định:** 13/06/2026
**Kết luận:** ⚠️ CẦN XEM XÉT LẠI — Rủi ro CAO (giá vượt khung)

---

### 1. Kiểm tra Pháp lý (LegalGraphRAG)
| Hạng mục | Kết quả |
|---------|---------|
| Giấy phép kinh doanh nhà cung cấp | ✅ ĐẠT |
| Chứng nhận TCVN 6306-1:2015 | ✅ ĐẠT |
| Hồ sơ kỹ thuật (TDS) | ✅ ĐẠT |

### 2. Kiểm tra Tài chính (ErpBudgetCheck)
| Hạng mục | Giá trị |
|---------|---------|
| Đơn giá đề xuất (ABB 250kVA) | 185.000.000 VND/bộ |
| Khung giá EVN 2024 | 150.000.000 VND/bộ |
| Chênh lệch | **+23.3%** ❌ |
| Tổng chênh lệch (50 bộ) | **1.750.000.000 VND** |

**Nhận xét:** Vượt ngưỡng cho phép 130% khung giá. Cần giải trình hoặc thay nhà cung cấp.
""",
        "resolution_md": (
            "Yêu cầu nhà thầu giải trình chênh lệch giá hoặc đề xuất nhà cung cấp thay thế. "
            "Có thể xem xét Siemens Energy hoặc THIBIDI (giá tham chiếu 148-155 triệu VND/bộ). "
            "Hoàn thiện hồ sơ trong 15 ngày làm việc."
        ),
        "checks": [
            {"tool": "LegalGraphRAG", "status": "pass", "score": 0.89},
            {"tool": "ErpBudgetCheck", "status": "fail", "score": 0.23, "price_anomaly": True},
        ],
        "critic_verdict": {
            "approved": False,
            "confidence": 0.88,
            "comments": "Giá vượt 23.3% khung EVN. Cần đàm phán giá hoặc đổi nhà cung cấp trước khi phê duyệt.",
        },
    },
    # === KT — rejected (thiếu hồ sơ) ===
    {
        "doc_no": "EVNHANOI-KT-2024-018",
        "overall_risk": RiskLevel.high,
        "report_md": """## Kết quả Thẩm định AI

**Hồ sơ:** EVNHANOI-KT-2024-018 — Kiểm tra thí nghiệm thiết bị điện cao áp định kỳ 2024
**Ngày thẩm định:** 13/06/2026
**Kết luận:** ❌ KHÔNG ĐỦ ĐIỀU KIỆN — Thiếu tài liệu bắt buộc

---

### Kiểm tra Pháp lý (LegalGraphRAG)
| Hạng mục | Kết quả |
|---------|---------|
| Hồ sơ năng lực đơn vị thí nghiệm | ✅ ĐẠT |
| Biên bản nghiệm thu thí nghiệm định kỳ 2023 | ❌ THIẾU |
| Báo cáo kỹ thuật thử nghiệm lần trước | ❌ THIẾU |

**Nhận xét:** Theo Quy trình thí nghiệm định kỳ EVN-QT-KT-07, biên bản nghiệm thu kỳ trước
là tài liệu bắt buộc để so sánh, phát hiện xu hướng suy giảm cách điện.
""",
        "resolution_md": (
            "Trả lại hồ sơ. Yêu cầu bổ sung: (1) Biên bản nghiệm thu thí nghiệm định kỳ 2023 "
            "có ký xác nhận của Trưởng phòng Kỹ thuật. "
            "(2) Báo cáo kỹ thuật phân tích xu hướng cách điện 3 năm gần nhất. "
            "Hạn nộp lại: trong vòng 20 ngày làm việc."
        ),
        "checks": [
            {"tool": "LegalGraphRAG", "status": "fail", "score": 0.12, "missing_docs": ["bien_ban_nghiem_thu_2023", "bao_cao_ky_thuat"]},
        ],
        "critic_verdict": {
            "approved": False,
            "confidence": 0.97,
            "comments": "Thiếu tài liệu bắt buộc theo ND24 và quy trình nội bộ EVN. Không thể thẩm định khi thiếu baseline kỳ trước.",
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
