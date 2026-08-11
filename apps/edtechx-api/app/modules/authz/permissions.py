"""The permission catalogue.

Permissions are `module.resource.action` strings. They are declared here, in
one place, and validated at startup: a role referencing an unknown permission
fails the boot rather than failing a request at 08:15 on results day.

Grants are additive only. There are no deny rules — see ADR-005.
"""

from __future__ import annotations

from typing import Final

# --- actions --------------------------------------------------------------

READ: Final = "read"
WRITE: Final = "write"
CREATE: Final = "create"
DELETE: Final = "delete"
APPROVE: Final = "approve"
PUBLISH: Final = "publish"
EXPORT: Final = "export"
MANAGE: Final = "manage"  # implies every action on the resource

ACTIONS: Final = frozenset(
    {READ, WRITE, CREATE, DELETE, APPROVE, PUBLISH, EXPORT, MANAGE}
)


def _perms(module: str, resource: str, *actions: str) -> set[str]:
    return {f"{module}.{resource}.{action}" for action in actions}


# --- catalogue ------------------------------------------------------------

CATALOGUE: Final[frozenset[str]] = frozenset(
    set()
    # tenancy
    | _perms("tenancy", "tenant", READ, WRITE, MANAGE)
    | _perms("tenancy", "domain", READ, WRITE, MANAGE)
    # identity
    | _perms("identity", "user", READ, CREATE, WRITE, DELETE, MANAGE)
    | _perms("identity", "membership", READ, CREATE, WRITE, DELETE, MANAGE)
    | _perms("identity", "session", READ, DELETE)
    # authz
    | _perms("authz", "role", READ, CREATE, WRITE, DELETE, MANAGE)
    | _perms("authz", "grant", READ, CREATE, DELETE, MANAGE)
    # audit
    | _perms("audit", "event", READ, EXPORT)
    # institution
    | _perms("institution", "campus", READ, WRITE, MANAGE)
    | _perms("institution", "department", READ, WRITE, MANAGE)
    | _perms("institution", "staff", READ, WRITE, MANAGE)
    | _perms("institution", "staff_hr", READ)  # never inherited from admin
    # academics
    | _perms("academics", "year", READ, WRITE, MANAGE)
    | _perms("academics", "term", READ, WRITE, MANAGE)
    | _perms("academics", "level", READ, WRITE, MANAGE)
    | _perms("academics", "class", READ, WRITE, MANAGE)
    | _perms("academics", "subject", READ, WRITE, MANAGE)
    | _perms("academics", "grading_scale", READ, WRITE, MANAGE)
    # people
    # `person` is the human record; `student` is the relationship. Separate
    # permissions because they are separately sensitive: an admissions clerk
    # who may create a person is not thereby entitled to read every learner's
    # enrolment history.
    | _perms("people", "person", READ, CREATE, WRITE, DELETE, EXPORT, MANAGE)
    | _perms("people", "student", READ, CREATE, WRITE, DELETE, EXPORT, MANAGE)
    | _perms("people", "student_sensitive", READ)  # medical / SEN overlay
    | _perms("people", "safeguarding", READ, WRITE)  # named individuals only
    | _perms("people", "guardian", READ, CREATE, WRITE, DELETE, MANAGE)
    | _perms("people", "enrolment", READ, WRITE, MANAGE)
    # Awarding a qualification is the most consequential record the institution
    # writes about a person, and the last one anybody can correct informally.
    | _perms("people", "award", READ, CREATE, APPROVE, EXPORT, MANAGE)
    # attendance
    | _perms("attendance", "session", READ, CREATE, WRITE)
    | _perms("attendance", "mark", READ, WRITE, EXPORT)
    | _perms("attendance", "policy", READ, WRITE, MANAGE)
    # assessment
    | _perms("assessment", "assessment", READ, CREATE, WRITE, DELETE)
    | _perms("assessment", "score", READ, WRITE, EXPORT)
    | _perms("assessment", "result", READ, APPROVE, PUBLISH, EXPORT)
    # research
    # Separate from `academics` because supervising a candidate is not the same
    # authority as configuring a programme, and a graduate school routinely
    # gives one to people it would never give the other. `milestone` carries
    # APPROVE for the same reason `result` does: passing an upgrade viva is a
    # decision somebody is accountable for, not an edit.
    | _perms("research", "supervision", READ, CREATE, WRITE, MANAGE)
    | _perms("research", "milestone", READ, WRITE, APPROVE)
    | _perms("research", "meeting", READ, CREATE)
    # reporting
    # Three document resources rather than one, because a school that lets a
    # form tutor print report cards has not thereby let them print transcripts,
    # and `document` has to exist for the certificates and statements neither
    # word covers. A template declares which of the three governs it.
    | _perms("reporting", "report_card", READ, CREATE, EXPORT)
    | _perms("reporting", "transcript", READ, CREATE, EXPORT)
    | _perms("reporting", "document", READ, CREATE, EXPORT)
    | _perms("reporting", "template", READ, WRITE, PUBLISH)
    # finance
    | _perms("finance", "fee_structure", READ, WRITE, MANAGE)
    | _perms("finance", "invoice", READ, CREATE, WRITE, DELETE, EXPORT)
    | _perms("finance", "payment", READ, CREATE, WRITE, EXPORT)
    | _perms("finance", "report", READ, EXPORT)
    # communication
    | _perms("communication", "announcement", READ, CREATE, WRITE, DELETE, PUBLISH)
    | _perms("communication", "message", READ, CREATE)
    # learning
    | _perms("learning", "course", READ, CREATE, WRITE, DELETE, MANAGE)
    | _perms("learning", "assignment", READ, CREATE, WRITE, DELETE)
    | _perms("learning", "submission", READ, CREATE, WRITE)
    | _perms("learning", "grade", READ, WRITE, PUBLISH)
    # customization
    | _perms("customization", "theme", READ, WRITE, PUBLISH)
    | _perms("customization", "terminology", READ, WRITE, PUBLISH)
    | _perms("customization", "navigation", READ, WRITE, PUBLISH)
    | _perms("customization", "dashboard", READ, WRITE, PUBLISH)
    | _perms("customization", "form", READ, WRITE, PUBLISH)
    # billing
    | _perms("billing", "subscription", READ, WRITE, MANAGE)
    | _perms("billing", "usage", READ, EXPORT)
    # intelligence
    | _perms("intelligence", "assistant", READ, WRITE)
    | _perms("intelligence", "design", READ, WRITE, APPROVE)
    | _perms("intelligence", "provider", READ, WRITE, MANAGE)
    # platform (operator console; never grants tenant content by itself)
    | _perms("platform", "tenant", READ, CREATE, WRITE, MANAGE)
    | _perms("platform", "health", READ)
    | _perms("platform", "break_glass", CREATE)
)


class UnknownPermission(ValueError):
    """Raised when a role references a permission outside the catalogue."""


def validate(permission: str) -> str:
    if permission in CATALOGUE:
        return permission
    if permission.endswith(".*") and any(
        p.startswith(permission[:-1]) for p in CATALOGUE
    ):
        return permission
    raise UnknownPermission(f"{permission!r} is not in the permission catalogue")


def validate_all(permissions: set[str]) -> set[str]:
    for permission in sorted(permissions):
        validate(permission)
    return permissions


def expand(granted: set[str]) -> frozenset[str]:
    """Resolve wildcards and `manage` into the concrete permissions they imply.

    Expansion happens once, when a principal is built, so the hot path is a
    plain set membership test rather than a pattern match per request.
    """
    resolved: set[str] = set()
    for grant in granted:
        if grant.endswith(".*"):
            prefix = grant[:-1]
            resolved.update(p for p in CATALOGUE if p.startswith(prefix))
        elif grant.endswith(f".{MANAGE}"):
            resolved.add(grant)
            prefix = grant.rsplit(".", 1)[0] + "."
            resolved.update(p for p in CATALOGUE if p.startswith(prefix))
        else:
            resolved.add(grant)
    return frozenset(resolved)


def has(permissions: frozenset[str], required: str) -> bool:
    """Test a required permission against an already-expanded set."""
    if required in permissions:
        return True
    # `x.y.manage` satisfies any action on `x.y`, even if `expand` was skipped.
    module_resource = required.rsplit(".", 1)[0]
    return f"{module_resource}.{MANAGE}" in permissions
