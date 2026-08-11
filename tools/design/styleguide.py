"""Render the EdirasX design system as a page, so it can be looked at.

A design system that exists only as tokens is a design system nobody has seen.
This renders every foundation and every component in every state onto one page,
which is what makes it possible to notice that a disabled button is invisible or
that the gold fails on ivory — the things no unit test will ever tell you.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "apps" / "edtechx-api"))

from app.modules.design import components as ui  # noqa: E402
from app.modules.design import contrast as ink  # noqa: E402
from app.modules.design import ornament  # noqa: E402
from app.modules.design.shell import document  # noqa: E402
from app.modules.design.theme import resolve, review  # noqa: E402
from app.modules.design.tokens import PRIMITIVES  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[2] / "docs" / "edtechx" / "design"

EXTRA = """
.sg { max-width: 78rem; margin: 0 auto; padding: var(--space-10) var(--space-7) var(--space-13); }
.sg__masthead { display: flex; align-items: center; gap: var(--space-5);
  padding-block-end: var(--space-6); border-block-end: 1px solid var(--border-hairline); }
.sg__title { font-family: var(--font-display); font-size: var(--text-4xl);
  font-weight: 600; letter-spacing: var(--tracking-tighter); margin: 0; line-height: 1; }
.sg__sub { color: var(--text-secondary); margin: var(--space-2) 0 0; font-size: var(--text-sm); }
.sg__row { display: flex; flex-wrap: wrap; gap: var(--space-3); align-items: center; }
.sg__stack { display: grid; gap: var(--space-4); }
.sg__swatches { display: grid; grid-template-columns: repeat(auto-fill, minmax(7rem, 1fr));
  gap: var(--space-3); }
.sg__swatch { border: 1px solid var(--border-hairline); border-radius: var(--radius-sm);
  overflow: hidden; }
.sg__chip { height: 3.25rem; }
.sg__meta { padding: var(--space-2) var(--space-3); font-size: var(--text-3xs);
  font-family: var(--font-mono); color: var(--text-secondary); display: flex;
  justify-content: space-between; gap: var(--space-3); }
.sg__type td { padding: var(--space-3) var(--space-4) var(--space-3) 0;
  border-block-end: 1px solid var(--border-hairline); vertical-align: baseline; }
.sg__verdict { display: grid; grid-template-columns: 1fr auto; gap: var(--space-3);
  padding: var(--space-2) 0; border-block-end: 1px solid var(--border-hairline);
  font-size: var(--text-sm); align-items: baseline; }
.sg__ratio { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.sg__ok { color: var(--text-success); } .sg__warn { color: var(--text-warning); }
.sg__err { color: var(--text-danger); }
.sg__dark { background: var(--midnight-800); padding: var(--space-6);
  border-radius: var(--radius-md); }
.sg__dark * { color: var(--ivory-50); }
"""


def swatches(group: str) -> str:
    scale = PRIMITIVES[group]
    cells = []
    for step, value in scale.items():
        on_white = ink.contrast(value, "#FAF6EE")
        cells.append(
            f'<div class="sg__swatch"><div class="sg__chip" style="background:{value}"></div>'
            f'<div class="sg__meta"><span>{group}.{step}</span>'
            f"<span>{on_white:.1f}</span></div></div>"
        )
    return f'<div class="sg__swatches">{"".join(cells)}</div>'


def type_scale() -> str:
    samples = [
        ("6xl", "display", "Meridian", "Hero"),
        ("4xl", "display", "Academic Transcript", "Page title"),
        ("2xl", "display", "Autumn Term results", "Section title"),
        ("lg", "display", "Ada Nwosu", "Record heading"),
        ("md", "sans", "The institution defines its academic world.", "Lede"),
        ("base", "sans", "EdirasX provides the technology to represent it.", "Body"),
        ("sm", "sans", "Chemistry · Examination · 82 out of 100", "Data"),
        ("2xs", "sans", "Issued 18 December 2026", "Meta"),
        ("3xs", "sans", "ACADEMIC RECORD", "Micro-label"),
    ]
    rows = []
    for size, family, text, role in samples:
        style = (
            f"font-family:var(--font-{family});font-size:var(--text-{size});"
            + ("font-weight:600;letter-spacing:var(--tracking-tighter);"
               if family == "display" else "")
            + ("letter-spacing:var(--tracking-widest);text-transform:uppercase;"
               "font-weight:600;" if size == "3xs" else "")
        )
        rows.append(
            f'<tr><td style="{style}">{text}</td>'
            f'<td class="ed-label" style="white-space:nowrap">{role}</td>'
            f'<td class="ed-quiet" style="font-family:var(--font-mono);'
            f'font-size:var(--text-3xs);white-space:nowrap">--text-{size}</td></tr>'
        )
    return f'<table class="sg__type" style="width:100%">{"".join(rows)}</table>'


def guardrails() -> str:
    verdicts = review(resolve()).verdicts
    rows = []
    for verdict in verdicts:
        tone = {"ok": "sg__ok", "warning": "sg__warn", "error": "sg__err"}[verdict.severity]
        rows.append(
            f'<div class="sg__verdict"><span>{ui.e(verdict.role)}</span>'
            f'<span class="sg__ratio {tone}">{verdict.ratio}:1</span></div>'
        )
    return "".join(rows)


def build() -> str:
    theme = resolve()
    parts: list[str] = ['<div class="sg">']

    parts.append(
        '<header class="sg__masthead">'
        + ornament.monogram(64)
        + "<div><h1 class=\"sg__title\">EdirasX</h1>"
        '<p class="sg__sub">The design system. Royal institution, rendered by a '
        "precision instrument.</p></div></header>"
    )

    parts.append(ui.section("Identity", (
        '<div class="ed-grid ed-grid--3" style="align-items:center">'
        + f"<div>{ornament.monogram(120)}"
        '<p class="ed-lede" style="margin-block-start:var(--space-4);font-size:var(--text-sm)">'
        "The seal — two squares at 45° — with the X held in its centre as void. "
        "The Latin letterform is produced by the Arabic geometry rather than "
        "placed beside it.</p></div>"
        + '<div style="display:grid;gap:var(--space-4);justify-items:start">'
        + f"<div>{ornament.node(10)}</div>"
        + f"<div style=\"width:100%\">{ornament.rule()}</div>"
        + f"<div>{ornament.corner(48)}</div>"
        + f"<div>{ornament.spinner(28)}</div>"
        + '<p class="ed-label">Node · rule · corner · progress</p></div>'
        + '<div style="position:relative;height:12rem;background:var(--midnight-800);'
        'border-radius:var(--radius-md);overflow:hidden">'
        + '<div style="position:absolute;inset:0;opacity:.12;color:var(--gold-500)">'
        + ornament.lattice(cell=58) + "</div>"
        + '<p class="ed-label" style="position:absolute;bottom:var(--space-4);'
        'left:var(--space-4);color:var(--gold-500)">Lattice · ceremonial ground</p></div>'
        + "</div>"
    ), heading="One construction, at five scales"))

    parts.append(ui.section("Palette", (
        '<div class="sg__stack">'
        + "".join(
            f'<div><p class="ed-label" style="margin-block-end:var(--space-2)">{name}</p>'
            f"{swatches(group)}</div>"
            for group, name in (
                ("midnight", "Midnight — the institutional ground"),
                ("royal", "Royal — authority, and the interactive colour"),
                ("gold", "Champagne — jewellery, never a background"),
                ("ivory", "Ivory — the page"),
                ("charcoal", "Charcoal — text and structure"),
                ("garnet", "Garnet — ceremonial, and error"),
            )
        )
        + "</div>"
    ), heading="Six ramps. The number beside each step is its contrast on ivory."))

    parts.append(ui.section("Typography", type_scale(),
                            heading="Source Serif 4 carries identity; Inter carries work"))

    parts.append(ui.section("Arabic", (
        '<div class="ed-grid ed-grid--2">'
        '<div><p class="ed-arabic" style="font-size:var(--text-2xl);margin:0">'
        "الدراسة — طلب العلم</p>"
        '<p class="ed-arabic" style="margin-block-start:var(--space-3)">'
        "تُعرّف المؤسسة عالمها الأكاديمي، وتوفّر إدراس إكس التقنية اللازمة لتمثيله.</p></div>"
        '<p class="ed-lede" style="font-size:var(--text-sm)">Amiri, set at 1.15× with its '
        "own line height so it sits level with the Latin rather than beneath it. "
        "Arabic is a family in this system, not a fallback the Latin stack falls "
        "through to.</p></div>"
    ), heading="A first-class family, not a fallback"))

    parts.append(ui.section("Actions", (
        '<div class="sg__stack">'
        f'<div class="sg__row">{ui.button("Save changes", variant="primary")}'
        f'{ui.button("Issue transcript", variant="ceremonial")}'
        f'{ui.button("Cancel")}{ui.button("Remove", variant="danger")}'
        f'{ui.button("Learn more", variant="quiet")}</div>'
        f'<div class="sg__row">{ui.button("Disabled", variant="primary", disabled=True)}'
        f'{ui.button("Disabled")}{ui.button("Publishing", variant="primary", loading=True)}'
        f'{ui.button("Small", size="sm")}'
        f'{ui.button("Small primary", variant="primary", size="sm")}</div>'
        f'<p>An ordinary sentence containing <a class="ed-link" href="#">a link</a> '
        "so its weight against body text can be judged.</p>"
        "</div>"
    ), heading="Gold is earned by consequence, not by prominence"))

    parts.append(ui.section("Fields", (
        '<div class="ed-grid ed-grid--3">'
        + ui.field("Student name", ui.text_input(value="Ada Nwosu"))
        + ui.field("Admission number", ui.text_input(placeholder="e.g. S-001"),
                   hint="The institution's own identifier.")
        + ui.field("Academic year", ui.select(
            [("2026", "2026/27"), ("2025", "2025/26")], value="2026"))
        + ui.field("Date of birth", ui.text_input(value="2011-04-02", invalid=True),
                   error="This date is in the future.")
        + ui.field("Locked", ui.text_input(value="Cannot be changed", disabled=True))
        + ui.field("Comment", ui.textarea(placeholder="A remark for the report card…"))
        + "</div>"
        + '<div class="ed-choices" style="margin-block-start:var(--space-5)">'
        + ui.checkbox("Receives reports", checked=True)
        + ui.checkbox("Emergency contact")
        + ui.checkbox("Unavailable", disabled=True)
        + ui.checkbox("Primary guardian", radio=True, checked=True, name="g")
        + ui.checkbox("Secondary", radio=True, name="g")
        + ui.switch("Publish to families", on=True)
        + ui.switch("Locked", disabled=True)
        + "</div>"
    ), heading="Every state, declared rather than discovered"))

    parts.append(ui.section("Status", (
        '<div class="sg__row">'
        + "".join(
            ui.badge(label, tone=tone) for label, tone in (
                ("Enrolled", "success"), ("Published", "accent"), ("Distinction", "gold"),
                ("Pending review", "warning"), ("Withdrawn", "danger"), ("Draft", "neutral"),
            )
        )
        + f'{ui.avatar("Ada Nwosu")}{ui.avatar("Nadia Rahman", large=True)}'
        + "</div>"
        + '<div class="ed-grid ed-grid--2" style="margin-block-start:var(--space-5)">'
        + ui.alert("Two marks are missing for children who have since left. "
                   "You may publish over this with a reason.",
                   title="Not ready to publish", tone="warning")
        + ui.alert("The autumn term results were published on 18 December.",
                   title="Published", tone="success")
        + "</div>"
    ), heading="Badges, avatars, alerts"))

    parts.append(ui.section("Figures", (
        ui.figures([
            ui.figure("On roll", "412", delta="+18 this term", direction="up"),
            ui.figure("Attendance", "96.4", unit="%", delta="−0.8", direction="down"),
            ui.figure("Results published", "7", unit="of 9", note="Two awaiting the board"),
            ui.figure("Documents issued", "1,284", delta="+96", direction="up"),
        ])
    ), heading="Separated by rules, not boxed in cards"))

    parts.append(ui.section("Data", (
        '<p class="ed-lede" style="font-size:var(--text-sm);margin-block-end:var(--space-4)">'
        "Each table declares what kind of data it holds, and its small-screen "
        "composition follows from that. Narrow this window to see four different "
        "answers.</p>"
        + ui.data_table(
            [("Course", "text"), ("Detail", "text"), ("Grade", "num"), ("Note", "text")],
            [],
            shape="matrix",
            empty_state="".join([
                "<table class='ed-table ed-data' data-shape='matrix'>"
                "<thead><tr><th>Course</th><th>Assessment</th><th class='num'>Grade</th>"
                "<th>Note</th></tr></thead><tbody>",
                ui.matrix_row(subject="Chemistry", grade="A",
                              details=[("Mark", "82 / 100"), ("Assessment", "Examination")],
                              note="Practical write-ups are the strongest in the set."),
                ui.matrix_row(subject="History", grade="B",
                              details=[("Mark", "64 / 100"), ("Assessment", "Examination")]),
                ui.matrix_row(subject="Mathematics", grade="A",
                              details=[("Mark", "78 / 100"), ("Assessment", "Coursework")]),
                "</tbody></table>",
            ]),
        )
        + '<div style="margin-block-start:var(--space-6)">'
        + ui.data_table(
            [("Year", "text"), ("Programme", "text"), ("From", "text"),
             ("To", "text"), ("Outcome", "text")],
            [
                ("2026/27", "BSc Computer Science", "21 Sep 2026", "—", ui.badge("Active", tone="success")),
                ("2025/26", "Foundation Year", "22 Sep 2025", "12 Jun 2026", ui.badge("Progressed", tone="neutral")),
            ],
            shape="ledger",
        )
        + "</div>"
        + ui.pagination(page=1, pages=9, total=412)
    ), heading="Four data shapes, four small-screen answers"))

    parts.append(ui.section("Waiting and nothing", (
        '<div class="ed-grid ed-grid--2">'
        + ui.panel(ui.skeleton(lines=4) + '<p class="ed-label" '
                   'style="margin-block-start:var(--space-4)">Loading</p>')
        + ui.panel(ui.empty(
            "No programmes yet",
            "A programme is what a student is admitted to — a degree, a diploma, "
            "a curriculum. Create one and levels can sit inside it.",
            action=ui.button("Create a programme", variant="primary", size="sm"),
        ), quiet=True)
        + "</div>"
        + '<div style="margin-block-start:var(--space-5);max-width:24rem">'
        + ui.progress(68, label="Importing 412 students")
        + "</div>"
    ), heading="An empty state says what a place is for"))

    parts.append(ui.section("Accessibility", (
        '<p class="ed-lede" style="font-size:var(--text-sm);margin-block-end:var(--space-4)">'
        "Every pairing that decides whether a parent can read a grade on a phone, "
        "checked against WCAG 2.2. An institution changing its colours is judged "
        "by the same eleven and told what to do about a failure — not silently "
        "corrected.</p>"
        + guardrails()
    ), heading=review(resolve()).summary()))

    parts.append("</div>")
    return document(theme=theme, body="".join(parts), title="EdirasX — Design System",
                    extra_css=EXTRA, font_base="fonts")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "styleguide.html"
    target.write_text(build(), encoding="utf-8")
    print(f"{target}  {target.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
