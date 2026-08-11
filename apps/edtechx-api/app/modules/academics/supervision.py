"""Reading and writing a candidature.

Two questions, and the whole module exists to answer them well:

  *Where am I?* — asked by a researcher, answered by a position on a track that
  is years long, not by a list of things due this week. A doctorate is the only
  thing EdirasX models where the interesting unit of time is the year and the
  interesting fact is how much of it is left.

  *Who is drifting?* — asked by a supervisor, and answered by two numbers no
  taught-course product computes: how long since this candidate was last seen,
  and how far past its date the next milestone is. Research degrees fail
  quietly, and both of those go wrong months before anybody files a concern.

Everything here reads through `scoped_select`, so a supervisor's caseload is
their caseload because the SQL says so, not because a template filtered a list
somebody had already fetched.
"""

from __future__ import annotations

import calendar
import uuid
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import Principal
from app.modules.academics import scopes as research_scopes
from app.modules.academics.research import (
    DECIDED_STATES,
    Milestone,
    MilestoneState,
    Supervision,
    SupervisionMeeting,
)
from app.modules.academics.structure import MilestoneDefinition, SupervisionRole
from app.modules.authz.predicates import scoped_select
from app.modules.people import service as people

__all__ = [
    "Candidature",
    "CandidatureMilestone",
    "CaseloadEntry",
    "SupervisorRecord",
    "assign_supervisor",
    "candidature",
    "caseload",
    "end_supervision",
    "log_meeting",
    "plan_milestones",
    "record_milestone",
]


def add_months(start: date, months: int) -> date:
    """Calendar arithmetic that never produces 31 February.

    Written out rather than pulled from a dependency because a milestone date
    is a date an institution will hold somebody to, and "the last day of the
    month, unless the month is shorter, in which case the last day of that"
    is the rule every research office already uses.
    """
    total = start.month - 1 + months
    year = start.year + total // 12
    month = total % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def months_between(start: date, end: date) -> int:
    """Whole months elapsed, floor. Negative before the start."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


# --- writing ----------------------------------------------------------------


def assign_supervisor(
    db: Session,
    *,
    student_relationship_id: uuid.UUID,
    staff_relationship_id: uuid.UUID,
    supervision_role_id: uuid.UUID,
    on: date,
) -> Supervision:
    """Open a supervision span. Idempotent for a span that is already open."""
    existing = db.execute(
        select(Supervision).where(
            Supervision.student_relationship_id == student_relationship_id,
            Supervision.staff_relationship_id == staff_relationship_id,
            Supervision.supervision_role_id == supervision_role_id,
            Supervision.ended_on.is_(None),
        )
    ).scalars().first()
    if existing is not None:
        return existing
    row = Supervision(
        student_relationship_id=student_relationship_id,
        staff_relationship_id=staff_relationship_id,
        supervision_role_id=supervision_role_id,
        started_on=on,
    )
    db.add(row)
    db.flush()
    return row


def end_supervision(
    db: Session, supervision: Supervision, *, on: date, reason: str = ""
) -> Supervision:
    supervision.ended_on = on
    supervision.ended_reason = reason or None
    db.flush()
    return supervision


def plan_milestones(
    db: Session,
    *,
    student_relationship_id: uuid.UUID,
    programme_id: uuid.UUID,
    from_date: date,
) -> list[Milestone]:
    """Materialise this programme's requirements as dated records.

    Called when candidature opens, and safe to call again: a definition added
    to the programme afterwards is planned onto the candidates who are still
    working, and one that already has a record is left exactly as it is —
    including its dates, because a rule change must never silently move a date
    somebody has been working towards.
    """
    definitions = db.execute(
        select(MilestoneDefinition)
        .where(
            MilestoneDefinition.programme_id == programme_id,
            MilestoneDefinition.is_required.is_(True),
        )
        .order_by(MilestoneDefinition.sequence)
    ).scalars().all()
    have = {
        row.milestone_definition_id
        for row in db.execute(
            select(Milestone).where(
                Milestone.student_relationship_id == student_relationship_id
            )
        ).scalars()
    }
    planned: list[Milestone] = []
    for definition in definitions:
        if definition.id in have:
            continue
        row = Milestone(
            student_relationship_id=student_relationship_id,
            milestone_definition_id=definition.id,
            state=MilestoneState.expected,
            due_on=(
                add_months(from_date, definition.expected_offset_months)
                if definition.expected_offset_months is not None
                else None
            ),
        )
        db.add(row)
        planned.append(row)
    db.flush()
    return planned


class MilestoneTransitionRefused(ValueError):
    """A milestone was moved to a state its dates do not support."""


def record_milestone(
    db: Session,
    milestone: Milestone,
    *,
    state: MilestoneState,
    on: date,
    outcome_label: str = "",
    note: str = "",
) -> Milestone:
    """Move one milestone, keeping its dates and its state in agreement.

    The database enforces that a decided state carries a decision date; this
    refuses the other direction — a decision recorded before the submission it
    ruled on — with a message rather than an integrity error, because a research
    administrator typing a date is the ordinary path here and a stack trace is
    not an answer.
    """
    if state in DECIDED_STATES:
        if milestone.submitted_on is not None and on < milestone.submitted_on:
            raise MilestoneTransitionRefused(
                f"A decision dated {on} cannot rule on work submitted on "
                f"{milestone.submitted_on}."
            )
        milestone.decided_on = on
    elif state is MilestoneState.submitted:
        milestone.submitted_on = on
        milestone.decided_on = None
    elif state is MilestoneState.scheduled:
        milestone.scheduled_for = on
        milestone.decided_on = None
    else:
        milestone.decided_on = None
    milestone.state = state
    if outcome_label:
        milestone.outcome_label = outcome_label
    if note:
        milestone.note = note
    db.flush()
    return milestone


def log_meeting(
    db: Session,
    *,
    student_relationship_id: uuid.UUID,
    held_on: date,
    staff_relationship_id: uuid.UUID | None = None,
    summary: str = "",
    next_meeting_on: date | None = None,
) -> SupervisionMeeting:
    row = SupervisionMeeting(
        student_relationship_id=student_relationship_id,
        staff_relationship_id=staff_relationship_id,
        held_on=held_on,
        summary=summary or None,
        next_meeting_on=next_meeting_on,
    )
    db.add(row)
    db.flush()
    return row


# --- reading ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CandidatureMilestone:
    """One checkpoint, with the words to describe it and the arithmetic done."""

    name: str
    code: str
    sequence: int
    state: MilestoneState
    due_on: date | None
    decided_on: date | None
    submitted_on: date | None
    scheduled_for: date | None
    outcome_label: str | None
    offset_months: int | None
    is_overdue: bool

    @property
    def is_decided(self) -> bool:
        return self.state in DECIDED_STATES

    @property
    def when(self) -> date | None:
        """The one date worth showing: what happened, or what is expected."""
        return self.decided_on or self.scheduled_for or self.submitted_on or self.due_on


@dataclass(frozen=True, slots=True)
class SupervisorRecord:
    name: str
    role: str
    is_primary: bool
    since: date


@dataclass(slots=True)
class Candidature:
    """Everything a research candidate's own screen is made of.

    `horizon_months` is derived from the programme's own last requirement
    rather than from a duration column, because the institution has already
    said when it expects a thesis by putting an offset on the submission
    milestone, and asking it to say so twice is how the two disagree.
    """

    researcher: str
    reference: str | None
    started_on: date
    on: date
    milestones: list[CandidatureMilestone] = field(default_factory=list)
    supervisors: list[SupervisorRecord] = field(default_factory=list)
    meetings: list[SupervisionMeeting] = field(default_factory=list)

    @property
    def horizon_months(self) -> int:
        offsets = [m.offset_months for m in self.milestones if m.offset_months]
        return max(offsets) if offsets else 0

    @property
    def elapsed_months(self) -> int:
        return max(0, months_between(self.started_on, self.on))

    @property
    def completed(self) -> int:
        return sum(1 for m in self.milestones if m.state is MilestoneState.passed)

    @property
    def overdue(self) -> list[CandidatureMilestone]:
        return [m for m in self.milestones if m.is_overdue]

    @property
    def next_requirement(self) -> CandidatureMilestone | None:
        """The earliest undecided checkpoint. Overdue ones come first."""
        pending = [m for m in self.milestones if not m.is_decided]
        if not pending:
            return None
        return min(pending, key=lambda m: (m.due_on or date.max, m.sequence))

    @property
    def last_meeting(self) -> SupervisionMeeting | None:
        return self.meetings[0] if self.meetings else None

    @property
    def days_since_meeting(self) -> int | None:
        last = self.last_meeting
        return None if last is None else (self.on - last.held_on).days


def _milestone_view(
    row: Milestone, definition: MilestoneDefinition, *, on: date
) -> CandidatureMilestone:
    return CandidatureMilestone(
        name=definition.name,
        code=definition.code,
        sequence=definition.sequence,
        state=row.state,
        due_on=row.due_on,
        decided_on=row.decided_on,
        submitted_on=row.submitted_on,
        scheduled_for=row.scheduled_for,
        outcome_label=row.outcome_label,
        offset_months=definition.expected_offset_months,
        is_overdue=row.is_overdue(on=on),
    )


def candidature(
    db: Session,
    principal: Principal | None,
    *,
    student_relationship_id: uuid.UUID,
    on: date,
    started_on: date | None = None,
) -> Candidature:
    """One researcher's whole position, read under the caller's own scope.

    A supervisor calling this for somebody they do not supervise gets a
    candidature with no milestones rather than a refusal, for the same reason
    `scoped_get` returns `None`: "you may not see this" and "there is nothing
    here" must be the same answer.

    Candidature begins when the placement begins, and that is read from the
    enrolment rather than passed in — a second source for the same date is a
    second source to disagree. Research intake is continuous, so that date is
    routinely a Tuesday in April with no academic year attached to it, which is
    exactly why every structural layer on an enrolment is optional.
    """
    student = people.student(db, student_relationship_id)
    person = people.person(db, student.person_id) if student else None
    if started_on is None:
        placements = people.open_enrolments(db, student) if student else []
        started_on = min((p.started_on for p in placements), default=on)

    rows = db.execute(
        scoped_select(
            Milestone,
            research_scopes.MILESTONES,
            db=db,
            principal=principal,
            permission="research.milestone.read",
        ).where(Milestone.student_relationship_id == student_relationship_id)
    ).scalars().all()
    definitions = {
        d.id: d
        for d in db.execute(
            select(MilestoneDefinition).where(
                MilestoneDefinition.id.in_([r.milestone_definition_id for r in rows])
            )
        ).scalars()
    }
    milestones = sorted(
        (
            _milestone_view(row, definitions[row.milestone_definition_id], on=on)
            for row in rows
            if row.milestone_definition_id in definitions
        ),
        key=lambda m: m.sequence,
    )

    supervisions = db.execute(
        scoped_select(
            Supervision,
            research_scopes.SUPERVISIONS,
            db=db,
            principal=principal,
            permission="research.supervision.read",
        ).where(
            Supervision.student_relationship_id == student_relationship_id,
            Supervision.ended_on.is_(None),
        )
    ).scalars().all()
    supervisors = sorted(
        (_supervisor_view(db, s) for s in supervisions),
        key=lambda s: (not s.is_primary, s.name),
    )

    meetings = db.execute(
        scoped_select(
            SupervisionMeeting,
            research_scopes.SUPERVISION_MEETINGS,
            db=db,
            principal=principal,
            permission="research.meeting.read",
        )
        .where(SupervisionMeeting.student_relationship_id == student_relationship_id)
        .order_by(SupervisionMeeting.held_on.desc())
    ).scalars().all()

    return Candidature(
        researcher=person.full_name if person else "",
        reference=student.reference if student else None,
        started_on=started_on,
        on=on,
        milestones=milestones,
        supervisors=supervisors,
        meetings=list(meetings),
    )


def _supervisor_view(db: Session, supervision: Supervision) -> SupervisorRecord:
    staff = people.staff(db, supervision.staff_relationship_id)
    person = people.person(db, staff.person_id) if staff else None
    role = db.get(SupervisionRole, supervision.supervision_role_id)
    return SupervisorRecord(
        name=person.full_name if person else "",
        role=role.name if role else "Supervisor",
        is_primary=bool(role.is_primary) if role else False,
        since=supervision.started_on,
    )


@dataclass(frozen=True, slots=True)
class CaseloadEntry:
    """One researcher as their supervisor needs to see them."""

    student_relationship_id: uuid.UUID
    researcher: str
    reference: str | None
    role: str
    since: date
    candidature: Candidature

    @property
    def needs_attention(self) -> bool:
        """The two ways a research degree goes wrong before anybody files a concern."""
        return bool(self.candidature.overdue) or self.is_out_of_contact

    @property
    def is_out_of_contact(self) -> bool:
        gap = self.candidature.days_since_meeting
        return gap is None or gap > CONTACT_GAP_DAYS


#: What counts as out of contact. Not a regulation — institutions differ, and
#: this becomes a policy row the moment one of them says a different number.
#: Stated here as one named constant rather than scattered as `> 90`.
CONTACT_GAP_DAYS: int = 90


def caseload(
    db: Session, principal: Principal | None, *, on: date
) -> list[CaseloadEntry]:
    """Every researcher this principal currently supervises, worst first.

    Two narrowings, and both are load-bearing. The scope decides what may be
    read at all; the caller's own staff record decides what is *theirs*. Only
    the second turns a readable list into a caseload — a supervisor legitimately
    sees the co-supervisor on their candidate, and without this a candidate with
    two supervisors would appear twice on both their lists.

    A person with no staff record has no caseload, which is why a registrar
    reading this gets nothing rather than the whole graduate school. That list
    exists, it is a different question, and it belongs on a different screen.
    """
    mine = people.staff_for_user(db, principal.user_id if principal else None)
    if mine is None:
        return []

    supervisions = db.execute(
        scoped_select(
            Supervision,
            research_scopes.SUPERVISIONS,
            db=db,
            principal=principal,
            permission="research.supervision.read",
        ).where(
            Supervision.ended_on.is_(None),
            Supervision.staff_relationship_id == mine.id,
        )
    ).scalars().all()

    entries: list[CaseloadEntry] = []
    seen: set[uuid.UUID] = set()
    for supervision in supervisions:
        if supervision.student_relationship_id in seen:
            continue
        seen.add(supervision.student_relationship_id)
        student = people.student(db, supervision.student_relationship_id)
        person = people.person(db, student.person_id) if student else None
        role = db.get(SupervisionRole, supervision.supervision_role_id)
        entries.append(
            CaseloadEntry(
                student_relationship_id=supervision.student_relationship_id,
                researcher=person.full_name if person else "",
                reference=student.reference if student else None,
                role=role.name if role else "Supervisor",
                since=supervision.started_on,
                candidature=candidature(
                    db,
                    principal,
                    student_relationship_id=supervision.student_relationship_id,
                    on=on,
                ),
            )
        )
    return sorted(
        entries,
        key=lambda e: (
            not e.candidature.overdue,
            not e.is_out_of_contact,
            e.researcher,
        ),
    )
