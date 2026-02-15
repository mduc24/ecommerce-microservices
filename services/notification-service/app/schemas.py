"""
Pydantic schemas for notification service.
"""

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Response schema for a notification record."""

    id: int
    type: str
    recipient_email: str
    subject: str
    order_id: int | None
    user_id: int | None
    status: str
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response schema for listing notifications."""

    notifications: list[NotificationResponse]
    total: int
