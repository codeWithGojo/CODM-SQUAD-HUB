from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.communication import Notification
from app.models.enums import NotificationType


def create_notification(
    db: Session,
    *,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    title: str,
    body: str,
    action_url: str | None = None,
    data: dict | None = None,
) -> Notification:
    row = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        action_url=action_url,
        data=data or {},
    )
    db.add(row)
    return row
