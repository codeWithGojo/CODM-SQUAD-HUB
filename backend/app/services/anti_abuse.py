from __future__ import annotations

import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.security import privacy_hash
from app.models.user import AccountSecurityEvent, User


def request_fingerprints(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    device = request.headers.get("x-device-fingerprint")
    return privacy_hash(ip), privacy_hash(device)


def record_security_event(
    db: Session,
    *,
    request: Request,
    event_type: str,
    user: User | None = None,
    phone: str | None = None,
    risk_score: int = 0,
    details: str | None = None,
) -> AccountSecurityEvent:
    ip_hash, device_hash = request_fingerprints(request)
    if user:
        user.last_known_ip_hash = ip_hash
        if device_hash:
            user.device_fingerprint_hash = device_hash
    row = AccountSecurityEvent(
        user_id=user.id if user else None,
        phone_hash=privacy_hash(phone),
        ip_hash=ip_hash,
        device_fingerprint_hash=device_hash,
        event_type=event_type,
        risk_score=max(0, min(100, risk_score)),
        details=details,
    )
    db.add(row)
    return row
