"""How a scope reaches a supervision, a milestone, and a meeting.

Narrower than the plans for classroom records, on purpose. Three scope kinds
that reach almost everything else are absent here, and each absence is a
decision rather than an omission:

**No `taught_by_self`.** A lecturer who teaches a research candidate's taught
component has no claim on that candidate's thesis milestones. The two are
different relationships with the same person, and letting the teaching one
reach the research one would mean every demonstrator on a doctoral training
module could read every candidate's upgrade outcome.

**No `own_children`.** A guardianship reaches a child's attendance and their
published results because a family is accountable for those. A supervision
record is a working relationship between two adults, and a system that exposed
it to whoever was listed as next of kin at admission would be widening a
boundary nobody granted.

**`supervised_by_self` follows the *open* supervision.** A supervisor who
handed a candidate to a colleague stops reading their record, for the same
reason a teacher's scope follows the open enrolment. The history of who
supervised whom is not lost — it is in the closed rows, reachable by the
programme and unit scopes that exist to answer exactly that question.
"""

from __future__ import annotations

from sqlalchemy import ColumnElement, select

from app.modules.academics import service as academics
from app.modules.academics.research import Milestone, Supervision, SupervisionMeeting
from app.modules.academics.structure import MilestoneDefinition
from app.modules.authz.predicates import ScopeContext, ScopePlan
from app.modules.authz.scopes import ScopeKind
from app.modules.people import scopes as people_scopes

__all__ = ["MILESTONES", "SUPERVISIONS", "SUPERVISION_MEETINGS"]


# --- milestones -------------------------------------------------------------
#
# A milestone is narrowed by the programme that *set the requirement* rather
# than by the candidate's current placement. The two agree in every ordinary
# case, and where they disagree — a candidate transferred between programmes
# mid-candidature — the requirement belongs to the programme that imposed it,
# which is the one whose graduate school has to rule on it.


def _definitions_in_programmes(programme_ids) -> ColumnElement[bool]:
    return Milestone.milestone_definition_id.in_(
        select(MilestoneDefinition.id).where(
            MilestoneDefinition.programme_id.in_(programme_ids)
        )
    )


def _milestones_in_programmes(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return _definitions_in_programmes(context.ids)


def _milestones_in_units(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return _definitions_in_programmes(academics.programme_ids_under(context.ids))


def _milestones_of(builder):
    def clause(context: ScopeContext) -> ColumnElement[bool] | None:
        inner = builder(context)
        if inner is None:
            return None
        return Milestone.student_relationship_id.in_(
            people_scopes.student_ids_where(inner)
        )

    return clause


MILESTONES = ScopePlan(
    resource="research_milestone",
    clauses={
        ScopeKind.campus: _milestones_in_units,
        ScopeKind.department: _milestones_in_units,
        ScopeKind.academic_unit: _milestones_in_units,
        ScopeKind.programme: _milestones_in_programmes,
        ScopeKind.supervised_by_self: _milestones_of(
            people_scopes.supervised_by_self_clause
        ),
        ScopeKind.self_only: _milestones_of(people_scopes.student_self_clause),
    },
)


# --- supervisions and meetings ---------------------------------------------
#
# These have no definition to borrow a programme from, so they are narrowed
# through the candidate's placement in the ordinary way.


def _rows_of(model, builder):
    def clause(context: ScopeContext) -> ColumnElement[bool] | None:
        inner = builder(context)
        if inner is None:
            return None
        return model.student_relationship_id.in_(
            people_scopes.student_ids_where(inner)
        )

    return clause


def _plan_for(model, resource: str) -> ScopePlan:
    return ScopePlan(
        resource=resource,
        clauses={
            ScopeKind.campus: _rows_of(model, people_scopes.students_in_units_clause),
            ScopeKind.department: _rows_of(
                model, people_scopes.students_in_units_clause
            ),
            ScopeKind.academic_unit: _rows_of(
                model, people_scopes.students_in_units_clause
            ),
            ScopeKind.programme: _rows_of(
                model, people_scopes.students_in_programmes_clause
            ),
            ScopeKind.supervised_by_self: _rows_of(
                model, people_scopes.supervised_by_self_clause
            ),
            ScopeKind.self_only: _rows_of(model, people_scopes.student_self_clause),
        },
    )


SUPERVISIONS = _plan_for(Supervision, "supervision")
SUPERVISION_MEETINGS = _plan_for(SupervisionMeeting, "supervision_meeting")
