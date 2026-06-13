"""Seed alerts — 8 cảnh báo từ hồ sơ UAV và các hồ sơ khác.

Idempotent: kiểm tra description trước khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Alert, AlertStatus

logger = logging.getLogger(__name__)

ALERTS_DATA = [
    {
        "doc_no": "EVNHANOI-UAV-198-2024",
        "title": "Giá đề xuất UAV vượt 18% so với tham chiếu thị trường",
        "severity": "high",
        "source": "ErpInventoryCheck",
        "description": (
            "Hồ sơ EVNHANOI-UAV-198-2024: Giá DJI Matrice 300 RTK đề xuất 485.000.000 VND/bộ, "
            "tham chiếu thị trường Q3/2024 là 411.000.000 VND/bộ (chênh lệch 18%). "
            "Tổng chênh lệch: 222.000.000 VND cho 3 bộ. Cần giải trình hoặc đàm phán lại."
        ),
        "status": AlertStatus.open,
    },
    {
        "doc_no": "EVNHANOI-UAV-198-2024",
        "title": "Nhà thầu chưa cung cấp ISO 9001:2015 phiên bản mới nhất",
        "severity": "high",
        "source": "LegalGraphRAG",
        "description": (
            "Hồ sơ EVNHANOI-UAV-198-2024: Công ty CP Công nghệ Thiên Vũ đính kèm chứng chỉ "
            "ISO 9001:2008 (đã hết hiệu lực từ 2018). Theo Điều 12 Nghị định 24/2024/NĐ-CP, "
            "cần chứng chỉ còn hiệu lực tối thiểu 6 tháng từ ngày nộp hồ sơ."
        ),
        "status": AlertStatus.open,
    },
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
