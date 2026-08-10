"""The one call a client makes before rendering anything.

Returns this person's world: the navigation, in their institution's own words,
containing only what their institution actually uses, only what they are
permitted to see, and only what the plan includes — ordered by what they came
here to do.

Deliberately one call rather than several. A client that assembles its own
navigation from four endpoints is a client that makes its own decisions about
what to show, and the moment there are two clients they disagree. The server
decides; the client renders.

`absent` is returned only to somebody who could act on it. A registrar setting
the institution up needs to know that programmes are missing because nobody has
configured them; a parent needs no explanation of a concept that has nothing to
do with them.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentPrincipal, DbSession, TenantContext
from app.modules.authz import permissions as perms
from app.modules.experience import service as experience

router = APIRouter(tags=["experience"])


class CapabilityOut(BaseModel):
    key: str
    label: str
    label_plural: str
    group: str
    description: str
    empty_action: str
    is_primary: bool
    upgrade_from: str | None


class ExperienceOut(BaseModel):
    institution: str
    self_description: str
    role_shape: str
    groups: list[str]
    capabilities: list[CapabilityOut]
    primary: list[str]
    vocabulary: dict[str, dict[str, str]]
    preferences: dict
    absent: dict[str, str] | None
    is_set_up: bool


@router.get(
    "/experience",
    response_model=ExperienceOut,
    summary="This person's world, in this institution's own words",
)
def read_experience(
    db: DbSession, principal: CurrentPrincipal, tenant: TenantContext
) -> ExperienceOut:
    from app.modules.authz.models import MembershipRole

    role_keys = [
        grant.role.key
        for grant in db.query(MembershipRole)
        .filter(MembershipRole.membership_id == principal.membership_id)
        .all()
    ]
    resolved = experience.resolve(
        db,
        principal,
        role_keys=role_keys,
        institution=tenant.name if tenant else "",
    )
    explains = perms.has(principal.permissions, "tenancy.tenant.write")
    return ExperienceOut(
        institution=resolved.institution,
        self_description=resolved.self_description,
        role_shape=resolved.role_shape,
        groups=list(resolved.groups),
        capabilities=[
            CapabilityOut(
                key=c.key, label=c.label, label_plural=c.label_plural, group=c.group,
                description=c.description, empty_action=c.empty_action,
                is_primary=c.is_primary, upgrade_from=c.upgrade_from,
            )
            for c in resolved.capabilities
        ],
        primary=[c.key for c in resolved.primary],
        vocabulary=resolved.vocabulary,
        preferences=resolved.preferences,
        absent=dict(resolved.absent) if explains else None,
        is_set_up=resolved.is_set_up,
    )
