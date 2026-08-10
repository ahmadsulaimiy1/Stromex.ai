"""Roles and grants.

System roles are *templates in code*, materialized as ordinary tenant-owned
rows when a school is provisioned. That keeps two properties at once: the
platform can reason about `role.key == "teacher"` across every school, and a
school can freely edit, clone, or ignore what it was given.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class Role(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_roles_tenant_id_key"),
    )

    key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # System roles may be edited but not deleted, and their key is stable.
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    permissions: Mapped[list[RolePermission]] = relationship(
        back_populates="role", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def permission_keys(self) -> set[str]:
        return {p.permission for p in self.permissions}

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Role {self.key}>"


class RolePermission(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "role_id", "permission", name="uq_role_permissions_role_permission"
        ),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    permission: Mapped[str] = mapped_column(String(96), nullable=False)

    role: Mapped[Role] = relationship(back_populates="permissions")


class MembershipRole(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A role held by a membership, narrowed by a scope.

    `expires_at` is what makes cover arrangements safe: a teacher covering a
    colleague for a fortnight gets a grant that lapses on its own, rather than
    one that depends on somebody remembering to revoke it.
    """

    __tablename__ = "membership_roles"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "membership_id",
            "role_id",
            name="uq_membership_roles_membership_role",
        ),
    )

    membership_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    # {"kind": "taught_by_self"} | {"kind": "department", "ids": [...]} | ...
    scope: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    granted_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # One-directional by design: authz depends on identity, never the reverse.
    # Referenced by name so this module does not import identity's models.
    #
    # `viewonly` because both foreign keys are tenant-scoped — they reference
    # `(tenant_id, id)` so that one tenant cannot point at another's row — which
    # means both relationships nominally write `tenant_id`. That column belongs
    # to `TenantOwned` and is stamped from the request context; no relationship
    # owns it. Declaring these read-only says so, rather than leaving two
    # relationships quietly competing to set the same value.
    membership: Mapped[object] = relationship(
        "Membership", lazy="selectin", viewonly=True
    )
    role: Mapped[Role] = relationship(lazy="selectin", viewonly=True)

    def is_effective(self, now: datetime) -> bool:
        return self.expires_at is None or self.expires_at > now
