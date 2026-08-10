"""Roles and grants, as a service other modules may call."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.authz.models import MembershipRole, Role, RolePermission
from app.modules.authz.scopes import Scope
from app.modules.authz.system_roles import SYSTEM_ROLES, SYSTEM_ROLES_BY_KEY


def materialize_system_roles(db: Session) -> int:
    """Create this school's copy of every system role template.

    Templates live in code so the platform can reason about `role.key`; the
    rows live in the tenant so a school can edit them freely. Idempotent, so
    re-running it after adding a template backfills rather than duplicating.
    """
    existing = set(db.execute(select(Role.key)).scalars().all())
    created = 0
    for template in SYSTEM_ROLES:
        if template.key in existing:
            continue
        role = Role(
            key=template.key,
            name=template.name,
            description=template.description,
            is_system=True,
        )
        db.add(role)
        db.flush()
        for permission in sorted(template.permissions):
            db.add(RolePermission(role_id=role.id, permission=permission))
        created += 1
    return created


def grant_role(
    db: Session,
    *,
    membership_id: uuid.UUID,
    role_key: str,
    scope: Scope | None = None,
    granted_by_membership_id: uuid.UUID | None = None,
    expires_at: datetime | None = None,
) -> MembershipRole:
    role = db.execute(select(Role).where(Role.key == role_key)).scalar_one_or_none()
    if role is None:
        raise LookupError(f"No role {role_key!r} in this school")
    template = SYSTEM_ROLES_BY_KEY.get(role_key)
    effective = scope or (template.default_scope if template else None)
    grant = MembershipRole(
        membership_id=membership_id,
        role_id=role.id,
        scope=effective.to_json() if effective else {},
        granted_by_membership_id=granted_by_membership_id,
        granted_at=datetime.now(UTC),
        expires_at=expires_at,
    )
    db.add(grant)
    db.flush()
    return grant


def role_id_for(db: Session, role_key: str) -> uuid.UUID | None:
    return db.execute(select(Role.id).where(Role.key == role_key)).scalar_one_or_none()
