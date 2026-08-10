"""System role templates.

Starting points, not law. Every school may clone, edit, or ignore these; what
stays stable is the `key`, so the platform can reason about "the teacher role"
without assuming anything about what a given school put in it.

Wildcards are used where a role genuinely owns a whole module. Everywhere else
permissions are listed explicitly, because a role that quietly grows when a new
permission is added to a module is how privilege creep happens.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.authz.permissions import CATALOGUE, validate_all
from app.modules.authz.scopes import Scope, ScopeKind


@dataclass(frozen=True, slots=True)
class RoleTemplate:
    key: str
    name: str
    description: str
    permissions: frozenset[str]
    default_scope: Scope
    requires_mfa: bool = False


def _p(*permissions: str) -> frozenset[str]:
    return frozenset(permissions)


TEACHER_PERMISSIONS = _p(
    "academics.class.read",
    "academics.subject.read",
    "academics.year.read",
    "academics.term.read",
    "academics.grading_scale.read",
    "people.person.read",
    "people.student.read",
    "people.guardian.read",
    "attendance.session.read",
    "attendance.session.create",
    "attendance.session.write",
    "attendance.mark.read",
    "attendance.mark.write",
    "assessment.assessment.read",
    "assessment.assessment.create",
    "assessment.assessment.write",
    "assessment.score.read",
    "assessment.score.write",
    "assessment.result.read",
    "learning.course.read",
    "learning.assignment.read",
    "learning.assignment.create",
    "learning.assignment.write",
    "learning.submission.read",
    "learning.grade.read",
    "learning.grade.write",
    "communication.announcement.read",
    "communication.announcement.create",
    "communication.message.read",
    "communication.message.create",
    "intelligence.assistant.read",
    "intelligence.assistant.write",
)

SYSTEM_ROLES: tuple[RoleTemplate, ...] = (
    RoleTemplate(
        key="owner",
        name="Owner",
        description="Full control of the school, including billing and deletion.",
        permissions=frozenset(
            p for p in CATALOGUE if not p.startswith(("platform.", "people.safeguarding"))
        ),
        default_scope=Scope(ScopeKind.tenant),
        requires_mfa=True,
    ),
    RoleTemplate(
        key="admin",
        name="Administrator",
        description="Full operational control. Cannot change billing or delete the school.",
        permissions=frozenset(
            p
            for p in CATALOGUE
            if not p.startswith(
                ("platform.", "billing.", "people.safeguarding", "institution.staff_hr")
            )
        ),
        default_scope=Scope(ScopeKind.tenant),
        requires_mfa=True,
    ),
    RoleTemplate(
        key="registrar",
        name="Registrar",
        description="People, enrolment, academic structure, and records.",
        permissions=_p(
            "people.person.manage",
            "people.student.manage",
            "people.guardian.manage",
            "people.enrolment.manage",
            "people.award.manage",
            # A registrar places students into faculties and departments, so
            # they must be able to see them. Absent until the experience layer
            # asked the question and found a registrar unable to find their own
            # institution's structure.
            "institution.department.read",
            "institution.campus.read",
            "academics.year.manage",
            "academics.term.manage",
            "academics.level.manage",
            "academics.class.manage",
            "academics.subject.manage",
            "academics.grading_scale.read",
            "attendance.mark.read",
            "attendance.mark.export",
            "assessment.result.read",
            "assessment.result.export",
            "reporting.report_card.read",
            "reporting.report_card.create",
            "reporting.transcript.read",
            "reporting.transcript.create",
            "communication.announcement.read",
            "communication.announcement.create",
            "identity.membership.read",
            "audit.event.read",
        ),
        default_scope=Scope(ScopeKind.tenant),
    ),
    RoleTemplate(
        key="principal",
        name="Principal",
        description="Institution-wide oversight, approval, and publication.",
        permissions=_p(
            "people.person.read",
            "people.student.read",
            "people.guardian.read",
            "people.enrolment.read",
            "people.award.read",
            "people.award.approve",
            "academics.class.read",
            "academics.subject.read",
            "academics.year.read",
            "academics.term.read",
            "attendance.mark.read",
            "attendance.mark.export",
            "assessment.assessment.read",
            "assessment.score.read",
            "assessment.result.read",
            "assessment.result.approve",
            "assessment.result.publish",
            "assessment.result.export",
            "finance.report.read",
            "finance.report.export",
            "institution.staff.read",
            "institution.department.read",
            "institution.campus.read",
            "communication.announcement.publish",
            "communication.announcement.create",
            "communication.announcement.read",
            "audit.event.read",
            "intelligence.assistant.read",
            "intelligence.assistant.write",
        ),
        default_scope=Scope(ScopeKind.tenant),
        requires_mfa=True,
    ),
    RoleTemplate(
        key="head_of_department",
        name="Head of Department",
        description="Manages subjects, staff, and results within a department.",
        permissions=TEACHER_PERMISSIONS
        | _p(
            "assessment.result.approve",
            "institution.staff.read",
            "academics.subject.write",
        ),
        # Materialized with concrete department ids at grant time.
        default_scope=Scope(ScopeKind.tenant),
    ),
    RoleTemplate(
        key="teacher",
        name="Teacher",
        description="Attendance, assessment, assignments, and communication for own classes.",
        permissions=TEACHER_PERMISSIONS,
        default_scope=Scope(ScopeKind.taught_by_self),
    ),
    RoleTemplate(
        key="form_tutor",
        name="Form Tutor",
        description="Teacher, plus pastoral oversight of a tutor group.",
        permissions=TEACHER_PERMISSIONS | _p("people.student_sensitive.read"),
        default_scope=Scope(ScopeKind.taught_by_self),
    ),
    RoleTemplate(
        key="bursar",
        name="Bursar",
        description="The school's finances.",
        permissions=_p(
            "finance.fee_structure.manage",
            "finance.invoice.read",
            "finance.invoice.create",
            "finance.invoice.write",
            "finance.invoice.export",
            "finance.payment.read",
            "finance.payment.create",
            "finance.payment.write",
            "finance.payment.export",
            "finance.report.read",
            "finance.report.export",
            "people.student.read",
            "people.guardian.read",
            "communication.message.create",
            "communication.message.read",
            "audit.event.read",
        ),
        default_scope=Scope(ScopeKind.tenant),
        requires_mfa=True,
    ),
    RoleTemplate(
        key="admissions_officer",
        name="Admissions Officer",
        description="The admissions pipeline.",
        permissions=_p(
            "people.person.read",
            "people.person.create",
            "people.person.write",
            "people.student.read",
            "people.student.create",
            "people.student.write",
            "people.guardian.read",
            "people.guardian.create",
            "people.guardian.write",
            "people.enrolment.read",
            "people.enrolment.write",
            "academics.level.read",
            "academics.class.read",
            "communication.message.create",
            "communication.message.read",
            "customization.form.read",
        ),
        default_scope=Scope(ScopeKind.tenant),
    ),
    RoleTemplate(
        key="student",
        name="Student",
        description="Own courses, assignments, results, and timetable.",
        permissions=_p(
            "learning.course.read",
            "learning.assignment.read",
            "learning.submission.read",
            "learning.submission.create",
            "learning.submission.write",
            "learning.grade.read",
            "assessment.result.read",
            "attendance.mark.read",
            "academics.class.read",
            "academics.subject.read",
            "communication.announcement.read",
            "communication.message.read",
            "communication.message.create",
            "intelligence.assistant.read",
            "intelligence.assistant.write",
        ),
        default_scope=Scope(ScopeKind.self_only),
    ),
    RoleTemplate(
        key="guardian",
        name="Parent or Guardian",
        description="Their own children's records, fees, and school communication.",
        permissions=_p(
            "people.person.read",
            "people.student.read",
            "attendance.mark.read",
            "assessment.result.read",
            "reporting.report_card.read",
            "finance.invoice.read",
            "finance.payment.read",
            "finance.payment.create",
            "communication.announcement.read",
            "communication.message.read",
            "communication.message.create",
            "learning.course.read",
            "learning.assignment.read",
            "learning.grade.read",
        ),
        default_scope=Scope(ScopeKind.own_children),
    ),
)

SYSTEM_ROLES_BY_KEY: dict[str, RoleTemplate] = {r.key: r for r in SYSTEM_ROLES}


def validate_catalogue() -> None:
    """Fail the boot, not a request, if a template drifts from the catalogue."""
    for template in SYSTEM_ROLES:
        try:
            validate_all(set(template.permissions))
        except Exception as exc:  # pragma: no cover - startup guard
            raise RuntimeError(
                f"System role {template.key!r} references an unknown permission: {exc}"
            ) from exc
