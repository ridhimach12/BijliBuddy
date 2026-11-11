"""Notification helper service."""

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Notification


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notif_type: str = "booking_update",
    related_booking_id: Optional[int] = None,
) -> Notification:
    """Persist an in-app notification for a user."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        related_booking_id=related_booking_id,
        is_read=False,
    )
    db.add(notif)
    return notif
