from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_platform_admin
from app.core.time import utcnow
from app.models.commerce import PaymentTransaction
from app.models.communication import Notification
from app.models.enums import (
    AuditAction,
    BlacklistStatus,
    DisputeStatus,
    PaymentStatus,
    TournamentOrganizerStatus,
    TournamentStatus,
    VerificationStatus,
)
from app.models.governance import BlacklistEntry, TournamentDispute
from app.models.misc import AccountReport
from app.models.organization_extra import Achievement, AuditLog
from app.models.organizer import TournamentOrganizerApplication
from app.models.team import Organization, Team
from app.models.tournament import Tournament
from app.models.transfer import TransferRumour
from app.models.user import AccountSecurityEvent, User
from app.schemas.admin import (
    AchievementVerificationIn,
    BroadcastNotificationIn,
    ReportIn,
    ReportReviewIn,
    RumourPublishIn,
    UserBanIn,
    VerificationIn,
)
from app.services.audit import write_audit_log
from app.services.notifications import create_notification
from app.services.jobs import create_due_scrim_reminders, deliver_pending_push_notifications
from app.services.realtime import realtime

admin_router = APIRouter(prefix="/admin", tags=["admin"])
moderation_router = APIRouter(prefix="/moderation", tags=["moderation"])


@moderation_router.post("/reports", status_code=status.HTTP_201_CREATED)
def file_account_report(
    payload: ReportIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.reported_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot report your own account.")
    if not db.get(User, payload.reported_user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reported user not found.")
    row = AccountReport(reported_by=current_user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@admin_router.get("/dashboard")
def dashboard(
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    active_blacklist = db.query(BlacklistEntry.id).filter(BlacklistEntry.status.in_([BlacklistStatus.ACTIVE, BlacklistStatus.APPEALED])).count()
    revenue_kobo = db.query(func.coalesce(func.sum(PaymentTransaction.amount_kobo), 0)).filter(PaymentTransaction.status == PaymentStatus.SUCCESS).scalar()
    return {
        "users": db.query(User.id).count(),
        "banned_users": db.query(User.id).filter(User.is_banned.is_(True)).count(),
        "organizations": db.query(Organization.id).count(),
        "teams": db.query(Team.id).count(),
        "live_tournaments": db.query(Tournament.id).filter(Tournament.status == TournamentStatus.LIVE).count(),
        "open_disputes": db.query(TournamentDispute.id).filter(TournamentDispute.status.in_([DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.ESCALATED])).count(),
        "pending_organizers": db.query(TournamentOrganizerApplication.id).filter(TournamentOrganizerApplication.status == TournamentOrganizerStatus.PENDING).count(),
        "active_blacklist_entries": active_blacklist,
        "pending_reports": db.query(AccountReport.id).filter(AccountReport.reviewed.is_(False)).count(),
        "failed_payments": db.query(PaymentTransaction.id).filter(PaymentTransaction.status == PaymentStatus.FAILED).count(),
        "revenue_kobo": int(revenue_kobo or 0),
        "websocket_connections": realtime.connection_count,
    }


@admin_router.get("/users")
def list_users(
    search: str | None = Query(default=None, max_length=100),
    banned: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(User.gamertag.ilike(pattern), User.shid.ilike(pattern), User.phone.ilike(pattern)))
    if banned is not None:
        query = query.filter(User.is_banned.is_(banned))
    return query.order_by(User.created_at.desc()).limit(limit).all()


@admin_router.patch("/users/{user_id}/ban")
def set_user_ban(
    user_id: uuid.UUID,
    payload: UserBanIn,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if row.id == admin.id and payload.banned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot ban your own admin account.")
    row.is_banned = payload.banned
    row.ban_reason = payload.reason if payload.banned else None
    row.banned_until = payload.banned_until if payload.banned else None
    write_audit_log(
        db,
        actor_user_id=admin.id,
        action=AuditAction.BAN if payload.banned else AuditAction.UNBAN,
        target_type="user",
        target_id=row.id,
        summary=f"{'Banned' if payload.banned else 'Unbanned'} {row.gamertag}.",
        metadata={"reason": payload.reason, "banned_until": payload.banned_until.isoformat() if payload.banned_until else None},
    )
    create_notification(
        db,
        user_id=row.id,
        notification_type=payload_notification_type(),
        title="Account suspended" if payload.banned else "Account restored",
        body=payload.reason or ("Your account has been suspended." if payload.banned else "Your account access has been restored."),
    )
    db.commit()
    background_tasks.add_task(
        realtime.send_user,
        row.id,
        {"type": "account.ban_changed", "banned": payload.banned, "banned_until": payload.banned_until.isoformat() if payload.banned_until else None},
    )
    return row


def payload_notification_type():
    from app.models.enums import NotificationType

    return NotificationType.MODERATION


@admin_router.patch("/organizations/{organization_id}/verification")
def verify_organization(
    organization_id: uuid.UUID,
    payload: VerificationIn,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    row = db.get(Organization, organization_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    row.verification_status = payload.status
    write_audit_log(
        db,
        actor_user_id=admin.id,
        action=AuditAction.VERIFY,
        target_type="organization",
        target_id=row.id,
        summary=f"Set organization verification to {payload.status.value}.",
        metadata={"note": payload.note},
    )
    db.commit()
    db.refresh(row)
    return row


@admin_router.patch("/users/{user_id}/verification")
def verify_player(
    user_id: uuid.UUID,
    payload: VerificationIn,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    row.verification_status = payload.status
    write_audit_log(
        db,
        actor_user_id=admin.id,
        action=AuditAction.VERIFY,
        target_type="user",
        target_id=row.id,
        summary=f"Set player verification to {payload.status.value}.",
        metadata={"note": payload.note},
    )
    db.commit()
    db.refresh(row)
    return row


@admin_router.patch("/achievements/{achievement_id}/verification")
def verify_achievement(
    achievement_id: uuid.UUID,
    payload: AchievementVerificationIn,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    row = db.get(Achievement, achievement_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found.")
    row.is_verified = payload.verified
    row.verified_by = admin.id if payload.verified else None
    write_audit_log(
        db,
        actor_user_id=admin.id,
        action=AuditAction.VERIFY if payload.verified else AuditAction.UPDATE,
        target_type="achievement",
        target_id=row.id,
        summary="Verified achievement." if payload.verified else "Removed achievement verification.",
        metadata={"note": payload.note},
    )
    db.commit()
    db.refresh(row)
    return row


@admin_router.get("/reports")
def list_reports(
    reviewed: bool | None = False,
    limit: int = Query(default=100, ge=1, le=200),
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AccountReport)
    if reviewed is not None:
        query = query.filter(AccountReport.reviewed.is_(reviewed))
    return query.order_by(AccountReport.created_at.desc()).limit(limit).all()


@admin_router.patch("/reports/{report_id}")
def review_report(
    report_id: uuid.UUID,
    payload: ReportReviewIn,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    row = db.get(AccountReport, report_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    row.reviewed = True
    row.reviewed_by = admin.id
    row.review_note = payload.review_note
    write_audit_log(
        db,
        actor_user_id=admin.id,
        action=AuditAction.UPDATE,
        target_type="account_report",
        target_id=row.id,
        summary="Reviewed an account report.",
    )
    db.commit()
    db.refresh(row)
    return row


@admin_router.get("/audit-logs")
def audit_logs(
    before: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if before:
        query = query.filter(AuditLog.created_at < before)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()


@admin_router.get("/security-events")
def security_events(
    user_id: uuid.UUID | None = None,
    minimum_risk: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=100, ge=1, le=200),
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AccountSecurityEvent).filter(AccountSecurityEvent.risk_score >= minimum_risk)
    if user_id:
        query = query.filter(AccountSecurityEvent.user_id == user_id)
    return query.order_by(AccountSecurityEvent.created_at.desc()).limit(limit).all()


@admin_router.get("/payments")
def payments(
    payment_status: PaymentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    query = db.query(PaymentTransaction)
    if payment_status:
        query = query.filter(PaymentTransaction.status == payment_status)
    return query.order_by(PaymentTransaction.created_at.desc()).limit(limit).all()


@admin_router.post("/notifications/broadcast")
def broadcast_notification(
    payload: BroadcastNotificationIn,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User.id)
    if payload.user_ids:
        query = query.filter(User.id.in_(payload.user_ids))
    user_ids = [row[0] for row in query.limit(10_000).all()]
    for user_id in user_ids:
        create_notification(
            db,
            user_id=user_id,
            notification_type=payload.notification_type,
            title=payload.title,
            body=payload.body,
            action_url=payload.action_url,
        )
    write_audit_log(
        db,
        actor_user_id=admin.id,
        action=AuditAction.CREATE,
        target_type="notification_broadcast",
        target_id=None,
        summary=f"Broadcast notification to {len(user_ids)} users.",
    )
    db.commit()
    for user_id in user_ids:
        background_tasks.add_task(realtime.send_user, user_id, {"type": "notification.created", "title": payload.title})
    return {"created": len(user_ids)}


@admin_router.patch("/transfer-rumours/{rumour_id}")
def publish_rumour(
    rumour_id: uuid.UUID,
    payload: RumourPublishIn,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    row = db.get(TransferRumour, rumour_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rumour not found.")
    row.is_public = payload.is_public
    write_audit_log(
        db,
        actor_user_id=admin.id,
        action=AuditAction.APPROVE if payload.is_public else AuditAction.UPDATE,
        target_type="transfer_rumour",
        target_id=row.id,
        summary="Published transfer rumour." if payload.is_public else "Unpublished transfer rumour.",
    )
    db.commit()
    db.refresh(row)
    return row


@admin_router.post("/jobs/scrim-reminders")
def run_scrim_reminders(
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    result = create_due_scrim_reminders(db)
    db.commit()
    return result


@admin_router.post("/jobs/push-notifications")
def run_push_delivery(
    limit: int = Query(default=200, ge=1, le=1000),
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    result = deliver_pending_push_notifications(db, limit=limit)
    db.commit()
    return result
