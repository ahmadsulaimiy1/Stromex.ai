"""How a scope reaches a mark and a published result.

The asymmetry is the interesting part. A teacher reaches the *working* scores of
the classes they teach; a guardian reaches their child's *published* results and
nothing else. A parent who could read a draft score would be reading a mark
before the institution had decided it was right, which is the whole reason the
two tables are separate (ADR-033).
"""

from __future__ import annotations

from sqlalchemy import ColumnElement, select

from app.modules.academics import service as academics
from app.modules.assessment.models import Assessment, AssessmentScore, PublishedResult
from app.modules.authz.predicates import ScopeContext, ScopePlan
from app.modules.authz.scopes import ScopeKind
from app.modules.people import scopes as people_scopes

__all__ = ["PUBLISHED_RESULTS", "SCORES"]


def _assessments_in_classes(ids) -> ColumnElement[bool]:
    return Assessment.class_group_id.in_(ids)


def _scores_where(condition) -> ColumnElement[bool]:
    return AssessmentScore.assessment_id.in_(select(Assessment.id).where(condition))


def _scores_in_classes(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return _scores_where(_assessments_in_classes(context.ids))


def _scores_taught_by_self(context: ScopeContext) -> ColumnElement[bool] | None:
    if context.membership_id is None:
        return None
    return _scores_where(
        _assessments_in_classes(
            academics.class_group_ids_taught_by(context.membership_id)
        )
    )


def _scores_in_units(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return _scores_where(
        _assessments_in_classes(academics.class_group_ids_under(context.ids))
    )


SCORES = ScopePlan(
    resource="assessment_score",
    clauses={
        ScopeKind.campus: _scores_in_units,
        ScopeKind.department: _scores_in_units,
        ScopeKind.academic_unit: _scores_in_units,
        ScopeKind.klass: _scores_in_classes,
        ScopeKind.taught_by_self: _scores_taught_by_self,
        # Deliberately no `own_children` and no `self`. A working score is a
        # teacher's draft; a family reads the published result.
    },
)


def _results_of(builder):
    def clause(context: ScopeContext) -> ColumnElement[bool] | None:
        inner = builder(context)
        if inner is None:
            return None
        return PublishedResult.student_relationship_id.in_(
            people_scopes.student_ids_where(inner)
        )

    return clause


def _results_in_classes(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return PublishedResult.assessment_id.in_(
        select(Assessment.id).where(_assessments_in_classes(context.ids))
    )


def _results_taught_by_self(context: ScopeContext) -> ColumnElement[bool] | None:
    if context.membership_id is None:
        return None
    return PublishedResult.assessment_id.in_(
        select(Assessment.id).where(
            _assessments_in_classes(
                academics.class_group_ids_taught_by(context.membership_id)
            )
        )
    )


def _results_in_units(context: ScopeContext) -> ColumnElement[bool] | None:
    if not context.ids:
        return None
    return PublishedResult.assessment_id.in_(
        select(Assessment.id).where(
            _assessments_in_classes(academics.class_group_ids_under(context.ids))
        )
    )


PUBLISHED_RESULTS = ScopePlan(
    resource="published_result",
    clauses={
        ScopeKind.campus: _results_in_units,
        ScopeKind.department: _results_in_units,
        ScopeKind.academic_unit: _results_in_units,
        ScopeKind.klass: _results_in_classes,
        ScopeKind.taught_by_self: _results_taught_by_self,
        ScopeKind.own_children: _results_of(people_scopes.own_children_clause),
        ScopeKind.self_only: _results_of(people_scopes.student_self_clause),
    },
)
