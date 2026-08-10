"""Resolving the school's vocabulary.

The default map below is EdirasX's *starting point*, not the platform's
assumption. Every key is overridable, and the resolver falls back key by key,
so a school that renames two words does not have to restate the other thirty.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customization.models import ConfigStatus, TerminologySet

# Canonical keys, and what EdirasX calls them when a school has said nothing.
DEFAULT_TERMS: dict[str, dict[str, str]] = {
    "student": {"singular": "student", "plural": "students"},
    "teacher": {"singular": "teacher", "plural": "teachers"},
    "guardian": {"singular": "parent", "plural": "parents"},
    "staff": {"singular": "staff member", "plural": "staff"},
    # The human record, as distinct from any relationship to the institution.
    # An institution that speaks of "members" or "registrants" renames it here.
    "person": {"singular": "person", "plural": "people"},
    "admission": {"singular": "admission", "plural": "admissions"},
    "award": {"singular": "award", "plural": "awards"},
    "class_group": {"singular": "class", "plural": "classes"},
    "level": {"singular": "year group", "plural": "year groups"},
    "stage": {"singular": "stage", "plural": "stages"},
    # Canonical key is `course` — the neutral term across sectors. Its default
    # is "subject", which is what a school expects to see; a university
    # overrides it to "module" and a research institute to "unit".
    "course": {"singular": "subject", "plural": "subjects"},
    "programme": {"singular": "programme", "plural": "programmes"},
    "qualification": {"singular": "qualification", "plural": "qualifications"},
    "academic_unit": {"singular": "department", "plural": "departments"},
    "cohort": {"singular": "cohort", "plural": "cohorts"},
    "academic_period": {"singular": "term", "plural": "terms"},
    "credit": {"singular": "credit", "plural": "credits"},
    "supervisor": {"singular": "supervisor", "plural": "supervisors"},
    "milestone": {"singular": "milestone", "plural": "milestones"},
    "academic_year": {"singular": "academic year", "plural": "academic years"},
    "assessment": {"singular": "assessment", "plural": "assessments"},
    "grade": {"singular": "grade", "plural": "grades"},
    "attendance": {"singular": "attendance", "plural": "attendance"},
    "report_card": {"singular": "report card", "plural": "report cards"},
    "enrolment": {"singular": "enrolment", "plural": "enrolments"},
}


@dataclass(frozen=True, slots=True)
class Vocabulary:
    """A school's resolved words, ready to render."""

    terms: dict[str, dict[str, str]]
    locale: str = "en"

    def word(self, key: str, *, plural: bool = False) -> str:
        entry = self.terms.get(key) or DEFAULT_TERMS.get(key)
        if entry is None:
            raise KeyError(
                f"{key!r} is not a known terminology key. Add it to DEFAULT_TERMS "
                "so every school gets a sensible default before any school overrides it."
            )
        return entry["plural" if plural else "singular"]

    def title(self, key: str, *, plural: bool = False) -> str:
        word = self.word(key, plural=plural)
        return word[:1].upper() + word[1:]


def resolve(db: Session, *, locale: str = "en") -> Vocabulary:
    """Merge the school's published overrides over the defaults, key by key."""
    published = db.execute(
        select(TerminologySet)
        .where(
            TerminologySet.locale == locale,
            TerminologySet.status == ConfigStatus.published,
        )
        .order_by(TerminologySet.version.desc())
    ).scalars().first()

    merged = {key: dict(value) for key, value in DEFAULT_TERMS.items()}
    if published:
        for key, value in (published.terms or {}).items():
            merged.setdefault(key, {}).update(value)
    return Vocabulary(terms=merged, locale=locale)


def publish(
    db: Session,
    *,
    terms: dict[str, dict[str, str]],
    locale: str = "en",
    membership_id: uuid.UUID | None = None,
) -> TerminologySet:
    """Publish a new version, superseding rather than mutating the previous one.

    History is kept so a rollback restores a prior version by reference. A
    school that renames its vocabulary mid-year and regrets it must be able to
    undo that without retyping it.
    """
    from datetime import UTC, datetime

    current = db.execute(
        select(TerminologySet)
        .where(TerminologySet.locale == locale)
        .order_by(TerminologySet.version.desc())
    ).scalars().first()

    for key, value in terms.items():
        if not {"singular", "plural"} <= set(value):
            raise ValueError(f"Terminology for {key!r} needs both singular and plural.")

    if current is not None and current.status is ConfigStatus.published:
        current.status = ConfigStatus.archived

    published = TerminologySet(
        locale=locale,
        status=ConfigStatus.published,
        version=(current.version + 1) if current else 1,
        parent_version_id=current.id if current else None,
        terms=terms,
        published_at=datetime.now(UTC),
        published_by_membership_id=membership_id,
    )
    db.add(published)
    db.flush()
    return published
