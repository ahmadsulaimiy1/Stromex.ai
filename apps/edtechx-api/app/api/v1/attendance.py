"""The register, over HTTP. Three calls, and the whole point is that it is three.

A teacher on a phone, in a room, on a school's network. Open the register, mark
it, submit it. Every extra round trip is a second they do not have, so the first
call returns everybody already in order with whatever mark they have, and the
second takes the entire register in one request.

Entitlement and permission are declared separately (ADR-030) and checked in that
order: what this person may do, then what the institution has bought.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import (
    CurrentPrincipal,
    DbSession,
    RequireEntitlement,
    RequirePermission,
)
from app.core import errors
from app.modules.attendance import scopes as attendance_scopes
from app.modules.attendance import service as attendance
from app.modules.attendance.models import AttendanceSession
from app.modules.authz.predicates import scoped_get

router = APIRouter(tags=["attendance"], prefix="/attendance")

READ = "attendance.mark.read"
WRITE = "attendance.mark.write"
FEATURE = "core.attendance"


class CodeOut(BaseModel):
    id: str
    code: str
    label: str
    category: str
    counts_as_present: bool
    requires_reason: bool
    is_default: bool
    colour: str | None


class EntryOut(BaseModel):
    student_relationship_id: str
    name: str
    reference: str | None
    code_id: str | None
    code: str | None
    reason: str | None
    minutes_late: int | None
    is_marked: bool


class RegisterOut(BaseModel):
    session_id: str
    occurred_on: date
    slot: str
    status: str
    entries: list[EntryOut]
    codes: list[CodeOut]
    default_code_id: str | None
    marked: int
    total: int
    needs_reason: list[str]
    can_submit: bool


class MarkIn(BaseModel):
    student_relationship_id: uuid.UUID
    code_id: uuid.UUID
    reason: str | None = Field(default=None, max_length=500)
    minutes_late: int | None = Field(default=None, ge=0, le=600)


class MarkRequest(BaseModel):
    marks: list[MarkIn] = Field(default_factory=list, max_length=500)
    # Required once a register has been submitted; the record has been relied on.
    amendment_reason: str | None = Field(default=None, max_length=500)


def _session_or_404(db, principal, session_id: uuid.UUID) -> AttendanceSession:
    found = scoped_get(
        AttendanceSession, session_id, attendance_scopes.SESSIONS,
        db=db, principal=principal, permission=READ,
    )
    if found is None:
        # The same answer as an id that was never issued: a teacher must not be
        # able to learn that another class took a register by probing.
        raise errors.ResourceNotFound()
    return found


def _render(db, session: AttendanceSession) -> RegisterOut:
    current = attendance.register(db, session)
    available = attendance.codes(db)
    default = attendance.default_code(db)
    return RegisterOut(
        session_id=str(current.session_id),
        occurred_on=current.occurred_on,
        slot=current.slot,
        status=current.status,
        entries=[
            EntryOut(
                student_relationship_id=str(e.student_relationship_id),
                name=e.name, reference=e.reference,
                code_id=str(e.code_id) if e.code_id else None, code=e.code,
                reason=e.reason, minutes_late=e.minutes_late, is_marked=e.is_marked,
            )
            for e in current.entries
        ],
        codes=[
            CodeOut(
                id=str(c.id), code=c.code, label=c.label, category=c.category.value,
                counts_as_present=c.counts_as_present,
                requires_reason=c.requires_reason, is_default=c.is_default,
                colour=c.colour,
            )
            for c in available
        ],
        default_code_id=str(default.id) if default else None,
        marked=sum(1 for e in current.entries if e.is_marked),
        total=len(current.entries),
        needs_reason=[str(i) for i in current.unanswered],
        can_submit=current.can_submit,
    )


@router.post(
    "/register",
    response_model=RegisterOut,
    summary="Open today's register and return everybody in it",
    dependencies=[
        Depends(RequirePermission(WRITE)),
        Depends(RequireEntitlement(FEATURE)),
    ],
)
def open_register(
    db: DbSession,
    principal: CurrentPrincipal,
    class_group_id: uuid.UUID | None = None,
    course_id: uuid.UUID | None = None,
    occurred_on: date | None = None,
    slot: str = "",
) -> RegisterOut:
    """One call: the register, the people, the codes, and the default.

    Idempotent — reopening returns the register already in progress rather than
    starting a second one that disagrees with it.
    """
    try:
        session = attendance.open_session(
            db,
            occurred_on=occurred_on or date.today(),
            class_group_id=class_group_id,
            course_id=course_id,
            slot=slot,
            membership_id=principal.membership_id,
        )
    except attendance.AttendanceError as exc:
        raise errors.ValidationFailed({"class_group_id": str(exc)}) from exc
    # Opening tells you nothing you could not already see: the scope check is
    # the same one a read would make.
    _session_or_404(db, principal, session.id)
    return _render(db, session)


@router.post(
    "/register/{session_id}/marks",
    response_model=RegisterOut,
    summary="Record the whole register in one request",
    dependencies=[
        Depends(RequirePermission(WRITE)),
        Depends(RequireEntitlement(FEATURE)),
    ],
)
def record_marks(
    session_id: uuid.UUID,
    request: MarkRequest,
    db: DbSession,
    principal: CurrentPrincipal,
) -> RegisterOut:
    session = _session_or_404(db, principal, session_id)
    try:
        attendance.set_marks(
            db,
            session,
            {m.student_relationship_id: m.code_id for m in request.marks},
            reasons={m.student_relationship_id: m.reason for m in request.marks
                     if m.reason is not None},
            minutes_late={m.student_relationship_id: m.minutes_late
                          for m in request.marks if m.minutes_late is not None},
            membership_id=principal.membership_id,
            amendment_reason=request.amendment_reason,
        )
    except attendance.AttendanceError as exc:
        raise errors.ValidationFailed({"marks": str(exc)}) from exc
    return _render(db, session)


@router.post(
    "/register/{session_id}/submit",
    response_model=RegisterOut,
    summary="Close the register",
    dependencies=[
        Depends(RequirePermission(WRITE)),
        Depends(RequireEntitlement(FEATURE)),
    ],
)
def submit_register(
    session_id: uuid.UUID, db: DbSession, principal: CurrentPrincipal
) -> RegisterOut:
    session = _session_or_404(db, principal, session_id)
    try:
        attendance.submit(db, session, membership_id=principal.membership_id)
    except attendance.AttendanceError as exc:
        raise errors.ValidationFailed({"register": str(exc)}) from exc
    return _render(db, session)
