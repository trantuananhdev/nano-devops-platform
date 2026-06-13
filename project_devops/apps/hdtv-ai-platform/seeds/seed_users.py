"""Seed users — 8 nhân viên EVN Hà Nội thực tế từ hồ sơ 198/TTr-EVNHANOI.

Idempotent: kiểm tra email trước khi insert.
Password mặc định: EVN@2024! (bcrypt hashed)
"""
import logging

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, UserRole

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD = "EVN@2024!"

# Người dùng thực tế từ Tờ trình 198/TTr-EVNHANOI, 07/KT, Báo cáo thẩm tra và Phiếu trình HĐTV
USERS_DATA = [
    {
        "name": "Nguyễn Danh Duyên",
        "email": "admin@evnhanoi.vn",
        "role": UserRole.admin,
        # Chủ tịch HĐTV EVNHANOI — ký ban hành Nghị quyết (Phiếu trình 10/02/2025)
    },
    {
        "name": "Đỗ Tuấn Anh",
        "email": "dtanh@evnhanoi.vn",
        "role": UserRole.hdtv_leader,
        # Thành viên HĐTV — ký đồng ý Phiếu trình (vị trí 1/5)
    },
    {
        "name": "Đoàn Đức Tiến",
        "email": "ddtien@evnhanoi.vn",
        "role": UserRole.dept_head,
        # Trưởng Ban Tổng hợp — ký Báo cáo thẩm tra ngày 24/01/2025
    },
    {
        "name": "Nguyễn Anh Dũng",
        "email": "nadung@evnhanoi.vn",
        "role": UserRole.dept_head,
        # Phó TGĐ Kỹ thuật — ký phê duyệt Tờ trình 07/KT ngày 07/01/2025
    },
    {
        "name": "Hà Tuấn Minh",
        "email": "htminh@evnhanoi.vn",
        "role": UserRole.specialist,
        # Cán bộ thụ lý Ban Tổng hợp — người thẩm tra hồ sơ 198/TTr-EVNHANOI
    },
    {
        "name": "Đào Ngọc Chung",
        "email": "dnchung@evnhanoi.vn",
        "role": UserRole.specialist,
        # KT. Phó Trưởng Ban Kỹ thuật — soạn và ký Tờ trình 07/KT ngày 07/01/2025
    },
    {
        "name": "Trần Văn Thương",
        "email": "tvthuong@evnhanoi.vn",
        "role": UserRole.specialist,
        # Thành viên HĐTV — ký đồng ý Phiếu trình (vị trí 3/5)
    },
    {
        "name": "Phạm Đại Nghĩa",
        "email": "pdnghia@evnhanoi.vn",
        "role": UserRole.specialist,
        # Thành viên HĐTV — ký đồng ý Phiếu trình (vị trí 4/5)
    },
]


async def seed_users(session: AsyncSession) -> dict[str, int]:
    """Seed users, return email→id map."""
    hashed_pw = pwd_context.hash(DEFAULT_PASSWORD)
    id_map: dict[str, int] = {}

    for u in USERS_DATA:
        existing = (
            await session.execute(select(User).where(User.email == u["email"]))
        ).scalar_one_or_none()

        if existing:
            if not existing.password_hash:
                existing.password_hash = hashed_pw
                await session.flush()
            id_map[u["email"]] = existing.id
            logger.info("User already exists: %s", u["email"])
            continue

        user = User(
            name=u["name"],
            email=u["email"],
            role=u["role"],
            password_hash=hashed_pw,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        id_map[u["email"]] = user.id
        logger.info("Seeded user: %s (%s)", u["name"], u["role"].value)

    await session.commit()
    return id_map
