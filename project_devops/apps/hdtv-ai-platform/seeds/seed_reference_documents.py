"""Seed reference documents cho hồ sơ UAV 198/TTr-EVNHANOI.

Phản ánh đúng các file thật người dùng đã upload từ:
  data/seed/dossier_198_uav/

Idempotent: kiểm tra dossier_id + file_name trước khi insert.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ReferenceDocument

logger = logging.getLogger(__name__)

# Ánh xạ file thật → metadata seed (file_key là path trong MinIO bucket hdtv-docs)
_UAV_DOCS = [
    {
        "file_name": "02. Tờ trình xin duyệt HĐTV (B4 ký TGĐ trình HĐTV).pdf",
        "file_key":  "dossiers/uav-198/02-to-trinh-xin-duyet-HDTV.pdf",
        "file_size": 1_240_000,
        "content_type": "application/pdf",
    },
    {
        "file_name": "03. Báo cáo thẩm tra.pdf",
        "file_key":  "dossiers/uav-198/03-bao-cao-tham-tra.pdf",
        "file_size": 890_000,
        "content_type": "application/pdf",
    },
    {
        "file_name": "03. Phiếu trình.pdf",
        "file_key":  "dossiers/uav-198/03-phieu-trinh.pdf",
        "file_size": 320_000,
        "content_type": "application/pdf",
    },
    {
        "file_name": "Ý kiến góp ý của máy bay không người lái của tư vấn ngoài.pdf",
        "file_key":  "dossiers/uav-198/y-kien-tu-van-ngoai-1.pdf",
        "file_size": 560_000,
        "content_type": "application/pdf",
    },
    {
        "file_name": "Ý kiến góp ý của máy bay không người lái của tư vấn ngoài 2.pdf",
        "file_key":  "dossiers/uav-198/y-kien-tu-van-ngoai-2.pdf",
        "file_size": 480_000,
        "content_type": "application/pdf",
    },
    {
        "file_name": "Tờ trình B4 trình PTGĐ.pdf",
        "file_key":  "dossiers/uav-198/to-trinh-B4-trinh-PTGD.pdf",
        "file_size": 210_000,
        "content_type": "application/pdf",
    },
    {
        "file_name": "Tiêu chí kỹ thuật so sánh 3 sản phẩm final.xlsx",
        "file_key":  "dossiers/uav-198/tieu-chi-ky-thuat-3-san-pham.xlsx",
        "file_size": 95_000,
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    },
    {
        "file_name": "BC góp ý các nhà cung cấp.xlsx",
        "file_key":  "dossiers/uav-198/bc-gop-y-nha-cung-cap.xlsx",
        "file_size": 72_000,
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    },
    {
        "file_name": "QĐ giao danh mục MSTS X06 2024.pdf",
        "file_key":  "dossiers/uav-198/can-cu/QD-8594-giao-danh-muc-MSTS-X06-2024.pdf",
        "file_size": 430_000,
        "content_type": "application/pdf",
    },
]


async def seed_reference_documents(
    session: AsyncSession,
    dossier_id_map: dict[str, int],
    uploader_id: int = 1,
) -> None:
    """Seed reference documents cho hồ sơ UAV. uploader_id mặc định là admin (id=1)."""
    uav_dossier_id = dossier_id_map.get("198/TTr-EVNHANOI")
    if not uav_dossier_id:
        logger.warning("Dossier 198/TTr-EVNHANOI không tồn tại, bỏ qua seed reference_documents")
        return

    for doc in _UAV_DOCS:
        existing = (
            await session.execute(
                select(ReferenceDocument).where(
                    ReferenceDocument.dossier_id == uav_dossier_id,
                    ReferenceDocument.file_name == doc["file_name"],
                )
            )
        ).scalar_one_or_none()

        if existing:
            logger.info("ReferenceDocument already exists: %s", doc["file_name"])
            continue

        row = ReferenceDocument(
            dossier_id=uav_dossier_id,
            file_name=doc["file_name"],
            file_key=doc["file_key"],
            file_size=doc["file_size"],
            content_type=doc["content_type"],
            uploaded_by=uploader_id,
        )
        session.add(row)
        logger.info("Seeded reference doc: %s", doc["file_name"])

    await session.commit()
    logger.info("Seeded %d reference documents cho UAV 198/TTr-EVNHANOI", len(_UAV_DOCS))
