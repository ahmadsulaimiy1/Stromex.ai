"""How a scope reaches a register.

Attendance is the resource a teacher touches most and the one a guardian cares
about most, and their reach is entirely different: a teacher reaches the classes
they teach, a guardian reaches their own children's marks and nothing else in
the room. Both are compiled into the query (ADR-029) rather than filtered
afterwards, because a register is a list of named children and a leak here is a
leak of exactly the thing a school is most careful with.
"""

from __future__ import annotations

from sqlalchemy import ColumnElement, select

from app.modules.academics import service as academics
from app.modules.attendance.models import AttendanceMark, AttendanceSession
from app.modules.authz.predicates import ScopeContext, ScopePlan
from app.modules.authz.scopes import ScopeKind
from app.modules.people import scopes as people_scopes

__all__ = ["MARKS", "SESSIONS"]


def _sessions_in_classes(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return AttendanceSession.class_group_id.in_(context.ids)


def _sessions_taught_by_self(context: ScopeContext) -> ColumnElement[bool] | None:
    if context.membership_id is None:
        return None
    return AttendanceSession.class_group_id.in_(
        academics.class_group_ids_taught_by(context.membership_id)
    )


def _sessions_in_units(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return AttendanceSession.class_group_id.in_(
        academics.class_group_ids_under(context.ids)
    )


SESSIONS = ScopePlan(
    resource="attendance_session",
    clauses={
        ScopeKind.campus: _sessions_in_units,
        ScopeKind.department: _sessions_in_units,
        ScopeKind.academic_unit: _sessions_in_units,
        ScopeKind.klass: _sessions_in_classes,
        ScopeKind.taught_by_self: _sessions_taught_by_self,
        # A guardian and a student reach *marks*, not whole registers. A parent
        # who could open a register would be reading a list of other people's
        # children, which is precisely what a register is.
    },
)


def _marks_of(builder):
    """Marks belonging to the students a people-scope reaches.

    Composed from the people plan rather than rewritten, so a guardian's reach
    over attendance is the same reach they have over the child — and cannot
    drift from it when one of the two is changed.
    """

    def clause(context: ScopeContext) -> ColumnElement[bool] | None:
        inner = builder(context)
        if inner is None:
            return None
        # Through `people.scopes`, not through its tables. The module-boundary
        # test caught the shortcut, and the shortcut was the wrong answer: a
        # guardian's reach over attendance must be the *same* reach they have
        # over the child, and two copies of it drift.
        return AttendanceMark.student_relationship_id.in_(
            people_scopes.student_ids_where(inner)
        )

    return clause


def _marks_in_sessions(builder):
    def clause(context: ScopeContext) -> ColumnElement[bool] | None:
        inner = builder(context)
        if inner is None:
            return None
        return AttendanceMark.session_id.in_(
            select(AttendanceSession.id).where(inner)
        )

    return clause


MARKS = ScopePlan(
    resource="attendance_mark",
    clauses={
        ScopeKind.campus: _marks_in_sessions(_sessions_in_units),
        ScopeKind.department: _marks_in_sessions(_sessions_in_units),
        ScopeKind.academic_unit: _marks_in_sessions(_sessions_in_units),
        ScopeKind.klass: _marks_in_sessions(_sessions_in_classes),
        ScopeKind.taught_by_self: _marks_in_sessions(_sessions_taught_by_self),
        ScopeKind.own_children: _marks_of(people_scopes.own_children_clause),
        ScopeKind.self_only: _marks_of(people_scopes.student_self_clause),
    },
)
