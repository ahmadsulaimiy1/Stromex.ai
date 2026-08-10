"""Academic structure — the shape of a school, held as data.

The trap this module exists to avoid is a generic-looking schema that quietly
assumes one country's school system. Three specific decisions keep it out:

**Stages are a tree, not an enum.** A school may have one tier, two, or three,
under any names: Primary/Secondary, Elementary/Middle/High,
Nursery/Primary/College, Foundation/Undergraduate/Postgraduate. `parent_id`
makes depth the school's choice rather than ours.

**Levels carry no number that means anything to us.** There is a `sequence` for
ordering and a name the school chose. There is deliberately no `grade_level`
integer, because the moment one exists, code starts doing arithmetic on it and
"Year 7" is silently assumed to be one more than "Year 6" in a way that is
false for a school running Foundation → Undergraduate.

**Terms are counted, not named by us.** Two semesters, three terms, four
quarters, or one continuous year are the same structure with a different number
of rows.

The acceptance test for all of this is `test_four_schools.py`, which configures
four genuinely different institutions and asserts that no product code changed.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeletable, TenantOwned, Timestamped, UUIDPrimaryKey


class ScaleKind(str, enum.Enum):
    """How a grading scale expresses attainment.

    Platform-fixed because the *arithmetic* differs per kind — a GPA is
    averaged differently from a percentage, and a descriptor is not averaged at
    all. The bands, labels, thresholds, and pass marks within each kind are
    entirely the school's.
    """

    percentage = "percentage"
    letter = "letter"
    gpa = "gpa"
    descriptor = "descriptor"
    points = "points"


class ProgressionOutcome(str, enum.Enum):
    promote = "promote"
    repeat = "repeat"
    review = "review"
    graduate = "graduate"


class AcademicStage(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A tier of the institution, at whatever depth the school uses."""

    __tablename__ = "academic_stages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_academic_stages_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_stages.id", ondelete="RESTRICT")
    )
    # Anything the school needs that the platform has no opinion about.
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    levels: Mapped[list[Level]] = relationship(back_populates="stage")

    @property
    def is_root(self) -> bool:
        return self.parent_id is None


class Level(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A year group, form, grade, or study level — the school's word for it.

    Note the absence of any integer that encodes *which* year this is in a
    national system. `sequence` orders levels within a school and means nothing
    outside it.
    """

    __tablename__ = "levels"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_levels_tenant_code"),
    )

    stage_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_stages.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(40))
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # The level a promoted student moves to. Explicit rather than "sequence + 1",
    # because the next level is not always the next number: it may be in
    # another stage, or there may be none because this level graduates.
    next_level_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("levels.id", ondelete="SET NULL")
    )
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    stage: Mapped[AcademicStage] = relationship(back_populates="levels")


class AcademicYear(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    __tablename__ = "academic_years"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_academic_years_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Term(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A division of the academic year: term, semester, quarter, or the year itself."""

    __tablename__ = "terms"
    __table_args__ = (
        UniqueConstraint("tenant_id", "academic_year_id", "sequence", name="uq_terms_year_seq"),
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Weight in the year's aggregate, for schools that weight terms unequally.
    weight: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False, default=1)


class Subject(UUIDPrimaryKey, Timestamped, SoftDeletable, TenantOwned, Base):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_subjects_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    # "Core" is a school's judgement, not a platform category. Progression
    # rules can require core subjects to be passed without the platform having
    # any opinion about which they are.
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Credit-bearing institutions set this; term-and-grade schools leave it null.
    credits: Mapped[float | None] = mapped_column(Numeric(6, 2))
    grading_scale_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("grading_scales.id", ondelete="SET NULL")
    )
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ClassGroup(UUIDPrimaryKey, Timestamped, SoftDeletable, TenantOwned, Base):
    """A teaching group: class, form, section, seminar group, cohort."""

    __tablename__ = "class_groups"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "academic_year_id", "code", name="uq_class_groups_year_code"
        ),
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("levels.id", ondelete="RESTRICT"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class GradingScale(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    __tablename__ = "grading_scales"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_grading_scales_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    kind: Mapped[ScaleKind] = mapped_column(
        Enum(ScaleKind, name="grading_scale_kind"), nullable=False
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    bands: Mapped[list[GradingBand]] = relationship(
        back_populates="scale", cascade="all, delete-orphan", lazy="selectin"
    )

    def band_for(self, value: float) -> GradingBand | None:
        for band in sorted(self.bands, key=lambda b: float(b.min_value), reverse=True):
            if float(band.min_value) <= value <= float(band.max_value):
                return band
        return None


class GradingBand(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One step of a scale: its label, its range, its points, and whether it passes."""

    __tablename__ = "grading_bands"

    scale_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("grading_scales.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(40), nullable=False)
    descriptor: Mapped[str | None] = mapped_column(Text)
    min_value: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    max_value: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    # What this band contributes when averaged — grade points for a GPA scale,
    # the mark itself for a percentage scale.
    points: Mapped[float | None] = mapped_column(Numeric(8, 3))
    is_pass: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    scale: Mapped[GradingScale] = relationship(back_populates="bands")


class ProgressionRule(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """When a student moves up, expressed as data.

    The condition tree lives in `conditions` and is evaluated by
    `academics.progression`. A school that requires a pass mark plus attendance,
    one that requires a GPA, one that requires a class position, and one that
    requires accumulated credits are four rows here — not four branches in the
    product.
    """

    __tablename__ = "progression_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_progression_rules_tenant_code"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    # Null means "the school's default rule"; a level id narrows it to that level.
    level_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("levels.id", ondelete="CASCADE")
    )
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    on_pass: Mapped[ProgressionOutcome] = mapped_column(
        Enum(ProgressionOutcome, name="progression_outcome"),
        nullable=False,
        default=ProgressionOutcome.promote,
    )
    on_fail: Mapped[ProgressionOutcome] = mapped_column(
        Enum(ProgressionOutcome, name="progression_outcome"),
        nullable=False,
        default=ProgressionOutcome.repeat,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
