from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.enums import AuditAction
from app.models.organization_extra import AuditLog


def write_audit_log(
    db: Session,
    *,
    actor_user_id: uuid.UUID | None,
    action: AuditAction,
    target_type: str,
    target_id: uuid.UUID | None,
    summary: str,
    metadata: dict | None = None,
    ip_hash: str | None = None,
) -> AuditLog:
    row = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        summary=summary,
        metadata_json=metadata or {},
        ip_hash=ip_hash,
    )
    db.add(row)
    return row
