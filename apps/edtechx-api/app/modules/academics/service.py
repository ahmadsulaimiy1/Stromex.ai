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
    "current_year",
    "find_class_group",
    "find_cohort",
    "find_course",
    "find_level",
    "find_programme",
    "find_qualification",
    "resolve_placement",
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
