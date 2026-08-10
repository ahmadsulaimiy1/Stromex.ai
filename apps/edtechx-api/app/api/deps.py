"""Request dependencies: the enforced steps of the request lifecycle.

Steps 2, 5, 6, and 8 of EDTECHX_ARCHITECTURE.md §5 live here. They are
dependencies rather than middleware so that FastAPI's own dependency graph
makes them visible on every route signature — a route that lacks them is
obvious in review, and `test_route_coverage` fails the build if one slips
through.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.core.context import Principal, set_principal, set_tenant
from app.core.security import InvalidToken, decode_access_token, is_elevated
from app.db.session import bind_tenant, get_session_factory
from app.modules.audit.models import SecurityEvent, SecurityEventKind, Severity
from app.modules.authz import permissions as perms
from app.modules.authz.models import MembershipRole
from app.modules.authz.scopes import ScopeSet, parse_scopes
from app.modules.identity.models import Membership, MembershipStatus, User, UserStatus
from app.modules.tenancy.resolver import (
    ResolvedTenant,
    TenantMismatch,
    TenantUnavailable,
    UnknownHost,
    assert_token_matches_host,
    resolve_from_host,
)

logger = structlog.get_logger(__name__)


def _record_security_event(
    kind: SecurityEventKind,
    *,
    request: Request,
    tenant_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    severity: Severity = Severity.warning,
    **detail: object,
) -> None:
    """Write a security event on its own session.

    Deliberately separate from the request's session: the request is about to
    be rejected and rolled back, and the record of the attempt must survive
    that.
    """
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
                ip=request.client.host if request.client else None,
                request_id=getattr(request.state, "request_id", None),
                occurred_at=datetime.now(UTC),
            )
        )
        session.commit()
    except Exception:  # pragma: no cover - never let logging break a request
        session.rollback()
        logger.warning("security_event_write_failed", kind=kind.value)
    finally:
        session.close()


# --- step 2: tenant from host ---------------------------------------------


def get_tenant_context(request: Request) -> ResolvedTenant | None:
    """Resolve the tenant from the Host header. Never from client input."""
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        resolved = resolve_from_host(session, request.headers.get("host"))
    except UnknownHost as exc:
        _record_security_event(
            SecurityEventKind.unknown_host,
            request=request,
            host=request.headers.get("host"),
        )
        raise errors.TenantNotResolved() from exc
    except TenantUnavailable as exc:
        raise errors.TenantSuspended() from exc
    finally:
        session.close()

    request.state.tenant_id = resolved.id if resolved else None
    set_tenant(resolved.id if resolved else None)
    return resolved


TenantContext = Annotated[ResolvedTenant | None, Depends(get_tenant_context)]


# --- step 6: a session bound to that tenant -------------------------------


def get_db(tenant: TenantContext) -> Iterator[Session]:
    session = get_session_factory()()
    bind_tenant(session, tenant.id if tenant else None)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


DbSession = Annotated[Session, Depends(get_db)]


# --- steps 4 and 5: authenticate, and check the token against the host ----


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def get_optional_principal(
    request: Request, tenant: TenantContext, db: DbSession
) -> Principal | None:
    token = _bearer_token(request)
    if token is None:
        return None

    try:
        claims = decode_access_token(token)
    except InvalidToken as exc:
        raise errors.NotAuthenticated() from exc

    # Step 5. A token minted for one school must not work on another's host.
    try:
        assert_token_matches_host(tenant.id if tenant else None, claims.tenant_id)
    except TenantMismatch as exc:
        _record_security_event(
            SecurityEventKind.tenant_mismatch,
            request=request,
            tenant_id=exc.host_tenant,
            user_id=claims.user_id,
            severity=Severity.critical,
            token_tenant=exc.token_tenant,
        )
        raise errors.TenantContextMismatch() from exc

    membership = db.get(Membership, claims.membership_id)
    if membership is None or membership.status is not MembershipStatus.active:
        raise errors.NotAuthenticated()
    if membership.user_id != claims.user_id:
        # The token's user and membership disagree: a forged or stale pairing.
        _record_security_event(
            SecurityEventKind.permission_denied,
            request=request,
            tenant_id=claims.tenant_id,
            user_id=claims.user_id,
            severity=Severity.critical,
            reason="membership_user_mismatch",
        )
        raise errors.NotAuthenticated()

    user = db.get(User, claims.user_id)
    if user is None or user.status is not UserStatus.active:
        raise errors.NotAuthenticated()

    granted, scopes = _load_grants(db, membership.id)
    principal = Principal(
        user_id=user.id,
        membership_id=membership.id,
        tenant_id=claims.tenant_id,
        permissions=granted,
        scopes=tuple(s.kind.value for s in scopes.scopes),
        session_id=claims.session_id,
        authenticated_at=claims.authenticated_at.timestamp(),
        is_platform_operator=user.is_platform_operator,
    )
    set_principal(principal)
    request.state.principal = principal
    return principal


def _load_grants(db: Session, membership_id: uuid.UUID) -> tuple[frozenset[str], ScopeSet]:
    now = datetime.now(UTC)
    grants = (
        db.execute(select(MembershipRole).where(MembershipRole.membership_id == membership_id))
        .scalars()
        .all()
    )
    effective = [g for g in grants if g.is_effective(now)]
    granted: set[str] = set()
    for grant in effective:
        granted |= grant.role.permission_keys
    return perms.expand(granted), parse_scopes([g.scope for g in effective])


OptionalPrincipal = Annotated[Principal | None, Depends(get_optional_principal)]


def get_principal(principal: OptionalPrincipal) -> Principal:
    if principal is None:
        raise errors.NotAuthenticated()
    return principal


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]


# --- step 8: permission --------------------------------------------------


class RequirePermission:
    """Route dependency asserting a permission before the handler runs."""

    def __init__(self, permission: str, *, elevated: bool = False) -> None:
        # Validated at import time, so a typo fails the boot, not a request.
        perms.validate(permission)
        self.permission = permission
        self.elevated = elevated

    def __call__(self, request: Request, principal: CurrentPrincipal) -> Principal:
        if not perms.has(principal.permissions, self.permission):
            _record_security_event(
                SecurityEventKind.permission_denied,
                request=request,
                tenant_id=principal.tenant_id,
                user_id=principal.user_id,
                severity=Severity.info,
                permission=self.permission,
            )
            raise errors.PermissionDenied()
        if self.elevated and not is_elevated(
            datetime.fromtimestamp(principal.authenticated_at, UTC)
        ):
            raise errors.ElevationRequired()
        return principal
