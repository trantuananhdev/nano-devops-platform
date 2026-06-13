"""Seed alerts — 8 cảnh báo dựa trên tài liệu thật.

2 cảnh báo UAV từ Báo cáo thẩm tra Ban Tổng hợp ngày 24/01/2025.
Idempotent: kiểm tra description trước khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Alert, AlertStatus

logger = logging.getLogger(__name__)

ALERTS_DATA = [
    # === 2 cảnh báo UAV từ Báo cáo thẩm tra thật (Hà Tuấn Minh — Ban Tổng hợp, 24/01/2025) ===
    {
        "doc_no": "198/TTr-EVNHANOI",
        "title": "Chưa thống nhất thuật ngữ trong Tiêu chuẩn kỹ thuật UAV",
        "severity": "medium",
        "source": "TechnicalStandardCheck",
        "description": (
            "Hồ sơ 198/TTr-EVNHANOI: Phụ lục I (Tờ trình 07/KT) sử dụng đan xen hai cụm từ "
            "'máy bay không người lái' và 'thiết bị bay không người lái' cho cùng một đối tượng. "
            "Theo kiến nghị Báo cáo thẩm tra Ban Tổng hợp (24/01/2025): Ban Kỹ thuật cần thống "
            "nhất một cụm từ duy nhất xuyên suốt toàn bộ tài liệu trước khi ban hành tiêu chuẩn."
        ),
        "status": AlertStatus.open,
    },
    {
        "doc_no": "198/TTr-EVNHANOI",
        "title": "Tiêu chuẩn kỹ thuật còn chứa yếu tố đấu thầu không phù hợp",
        "severity": "medium",
        "source": "ProcurementCheck",
        "description": (
            "Hồ sơ 198/TTr-EVNHANOI: Phụ lục I (Tờ trình 07/KT) còn sử dụng các cụm từ 'Nhà thầu' "
            "và 'Hồ sơ dự thầu' — đây là văn bản phê duyệt tiêu chuẩn kỹ thuật, không phải hồ sơ "
            "mời thầu. Theo kiến nghị Báo cáo thẩm tra (24/01/2025): cần loại bỏ các yếu tố đấu "
            "thầu để tránh nhầm lẫn về bản chất pháp lý của văn bản tiêu chuẩn kỹ thuật."
        ),
        "status": AlertStatus.open,
    },
    # === Các cảnh báo hồ sơ khác ===
    {
        "doc_no": "EVNHANOI-MBA-2024-021",
        "title": "Giá MBA ABB 250kVA vượt 23% khung giá EVN",
        "severity": "high",
        "source": "ErpBudgetCheck",
        "description": (
            "Hồ sơ EVNHANOI-MBA-2024-021: Đơn giá MBA ABB 250kVA đề xuất 185.000.000 VND/bộ, "
            "khung giá EVN 2024 là 150.000.000 VND/bộ. Chênh lệch 23.3%. "
            "50 bộ × 35.000.000 VND = tổng chênh lệch 1.750.000.000 VND."
        ),
        "status": AlertStatus.open,
    },
    {
        "doc_no": "EVNHANOI-XL-2024-015",
        "title": "Tiến độ thi công trạm 110kV Tây Hồ có nguy cơ trễ 45 ngày",
        "severity": "medium",
        "source": "ScheduleValidator",
        "description": (
            "Hồ sơ EVNHANOI-XL-2024-015: Kế hoạch hoàn thành Q4/2024 không khả thi do "
            "phụ thuộc vào tiến độ giải phóng mặt bằng (dự kiến chậm 45 ngày). "
            "Khuyến nghị: cập nhật tiến độ hợp đồng hoặc phân kỳ thi công."
        ),
        "status": AlertStatus.open,
    },
    {
        "doc_no": "EVNHANOI-CAP-2024-033",
        "title": "Hồ sơ thiếu bản vẽ thiết kế kỹ thuật hệ thống cáp ngầm",
        "severity": "medium",
        "source": "LegalGraphRAG",
        "description": (
            "Hồ sơ EVNHANOI-CAP-2024-033: Chưa đính kèm bản vẽ thiết kế kỹ thuật hệ thống "
            "cáp ngầm theo TCVN 9208:2012. Cần bổ sung: mặt cắt tuyến cáp, bản vẽ hố đấu nối, "
            "sơ đồ đơn tuyến trước khi trình HĐTV."
        ),
        "status": AlertStatus.open,
    },
    {
        "doc_no": "EVNHANOI-TU-2024-028",
        "title": "Chỉ có 1 nhà thầu nộp hồ sơ — không đảm bảo tính cạnh tranh",
        "severity": "medium",
        "source": "ProcurementAudit",
        "description": (
            "Hồ sơ EVNHANOI-TU-2024-028: Chỉ có 1/3 nhà thầu đủ điều kiện nộp hồ sơ dự thầu. "
            "Theo Điều 38 Luật Đấu thầu 2023, cần tối thiểu 3 hồ sơ hợp lệ. "
            "Đã phát hành thông báo mời thầu lần 2 — đang chờ kết quả."
        ),
        "status": AlertStatus.resolved,
    },
    {
        "doc_no": "EVNHANOI-BT-2024-009",
        "title": "Phần mềm DIGSI 5 chưa có hợp đồng bản quyền phù hợp",
        "severity": "medium",
        "source": "LegalGraphRAG",
        "description": (
            "Hồ sơ EVNHANOI-BT-2024-009: Hợp đồng bản quyền DIGSI 5 (Siemens) đang ở gói "
            "Single-user nhưng sẽ dùng cho 5 kỹ sư. Cần nâng cấp lên Multi-user license "
            "hoặc Site license trước khi phê duyệt."
        ),
        "status": AlertStatus.open,
    },
    {
        "doc_no": "EVNHANOI-SCADA-2024-007",
        "title": "Hệ thống SCADA thẩm định hoàn tất — không phát hiện rủi ro",
        "severity": "low",
        "source": "system",
        "description": (
            "Hồ sơ EVNHANOI-SCADA-2024-007: AI thẩm định hoàn tất. "
            "Tất cả 3 kiểm tra đều pass: pháp lý ĐẠT (0.94), tài chính ĐẠT (0.91), "
            "kỹ thuật ĐẠT (0.88). Không phát hiện rủi ro. Đề nghị phê duyệt."
        ),
        "status": AlertStatus.resolved,
    },
]


async def seed_alerts(session: AsyncSession, dossier_id_map: dict[str, int]) -> None:
    """Seed alerts với dossier FK."""
    for a in ALERTS_DATA:
        doc_no = a["doc_no"]
        dossier_id = dossier_id_map.get(doc_no)

        existing = (
            await session.execute(
                select(Alert).where(Alert.description == a["description"])
            )
        ).scalar_one_or_none()

        if existing:
            logger.info("Alert already exists: %s", a["title"])
            continue

        alert = Alert(
            dossier_id=dossier_id,
            title=a["title"],
            severity=a["severity"],
            source=a["source"],
            description=a["description"],
            status=a["status"],
        )
        session.add(alert)
        logger.info("Seeded alert [%s]: %s", a["severity"], a["title"])

    await session.commit()
