"""Resolve a request's tenant from its host.

Only two sources are ever consulted: the Host header, and the `tid` claim of an
authenticated token. Never a query parameter, a body field, or a client-supplied
header — those are attacker-controlled in exactly the way a tenant identifier
must not be.

When both are present and disagree, the request is refused. That single check
defeats the most plausible real attack: a legitimately-issued token from School
A replayed against School B's hostname.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.tenancy.models import Tenant, TenantDomain, TenantStatus


class TenantResolutionError(Exception):
    """Base class for host-to-tenant failures."""


class UnknownHost(TenantResolutionError):
    pass


class TenantUnavailable(TenantResolutionError):
    def __init__(self, status: TenantStatus) -> None:
        super().__init__(f"Tenant is {status.value}")
        self.status = status


class TenantMismatch(TenantResolutionError):
    """The token's tenant is not the host's tenant."""

    def __init__(self, host_tenant: uuid.UUID, token_tenant: uuid.UUID) -> None:
        super().__init__("Token tenant does not match host tenant")
        self.host_tenant = host_tenant
        self.token_tenant = token_tenant


@dataclass(frozen=True, slots=True)
class ResolvedTenant:
    id: uuid.UUID
    slug: str
    name: str
    status: TenantStatus
    hostname: str
    locale: str
    timezone: str


def normalize_host(raw_host: str | None) -> str:
    """Strip port, trailing dot, and case from a Host header."""
    if not raw_host:
        return ""
    host = raw_host.strip().lower()
    # IPv6 literals arrive bracketed; a port follows the closing bracket.
    if host.startswith("["):
        closing = host.find("]")
        if closing != -1:
            return host[: closing + 1]
    if ":" in host:
        host = host.split(":", 1)[0]
    return host.rstrip(".")


def is_platform_host(host: str) -> bool:
    settings = get_settings()
    return host in {h.lower() for h in settings.platform_hosts}


def subdomain_slug(host: str) -> str | None:
    """Extract a tenant slug from `<slug>.<tenant_base_domain>`."""
    settings = get_settings()
    base = settings.tenant_base_domain.lower()
    if not host.endswith("." + base):
        return None
    label = host[: -(len(base) + 1)]
    # Only a single label. `a.b.edtechx.com` is not a tenant host; treating it
    # as one would let anybody mint plausible-looking hostnames.
    if not label or "." in label:
        return None
    return label


def resolve_from_host(session: Session, raw_host: str | None) -> ResolvedTenant | None:
    """Resolve a tenant from the Host header, or None for a platform host.

    Raises UnknownHost when the host looks tenant-shaped but matches nothing,
    and TenantUnavailable when the school is suspended, archived, or still
    provisioning.
    """
    host = normalize_host(raw_host)
    if not host or is_platform_host(host):
        return None

    stmt = (
        select(Tenant, TenantDomain)
        .join(TenantDomain, TenantDomain.tenant_id == Tenant.id)
        .where(TenantDomain.hostname == host)
        # This table is read to *establish* context, so it carries no RLS
        # policy; the option documents that the absence is intentional.
        .execution_options(skip_tenant_filter=True)
    )
    row = session.execute(stmt).first()

    if row is None:
        slug = subdomain_slug(host)
        if slug is None:
            raise UnknownHost(f"No tenant is configured for host {host!r}")
        tenant = session.execute(
            select(Tenant)
            .where(Tenant.slug == slug)
            .execution_options(skip_tenant_filter=True)
        ).scalar_one_or_none()
        if tenant is None:
            raise UnknownHost(f"No tenant is configured for host {host!r}")
        domain_host = host
    else:
        tenant, domain = row
        if not domain.is_verified:
            raise UnknownHost(f"Host {host!r} is not verified for this school")
        domain_host = domain.hostname

    if tenant.status is not TenantStatus.active:
        raise TenantUnavailable(tenant.status)

    return ResolvedTenant(
        id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        status=tenant.status,
        hostname=domain_host,
        locale=tenant.locale,
        timezone=tenant.timezone,
    )


def assert_token_matches_host(
    host_tenant_id: uuid.UUID | None, token_tenant_id: uuid.UUID | None
) -> uuid.UUID | None:
    """Refuse a token minted for a different school than the host serves."""
    if host_tenant_id is None:
        return token_tenant_id
    if token_tenant_id is None:
        return host_tenant_id
    if host_tenant_id != token_tenant_id:
        raise TenantMismatch(host_tenant_id, token_tenant_id)
    return host_tenant_id
