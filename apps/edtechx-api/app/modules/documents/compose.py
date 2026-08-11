"""Building what a document says, once, from the academic state it describes.

This is where the historical-integrity rule is actually implemented, so it is
worth stating precisely rather than gesturing at.

**Historical facts — composed here and frozen into the document.**
Every published result and the grading it was given; the credits it carried and
what the institution called them; which programme, level, class and cohort the
student was in *during the period covered*, resolved from the enrolment that was
open then rather than from where they are today; the period's own name and
dates; course names as they stood; attendance for that span; the comments staff
wrote at issue; the progression the institution recorded; qualifications
awarded; the grading key needed to read the grades; and every total, average and
grade-point average, computed once here and never recomputed.

**Current presentation metadata — deliberately resolved fresh at render.**
The institution's crest, colours, address, contact details and letterhead. A
school that moves premises reprints an old transcript with the address that
reaches it today, because an address is a way of contacting an institution and
not a claim about where it stood in 2019. An institution that wants the opposite
sets `freeze_branding` on the template and gets a copy taken at issue.

**Terminology sits on the historical side**, which is the choice most likely to
surprise. A report card that said "Form" when it was issued keeps saying "Form"
after the school renames forms to classes, because the document is a record of
what the institution said, and it said "Form".

Nothing in this module recomputes an issued document. `compose` runs once, at
issue; reprinting reads the payload it produced.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from app.modules.academics import service as academics
from app.modules.assessment import service as assessment
from app.modules.attendance import service as attendance
from app.modules.customization import branding as branding_module
from app.modules.customization import terminology
from app.modules.documents import sections as catalogue
from app.modules.people import service as people

__all__ = ["ComposeError", "Composition", "compose"]


class ComposeError(ValueError):
    """A document that cannot honestly be produced."""


# --- small conversions -----------------------------------------------------
#
# `Numeric` columns arrive as `Decimal`, which JSONB will not take, and dates
# arrive as `date`. Both are converted at the edge so that everything below
# deals in plain JSON values and the payload is serialisable by construction.


def _num(value) -> float | None:
    return None if value is None else float(value)


def _iso(value) -> str | None:
    return None if value is None else value.isoformat()


def _round(value: float | None, places: int) -> float | None:
    return None if value is None else round(value, places)


@dataclass(frozen=True, slots=True)
class Composition:
    """A document's content, ready to be frozen."""

    title: str
    subject: dict
    context: dict
    terms: dict
    blocks: list[dict]
    sources: dict
    branding: dict | None = None
    warnings: tuple[str, ...] = ()

    def as_payload(self) -> dict:
        payload = {
            "title": self.title,
            "subject": self.subject,
            "context": self.context,
            "terminology": self.terms,
            "sections": self.blocks,
        }
        if self.branding is not None:
            payload["branding"] = self.branding
        return payload


@dataclass(slots=True)
class _Gathered:
    """Everything read from the database, before any section is built."""

    student: object
    person: object
    periods: list  # AcademicPeriod rows, in the institution's sequence
    results_by_period: dict  # period_id | None -> list[PublishedResult]
    assessments: dict
    courses: dict
    enrolments: list
    placements: dict  # period_id | None -> list[Enrolment]
    awards: list
    events: list
    scales: dict
    unit_labels: tuple[str, str] = ("", "")
    warnings: list[str] = field(default_factory=list)


# --- gathering --------------------------------------------------------------


# Sections that report on a span of academic time. A document containing none of
# them covers no period, and must not claim one: a certificate of enrolment
# issued in March is not "the autumn term", and subtitling it that way would be
# the document asserting something nobody asked it to.
PERIOD_BEARING = frozenset(
    {
        "course_results",
        "period_results",
        "attainment_summary",
        "credit_summary",
        "grade_points",
        "attendance",
        "progression",
    }
)


def _select_periods(
    db: Session,
    *,
    period_ids: Sequence[uuid.UUID] | None,
    academic_year_id: uuid.UUID | None,
    pairs,
    reports_on_periods: bool = True,
) -> list:
    """Which periods this document covers, in the institution's own order.

    Three ways of asking, in decreasing specificity: the caller names periods, or
    names a year, or names neither and means "everything this student has". The
    third is the transcript case and is why the periods are derived from the
    results rather than from the calendar — a student who joined in the second
    year has no results in the first, and a transcript that printed an empty
    first year would be describing somebody else's degree.
    """
    if period_ids is not None:
        found = [academics.period(db, pid) for pid in period_ids]
        return [p for p in found if p is not None]
    if academic_year_id is not None:
        return academics.periods_in(db, academic_year_id)
    if not reports_on_periods:
        return []

    seen: dict[uuid.UUID, object] = {}
    for _result, pid in pairs:
        if pid is not None and pid not in seen:
            found = academics.period(db, pid)
            if found is not None:
                seen[pid] = found
    return sorted(
        seen.values(),
        key=lambda p: (
            getattr(academics.year(db, p.academic_year_id), "starts_on", date.min),
            p.sequence,
        ),
    )


def _unit_labels(db: Session, results_by_period: dict) -> tuple[str, str]:
    """What this institution calls one unit of credit, and several.

    The singular is a historical fact and is on the published row. The plural is
    not: only the singular was worth a column on `published_results`, so it is
    read from the institution's live credit system — and only when the two
    singulars still agree. An institution that has since renamed its unit gets
    the historical singular in both positions rather than a plural we invented
    by adding an "s" to a word we no longer recognise.
    """
    snapshot = next(
        (
            result.credit_unit_label
            for rows in results_by_period.values()
            for result in rows
            if result.credit_unit_label
        ),
        "",
    )
    singular, plural = academics.credit_unit_label(db, None)
    if not snapshot:
        return (singular, plural)
    if snapshot == singular:
        return (singular, plural)
    return (snapshot, snapshot)


def _gather(
    db: Session,
    *,
    student,
    period_ids: Sequence[uuid.UUID] | None,
    academic_year_id: uuid.UUID | None,
    reports_on_periods: bool = True,
) -> _Gathered:
    person = people.person(db, student.person_id)
    if person is None:
        raise ComposeError(
            "That student record has no person behind it, so there is nobody to "
            "issue a document about."
        )

    everything = assessment.results_with_periods(db, student.id)
    periods = _select_periods(
        db,
        period_ids=period_ids,
        academic_year_id=academic_year_id,
        pairs=everything,
        reports_on_periods=reports_on_periods,
    )
    wanted = {p.id for p in periods}

    results_by_period: dict = {}
    for result, pid in everything:
        if periods and pid not in wanted:
            continue
        results_by_period.setdefault(pid, []).append(result)

    assessment_ids = [
        r.assessment_id for rows in results_by_period.values() for r in rows
    ]
    assessments = assessment.assessment_summaries(db, assessment_ids)

    course_ids = {r.course_id for rows in results_by_period.values() for r in rows}
    course_ids |= {a["course_id"] for a in assessments.values()}
    courses = {
        cid: academics.course(db, cid) for cid in course_ids if cid is not None
    }

    enrolments = people.enrolments_for(db, student)
    placements = {
        p.id: people.enrolment_on(db, student, p.ends_on) for p in periods
    }
    if not periods:
        placements[None] = people.open_enrolments(db, student) or enrolments[-1:]

    scale_codes = {
        r.grading_scale_code for rows in results_by_period.values() for r in rows
    }
    scales = {
        code: academics.grading_scale_by_code(db, code)
        for code in scale_codes
        if code
    }

    unit_labels = _unit_labels(db, results_by_period)

    return _Gathered(
        student=student,
        person=person,
        periods=periods,
        results_by_period=results_by_period,
        assessments=assessments,
        courses=courses,
        enrolments=enrolments,
        placements=placements,
        awards=people.awards_for(db, student),
        events=people.history(db, student),
        scales=scales,
        unit_labels=unit_labels,
    )


# --- course rows ------------------------------------------------------------


def _aggregate(entries: list[dict], how: str) -> tuple[float | None, float | None]:
    """The course-level mark, computed once and frozen.

    Returns `(value, out_of)`. `weighted` uses the weight each assessment
    carried *at publication*, which is on the published row rather than on the
    live assessment — a department that moves coursework from 30% to 40% next
    year has not changed last year's report card.
    """
    marked = [e for e in entries if e["score"] is not None]
    if not marked or how == "none":
        return (None, None)
    if how == "sum":
        out_of = sum(e["max_score"] for e in marked if e["max_score"] is not None)
        return (sum(e["score"] for e in marked), out_of or None)
    if how == "mean":
        percentages = [
            e["score"] / e["max_score"] * 100
            for e in marked
            if e["max_score"]
        ]
        if not percentages:
            return (sum(e["score"] for e in marked) / len(marked), None)
        return (sum(percentages) / len(percentages), 100.0)
    # weighted
    usable = [e for e in marked if e["max_score"] and e["weight"]]
    if not usable:
        return _aggregate(entries, "mean")
    total_weight = sum(e["weight"] for e in usable)
    if not total_weight:
        return _aggregate(entries, "mean")
    value = sum(
        (e["score"] / e["max_score"]) * e["weight"] for e in usable
    ) / total_weight
    return (value * 100, 100.0)


def _course_rows(data: _Gathered, results: list, options: dict) -> list[dict]:
    """One row per course, with its assessments underneath it."""
    grouped: dict = {}
    for result in results:
        course_id = result.course_id or data.assessments.get(
            result.assessment_id, {}
        ).get("course_id")
        grouped.setdefault(course_id, []).append(result)

    how = str(options.get("aggregate") or "none")
    rows: list[dict] = []
    for course_id, entries_raw in grouped.items():
        course = data.courses.get(course_id)
        entries = [
            {
                "assessment": data.assessments.get(r.assessment_id, {}).get(
                    "name", ""
                ),
                "kind_label": data.assessments.get(r.assessment_id, {}).get(
                    "kind_label", ""
                ),
                "score": _num(r.score),
                "max_score": _num(r.max_score),
                "band": r.band_label,
                "points": _num(r.points),
                "is_pass": r.is_pass,
                "is_absent": r.is_absent,
                "weight": _num(r.weight),
                "comment": r.comment,
                "amended": r.amended_at is not None,
            }
            for r in entries_raw
        ]
        credits = next(
            (_num(r.credits) for r in entries_raw if r.credits is not None), None
        )
        value, out_of = _aggregate(entries, how)

        band_label = None
        points = None
        is_pass = None
        if value is not None:
            code = next((r.grading_scale_code for r in entries_raw if r.grading_scale_code), None)
            scale = data.scales.get(code)
            band = scale.band_for(value) if scale is not None else None
            if band is not None:
                band_label, points, is_pass = band.label, _num(band.points), band.is_pass
        if value is None and len(entries) == 1:
            # A single assessment needs no arithmetic: the published band is the
            # course's band, and re-deriving it could disagree with what the
            # institution actually awarded.
            band_label = entries[0]["band"]
            points = entries[0]["points"]
            is_pass = entries[0]["is_pass"]

        rows.append(
            {
                "course": course.name if course else "",
                "course_code": course.code if course else "",
                "credits": credits,
                "entries": entries,
                "score": _round(value, 2),
                "max_score": out_of,
                "percentage": _round(
                    (value / out_of * 100) if value is not None and out_of else None, 2
                ),
                "band": band_label,
                "points": points,
                "is_pass": is_pass,
                "comment": next((e["comment"] for e in entries if e["comment"]), None),
            }
        )

    order = str(options.get("order") or "course")
    key = (lambda r: r["course_code"]) if order == "course_code" else (lambda r: r["course"])
    return sorted(rows, key=key)


def _grade_point_average(rows: list[dict]) -> float | None:
    """Weighted by credit where the institution counts credit, else a mean.

    Returns `None` when no course carries points, which is how a school grading
    A–E with no points ends up with no grade-point average rather than with a
    zero — a number nobody computed is not the same as a number that is zero.
    """
    graded = [r for r in rows if r["points"] is not None]
    if not graded:
        return None
    weighted = [r for r in graded if r["credits"]]
    if weighted:
        total = sum(r["credits"] for r in weighted)
        return sum(r["points"] * r["credits"] for r in weighted) / total
    return sum(r["points"] for r in graded) / len(graded)


def _credit_totals(rows: list[dict]) -> tuple[float, float]:
    attempted = sum(r["credits"] for r in rows if r["credits"])
    earned = sum(r["credits"] for r in rows if r["credits"] and r["is_pass"])
    return (attempted, earned)


# --- placement descriptions -------------------------------------------------


def _describe_placement(db: Session, enrolment) -> dict:
    if enrolment is None:
        return {}
    programme = academics.programme(db, enrolment.programme_id)
    level = academics.level(db, enrolment.level_id)
    group = academics.class_group(db, enrolment.class_group_id)
    cohort = academics.cohort(db, enrolment.cohort_id)
    year = academics.year(db, enrolment.academic_year_id)
    return {
        "programme": programme.name if programme else None,
        "programme_code": programme.code if programme else None,
        "level": level.name if level else None,
        "class_group": group.name if group else None,
        "class_group_kind": group.kind_label if group else None,
        "cohort": cohort.name if cohort else None,
        "academic_year": year.name if year else None,
        "started_on": _iso(enrolment.started_on),
        "ended_on": _iso(enrolment.ended_on),
        "status": enrolment.status.value,
        "outcome": enrolment.outcome.value if enrolment.outcome else None,
    }


# --- the sections -----------------------------------------------------------


def _section_identity(db, data, options, ctx) -> dict:
    person = data.person
    block = {"full_name": person.full_name}
    if options.get("show_reference"):
        block["reference"] = data.student.reference or ""
    if options.get("show_date_of_birth"):
        block["date_of_birth"] = _iso(getattr(person, "date_of_birth", None))
    if options.get("show_guardians"):
        block["guardians"] = [
            {
                "name": (
                    guardian.full_name
                    if (guardian := people.person(db, link.guardian_person_id))
                    else ""
                ),
                "relationship": link.relationship_label or "",
            }
            for link in people.guardians_of(db, person)
        ]
    return block


def _section_placement(db, data, options, ctx) -> dict:
    covered = data.periods[-1] if data.periods else None
    open_now = data.placements.get(covered.id if covered else None) or []
    described = _describe_placement(db, open_now[0] if open_now else None)
    if not options.get("show_class"):
        described.pop("class_group", None)
    if not options.get("show_cohort"):
        described.pop("cohort", None)
    return described


def _section_enrolment_history(db, data, options, ctx) -> dict:
    rows = [_describe_placement(db, e) for e in data.enrolments]
    if not options.get("show_outcomes"):
        for row in rows:
            row.pop("outcome", None)
    return {"rows": rows}


def _section_course_results(db, data, options, ctx) -> dict:
    results = [r for rows in data.results_by_period.values() for r in rows]
    rows = _course_rows(data, results, options)
    return {"columns": list(options.get("columns") or ()), "rows": rows}


def _section_period_results(db, data, options, ctx) -> dict:
    groups = []
    for period in data.periods:
        results = data.results_by_period.get(period.id, [])
        if not results:
            continue
        rows = _course_rows(data, results, options)
        attempted, earned = _credit_totals(rows)
        year = academics.year(db, period.academic_year_id)
        groups.append(
            {
                "period": period.name,
                "kind_label": period.kind_label,
                "academic_year": year.name if year else None,
                "starts_on": _iso(period.starts_on),
                "ends_on": _iso(period.ends_on),
                "placement": _describe_placement(
                    db,
                    (data.placements.get(period.id) or [None])[0],
                ),
                "rows": rows,
                "credits_attempted": attempted or None,
                "credits_earned": earned or None,
                "grade_point_average": _round(_grade_point_average(rows), 2),
            }
        )
    return {"columns": list(options.get("columns") or ()), "groups": groups}


def _all_rows(data, options) -> list[dict]:
    results = [r for rows in data.results_by_period.values() for r in rows]
    return _course_rows(data, results, options)


def _section_attainment_summary(db, data, options, ctx) -> dict:
    rows = _all_rows(data, {"aggregate": "weighted"})
    marked = [r for r in rows if r["score"] is not None]
    block: dict = {"courses": len(rows)}
    if options.get("show_average") and marked:
        block["average"] = _round(
            sum(r["percentage"] or r["score"] for r in marked) / len(marked), 2
        )
    if options.get("show_pass_count"):
        judged = [r for r in rows if r["is_pass"] is not None]
        if judged:
            block["passed"] = sum(1 for r in judged if r["is_pass"])
            block["failed"] = sum(1 for r in judged if not r["is_pass"])
    return block


def _section_credit_summary(db, data, options, ctx) -> dict:
    singular, plural = data.unit_labels
    rows = _all_rows(data, {"aggregate": "weighted"})
    attempted, earned = _credit_totals(rows)
    if not attempted:
        return {}
    block = {
        "unit_label": singular,
        "unit_label_plural": plural,
        "attempted": attempted,
        "earned": earned,
    }
    if options.get("show_cumulative"):
        block["cumulative_earned"] = earned
    return block


def _section_grade_points(db, data, options, ctx) -> dict:
    places = int(options.get("decimal_places") or 2)
    rows = _all_rows(data, {"aggregate": "weighted"})
    average = _grade_point_average(rows)
    if average is None:
        return {}
    block = {"average": _round(average, places), "decimal_places": places}
    if options.get("show_cumulative"):
        block["cumulative"] = _round(average, places)
    return block


def _section_attendance(db, data, options, ctx) -> dict:
    since = data.periods[0].starts_on if data.periods else None
    until = data.periods[-1].ends_on if data.periods else None
    summary = attendance.summarise(db, data.student.id, since=since, until=until)
    if summary.sessions == 0:
        return {}
    block = {"sessions": summary.sessions, "present": summary.present}
    if options.get("show_breakdown"):
        block.update(
            {
                "absent": summary.absent,
                "late": summary.late,
                "excused": summary.excused,
            }
        )
    if options.get("show_rate") and summary.rate is not None:
        block["rate"] = _round(summary.rate * 100, 1)
    return block


def _section_comments(db, data, options, ctx) -> dict:
    supplied = ctx.get("comments") or {}
    slots = list(options.get("slots") or ())
    entries = [
        {"slot": slot, "text": str(supplied[slot]).strip()}
        for slot in slots
        if supplied.get(slot)
    ]
    unknown = set(supplied) - set(slots)
    if unknown:
        raise ComposeError(
            "This template has no comment slot for: " + ", ".join(sorted(unknown))
        )
    return {"entries": entries} if entries else {}


_PROGRESSION_KINDS = {"progressed", "repeated", "completed", "awarded", "withdrawn"}


def _section_progression(db, data, options, ctx) -> dict:
    since = data.periods[0].starts_on if data.periods else None
    until = data.periods[-1].ends_on if data.periods else None
    decisions = [
        {
            "kind": event.kind.value,
            "occurred_on": _iso(event.occurred_on),
            "reason": event.reason,
            "detail": {k: v for k, v in (event.detail or {}).items() if v is not None},
        }
        for event in data.events
        if event.kind.value in _PROGRESSION_KINDS
        and (since is None or event.occurred_on >= since)
        and (until is None or event.occurred_on <= until)
    ]
    latest = data.enrolments[-1] if data.enrolments else None
    block: dict = {"decisions": decisions}
    if latest is not None:
        block["standing"] = latest.status.value
        block["outcome"] = latest.outcome.value if latest.outcome else None
        if options.get("show_next_placement") and latest.ended_on is None:
            block["current"] = _describe_placement(db, latest)
    return block if decisions or latest is not None else {}


def _section_qualifications(db, data, options, ctx) -> dict:
    rows = []
    for granted in data.awards:
        qualification = academics.qualification(db, granted.qualification_id)
        row = {
            "qualification": qualification.name if qualification else "",
            "short_name": (qualification.short_name if qualification else None),
            "category": (qualification.category_label if qualification else None),
            "awarding_body": (qualification.awarding_body if qualification else None),
            "awarded_on": _iso(granted.awarded_on),
        }
        if options.get("show_classification"):
            row["classification"] = granted.classification_label
        if options.get("show_reference"):
            row["reference"] = granted.reference
        rows.append(row)
    return {"rows": rows} if rows else {}


def _section_grading_key(db, data, options, ctx) -> dict:
    scales = []
    for code, scale in sorted(data.scales.items(), key=lambda kv: kv[0] or ""):
        if scale is None:
            continue
        bands = []
        for band in sorted(scale.bands, key=lambda b: b.sequence):
            entry = {"label": band.label, "is_pass": band.is_pass}
            if options.get("show_thresholds"):
                entry["min_value"] = _num(band.min_value)
                entry["max_value"] = _num(band.max_value)
            if options.get("show_descriptors"):
                entry["descriptor"] = band.descriptor
            if band.points is not None:
                entry["points"] = _num(band.points)
            bands.append(entry)
        scales.append({"code": code, "name": scale.name, "bands": bands})
    return {"scales": scales} if scales else {}


def _section_narrative(db, data, options, ctx) -> dict:
    text = str(options.get("text") or "")
    if not text.strip():
        return {}
    return {"text": _substitute(text, data, ctx), "align": options.get("align", "center")}


def _section_signatures(db, data, options, ctx) -> dict:
    overrides = ctx.get("signatories") or {}
    rows = []
    for signatory in options.get("signatories") or ():
        key = str(signatory.get("key") or signatory.get("title"))
        rows.append(
            {
                "key": key,
                "title": str(signatory.get("title") or ""),
                "name": str(overrides.get(key, signatory.get("name") or "")),
                "image_url": signatory.get("image_url") or "",
            }
        )
    return {"signatories": rows, "per_row": int(options.get("per_row") or 2)}


def _section_verification(db, data, options, ctx) -> dict:
    block = {
        "number": ctx.get("number") or "",
        "issued_on": _iso(ctx.get("issued_on")),
        "code": ctx.get("verification_code") or "",
    }
    if options.get("show_checksum"):
        block["checksum"] = ctx.get("checksum") or ""
    if options.get("show_url"):
        block["url"] = ctx.get("verification_url") or ""
    return block


BUILDERS = {
    "identity": _section_identity,
    "placement": _section_placement,
    "enrolment_history": _section_enrolment_history,
    "course_results": _section_course_results,
    "period_results": _section_period_results,
    "attainment_summary": _section_attainment_summary,
    "credit_summary": _section_credit_summary,
    "grade_points": _section_grade_points,
    "attendance": _section_attendance,
    "comments": _section_comments,
    "progression": _section_progression,
    "qualifications": _section_qualifications,
    "grading_key": _section_grading_key,
    "narrative": _section_narrative,
    "signatures": _section_signatures,
    "verification": _section_verification,
}


def _substitute(text: str, data: _Gathered, ctx: dict) -> str:
    """Fill a configured sentence from the document's own facts.

    Deliberately not `str.format`: a template is written by an administrator,
    and `str.format` on administrator-supplied text reaches attributes and
    indexes. Plain replacement of a fixed set of names cannot.
    """
    latest = data.enrolments[-1] if data.enrolments else None
    award = data.awards[-1] if data.awards else None
    values = {
        "{student_name}": data.person.full_name,
        "{reference}": data.student.reference or "",
        "{institution}": ctx.get("institution_name", ""),
        "{date}": _iso(ctx.get("issued_on")) or "",
        "{programme}": "",
        "{level}": "",
        "{qualification}": "",
        "{classification}": "",
    }
    if latest is not None:
        described = ctx["describe"](latest)
        values["{programme}"] = described.get("programme") or ""
        values["{level}"] = described.get("level") or ""
    if award is not None:
        qualification = ctx["qualification_of"](award)
        values["{qualification}"] = qualification
        values["{classification}"] = award.classification_label or ""
    for token, value in values.items():
        text = text.replace(token, value)
    return text


# --- the entry point --------------------------------------------------------


def compose(
    db: Session,
    *,
    template,
    student,
    period_ids: Sequence[uuid.UUID] | None = None,
    academic_year_id: uuid.UUID | None = None,
    comments: dict[str, str] | None = None,
    signatories: dict[str, str] | None = None,
    issued_on: date | None = None,
    number: str = "",
    verification_code: str = "",
    verification_url: str = "",
) -> Composition:
    """Build a document's content from the academic state it describes.

    Called once, at issue. Everything it returns is frozen into the document, so
    a section that would be different tomorrow has to be computed here — which
    is why the totals, the averages and the grade-point average are calculated
    in this module rather than in the renderer.
    """
    data = _gather(
        db,
        student=student,
        period_ids=period_ids,
        academic_year_id=academic_year_id,
        reports_on_periods=any(
            entry["key"] in PERIOD_BEARING and entry.get("visible", True)
            for entry in template.sections
        ),
    )
    words = terminology.resolve(db)
    identity = branding_module.resolve(db)

    ctx = {
        "comments": comments or {},
        "signatories": signatories or {},
        "issued_on": issued_on,
        "number": number,
        "verification_code": verification_code,
        "verification_url": verification_url,
        "institution_name": identity.formal_name,
        "describe": lambda enrolment: _describe_placement(db, enrolment),
        "qualification_of": lambda granted: (
            q.name
            if (q := academics.qualification(db, granted.qualification_id))
            else ""
        ),
    }

    blocks: list[dict] = []
    for entry in template.sections:
        if not entry.get("visible", True):
            continue
        section = catalogue.get(entry["key"])
        content = BUILDERS[section.key](db, data, entry["options"], ctx)
        if not content and entry.get("omit_when_empty", section.omit_when_empty):
            # A section that composed to nothing is dropped. This is the *only*
            # rule that removes a section here, and it is deliberately about the
            # data rather than about the institution's configuration.
            #
            # An earlier version also suppressed any section whose academic layer
            # this institution had no rows in — and a sabotage found it did
            # nothing that this line does not already do, because a section
            # requiring credits can only have content where credits exist. Worse,
            # it could suppress a section that genuinely held historical data: a
            # university that deleted its credit systems would start printing
            # transcripts without the credits its graduates actually earned.
            #
            # "Complexity must be capability, never burden" (ADR-032) belongs at
            # the point where a template is *designed* — `sections.available_to`,
            # which never offers a nursery a grade-point average — not at the
            # point where an issued document is composed from history.
            continue
        blocks.append(
            {
                "key": section.key,
                "title": entry.get("title") or section.default_title,
                "content": content,
            }
        )

    covered = [
        {
            "id": str(p.id),
            "name": p.name,
            "kind_label": p.kind_label,
            "starts_on": _iso(p.starts_on),
            "ends_on": _iso(p.ends_on),
        }
        for p in data.periods
    ]
    year_row = (
        academics.year(db, data.periods[0].academic_year_id) if data.periods else None
    )

    # What this document was composed from, and what those rows looked like at
    # the time. Recorded so `outdated` can answer "has anything behind this
    # changed since?" without keeping a second copy of the results.
    result_ids = [r.id for rows in data.results_by_period.values() for r in rows]
    corrections = assessment.amendment_counts(db, result_ids)
    sources = {
        "published_results": {str(rid): corrections.get(rid, 0) for rid in result_ids},
        "qualification_awards": [str(a.id) for a in data.awards],
    }

    return Composition(
        title=template.purpose_label,
        subject={
            "student_relationship_id": str(data.student.id),
            "person_id": str(data.person.id),
            "full_name": data.person.full_name,
            "reference": data.student.reference or "",
        },
        context={
            "academic_year": year_row.name if year_row else None,
            "academic_year_id": str(year_row.id) if year_row else None,
            "periods": covered,
            "template": {
                "code": template.code,
                "version": template.version,
                "name": template.name,
            },
        },
        terms={key: dict(value) for key, value in words.terms.items()},
        blocks=blocks,
        sources=sources,
        branding=identity.as_dict() if template.freeze_branding else None,
    )
