"""How a scope reaches a person, a student record, or an enrolment.

`authz` owns the vocabulary of scopes and the rules for combining them. It does
not own the joins, because only this module knows that a student is in a class
through an open enrolment rather than through a column. So the plans live here,
next to the tables they constrain, and `authz` compiles them.

Three decisions worth stating, because each could reasonably have gone the
other way and the choice is not recoverable from the SQL:

**Scope follows the *open* enrolment.** A teacher allocated to 7B this year
reaches the children in 7B *now*. It does not reach a child who left in
October, whose record belongs to whoever has the historical permission. That
choice keeps the everyday case tight; a scope that quietly included every child
who ever sat in the room would grow without anybody deciding it should.

**The academic-unit tree is walked downwards.** A head of faculty reaches the
departments inside it, recursively. Anything else makes the scope meaningless
the moment an institution nests two levels — which ADR-024 exists to allow.

**A guardian reaches their children through `people`, not through `users`.** The
principal's identity is matched to *this institution's* record of them, and the
guardianships hang off that. The same human at another institution is a
different `Person` and reaches nothing here (ADR-027).
"""

from __future__ import annotations

from sqlalchemy import ColumnElement, select

from app.modules.academics import service as academics
from app.modules.authz.predicates import ScopeContext, ScopePlan
from app.modules.authz.scopes import ScopeKind
from app.modules.people.enrolment import Enrolment
from app.modules.people.models import GuardianRelationship, Person, StudentRelationship

__all__ = [
    "ENROLMENTS",
    "PEOPLE",
    "STUDENT_RELATIONSHIPS",
    "own_children_clause",
    "student_ids_where",
    "student_self_clause",
]


# --- building blocks -------------------------------------------------------
#
# Anything that touches an academics table comes from `academics.service` as a
# `Select`, so this module composes the boundary into one statement without
# importing tables it does not own. The composition matters as much as the
# boundary rule: a list of ids fetched into Python is one refactor away from
# being applied after the rows have arrived.


def _open_enrolments():
    """Placements that have not ended. The everyday meaning of "is in"."""
    return select(
        Enrolment.student_relationship_id.label("student_relationship_id"),
        Enrolment.class_group_id.label("class_group_id"),
        Enrolment.level_id.label("level_id"),
        Enrolment.programme_id.label("programme_id"),
        Enrolment.cohort_id.label("cohort_id"),
    ).where(Enrolment.ended_on.is_(None)).subquery()


def _students_where(condition) -> ColumnElement[bool]:
    """Student relationships whose current placement satisfies `condition`."""
    placements = _open_enrolments()
    return StudentRelationship.id.in_(
        select(placements.c.student_relationship_id).where(condition(placements))
    )


def _my_person_id(context: ScopeContext):
    """This institution's record of the person making the request.

    A subquery rather than a fetched id, so the whole predicate stays one
    statement — and so a principal with no person record here produces an empty
    set rather than a `None` that some later `==` reads as a match.
    """
    return select(Person.id).where(
        Person.user_id == context.user_id, Person.deleted_at.is_(None)
    )


def _my_children_person_ids(context: ScopeContext):
    return select(GuardianRelationship.student_person_id).where(
        GuardianRelationship.guardian_person_id.in_(_my_person_id(context))
    )


def _my_class_group_ids(context: ScopeContext):
    return academics.class_group_ids_taught_by(context.membership_id)


# --- student relationships -------------------------------------------------


def _students_in_units(context: ScopeContext) -> ColumnElement[bool] | None:
    """Students on a programme belonging to one of these units, or below them.

    A student whose placement names no programme is not reached by a unit
    scope. That is correct rather than convenient: a head of department has no
    claim on a child the institution has not placed in their department, and
    guessing one would be the authorization boundary drifting outwards.
    """
    if not context.ids:
        return None
    programmes = academics.programme_ids_under(context.ids)
    return _students_where(lambda p: p.c.programme_id.in_(programmes))


def _students_in_levels(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return _students_where(lambda p: p.c.level_id.in_(context.ids))


def _students_in_classes(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return _students_where(lambda p: p.c.class_group_id.in_(context.ids))


def _students_in_programmes(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return _students_where(lambda p: p.c.programme_id.in_(context.ids))


def _students_in_cohorts(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return _students_where(lambda p: p.c.cohort_id.in_(context.ids))


def _students_taught_by_self(context: ScopeContext) -> ColumnElement[bool] | None:
    if context.membership_id is None:
        return None
    mine = _my_class_group_ids(context)
    return _students_where(lambda p: p.c.class_group_id.in_(mine))


def _own_children(context: ScopeContext) -> ColumnElement[bool] | None:
    if context.user_id is None:
        return None
    return StudentRelationship.person_id.in_(_my_children_person_ids(context))


def _student_self(context: ScopeContext) -> ColumnElement[bool] | None:
    if context.user_id is None:
        return None
    return StudentRelationship.person_id.in_(_my_person_id(context))


STUDENT_RELATIONSHIPS = ScopePlan(
    resource="student_relationship",
    clauses={
        ScopeKind.campus: _students_in_units,
        ScopeKind.department: _students_in_units,
        ScopeKind.academic_unit: _students_in_units,
        ScopeKind.programme: _students_in_programmes,
        ScopeKind.cohort: _students_in_cohorts,
        ScopeKind.level: _students_in_levels,
        ScopeKind.klass: _students_in_classes,
        ScopeKind.taught_by_self: _students_taught_by_self,
        ScopeKind.own_children: _own_children,
        ScopeKind.self_only: _student_self,
        # `subject` is deliberately absent. A subject scope says which courses
        # somebody may configure, not which children they may read, and letting
        # it through here would turn "may edit the Chemistry syllabus" into
        # "may read every chemistry student's record".
    },
)


# --- people ----------------------------------------------------------------


def _people_via_students(builder):
    """Lift a student-relationship clause to the person behind it."""

    def clause(context: ScopeContext) -> ColumnElement[bool] | None:
        inner = builder(context)
        if inner is None:
            return None
        return Person.id.in_(
            select(StudentRelationship.person_id).where(inner)
        )

    return clause


def _person_self(context: ScopeContext) -> ColumnElement[bool] | None:
    """Yourself, and — for a guardian — the children you are responsible for.

    A guardian holds `self` over their own record and `own_children` over their
    children's. Both are person rows, and merging them here would make a
    guardian's "see my own details" silently include their children, which is
    a widening nobody granted.
    """
    if context.user_id is None:
        return None
    return Person.user_id == context.user_id


def _person_own_children(context: ScopeContext) -> ColumnElement[bool] | None:
    if context.user_id is None:
        return None
    return Person.id.in_(_my_children_person_ids(context))


PEOPLE = ScopePlan(
    resource="person",
    clauses={
        ScopeKind.campus: _people_via_students(_students_in_units),
        ScopeKind.department: _people_via_students(_students_in_units),
        ScopeKind.academic_unit: _people_via_students(_students_in_units),
        ScopeKind.programme: _people_via_students(_students_in_programmes),
        ScopeKind.cohort: _people_via_students(_students_in_cohorts),
        ScopeKind.level: _people_via_students(_students_in_levels),
        ScopeKind.klass: _people_via_students(_students_in_classes),
        ScopeKind.taught_by_self: _people_via_students(_students_taught_by_self),
        ScopeKind.own_children: _person_own_children,
        ScopeKind.self_only: _person_self,
    },
)


# --- enrolments ------------------------------------------------------------


def _enrolments_of(builder):
    def clause(context: ScopeContext) -> ColumnElement[bool] | None:
        inner = builder(context)
        if inner is None:
            return None
        return Enrolment.student_relationship_id.in_(
            select(StudentRelationship.id).where(inner)
        )

    return clause


def _enrolments_in_units(context: ScopeContext) -> ColumnElement[bool] | None:
    """Directly on the enrolment, not via the current placement.

    Deliberately different from the student version. A head of department asks
    "which placements were in my department?" and must see the ones that have
    since ended — otherwise a student's departmental history vanishes the moment
    they move on, and the enrolment table's whole purpose is that it does not.
    """
    if not context.ids:
        return None
    return Enrolment.programme_id.in_(academics.programme_ids_under(context.ids))


ENROLMENTS = ScopePlan(
    resource="enrolment",
    clauses={
        ScopeKind.campus: _enrolments_in_units,
        ScopeKind.department: _enrolments_in_units,
        ScopeKind.academic_unit: _enrolments_in_units,
        ScopeKind.programme: lambda c: (
            Enrolment.programme_id.in_(c.ids) if c.ids else None
        ),
        ScopeKind.cohort: lambda c: (
            Enrolment.cohort_id.in_(c.ids) if c.ids else None
        ),
        ScopeKind.level: lambda c: (
            Enrolment.level_id.in_(c.ids) if c.ids else None
        ),
        ScopeKind.klass: lambda c: (
            Enrolment.class_group_id.in_(c.ids) if c.ids else None
        ),
        ScopeKind.taught_by_self: _enrolments_of(_students_taught_by_self),
        ScopeKind.own_children: _enrolments_of(_own_children),
        ScopeKind.self_only: _enrolments_of(_student_self),
    },
)


# Published deliberately. Another module composing a guardian's reach over
# attendance must use *this* clause rather than write its own, or the two drift
# and one of them is wrong about whose child a parent may read.
own_children_clause = _own_children
student_self_clause = _student_self


def student_ids_where(clause):
    """The student-relationship ids a people-clause reaches, as a `Select`.

    Published so another module can compose a reach over its own rows without
    importing this module's tables — the boundary rule with no exception carved
    out for the caller that finds it inconvenient. A `Select` rather than a list
    of ids for the reason ADR-029 exists: the boundary has to be *in* the query.
    """
    return select(StudentRelationship.id).where(clause)
