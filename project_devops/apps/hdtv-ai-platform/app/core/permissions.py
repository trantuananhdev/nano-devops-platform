"""Role-based permission checking utilities for HDTV AI Platform."""

from enum import Enum
from typing import Any, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.entities import User, UserRole

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: verify JWT and return the current User.

    Raises HTTP 401 if token is missing or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token xác thực không tồn tại",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: int | None = int(payload.get("sub", 0)) or None
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token lỗi")

    user = (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại")

    return user


def require_roles(allowed_roles: list[UserRole]) -> Callable[..., Any]:
    """Dependency factory: require current user to have one of the allowed roles."""

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền hạn không đủ. Cần role: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return dependency


# Permission helpers — dùng trong service/router để kiểm tra logic

def is_allowed_to_create_dossier(user_role: UserRole) -> bool:
    return user_role in [UserRole.specialist, UserRole.dept_head, UserRole.admin]


def is_allowed_to_submit_to_dept(user_role: UserRole) -> bool:
    return user_role in [UserRole.specialist, UserRole.dept_head, UserRole.admin]


def is_allowed_to_approve_dept(user_role: UserRole) -> bool:
    return user_role in [UserRole.dept_head, UserRole.admin]


def is_allowed_to_submit_to_board(user_role: UserRole) -> bool:
    return user_role in [UserRole.dept_head, UserRole.admin]


def is_allowed_to_appraise(user_role: UserRole) -> bool:
    return user_role in [UserRole.specialist, UserRole.dept_head, UserRole.hdtv_leader, UserRole.admin]


def is_allowed_to_approve_final(user_role: UserRole) -> bool:
    return user_role in [UserRole.hdtv_leader, UserRole.admin]


def is_allowed_to_view_admin(user_role: UserRole) -> bool:
    return user_role in [UserRole.admin]
