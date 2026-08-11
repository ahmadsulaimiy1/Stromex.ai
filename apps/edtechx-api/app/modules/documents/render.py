"""Turning a stored payload into a page.

This module reads `document.payload` and the institution's *current* branding.
It reads nothing else — no results, no enrolments, no grading scales — and that
constraint is the design rather than an omission. A renderer with database
access is a renderer that will eventually be asked to "just refresh the totals",
and the day it does, every reprint of every historical transcript quietly
becomes a different document.

The HTML is deliberately self-contained and unstyled by any external sheet:
a document is printed, emailed, and archived, and the copy that arrives three
years later has to render without our stylesheet still existing at that URL.
"""

from __future__ import annotations

from html import escape

from app.modules.customization.branding import Branding

__all__ = ["render_html", "render_text"]


def _e(value) -> str:
    return escape("" if value is None else str(value))


def _number(value) -> str:
    """Print 8 rather than 8.0, and 8.5 as 8.5.

    Small, and the difference between a transcript that looks typeset and one
    that looks like a spreadsheet export.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)) and float(value).is_integer():
        return str(int(value))
    return str(value)


# --- the page ---------------------------------------------------------------


def _styles(branding: Branding, page: dict) -> str:
    margin = page.get("margin_mm", 18)
    size = page.get("size", "A4")
    orientation = page.get("orientation", "portrait")
    heading = branding.heading_font or "Georgia, 'Times New Roman', serif"
    body = branding.body_font or "'Helvetica Neue', Arial, sans-serif"
    return f"""
@page {{ size: {_e(size)} {_e(orientation)}; margin: {_e(margin)}mm; }}
:root {{
  --ink: {_e(branding.ink_colour)};
  --primary: {_e(branding.primary_colour)};
  --accent: {_e(branding.accent_colour)};
  --rule: color-mix(in srgb, var(--ink) 14%, transparent);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: {_e(margin)}mm;
  font-family: {_e(body)}; color: var(--ink); background: #fff;
  font-size: 11pt; line-height: 1.45;
}}
h1, h2, h3, .masthead__name {{ font-family: {_e(heading)}; font-weight: 600; }}
.masthead {{
  display: flex; align-items: flex-start; gap: 16px;
  padding-bottom: 12px; border-bottom: 2px solid var(--primary); margin-bottom: 20px;
}}
.masthead__crest {{ height: 64px; width: auto; }}
.masthead__name {{ font-size: 18pt; color: var(--primary); margin: 0 0 2px; }}
.masthead__motto {{ font-style: italic; opacity: .75; margin: 0 0 4px; }}
.masthead__contact {{ font-size: 8.5pt; opacity: .7; margin: 0; }}
.doc-title {{
  font-size: 13pt; letter-spacing: .14em; text-transform: uppercase;
  text-align: center; margin: 0 0 4px; color: var(--primary);
}}
.doc-context {{ text-align: center; font-size: 9.5pt; opacity: .75; margin: 0 0 22px; }}
section {{ margin-bottom: 18px; break-inside: avoid; }}
section > h2 {{
  font-size: 9.5pt; letter-spacing: .1em; text-transform: uppercase;
  color: var(--accent); border-bottom: 1px solid var(--rule);
  padding-bottom: 3px; margin: 0 0 8px;
}}
dl.fields {{ display: grid; grid-template-columns: auto 1fr; gap: 2px 14px; margin: 0; }}
dl.fields dt {{ font-size: 9pt; opacity: .65; }}
dl.fields dd {{ margin: 0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 10pt; }}
th {{
  text-align: left; font-size: 8.5pt; letter-spacing: .06em; text-transform: uppercase;
  opacity: .6; border-bottom: 1px solid var(--rule); padding: 5px 6px;
}}
td {{ padding: 5px 6px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.entries {{ font-size: 8.5pt; opacity: .7; }}
.narrative {{ font-size: 12pt; line-height: 1.8; margin: 28px auto; max-width: 46em; }}
.signatures {{ display: flex; gap: 32px; margin-top: 34px; }}
.signature {{ flex: 1; }}
.signature__line {{ border-top: 1px solid var(--ink); padding-top: 4px; font-size: 9pt; }}
.signature__title {{ opacity: .6; font-size: 8.5pt; }}
.verification {{
  margin-top: 26px; padding-top: 8px; border-top: 1px solid var(--rule);
  font-size: 8pt; opacity: .7; display: flex; justify-content: space-between; gap: 12px;
}}
.footer-note {{ margin-top: 6px; font-size: 8pt; opacity: .6; }}
.void {{
  position: fixed; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 72pt; color: rgba(180, 30, 30, .16); transform: rotate(-24deg);
  letter-spacing: .2em; pointer-events: none;
}}
"""


def _masthead(branding: Branding) -> str:
    crest = (
        f'<img class="masthead__crest" src="{_e(branding.crest_url or branding.logo_url)}" alt="">'
        if (branding.crest_url or branding.logo_url)
        else ""
    )
    contact = " · ".join(
        part
        for part in (
            branding.address,
            branding.contact_phone,
            branding.contact_email,
            branding.website,
        )
        if part
    )
    motto = (
        f'<p class="masthead__motto">{_e(branding.motto)}</p>' if branding.motto else ""
    )
    return (
        '<header class="masthead">'
        f"{crest}"
        "<div>"
        f'<p class="masthead__name">{_e(branding.formal_name)}</p>'
        f"{motto}"
        f'<p class="masthead__contact">{_e(contact)}</p>'
        "</div>"
        "</header>"
    )


# --- sections ---------------------------------------------------------------


def _fields(pairs) -> str:
    rows = "".join(
        f"<dt>{_e(label)}</dt><dd>{_e(value)}</dd>"
        for label, value in pairs
        if value not in (None, "", [])
    )
    return f'<dl class="fields">{rows}</dl>' if rows else ""


_COLUMN_LABELS = {
    "course": "Course",
    "course_code": "Code",
    "credits": "Credits",
    "assessments": "Assessments",
    "score": "Mark",
    "max_score": "Out of",
    "percentage": "%",
    "band": "Grade",
    "points": "Points",
    "outcome": "Outcome",
    "comment": "Comment",
    "weight": "Weight",
}

_NUMERIC_COLUMNS = {"credits", "score", "max_score", "percentage", "points", "weight"}


def _cell(row: dict, column: str, terms: dict) -> str:
    if column == "assessments":
        return '<span class="entries">' + _e(
            "; ".join(
                f"{entry['assessment']} {_number(entry['score'])}"
                + (f"/{_number(entry['max_score'])}" if entry.get("max_score") else "")
                for entry in row.get("entries") or []
            )
        ) + "</span>"
    if column == "outcome":
        passed = row.get("is_pass")
        return "" if passed is None else ("Pass" if passed else "Fail")
    value = row.get(column)
    return _e(_number(value)) if column in _NUMERIC_COLUMNS else _e(value)


def _label_for(column: str, terms: dict) -> str:
    """Column headings in the institution's own words where it has one."""
    if column in ("course", "course_code"):
        word = (terms.get("course") or {}).get("singular")
        base = (word or "course").title()
        return base if column == "course" else "Code"
    if column == "credits":
        return (terms.get("credit") or {}).get("plural", "credits").title()
    if column == "band":
        return (terms.get("grade") or {}).get("singular", "grade").title()
    return _COLUMN_LABELS.get(column, column.replace("_", " ").title())


def _results_table(columns: list[str], rows: list[dict], terms: dict) -> str:
    if not rows:
        return ""
    columns = columns or ["course", "score", "band"]
    # A column every row leaves empty is a column that makes the page look
    # unfinished, so it is dropped rather than printed blank.
    used = [
        column
        for column in columns
        if column == "course"
        or any(_cell(row, column, terms).strip() for row in rows)
    ]
    head = "".join(
        f'<th class="{"num" if c in _NUMERIC_COLUMNS else ""}">{_e(_label_for(c, terms))}</th>'
        for c in used
    )
    body = "".join(
        "<tr>"
        + "".join(
            f'<td class="{"num" if c in _NUMERIC_COLUMNS else ""}">{_cell(row, c, terms)}</td>'
            for c in used
        )
        + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _render_section(block: dict, terms: dict, branding: Branding) -> str:
    key = block["key"]
    content = block.get("content") or {}
    title = block.get("title") or ""

    if key == "identity":
        inner = _fields(
            [
                ("Name", content.get("full_name")),
                ("Reference", content.get("reference")),
                ("Date of birth", content.get("date_of_birth")),
            ]
            + [
                (guardian["relationship"].title(), guardian["name"])
                for guardian in content.get("guardians") or []
            ]
        )
    elif key == "placement":
        inner = _fields(
            [
                ((terms.get("programme") or {}).get("singular", "programme").title(),
                 content.get("programme")),
                ((terms.get("level") or {}).get("singular", "level").title(),
                 content.get("level")),
                (content.get("class_group_kind") or "Class", content.get("class_group")),
                ((terms.get("cohort") or {}).get("singular", "cohort").title(),
                 content.get("cohort")),
                ("Academic year", content.get("academic_year")),
            ]
        )
    elif key == "enrolment_history":
        rows = content.get("rows") or []
        cells = "".join(
            "<tr>"
            f"<td>{_e(row.get('academic_year'))}</td>"
            f"<td>{_e(row.get('programme') or row.get('level'))}</td>"
            f"<td>{_e(row.get('class_group'))}</td>"
            f"<td>{_e(row.get('started_on'))}</td>"
            f"<td>{_e(row.get('ended_on') or '—')}</td>"
            f"<td>{_e(row.get('outcome') or row.get('status'))}</td>"
            "</tr>"
            for row in rows
        )
        inner = (
            "<table><thead><tr><th>Year</th><th>Programme</th><th>Group</th>"
            "<th>From</th><th>To</th><th>Outcome</th></tr></thead>"
            f"<tbody>{cells}</tbody></table>"
        )
    elif key == "course_results":
        inner = _results_table(content.get("columns") or [], content.get("rows") or [], terms)
    elif key == "period_results":
        parts = []
        for group in content.get("groups") or []:
            heading = " · ".join(
                part for part in (group.get("academic_year"), group.get("period")) if part
            )
            totals = _fields(
                [
                    ("Credits earned", _number(group.get("credits_earned"))),
                    ("Average", _number(group.get("grade_point_average"))),
                ]
            )
            parts.append(
                f"<h3>{_e(heading)}</h3>"
                + _results_table(content.get("columns") or [], group.get("rows") or [], terms)
                + totals
            )
        inner = "".join(parts)
    elif key == "attainment_summary":
        inner = _fields(
            [
                ("Courses", content.get("courses")),
                ("Average", _number(content.get("average"))),
                ("Passed", content.get("passed")),
                ("Not passed", content.get("failed")),
            ]
        )
    elif key == "credit_summary":
        unit = content.get("unit_label_plural") or "credits"
        inner = _fields(
            [
                (f"{unit.title()} attempted", _number(content.get("attempted"))),
                (f"{unit.title()} earned", _number(content.get("earned"))),
                (
                    f"Cumulative {unit}",
                    _number(content.get("cumulative_earned")),
                ),
            ]
        )
    elif key == "grade_points":
        inner = _fields(
            [
                ("Average", _number(content.get("average"))),
                ("Cumulative", _number(content.get("cumulative"))),
            ]
        )
    elif key == "attendance":
        inner = _fields(
            [
                ("Sessions", content.get("sessions")),
                ("Present", content.get("present")),
                ("Absent", content.get("absent")),
                ("Late", content.get("late")),
                ("Excused", content.get("excused")),
                (
                    "Rate",
                    f"{_number(content['rate'])}%"
                    if content.get("rate") is not None
                    else None,
                ),
            ]
        )
    elif key == "comments":
        inner = "".join(
            f'<p><strong>{_e(entry["slot"].replace("_", " ").title())}</strong><br>'
            f"{_e(entry['text'])}</p>"
            for entry in content.get("entries") or []
        )
    elif key == "progression":
        inner = _fields(
            [("Standing", content.get("standing")), ("Outcome", content.get("outcome"))]
        ) + "".join(
            f"<p>{_e(decision['kind'].title())} — {_e(decision['occurred_on'])}"
            + (f" ({_e(decision['reason'])})" if decision.get("reason") else "")
            + "</p>"
            for decision in content.get("decisions") or []
        )
    elif key == "qualifications":
        inner = "".join(
            _fields(
                [
                    ("Award", row.get("qualification")),
                    ("Classification", row.get("classification")),
                    ("Awarded", row.get("awarded_on")),
                    ("Reference", row.get("reference")),
                    ("Awarding body", row.get("awarding_body")),
                ]
            )
            for row in content.get("rows") or []
        )
    elif key == "grading_key":
        parts = []
        for scale in content.get("scales") or []:
            cells = "".join(
                "<tr>"
                f"<td>{_e(band['label'])}</td>"
                f"<td class=\"num\">{_e(_number(band.get('min_value')))}</td>"
                f"<td class=\"num\">{_e(_number(band.get('max_value')))}</td>"
                f"<td class=\"num\">{_e(_number(band.get('points')))}</td>"
                f"<td>{_e(band.get('descriptor') or '')}</td>"
                "</tr>"
                for band in scale.get("bands") or []
            )
            parts.append(
                f"<h3>{_e(scale.get('name'))}</h3>"
                "<table><thead><tr><th>Grade</th><th class='num'>From</th>"
                "<th class='num'>To</th><th class='num'>Points</th><th>Descriptor</th>"
                f"</tr></thead><tbody>{cells}</tbody></table>"
            )
        inner = "".join(parts)
    elif key == "narrative":
        align = content.get("align", "center")
        return (
            f'<div class="narrative" style="text-align:{_e(align)}">'
            + "".join(
                f"<p>{_e(paragraph)}</p>"
                for paragraph in str(content.get("text") or "").split("\n\n")
            )
            + "</div>"
        )
    elif key == "signatures":
        blocks = "".join(
            '<div class="signature">'
            + (
                f'<img src="{_e(s["image_url"])}" alt="" style="height:36px">'
                if s.get("image_url")
                else '<div style="height:36px"></div>'
            )
            + f'<div class="signature__line">{_e(s.get("name") or "")}</div>'
            f'<div class="signature__title">{_e(s.get("title"))}</div>'
            "</div>"
            for s in content.get("signatories") or []
        )
        return f'<div class="signatures">{blocks}</div>' if blocks else ""
    elif key == "verification":
        url = content.get("url") or ""
        right = (
            f'Verify at {_e(url)}'
            if url
            else (f"Code {_e(content.get('code'))}" if content.get("code") else "")
        )
        return (
            '<div class="verification">'
            f"<span>{_e(content.get('number'))} · issued {_e(content.get('issued_on'))}</span>"
            f"<span>{right}</span>"
            "</div>"
        )
    else:  # pragma: no cover - every catalogue key is handled above
        inner = ""

    if not inner:
        return ""
    return f"<section><h2>{_e(title)}</h2>{inner}</section>"


# --- entry points -----------------------------------------------------------


def render_html(
    payload: dict,
    *,
    branding: Branding,
    page: dict | None = None,
    watermark: str = "",
) -> str:
    """A complete, self-contained page for one document.

    `payload` is the document's frozen content and `branding` is resolved by the
    caller — from the document itself when the template froze it, otherwise from
    the institution as it stands today. This function never chooses between the
    two, because that is a policy decision and this is a renderer.
    """
    page = page or {}
    terms = payload.get("terminology") or {}
    context = payload.get("context") or {}
    periods = context.get("periods") or []
    subtitle = " · ".join(
        part
        for part in (
            context.get("academic_year"),
            ", ".join(p["name"] for p in periods) if periods else "",
        )
        if part
    )

    body = "".join(
        _render_section(block, terms, branding)
        for block in payload.get("sections") or []
    )
    footer = (
        f'<p class="footer-note">{_e(branding.footer_note)}</p>'
        if branding.footer_note
        else ""
    )
    stamp = f'<div class="void">{_e(watermark)}</div>' if watermark else ""

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{_e(payload.get('title'))} — "
        f"{_e((payload.get('subject') or {}).get('full_name'))}</title>"
        f"<style>{_styles(branding, page)}</style></head><body>"
        f"{stamp}{_masthead(branding)}"
        f"<h1 class='doc-title'>{_e(payload.get('title'))}</h1>"
        + (f"<p class='doc-context'>{_e(subtitle)}</p>" if subtitle else "")
        + f"{body}{footer}</body></html>"
    )


def render_text(payload: dict) -> str:
    """A plain-text rendering, for an email body or an accessibility fallback.

    Same payload, same frozen content; the difference is only how it is set. A
    second renderer exists mainly to prove the payload is genuinely presentation
    -independent — if it were not, this one could not be written.
    """
    lines: list[str] = [str(payload.get("title") or "")]
    subject = payload.get("subject") or {}
    if subject.get("full_name"):
        lines.append(subject["full_name"])
    for block in payload.get("sections") or []:
        content = block.get("content") or {}
        lines.append("")
        lines.append(str(block.get("title") or "").upper())
        if "rows" in content:
            for row in content["rows"]:
                label = row.get("course") or row.get("qualification") or ""
                value = row.get("band") or row.get("classification") or ""
                lines.append(f"  {label}: {_number(row.get('score'))} {value}".rstrip())
        elif "groups" in content:
            for group in content["groups"]:
                lines.append(f"  {group.get('period')}")
                for row in group.get("rows") or []:
                    lines.append(
                        f"    {row.get('course')}: {row.get('band') or ''}".rstrip()
                    )
        else:
            for key, value in content.items():
                if isinstance(value, (str, int, float)) and value != "":
                    lines.append(f"  {key.replace('_', ' ').title()}: {value}")
    return "\n".join(lines)
