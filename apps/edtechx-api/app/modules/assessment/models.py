"""Marks, and the difference between a mark and a result.

The distinction this module exists to hold is one that most systems never draw
and every institution depends on:

    a **score** is what a teacher entered — working, revisable, theirs
    a **result** is what the institution has said — official, immutable, quoted

A system where entering a mark publishes it has no way to correct a
transcription error before a parent sees it, no way to moderate across two
teachers marking the same paper, and no way to answer "what did we actually
publish in July?" once somebody edits a cell in September. So the two are
different tables, and the boundary between them is an explicit institutional
act with a workflow in front of it.

**A published result is a snapshot, not a view.** It carries the mark *and the
grading it was given* — the band, the points, whether it passed — because a
school that changes its grade boundaries next year must not silently change
what it awarded last year. A transcript reprinted in 2031 has to say what the
2026 transcript said.

**The workflow is the institution's.** A school approves Teacher → Principal. A
university approves Lecturer → Programme Coordinator → Department → Board. A
research programme does something else again. So the steps are rows, and this
module knows only how to walk them.

**A correction after publication is an amendment, never an overwrite.** Previous
value, new value, actor, reason, timestamp — append-only at the database, on the
same principle as the audit log, the enrolment ledger and the attendance
amendments.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeletable, TenantOwned, Timestamped, UUIDPrimaryKey


class AssessmentStatus(str, enum.Enum):
    draft = "draft"
    open = "open"        # marks may be entered
    closed = "closed"    # entry finished; awaiting the result process
    cancelled = "cancelled"


class ResultStage(str, enum.Enum):
    """The lifecycle of an academic record.

    Platform-fixed *stages*, institution-defined *steps*. Every institution
    drafts, reviews, approves and publishes; what differs is who does each and
    how many of them there are, and that is `approval_workflows`.

    `published` is terminal. There is no transition out of it — a published
    result is corrected by an amendment, which is a new fact about it rather
    than a different value in it.
    """

    draft = "draft"
    submitted = "submitted"
    in_review = "in_review"
    approved = "approved"
    published = "published"
    withdrawn = "withdrawn"

    @property
    def is_official(self) -> bool:
        return self is ResultStage.published


class Assessment(UUIDPrimaryKey, Timestamped, SoftDeletable, TenantOwned, Base):
    """A thing that produces marks: a test, an essay, a practical, a viva.

    `kind_label` is the institution's word — "Test", "Coursework", "Continuous
    assessment", "Practical", "Viva". `weight` is how much it contributes where
    the institution combines several, and means nothing on its own.
    """

    __tablename__ = "assessments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_assessments_tenant_code"),
        CheckConstraint("max_score IS NULL OR max_score > 0", name="positive_maximum"),
        Index("ix_assessments_tenant_course", "tenant_id", "course_id"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind_label: Mapped[str] = mapped_column(String(60), nullable=False, default="Assessment")
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="RESTRICT")
    )
    class_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="RESTRICT")
    )
    academic_period_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_periods.id", ondelete="RESTRICT")
    )
    # Null for an assessment graded on a descriptor scale with no numeric
    # maximum — a competency judged met or not met has no mark out of anything.
    max_score: Mapped[float | None] = mapped_column(Numeric(10, 3))
    weight: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False, default=1)
    grading_scale_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("grading_scales.id", ondelete="RESTRICT")
    )
    due_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus, name="assessment_status"),
        nullable=False,
        default=AssessmentStatus.draft,
    )
    # Whether two markers are required before this can be submitted. A row,
    # because moderation is a departmental policy rather than a product opinion.
    requires_moderation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AssessmentScore(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One person's mark on one assessment. The teacher's working value.

    Editable, deliberately and for as long as the assessment is open. This is
    the row a teacher fixes when they misread a 6 as a 5, and nothing here has
    been said to anybody yet.
    """

    __tablename__ = "assessment_scores"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "assessment_id", "student_relationship_id",
            name="uq_assessment_scores_student",
        ),
        Index("ix_assessment_scores_tenant_student", "tenant_id",
              "student_relationship_id"),
    )

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Null is a real and different state from zero: not marked, versus marked
    # and worth nothing. A publication refuses to proceed on the first and
    # publishes the second.
    score: Mapped[float | None] = mapped_column(Numeric(10, 3))
    is_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    comment: Mapped[str | None] = mapped_column(Text)
    entered_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    entered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    moderated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    moderated_score: Mapped[float | None] = mapped_column(Numeric(10, 3))
    moderation_note: Mapped[str | None] = mapped_column(Text)

    @property
    def effective_score(self) -> float | None:
        """What counts: the moderator's mark where there is one."""
        return self.moderated_score if self.moderated_score is not None else self.score


class ApprovalWorkflow(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """Who has to agree before an academic record becomes official.

    Rows, because a school's Teacher → Principal and a university's Lecturer →
    Programme Coordinator → Department → Board are the same mechanism with
    different names and lengths. `steps` is an ordered list of
    `{key, name, permission}`; the permission is validated against the catalogue
    when the workflow is saved, so a typo fails at configuration time rather
    than at the end of term.

    An institution with no workflow row publishes in one step, by somebody
    holding the publish permission. That is a legitimate configuration and not
    a missing one: a small school where the head teacher enters and publishes
    the marks herself should not have to invent a committee.
    """

    __tablename__ = "approval_workflows"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_approval_workflows_tenant_code"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    # What this workflow governs. One value today; named rather than assumed so
    # admissions and awards can use the same machine later.
    applies_to: Mapped[str] = mapped_column(String(40), nullable=False, default="results")
    steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ResultSet(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A batch of results moving through the institution's workflow together.

    The unit of publication, because publication is a decision about a cohort
    and a period rather than about one child. A results day is one row here.
    """

    __tablename__ = "result_sets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_result_sets_tenant_code"),
        Index("ix_result_sets_tenant_stage", "tenant_id", "stage"),
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    academic_period_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_periods.id", ondelete="RESTRICT")
    )
    class_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="RESTRICT")
    )
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("programmes.id", ondelete="RESTRICT")
    )
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("approval_workflows.id", ondelete="RESTRICT")
    )
    stage: Mapped[ResultStage] = mapped_column(
        Enum(ResultStage, name="result_stage"), nullable=False, default=ResultStage.draft
    )
    # Which step of the workflow is outstanding. Null once approved.
    current_step: Mapped[str | None] = mapped_column(String(64))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    # Who may see it once published. A school that publishes to staff before
    # families needs this to be a decision rather than a deployment.
    audience: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    note: Mapped[str | None] = mapped_column(Text)


class ApprovalRecord(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One step taken on one result set. Append-only.

    Records refusals as well as approvals, because "the board sent it back on
    the 14th" is part of how a result came to be what it is, and a ledger that
    keeps only the yeses is a ledger that cannot explain a delay.
    """

    __tablename__ = "approval_records"
    __table_args__ = (
        Index("ix_approval_records_tenant_set", "tenant_id", "result_set_id"),
    )

    result_set_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("result_sets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    step_key: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)  # approved | returned
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    reason: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PublishedResult(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """What the institution said, frozen at the moment it said it.

    The columns below are a *snapshot*, not references. The band label, the
    points and the pass flag are copied from the grading scale as it stood at
    publication, because a school that moves its grade boundaries next year must
    not silently change what it awarded last year — and a transcript reprinted
    in 2031 has to say what the 2026 transcript said.

    That redundancy is the feature. Recomputing from live scores and a live
    scale would be smaller, tidier, and wrong.
    """

    __tablename__ = "published_results"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "result_set_id", "student_relationship_id", "assessment_id",
            name="uq_published_results_entry",
        ),
        Index("ix_published_results_tenant_student", "tenant_id",
              "student_relationship_id"),
    )

    result_set_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("result_sets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessments.id", ondelete="RESTRICT")
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="RESTRICT")
    )
    # The snapshot.
    score: Mapped[float | None] = mapped_column(Numeric(10, 3))
    max_score: Mapped[float | None] = mapped_column(Numeric(10, 3))
    band_label: Mapped[str | None] = mapped_column(String(40))
    points: Mapped[float | None] = mapped_column(Numeric(8, 3))
    is_pass: Mapped[bool | None] = mapped_column(Boolean)
    is_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Which scale produced the band, named rather than joined — the scale may be
    # edited or deleted, and this row must still explain itself.
    grading_scale_code: Mapped[str | None] = mapped_column(String(40))
    comment: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Set by an amendment, so the current value and the fact that it changed are
    # both readable without a join.
    amended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ResultAmendment(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A correction to something already published. Append-only.

    Everything an examinations officer is asked for a year later: what it was,
    what it became, who changed it, when, and why. Without the reason the row is
    an anomaly rather than a record.
    """

    __tablename__ = "result_amendments"
    __table_args__ = (
        Index("ix_result_amendments_tenant_result", "tenant_id", "published_result_id"),
    )

    published_result_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("published_results.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_score: Mapped[float | None] = mapped_column(Numeric(10, 3))
    new_score: Mapped[float | None] = mapped_column(Numeric(10, 3))
    previous_band_label: Mapped[str | None] = mapped_column(String(40))
    new_band_label: Mapped[str | None] = mapped_column(String(40))
    previous_comment: Mapped[str | None] = mapped_column(Text)
    new_comment: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


__all__ = [
    "ApprovalRecord",
    "ApprovalWorkflow",
    "Assessment",
    "AssessmentScore",
    "AssessmentStatus",
    "PublishedResult",
    "ResultAmendment",
    "ResultSet",
    "ResultStage",
]
