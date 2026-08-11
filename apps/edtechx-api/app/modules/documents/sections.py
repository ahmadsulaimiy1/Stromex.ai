"""What a document can be made of.

A report card, a transcript, a progress report, a certificate and a completion
statement are not five products. They are five *orderings* of the same small set
of sections, with different ones switched on. So this module is a catalogue —
declared once, validated at boot, exactly like the permission catalogue and the
feature catalogue — and a template is a list of keys from it.

The consequence worth stating plainly: adding "certificate of enrolment" to the
product is a row, not a release. An institution that needs one arranges
`identity`, `placement`, `narrative`, `signatures` and `verification` in its own
order, gives it its own name, and prints it. Nothing here knows the difference
between that document and a doctoral completion statement, because there is no
difference to know.

**Layers gate sections.** A section that requires the `credits` layer is
silently absent for an institution that counts no credits — not shown empty, not
shown greyed out, not shown at all. That is the same rule the navigation
follows (ADR-032): complexity must be capability, never burden. A nursery
choosing sections for its progress report is not offered a grade-point average.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Final

__all__ = [
    "CATALOGUE",
    "PURPOSES",
    "Section",
    "UnknownSection",
    "available_to",
    "get",
    "validate_sections",
]


class UnknownSection(ValueError):
    """A template named a section outside the catalogue."""


def _frozen(mapping: dict[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(mapping)


@dataclass(frozen=True, slots=True)
class Section:
    """One block a document can contain."""

    key: str
    # A starting point, not a decision. Every template may retitle every
    # section, because "Attendance" is "Punctuality and attendance" somewhere
    # and untranslated English somewhere else.
    default_title: str
    # Academic layers whose presence means this section can say anything.
    # Empty means it applies to every institution.
    requires_layers: tuple[str, ...] = ()
    # Whether a section that composed to nothing is dropped. True for almost
    # everything: a report card with an empty "Awards" heading looks like a
    # mistake. False for the few that must appear even when blank — a signature
    # block is *supposed* to be empty until somebody signs it.
    omit_when_empty: bool = True
    default_options: Mapping[str, Any] = field(default_factory=lambda: _frozen({}))
    description: str = ""


# The columns a results table can carry. Named here so a template that asks for
# a column nobody implemented fails at configuration time.
RESULT_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "course",
        "course_code",
        "credits",
        "assessments",
        "score",
        "max_score",
        "percentage",
        "band",
        "points",
        "outcome",
        "comment",
        "weight",
    }
)

AGGREGATIONS: Final[frozenset[str]] = frozenset({"none", "sum", "mean", "weighted"})


CATALOGUE: Final[tuple[Section, ...]] = (
    Section(
        key="identity",
        default_title="Student",
        omit_when_empty=False,
        default_options=_frozen(
            {
                "show_reference": True,
                "show_date_of_birth": False,
                "show_guardians": False,
                "show_photograph": False,
            }
        ),
        description="Who the document is about.",
    ),
    Section(
        key="placement",
        default_title="Placement",
        default_options=_frozen({"show_class": True, "show_cohort": False}),
        description=(
            "Where the student sat during the period covered — resolved from the "
            "enrolment that was open then, never from where they are today."
        ),
    ),
    Section(
        key="enrolment_history",
        default_title="Academic history",
        default_options=_frozen({"show_outcomes": True, "show_gaps": False}),
        description="Every placement, with its dates and how it ended.",
    ),
    Section(
        key="course_results",
        default_title="Results",
        default_options=_frozen(
            {
                "columns": (
                    "course",
                    "assessments",
                    "score",
                    "max_score",
                    "band",
                    "comment",
                ),
                "aggregate": "none",
                "order": "course",
            }
        ),
        description="One row per course for the period covered.",
    ),
    Section(
        key="period_results",
        default_title="Results by period",
        default_options=_frozen(
            {
                "columns": ("course_code", "course", "credits", "band", "points"),
                "aggregate": "weighted",
            }
        ),
        description=(
            "The transcript shape: results grouped under each period, in the "
            "institution's own sequence."
        ),
    ),
    Section(
        key="attainment_summary",
        default_title="Summary",
        default_options=_frozen({"show_average": True, "show_pass_count": True}),
        description="Totals across the courses shown.",
    ),
    Section(
        key="credit_summary",
        default_title="Credit",
        requires_layers=("credits",),
        default_options=_frozen({"show_cumulative": True}),
        description="Attempted and earned, per period and cumulative.",
    ),
    Section(
        key="grade_points",
        default_title="Grade point average",
        default_options=_frozen({"decimal_places": 2, "show_cumulative": True}),
        description=(
            "Present only where the institution's own bands carry points. A "
            "school grading A-E with no points has no GPA and is not shown one."
        ),
    ),
    Section(
        key="attendance",
        default_title="Attendance",
        default_options=_frozen({"show_rate": True, "show_breakdown": True}),
        description="Sessions, presences and absences for the period covered.",
    ),
    Section(
        key="comments",
        default_title="Comments",
        default_options=_frozen({"slots": ("class_teacher", "head")}),
        description=(
            "The remarks staff wrote at issue. Supplied when the document is "
            "issued and frozen with it — a comment is about a moment."
        ),
    ),
    Section(
        key="progression",
        default_title="Progression",
        default_options=_frozen({"show_next_placement": True}),
        description=(
            "What the institution decided, read from the enrolment ledger rather "
            "than recalculated. The decision is a recorded fact."
        ),
    ),
    Section(
        key="qualifications",
        default_title="Award",
        requires_layers=("qualifications",),
        default_options=_frozen({"show_classification": True, "show_reference": True}),
        description="Qualifications awarded, with their classification.",
    ),
    Section(
        key="grading_key",
        default_title="Grading",
        requires_layers=("grading",),
        default_options=_frozen({"show_thresholds": True, "show_descriptors": False}),
        description=(
            "The scale the results were graded on, as it stood when they were "
            "published — so a reader in 2031 can interpret a 2026 grade."
        ),
    ),
    Section(
        key="narrative",
        default_title="",
        omit_when_empty=True,
        default_options=_frozen({"text": "", "align": "center"}),
        description=(
            "Configured prose with substitutions — the body of a certificate. "
            "Substituted at issue, then frozen."
        ),
    ),
    Section(
        key="signatures",
        default_title="Signed",
        omit_when_empty=False,
        # Layout only. `signatories` used to be here — a list of
        # `{title, name, image_url}` typed into the template — which meant
        # anybody who could edit a template could put any name and any picture
        # on a transcript. Who signs now comes from the signatory registry and
        # is not configurable from the design (ADR-040).
        default_options=_frozen({"per_row": 2}),
        description=(
            "Who certified the document, resolved from the institution's "
            "signatory registry at issue and frozen."
        ),
    ),
    Section(
        key="verification",
        default_title="Verification",
        omit_when_empty=False,
        default_options=_frozen({"show_checksum": False, "show_url": True}),
        description=(
            "Document number, issue date, and the code a third party uses to "
            "check the document is genuine."
        ),
    ),
)

BY_KEY: Final[dict[str, Section]] = {s.key: s for s in CATALOGUE}


# The permission resource a template is governed by. Three, not one, because a
# school that lets a form tutor print report cards has not thereby let them
# print transcripts — and because "document" has to exist for the certificates
# and statements neither word covers.
PURPOSES: Final[frozenset[str]] = frozenset({"report_card", "transcript", "document"})


def get(key: str) -> Section:
    try:
        return BY_KEY[key]
    except KeyError:
        raise UnknownSection(
            f"{key!r} is not a document section. Known sections: "
            + ", ".join(sorted(BY_KEY))
        ) from None


def available_to(layers: frozenset[str]) -> tuple[Section, ...]:
    """The sections an institution with these layers can meaningfully use.

    What the template designer is *offered*. An institution that counts no
    credits is not shown a credit section it would have to leave empty, for the
    same reason its navigation has no Programmes item.
    """
    return tuple(
        s
        for s in CATALOGUE
        if not s.requires_layers or any(layer in layers for layer in s.requires_layers)
    )


def validate_sections(sections: list[dict]) -> list[dict]:
    """Normalise a template's section list, or refuse it.

    Every option is merged over the section's defaults here rather than at
    render time, so a template row is self-describing: reading it tells you what
    the document will contain without also knowing which release built it.
    """
    if not sections:
        raise UnknownSection("A document template with no sections prints nothing.")

    seen: set[str] = set()
    normalised: list[dict] = []
    for index, entry in enumerate(sections):
        key = str(entry.get("key") or "").strip()
        if not key:
            raise UnknownSection(f"Section {index + 1} has no key.")
        section = get(key)
        if key in seen:
            raise UnknownSection(f"Section {key!r} appears twice.")
        seen.add(key)

        options = dict(section.default_options)
        options.update(entry.get("options") or {})
        _validate_options(key, options)

        normalised.append(
            {
                "key": key,
                "title": str(entry.get("title") or section.default_title),
                "visible": bool(entry.get("visible", True)),
                "omit_when_empty": bool(
                    entry.get("omit_when_empty", section.omit_when_empty)
                ),
                "options": options,
            }
        )
    return normalised


def _validate_options(key: str, options: dict) -> None:
    columns = options.get("columns")
    if columns is not None:
        unknown = {str(c) for c in columns} - RESULT_COLUMNS
        if unknown:
            raise UnknownSection(
                f"Section {key!r} asks for columns that do not exist: "
                + ", ".join(sorted(unknown))
            )
    aggregate = options.get("aggregate")
    if aggregate is not None and str(aggregate) not in AGGREGATIONS:
        raise UnknownSection(
            f"Section {key!r} asks for an unknown aggregation {aggregate!r}. "
            "One of: " + ", ".join(sorted(AGGREGATIONS))
        )
    if key == "signatures" and options.get("signatories"):
        # Refused rather than ignored. A template carrying its own list of
        # signatory names is a template written against the old model, and
        # silently dropping the list would print a document signed by somebody
        # other than whom its author intended — which is worse than refusing.
        raise UnknownSection(
            "Signatories are no longer configured on a template. Who signs comes "
            "from the institution's signatory registry; list the offices this "
            "document requires in the template's `signatories` setting instead."
        )


def validate_catalogue() -> None:
    """Called at boot, on the same principle as the permission catalogue."""
    keys = [s.key for s in CATALOGUE]
    if len(keys) != len(set(keys)):
        raise ValueError("Two document sections share a key.")
    for section in CATALOGUE:
        _validate_options(section.key, dict(section.default_options))
