from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.time import utcnow
from app.models.communication import ChatMessage, ChatParticipant, ChatThread, Notification
from app.models.enums import ChatThreadType, NotificationType
from app.models.team import Team, TeamMember
from app.models.tournament import Tournament
from app.models.user import User
from app.schemas.communication import (
    ChatMessageEditIn,
    ChatMessageIn,
    ChatMessageOut,
    ChatThreadIn,
    ChatThreadOut,
    DeviceTokenIn,
    NotificationOut,
    ParticipantIn,
)
from app.services.notifications import create_notification
from app.services.permissions import require_chat_participant
from app.services.realtime import realtime

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
chat_router = APIRouter(prefix="/chat", tags=["chat"])


@notifications_router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    before: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    if before:
        query = query.filter(Notification.created_at < before)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


@notifications_router.get("/unread-count")
def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(Notification.id).filter(Notification.user_id == current_user.id, Notification.is_read.is_(False)).count()
    return {"unread_count": count}


@notifications_router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(Notification, notification_id)
    if not row or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    row.is_read = True
    row.read_at = row.read_at or utcnow()
    db.commit()
    db.refresh(row)
    return row


@notifications_router.post("/read-all")
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = utcnow()
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .update({"is_read": True, "read_at": now}, synchronize_session=False)
    )
    db.commit()
    return {"updated": count}


@notifications_router.put("/device-token", status_code=status.HTTP_204_NO_CONTENT)
def update_device_token(
    payload: DeviceTokenIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.fcm_device_token = payload.token.strip() if payload.token else None
    db.commit()


def _thread_or_404(db: Session, thread_id: uuid.UUID) -> ChatThread:
    thread = db.get(ChatThread, thread_id)
    if not thread or thread.is_archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found.")
    return thread


def _active_team_member_ids(db: Session, team: Team) -> list[uuid.UUID]:
    ids = [row[0] for row in db.query(TeamMember.user_id).filter_by(team_id=team.id, is_active=True).all()]
    if team.manager_id:
        ids.append(team.manager_id)
    return ids


@chat_router.post("/threads", response_model=ChatThreadOut, status_code=status.HTTP_201_CREATED)
def create_thread(
    payload: ChatThreadIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    participant_ids = set(payload.participant_ids)
    participant_ids.add(current_user.id)
    direct_key = None
    if payload.thread_type == ChatThreadType.DIRECT:
        if current_user.id in payload.participant_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose another user for a direct chat.")
        direct_key = ":".join(sorted(str(value) for value in participant_ids))
        existing = db.query(ChatThread).filter_by(direct_key=direct_key, is_archived=False).first()
        if existing:
            return existing
    elif payload.thread_type == ChatThreadType.TEAM:
        team = db.get(Team, payload.team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
        member_ids = set(_active_team_member_ids(db, team))
        if current_user.id not in member_ids and not current_user.is_platform_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active team membership required.")
        participant_ids = member_ids
    elif payload.thread_type == ChatThreadType.TOURNAMENT:
        tournament = db.get(Tournament, payload.tournament_id)
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found.")
        if tournament.organizer_id != current_user.id and not current_user.is_platform_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the tournament organizer may create this thread.")
    elif payload.thread_type == ChatThreadType.SUPPORT:
        participant_ids = {current_user.id}

    existing_users = {row[0] for row in db.query(User.id).filter(User.id.in_(participant_ids)).all()}
    if existing_users != participant_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more chat participants do not exist.")
    row = ChatThread(
        direct_key=direct_key,
        thread_type=payload.thread_type,
        title=payload.title,
        team_id=payload.team_id,
        tournament_id=payload.tournament_id,
        created_by=current_user.id,
    )
    db.add(row)
    db.flush()
    db.add_all(
        ChatParticipant(
            thread_id=row.id,
            user_id=user_id,
            is_admin=user_id == current_user.id,
        )
        for user_id in participant_ids
    )
    db.commit()
    db.refresh(row)
    return row


@chat_router.get("/threads", response_model=list[ChatThreadOut])
def list_threads(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ChatThread)
        .join(ChatParticipant, ChatParticipant.thread_id == ChatThread.id)
        .filter(
            ChatParticipant.user_id == current_user.id,
            ChatParticipant.is_active.is_(True),
            ChatThread.is_archived.is_(False),
        )
        .order_by(ChatThread.updated_at.desc())
        .limit(limit)
        .all()
    )


@chat_router.get("/threads/{thread_id}/participants")
def list_participants(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _thread_or_404(db, thread_id)
    require_chat_participant(db, thread_id, current_user.id)
    return db.query(ChatParticipant).filter_by(thread_id=thread_id, is_active=True).all()


@chat_router.post("/threads/{thread_id}/participants", status_code=status.HTTP_201_CREATED)
def add_participant(
    thread_id: uuid.UUID,
    payload: ParticipantIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = _thread_or_404(db, thread_id)
    actor = require_chat_participant(db, thread_id, current_user.id)
    if not actor.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Thread admin access required.")
    if thread.thread_type == ChatThreadType.DIRECT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Direct threads cannot add participants.")
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    row = db.query(ChatParticipant).filter_by(thread_id=thread_id, user_id=payload.user_id).first()
    if row:
        row.is_active = True
        row.is_admin = payload.is_admin
    else:
        row = ChatParticipant(thread_id=thread_id, **payload.model_dump())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@chat_router.get("/threads/{thread_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    thread_id: uuid.UUID,
    before: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _thread_or_404(db, thread_id)
    require_chat_participant(db, thread_id, current_user.id)
    query = db.query(ChatMessage).filter(ChatMessage.thread_id == thread_id)
    if before:
        query = query.filter(ChatMessage.created_at < before)
    return query.order_by(ChatMessage.created_at.desc()).limit(limit).all()


@chat_router.post("/threads/{thread_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    thread_id: uuid.UUID,
    payload: ChatMessageIn,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = _thread_or_404(db, thread_id)
    participant = require_chat_participant(db, thread_id, current_user.id)
    if payload.reply_to_message_id:
        replied = db.get(ChatMessage, payload.reply_to_message_id)
        if not replied or replied.thread_id != thread_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reply target is not in this thread.")
    row = ChatMessage(
        thread_id=thread_id,
        sender_user_id=current_user.id,
        body=payload.body.strip(),
        attachments=payload.attachments,
        reply_to_message_id=payload.reply_to_message_id,
    )
    db.add(row)
    thread.updated_at = utcnow()
    participant.last_read_at = utcnow()
    db.flush()
    recipients = [
        value[0]
        for value in db.query(ChatParticipant.user_id)
        .filter(
            ChatParticipant.thread_id == thread_id,
            ChatParticipant.is_active.is_(True),
            ChatParticipant.user_id != current_user.id,
        )
        .all()
    ]
    for recipient_id in recipients:
        create_notification(
            db,
            user_id=recipient_id,
            notification_type=NotificationType.CHAT,
            title=thread.title or "New message",
            body=payload.body.strip()[:180] or "Sent an attachment",
            action_url=f"/chat/{thread.id}",
            data={"thread_id": str(thread.id), "message_id": str(row.id)},
        )
    db.commit()
    db.refresh(row)
    event = {
        "type": "chat.message.created",
        "thread_id": str(thread_id),
        "message": {
            "id": str(row.id),
            "sender_user_id": str(row.sender_user_id),
            "body": row.body,
            "attachments": row.attachments,
            "reply_to_message_id": str(row.reply_to_message_id) if row.reply_to_message_id else None,
            "created_at": row.created_at.isoformat(),
        },
    }
    background_tasks.add_task(realtime.publish_channel, f"chat:{thread_id}", event)
    for recipient_id in recipients:
        background_tasks.add_task(realtime.send_user, recipient_id, event)
    return row


@chat_router.patch("/messages/{message_id}", response_model=ChatMessageOut)
def edit_message(
    message_id: uuid.UUID,
    payload: ChatMessageEditIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(ChatMessage, message_id)
    if not row or row.sender_user_id != current_user.id or row.deleted_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    row.body = payload.body.strip()
    row.edited_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


@chat_router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(ChatMessage, message_id)
    if not row or row.sender_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    row.body = ""
    row.attachments = []
    row.deleted_at = utcnow()
    db.commit()


@chat_router.post("/threads/{thread_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_thread_read(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    participant = require_chat_participant(db, thread_id, current_user.id)
    participant.last_read_at = utcnow()
    db.commit()
