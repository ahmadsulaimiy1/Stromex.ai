"""Attendance: the thing a teacher opens the product to do.

Three tables, and the shape of each is decided by one question — *what will a
school be asked to produce three years from now?* An attendance record is
evidence. It is quoted in safeguarding referrals, in exclusion appeals, in
funding audits and in court. So the design is closer to the enrolment ledger
than to a checkbox grid.

**The codes are the school's.** Present, Absent, Late, Authorised, Unauthorised,
Sick, Study leave, Educational visit, Religious observance — every institution
has its own list and its own letters, and none of them is ours to fix. What *is*
platform-fixed is the `category`, because the arithmetic depends on it: a
percentage attendance figure has to know which codes count as present, and no
amount of configuration makes that the school's arbitrary choice.

**A session is a moment, not a lesson.** A nursery takes a register for a room
each morning; a secondary school takes one per lesson; a university records
attendance at a seminar. All three are "these people, at this moment, marked by
this person" — a class group *or* a course, and at least one of them.

**A correction is an addition.** A mark can be changed — a child who arrived at
half past nine was marked absent at nine, and that is the system working — but
the change is recorded with a reason, and the ledger is append-only at the
database. "Who changed this, when, and why" is the first question anybody asks
about an attendance record that matters.
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
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class MarkCategory(str, enum.Enum):
    """What a code *means* for arithmetic. Platform-fixed, and only this is.

    A school names its codes and chooses their letters, colours and rules. It
    does not get to decide whether "present" counts towards a percentage
    present, because that is not a policy question — it is what the word means.
    Without this, every attendance figure in the product would be uncomputable.
    """

    present = "present"
    absent = "absent"
    late = "late"
    excused = "excused"
    other = "other"


class SessionStatus(str, enum.Enum):
    """A register's life.

    `open` is a register in progress — a teacher part way down the room. It is a
    real state and not a draft: the marks already in it are true, and a fire
    alarm at 09:04 must not lose them.
    """

    open = "open"
    submitted = "submitted"
    amended = "amended"


class AttendanceCode(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One mark a school can give. Its letter, its meaning, its rules."""

    __tablename__ = "attendance_codes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_attendance_codes_tenant_code"),
    )

    code: Mapped[str] = mapped_column(String(8), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[MarkCategory] = mapped_column(
        Enum(MarkCategory, name="attendance_mark_category"), nullable=False
    )
    # Usually implied by the category, and deliberately separate from it: a
    # school that counts an educational visit as present, and one that does not,
    # both use the `other` category and disagree about this column.
    counts_as_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # A code that cannot be given without an explanation. The absence workflow
    # is this column plus a session that will not submit until they are answered.
    requires_reason: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # The one a register starts on, so marking a full room is one action.
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    colour: Mapped[str | None] = mapped_column(String(9))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AttendanceSession(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One register: these people, at this moment, taken by this person."""

    __tablename__ = "attendance_sessions"
    __table_args__ = (
        # A register of nobody in particular cannot be produced later. One of
        # the two must say who was in the room.
        CheckConstraint(
            "class_group_id IS NOT NULL OR course_id IS NOT NULL",
            name="names_a_group",
        ),
        UniqueConstraint(
            "tenant_id", "class_group_id", "course_id", "occurred_on", "slot",
            name="uq_attendance_sessions_moment",
        ),
        Index("ix_attendance_sessions_tenant_date", "tenant_id", "occurred_on"),
    )

    class_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="RESTRICT")
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="RESTRICT")
    )
    academic_period_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_periods.id", ondelete="RESTRICT")
    )
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    # "Morning", "Afternoon", "Period 3", "Session 1" — the school's own word for
    # which register this is, and empty for a school that takes one a day.
    slot: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="attendance_session_status"),
        nullable=False,
        default=SessionStatus.open,
    )
    taken_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)

    @property
    def is_open(self) -> bool:
        return self.status is SessionStatus.open


class AttendanceMark(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One person's mark in one register. Current state; history is elsewhere."""

    __tablename__ = "attendance_marks"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "session_id", "student_relationship_id",
            name="uq_attendance_marks_session_student",
        ),
        Index("ix_attendance_marks_tenant_student", "tenant_id",
              "student_relationship_id"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("attendance_codes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    minutes_late: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(Text)
    recorded_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AttendanceAmendment(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """Every change to a mark, with its reason. Append-only at the database.

    A mark is corrected all the time and legitimately — the child who arrived at
    half past nine was absent at nine, and the register was right both times.
    What must survive is *that it changed*: an attendance record quoted in a
    safeguarding referral or an exclusion appeal is worth exactly as much as the
    answer to "who changed this, and why".
    """

    __tablename__ = "attendance_amendments"
    __table_args__ = (
        Index("ix_attendance_amendments_tenant_mark", "tenant_id", "mark_id"),
    )

    mark_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("attendance_marks.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_code_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    new_code_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    previous_reason: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


__all__ = [
    "AttendanceAmendment",
    "AttendanceCode",
    "AttendanceMark",
    "AttendanceSession",
    "MarkCategory",
    "SessionStatus",
]
