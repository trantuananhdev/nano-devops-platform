"""Role-based permission checking utilities for HDTV AI Platform."""

from enum import Enum
from typing import Any, Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import User, UserRole


def require_roles(allowed_roles: list[UserRole]) -> Callable[..., Any]:
    """
    Dependency that requires the current user to have one of the allowed roles.
    
    NOTE: In a real system, this would get the current user from authentication.
    For now, we'll just check role existence (placeholder).
    """
    async def dependency(
        # TODO: In real auth, we'd have a get_current_user dependency here
        session: AsyncSession = Depends(get_db),
    ) -> None:
        # Placeholder: For now, we'll just verify roles exist in the system
        # In real use, this would check the current authenticated user's role
        pass

    return dependency


def is_allowed_to_create_dossier(user_role: UserRole) -> bool:
    """Check if a user is allowed to create a dossier."""
    return user_role in [
        UserRole.specialist,
        UserRole.dept_head,
        UserRole.admin,
    ]


def is_allowed_to_submit_to_dept(user_role: UserRole) -> bool:
    """Check if a user is allowed to submit a dossier to the department head."""
    return user_role in [
        UserRole.specialist,
        UserRole.dept_head,
        UserRole.admin,
    ]


def is_allowed_to_approve_dept(user_role: UserRole) -> bool:
    """Check if a user is allowed to approve a dossier as department head."""
    return user_role in [
        UserRole.dept_head,
        UserRole.admin,
    ]


def is_allowed_to_submit_to_board(user_role: UserRole) -> bool:
    """Check if a user is allowed to submit a dossier to the board."""
    return user_role in [
        UserRole.dept_head,
        UserRole.admin,
    ]


def is_allowed_to_appraise(user_role: UserRole) -> bool:
    """Check if a user is allowed to start an AI appraisal."""
    return user_role in [
        UserRole.specialist,
        UserRole.dept_head,
        UserRole.hdtv_leader,
        UserRole.admin,
    ]


def is_allowed_to_approve_final(user_role: UserRole) -> bool:
    """Check if a user is allowed to give final approval."""
    return user_role in [
        UserRole.hdtv_leader,
        UserRole.admin,
    ]


def is_allowed_to_view_admin(user_role: UserRole) -> bool:
    """Check if a user is allowed to view the admin panel."""
    return user_role in [
        UserRole.admin,
    ]
