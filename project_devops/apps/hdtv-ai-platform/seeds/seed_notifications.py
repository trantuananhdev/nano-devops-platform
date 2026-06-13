"""Seed notifications — 15 thông báo cho các users.

Dùng emails của người dùng thực tế từ hồ sơ 198/TTr-EVNHANOI.
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
        # === Chủ tịch HĐTV (Nguyễn Danh Duyên — admin) ===
        Notification(
            user_id=user_id_map["admin@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.appraisal_complete,
            title="AI thẩm định xong: Tờ trình 198/TTr-EVNHANOI",
            message=(
                "AI đã hoàn tất thẩm định Tờ trình 198/TTr-EVNHANOI (Phê duyệt TCKT UAV). "
                "Mức rủi ro: Trung bình. Có 2 kiến nghị hiệu chỉnh nhỏ. Đề nghị HĐTV thông qua."
            ),
            is_read=False,
            extra_data={"doc_no": "198/TTr-EVNHANOI", "risk_level": "medium"},
        ),
        Notification(
            user_id=user_id_map["admin@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-MBA-2024-021"),
            type=NotificationType.appraisal_complete,
            title="Cảnh báo giá: Hồ sơ MBA 250kVA vượt ngân sách",
            message="AI phát hiện giá MBA ABB vượt 23.3% khung giá EVN. Tổng chênh lệch: 1.750.000.000 VND.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-MBA-2024-021", "risk_level": "high"},
        ),
        # === Thành viên HĐTV (Đỗ Tuấn Anh — hdtv_leader) ===
        Notification(
            user_id=user_id_map["dtanh@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.status_change,
            title="Phiếu trình HĐTV: Tờ trình 198/TTr-EVNHANOI chờ biểu quyết",
            message=(
                "Ban Tổng hợp đã hoàn thành thẩm tra Tờ trình 198/TTr-EVNHANOI và trình Phiếu lên "
                "HĐTV. Đề nghị các thành viên HĐTV xem xét và ký đồng ý."
            ),
            is_read=False,
            extra_data={"doc_no": "198/TTr-EVNHANOI", "new_status": "submitted_to_board"},
        ),
        Notification(
            user_id=user_id_map["dtanh@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-SCADA-2024-007"),
            type=NotificationType.status_change,
            title="Hồ sơ SCADA/DMS đã được phê duyệt",
            message="Hồ sơ EVNHANOI-SCADA-2024-007 chuyển sang 'Đã phê duyệt'. AI thẩm định không phát hiện rủi ro.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-SCADA-2024-007", "new_status": "approved"},
        ),
        # === Trưởng Ban Tổng hợp (Đoàn Đức Tiến — dept_head) ===
        Notification(
            user_id=user_id_map["ddtien@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.document_uploaded,
            title="Tờ trình 198/TTr-EVNHANOI cần thẩm tra",
            message=(
                "TGĐ Nguyễn Anh Tuấn đã ký Tờ trình 198/TTr-EVNHANOI và chuyển Ban Tổng hợp "
                "thẩm tra. Người thụ lý: Hà Tuấn Minh. Hạn thẩm tra theo quy định."
            ),
            is_read=True,
            extra_data={"doc_no": "198/TTr-EVNHANOI", "file_name": "198-TTr-EVNHANOI.pdf"},
        ),
        Notification(
            user_id=user_id_map["ddtien@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-CAP-2024-033"),
            type=NotificationType.document_uploaded,
            title="Tài liệu mới: Hồ sơ cáp ngầm 22kV bổ sung bản vẽ",
            message="Hồ sơ EVNHANOI-CAP-2024-033: Đã upload bổ sung bản vẽ thiết kế kỹ thuật hệ thống cáp ngầm.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-CAP-2024-033", "file_name": "ban-ve-cap-ngam-22kV.pdf"},
        ),
        # === Phó TGĐ KT (Nguyễn Anh Dũng — dept_head) ===
        Notification(
            user_id=user_id_map["nadung@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.status_change,
            title="Tờ trình 07/KT đã được phê duyệt và trình TGĐ",
            message=(
                "Tờ trình 07/KT (Ban Kỹ thuật, 07/01/2025) đã được PTGĐ Kỹ thuật ký phê duyệt "
                "và chuyển TGĐ ký Tờ trình 198/TTr-EVNHANOI trình HĐTV."
            ),
            is_read=True,
            extra_data={"doc_no": "198/TTr-EVNHANOI", "new_status": "dept_approved"},
        ),
        Notification(
            user_id=user_id_map["nadung@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-KT-2024-018"),
            type=NotificationType.status_change,
            title="Hồ sơ thí nghiệm KT bị từ chối — thiếu tài liệu",
            message="AI thẩm định từ chối EVNHANOI-KT-2024-018 do thiếu biên bản nghiệm thu 2023.",
            is_read=True,
            extra_data={"doc_no": "EVNHANOI-KT-2024-018", "new_status": "rejected"},
        ),
        # === Cán bộ thụ lý Ban TH (Hà Tuấn Minh — specialist) ===
        Notification(
            user_id=user_id_map["htminh@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.clarification_requested,
            title="AI cần làm rõ: Chứng nhận xuất xứ UAV",
            message=(
                "AI thẩm định Tờ trình 198/TTr-EVNHANOI cần xác nhận: "
                "Yêu cầu 'Nhà sản xuất có chứng nhận ISO' có bao gồm chứng nhận xuất xứ Việt Nam không?"
            ),
            is_read=False,
            extra_data={"doc_no": "198/TTr-EVNHANOI", "clarification_id": 1},
        ),
        Notification(
            user_id=user_id_map["htminh@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.appraisal_complete,
            title="Thẩm tra 198/TTr-EVNHANOI hoàn tất — đề nghị HĐTV thông qua",
            message=(
                "Báo cáo thẩm tra Tờ trình 198/TTr-EVNHANOI đã hoàn tất (24/01/2025). "
                "Kết luận: Đề nghị HĐTV thông qua, có 2 kiến nghị hiệu chỉnh nhỏ."
            ),
            is_read=True,
            extra_data={"doc_no": "198/TTr-EVNHANOI"},
        ),
        # === Ban KT (Đào Ngọc Chung — specialist) ===
        Notification(
            user_id=user_id_map["dnchung@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.status_change,
            title="Tờ trình 198/TTr-EVNHANOI đang thẩm định AI",
            message=(
                "Tờ trình 198/TTr-EVNHANOI vừa chuyển sang trạng thái 'Đang thẩm định'. "
                "Hệ thống AI đang phân tích tiêu chuẩn kỹ thuật UAV. Kết quả dự kiến trong vài phút."
            ),
            is_read=True,
            extra_data={"doc_no": "198/TTr-EVNHANOI", "new_status": "appraising"},
        ),
        Notification(
            user_id=user_id_map["dnchung@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.appraisal_complete,
            title="AI phát hiện 2 điểm cần hiệu chỉnh trong TCKT UAV",
            message=(
                "AI đề nghị Ban Kỹ thuật hiệu chỉnh: (1) Thống nhất thuật ngữ 'thiết bị bay'/'máy bay'; "
                "(2) Loại bỏ cụm từ 'Nhà thầu', 'Hồ sơ dự thầu' khỏi Tiêu chuẩn kỹ thuật."
            ),
            is_read=False,
            extra_data={"doc_no": "198/TTr-EVNHANOI", "issues": 2},
        ),
        # === Thành viên HĐTV (Trần Văn Thương — specialist) ===
        Notification(
            user_id=user_id_map["tvthuong@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("198/TTr-EVNHANOI"),
            type=NotificationType.status_change,
            title="Phiếu trình UAV cần ý kiến thành viên HĐTV",
            message=(
                "Ban Tổng hợp đã lập Phiếu trình Chủ tịch HĐTV về Tờ trình 198/TTr-EVNHANOI. "
                "Đề nghị thành viên HĐTV ký đồng ý theo quy trình (10/02/2025)."
            ),
            is_read=False,
            extra_data={"doc_no": "198/TTr-EVNHANOI", "new_status": "submitted_to_board"},
        ),
        # === Thành viên HĐTV (Phạm Đại Nghĩa — specialist) ===
        Notification(
            user_id=user_id_map["pdnghia@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-VT-2024-052"),
            type=NotificationType.status_change,
            title="Hồ sơ vật tư SCTX đã qua HĐTV xem xét",
            message="Hồ sơ EVNHANOI-VT-2024-052 đã được HĐTV xem xét. Đang chờ quyết định phê duyệt chính thức.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-VT-2024-052", "new_status": "board_reviewed"},
        ),
        Notification(
            user_id=user_id_map["pdnghia@evnhanoi.vn"],
            dossier_id=dossier_id_map.get("EVNHANOI-NL-2024-061"),
            type=NotificationType.status_change,
            title="Hồ sơ Smart Grid cần chỉnh sửa bổ sung",
            message="Hồ sơ EVNHANOI-NL-2024-061 được trả về để bổ sung điều khoản bảo mật dữ liệu lưới điện.",
            is_read=False,
            extra_data={"doc_no": "EVNHANOI-NL-2024-061", "new_status": "needs_revision"},
        ),
    ]

    for notif in notifications:
        session.add(notif)

    await session.commit()
    logger.info("Seeded %d notifications", len(notifications))
