"""Enrolment as history, not as a pointer.

The tempting design is one column: `student.class_id`. It is simple, it is
fast, and it destroys the record. Move a child from 3A to 3B and the fact that
they spent two terms in 3A is gone — along with their attendance's meaning,
their result's context, and any honest answer to "which class was she in when
that happened?". A school that keeps records for a decade cannot be built on a
field that only ever knows the present.

So placement is a **row with a beginning and an end**. A transfer closes one
enrolment and opens another. A promotion closes one and opens another. A
withdrawal closes one and opens nothing. Nothing is overwritten, and the
sequence of rows *is* the student's academic history.

Alongside that sits an append-only ledger, `enrolment_events`, which records
why each transition happened, on what date it took effect, and who decided.
The two are different questions — "where was she?" and "why did she move?" —
and a registrar needs both. The ledger is protected the same way the audit log
is: the application role holds no UPDATE or DELETE on it, so the code is
structurally incapable of rewriting a student's history.

**Every academic layer is optional.** A nursery enrolment has a level and a
class group and no programme. A doctoral enrolment has a programme and a level
and neither. A rolling-intake literacy course has no academic year. The same
table serves all of them because it requires none of them.
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


class EnrolmentStatus(str, enum.Enum):
    """Where this particular placement stands.

    `suspended` covers deferral, intermission, and leave of absence — three
    words for one state, and which word an institution uses is terminology.
    """

    prospective = "prospective"
    active = "active"
    suspended = "suspended"
    ended = "ended"


class EnrolmentOutcome(str, enum.Enum):
    """Why a placement ended. Null while it is still open.

    Deliberately about the *enrolment*, not about the student. "Progressed"
    says this placement finished and the next one began; what the next one is
    is the next row's business.
    """

    progressed = "progressed"
    repeated = "repeated"
    transferred = "transferred"
    withdrawn = "withdrawn"
    completed = "completed"
    discontinued = "discontinued"


class EnrolmentEventKind(str, enum.Enum):
    """The vocabulary of the ledger.

    Fixed, because these are the transitions the product itself performs, and
    an open vocabulary would make the history unqueryable. What an institution
    *calls* each one is terminology; what happened is this.
    """

    admitted = "admitted"
    enrolled = "enrolled"
    placed = "placed"
    transferred = "transferred"
    suspended = "suspended"
    resumed = "resumed"
    withdrawn = "withdrawn"
    readmitted = "readmitted"
    progressed = "progressed"
    repeated = "repeated"
    completed = "completed"
    awarded = "awarded"
    corrected = "corrected"


class Enrolment(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One placement of one student, for one span of time.

    Every structural column is nullable. That is the whole point: the layers an
    institution does not use are absent rather than faked, and an enrolment
    that names only a programme is as valid as one that names only a class.

    Note that there is deliberately **no** unique constraint forcing a single
    open enrolment per student. Concurrent enrolment is ordinary — a joint
    honours student on two programmes, a pupil taking one course at a
    neighbouring institution, an apprentice enrolled both on a qualification
    and on a short competency unit. The service layer closes the previous
    placement when a transfer or a promotion says to; it does not assume that
    two open placements are a mistake.
    """

    __tablename__ = "enrolments"
    __table_args__ = (
        CheckConstraint(
            "ended_on IS NULL OR ended_on >= started_on",
            name="ends_after_start",
        ),
        # An open placement has no outcome, and a closed one is not left
        # unexplained. The two ends of the same invariant.
        CheckConstraint(
            "(ended_on IS NULL) = (outcome IS NULL)",
            name="outcome_matches_end",
        ),
        Index(
            "ix_enrolments_tenant_student",
            "tenant_id",
            "student_relationship_id",
            "started_on",
        ),
        Index("ix_enrolments_tenant_class_group", "tenant_id", "class_group_id"),
        Index("ix_enrolments_tenant_programme", "tenant_id", "programme_id"),
    )

    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # --- every one of these is optional ---
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="RESTRICT")
    )
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("programmes.id", ondelete="RESTRICT")
    )
    level_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("levels.id", ondelete="RESTRICT")
    )
    class_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="RESTRICT")
    )
    cohort_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="SET NULL")
    )

    status: Mapped[EnrolmentStatus] = mapped_column(
        Enum(EnrolmentStatus, name="enrolment_status"),
        nullable=False,
        default=EnrolmentStatus.prospective,
    )
    outcome: Mapped[EnrolmentOutcome | None] = mapped_column(
        Enum(EnrolmentOutcome, name="enrolment_outcome")
    )
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date)
    # Where this placement came from, so the chain can be walked in either
    # direction without reconstructing it from dates.
    previous_enrolment_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("enrolments.id", ondelete="SET NULL")
    )
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @property
    def is_open(self) -> bool:
        return self.ended_on is None


class EnrolmentEvent(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """The append-only record of what happened, and why.

    Two dates, deliberately. `occurred_on` is when the change took effect in
    the institution's world; `created_at` is when somebody typed it in. They
    are routinely weeks apart — a withdrawal backdated to the last day of term,
    a transfer recorded after the holidays — and a system with only one of them
    will eventually produce a register that nobody can reconcile.

    The application role holds no UPDATE or DELETE on this table (see
    `app.db.rls.grant_app_role`). A correction is a new event of kind
    `corrected`, not an edit.
    """

    __tablename__ = "enrolment_events"
    __table_args__ = (
        Index(
            "ix_enrolment_events_tenant_enrolment",
            "tenant_id",
            "enrolment_id",
            "occurred_on",
        ),
    )

    enrolment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("enrolments.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[EnrolmentEventKind] = mapped_column(
        Enum(EnrolmentEventKind, name="enrolment_event_kind"), nullable=False
    )
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    # What moved: previous and new placement ids, the progression rule's
    # reasoning, the imported row's line number. Whatever makes the event
    # explainable a decade later without the code that wrote it.
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class QualificationAward(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """What the institution awarded, when, and under what classification.

    The terminal state of a student's journey, and the one place the whole
    continuum has to meet: a certificate of attendance and a doctorate are the
    same row with different `qualification_id` values, because the
    qualification itself is configuration.

    `classification_label` is free text for the same reason. Honours divisions,
    Latin honours, distinction/merit/pass, competent/not-yet-competent — every
    one of those is an institution's own vocabulary, and an enum would encode
    one country's convention as the platform's opinion.
    """

    __tablename__ = "qualification_awards"
    __table_args__ = (
        Index(
            "uq_qualification_awards_tenant_reference",
            "tenant_id",
            "reference",
            unique=True,
            postgresql_where=text("reference IS NOT NULL"),
        ),
        Index(
            "ix_qualification_awards_tenant_student",
            "tenant_id",
            "student_relationship_id",
        ),
    )

    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    qualification_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("qualifications.id", ondelete="RESTRICT"), nullable=False
    )
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("programmes.id", ondelete="SET NULL")
    )
    enrolment_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("enrolments.id", ondelete="SET NULL")
    )
    awarded_on: Mapped[date] = mapped_column(Date, nullable=False)
    classification_label: Mapped[str | None] = mapped_column(String(80))
    # Certificate or award number, where the institution issues one.
    reference: Mapped[str | None] = mapped_column(String(64))
    awarded_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


__all__ = [
    "Enrolment",
    "EnrolmentEvent",
    "EnrolmentEventKind",
    "EnrolmentOutcome",
    "EnrolmentStatus",
    "QualificationAward",
]
