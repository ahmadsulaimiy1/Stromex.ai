"""Permission catalogue, expansion, and scope parsing."""

from __future__ import annotations

import uuid

import pytest

from app.modules.authz import permissions as perms
from app.modules.authz.scopes import InvalidScope, Scope, ScopeKind, ScopeSet, parse_scopes
from app.modules.authz.system_roles import SYSTEM_ROLES, SYSTEM_ROLES_BY_KEY, validate_catalogue

# --- catalogue ------------------------------------------------------------


def test_every_system_role_uses_known_permissions() -> None:
    """A role referencing an unknown permission must fail at boot, not at 08:15."""
    validate_catalogue()


def test_unknown_permission_is_rejected() -> None:
    with pytest.raises(perms.UnknownPermission):
        perms.validate("people.student.teleport")


def test_catalogue_entries_are_well_formed() -> None:
    for permission in perms.CATALOGUE:
        module, resource, action = permission.split(".")
        assert module and resource
        assert action in perms.ACTIONS, f"{permission} uses an undeclared action"


def test_no_negative_permissions_exist() -> None:
    """ADR-005: grants are additive; denial is absence."""
    assert not any(p.startswith("!") or ".deny" in p for p in perms.CATALOGUE)


# --- expansion ------------------------------------------------------------


def test_manage_expands_to_every_action_on_the_resource() -> None:
    expanded = perms.expand({"people.student.manage"})
    assert "people.student.read" in expanded
    assert "people.student.delete" in expanded
    assert "people.student.export" in expanded
    # ...and does not leak into a neighbouring resource.
    assert "people.guardian.read" not in expanded


def test_module_wildcard_expands_within_its_module_only() -> None:
    expanded = perms.expand({"finance.*"})
    assert "finance.invoice.read" in expanded
    assert all(p.startswith("finance.") for p in expanded)


def test_manage_does_not_leak_across_a_shared_prefix() -> None:
    """`people.student.manage` must not confer `people.student_sensitive.read`.

    Prefix matching is the obvious implementation and the obvious bug: medical
    and SEN notes sit behind a separate overlay permission precisely so that a
    broad grant cannot reach them.
    """
    expanded = perms.expand({"people.student.manage"})
    assert "people.student_sensitive.read" not in expanded


def test_has_accepts_manage_as_a_substitute() -> None:
    granted = frozenset({"finance.invoice.manage"})
    assert perms.has(granted, "finance.invoice.write")
    assert not perms.has(granted, "finance.payment.write")


# --- system roles ---------------------------------------------------------


def test_teacher_cannot_publish_results() -> None:
    """Publication is a deliberate institutional act, not a teaching one."""
    teacher = SYSTEM_ROLES_BY_KEY["teacher"]
    expanded = perms.expand(set(teacher.permissions))
    assert "assessment.result.publish" not in expanded
    assert "assessment.result.approve" not in expanded


def test_teacher_defaults_to_their_own_classes() -> None:
    assert SYSTEM_ROLES_BY_KEY["teacher"].default_scope.kind is ScopeKind.taught_by_self


def test_guardian_is_scoped_to_own_children() -> None:
    guardian = SYSTEM_ROLES_BY_KEY["guardian"]
    assert guardian.default_scope.kind is ScopeKind.own_children
    expanded = perms.expand(set(guardian.permissions))
    assert "people.student.write" not in expanded
    assert "assessment.score.write" not in expanded


def test_student_cannot_read_other_students() -> None:
    student = SYSTEM_ROLES_BY_KEY["student"]
    assert student.default_scope.kind is ScopeKind.self_only
    expanded = perms.expand(set(student.permissions))
    assert "people.guardian.read" not in expanded
    assert "assessment.score.write" not in expanded


def test_no_tenant_role_carries_platform_permissions() -> None:
    """A school administrator is not a platform operator, however senior."""
    for template in SYSTEM_ROLES:
        expanded = perms.expand(set(template.permissions))
        offending = {p for p in expanded if p.startswith("platform.")}
        assert not offending, f"{template.key} carries platform permissions: {offending}"


def test_safeguarding_is_never_granted_by_a_broad_role() -> None:
    """Safeguarding access is by named individual only — never inherited."""
    for key in ("owner", "admin", "registrar", "principal", "teacher"):
        expanded = perms.expand(set(SYSTEM_ROLES_BY_KEY[key].permissions))
        assert not any(p.startswith("people.safeguarding") for p in expanded), (
            f"{key} inherits safeguarding access"
        )


def test_admin_cannot_read_hr_records_or_change_billing() -> None:
    expanded = perms.expand(set(SYSTEM_ROLES_BY_KEY["admin"].permissions))
    assert "institution.staff_hr.read" not in expanded
    assert not any(p.startswith("billing.") for p in expanded)


def test_privileged_roles_require_mfa() -> None:
    for key in ("owner", "admin", "principal", "bursar"):
        assert SYSTEM_ROLES_BY_KEY[key].requires_mfa, f"{key} should require MFA"


# --- scopes ---------------------------------------------------------------


def test_id_bearing_scope_requires_ids() -> None:
    with pytest.raises(InvalidScope):
        Scope(ScopeKind.department)


def test_non_id_scope_rejects_ids() -> None:
    with pytest.raises(InvalidScope):
        Scope(ScopeKind.taught_by_self, frozenset({uuid.uuid4()}))


def test_scope_round_trips_through_json() -> None:
    original = Scope(ScopeKind.department, frozenset({uuid.uuid4(), uuid.uuid4()}))
    assert Scope.from_json(original.to_json()) == original


def test_absent_scope_defaults_to_the_whole_tenant() -> None:
    assert Scope.from_json(None).kind is ScopeKind.tenant
    assert Scope.from_json({}).kind is ScopeKind.tenant


def test_malformed_scope_is_rejected_rather_than_ignored() -> None:
    with pytest.raises(InvalidScope):
        Scope.from_json({"kind": "everything"})
    with pytest.raises(InvalidScope):
        Scope.from_json({"kind": "department", "ids": ["not-a-uuid"]})


def test_scopes_union_rather_than_intersect() -> None:
    """A head of two departments must reach both, not neither."""
    a, b = uuid.uuid4(), uuid.uuid4()
    scopes = parse_scopes(
        [
            {"kind": "department", "ids": [str(a)]},
            {"kind": "department", "ids": [str(b)]},
        ]
    )
    assert scopes.ids_for(ScopeKind.department) == {a, b}


def test_tenant_scope_makes_the_set_unrestricted() -> None:
    scopes = ScopeSet.of([Scope(ScopeKind.taught_by_self), Scope(ScopeKind.tenant)])
    assert scopes.is_unrestricted
