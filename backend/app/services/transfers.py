from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.time import as_utc, utcnow
from app.models.enums import (
    BlacklistSubjectType,
    BlacklistStatus,
    NotificationType,
    PlayerContractStatus,
    SanctionType,
    TeamRole,
    TransferOfferStatus,
    TransferOfferType,
)
from app.models.governance import BlacklistEntry
from app.models.team import PlayerTimelineEvent, Team, TeamMember
from app.models.transfer import Contract, TransferOffer, TransferOfferEvent
from app.models.user import User
from app.services.notifications import create_notification


OPEN_OFFER_STATES = {
    TransferOfferStatus.PENDING_CLUB_REVIEW,
    TransferOfferStatus.COUNTERED,
    TransferOfferStatus.PENDING_PLAYER_REVIEW,
    TransferOfferStatus.ACCEPTED,
}


def active_contract(db: Session, player_id: uuid.UUID) -> Contract | None:
    return (
        db.query(Contract)
        .filter(Contract.player_id == player_id, Contract.is_active.is_(True))
        .with_for_update()
        .first()
    )


def expire_pending_offers(db: Session) -> int:
    now = utcnow()
    rows = (
        db.query(TransferOffer)
        .filter(TransferOffer.status.in_(OPEN_OFFER_STATES), TransferOffer.expires_at <= now)
        .with_for_update()
        .all()
    )
    for row in rows:
        _transition(db, row, TransferOfferStatus.EXPIRED, row.created_by, "Offer expired automatically.")
    return len(rows)


def assert_no_transfer_ban(db: Session, player: User, *teams: Team | None) -> None:
    now = utcnow()
    subjects: list[tuple[BlacklistSubjectType, uuid.UUID]] = [(BlacklistSubjectType.USER, player.id)]
    for team in teams:
        if not team:
            continue
        subjects.append((BlacklistSubjectType.TEAM, team.id))
        if team.organization_id:
            subjects.append((BlacklistSubjectType.ORGANIZATION, team.organization_id))
    clauses = [
        (BlacklistEntry.subject_type == subject_type) & (BlacklistEntry.subject_id == subject_id)
        for subject_type, subject_id in subjects
    ]
    entry = (
        db.query(BlacklistEntry)
        .filter(
            or_(*clauses),
            BlacklistEntry.status.in_([BlacklistStatus.ACTIVE, BlacklistStatus.APPEALED]),
            BlacklistEntry.sanction_type.in_([SanctionType.TRANSFER_BAN, SanctionType.PLATFORM_BAN]),
            BlacklistEntry.starts_at <= now,
            or_(BlacklistEntry.ends_at.is_(None), BlacklistEntry.ends_at > now),
        )
        .first()
    )
    if entry:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Transfer blocked by active CRA sanction for {entry.subject_name_snapshot}.",
        )


def create_offer(
    db: Session,
    *,
    player: User,
    destination: Team,
    created_by: User,
    values: dict,
    expires_in_hours: int,
) -> TransferOffer:
    if player.career_status.value != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only active players may receive offers.")
    if not player.is_adult and not player.parental_consent_confirmed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verified parental consent is required for this player.")
    contract = active_contract(db, player.id)
    source = db.get(Team, contract.team_id) if contract else None
    offer_type = values["offer_type"]
    if source and source.id == destination.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The player already has an active contract with this team.")
    if offer_type == TransferOfferType.FREE_SIGNING and contract:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A contracted player cannot receive a free-agent offer.")
    if offer_type in {TransferOfferType.PERMANENT, TransferOfferType.LOAN} and not contract:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Use a free-signing offer for a free agent.")
    assert_no_transfer_ban(db, player, source, destination)
    duplicate = (
        db.query(TransferOffer.id)
        .filter(
            TransferOffer.player_id == player.id,
            TransferOffer.to_team_id == destination.id,
            TransferOffer.status.in_(OPEN_OFFER_STATES),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This team already has an open offer for the player.")
    initial_status = (
        TransferOfferStatus.PENDING_PLAYER_REVIEW if not source else TransferOfferStatus.PENDING_CLUB_REVIEW
    )
    row = TransferOffer(
        player_id=player.id,
        from_team_id=source.id if source else None,
        to_team_id=destination.id,
        created_by=created_by.id,
        status=initial_status,
        expires_at=utcnow() + timedelta(hours=expires_in_hours),
        **values,
    )
    db.add(row)
    db.flush()
    _event(db, row, created_by.id, None, initial_status, "Offer created.")
    create_notification(
        db,
        user_id=source.manager_id if source and source.manager_id else player.id,
        notification_type=NotificationType.TRANSFER,
        title="New transfer offer",
        body=f"{destination.name} submitted an offer for {player.gamertag}.",
        action_url=f"/transfers/offers/{row.id}",
        data={"offer_id": str(row.id)},
    )
    if source:
        create_notification(
            db,
            user_id=player.id,
            notification_type=NotificationType.TRANSFER,
            title="A club has made an offer",
            body=f"{destination.name}'s offer is awaiting club review.",
            action_url=f"/transfers/offers/{row.id}",
            data={"offer_id": str(row.id)},
        )
    return row


def transition_offer(
    db: Session,
    offer: TransferOffer,
    *,
    target: TransferOfferStatus,
    actor_id: uuid.UUID,
    note: str | None,
) -> TransferOffer:
    if as_utc(offer.expires_at) <= utcnow() and offer.status in OPEN_OFFER_STATES:
        _transition(db, offer, TransferOfferStatus.EXPIRED, actor_id, "Offer expired automatically.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The offer has expired.")
    _transition(db, offer, target, actor_id, note)
    return offer


def _transition(
    db: Session,
    offer: TransferOffer,
    target: TransferOfferStatus,
    actor_id: uuid.UUID,
    note: str | None,
) -> None:
    previous = offer.status
    offer.status = target
    if target not in OPEN_OFFER_STATES:
        offer.resolved_at = utcnow()
    _event(db, offer, actor_id, previous, target, note)


def _event(
    db: Session,
    offer: TransferOffer,
    actor_id: uuid.UUID,
    previous: TransferOfferStatus | None,
    target: TransferOfferStatus,
    note: str | None,
) -> None:
    db.add(
        TransferOfferEvent(
            offer_id=offer.id,
            actor_user_id=actor_id,
            from_status=previous.value if previous else None,
            to_status=target.value,
            note=note,
            snapshot={
                "offer_type": offer.offer_type.value,
                "transfer_fee_naira": offer.transfer_fee_naira,
                "loan_fee_naira": offer.loan_fee_naira,
                "loan_duration_days": offer.loan_duration_days,
                "proposed_salary_naira": offer.proposed_salary_naira,
                "proposed_contract_length_months": offer.proposed_contract_length_months,
            },
        )
    )


def complete_offer(db: Session, offer: TransferOffer, actor: User) -> Contract:
    if offer.status != TransferOfferStatus.ACCEPTED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The player must accept the offer first.")
    player = db.get(User, offer.player_id)
    destination = db.get(Team, offer.to_team_id)
    source = db.get(Team, offer.from_team_id) if offer.from_team_id else None
    if not player or not destination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player or destination team not found.")
    assert_no_transfer_ban(db, player, source, destination)
    current = active_contract(db, player.id)
    if current and source and current.team_id != source.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The player's active contract changed after this offer was created.")
    if current:
        current.is_active = False
        current.status = PlayerContractStatus.ON_LOAN if offer.offer_type == TransferOfferType.LOAN else PlayerContractStatus.TERMINATED
    db.flush()

    active_memberships = (
        db.query(TeamMember)
        .filter(TeamMember.user_id == player.id, TeamMember.is_active.is_(True))
        .with_for_update()
        .all()
    )
    for membership in active_memberships:
        membership.is_active = False
        membership.left_at = utcnow()
    destination_membership = (
        db.query(TeamMember)
        .filter(TeamMember.user_id == player.id, TeamMember.team_id == destination.id)
        .order_by(TeamMember.joined_at.desc())
        .first()
    )
    if destination_membership:
        destination_membership.is_active = True
        destination_membership.left_at = None
        destination_membership.joined_at = utcnow()
        destination_membership.role = TeamRole.PLAYER
    else:
        db.add(TeamMember(user_id=player.id, team_id=destination.id, role=TeamRole.PLAYER))

    is_loan = offer.offer_type == TransferOfferType.LOAN
    length_days = offer.loan_duration_days if is_loan else (offer.proposed_contract_length_months or 12) * 30
    contract = Contract(
        player_id=player.id,
        team_id=destination.id,
        parent_contract_id=current.id if current and is_loan else None,
        loan_return_team_id=source.id if source and is_loan else None,
        status=PlayerContractStatus.ON_LOAN if is_loan else PlayerContractStatus.UNDER_CONTRACT,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=length_days),
        salary_naira=offer.proposed_salary_naira,
        terms={
            "offer_id": str(offer.id),
            "transfer_fee_naira": offer.transfer_fee_naira,
            "loan_fee_naira": offer.loan_fee_naira,
            "loan_salary_payer": offer.loan_salary_payer,
            "loan_option_to_buy": offer.loan_option_to_buy,
            "loan_recall_clause": offer.loan_recall_clause,
        },
        signed_by_player_at=utcnow(),
        signed_by_team_at=utcnow(),
    )
    db.add(contract)
    db.add(
        PlayerTimelineEvent(
            user_id=player.id,
            event_type="loan" if is_loan else "transfer",
            description=f"Joined {destination.name}{' on loan' if is_loan else ''}.",
            from_team_id=source.id if source else None,
            to_team_id=destination.id,
            metadata_json={"offer_id": str(offer.id), "fee_public": offer.fee_is_public},
        )
    )
    _transition(db, offer, TransferOfferStatus.COMPLETED, actor.id, "Transfer completed.")
    create_notification(
        db,
        user_id=player.id,
        notification_type=NotificationType.TRANSFER,
        title="Transfer completed",
        body=f"You have joined {destination.name}{' on loan' if is_loan else ''}.",
        action_url="/career",
        data={"offer_id": str(offer.id), "team_id": str(destination.id)},
    )
    return contract
