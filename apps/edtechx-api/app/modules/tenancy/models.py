"""Tenancy: the school, and the hostnames it answers on."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Timestamped, UUIDPrimaryKey


class TenantStatus(str, enum.Enum):
    provisioning = "provisioning"
    active = "active"
    suspended = "suspended"
    archived = "archived"


class DomainKind(str, enum.Enum):
    subdomain = "subdomain"
    custom = "custom"


class Tenant(UUIDPrimaryKey, Timestamped, Base):
    """A school.

    Deliberately *not* TenantOwned: this table defines tenants rather than
    belonging to one, so it carries no RLS policy. Access to it is guarded by
    permission alone, and only the platform console can list it.
    """

    __tablename__ = "tenants"

    slug: Mapped[str] = mapped_column(String(63), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, name="tenant_status"),
        nullable=False,
        default=TenantStatus.provisioning,
    )
    # Declared, never geolocated — see EDTECHX_DECISIONS.md ADR-010.
    country: Mapped[str | None] = mapped_column(String(2))
    region: Mapped[str | None] = mapped_column(String(32))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    domains: Mapped[list[TenantDomain]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )

    @property
    def is_usable(self) -> bool:
        return self.status == TenantStatus.active

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Tenant {self.slug} {self.status.value}>"


class TenantDomain(UUIDPrimaryKey, Timestamped, Base):
    """A hostname that resolves to a tenant.

    Also not TenantOwned, and for a specific reason: this table is read *to
    establish* the tenant context, before any context exists. A row-level
    policy here would make host resolution impossible. It is therefore
    read-only on the request path and writable only through the tenancy
    service, which checks permissions itself.
    """

    __tablename__ = "tenant_domains"
    __table_args__ = (UniqueConstraint("hostname", name="uq_tenant_domains_hostname"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hostname: Mapped[str] = mapped_column(String(253), nullable=False)
    kind: Mapped[DomainKind] = mapped_column(
        Enum(DomainKind, name="tenant_domain_kind"),
        nullable=False,
        default=DomainKind.subdomain,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped[Tenant] = relationship(back_populates="domains")

    @property
    def is_verified(self) -> bool:
        # Subdomains under our own base domain are ours to assert; custom
        # domains must prove control before they can carry a school's identity.
        return self.kind == DomainKind.subdomain or self.verified_at is not None
