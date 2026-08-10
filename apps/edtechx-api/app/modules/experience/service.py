"""Resolving one institution, one person, into one experience.

The whole of EdirasX's flexibility arrives here and has to leave as something
that looks purpose-built. A nursery administrator opens the product and sees
students, classes, attendance, teachers, parents and reports. A university
registrar opens the same deployment and sees faculties, departments,
programmes, levels, courses, credits and semesters. Neither is shown the
other's world, and neither is shown an empty menu item explaining what they are
missing.

That is not a frontend concern. If the interface decides, then every client —
the web app, the phone, a future API consumer, a report generator — decides
again, and they drift. So the answer is computed once, here, from state that is
already authoritative:

    configuration  what this institution actually uses
  + permission     what this person may see
  + entitlement    what this institution has bought
  + role           what this person came here to do
  + terminology    what this institution calls it
  + preference     how this person likes to work

and the client renders what it is given.

The result deliberately carries *reasons*. A capability that is absent because
the institution does not use the concept and one that is absent because the
person may not see it are different facts, and a support conversation that
cannot distinguish them is a support conversation that goes nowhere.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import Principal
from app.modules.academics import service as academics
from app.modules.authz import permissions as perms
from app.modules.billing import service as billing
from app.modules.customization import terminology
from app.modules.experience.capabilities import (
    BY_KEY,
    CAPABILITIES,
    DEFAULT_SHAPE,
    GROUPS,
    ROLE_SHAPES,
    Capability,
    RoleShape,
)
from app.modules.experience.models import InterfaceProfile, UserPreference


class Absence(str):
    """Why something is not here. A string, because that is all it needs to be."""


NOT_CONFIGURED = Absence("not_configured")
NOT_PERMITTED = Absence("not_permitted")
NOT_ENTITLED = Absence("not_entitled")
HIDDEN_BY_INSTITUTION = Absence("hidden_by_institution")


@dataclass(frozen=True, slots=True)
class ResolvedCapability:
    """One thing this person can do, as the interface should present it."""

    key: str
    label: str
    label_plural: str
    group: str
    description: str
    empty_action: str
    is_primary: bool = False
    # Set when the capability is shown as a purchase rather than as a place.
    upgrade_from: str | None = None


@dataclass(frozen=True, slots=True)
class Experience:
    """Everything a client needs to render this person's world, and nothing else."""

    institution: str
    self_description: str
    role_shape: str
    groups: tuple[str, ...]
    capabilities: tuple[ResolvedCapability, ...]
    primary: tuple[ResolvedCapability, ...]
    vocabulary: dict[str, dict[str, str]]
    preferences: dict[str, object]
    # Capability key → why it is not here. Never sent to an ordinary client;
    # this is for support, for tests, and for the setup experience.
    absent: dict[str, str] = field(default_factory=dict)
    is_set_up: bool = False

    def keys(self) -> tuple[str, ...]:
        return tuple(c.key for c in self.capabilities)

    def grouped(self) -> dict[str, tuple[ResolvedCapability, ...]]:
        """Capabilities by group, in the role's own order, empty groups dropped."""
        out: dict[str, tuple[ResolvedCapability, ...]] = {}
        for group in self.groups:
            members = tuple(c for c in self.capabilities if c.group == group)
            if members:
                out[group] = members
        return out


# --- the institution's declared shape --------------------------------------


def profile(db: Session) -> InterfaceProfile | None:
    return db.execute(select(InterfaceProfile)).scalars().first()


def configured_layers(db: Session) -> frozenset[str]:
    """The layers this institution's world contains.

    What exists, plus what has been declared, minus what has been suppressed —
    and suppression cannot remove a layer that has rows, because data that
    exists must stay reachable. An institution can always show a layer it does
    not yet use, and can never hide one it is actively using.
    """
    populated = academics.populated_layers(db)
    declared = profile(db)
    if declared is None:
        return populated
    return frozenset(
        (populated | set(declared.declared_layers or ()))
        - (set(declared.suppressed_layers or ()) - populated)
    )


def declare_layers(
    db: Session,
    *,
    layers: list[str],
    membership_id: uuid.UUID | None = None,
    self_description: str | None = None,
) -> InterfaceProfile:
    """An institution saying what it intends to use, before it has used it.

    The setup experience writes this. Validated against the known layers so a
    typo produces an error at configuration time rather than a concept that
    never appears and nobody can explain.
    """
    unknown = sorted(set(layers) - set(academics.LAYER_TABLES))
    if unknown:
        raise ValueError(f"Not layers of the academic model: {unknown}")
    existing = profile(db)
    if existing is None:
        existing = InterfaceProfile(declared_layers=list(layers))
        db.add(existing)
    else:
        existing.declared_layers = list(layers)
    if self_description is not None:
        existing.self_description = self_description
    existing.updated_by_membership_id = membership_id
    db.flush()
    return existing


def suppress_layers(
    db: Session, *, layers: list[str], membership_id: uuid.UUID | None = None
) -> InterfaceProfile:
    existing = profile(db) or InterfaceProfile(declared_layers=[])
    if existing.id is None:
        db.add(existing)
    existing.suppressed_layers = list(layers)
    existing.updated_by_membership_id = membership_id
    db.flush()
    return existing


# --- the person's own choices ----------------------------------------------


def preferences(db: Session, membership_id: uuid.UUID | None) -> UserPreference | None:
    if membership_id is None:
        return None
    return db.execute(
        select(UserPreference).where(UserPreference.membership_id == membership_id)
    ).scalars().first()


def set_preferences(
    db: Session, membership_id: uuid.UUID, **values: object
) -> UserPreference:
    existing = preferences(db, membership_id)
    if existing is None:
        existing = UserPreference(membership_id=membership_id)
        db.add(existing)
    for key, value in values.items():
        if hasattr(existing, key) and value is not None:
            setattr(existing, key, value)
    db.flush()
    return existing


# --- resolution -------------------------------------------------------------


def _shape_for(role_keys: list[str]) -> RoleShape:
    """The most specific role template this person matches.

    A person holding several roles gets the one that leads: a head of department
    who also teaches opens the product as a head of department, because that is
    the job whose questions the others do not answer. A school's invented role
    matches nothing and gets a sensible default rather than an error.
    """
    for key in ("owner", "principal", "admin", "registrar", "bursar",
                "head_of_department", "admissions_officer", "form_tutor",
                "teacher", "guardian", "student"):
        if key in role_keys:
            return ROLE_SHAPES[key]
    return DEFAULT_SHAPE


def _label(capability: Capability, words: terminology.Vocabulary) -> tuple[str, str]:
    if capability.term is None:
        return _humanise(capability.key), _humanise(capability.key)
    return (
        words.title(capability.term),
        words.title(capability.term, plural=True),
    )


def _humanise(key: str) -> str:
    tail = key.split(".")[-1].replace("_", " ")
    return tail[:1].upper() + tail[1:]


def _admits(capability: Capability, layers: frozenset[str]) -> bool:
    """Whether this institution's world contains the concept at all."""
    if not capability.layers:
        return True
    return any(layer in layers for layer in capability.layers)


def resolve(
    db: Session,
    principal: Principal | None,
    *,
    role_keys: list[str] | None = None,
    institution: str = "",
) -> Experience:
    """Compute one person's experience of one institution.

    Four questions per capability, asked in an order chosen so the *reason* an
    absence is recorded is the most useful one. Configuration comes first
    because "this institution does not do that" explains an absence completely
    and makes the other three moot; permission next because existence is
    sensitive; entitlement last among the absolute checks because it is the only
    one that can turn into an offer rather than a silence.
    """
    words = terminology.resolve(db)
    layers = configured_layers(db)
    declared = profile(db)
    hidden = set((declared.hidden_capabilities if declared else None) or ())
    held = principal.permissions if principal else frozenset()
    shape = _shape_for(role_keys or [])
    may_purchase = perms.has(held, "billing.subscription.write") if principal else False

    resolved: list[ResolvedCapability] = []
    absent: dict[str, str] = {}

    for capability in CAPABILITIES:
        if not _admits(capability, layers):
            absent[capability.key] = NOT_CONFIGURED
            continue
        if capability.key in hidden:
            absent[capability.key] = HIDDEN_BY_INSTITUTION
            continue
        if capability.permission and not perms.has(held, capability.permission):
            absent[capability.key] = NOT_PERMITTED
            continue

        upgrade_from: str | None = None
        if capability.feature:
            verdict = billing.feature(db, capability.feature)
            if not verdict:
                # An offer, but only to somebody who could act on it. A padlock a
                # teacher cannot open is an advertisement placed in their way.
                if capability.offer_upgrade and may_purchase:
                    upgrade_from = verdict.plan_key or "current plan"
                else:
                    absent[capability.key] = NOT_ENTITLED
                    continue

        label, plural = _label(capability, words)
        resolved.append(
            ResolvedCapability(
                key=capability.key,
                label=label,
                label_plural=plural,
                group=capability.group,
                description=capability.description,
                empty_action=capability.empty_action.replace("{term}", label.lower()),
                is_primary=capability.key in shape.primary,
                upgrade_from=upgrade_from,
            )
        )

    order = {key: index for index, key in enumerate(shape.groups)}
    catalogue_order = {c.key: index for index, c in enumerate(CAPABILITIES)}
    resolved.sort(
        key=lambda c: (
            order.get(c.group, len(order)),
            0 if c.is_primary else 1,
            catalogue_order[c.key],
        )
    )
    groups = tuple(
        group for group in (*shape.groups, *GROUPS)
        if any(c.group == group for c in resolved)
    )
    # Deduplicate while preserving the role's order.
    seen: list[str] = []
    for group in groups:
        if group not in seen:
            seen.append(group)

    stored = preferences(db, principal.membership_id if principal else None)
    return Experience(
        institution=institution,
        self_description=(declared.self_description if declared else None) or "",
        role_shape=shape.role,
        groups=tuple(seen),
        capabilities=tuple(resolved),
        primary=tuple(c for c in resolved if c.is_primary),
        vocabulary=words.terms,
        preferences={
            "colour_scheme": stored.colour_scheme if stored else "system",
            "density": stored.density if stored else "comfortable",
            "reduce_motion": stored.reduce_motion if stored else False,
            "locale": (stored.locale if stored else None) or words.locale,
            "pinned": list(stored.pinned) if stored else [],
        },
        absent=absent,
        is_set_up=bool(declared and declared.is_set_up),
    )


def capability_is_present(experience: Experience, key: str) -> bool:
    if key not in BY_KEY:
        raise KeyError(f"{key!r} is not a capability")
    return key in experience.keys()
