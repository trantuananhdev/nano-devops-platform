"""Seed users — 8 nhân viên EVN Hà Nội với 4 roles.

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

USERS_DATA = [
    {
        "name": "Nguyễn Văn An",
        "email": "admin@evnhanoi.vn",
        "role": UserRole.admin,
    },
    {
        "name": "Trần Thị Bích",
        "email": "tbich@evnhanoi.vn",
        "role": UserRole.hdtv_leader,
    },
    {
        "name": "Phạm Văn Cường",
        "email": "pvcuong@evnhanoi.vn",
        "role": UserRole.dept_head,
    },
    {
        "name": "Lê Văn Dũng",
        "email": "lvdung@evnhanoi.vn",
        "role": UserRole.dept_head,
    },
    {
        "name": "Hoàng Thị Em",
        "email": "htem@evnhanoi.vn",
        "role": UserRole.specialist,
    },
    {
        "name": "Vũ Văn Phúc",
        "email": "vvphuc@evnhanoi.vn",
        "role": UserRole.specialist,
    },
    {
        "name": "Đỗ Thị Giang",
        "email": "dtgiang@evnhanoi.vn",
        "role": UserRole.specialist,
    },
    {
        "name": "Bùi Văn Hùng",
        "email": "bvhung@evnhanoi.vn",
        "role": UserRole.specialist,
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
            # Update password_hash nếu chưa có
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
