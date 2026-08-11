"""How a scope reaches a document.

A document is *about* a student, so its reach is the student's reach. That
relationship is expressed by lifting `people`'s own clauses onto this table
rather than by rewriting the joins here — two modules with their own idea of
whose child a parent may read is two modules of which one is eventually wrong.

The composition is `document.student_relationship_id IN (the students this
scope reaches)`, which stays one statement and therefore stays enforced by the
database rather than by whatever the caller does with the list (ADR-029).
"""

from __future__ import annotations

from app.modules.authz.predicates import ScopeContext, ScopePlan
from app.modules.authz.scopes import ScopeKind
from app.modules.documents.models import Document
from app.modules.people import scopes as people_scopes

__all__ = ["DOCUMENTS"]


def _via_students(kind: ScopeKind):
    """Reuse the clause `people` already wrote for this kind of scope.

    Reading it out of the published plan rather than importing a private helper
    means a change to how a department reaches its students reaches documents on
    the same day, without anybody remembering that this file exists.
    """
    inner_builder = people_scopes.STUDENT_RELATIONSHIPS.clauses[kind]

    def clause(context: ScopeContext):
        inner = inner_builder(context)
        if inner is None:
            return None
        return Document.student_relationship_id.in_(
            people_scopes.student_ids_where(inner)
        )

    return clause


DOCUMENTS = ScopePlan(
    resource="document",
    clauses={
        kind: _via_students(kind)
        for kind in (
            ScopeKind.campus,
            ScopeKind.department,
            ScopeKind.academic_unit,
            ScopeKind.programme,
            ScopeKind.cohort,
            ScopeKind.level,
            ScopeKind.klass,
            ScopeKind.taught_by_self,
            ScopeKind.own_children,
            ScopeKind.self_only,
        )
    },
)
