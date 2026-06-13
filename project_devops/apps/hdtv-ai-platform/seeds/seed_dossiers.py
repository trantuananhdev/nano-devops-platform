"""Seed dossiers — 12 hồ sơ EVNHANOI cover đủ 11 trạng thái.

Hồ sơ 1 (198/TTr-EVNHANOI): trích dẫn thật từ Tờ trình ngày 08/01/2025 — TGĐ Nguyễn Anh Tuấn ký.
Idempotent: kiểm tra doc_no trước khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Dossier, DossierStatus, RiskLevel

logger = logging.getLogger(__name__)

_UAV_PDF_TEXT = (
    "Số: 198/TTr-EVNHANOI, Hà Nội ngày 08 tháng 01 năm 2025\n\n"
    "TỜ TRÌNH — Về việc phê duyệt tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV)\n"
    "Kính gửi: Hội đồng Thành viên Tổng Công ty Điện lực TP Hà Nội\n\n"
    "Căn cứ QĐ 8594/QĐ-EVNHANOI ngày 06/12/2023 (giao danh mục mua sắm 2024 đợt 2 cho Công ty "
    "Lưới điện Cao thế TP HN); Xét Tờ trình 07/KT ngày 07/01/2025 của Ban Kỹ thuật (đã được "
    "Phó TGĐ Kỹ thuật Nguyễn Anh Dũng phê duyệt).\n\n"
    "MỤC ĐÍCH: Mua sắm và vận hành thí điểm 04 bộ UAV phục vụ kiểm tra đường dây 220/110kV, "
    "giao Công ty Lưới điện Cao thế TP HN thực hiện (NQ 180/NQ-HĐTV, QĐ 8594/QĐ-EVNHANOI).\n\n"
    "YÊU CẦU KỸ THUẬT (Phụ lục I — 07/KT):\n"
    "1. THIẾT BỊ BAY: Trọng lượng ≤16kg (không camera), tối đa ≤31kg. "
    "Kích thước ≤1100×1150×800mm. Động cơ không chổi than ≥4 cái. Tín hiệu ≥15km.\n"
    "2. HIỆU NĂNG: Bay ≥40 phút; quãng đường ≥35km; tốc độ ≥15m/s; "
    "kháng gió ≥12m/s (cấp 5); IP45+.\n"
    "3. ĐỊNH VỊ: RTK tích hợp; GNSS ≥4 hệ thống (GPS+GLONASS+BeiDou+Galileo); "
    "độ chính xác ≤1cm+1ppm RTK.\n"
    "4. CAMERA: Màu zoom quang ≥15×; Nhiệt (FLIR/tương đương) ≥640×512px, đo ±2°C.\n"
    "5. LIDAR: ≥480.000 điểm/giây; tầm ≥450m; độ chính xác ±5cm.\n"
    "6. TẢI TRỌNG: Phụ ≥1.5kg; cảm biến chướng ngại vật ≥4 hướng.\n"
    "7. CHUNG: Nhà sản xuất ISO; thiết bị mới 100%, sản xuất ≤2 năm; nhiệt đới hóa phù hợp VN.\n\n"
    "KHẢO SÁT GIÁ: Hỏi 4 đơn vị (VJO Việt Nam, Apex Tech VN, MAJ, Thiết bị Thắng Lợi). "
    "2 đơn vị phúc đáp: Apex Tech Việt Nam và MAJ.\n"
    "TGĐ EVNHANOI: Nguyễn Anh Tuấn"
)

DOSSIERS_DATA = [
    {
        "doc_no": "198/TTr-EVNHANOI",
        "title": (
            "Phê duyệt tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV) "
            "phục vụ kiểm tra đường dây 220/110kV"
        ),
        "unit": "Ban Kỹ thuật / EVNHANOI (đề xuất từ Công ty Lưới điện Cao thế TP HN)",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.board_reviewed,
        "pdf_url": "dossiers/uav-198/02-to-trinh-xin-duyet-HDTV.pdf",
        "pdf_text": _UAV_PDF_TEXT,
    },
    {
        "doc_no": "EVNHANOI-MBA-2024-021",
        "title": "Mua sắm máy biến áp phân phối 3 pha 22/0.4kV — 250kVA (50 bộ)",
        "unit": "Ban Vật tư - Đầu tư / EVNHANOI",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.dept_approved,
        "pdf_text": "Hồ sơ mua sắm MBA 250kVA phục vụ thay thế thiết bị quá tải trên lưới trung thế Hà Nội.",
    },
    {
        "doc_no": "EVNHANOI-CAP-2024-033",
        "title": "Mua sắm cáp ngầm 22kV XLPE phục vụ ngầm hóa lưới điện Quận Hoàn Kiếm",
        "unit": "Ban Kỹ thuật - Sản xuất / EVNHANOI",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.pending,
        "pdf_text": "Hồ sơ cáp ngầm 22kV theo kế hoạch ngầm hóa lưới điện đường phố cổ Hà Nội.",
    },
    {
        "doc_no": "EVNHANOI-SCADA-2024-007",
        "title": "Nâng cấp hệ thống SCADA/DMS điều độ lưới điện Hà Nội",
        "unit": "Ban CNTT / EVNHANOI",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.approved,
        "pdf_text": "Nâng cấp hệ thống SCADA trung tâm điều độ lưới điện, tích hợp DMS thế hệ mới.",
    },
    {
        "doc_no": "EVNHANOI-IT-2024-044",
        "title": "Mua sắm máy tính xách tay phục vụ công tác vận hành và quản lý",
        "unit": "Ban CNTT / EVNHANOI",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.draft,
        "pdf_text": None,
    },
    {
        "doc_no": "EVNHANOI-XL-2024-015",
        "title": "Thi công lắp đặt trạm biến áp 110kV Tây Hồ — giai đoạn 2",
        "unit": "Ban Quản lý Dự án / EVNHANOI",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.submitted_to_dept,
        "pdf_text": "Gói thầu thi công xây lắp trạm 110kV Tây Hồ phục vụ cấp điện khu vực Tây Hồ Tây.",
    },
    {
        "doc_no": "EVNHANOI-TU-2024-028",
        "title": "Tư vấn giám sát xây dựng đường dây 110kV Đông Anh - Sóc Sơn",
        "unit": "Ban Quản lý Dự án / EVNHANOI",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.dept_rejected,
        "pdf_text": "Tư vấn giám sát thi công đường dây 110kV mạch kép từ trạm Đông Anh đến Sóc Sơn.",
    },
    {
        "doc_no": "EVNHANOI-BT-2024-009",
        "title": "Bảo trì thiết bị đo đếm điện năng 110kV tại các trạm khu vực Hà Nội",
        "unit": "Ban Kỹ thuật - Sản xuất / EVNHANOI",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.submitted_to_board,
        "pdf_text": "Bảo trì định kỳ hệ thống đo đếm điện năng theo quy định kiểm định đo lường.",
    },
    {
        "doc_no": "EVNHANOI-VT-2024-052",
        "title": "Mua sắm vật tư thiết bị điện cho sửa chữa thường xuyên lưới điện 2024",
        "unit": "Ban Vật tư - Đầu tư / EVNHANOI",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.board_reviewed,
        "pdf_text": "Vật tư SCTX gồm: cầu chì, cột điện, sứ cách điện, dây dẫn trung thế.",
    },
    {
        "doc_no": "EVNHANOI-KT-2024-018",
        "title": "Kiểm tra thí nghiệm thiết bị điện cao áp định kỳ 2024",
        "unit": "Ban Kỹ thuật - Sản xuất / EVNHANOI",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.rejected,
        "pdf_text": "Hồ sơ thí nghiệm định kỳ MBA, máy cắt, dao cách ly 110kV. Thiếu biên bản nghiệm thu 2023.",
    },
    {
        "doc_no": "EVNHANOI-NL-2024-061",
        "title": "Mua sắm phần mềm quản lý vận hành lưới điện thông minh (Smart Grid)",
        "unit": "Ban CNTT / EVNHANOI",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.needs_revision,
        "pdf_text": "Phần mềm tích hợp IoT sensor lưới điện, phân tích dữ liệu real-time cho điều độ.",
    },
    {
        "doc_no": "EVNHANOI-AN-2024-006",
        "title": "Mua sắm dụng cụ an toàn lao động làm việc điện cao áp năm 2024",
        "unit": "Ban An toàn - Bảo hộ lao động / EVNHANOI",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.pending,
        "pdf_text": "Dụng cụ AT: găng tay cách điện, thảm cao su, sào thao tác, thiết bị đo điện cầm tay.",
    },
]


async def seed_dossiers(session: AsyncSession) -> dict[str, int]:
    """Seed dossiers, return doc_no→id map."""
    id_map: dict[str, int] = {}

    for d in DOSSIERS_DATA:
        existing = (
            await session.execute(select(Dossier).where(Dossier.doc_no == d["doc_no"]))
        ).scalar_one_or_none()

        if existing:
            id_map[d["doc_no"]] = existing.id
            logger.info("Dossier already exists: %s", d["doc_no"])
            continue

        dossier = Dossier(**d)
        session.add(dossier)
        await session.flush()
        id_map[d["doc_no"]] = dossier.id
        logger.info("Seeded dossier: %s — %s", d["doc_no"], d["status"].value)

    await session.commit()
    return id_map
