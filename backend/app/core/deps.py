from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.time import as_utc, utcnow
from app.models.enums import TournamentOrganizerStatus
from app.models.organizer import TournamentOrganizerApplication
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    raw_sub = decode_access_token(credentials.credentials)
    try:
        user_id = uuid.UUID(raw_sub or "")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.") from exc

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    if user.is_banned and (user.banned_until is None or as_utc(user.banned_until) > utcnow()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is banned.")
    user.last_active = utcnow()
    return user


def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator access required.")
    return current_user


def require_tournament_organizer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if current_user.is_platform_admin:
        return current_user
    approved = (
        db.query(TournamentOrganizerApplication.id)
        .filter(
            TournamentOrganizerApplication.user_id == current_user.id,
            TournamentOrganizerApplication.status == TournamentOrganizerStatus.APPROVED,
        )
        .first()
    )
    if not approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approved Tournament Organizer access required.",
        )
    return current_user
