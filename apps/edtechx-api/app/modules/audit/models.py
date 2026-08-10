"""Audit and security events.

`audit_events` is a compliance artefact, not a debugging tool. The application
role holds no UPDATE or DELETE grant on it (see `app.db.rls.grant_app_role`),
so the code is structurally incapable of rewriting history.

`security_events` is deliberately *not* tenant-owned: the most interesting
security events happen when tenant resolution fails, when a token is presented
on the wrong host, or when nobody is authenticated at all. A table that could
only be written inside a valid tenant context would miss exactly those.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    read_sensitive = "read_sensitive"
    approve = "approve"
    publish = "publish"
    unpublish = "unpublish"
    export = "export"
    login = "login"
    logout = "logout"
    grant = "grant"
    revoke = "revoke"
    configure = "configure"
    rollback = "rollback"


class SecurityEventKind(str, enum.Enum):
    login_failed = "login_failed"
    account_locked = "account_locked"
    tenant_mismatch = "tenant_mismatch"
    unknown_host = "unknown_host"
    refresh_reuse = "refresh_reuse"
    permission_denied = "permission_denied"
    scope_denied = "scope_denied"
    rate_limited = "rate_limited"
    cross_tenant_write_attempt = "cross_tenant_write_attempt"
    break_glass = "break_glass"
    # A background job or system operation reading without a scope, inside one
    # tenant and with a stated reason (`authz.predicates.system_access`).
    # Recorded at `info`: it is legitimate, and it is exactly the thing somebody
    # will need to reconstruct when asking why a job read every student record.
    system_access = "system_access"


class Severity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AuditEvent(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index(
            "ix_audit_events_tenant_resource",
            "tenant_id",
            "resource_type",
            "resource_id",
            "created_at",
        ),
        Index("ix_audit_events_tenant_actor", "tenant_id", "actor_user_id", "created_at"),
    )

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    # Before/after are recorded for academic and financial records, where an
    # auditor needs to see what changed, not merely that something did.
    before: Mapped[dict | None] = mapped_column(JSONB)
    after: Mapped[dict | None] = mapped_column(JSONB)
    reason: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[str | None] = mapped_column(String(64))
    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(512))


class SecurityEvent(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "security_events"
    __table_args__ = (Index("ix_security_events_kind_created", "kind", "created_at"),)

    # Nullable on purpose — see the module docstring.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    kind: Mapped[SecurityEventKind] = mapped_column(
        Enum(SecurityEventKind, name="security_event_kind"), nullable=False
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="security_event_severity"), nullable=False, default=Severity.warning
    )
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ip: Mapped[str | None] = mapped_column(String(45))
    request_id: Mapped[str | None] = mapped_column(String(64))
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
