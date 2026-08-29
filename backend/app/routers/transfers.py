from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_tournament_organizer
from app.models.enums import NotificationType, PlayerContractStatus, TeamRole, TransferOfferStatus
from app.models.team import Team, TeamMember
from app.models.transfer import (
    Contract,
    MarketValueSnapshot,
    TransferOffer,
    TransferOfferEvent,
    TransferRumour,
    TransferWatchlist,
    TransferWindow,
)
from app.models.user import User
from app.schemas.transfers import (
    ClubDecision,
    ContractListingIn,
    ContractOut,
    CounterDecision,
    OfferCreate,
    OfferOut,
    PlayerDecision,
    RumourIn,
    TransferWindowIn,
    WatchlistIn,
)
from app.services.market_value import compute_market_value
from app.services.notifications import create_notification
from app.services.permissions import require_team_manager
from app.services.realtime import realtime
from app.services.transfers import complete_offer, create_offer, expire_pending_offers, transition_offer

router = APIRouter(prefix="/transfers", tags=["transfer centre"])


def _offer_or_404(db: Session, offer_id: uuid.UUID) -> TransferOffer:
    row = db.get(TransferOffer, offer_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer offer not found.")
    return row


def _require_offer_access(db: Session, offer: TransferOffer, user: User) -> None:
    if user.is_platform_admin or offer.player_id == user.id or offer.created_by == user.id:
        return
    team_ids = [offer.to_team_id] + ([offer.from_team_id] if offer.from_team_id else [])
    permitted = (
        db.query(Team.id)
        .filter(Team.id.in_(team_ids), Team.manager_id == user.id)
        .first()
    )
    if not permitted:
        permitted = (
            db.query(TeamMember.id)
            .filter(
                TeamMember.team_id.in_(team_ids),
                TeamMember.user_id == user.id,
                TeamMember.role == TeamRole.MANAGER,
                TeamMember.is_active.is_(True),
            )
            .first()
        )
    if not permitted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this offer.")


@router.post("/offers", response_model=OfferOut, status_code=status.HTTP_201_CREATED)
def submit_offer(
    payload: OfferCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expire_pending_offers(db)
    destination = require_team_manager(db, payload.to_team_id, current_user)
    player = db.get(User, payload.player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found.")
    values = payload.model_dump(exclude={"expires_in_hours", "player_id", "to_team_id"})
    row = create_offer(
        db,
        player=player,
        destination=destination,
        created_by=current_user,
        values=values,
        expires_in_hours=payload.expires_in_hours,
    )
    db.commit()
    db.refresh(row)
    background_tasks.add_task(
        realtime.publish_channel,
        "transfers:feed",
        {"type": "transfer.offer.created", "offer_id": str(row.id), "player_id": str(row.player_id)},
    )
    return row


@router.get("/offers", response_model=list[OfferOut])
def my_offer_inbox(
    offer_status: TransferOfferStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    changed = expire_pending_offers(db)
    managed_ids = [row[0] for row in db.query(Team.id).filter(Team.manager_id == current_user.id).all()]
    managed_ids.extend(
        row[0]
        for row in db.query(TeamMember.team_id)
        .filter(
            TeamMember.user_id == current_user.id,
            TeamMember.role == TeamRole.MANAGER,
            TeamMember.is_active.is_(True),
        )
        .all()
    )
    query = db.query(TransferOffer)
    if not current_user.is_platform_admin:
        query = query.filter(
            or_(
                TransferOffer.player_id == current_user.id,
                TransferOffer.created_by == current_user.id,
                TransferOffer.from_team_id.in_(managed_ids) if managed_ids else False,
                TransferOffer.to_team_id.in_(managed_ids) if managed_ids else False,
            )
        )
    if offer_status:
        query = query.filter(TransferOffer.status == offer_status)
    rows = query.order_by(TransferOffer.created_at.desc()).limit(limit).all()
    if changed:
        db.commit()
    return rows


@router.get("/offers/{offer_id}", response_model=OfferOut)
def get_offer(
    offer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _offer_or_404(db, offer_id)
    _require_offer_access(db, row, current_user)
    if expire_pending_offers(db):
        db.commit()
        db.refresh(row)
    return row


@router.get("/offers/{offer_id}/events")
def offer_history(
    offer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _offer_or_404(db, offer_id)
    _require_offer_access(db, row, current_user)
    return (
        db.query(TransferOfferEvent)
        .filter_by(offer_id=offer_id)
        .order_by(TransferOfferEvent.created_at.asc())
        .all()
    )


@router.post("/offers/{offer_id}/club-decision", response_model=OfferOut)
def club_decision(
    offer_id: uuid.UUID,
    payload: ClubDecision,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _offer_or_404(db, offer_id)
    if not row.from_team_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A free-agent offer has no releasing club.")
    source = require_team_manager(db, row.from_team_id, current_user)
    if row.status != TransferOfferStatus.PENDING_CLUB_REVIEW:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This offer is not awaiting club review.")
    if payload.decision == "counter":
        for key, value in payload.model_dump(exclude={"decision", "note"}, exclude_unset=True).items():
            setattr(row, key, value)
        target = TransferOfferStatus.COUNTERED
    elif payload.decision == "approve":
        target = TransferOfferStatus.PENDING_PLAYER_REVIEW
    else:
        target = TransferOfferStatus.REJECTED_BY_CLUB
    transition_offer(db, row, target=target, actor_id=current_user.id, note=payload.note)
    destination = db.get(Team, row.to_team_id)
    if destination and destination.manager_id:
        create_notification(
            db,
            user_id=destination.manager_id,
            notification_type=NotificationType.TRANSFER,
            title=f"Offer {payload.decision}d by {source.name}",
            body=f"The club reviewed transfer offer {row.id}.",
            action_url=f"/transfers/offers/{row.id}",
        )
    if target == TransferOfferStatus.PENDING_PLAYER_REVIEW:
        create_notification(
            db,
            user_id=row.player_id,
            notification_type=NotificationType.TRANSFER,
            title="Transfer offer ready for your decision",
            body="Your club approved the offer. Review the contract terms before accepting.",
            action_url=f"/transfers/offers/{row.id}",
        )
    db.commit()
    db.refresh(row)
    return row


@router.post("/offers/{offer_id}/counter-decision", response_model=OfferOut)
def counter_decision(
    offer_id: uuid.UUID,
    payload: CounterDecision,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _offer_or_404(db, offer_id)
    require_team_manager(db, row.to_team_id, current_user)
    if row.status != TransferOfferStatus.COUNTERED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This offer has no counter awaiting a decision.")
    target = TransferOfferStatus.PENDING_PLAYER_REVIEW if payload.accept else TransferOfferStatus.CANCELLED
    transition_offer(db, row, target=target, actor_id=current_user.id, note=payload.note)
    if payload.accept:
        create_notification(
            db,
            user_id=row.player_id,
            notification_type=NotificationType.TRANSFER,
            title="Transfer offer ready for your decision",
            body="The clubs agreed terms. You have the final decision.",
            action_url=f"/transfers/offers/{row.id}",
        )
    db.commit()
    db.refresh(row)
    return row


@router.post("/offers/{offer_id}/player-decision", response_model=OfferOut)
def player_decision(
    offer_id: uuid.UUID,
    payload: PlayerDecision,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _offer_or_404(db, offer_id)
    if row.player_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the player can make this decision.")
    if row.status != TransferOfferStatus.PENDING_PLAYER_REVIEW:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This offer is not awaiting the player.")
    target = TransferOfferStatus.ACCEPTED if payload.accept else TransferOfferStatus.REJECTED_BY_PLAYER
    transition_offer(db, row, target=target, actor_id=current_user.id, note=payload.note)
    destination = db.get(Team, row.to_team_id)
    if destination and destination.manager_id:
        create_notification(
            db,
            user_id=destination.manager_id,
            notification_type=NotificationType.TRANSFER,
            title="Player accepted the offer" if payload.accept else "Player rejected the offer",
            body=f"The player has reviewed offer {row.id}.",
            action_url=f"/transfers/offers/{row.id}",
        )
    db.commit()
    db.refresh(row)
    return row


@router.post("/offers/{offer_id}/complete", response_model=ContractOut)
def finalize_transfer(
    offer_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _offer_or_404(db, offer_id)
    require_team_manager(db, row.to_team_id, current_user)
    contract = complete_offer(db, row, current_user)
    db.commit()
    db.refresh(contract)
    background_tasks.add_task(
        realtime.publish_channel,
        "transfers:feed",
        {
            "type": "transfer.completed",
            "offer_id": str(row.id),
            "player_id": str(row.player_id),
            "from_team_id": str(row.from_team_id) if row.from_team_id else None,
            "to_team_id": str(row.to_team_id),
        },
    )
    return contract


@router.delete("/offers/{offer_id}", response_model=OfferOut)
def cancel_offer(
    offer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _offer_or_404(db, offer_id)
    require_team_manager(db, row.to_team_id, current_user)
    if row.status not in {
        TransferOfferStatus.PENDING_CLUB_REVIEW,
        TransferOfferStatus.COUNTERED,
        TransferOfferStatus.PENDING_PLAYER_REVIEW,
    }:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This offer can no longer be cancelled.")
    transition_offer(db, row, target=TransferOfferStatus.CANCELLED, actor_id=current_user.id, note="Cancelled by bidder.")
    db.commit()
    db.refresh(row)
    return row


@router.put("/contracts/{contract_id}/listing")
def update_contract_listing(
    contract_id: uuid.UUID,
    payload: ContractListingIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(Contract, contract_id)
    if not row or not row.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active contract not found.")
    if row.player_id != current_user.id:
        require_team_manager(db, row.team_id, current_user)
    row.status = PlayerContractStatus(payload.status)
    db.commit()
    db.refresh(row)
    return row


@router.put("/watchlists/{team_id}", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    team_id: uuid.UUID,
    payload: WatchlistIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, team_id, current_user)
    if not db.get(User, payload.player_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found.")
    row = db.query(TransferWatchlist).filter_by(team_id=team_id, player_id=payload.player_id).first()
    if row:
        row.priority = payload.priority
        row.note = payload.note
    else:
        row = TransferWatchlist(team_id=team_id, player_id=payload.player_id, added_by=current_user.id, **payload.model_dump(exclude={"player_id"}))
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/watchlists/{team_id}")
def watchlist(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, team_id, current_user)
    return db.query(TransferWatchlist).filter_by(team_id=team_id).order_by(TransferWatchlist.priority.asc()).all()


@router.delete("/watchlists/{team_id}/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    team_id: uuid.UUID,
    player_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, team_id, current_user)
    db.query(TransferWatchlist).filter_by(team_id=team_id, player_id=player_id).delete()
    db.commit()


@router.post("/rumours", status_code=status.HTTP_201_CREATED)
def create_rumour(
    payload: RumourIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = payload.linked_team_id or payload.from_team_id
    if team_id:
        require_team_manager(db, team_id, current_user)
    elif not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A team manager or admin must create rumours.")
    values = payload.model_dump()
    if values["is_public"] and not current_user.is_platform_admin:
        values["is_public"] = False
    row = TransferRumour(created_by=current_user.id, **values)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/rumours")
def public_rumours(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.query(TransferRumour).filter_by(is_public=True).order_by(TransferRumour.created_at.desc()).limit(limit).all()


@router.get("/market-values/{player_id}")
def latest_market_value(player_id: uuid.UUID, db: Session = Depends(get_db)):
    row = (
        db.query(MarketValueSnapshot)
        .filter_by(player_id=player_id)
        .order_by(MarketValueSnapshot.computed_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No market-value estimate exists yet.")
    return row


@router.post("/market-values/{player_id}/recalculate", status_code=status.HTTP_201_CREATED)
def recalculate_market_value(
    player_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id != player_id and not current_user.is_platform_admin:
        watched = (
            db.query(TransferWatchlist.id)
            .join(Team, Team.id == TransferWatchlist.team_id)
            .filter(TransferWatchlist.player_id == player_id, Team.manager_id == current_user.id)
            .first()
        )
        if not watched:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the player, an admin, or a watching team manager may recalculate.")
    try:
        row = compute_market_value(db, player_id=player_id, trigger_type="manual")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.commit()
    db.refresh(row)
    return row


@router.post("/windows", status_code=status.HTTP_201_CREATED)
def create_transfer_window(
    payload: TransferWindowIn,
    organizer: User = Depends(require_tournament_organizer),
    db: Session = Depends(get_db),
):
    row = TransferWindow(organizer_id=organizer.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/windows")
def list_transfer_windows(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.query(TransferWindow).order_by(TransferWindow.transfer_window_opens.desc()).limit(limit).all()
