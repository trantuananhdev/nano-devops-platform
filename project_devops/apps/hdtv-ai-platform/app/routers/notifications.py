from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import NotificationType
from app.schemas.dossier import (
    NotificationCreate,
    NotificationOut,
    NotificationMarkRead,
    NotificationPage,
)
from app.services.notification_service import (
    create_notification,
    get_user_notifications,
    get_notification,
    mark_notification_read,
    mark_all_user_notifications_read,
)


router = APIRouter()


@router.get("/user/{user_id}", response_model=NotificationPage)
async def get_user_notifications_endpoint(
    user_id: int,
    offset: int = Query(default=0, ge=0, description="Skip N rows"),
    limit: int = Query(default=20, ge=1, le=200, description="Max rows (default 20, max 200)"),
    session: AsyncSession = Depends(get_db),
) -> NotificationPage:
    """Get paginated list of notifications for a user, ordered by most recent first."""
    items, total, unread_count = await get_user_notifications(
        session=session,
        user_id=user_id,
        offset=offset,
        limit=limit,
    )
    return NotificationPage(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + len(items)) < total,
        unread_count=unread_count,
    )


@router.get("/{notification_id}", response_model=NotificationOut)
async def get_single_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_db),
) -> NotificationOut:
    """Get a single notification by ID."""
    notification = await get_notification(session, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationOut.model_validate(notification)


@router.patch("/{notification_id}", response_model=NotificationOut)
async def mark_notification_read_endpoint(
    notification_id: int,
    body: NotificationMarkRead = NotificationMarkRead(),
    session: AsyncSession = Depends(get_db),
) -> NotificationOut:
    """Mark a notification as read (or unread)."""
    notification = await mark_notification_read(
        session=session,
        notification_id=notification_id,
        is_read=body.is_read,
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationOut.model_validate(notification)


@router.patch("/user/{user_id}/mark-all-read", response_model=dict)
async def mark_all_notifications_read_endpoint(
    user_id: int,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Mark all notifications for a user as read."""
    count = await mark_all_user_notifications_read(session=session, user_id=user_id)
    return {"marked_count": count}


@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
async def create_new_notification(
    body: NotificationCreate,
    session: AsyncSession = Depends(get_db),
) -> NotificationOut:
    """Create a new notification (for internal use)."""
    try:
        notification_type = NotificationType(body.type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    notification = await create_notification(
        session=session,
        user_id=body.user_id,
        type=notification_type,
        title=body.title,
        message=body.message,
        dossier_id=body.dossier_id,
        extra_data=body.extra_data,
    )
    return NotificationOut.model_validate(notification)
