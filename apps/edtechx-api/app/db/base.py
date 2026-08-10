"""Declarative base, shared mixins, and the tenant-owned model registry.

`TenantOwned` is the marker that drives three separate mechanisms:

  1. the `tenant_id` column and its index,
  2. the row-level security policy emitted by `app.db.rls`,
  3. the generated isolation test suite.

Because all three derive from one marker, adding a new tenant-owned model
automatically gets isolation, a policy, and a test. Nobody has to remember.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def utcnow() -> datetime:
    return datetime.now(UTC)


class UUIDPrimaryKey:
    """UUID keys, not sequential integers.

    Sequential ids leak record volume to anyone who can create one, and invite
    enumeration. Scope checks make enumeration useless, but defence in depth is
    cheap here.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=utcnow,
    )


class SoftDeletable:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


# Every model carrying this mixin, in declaration order. Read by app.db.rls
# and by the generated isolation tests.
TENANT_OWNED_MODELS: list[type[Any]] = []


class TenantOwned:
    """Marks a model as belonging to exactly one tenant."""

    @declared_attr
    def tenant_id(cls) -> Mapped[uuid.UUID]:  # noqa: N805
        return mapped_column(
            PGUUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Abstract intermediates and non-mapped helpers are skipped; only real
        # tables carry a policy and a test.
        if getattr(cls, "__tablename__", None) and not getattr(
            cls, "__abstract__", False
        ):
            TENANT_OWNED_MODELS.append(cls)


def tenant_index(table_name: str, *columns: str, unique: bool = False) -> Index:
    """Build an index led by `tenant_id`.

    Leading with `tenant_id` matches both how RLS filters and how every query
    is actually shaped, so the same index serves both.
    """
    name = f"{'uq' if unique else 'ix'}_{table_name}_tenant_{'_'.join(columns)}"
    return Index(name, "tenant_id", *columns, unique=unique)
