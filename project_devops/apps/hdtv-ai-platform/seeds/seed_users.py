"""Seed users — 8 nhan vien EVN Ha Noi thuc te tu ho so 198/TTr-EVNHANOI.

Idempotent: kiem tra email truoc khi insert.
Password mac dinh: EVN@2024! (bcrypt hashed)
"""
import logging
import bcrypt as _bcrypt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User, UserRole

logger = logging.getLogger(__name__)

DEFAULT_PASSWORD = "EVN@2024!"

# Nguoi dung thuc te tu To trinh 198/TTr-EVNHANOI, 07/KT, Bao cao tham tra va Phieu trinh HDTV
USERS_DATA = [
    {
        "name": "Nguyen Danh Duyen",
        "email": "admin@evnhanoi.vn",
        "role": UserRole.admin,
        # Chu tich HDTV EVNHANOI — ky ban hanh Nghi quyet (Phieu trinh 10/02/2025)
    },
    {
        "name": "Do Tuan Anh",
        "email": "dtanh@evnhanoi.vn",
        "role": UserRole.hdtv_leader,
        # Thanh vien HDTV — ky dong y Phieu trinh (vi tri 1/5)
    },
    {
        "name": "Doan Duc Tien",
        "email": "ddtien@evnhanoi.vn",
        "role": UserRole.dept_head,
        # Truong Ban Tong hop — ky Bao cao tham tra ngay 24/01/2025
    },
    {
        "name": "Nguyen Anh Dung",
        "email": "nadung@evnhanoi.vn",
        "role": UserRole.dept_head,
        # Pho TGD Ky thuat — ky phe duyet To trinh 07/KT ngay 07/01/2025
    },
    {
        "name": "Ha Tuan Minh",
        "email": "htminh@evnhanoi.vn",
        "role": UserRole.specialist,
        # Can bo thu ly Ban Tong hop — nguoi tham tra ho so 198/TTr-EVNHANOI
    },
    {
        "name": "Dao Ngoc Chung",
        "email": "dnchung@evnhanoi.vn",
        "role": UserRole.specialist,
        # KT. Pho Truong Ban Ky thuat — soan va ky To trinh 07/KT ngay 07/01/2025
    },
    {
        "name": "Tran Van Thuong",
        "email": "tvthuong@evnhanoi.vn",
        "role": UserRole.specialist,
        # Thanh vien HDTV — ky dong y Phieu trinh (vi tri 3/5)
    },
    {
        "name": "Pham Dai Nghia",
        "email": "pdnghia@evnhanoi.vn",
        "role": UserRole.specialist,
        # Thanh vien HDTV — ky dong y Phieu trinh (vi tri 4/5)
    },
]


async def seed_users(session: AsyncSession) -> dict[str, int]:
    """Seed users, return email to id map."""
    pw_bytes = DEFAULT_PASSWORD.encode("utf-8")
    hashed_pw = _bcrypt.hashpw(pw_bytes, _bcrypt.gensalt(rounds=12)).decode("utf-8")
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
