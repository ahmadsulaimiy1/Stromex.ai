"""People — and the careful distinction between three things that are usually one.

  **Identity** (`identity.User`) is a credential. It is global, it belongs to a
  human being rather than to an institution, and it exists only for people who
  sign in. A four-year-old has none. A guardian who never opens the product has
  none. A person who teaches at two institutions has exactly one.

  **Person** is an institution's record *of* a human. It is tenant-owned, it may
  or may not point at an identity, and it carries the things an institution
  knows: what to call them, when they were born if that was recorded, how to
  reach them.

  **Relationship** is what that person *is* to the institution — a learner, a
  member of staff, somebody's guardian. Each is its own row, and one person may
  hold several at once without being duplicated. The teacher whose own child is
  a pupil is one Person with two relationships, not two people who happen to
  share a surname.

Collapsing any two of these is the mistake that makes a system unable to
represent an ordinary school. A `students` table with an `email` and a
`password_hash` cannot express a pupil with no email; a `users` table with a
`class_id` cannot express the teacher who is also a parent; and a `person` with
a `role` column cannot express either.

Nothing here assumes a sector. `kind_label` is the institution's own word —
"Pupil", "Learner", "Apprentice", "Researcher", "Trainee" — and the platform
never reads it to make a decision. The relationship *lifecycle* is fixed
(prospective, active, suspended, ended) because those four states are what the
system's own logic depends on; everything descriptive is a string the
institution chose.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeletable, TenantOwned, Timestamped, UUIDPrimaryKey


class RelationshipStatus(str, enum.Enum):
    """The lifecycle every institutional relationship shares.

    Platform-fixed, and short on purpose. These four states are the ones the
    product's own logic branches on — whether to show somebody in a list,
    whether they may sign in, whether their record is closed. Everything that
    varies by institution (why they left, what they are called, what they were
    awarded) is data elsewhere, not another value here.
    """

    prospective = "prospective"
    active = "active"
    suspended = "suspended"
    ended = "ended"


class Person(UUIDPrimaryKey, Timestamped, SoftDeletable, TenantOwned, Base):
    """A human being, as this institution records them.

    Deliberately separate from `users`. `user_id` is nullable and usually null:
    most people an institution knows never sign in. When it is set, it is the
    same global identity the person uses at every institution — which is why it
    is unique per tenant rather than globally, and why nothing about the person
    is stored on the user.

    **Names.** One required field, `full_name`, written the way the person
    writes it. The structured parts are optional and independent, because name
    order, the number of parts, and which part is the family name all vary, and
    a schema that demands "first" and "last" quietly tells a large part of the
    world that it was not built for them. `sort_name` exists so an institution
    can order its own lists by whichever part it sorts by.
    """

    __tablename__ = "people"
    __table_args__ = (
        # One person per identity per institution. Partial, because most people
        # have no identity at all and a plain unique constraint would allow
        # exactly one of them.
        Index(
            "uq_people_tenant_user",
            "tenant_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index("ix_people_tenant_sort_name", "tenant_id", "sort_name"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    given_names: Mapped[str | None] = mapped_column(String(120))
    family_name: Mapped[str | None] = mapped_column(String(120))
    preferred_name: Mapped[str | None] = mapped_column(String(120))
    sort_name: Mapped[str | None] = mapped_column(String(200))
    # Free text, and nullable. Neither an enum nor a required field: an
    # institution that does not record this must not be made to, and one that
    # does must not be limited to the options we imagined.
    gender_label: Mapped[str | None] = mapped_column(String(60))
    date_of_birth: Mapped[date | None] = mapped_column(Date)

    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(40))
    locale: Mapped[str | None] = mapped_column(String(16))
    address: Mapped[str | None] = mapped_column(Text)

    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @property
    def display_name(self) -> str:
        return self.preferred_name or self.full_name

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Person {self.full_name}>"


class StudentRelationship(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """This person learns here.

    Note what is *not* on this table: no class, no level, no year, no
    programme. Where somebody is placed changes over time and belongs to
    `enrolments`, where each placement is a record with a start and an end. A
    `class_id` here would be the single mutable field that erases a history
    every time a child moves group.
    """

    __tablename__ = "student_relationships"
    __table_args__ = (
        Index(
            "uq_student_relationships_tenant_reference",
            "tenant_id",
            "reference",
            unique=True,
            postgresql_where=text("reference IS NOT NULL"),
        ),
        Index("ix_student_relationships_tenant_person", "tenant_id", "person_id"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("people.id", ondelete="RESTRICT"), nullable=False
    )
    # The institution's own identifier: admission number, matriculation number,
    # registration number, candidate number. One column, because they are the
    # same idea, and nullable because some institutions issue none.
    reference: Mapped[str | None] = mapped_column(String(64))
    # "Student", "Pupil", "Learner", "Apprentice", "Researcher", "Candidate".
    kind_label: Mapped[str] = mapped_column(String(60), nullable=False, default="Student")
    status: Mapped[RelationshipStatus] = mapped_column(
        Enum(RelationshipStatus, name="relationship_status"),
        nullable=False,
        default=RelationshipStatus.prospective,
    )
    started_on: Mapped[date | None] = mapped_column(Date)
    ended_on: Mapped[date | None] = mapped_column(Date)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class StaffRelationship(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """This person works here.

    Separate from the student relationship rather than a `kind` on one table,
    because the two carry genuinely different facts: a staff record has an
    academic unit and an employment reference, a student record has enrolments
    and results. A doctoral researcher who also demonstrates in the laboratory
    holds one of each, and neither row is a compromise.
    """

    __tablename__ = "staff_relationships"
    __table_args__ = (
        Index(
            "uq_staff_relationships_tenant_reference",
            "tenant_id",
            "reference",
            unique=True,
            postgresql_where=text("reference IS NOT NULL"),
        ),
        Index("ix_staff_relationships_tenant_person", "tenant_id", "person_id"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("people.id", ondelete="RESTRICT"), nullable=False
    )
    reference: Mapped[str | None] = mapped_column(String(64))
    # "Teacher", "Lecturer", "Tutor", "Instructor", "Assessor", "Administrator",
    # "Technician", "Supervisor". The institution's word, never read by the
    # platform — what somebody may *do* comes from their role grants.
    kind_label: Mapped[str] = mapped_column(String(60), nullable=False, default="Staff")
    academic_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_units.id", ondelete="SET NULL")
    )
    # Whether this person can be allocated to teach. A fact the institution
    # records, not a category the platform imposes: plenty of staff never
    # teach, and in some institutions almost all of them do.
    is_teaching: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[RelationshipStatus] = mapped_column(
        Enum(RelationshipStatus, name="relationship_status"),
        nullable=False,
        default=RelationshipStatus.active,
    )
    started_on: Mapped[date | None] = mapped_column(Date)
    ended_on: Mapped[date | None] = mapped_column(Date)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class GuardianRelationship(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """This person is responsible for that one.

    Person to person, not user to student. The guardian is a `Person` like any
    other, which is what allows a mother who teaches at the school to be one
    record rather than two, and allows a grandparent with no email address to
    exist at all.

    `relationship_label` is free text on purpose. "Mother", "Father",
    "Grandmother", "Uncle", "Aunt", "Sponsor", "Legal guardian", "Foster
    carer", "Elder brother" — family structures are not a closed list, and an
    enum here would be a small, permanent statement about whose families count.
    """

    __tablename__ = "guardian_relationships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "guardian_person_id",
            "student_person_id",
            name="uq_guardian_relationships_pair",
        ),
        CheckConstraint(
            "guardian_person_id <> student_person_id",
            name="guardian_is_not_the_student",
        ),
        Index(
            "ix_guardian_relationships_tenant_student",
            "tenant_id",
            "student_person_id",
        ),
    )

    guardian_person_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("people.id", ondelete="RESTRICT"), nullable=False
    )
    student_person_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("people.id", ondelete="RESTRICT"), nullable=False
    )
    relationship_label: Mapped[str] = mapped_column(String(60), nullable=False)
    # Who is contacted first. An ordering, not a hierarchy of importance.
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_emergency_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Three separate permissions, because institutions genuinely separate them:
    # the parent who receives reports is not always the one who may collect the
    # child, and neither is always the one who pays.
    receives_reports: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    may_collect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_financially_responsible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    status: Mapped[RelationshipStatus] = mapped_column(
        Enum(RelationshipStatus, name="relationship_status"),
        nullable=False,
        default=RelationshipStatus.active,
    )
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


__all__ = [
    "GuardianRelationship",
    "Person",
    "RelationshipStatus",
    "StaffRelationship",
    "StudentRelationship",
]
