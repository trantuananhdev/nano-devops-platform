"""Seed notifications — 15 thông báo cho các users.

Idempotent: skip nếu đã có bất kỳ notification nào.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Notification, NotificationType

logger = logging.getLogger(__name__)


async def seed_notifications(
    session: AsyncSession,
    user_id_map: dict[str, int],
    dossier_id_map: dict[str, int],
) -> None:
    """Seed notifications."""
    existing = (await session.execute(select(Notification))).scalars().first()
    if existing:
        logger.info("Notifications already seeded, skipping")
        return

    notifications = [
        # === Admin ===
        Notification(
            user_id=user_id_map["admin@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-UAV-198-2024"),
            type=NotificationType.appraisal_complete,
            title="Thẩm định hoàn tất: Hồ sơ UAV",
            message="Hệ thống AI đã hoàn tất thẩm định hồ sơ EVNHANOI-UAV-198-2024. Mức rủi ro: Trung bình. Cần phê duyệt.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-UAV-198-2024", "risk_level": "medium"},
        ),
        Notification(
            user_id=user_id_map["admin@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-MBA-2024-021"),
            type=NotificationType.appraisal_complete,
            title="Cảnh báo giá: Hồ sơ MBA 250kVA",
            message="AI phát hiện giá MBA vượt 23.3% khung giá EVN. Cần xem xét trước khi phê duyệt.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-MBA-2024-021", "risk_level": "high"},
        ),
        # === HDTV Leader ===
        Notification(
            user_id=user_id_map["tbich@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-SCADA-2024-007"),
            type=NotificationType.status_change,
            title="Hồ sơ SCADA đã được phê duyệt",
            message="Hồ sơ EVNHANOI-SCADA-2024-007 đã chuyển sang trạng thái 'Đã phê duyệt' bởi Phạm Văn Cường.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-SCADA-2024-007", "new_status": "approved"},
        ),
        Notification(
            user_id=user_id_map["tbich@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-XL-2024-015"),
            type=NotificationType.status_change,
            title="Hồ sơ trạm 110kV Tây Hồ chờ phê duyệt Ban",
            message="Hồ sơ EVNHANOI-XL-2024-015 đã được trình lên Ban Kỹ thuật - Sản xuất chờ phê duyệt.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-XL-2024-015", "new_status": "submitted_to_dept"},
        ),
        Notification(
            user_id=user_id_map["tbich@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-UAV-198-2024"),
            type=NotificationType.clarification_requested,
            title="AI yêu cầu làm rõ: Hồ sơ UAV",
            message="AI cần xác nhận: 'Nhà thầu DJI Enterprise Vietnam có giấy phép bay thương mại UAV tại Việt Nam không?'",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-UAV-198-2024", "clarification_id": 1},
        ),
        # === Dept Head (Cường) ===
        Notification(
            user_id=user_id_map["pvcuong@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-CAP-2024-033"),
            type=NotificationType.document_uploaded,
            title="Tài liệu mới: Hồ sơ cáp ngầm 22kV",
            message="Hồ sơ EVNHANOI-CAP-2024-033: Bùi Văn Hùng vừa upload bổ sung bản vẽ thiết kế kỹ thuật.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-CAP-2024-033", "file_name": "ban-ve-cap-ngam-22kV.pdf"},
        ),
        Notification(
            user_id=user_id_map["pvcuong@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-KT-2024-018"),
            type=NotificationType.status_change,
            title="Hồ sơ thí nghiệm KT bị từ chối",
            message="AI thẩm định từ chối hồ sơ EVNHANOI-KT-2024-018 do thiếu biên bản nghiệm thu 2023.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-KT-2024-018", "new_status": "rejected"},
        ),
        # === Dept Head (Dũng) ===
        Notification(
            user_id=user_id_map["lvdung@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-VT-2024-052"),
            type=NotificationType.status_change,
            title="Hồ sơ vật tư SCTX đã qua HĐTV xem xét",
            message="Hồ sơ EVNHANOI-VT-2024-052 đã được HĐTV xem xét. Đang chờ quyết định phê duyệt chính thức.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-VT-2024-052", "new_status": "board_reviewed"},
        ),
        # === Specialist (Phúc — chuyên viên UAV) ===
        Notification(
            user_id=user_id_map["vvphuc@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-UAV-198-2024"),
            type=NotificationType.clarification_requested,
            title="Cần làm rõ: Giấy phép bay UAV nhà thầu",
            message="AI thẩm định hồ sơ UAV cần bạn xác nhận tình trạng giấy phép bay thương mại của DJI Enterprise Vietnam.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-UAV-198-2024", "clarification_id": 1},
        ),
        Notification(
            user_id=user_id_map["vvphuc@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-UAV-198-2024"),
            type=NotificationType.appraisal_complete,
            title="Thẩm định UAV bắt đầu xử lý",
            message="Hệ thống AI đã bắt đầu thẩm định hồ sơ EVNHANOI-UAV-198-2024. Kết quả sẽ có trong 5-10 phút.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-UAV-198-2024"},
        ),
        # === Specialist (Hùng — chuyên viên đấu thầu) ===
        Notification(
            user_id=user_id_map["bvhung@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-TU-2024-028"),
            type=NotificationType.status_change,
            title="Hồ sơ tư vấn giám sát bị Ban từ chối",
            message="Hồ sơ EVNHANOI-TU-2024-028: Ban Quản lý Dự án từ chối do không đủ số nhà thầu cạnh tranh.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-TU-2024-028", "new_status": "dept_rejected"},
        ),
        Notification(
            user_id=user_id_map["bvhung@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-BT-2024-009"),
            type=NotificationType.document_uploaded,
            title="Hồ sơ bảo trì thiết bị đo đếm sẵn sàng thẩm định",
            message="Hồ sơ EVNHANOI-BT-2024-009 đã bổ sung đủ tài liệu. Sẵn sàng để AI thẩm định.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-BT-2024-009"},
        ),
        # === Specialist (Giang — tài chính) ===
        Notification(
            user_id=user_id_map["dtgiang@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-MBA-2024-021"),
            type=NotificationType.appraisal_complete,
            title="Cảnh báo tài chính: Hồ sơ MBA vượt ngân sách",
            message="AI phát hiện đơn giá MBA ABB vượt 23.3% khung giá EVN. Tổng chênh lệch: 1.750.000.000 VND.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-MBA-2024-021", "budget_overrun": "23.3%"},
        ),
        # === Specialist (Em — pháp chế) ===
        Notification(
            user_id=user_id_map["htem@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-UAV-198-2024"),
            type=NotificationType.status_change,
            title="Hồ sơ UAV bắt đầu thẩm định",
            message="Hồ sơ EVNHANOI-UAV-198-2024 vừa chuyển sang trạng thái 'Đang thẩm định'. Đợi kết quả AI.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-UAV-198-2024", "new_status": "appraising"},
        ),
        Notification(
            user_id=user_id_map["htem@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-NL-2024-061"),
            type=NotificationType.status_change,
            title="Hồ sơ Smart Grid cần chỉnh sửa",
            message="Hồ sơ EVNHANOI-NL-2024-061 được trả về để bổ sung điều khoản bảo mật dữ liệu lưới điện.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-NL-2024-061", "new_status": "needs_revision"},
        ),
    ]

    for notif in notifications:
        session.add(notif)

    await session.commit()
    logger.info("Seeded %d notifications", len(notifications))
