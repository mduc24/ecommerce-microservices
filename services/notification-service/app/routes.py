"""
API routes for notification service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Notification
from app.schemas import NotificationResponse, NotificationListResponse
from app.services.email_service import send_email

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    recipient: str | None = Query(None),
    status: str | None = Query(None),
    order_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification)
    count_query = select(func.count(Notification.id))

    if recipient:
        query = query.where(Notification.recipient_email == recipient)
        count_query = count_query.where(Notification.recipient_email == recipient)
    if status:
        query = query.where(Notification.status == status)
        count_query = count_query.where(Notification.status == status)
    if order_id:
        query = query.where(Notification.order_id == order_id)
        count_query = count_query.where(Notification.order_id == order_id)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    results = await db.execute(
        query.order_by(Notification.id.desc()).offset(offset).limit(page_size)
    )
    notifications = results.scalars().all()

    return NotificationListResponse(notifications=notifications, total=total)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/retry/{notification_id}", response_model=NotificationResponse)
async def retry_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed notifications can be retried")

    # Determine template based on notification type
    template_map = {
        "order_confirmation": "order_confirmation.html",
        "order_status_update": "order_status_update.html",
    }
    template_name = template_map.get(notification.type)
    if not template_name:
        raise HTTPException(status_code=400, detail="Unknown notification type")

    # Re-send email
    email_result = await send_email(
        to=notification.recipient_email,
        subject=notification.subject,
        template_name=template_name,
        context={
            "user_email": notification.recipient_email,
            "order_id": notification.order_id or 0,
            "total_amount": 0,
            "items": [],
            "old_status": "",
            "new_status": "",
        },
    )

    notification.status = email_result["status"]
    notification.error_message = email_result.get("error_message")
    await db.commit()
    await db.refresh(notification)

    return notification
