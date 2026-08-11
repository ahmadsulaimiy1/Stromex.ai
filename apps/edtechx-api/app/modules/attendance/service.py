"""Taking a register, and everything that follows from having taken one.

The design target is thirty seconds. A teacher with a room in front of them,
on a phone, on a school's network, marks a full class and moves on. Everything
here is arranged around that:

  **The register arrives complete.** One call returns the people, in order, each
  already carrying the default mark. A teacher who has to tap thirty names to
  say "everyone is here" is a teacher who takes the register at lunchtime from
  memory, and that record is worth nothing.

  **Marking is one write.** The whole register goes in a single statement and a
  single transaction. Thirty round trips over a school's connection is the
  difference between thirty seconds and five minutes.

  **A part-marked register is a real state.** `open` is not a draft. A fire
  alarm at 09:04 must not lose the eleven marks already taken.

Who is in the register is *derived* from the open enrolments in that group on
that date (ADR-027), never from a stored list — a child who transferred in on
Monday appears on Monday without anybody rebuilding anything, and the register
for last March still shows March's class.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.attendance.models import (
    AttendanceAmendment,
    AttendanceCode,
    AttendanceMark,
    AttendanceSession,
    MarkCategory,
    SessionStatus,
)
from app.modules.audit.service import AuditAction, record
from app.modules.people import service as people


class AttendanceError(ValueError):
    """An operation the record would not survive."""


# --- codes ------------------------------------------------------------------


DEFAULT_CODES: tuple[tuple[str, str, MarkCategory, bool, bool], ...] = (
    # code, label, category, counts_as_present, requires_reason
    ("/", "Present", MarkCategory.present, True, False),
    ("L", "Late", MarkCategory.late, True, False),
    ("A", "Absent", MarkCategory.absent, False, True),
    ("E", "Excused", MarkCategory.excused, False, True),
)


def seed_codes(db: Session) -> int:
    """A starting point, not a policy.

    Four codes an institution can rename, recolour, extend or delete entirely.
    They exist because an empty code list makes the first register impossible,
    and a school should not have to design an attendance policy before it can
    find out whether the product works.
    """
    existing = {code.code for code in db.execute(select(AttendanceCode)).scalars().all()}
    created = 0
    for sequence, (code, label, category, present, needs_reason) in enumerate(
        DEFAULT_CODES
    ):
        if code in existing:
            continue
        db.add(
            AttendanceCode(
                code=code,
                label=label,
                category=category,
                counts_as_present=present,
                requires_reason=needs_reason,
                is_default=code == "/",
                sequence=sequence,
            )
        )
        created += 1
    db.flush()
    return created


def codes(db: Session) -> list[AttendanceCode]:
    return list(
        db.execute(
            select(AttendanceCode)
            .where(AttendanceCode.is_active.is_(True))
            .order_by(AttendanceCode.sequence, AttendanceCode.code)
        )
        .scalars()
        .all()
    )


def default_code(db: Session) -> AttendanceCode | None:
    available = codes(db)
    return next(
        (code for code in available if code.is_default),
        next((c for c in available if c.category is MarkCategory.present), None),
    )


# --- the register -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RegisterEntry:
    """One line of a register, ready to render."""

    student_relationship_id: uuid.UUID
    person_id: uuid.UUID
    name: str
    reference: str | None
    code_id: uuid.UUID | None
    code: str | None
    reason: str | None
    minutes_late: int | None
    is_marked: bool


@dataclass(frozen=True, slots=True)
class Register:
    session_id: uuid.UUID
    occurred_on: date
    slot: str
    status: str
    entries: tuple[RegisterEntry, ...]
    unanswered: tuple[uuid.UUID, ...]

    @property
    def is_complete(self) -> bool:
        return all(entry.is_marked for entry in self.entries)

    @property
    def can_submit(self) -> bool:
        """Complete, and with every code that demands an explanation given one."""
        return self.is_complete and not self.unanswered


def open_session(
    db: Session,
    *,
    occurred_on: date,
    class_group_id: uuid.UUID | None = None,
    course_id: uuid.UUID | None = None,
    academic_period_id: uuid.UUID | None = None,
    slot: str = "",
    membership_id: uuid.UUID | None = None,
) -> AttendanceSession:
    """Find or start the register for this moment.

    Idempotent by design. Two teachers opening the same register at the same
    moment — a class covered by somebody else, a page reloaded — must land on
    one register rather than on two that disagree.
    """
    if class_group_id is None and course_id is None:
        raise AttendanceError(
            "A register needs a class or a course, or nobody can say later who "
            "was in the room."
        )
    existing = db.execute(
        select(AttendanceSession).where(
            AttendanceSession.class_group_id == class_group_id,
            AttendanceSession.course_id == course_id,
            AttendanceSession.occurred_on == occurred_on,
            AttendanceSession.slot == slot,
        )
    ).scalars().first()
    if existing is not None:
        return existing

    session = AttendanceSession(
        class_group_id=class_group_id,
        course_id=course_id,
        academic_period_id=academic_period_id,
        occurred_on=occurred_on,
        slot=slot,
        taken_by_membership_id=membership_id,
    )
    db.add(session)
    db.flush()
    return session


def register(db: Session, session: AttendanceSession) -> Register:
    """Everyone who should be in this register, with whatever mark they have.

    Membership is derived from the open enrolments in the group on the day, so a
    child who joined on Monday is on Monday's register without anybody
    rebuilding a list — and March's register still shows March's class.
    """
    students = (
        people.students_in_class(
            db, session.class_group_id, on=session.occurred_on
        )
        if session.class_group_id
        else []
    )
    marks = {
        mark.student_relationship_id: mark
        for mark in db.execute(
            select(AttendanceMark).where(AttendanceMark.session_id == session.id)
        ).scalars().all()
    }
    by_id = {code.id: code for code in codes(db)}
    needs_reason = {code.id for code in by_id.values() if code.requires_reason}

    entries: list[RegisterEntry] = []
    unanswered: list[uuid.UUID] = []
    for student, person in students:
        mark = marks.get(student.id)
        code = by_id.get(mark.code_id) if mark else None
        if mark and mark.code_id in needs_reason and not (mark.reason or "").strip():
            unanswered.append(student.id)
        entries.append(
            RegisterEntry(
                student_relationship_id=student.id,
                person_id=person.id,
                name=person.display_name,
                reference=student.reference,
                code_id=mark.code_id if mark else None,
                code=code.code if code else None,
                reason=mark.reason if mark else None,
                minutes_late=mark.minutes_late if mark else None,
                is_marked=mark is not None,
            )
        )
    entries.sort(key=lambda e: (e.name.lower(), str(e.student_relationship_id)))
    return Register(
        session_id=session.id,
        occurred_on=session.occurred_on,
        slot=session.slot,
        status=session.status.value,
        entries=tuple(entries),
        unanswered=tuple(unanswered),
    )


def mark_all(
    db: Session,
    session: AttendanceSession,
    *,
    code_id: uuid.UUID,
    membership_id: uuid.UUID | None = None,
) -> int:
    """Give everybody unmarked the same code. The thirty-second path.

    A teacher who has to tap thirty names to say "everyone is here" takes the
    register at lunchtime from memory instead, and that record is worth nothing.
    Deliberately leaves existing marks alone: somebody already marked late does
    not become present because the room was then marked in.
    """
    current = register(db, session)
    unmarked = [e.student_relationship_id for e in current.entries if not e.is_marked]
    if not unmarked:
        return 0
    return set_marks(
        db,
        session,
        dict.fromkeys(unmarked, code_id),
        membership_id=membership_id,
    )


def set_marks(
    db: Session,
    session: AttendanceSession,
    marks: dict[uuid.UUID, uuid.UUID],
    *,
    reasons: dict[uuid.UUID, str] | None = None,
    minutes_late: dict[uuid.UUID, int] | None = None,
    membership_id: uuid.UUID | None = None,
    amendment_reason: str | None = None,
) -> int:
    """Record a whole register in one transaction.

    Every change to an existing mark writes an amendment, so a corrected
    register can always answer who changed it and why. Correcting a *submitted*
    register requires a reason: the first correction is the teacher finishing
    the job, and the second is somebody changing a record that has been relied
    on.
    """
    if session.status is SessionStatus.submitted and not (amendment_reason or "").strip():
        raise AttendanceError(
            "Changing a submitted register needs a reason. The record has "
            "already been relied on."
        )

    known = {code.id for code in codes(db)}
    unknown = sorted(str(c) for c in set(marks.values()) - known)
    if unknown:
        raise AttendanceError(f"Not attendance codes of this institution: {unknown}")

    existing = {
        mark.student_relationship_id: mark
        for mark in db.execute(
            select(AttendanceMark).where(
                AttendanceMark.session_id == session.id,
                AttendanceMark.student_relationship_id.in_(list(marks)),
            )
        ).scalars().all()
    }
    now = datetime.now(UTC)
    reasons = reasons or {}
    minutes_late = minutes_late or {}
    changed = 0

    for student_id, code_id in marks.items():
        reason = reasons.get(student_id)
        mark = existing.get(student_id)
        if mark is None:
            db.add(
                AttendanceMark(
                    session_id=session.id,
                    student_relationship_id=student_id,
                    code_id=code_id,
                    reason=reason,
                    minutes_late=minutes_late.get(student_id),
                    recorded_by_membership_id=membership_id,
                    recorded_at=now,
                )
            )
            changed += 1
            continue

        if mark.code_id == code_id and (reason is None or reason == mark.reason):
            continue
        db.add(
            AttendanceAmendment(
                mark_id=mark.id,
                previous_code_id=mark.code_id,
                new_code_id=code_id,
                previous_reason=mark.reason,
                reason=(amendment_reason or "Register completed").strip(),
                actor_membership_id=membership_id,
                occurred_at=now,
            )
        )
        mark.code_id = code_id
        if reason is not None:
            mark.reason = reason
        if student_id in minutes_late:
            mark.minutes_late = minutes_late[student_id]
        mark.recorded_by_membership_id = membership_id
        mark.recorded_at = now
        changed += 1

    if session.status is SessionStatus.submitted:
        session.status = SessionStatus.amended
    db.flush()
    return changed


def submit(
    db: Session, session: AttendanceSession, *, membership_id: uuid.UUID | None = None
) -> AttendanceSession:
    """Close the register. Refuses while it would be a misleading record.

    Two refusals, both about what the record would mean. A register missing
    people says nothing about them, and a register with an unexplained absence
    is the one somebody will need the explanation for.
    """
    current = register(db, session)
    if not current.is_complete:
        missing = sum(1 for entry in current.entries if not entry.is_marked)
        raise AttendanceError(
            f"{missing} person(s) have no mark. An incomplete register says "
            "nothing about them."
        )
    if current.unanswered:
        raise AttendanceError(
            f"{len(current.unanswered)} mark(s) need a reason before this "
            "register can be submitted."
        )
    session.status = SessionStatus.submitted
    session.submitted_at = datetime.now(UTC)
    session.taken_by_membership_id = session.taken_by_membership_id or membership_id
    db.flush()
    record(
        db,
        action=AuditAction.publish,
        resource_type="attendance_session",
        resource_id=session.id,
        after={"occurred_on": str(session.occurred_on), "slot": session.slot},
    )
    return session


# --- reading it back --------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AttendanceSummary:
    """One student's attendance over a span, with the figure and its parts."""

    sessions: int
    present: int
    absent: int
    late: int
    excused: int

    @property
    def rate(self) -> float | None:
        """Present as a proportion, or `None` when nothing was recorded.

        `None` rather than zero, and the distinction is the whole point: a
        student with no sessions has not attended nothing, they have no record —
        and a progression rule reading zero would hold them back for it
        (`academics.progression` treats missing data as missing, never as a
        failure).
        """
        if self.sessions == 0:
            return None
        return self.present / self.sessions


def summarise(
    db: Session,
    student_relationship_id: uuid.UUID,
    *,
    since: date | None = None,
    until: date | None = None,
) -> AttendanceSummary:
    statement = (
        select(AttendanceMark, AttendanceCode, AttendanceSession)
        .join(AttendanceCode, AttendanceCode.id == AttendanceMark.code_id)
        .join(AttendanceSession, AttendanceSession.id == AttendanceMark.session_id)
        .where(AttendanceMark.student_relationship_id == student_relationship_id)
    )
    if since is not None:
        statement = statement.where(AttendanceSession.occurred_on >= since)
    if until is not None:
        statement = statement.where(AttendanceSession.occurred_on <= until)

    rows = db.execute(statement).all()
    present = sum(1 for _mark, code, _s in rows if code.counts_as_present)
    return AttendanceSummary(
        sessions=len(rows),
        present=present,
        absent=sum(1 for _m, code, _s in rows if code.category is MarkCategory.absent),
        late=sum(1 for _m, code, _s in rows if code.category is MarkCategory.late),
        excused=sum(1 for _m, code, _s in rows if code.category is MarkCategory.excused),
    )


def amendments_for(db: Session, mark_id: uuid.UUID) -> list[AttendanceAmendment]:
    return list(
        db.execute(
            select(AttendanceAmendment)
            .where(AttendanceAmendment.mark_id == mark_id)
            .order_by(AttendanceAmendment.occurred_at)
        )
        .scalars()
        .all()
    )
