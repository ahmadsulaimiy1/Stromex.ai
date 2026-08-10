"""Student records over HTTP — the first routes with a scope in the query.

Every handler here is short, and all three are the same three lines: take the
principal, build a scoped statement, run it. That is the point. The
authorization boundary is not something these functions apply; it is something
they cannot avoid, because the only way to obtain a statement is
`scoped_select`, and the only way that returns rows is if the principal's grants
for *this permission* say so.

Two shapes matter more than they look.

**The count is scoped too.** A list endpoint that filters its rows and then
counts the table tells an unauthorized caller exactly how many records they
cannot see, which is most of what they wanted. `total` here is the number of
rows this principal may read and nothing else.

**A record out of scope is a 404.** Not a 403. "You may not see this" and "this
does not exist" have to be the same answer, or the difference between them is
the answer (ADR-004).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import CurrentPrincipal, DbSession, RequirePermission
from app.core import errors
from app.core.context import Principal
from app.modules.authz.predicates import scoped_count, scoped_get, scoped_select
from app.modules.people import scopes as people_scopes
from app.modules.people import service as people_service
from app.modules.people.models import Person, StudentRelationship

router = APIRouter(tags=["people"])

READ_STUDENTS = "people.student.read"

# The ceiling is the endpoint's, not the caller's. An unbounded page size turns
# any list into an export, and an export is a separate permission.
MAX_PAGE = 100


class StudentSummary(BaseModel):
    id: str
    person_id: str
    full_name: str
    reference: str | None
    kind_label: str
    status: str


class StudentPage(BaseModel):
    items: list[StudentSummary]
    total: int
    limit: int
    offset: int


def _summarise(student: StudentRelationship, person: Person | None) -> StudentSummary:
    return StudentSummary(
        id=str(student.id),
        person_id=str(student.person_id),
        full_name=person.display_name if person else "",
        reference=student.reference,
        kind_label=student.kind_label,
        status=student.status.value,
    )


@router.get(
    "/students",
    response_model=StudentPage,
    summary="List the students this person may see",
    dependencies=[Depends(RequirePermission(READ_STUDENTS))],
)
def list_students(
    db: DbSession,
    principal: CurrentPrincipal,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=120)] = None,
) -> StudentPage:
    """The list, the search and the total, all through one predicate.

    `search` narrows with `AND`, on top of the scope. A filter can only ever
    shrink the result — which is why searching for a name outside the caller's
    scope returns nothing rather than confirming it exists.
    """
    statement = scoped_select(
        StudentRelationship,
        people_scopes.STUDENT_RELATIONSHIPS,
        db=db,
        principal=principal,
        permission=READ_STUDENTS,
    )
    if search:
        statement = statement.where(
            StudentRelationship.person_id.in_(
                _person_ids_matching(db, principal, search)
            )
        )
        total = db.execute(
            statement.with_only_columns(StudentRelationship.id)
        ).scalars().all()
        total_count = len(total)
    else:
        total_count = scoped_count(
            StudentRelationship,
            people_scopes.STUDENT_RELATIONSHIPS,
            db=db,
            principal=principal,
            permission=READ_STUDENTS,
        )

    rows = db.execute(
        statement.order_by(StudentRelationship.created_at, StudentRelationship.id)
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    # Loaded through the owning module, from ids that came out of an
    # already-scoped query. A route never fetches a scoped row by id itself;
    # `test_boundaries.py` fails the commit that starts.
    found = people_service.people_by_ids(db, [row.person_id for row in rows])
    return StudentPage(
        items=[_summarise(row, found.get(row.person_id)) for row in rows],
        total=total_count,
        limit=limit,
        offset=offset,
    )


def _person_ids_matching(db, principal: Principal, search: str):
    """Names matching the search — themselves scoped, not merely filtered.

    Searching people through the people plan rather than through a bare `LIKE`
    means a search cannot become the one unscoped path into the table.
    """
    from sqlalchemy import func

    return (
        scoped_select(
            Person,
            people_scopes.PEOPLE,
            db=db,
            principal=principal,
            permission=READ_STUDENTS,
        )
        .with_only_columns(Person.id)
        .where(func.lower(Person.full_name).contains(search.strip().lower()))
    )


@router.get(
    "/students/{student_id}",
    response_model=StudentSummary,
    summary="One student, if this person may see them",
    dependencies=[Depends(RequirePermission(READ_STUDENTS))],
)
def read_student(
    student_id: uuid.UUID, db: DbSession, principal: CurrentPrincipal
) -> StudentSummary:
    student = scoped_get(
        StudentRelationship,
        student_id,
        people_scopes.STUDENT_RELATIONSHIPS,
        db=db,
        principal=principal,
        permission=READ_STUDENTS,
    )
    if student is None:
        # Deliberately the same response as an id that was never issued.
        raise errors.ResourceNotFound()
    found = people_service.people_by_ids(db, [student.person_id])
    return _summarise(student, found.get(student.person_id))
