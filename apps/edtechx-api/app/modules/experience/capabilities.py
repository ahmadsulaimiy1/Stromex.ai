"""What each institution's interface contains — derived, never assumed.

**Complexity must be capability, never burden.** The academic engine supports
academic units, stages, programmes, qualifications, levels, cohorts, courses,
class groups, academic periods, credit systems, supervision and milestones. A
nursery administrator must never be shown one of them, and not as an empty menu
item either: a "Programmes — 0 programmes" row teaches a person that their
system is full of things they do not understand and have done something wrong
about.

So a capability appears only when **four** independent questions all say yes:

  1. *Does this institution's world contain the concept?* Answered from its own
     configuration — the layers it has put rows in, plus any it has declared it
     intends to use. Not from a profile enum: ADR-024 forbids one, and a
     `NURSERY | SECONDARY | UNIVERSITY` field is the same mistake wearing a
     different hat.
  2. *May this person see it?* The permission, which they either hold or do not.
  3. *Has the institution bought it?* The entitlement (ADR-030).
  4. *Is it relevant to this person's role?* Ordering and prominence, not
     access — a teacher and a bursar both may see fees, and only one of them
     opens the product to look at them.

The four answers are not interchangeable, and what happens when one says no
differs:

  **Not in this institution's world** → absent. The concept does not exist here.
  **Not permitted** → absent. Existence is sensitive (ADR-004).
  **Not entitled** → absent for most people; shown *as an upgrade* only to
  somebody who could actually act on it, because a padlock a teacher cannot
  open is an advertisement placed in their way.
  **Not relevant to the role** → present, lower down.

The distinction that follows is the one the brief calls zero-state
intelligence: a capability that is present but has no records yet is a *useful
empty state* — "your school has no courses yet" with the action that fixes it.
A capability that is absent has no empty state, because it has no state at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True, slots=True)
class Capability:
    """One thing an institution's interface can contain."""

    key: str
    # The terminology key this concept is named by, so the label is the
    # institution's own word. `None` for the few things every institution calls
    # the same thing.
    term: str | None
    # Where it sits. Groups are ordered by the role, not by this list.
    group: str
    # The layers whose presence means this institution uses the concept. Any one
    # of them is enough. Empty means the capability does not depend on academic
    # configuration at all — every institution has people.
    layers: tuple[str, ...] = ()
    # The permission required to see it. A capability with none is visible to
    # anybody who got this far, which is true of very little.
    permission: str | None = None
    # The plan feature required. `None` means it is part of the product rather
    # than part of a plan.
    feature: str | None = None
    # A short sentence for the empty state, used when the capability is present
    # and has no records. Phrased as what to do, not as what is missing.
    empty_action: str = ""
    # Whether an unentitled institution should be shown an upgrade affordance
    # rather than nothing — for capabilities that are genuinely a purchase
    # decision rather than a structural absence.
    offer_upgrade: bool = True
    description: str = ""


GROUPS: Final[tuple[str, ...]] = (
    "today",
    "people",
    "academics",
    "operations",
    "finance",
    "communication",
    "insight",
    "configuration",
)


# --- the catalogue ---------------------------------------------------------
#
# Ordered within each group by how ordinary the concept is, so that an
# institution using few of them still gets a sensible sequence.

CAPABILITIES: Final[tuple[Capability, ...]] = (
    # --- people: every institution has these ---
    Capability(
        key="people.students",
        term="student",
        group="people",
        permission="people.student.read",
        empty_action="Add your first {term}",
        description="The people who learn here.",
    ),
    Capability(
        key="people.staff",
        term="staff",
        group="people",
        permission="institution.staff.read",
        empty_action="Add your first {term}",
    ),
    Capability(
        key="people.guardians",
        term="guardian",
        group="people",
        permission="people.guardian.read",
        empty_action="Link a {term} to a student",
    ),
    Capability(
        key="people.enrolment",
        term="enrolment",
        group="people",
        permission="people.enrolment.read",
        description="Admissions, placements, transfers and completion.",
    ),
    # --- academic structure: only what the institution actually uses ---
    Capability(
        key="academics.units",
        term="academic_unit",
        group="academics",
        layers=("academic_units",),
        permission="institution.department.read",
        empty_action="Create your first {term}",
        description="Faculties, schools, departments — whatever this institution nests.",
    ),
    Capability(
        key="academics.stages",
        term="stage",
        group="academics",
        layers=("stages",),
        permission="academics.level.read",
        empty_action="Create your first {term}",
    ),
    Capability(
        key="academics.programmes",
        term="programme",
        group="academics",
        layers=("programmes",),
        permission="academics.level.read",
        empty_action="Create your first {term}",
    ),
    Capability(
        key="academics.qualifications",
        term="qualification",
        group="academics",
        layers=("qualifications",),
        permission="academics.level.read",
        empty_action="Define your first {term}",
    ),
    Capability(
        key="academics.levels",
        term="level",
        group="academics",
        layers=("levels",),
        permission="academics.level.read",
        empty_action="Create your first {term}",
    ),
    Capability(
        key="academics.cohorts",
        term="cohort",
        group="academics",
        layers=("cohorts",),
        permission="academics.level.read",
        empty_action="Create your first {term}",
    ),
    Capability(
        key="academics.classes",
        term="class_group",
        group="academics",
        layers=("classes",),
        permission="academics.class.read",
        empty_action="Create your first {term}",
    ),
    Capability(
        key="academics.courses",
        term="course",
        group="academics",
        layers=("courses",),
        permission="academics.subject.read",
        empty_action="Add your first {term}",
    ),
    Capability(
        key="academics.calendar",
        term="academic_year",
        group="academics",
        layers=("years", "periods"),
        permission="academics.year.read",
        empty_action="Set up your {term}",
        description="Years, terms, semesters — the institution's own divisions.",
    ),
    Capability(
        key="academics.credits",
        term="credit",
        group="academics",
        layers=("credits",),
        permission="academics.level.read",
        empty_action="Define how this institution counts {term}",
    ),
    Capability(
        key="academics.grading",
        term="grade",
        group="academics",
        layers=("grading",),
        permission="academics.grading_scale.read",
        empty_action="Create your first grading scale",
    ),
    Capability(
        key="academics.progression",
        term="level",
        group="academics",
        layers=("progression",),
        permission="academics.level.manage",
        empty_action="Set the rule for moving up",
    ),
    # --- research: present only for institutions that supervise ---
    Capability(
        key="research.supervision",
        term="supervisor",
        group="academics",
        layers=("supervision",),
        permission="people.student.read",
        empty_action="Name the {term} roles this institution uses",
    ),
    Capability(
        key="research.milestones",
        term="milestone",
        group="academics",
        layers=("milestones",),
        permission="people.student.read",
        empty_action="Define the {term}s a research student passes",
    ),
    # --- operations: gated by entitlement, not by academic shape ---
    Capability(
        key="operations.attendance",
        term="attendance",
        group="operations",
        permission="attendance.mark.read",
        feature="core.attendance",
        empty_action="Take your first register",
    ),
    Capability(
        key="operations.assessment",
        term="assessment",
        group="operations",
        permission="assessment.assessment.read",
        feature="core.assessment",
        empty_action="Create your first {term}",
    ),
    Capability(
        key="operations.results",
        term="grade",
        group="operations",
        permission="assessment.result.read",
        feature="core.assessment",
        empty_action="Results appear here once marks are entered",
    ),
    Capability(
        key="operations.report_cards",
        term="report_card",
        group="operations",
        permission="reporting.report_card.read",
        feature="core.report_cards",
        empty_action="Design your first {term}",
    ),
    Capability(
        key="operations.transcripts",
        term="qualification",
        group="operations",
        layers=("credits", "qualifications"),
        permission="reporting.transcript.read",
        feature="core.report_cards",
        empty_action="Transcripts appear once results are published",
    ),
    Capability(
        key="operations.timetable",
        term="class_group",
        group="operations",
        layers=("classes",),
        permission="academics.class.read",
        feature="operations.timetabling",
        empty_action="Build your first timetable",
    ),
    Capability(
        key="operations.admissions",
        term="admission",
        group="operations",
        permission="people.student.create",
        empty_action="Take your first application",
    ),
    Capability(
        key="operations.imports",
        term="person",
        group="operations",
        permission="people.person.create",
        feature="core.bulk_import",
        empty_action="Import your people from a spreadsheet",
    ),
    # --- finance ---
    Capability(
        key="finance.invoices",
        term=None,
        group="finance",
        permission="finance.invoice.read",
        feature="finance.invoicing",
        empty_action="Set up your first fee structure",
    ),
    Capability(
        key="finance.payments",
        term=None,
        group="finance",
        permission="finance.payment.read",
        feature="finance.invoicing",
        empty_action="Payments appear here once a fee is issued",
    ),
    # --- communication ---
    Capability(
        key="communication.announcements",
        term=None,
        group="communication",
        permission="communication.announcement.read",
        feature="core.announcements",
        empty_action="Write your first announcement",
    ),
    Capability(
        key="communication.messages",
        term=None,
        group="communication",
        permission="communication.message.read",
        empty_action="",
    ),
    # --- learning ---
    Capability(
        key="learning.courses",
        term="course",
        group="operations",
        permission="learning.course.read",
        feature="learning.courses",
        empty_action="Build your first {term}",
    ),
    Capability(
        key="learning.assignments",
        term=None,
        group="operations",
        permission="learning.assignment.read",
        feature="learning.courses",
        empty_action="Set your first assignment",
    ),
    # --- insight ---
    Capability(
        key="insight.overview",
        term=None,
        group="insight",
        permission="audit.event.read",
        empty_action="",
        description="Enrolment, attendance and results at a glance.",
    ),
    Capability(
        key="insight.analytics",
        term=None,
        group="insight",
        permission="finance.report.read",
        feature="operations.advanced_analytics",
        empty_action="",
    ),
    # --- configuration ---
    Capability(
        key="configuration.terminology",
        term=None,
        group="configuration",
        permission="customization.terminology.read",
        feature="customization.terminology",
        empty_action="Rename anything this institution calls something else",
    ),
    Capability(
        key="configuration.theme",
        term=None,
        group="configuration",
        permission="customization.theme.read",
        feature="customization.theme",
        empty_action="Make this look like your institution",
    ),
    Capability(
        key="configuration.design_studio",
        term=None,
        group="configuration",
        permission="customization.theme.write",
        feature="customization.design_studio",
        empty_action="",
    ),
    Capability(
        key="configuration.roles",
        term=None,
        group="configuration",
        permission="authz.role.read",
        empty_action="",
    ),
    Capability(
        key="configuration.billing",
        term=None,
        group="configuration",
        permission="billing.subscription.read",
        empty_action="",
        offer_upgrade=False,
    ),
    Capability(
        key="intelligence.assistants",
        term=None,
        group="insight",
        permission="intelligence.assistant.read",
        feature="intelligence.assistants",
        empty_action="Ask a question about your institution",
    ),
)

BY_KEY: Final[dict[str, Capability]] = {c.key: c for c in CAPABILITIES}


# --- what each role opens the product to do -------------------------------
#
# Ordering and prominence, never access. A bursar and a teacher may both be
# permitted to see fees; only one of them came here for that.

@dataclass(frozen=True, slots=True)
class RoleShape:
    """The order a role's world appears in, and what leads it."""

    role: str
    groups: tuple[str, ...]
    # Capabilities pulled to the front regardless of their group, because they
    # are what this person came to do.
    primary: tuple[str, ...] = field(default_factory=tuple)


ROLE_SHAPES: Final[dict[str, RoleShape]] = {
    "owner": RoleShape(
        "owner",
        ("insight", "people", "academics", "operations", "finance",
         "communication", "configuration"),
        primary=("insight.overview",),
    ),
    "principal": RoleShape(
        "principal",
        ("insight", "operations", "people", "academics", "finance", "communication"),
        primary=("insight.overview", "operations.results", "operations.attendance"),
    ),
    "admin": RoleShape(
        "admin",
        ("people", "operations", "academics", "communication", "insight",
         "finance", "configuration"),
        primary=("people.students", "operations.admissions", "operations.attendance"),
    ),
    "registrar": RoleShape(
        "registrar",
        ("people", "academics", "operations", "communication", "insight"),
        primary=("people.students", "people.enrolment", "academics.classes"),
    ),
    "teacher": RoleShape(
        "teacher",
        ("today", "operations", "people", "communication", "academics"),
        primary=("operations.attendance", "operations.assessment", "people.students"),
    ),
    "form_tutor": RoleShape(
        "form_tutor",
        ("today", "operations", "people", "communication", "academics"),
        primary=("operations.attendance", "people.students"),
    ),
    "head_of_department": RoleShape(
        "head_of_department",
        ("today", "operations", "academics", "people", "insight", "communication"),
        primary=("operations.results", "academics.courses", "people.staff"),
    ),
    "bursar": RoleShape(
        "bursar",
        ("finance", "people", "communication", "insight"),
        primary=("finance.invoices", "finance.payments"),
    ),
    "admissions_officer": RoleShape(
        "admissions_officer",
        ("operations", "people", "communication"),
        primary=("operations.admissions", "people.students"),
    ),
    "student": RoleShape(
        "student",
        ("today", "operations", "communication"),
        primary=("learning.assignments", "operations.results", "operations.attendance"),
    ),
    "guardian": RoleShape(
        "guardian",
        ("today", "operations", "finance", "communication"),
        primary=("operations.attendance", "operations.results", "finance.invoices"),
    ),
}

# The order used when somebody's roles do not match a template — a school that
# invented "Head of Boarding" gets a sensible sequence rather than an arbitrary
# one, and never an error.
DEFAULT_SHAPE: Final[RoleShape] = RoleShape(
    "default",
    ("today", "people", "academics", "operations", "finance", "communication",
     "insight", "configuration"),
)
