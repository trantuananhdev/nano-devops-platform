from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any

from app.models.entities import Notification, NotificationType, User, UserRole


async def create_notification(
    session: AsyncSession,
    user_id: int,
    type: NotificationType,
    title: str,
    message: str,
    dossier_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        dossier_id=dossier_id,
        metadata=metadata or {},
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification


async def get_user_notifications(
    session: AsyncSession,
    user_id: int,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Notification], int, int]:
    # Get total count
    total_result = await session.execute(
        select(func.count(Notification.id)).where(Notification.user_id == user_id)
    )
    total = total_result.scalar_one()
    
    # Get unread count
    unread_result = await session.execute(
        select(func.count(Notification.id)).where(
            (Notification.user_id == user_id) & (Notification.is_read == False)
        )
    )
    unread_count = unread_result.scalar_one()
    
    # Get paginated notifications
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(result.scalars().all())
    
    return items, total, unread_count


async def get_notification(session: AsyncSession, notification_id: int) -> Notification | None:
    result = await session.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    return result.scalar_one_or_none()


async def mark_notification_read(
    session: AsyncSession,
    notification_id: int,
    is_read: bool = True,
) -> Notification | None:
    notification = await get_notification(session, notification_id)
    if notification:
        notification.is_read = is_read
        await session.commit()
        await session.refresh(notification)
    return notification


async def mark_all_user_notifications_read(
    session: AsyncSession,
    user_id: int,
) -> int:
    from sqlalchemy import update
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)
        .values(is_read=True)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


async def notify_on_status_change(
    session: AsyncSession,
    dossier_id: int,
    old_status: str,
    new_status: str,
    changed_by: int | None = None,
) -> None:
    # Get users to notify based on status
    users_to_notify = []
    
    if new_status == "submitted_to_dept":
        # Notify dept heads
        result = await session.execute(
            select(User).where(User.role == UserRole.dept_head)
        )
        users_to_notify = list(result.scalars().all())
    elif new_status in ["dept_approved", "dept_rejected"]:
        # Notify specialist and hdtv leaders
        result = await session.execute(
            select(User).where(
                (User.role == UserRole.specialist) | (User.role == UserRole.hdtv_leader)
            )
        )
        users_to_notify = list(result.scalars().all())
    elif new_status == "submitted_to_board":
        # Notify hdtv leaders
        result = await session.execute(
            select(User).where(User.role == UserRole.hdtv_leader)
        )
        users_to_notify = list(result.scalars().all())
    elif new_status in ["approved", "rejected"]:
        # Notify all active users
        result = await session.execute(
            select(User).where(User.is_active == True)
        )
        users_to_notify = list(result.scalars().all())
    
    # Create notifications
    for user in users_to_notify:
        await create_notification(
            session=session,
            user_id=user.id,
            type=NotificationType.status_change,
            title="Cập nhật trạng thái tờ trình",
            message=f"Tờ trình {dossier_id} thay đổi trạng thái từ {old_status} sang {new_status}",
            dossier_id=dossier_id,
            metadata={"old_status": old_status, "new_status": new_status, "changed_by": changed_by},
        )
