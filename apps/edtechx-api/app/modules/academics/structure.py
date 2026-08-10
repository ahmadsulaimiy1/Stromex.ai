"""The universal academic structure.

Five things that are routinely conflated, kept apart because collapsing any two
of them is what makes a system serve one kind of institution and no other:

  **Academic unit** — where in the organisation something sits. Campus,
  faculty, school, department, division. A self-referencing tree, because the
  depth is the institution's, not ours.

  **Programme** — what a student is admitted to. Bachelor of Computer Science,
  Diploma in Nursing, the primary curriculum. Usually leads to a qualification.

  **Level** — where a student has reached within a programme or stage. Year 3,
  Level 200, Intermediate, Foundation Year.

  **Course** — what is studied. Subject, module, unit, paper.

  **Qualification** — what completion awards, defined in the institution's own
  framework rather than a national one baked into an enum.

The word `kind` appears throughout as a *free-text label*, never an enum. An
institution that calls its top tier a "College" and another that calls it a
"Faculty" are the same row with a different string; a third that has invented a
tier we have never heard of is also the same row.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
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


class AcademicUnit(UUIDPrimaryKey, Timestamped, SoftDeletable, TenantOwned, Base):
    """Where something sits in the organisation.

    One table for campus, faculty, school, department and division, because
    they are the same thing at different depths and no institution agrees on
    which words go with which depth. `kind_label` is what this institution
    calls this tier; the platform never reads it to make a decision.
    """

    __tablename__ = "academic_units"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_academic_units_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    # "Campus", "Faculty", "School", "Department", "Centre", "Institute"…
    kind_label: Mapped[str] = mapped_column(String(60), nullable=False, default="Department")
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_units.id", ondelete="RESTRICT")
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    head_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @property
    def is_root(self) -> bool:
        return self.parent_id is None


class CreditSystem(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """How this institution counts academic work, if it counts it at all.

    Deliberately a row rather than a constant: credits, credit hours, units,
    ECTS and contact hours are not interchangeable, and an institution that
    uses none of them must not be forced to pretend.
    """

    __tablename__ = "credit_systems"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_credit_systems_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    # "credit", "credit hour", "unit", "ECTS credit", "module"
    unit_label: Mapped[str] = mapped_column(String(60), nullable=False, default="credit")
    unit_label_plural: Mapped[str] = mapped_column(String(60), nullable=False, default="credits")
    # Contact hours one unit represents, where the institution defines that.
    hours_per_unit: Mapped[float | None] = mapped_column(Numeric(8, 2))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Qualification(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """What completing a programme awards, in the institution's own framework.

    There is no `QualificationType` enum, and there will not be one. A national
    framework is configuration: an institution creates the qualifications it
    awards, orders them with `framework_level`, and groups them with a
    `category_label` it chose. `framework_level` orders qualifications *within
    this institution* and carries no meaning outside it.
    """

    __tablename__ = "qualifications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_qualifications_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(60))
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    # "Certificate", "Diploma", "Undergraduate", "Postgraduate", "Doctoral" —
    # the institution's own grouping, read only for display and filtering.
    category_label: Mapped[str | None] = mapped_column(String(80))
    framework_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    awarding_body: Mapped[str | None] = mapped_column(String(200))
    # Nullable throughout: a qualification may have no fixed duration, no credit
    # requirement, or neither. "A bachelor's is three years" is a statement
    # about one country, not about degrees.
    typical_duration_periods: Mapped[int | None] = mapped_column(Integer)
    required_credits: Mapped[float | None] = mapped_column(Numeric(10, 2))
    credit_system_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("credit_systems.id", ondelete="SET NULL")
    )
    # Conditions evaluated by the same engine as progression.
    completion_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Programme(UUIDPrimaryKey, Timestamped, SoftDeletable, TenantOwned, Base):
    """A named course of study a student is admitted to.

    Distinct from a level, which is where they have reached within it, and from
    a qualification, which is what they leave with. A primary school has one
    implicit programme or none; a university has hundreds.
    """

    __tablename__ = "programmes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_programmes_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    academic_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_units.id", ondelete="RESTRICT")
    )
    qualification_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("qualifications.id", ondelete="RESTRICT")
    )
    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_stages.id", ondelete="SET NULL")
    )
    # "Programme", "Course of study", "Curriculum", "Track", "Pathway"
    kind_label: Mapped[str] = mapped_column(String(60), nullable=False, default="Programme")
    # Nullable: variable-duration and open-ended programmes are ordinary, and a
    # research degree may have no fixed length at all.
    duration_periods: Mapped[int | None] = mapped_column(Integer)
    required_credits: Mapped[float | None] = mapped_column(Numeric(10, 2))
    credit_system_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("credit_systems.id", ondelete="SET NULL")
    )
    # Research programmes carry supervision; taught ones do not. A flag rather
    # than a separate table, because everything else about them is identical.
    is_research: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Cohort(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A group progressing together — an intake year, an evening group, a class of 2030."""

    __tablename__ = "cohorts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_cohorts_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("programmes.id", ondelete="CASCADE")
    )
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="SET NULL")
    )
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class MilestoneDefinition(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A checkpoint a programme requires: proposal, upgrade, submission, viva.

    Architecture for research education without building the research-management
    product now. A taught programme simply has none of these rows; a doctoral
    programme has several, in the institution's own sequence and vocabulary.
    """

    __tablename__ = "milestone_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "programme_id", "code", name="uq_milestone_prog_code"),
    )

    programme_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Months from the start of the programme, where the institution sets one.
    expected_offset_months: Mapped[int | None] = mapped_column(Integer)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Who signs it off, as a role key rather than a named person.
    approver_role_key: Mapped[str | None] = mapped_column(String(64))
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class SupervisionRole(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """The institution's supervision vocabulary and its rules.

    "Principal supervisor", "co-supervisor", "advisor", "mentor", "external
    examiner" — named by the institution, with its own limits on how many a
    student may have.
    """

    __tablename__ = "supervision_roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_supervision_roles_tenant_code"),
        CheckConstraint("max_per_student IS NULL OR max_per_student > 0",
                        name="ck_supervision_roles_positive_max"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_per_student: Mapped[int | None] = mapped_column(Integer)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# `Level` gains a programme, and `Course` replaces `Subject`. Both live in
# `models.py` alongside the rest of the academic core; this module holds the
# structures that were absent entirely.

__all__ = [
    "AcademicUnit",
    "Cohort",
    "CreditSystem",
    "MilestoneDefinition",
    "Programme",
    "Qualification",
    "SupervisionRole",
]
