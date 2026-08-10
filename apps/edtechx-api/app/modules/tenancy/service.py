"""Provisioning a school.

Creating a school touches three modules and two isolation boundaries: the
platform tables that define the tenant, and the tenant-owned tables that only
exist inside its context. Doing that correctly is subtle enough that it must
live in one audited place rather than being reassembled by each caller — which
is exactly what it was doing while it lived in a test fixture.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.core.errors import ConflictingState, ValidationFailed
from app.db.session import bind_tenant, get_session_factory
from app.modules.audit.service import AuditAction
from app.modules.audit.service import record as audit_record
from app.modules.authz.service import grant_role, materialize_system_roles
from app.modules.authz.system_roles import SYSTEM_ROLES
from app.modules.identity.service import create_membership, upsert_user
from app.modules.tenancy.models import (
    DomainKind,
    Tenant,
    TenantDomain,
    TenantStatus,
)

logger = structlog.get_logger(__name__)

# 2-63 characters. The optional-group form of this pattern also admitted a
# single character, which the docstring never promised and DNS convention
# does not want.
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$")

# Slugs that would collide with platform hostnames or read as official.
RESERVED_SLUGS = frozenset(
    {
        "www", "api", "app", "admin", "portal", "status", "help", "support",
        "docs", "mail", "static", "assets", "cdn", "edirasx", "edtechx",
        "platform", "console", "billing", "auth", "login", "test", "staging",
    }
)


@dataclass(frozen=True, slots=True)
class ProvisionedSchool:
    tenant_id: uuid.UUID
    slug: str
    hostname: str
    owner_user_id: uuid.UUID
    owner_membership_id: uuid.UUID
    roles_created: int


def validate_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if not SLUG_PATTERN.match(slug):
        raise ValidationFailed(
            {"slug": "Use 2-63 characters: lowercase letters, numbers, and hyphens."}
        )
    if slug in RESERVED_SLUGS:
        raise ValidationFailed({"slug": "That address is reserved."})
    return slug


def provision_school(
    *,
    slug: str,
    name: str,
    owner_email: str,
    owner_name: str,
    base_domain: str,
    country: str | None = None,
    timezone: str = "UTC",
    locale: str = "en",
    currency: str = "USD",
    owner_password: str | None = None,
    legal_name: str | None = None,
) -> ProvisionedSchool:
    """Create a school, its hostname, its roles, and its owner.

    Two sessions by necessity, not by preference. Tenants and users are platform
    tables written without a tenant context; roles and memberships are
    tenant-owned and must be written *inside* the new tenant's context so the
    row-level policy admits them. Attempting both from one session would either
    fail the policy or require a context switch mid-transaction.

    The tenant is created `provisioning` and only flipped to `active` once its
    roles and owner exist, so a half-built school never resolves for traffic.
    """
    slug = validate_slug(slug)
    if not name.strip():
        raise ValidationFailed({"name": "A school needs a name."})
    hostname = f"{slug}.{base_domain}".lower()

    factory = get_session_factory()
    platform = factory()
    bind_tenant(platform, None)
    try:
        if platform.execute(
            select(Tenant.id).where(Tenant.slug == slug)
        ).scalar_one_or_none():
            raise ConflictingState("A school already uses that address.")
        if platform.execute(
            select(TenantDomain.id).where(TenantDomain.hostname == hostname)
        ).scalar_one_or_none():
            raise ConflictingState("That address is already in use.")

        tenant = Tenant(
            slug=slug,
            name=name.strip(),
            legal_name=(legal_name or "").strip() or None,
            status=TenantStatus.provisioning,
            country=country,
            timezone=timezone,
            locale=locale,
            currency=currency,
        )
        platform.add(tenant)
        platform.flush()

        platform.add(
            TenantDomain(
                tenant_id=tenant.id,
                hostname=hostname,
                kind=DomainKind.subdomain,
                is_primary=True,
            )
        )

        tenant_id = tenant.id
        platform.commit()
    except Exception:
        platform.rollback()
        raise
    finally:
        platform.close()

    # The account is global, so it is created outside any tenant context.
    owner_id = upsert_user(
        email=owner_email, full_name=owner_name, password=owner_password
    )

    scoped = factory()
    bind_tenant(scoped, tenant_id)
    try:
        materialize_system_roles(scoped)
        membership = create_membership(
            scoped, user_id=owner_id, display_name=owner_name
        )
        grant_role(scoped, membership_id=membership.id, role_key="owner")
        audit_record(
            scoped,
            action=AuditAction.create,
            resource_type="tenant",
            resource_id=tenant_id,
            after={"slug": slug, "name": name, "hostname": hostname},
            reason="School provisioned",
            actor_user_id=owner_id,
            actor_membership_id=membership.id,
        )
        membership_id = membership.id
        scoped.commit()
    except Exception:
        scoped.rollback()
        _mark_failed(tenant_id)
        raise
    finally:
        scoped.close()

    activate(tenant_id)
    logger.info("school_provisioned", tenant_id=str(tenant_id), slug=slug)
    return ProvisionedSchool(
        tenant_id=tenant_id,
        slug=slug,
        hostname=hostname,
        owner_user_id=owner_id,
        owner_membership_id=membership_id,
        roles_created=len(SYSTEM_ROLES),
    )


def activate(tenant_id: uuid.UUID) -> None:
    """Flip a fully-built school to active so its hostname begins resolving."""
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        tenant = session.get(Tenant, tenant_id)
        if tenant is None:
            raise ConflictingState("No such school.")
        tenant.status = TenantStatus.active
        tenant.activated_at = datetime.now(UTC)
        session.commit()
    finally:
        session.close()


def _mark_failed(tenant_id: uuid.UUID) -> None:
    """Leave a half-provisioned school suspended rather than resolvable.

    Suspended is the honest state: the record exists and can be inspected or
    retried, but `resolve_from_host` refuses it, so no traffic ever reaches a
    school without roles or an owner.
    """
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        tenant = session.get(Tenant, tenant_id)
        if tenant is not None:
            tenant.status = TenantStatus.suspended
            session.commit()
    except Exception:  # pragma: no cover - cleanup must not mask the real error
        session.rollback()
        logger.error("provisioning_cleanup_failed", tenant_id=str(tenant_id))
    finally:
        session.close()


def suspend(tenant_id: uuid.UUID, reason: str) -> None:
    _set_status(tenant_id, TenantStatus.suspended, reason)


def resume(tenant_id: uuid.UUID, reason: str) -> None:
    _set_status(tenant_id, TenantStatus.active, reason)


def _set_status(tenant_id: uuid.UUID, status: TenantStatus, reason: str) -> None:
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        tenant = session.get(Tenant, tenant_id)
        if tenant is None:
            raise ConflictingState("No such school.")
        before = tenant.status.value
        tenant.status = status
        session.commit()
    finally:
        session.close()

    audit = get_session_factory()()
    bind_tenant(audit, tenant_id)
    try:
        audit_record(
            audit,
            action=AuditAction.configure,
            resource_type="tenant",
            resource_id=tenant_id,
            before={"status": before},
            after={"status": status.value},
            reason=reason,
        )
        audit.commit()
    finally:
        audit.close()
