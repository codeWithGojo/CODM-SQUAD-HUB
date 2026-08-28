from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import as_utc, utcnow
from app.models.communication import Notification
from app.models.competitive import Scrim
from app.models.enums import NotificationType, ScrimStatus
from app.models.team import Team
from app.models.user import User
from app.services.notifications import create_notification


def create_due_scrim_reminders(db: Session) -> dict[str, int]:
    now = utcnow()
    rows = (
        db.query(Scrim)
        .filter(
            Scrim.status == ScrimStatus.UPCOMING,
            Scrim.scheduled_at > now,
            Scrim.scheduled_at <= now + timedelta(hours=1),
        )
        .with_for_update()
        .all()
    )
    created = 0
    for scrim in rows:
        minutes = 15 if as_utc(scrim.scheduled_at) <= now + timedelta(minutes=15) else 60
        if minutes == 15 and scrim.reminder_15m_sent:
            continue
        if minutes == 60 and scrim.reminder_1h_sent:
            continue
        team_ids = [scrim.team_id] + ([scrim.opponent_team_id] if scrim.opponent_team_id else [])
        for team in db.query(Team).filter(Team.id.in_(team_ids)).all():
            if team.manager_id:
                create_notification(
                    db,
                    user_id=team.manager_id,
                    notification_type=NotificationType.MATCH,
                    title=f"Scrim starts in {minutes} minutes",
                    body=f"{team.name} vs {scrim.opponent_name} is coming up.",
                    action_url=f"/scrims/{scrim.id}",
                    data={"scrim_id": str(scrim.id), "minutes": minutes},
                )
                created += 1
        if minutes == 15:
            scrim.reminder_15m_sent = True
            scrim.reminder_1h_sent = True
        else:
            scrim.reminder_1h_sent = True
    return {"scrims_checked": len(rows), "notifications_created": created}


def deliver_pending_push_notifications(db: Session, *, limit: int = 200) -> dict[str, int | bool]:
    if not settings.firebase_credentials_path:
        return {"configured": False, "sent": 0, "failed": 0}
    credentials_path = Path(settings.firebase_credentials_path).expanduser()
    if not credentials_path.is_file():
        return {"configured": False, "sent": 0, "failed": 0}
    import firebase_admin
    from firebase_admin import credentials, messaging

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(str(credentials_path)))
    rows = (
        db.query(Notification, User)
        .join(User, User.id == Notification.user_id)
        .filter(Notification.push_sent_at.is_(None), User.fcm_device_token.is_not(None))
        .order_by(Notification.created_at.asc())
        .limit(limit)
        .all()
    )
    sent = failed = 0
    for notification, user in rows:
        try:
            messaging.send(
                messaging.Message(
                    token=user.fcm_device_token,
                    notification=messaging.Notification(title=notification.title, body=notification.body),
                    data={
                        "notification_id": str(notification.id),
                        "type": notification.type.value,
                        "action_url": notification.action_url or "",
                    },
                )
            )
            notification.push_sent_at = utcnow()
            notification.push_error = None
            sent += 1
        except Exception as exc:
            notification.push_error = str(exc)[:500]
            failed += 1
    return {"configured": True, "sent": sent, "failed": failed}
