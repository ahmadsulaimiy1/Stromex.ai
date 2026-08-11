"""Reading the academic structure by the institution's own codes.

Exists so other modules can resolve "the row this school calls `jss1`" without
importing academics' tables — the module-boundary rule, with no exception carved
out for the one caller that finds it inconvenient.

Every lookup is by code, because a code is what appears in a spreadsheet, in a
URL, and in the institution's own paperwork. Every lookup returns `None` rather
than raising, because "no such level" is an ordinary answer that the caller
turns into a message on a row, not an exception that stops a file of two
thousand.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.academics.models import (
    AcademicPeriod,
    AcademicYear,
    ClassGroup,
    Course,
    Level,
)
from app.modules.academics.structure import Cohort, Programme, Qualification

__all__ = [
    "ResolvedPlacement",
    "academic_unit_subtree",
    "class_group",
    "class_group_ids_taught_by",
    "class_group_ids_under",
    "cohort",
    "course",
    "credit_unit_label",
    "current_period",
    "current_year",
    "default_grading_scale",
    "find_class_group",
    "find_cohort",
    "find_course",
    "find_level",
    "find_programme",
    "find_qualification",
    "grading_scale",
    "grading_scale_by_code",
    "level",
    "period",
    "periods_in",
    "populated_layers",
    "programme",
    "programme_ids_under",
    "qualification",
    "resolve_placement",
    "year",
]


def _by_code(db: Session, model: type, code: str):
    if not code:
        return None
    return db.execute(
        select(model).where(model.code == code.strip())
    ).scalars().first()


def find_level(db: Session, code: str) -> Level | None:
    return _by_code(db, Level, code)


def find_programme(db: Session, code: str) -> Programme | None:
    return _by_code(db, Programme, code)


def find_cohort(db: Session, code: str) -> Cohort | None:
    return _by_code(db, Cohort, code)


def find_course(db: Session, code: str) -> Course | None:
    return _by_code(db, Course, code)


def find_qualification(db: Session, code: str) -> Qualification | None:
    return _by_code(db, Qualification, code)


def find_class_group(
    db: Session, code: str, *, academic_year_id: uuid.UUID | None = None
) -> ClassGroup | None:
    """A class group's code is unique per year, not per institution.

    "3A" exists in every year a school has run, and they are different groups
    with different children in them. Without the year, the newest is returned —
    which is right for an interactive lookup and would be wrong for an import,
    so the import passes the year.
    """
    if not code:
        return None
    statement = select(ClassGroup).where(ClassGroup.code == code.strip())
    if academic_year_id is not None:
        statement = statement.where(ClassGroup.academic_year_id == academic_year_id)
    return db.execute(
        statement.order_by(ClassGroup.created_at.desc())
    ).scalars().first()


def current_year(db: Session) -> AcademicYear | None:
    """The year the institution has marked current, if it has marked one."""
    return db.execute(
        select(AcademicYear).where(AcademicYear.is_current.is_(True))
    ).scalars().first()


def current_period(db: Session) -> AcademicPeriod | None:
    return db.execute(
        select(AcademicPeriod).where(AcademicPeriod.is_current.is_(True))
    ).scalars().first()


@dataclass(frozen=True, slots=True)
class ResolvedPlacement:
    """Codes turned into ids, with a message for every code that named nothing.

    Both halves matter. The ids let a placement be created; the problems let a
    row be reported precisely — "the level code `jss1` is not one of yours" is
    actionable, and "import failed" is not.
    """

    academic_year_id: uuid.UUID | None = None
    programme_id: uuid.UUID | None = None
    level_id: uuid.UUID | None = None
    class_group_id: uuid.UUID | None = None
    cohort_id: uuid.UUID | None = None
    problems: tuple[str, ...] = ()

    @property
    def names_anything(self) -> bool:
        return any(
            (
                self.academic_year_id,
                self.programme_id,
                self.level_id,
                self.class_group_id,
                self.cohort_id,
            )
        )


def resolve_placement(
    db: Session,
    *,
    programme_code: str = "",
    level_code: str = "",
    class_group_code: str = "",
    cohort_code: str = "",
    academic_year_id: uuid.UUID | None = None,
) -> ResolvedPlacement:
    """Turn whichever codes an institution uses into ids, and say what failed.

    Every code is optional, and a placement naming none of them is valid — a
    person can be admitted before anyone has decided where they will sit. What
    is *not* tolerated is a code that names nothing: silently dropping it would
    enrol a child into no class at all while reporting success.

    A class group implies its level and its year, so a file that names only the
    class does not also have to name the other two. The implication runs one
    way: a level does not imply a class.
    """
    problems: list[str] = []
    year_id = academic_year_id or (getattr(current_year(db), "id", None))

    programme = find_programme(db, programme_code)
    if programme_code and programme is None:
        problems.append(f"No programme has the code {programme_code!r}.")

    level = find_level(db, level_code)
    if level_code and level is None:
        problems.append(f"No level has the code {level_code!r}.")

    group = find_class_group(db, class_group_code, academic_year_id=year_id)
    if class_group_code and group is None:
        problems.append(
            f"No class has the code {class_group_code!r} in this academic year."
        )

    cohort = find_cohort(db, cohort_code)
    if cohort_code and cohort is None:
        problems.append(f"No cohort has the code {cohort_code!r}.")

    if group is not None:
        level = level or db.get(Level, group.level_id)
        year_id = group.academic_year_id
        if cohort is None and group.cohort_id is not None:
            cohort = db.get(Cohort, group.cohort_id)
    if programme is None and level is not None and level.programme_id is not None:
        programme = db.get(Programme, level.programme_id)

    if level is not None and group is not None and group.level_id != level.id:
        problems.append(
            f"The class {class_group_code!r} does not belong to the level "
            f"{level_code!r}."
        )

    return ResolvedPlacement(
        academic_year_id=year_id,
        programme_id=programme.id if programme else None,
        level_id=level.id if level else None,
        class_group_id=group.id if group else None,
        cohort_id=cohort.id if cohort else None,
        problems=tuple(problems),
    )


# --- selectables for the authorization layer ------------------------------
#
# Returned as SQLAlchemy `Select` objects rather than as lists of ids, and that
# is the whole point. An authorization boundary composed into one statement is
# enforced by the database; the same boundary fetched into Python and expanded
# is one refactor away from being applied after the rows have arrived.
#
# They live here rather than in the modules that use them because a module owns
# its tables (EDTECHX_ARCHITECTURE.md §3). `people` needs to know which
# programmes sit under a faculty; it does not need to import `programmes`.


def academic_unit_subtree(unit_ids):
    """A recursive walk down the unit tree, as a CTE.

    A head of faculty who could not see the departments inside it holds a scope
    that means nothing, so the walk is downwards and recursive — to whatever
    depth this institution happens to nest (ADR-024).

    The name carries a digest of the ids because two of these can appear in one
    statement: a head of two departments holds two scopes, both of which compile
    to a subtree walk, and SQLAlchemy refuses two unrelated CTEs sharing a name.
    Deriving the name from the ids also makes the *same* subtree deduplicate
    rather than being emitted twice.
    """
    import hashlib

    from app.modules.academics.structure import AcademicUnit

    digest = hashlib.sha1(
        ",".join(sorted(str(i) for i in unit_ids)).encode(), usedforsecurity=False
    ).hexdigest()[:12]
    roots = select(AcademicUnit.id.label("id")).where(AcademicUnit.id.in_(unit_ids))
    tree = roots.cte(f"unit_subtree_{digest}", recursive=True)
    return tree.union_all(select(AcademicUnit.id).where(AcademicUnit.parent_id == tree.c.id))


def programme_ids_under(unit_ids):
    """Programmes belonging to any of these academic units, or to units below them."""
    subtree = academic_unit_subtree(unit_ids)
    return select(Programme.id).where(
        Programme.academic_unit_id.in_(select(subtree.c.id))
    )


def class_group_ids_taught_by(membership_id):
    """The class groups this membership currently teaches.

    Current, not ever. A teacher's reach follows their present allocation; a
    scope that quietly accumulated every group they had ever taught would grow
    for years without anybody deciding it should.
    """
    from app.modules.academics.models import TeachingAllocation

    return select(TeachingAllocation.class_group_id).where(
        TeachingAllocation.membership_id == membership_id,
        TeachingAllocation.ends_on.is_(None),
    )


def class_group_ids_under(unit_ids):
    """Class groups whose level belongs to a programme under one of these units."""
    return select(ClassGroup.id).where(
        ClassGroup.level_id.in_(
            select(Level.id).where(Level.programme_id.in_(programme_ids_under(unit_ids)))
        )
    )


# --- which layers this institution actually uses --------------------------


LAYER_TABLES: dict[str, str] = {
    "academic_units": "academic_units",
    "stages": "academic_stages",
    "programmes": "programmes",
    "qualifications": "qualifications",
    "levels": "levels",
    "cohorts": "cohorts",
    "classes": "class_groups",
    "courses": "courses",
    "periods": "academic_periods",
    "years": "academic_years",
    "credits": "credit_systems",
    "grading": "grading_scales",
    "progression": "progression_rules",
    "supervision": "supervision_roles",
    "milestones": "milestone_definitions",
}


def populated_layers(db: Session) -> frozenset[str]:
    """The academic layers this institution has actually put rows in.

    The honest signal for what an institution's world contains. A nursery has no
    programmes because it has no programme rows — not because somebody ticked a
    box marked "nursery", which would be ADR-024's forbidden enum arriving
    through the back door.

    One query rather than fifteen, because this runs on the way to rendering a
    navigation and a person waiting for a page should not pay for fifteen round
    trips to learn what their own school is.
    """
    from sqlalchemy import literal, union_all
    from sqlalchemy import select as _select

    parts = [
        _select(literal(layer).label("layer")).where(
            _select(model_table.c.id).limit(1).exists()
        )
        for layer, table_name in LAYER_TABLES.items()
        if (model_table := Base.metadata.tables.get(table_name)) is not None
    ]
    if not parts:
        return frozenset()
    rows = db.execute(union_all(*parts)).scalars().all()
    return frozenset(rows)


def period(db: Session, period_id: uuid.UUID | None) -> AcademicPeriod | None:
    """One academic period by id, for callers that hold one from elsewhere."""
    return db.get(AcademicPeriod, period_id) if period_id else None


def grading_scale(db: Session, scale_id: uuid.UUID | None):
    """One grading scale, with its bands loaded.

    Returned as the object rather than as a computed band, because the caller
    asks it `band_for(value)` — the institution's own thresholds applied by the
    institution's own row, with this module holding no opinion about what passes.
    """
    from app.modules.academics.models import GradingScale

    return db.get(GradingScale, scale_id) if scale_id else None


# --- reading the structure a document has to describe ----------------------
#
# By id rather than by code, because a document is composed from rows another
# module already holds ids for — an enrolment's level, a published result's
# course — and looking those up by code would mean fetching them twice.


def year(db: Session, year_id: uuid.UUID | None) -> AcademicYear | None:
    return db.get(AcademicYear, year_id) if year_id else None


def level(db: Session, level_id: uuid.UUID | None) -> Level | None:
    return db.get(Level, level_id) if level_id else None


def class_group(db: Session, class_group_id: uuid.UUID | None) -> ClassGroup | None:
    return db.get(ClassGroup, class_group_id) if class_group_id else None


def course(db: Session, course_id: uuid.UUID | None) -> Course | None:
    return db.get(Course, course_id) if course_id else None


def programme(db: Session, programme_id: uuid.UUID | None):
    return db.get(Programme, programme_id) if programme_id else None


def cohort(db: Session, cohort_id: uuid.UUID | None):
    return db.get(Cohort, cohort_id) if cohort_id else None


def qualification(db: Session, qualification_id: uuid.UUID | None):
    return db.get(Qualification, qualification_id) if qualification_id else None


def periods_in(db: Session, academic_year_id: uuid.UUID | None) -> list[AcademicPeriod]:
    """Every period of one year, in the institution's own sequence."""
    if academic_year_id is None:
        return []
    return list(
        db.execute(
            select(AcademicPeriod)
            .where(AcademicPeriod.academic_year_id == academic_year_id)
            .order_by(AcademicPeriod.sequence)
        ).scalars().all()
    )


def credit_unit_label(db: Session, credit_system_id: uuid.UUID | None) -> tuple[str, str]:
    """What this institution calls one unit of academic work, and several.

    Returns empty strings when the institution counts nothing, which is the
    signal a document uses to leave the credit column out entirely rather than
    printing a blank one under a heading nobody here recognises.
    """
    from app.modules.academics.structure import CreditSystem

    system = db.get(CreditSystem, credit_system_id) if credit_system_id else None
    if system is None:
        system = db.execute(
            select(CreditSystem).where(CreditSystem.is_default.is_(True))
        ).scalars().first()
    if system is None:
        return ("", "")
    return (system.unit_label, system.unit_label_plural)


def default_grading_scale(db: Session):
    from app.modules.academics.models import GradingScale

    return db.execute(
        select(GradingScale).where(GradingScale.is_default.is_(True))
    ).scalars().first()


def grading_scale_by_code(db: Session, code: str):
    """The scale a published result named, for printing its key on a document.

    Returns `None` when the scale has since been deleted, and the caller prints
    the document without a grading key rather than refusing to print it — the
    result itself already carries the band it was awarded (ADR-033).
    """
    from app.modules.academics.models import GradingScale

    return _by_code(db, GradingScale, code) if code else None
