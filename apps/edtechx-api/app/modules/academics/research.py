"""Research candidature: supervision, milestones, and the record of meeting.

`structure.py` already declared the *vocabulary* of research education — a
programme may be a research programme, an institution may name its supervision
roles, a programme may require a proposal at month six and a viva at month
forty-eight. What it deliberately deferred was the records: which supervisor
supervises whom, whether this researcher's proposal actually happened, and when
anybody last sat down together.

Those records are here, and they are not a doctoral product bolted onto the
side. They are three more rows in the universal academic model, and they serve
a final-year undergraduate with a dissertation supervisor exactly as well as
they serve a PhD candidate. An institution that supervises nobody has none of
them and never learns they exist.

Three decisions that could each have gone the other way:

**Supervision is a placement, not a pointer.** The tempting column is
`student.supervisor_id`. It is one join shorter and it erases the fact that
somebody else supervised the first two years — which is exactly the fact a
thesis examiner, an appeal, and a funder all ask about. So supervision is a row
with a beginning and an end, for the same reason enrolment is.

**Overdue is computed, never stored.** A milestone's `state` records what the
institution *decided*; whether it is late is arithmetic on today's date against
`due_on`. A stored `overdue` flag needs a nightly job, is wrong between midnight
and the job running, and is wrong for a whole weekend when the job fails. There
is no such column, and `Milestone.is_overdue` is a property.

**A meeting is a fact; the gap between meetings is the signal.** Research
degrees rarely fail because a supervision meeting went badly. They fail because
the meetings quietly stopped and nobody noticed for eleven months. The meeting
row exists so that absence is measurable, which is why `SupervisionMeeting` is
worth a table of its own rather than a note on the milestone.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey

__all__ = [
    "DECIDED_STATES",
    "Milestone",
    "MilestoneState",
    "Supervision",
    "SupervisionMeeting",
]


class MilestoneState(str, enum.Enum):
    """What has happened to one required checkpoint.

    Note what is absent: `overdue`. Lateness is a relation between `due_on` and
    today, not a decision anybody records, and the moment it becomes a stored
    state the system starts telling researchers they are late on the day a cron
    job happens to run.

    `referred` is the state most systems omit and every research degree needs:
    the panel neither passed nor failed the candidate, it asked for the work
    again by a date. Collapsing it into `failed` is how a routine second attempt
    becomes a permanent mark on somebody's record.
    """

    expected = "expected"
    scheduled = "scheduled"
    submitted = "submitted"
    passed = "passed"
    referred = "referred"
    failed = "failed"
    waived = "waived"


#: The states that mean somebody has ruled on this milestone. A decision date is
#: required for exactly these and refused for the others, in the database.
DECIDED_STATES: frozenset[MilestoneState] = frozenset(
    {
        MilestoneState.passed,
        MilestoneState.referred,
        MilestoneState.failed,
        MilestoneState.waived,
    }
)

_DECIDED_SQL = "('passed', 'referred', 'failed', 'waived')"


class Supervision(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One member of staff supervising one researcher, in one named role, for a span.

    The supervisor is a `StaffRelationship` rather than a `Person`, which is
    what makes an external co-supervisor expressible without a second table:
    the institution records them as staff with its own `kind_label` and no
    login, and every query here works unchanged.
    """

    __tablename__ = "supervisions"
    __table_args__ = (
        CheckConstraint(
            "ended_on IS NULL OR ended_on >= started_on",
            name="ends_after_start",
        ),
        # One *open* supervision per researcher, supervisor and role. A closed
        # one may repeat, because a supervisor who steps away and returns is two
        # spans and both are true.
        Index(
            "uq_supervisions_open",
            "tenant_id",
            "student_relationship_id",
            "staff_relationship_id",
            "supervision_role_id",
            unique=True,
            postgresql_where=text("ended_on IS NULL"),
        ),
        Index(
            "ix_supervisions_tenant_supervisor",
            "tenant_id",
            "staff_relationship_id",
            "ended_on",
        ),
        Index(
            "ix_supervisions_tenant_researcher",
            "tenant_id",
            "student_relationship_id",
        ),
    )

    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    staff_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("staff_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supervision_role_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("supervision_roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date)
    # Why the span closed, in the institution's words: "completed", "on leave",
    # "transferred to Professor Adeyemi". Never read by the platform.
    ended_reason: Mapped[str | None] = mapped_column(String(200))
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @property
    def is_open(self) -> bool:
        return self.ended_on is None


class Milestone(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One researcher's instance of one checkpoint their programme requires.

    Materialised from `MilestoneDefinition` when candidature opens, so that the
    dates exist before anybody is late for them. A definition added to the
    programme afterwards is planned onto the researchers who are still in
    candidature and left alone for the ones who have finished — a rule change
    does not retroactively make a graduate delinquent.
    """

    __tablename__ = "research_milestones"
    __table_args__ = (
        Index(
            "uq_research_milestones_researcher_definition",
            "tenant_id",
            "student_relationship_id",
            "milestone_definition_id",
            unique=True,
        ),
        CheckConstraint(
            f"(state IN {_DECIDED_SQL}) = (decided_on IS NOT NULL)",
            name="decision_dated",
        ),
        # A decision cannot predate the submission it ruled on. Cheap, and it
        # catches the backdating typo that would otherwise sit in a candidate's
        # record until an examiner queried it years later.
        CheckConstraint(
            "submitted_on IS NULL OR decided_on IS NULL OR decided_on >= submitted_on",
            name="decision_after_submission",
        ),
        Index("ix_research_milestones_tenant_due", "tenant_id", "due_on"),
    )

    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    milestone_definition_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("milestone_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    state: Mapped[MilestoneState] = mapped_column(
        Enum(MilestoneState, name="milestone_state"),
        nullable=False,
        default=MilestoneState.expected,
    )
    # Nullable, because an institution may require a milestone without dating
    # it — "an upgrade viva, when the supervisor judges the work ready".
    due_on: Mapped[date | None] = mapped_column(Date)
    scheduled_for: Mapped[date | None] = mapped_column(Date)
    submitted_on: Mapped[date | None] = mapped_column(Date)
    decided_on: Mapped[date | None] = mapped_column(Date)
    # The panel's words for the outcome, which are not the state: "pass with
    # minor corrections", "referred, resubmit within twelve months".
    outcome_label: Mapped[str | None] = mapped_column(String(200))
    note: Mapped[str | None] = mapped_column(Text)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @property
    def is_decided(self) -> bool:
        return self.state in DECIDED_STATES

    def is_overdue(self, *, on: date) -> bool:
        """Late as of `on` — arithmetic, not a column.

        `expected` is the only state this can be true in, and that is the whole
        definition: overdue means the date has passed and *nothing has
        happened*. A viva with a date in the diary is not overdue because the
        diary date is in December; a thesis sitting with examiners is not
        overdue because the candidate has done their part. Flagging either red
        is how a research office learns to ignore the flag.

        A milestone somebody has ruled on is likewise never overdue, however
        late the ruling was; the record of the delay is `decided_on` against
        `due_on`, and a researcher who passed their upgrade six weeks late does
        not carry a red mark for the remaining thirty months.
        """
        if self.due_on is None or self.state is not MilestoneState.expected:
            return False
        return on > self.due_on


class SupervisionMeeting(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """That a meeting happened, when, and what was agreed.

    Two dates for the reason `EnrolmentEvent` has two: `held_on` is when the
    meeting took place, `created_at` is when somebody wrote it up, and in
    research supervision those are routinely a fortnight apart.

    The summary is the institution's record, not a transcript, and it is
    readable by the researcher it concerns. That is a deliberate constraint on
    what belongs in it: a supervisor's private concerns about a candidate are a
    safeguarding or pastoral record with its own permission, not a note on a
    row the candidate can open.
    """

    __tablename__ = "supervision_meetings"
    __table_args__ = (
        Index(
            "ix_supervision_meetings_tenant_researcher",
            "tenant_id",
            "student_relationship_id",
            "held_on",
        ),
    )

    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Nullable so a meeting survives the departure of the person who held it.
    staff_relationship_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("staff_relationships.id", ondelete="SET NULL")
    )
    held_on: Mapped[date] = mapped_column(Date, nullable=False)
    next_meeting_on: Mapped[date | None] = mapped_column(Date)
    summary: Mapped[str | None] = mapped_column(Text)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
