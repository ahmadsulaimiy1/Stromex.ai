"""Writing to the audit log.

Every module records audit events, which would make `audit.models` the one
import that legitimately crosses every boundary. It does not: modules call this
function instead, and the model stays private to its own module — the same rule
as everywhere else, with no exception carved out for the cross-cutting case.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.orm import Session

from app.core.context import get_principal, get_request_id
from app.db.session import bind_tenant, get_session_factory
from app.modules.audit.models import (
    AuditAction,
    AuditEvent,
    SecurityEvent,
    SecurityEventKind,
    Severity,
)

logger = structlog.get_logger(__name__)

# Re-exported deliberately. `AuditAction`, `SecurityEventKind`, and `Severity`
# are the vocabulary every module needs in order to *call* this service; they
# are not table definitions. Exposing them here keeps the boundary rule intact
# without carving out an exception for the one cross-cutting concern.
__all__ = [
    "AuditAction",
    "SecurityEventKind",
    "Severity",
    "record",
    "record_security",
]


def record(
    db: Session,
    *,
    action: AuditAction,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
    actor_user_id: uuid.UUID | None = None,
    actor_membership_id: uuid.UUID | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Add an audit event to the caller's transaction.

    Deliberately joins the caller's transaction rather than opening its own: an
    audit entry that survives a rolled-back change would be a record of
    something that never happened.
    """
    principal = get_principal()
    db.add(
        AuditEvent(
            actor_user_id=actor_user_id or (principal.user_id if principal else None),
            actor_membership_id=actor_membership_id
            or (principal.membership_id if principal else None),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before=before,
            after=after,
            reason=reason,
            request_id=get_request_id(),
            ip=ip,
            user_agent=(user_agent or "")[:512] or None,
        )
    )


def record_security(
    kind: SecurityEventKind,
    *,
    tenant_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    severity: Severity = Severity.warning,
    ip: str | None = None,
    **detail: object,
) -> None:
    """Record a security event on its own session.

    The opposite choice from `record`, for the opposite reason: security events
    describe attempts that are usually about to be rejected and rolled back.
    The record of the attempt must outlive the rejection.
    """
    from datetime import UTC, datetime

    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        session.add(
            SecurityEvent(
                tenant_id=tenant_id,
                user_id=user_id,
                kind=kind,
                severity=severity,
                detail={k: str(v) for k, v in detail.items()},
                ip=ip,
                request_id=get_request_id(),
                occurred_at=datetime.now(UTC),
            )
        )
        session.commit()
    except Exception:  # pragma: no cover - logging must never break a request
        session.rollback()
        logger.warning("security_event_write_failed", kind=kind.value)
    finally:
        session.close()
