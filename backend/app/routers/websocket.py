from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.core.time import as_utc, utcnow
from app.models.communication import ChatParticipant
from app.models.team import Team, TeamMember
from app.models.user import User
from app.services.realtime import realtime

router = APIRouter(tags=["realtime"])


def _authorized_channel(db, user: User, channel: str) -> bool:
    if channel in {"transfers:feed"} or channel.startswith("rankings:") or channel.startswith("tournament:") or channel.startswith("challenge:"):
        return True
    if channel == f"user:{user.id}" or channel == f"notifications:{user.id}":
        return True
    prefix, separator, raw_id = channel.partition(":")
    if not separator:
        return False
    try:
        entity_id = uuid.UUID(raw_id)
    except ValueError:
        return False
    if prefix == "chat":
        return bool(
            db.query(ChatParticipant.id)
            .filter_by(thread_id=entity_id, user_id=user.id, is_active=True)
            .first()
        )
    if prefix == "team":
        team = db.get(Team, entity_id)
        return bool(
            team
            and (
                user.is_platform_admin
                or team.manager_id == user.id
                or db.query(TeamMember.id)
                .filter_by(team_id=entity_id, user_id=user.id, is_active=True)
                .first()
            )
        )
    return False


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        auth = await asyncio.wait_for(websocket.receive_json(), timeout=10)
    except (asyncio.TimeoutError, ValueError, WebSocketDisconnect):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        return
    if auth.get("type") != "auth" or not isinstance(auth.get("token"), str):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication message")
        return
    subject = decode_access_token(auth["token"])
    try:
        user_id = uuid.UUID(subject) if subject else None
    except ValueError:
        user_id = None
    with SessionLocal() as db:
        user = db.get(User, user_id) if user_id else None
        actively_banned = bool(user and user.is_banned and (user.banned_until is None or as_utc(user.banned_until) > utcnow()))
        if not user or actively_banned:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or suspended account")
            return
    await realtime.connect(websocket, user.id, accept=False)
    await realtime.subscribe(websocket, f"user:{user.id}")
    await websocket.send_json({"type": "auth.ok", "user_id": str(user.id)})
    try:
        while True:
            message = await websocket.receive_json()
            command = message.get("type")
            if command == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            channel = message.get("channel")
            if command not in {"subscribe", "unsubscribe"} or not isinstance(channel, str) or len(channel) > 120:
                await websocket.send_json({"type": "error", "code": "invalid_command"})
                continue
            if command == "subscribe":
                with SessionLocal() as db:
                    fresh_user = db.get(User, user.id)
                    actively_banned = bool(
                        fresh_user
                        and fresh_user.is_banned
                        and (fresh_user.banned_until is None or as_utc(fresh_user.banned_until) > utcnow())
                    )
                    permitted = bool(fresh_user and not actively_banned and _authorized_channel(db, fresh_user, channel))
                if not permitted:
                    await websocket.send_json({"type": "error", "code": "channel_forbidden", "channel": channel})
                    continue
                await realtime.subscribe(websocket, channel)
                await websocket.send_json({"type": "subscribed", "channel": channel})
            else:
                await realtime.unsubscribe(websocket, channel)
                await websocket.send_json({"type": "unsubscribed", "channel": channel})
    except (WebSocketDisconnect, ValueError):
        pass
    finally:
        await realtime.disconnect(websocket)
