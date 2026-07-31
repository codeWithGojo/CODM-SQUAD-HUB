import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    raw_sub = decode_access_token(credentials.credentials)
    if not raw_sub or raw_sub.startswith("pending:"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or incomplete auth token.")

    try:
        user_id = uuid.UUID(raw_sub)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token subject.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is banned.")
    return user


def require_team_manager(team_id: str):
    """
    Factory for a dependency that checks the current user manages the
    given team. Used to gate manager-only actions (submitting official
    results, VOD reviews, managing roster) — the core rule that keeps
    the leaderboard trustworthy.
    """
    def _check(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        from app.models.team import Team
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team or team.manager_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only this team's manager can do that.")
        return current_user

    return _check
def require_tournament_organizer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.organizer import TournamentOrganizerApplication
    from app.models.enums import TournamentOrganizerStatus

    application = (
        db.query(TournamentOrganizerApplication)
        .filter(
            TournamentOrganizerApplication.user_id == current_user.id,
            TournamentOrganizerApplication.status == TournamentOrganizerStatus.APPROVED,
        )
        .first()
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an approved Tournament Organizer can do that.",
        )
    return current_user