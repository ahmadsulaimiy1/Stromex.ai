"""Scopes — the attribute half of the authorization model.

A scope answers "which resources?", where a permission answers "which action?".
Every scope must be expressible as a SQL predicate, not merely as a yes/no test
on an already-loaded row. That constraint is deliberate: if scope could only be
checked after loading, list endpoints would leak by row count and pagination
would become an oracle for records the user may not see.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


class ScopeKind(str, enum.Enum):
    tenant = "tenant"
    # Three words for a position in the same tree. ADR-024 made campus, faculty,
    # school and department one `academic_units` table, so all three resolve
    # through it — including descendants, because a head of faculty who could
    # not see the departments inside it would hold a scope that means nothing.
    campus = "campus"
    department = "department"
    academic_unit = "academic_unit"
    programme = "programme"
    cohort = "cohort"
    level = "level"
    klass = "class"
    subject = "subject"
    taught_by_self = "taught_by_self"
    own_children = "own_children"
    self_only = "self"


# The kinds that name a position in the academic-unit tree. Kept as one set so
# a resource's plan writes the subtree clause once rather than three times.
UNIT_KINDS: frozenset[ScopeKind] = frozenset(
    {ScopeKind.campus, ScopeKind.department, ScopeKind.academic_unit}
)


# Scopes that name a set of resource ids.
ID_BEARING: frozenset[ScopeKind] = frozenset(
    {
        ScopeKind.campus,
        ScopeKind.department,
        ScopeKind.academic_unit,
        ScopeKind.programme,
        ScopeKind.cohort,
        ScopeKind.level,
        ScopeKind.klass,
        ScopeKind.subject,
    }
)


class InvalidScope(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Scope:
    kind: ScopeKind
    ids: frozenset[uuid.UUID] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.kind in ID_BEARING and not self.ids:
            raise InvalidScope(f"scope {self.kind.value!r} requires at least one id")
        if self.kind not in ID_BEARING and self.ids:
            raise InvalidScope(f"scope {self.kind.value!r} does not take ids")

    @property
    def is_unrestricted(self) -> bool:
        return self.kind == ScopeKind.tenant

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": self.kind.value}
        if self.ids:
            payload["ids"] = sorted(str(i) for i in self.ids)
        return payload

    @classmethod
    def from_json(cls, payload: dict[str, Any] | None) -> Scope:
        if not payload:
            return cls(ScopeKind.tenant)
        raw_kind = payload.get("kind")
        try:
            kind = ScopeKind(raw_kind)
        except ValueError as exc:
            raise InvalidScope(f"unknown scope kind {raw_kind!r}") from exc
        raw_ids = payload.get("ids") or []
        try:
            ids = frozenset(uuid.UUID(str(i)) for i in raw_ids)
        except (ValueError, AttributeError) as exc:
            raise InvalidScope("scope ids must be uuids") from exc
        return cls(kind, ids)


@dataclass(frozen=True, slots=True)
class ScopeSet:
    """The union of every scope a principal holds for a given permission.

    Union, not intersection: holding `head_of_department` for two departments
    must widen reach across both, which is how schools actually work.
    """

    scopes: tuple[Scope, ...] = ()

    @classmethod
    def of(cls, scopes: Iterable[Scope]) -> ScopeSet:
        return cls(tuple(scopes))

    @property
    def is_unrestricted(self) -> bool:
        return any(s.is_unrestricted for s in self.scopes)

    def kinds(self) -> frozenset[ScopeKind]:
        return frozenset(s.kind for s in self.scopes)

    def ids_for(self, kind: ScopeKind) -> frozenset[uuid.UUID]:
        result: set[uuid.UUID] = set()
        for scope in self.scopes:
            if scope.kind == kind:
                result |= scope.ids
        return frozenset(result)

    def allows_all(self) -> bool:
        return self.is_unrestricted

    def __bool__(self) -> bool:
        return bool(self.scopes)


def parse_scopes(payloads: Iterable[dict[str, Any] | None]) -> ScopeSet:
    return ScopeSet.of(Scope.from_json(p) for p in payloads)


def scopes_for(principal: object, permission: str) -> ScopeSet:
    """The scopes a principal holds **for one permission**.

    The single most important function in this module, and the one whose
    absence was a defect. A principal's scopes are not a property of the
    principal; they are a property of each grant. Somebody who is a teacher
    (students, scoped to what they teach) and also a communications officer
    (announcements, school-wide) holds a `tenant` scope — and reading it as
    "this person is unrestricted" would hand them every student record in the
    school on the strength of a permission to write notices.

    So only the grants that actually confer `permission` contribute, and their
    scopes are unioned. A principal holding nothing relevant gets an empty set,
    which every predicate reads as *no rows* rather than as *all rows*.

    Expansion matters here: a grant of `people.student.manage` confers
    `people.student.read`, so its scope must apply to a read.
    """
    from app.modules.authz import permissions as perms

    grants = getattr(principal, "grants", ()) if principal is not None else ()
    relevant: list[Scope] = []
    for grant in grants:
        if not perms.has(perms.expand(set(grant.permissions)), permission):
            continue
        try:
            relevant.append(
                Scope(ScopeKind(grant.scope_kind), frozenset(grant.scope_ids))
            )
        except (ValueError, InvalidScope):
            # A grant whose scope cannot be understood confers nothing. Failing
            # closed here is the difference between a corrupted row costing a
            # person some access and it costing a school its confidentiality.
            continue
    return ScopeSet.of(relevant)
