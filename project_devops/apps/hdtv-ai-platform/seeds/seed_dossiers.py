"""Seed dossiers — 12 hồ sơ EVNHANOI cover đủ 11 trạng thái.

Hồ sơ 1 (EVNHANOI-UAV-198-2024): dữ liệu thật từ data/seed/dossier_198_uav/
Idempotent: kiểm tra doc_no trước khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Dossier, DossierStatus, RiskLevel

logger = logging.getLogger(__name__)

DOSSIERS_DATA = [
    # === HỒ SƠ CHÍNH — dữ liệu thật UAV EVNHANOI ===
    {
        "doc_no": "EVNHANOI-UAV-198-2024",
        "title": "Mua sắm máy bay không người lái (UAV) phục vụ kiểm tra, giám sát đường dây và trạm biến áp",
        "unit": "Ban Kỹ thuật - Sản xuất / EVNHANOI",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.appraising,
        "pdf_text": (
            "Căn cứ Quyết định số 8594/QĐ-EVNHANOI về việc giao danh mục mua sắm thường xuyên "
            "X06 đợt 2 năm 2024, Ban Kỹ thuật - Sản xuất đề nghị phê duyệt mua sắm 03 máy bay "
            "không người lái (UAV) loại đa rotor phục vụ kiểm tra, giám sát đường dây 110kV và "
            "trạm biến áp. Tổng dự toán: 1.855.000.000 VNĐ (một tỷ tám trăm năm mươi lăm triệu "
            "đồng). Nhà cung cấp đề xuất: Công ty CP Công nghệ Thiên Vũ và DJI Enterprise Vietnam. "
            "Tiêu chí kỹ thuật: tải trọng ≥1kg, thời gian bay ≥45 phút, camera nhiệt độ phân giải "
            "cao, chứng nhận ICAO Annex 8, kháng gió cấp 7."
        ),
    },
    # === 11 HỒ SƠ KHÁC — cover đủ trạng thái ===
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
