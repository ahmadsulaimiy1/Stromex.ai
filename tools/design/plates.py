"""Render flagship certificate compositions for inspection.

Not a test. This exists so a plate can be opened, printed, and argued about —
which is the only review that catches the things a test cannot see.

The data is deliberately hostile. The longest names, the longest qualification
titles, and the longest institution names that occur in real academic life, so
that a composition which survives them survives everything shorter. Shortening
the data to protect the design is how a design ships and then breaks on its
first real graduate.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))
OUT = ROOT / "docs" / "edtechx" / "design" / "plates"

from app.modules.design import geometry as geo  # noqa: E402
from app.modules.design.ceremony import budget_for  # noqa: E402
from app.modules.design.typeface import font_face_css  # noqa: E402
from app.modules.documents.plate import SHEETS, build  # noqa: E402

INK = "#0A101C"
GOLD = "#B08D57"
GARNET = "#5C1A2B"


def _css(plate) -> str:
    """Type set in millimetres, because the sheet is."""
    return f"""
@page {{ size: {plate.sheet.width}mm {plate.sheet.height}mm; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #E8E2D5; }}
.sheet {{
  position: relative; width: {plate.sheet.width}mm; height: {plate.sheet.height}mm;
  margin: 8mm auto; background: {geo.tint("#FFFFFF", 0.30)};
  box-shadow: 0 2mm 8mm rgba(10,16,28,0.18);
  overflow: hidden;
}}
.plate {{ position: absolute; inset: 0; }}
.plate svg {{ display: block; width: 100%; height: 100%; }}
.zone {{ position: absolute; text-align: center; }}
.label {{
  font-family: 'EdirasX Sans', system-ui, sans-serif;
  text-transform: uppercase; color: {geo.tint(INK, 0.62)};
  font-weight: 600;
}}
.display {{ font-family: 'EdirasX Display', Georgia, serif; color: {INK}; }}
.serif {{ font-family: 'EdirasX Display', Georgia, serif; color: {INK}; }}
.mono {{ font-family: 'EdirasX Mono', monospace; }}
.arabic {{ font-family: 'EdirasX Arabic', serif; direction: rtl; }}
.rule {{ position: absolute; background: {geo.tint(GOLD, 0.9)}; }}
"""


def _mm(value: float) -> str:
    return f"{value:.2f}mm"


def certificate(
    *,
    sheet_key: str,
    level: int,
    institution: str,
    institution_ar: str,
    conferral: str,
    recipient: str,
    recipient_ar: str,
    qualification: str,
    statement: str,
    distinction: str = "",
    signatures: tuple[tuple[str, str], ...] = (),
    serial: str = "",
    code: str = "",
    issued: str = "",
) -> str:
    sheet = SHEETS[sheet_key]
    budget = budget_for(level)
    plate = build(sheet=sheet, budget=budget, ink=INK, gold=GOLD,
                  serial=serial, institution=institution)
    f = plate.field
    # The field is composed as bands, not as offsets from one point. The first
    # render positioned every zone by arithmetic from the optical centre, and
    # the result was a horizontal strip of content through the middle of the
    # sheet with two dead bands above and below it. A composition distributes.
    peak_y = f.y + f.h * 0.395

    # --- the type scale, derived from the sheet rather than chosen ---
    # The peak is sized to the field's width so a long name and a short one
    # occupy the same measure; every other size steps down from it by the
    # level's own ratio, which is what makes the hierarchy a rule instead of a
    # sequence of decisions.
    peak = min(f.w / max(len(recipient), 22) * 1.62, f.h * 0.115)
    second = peak / budget.peak_ratio
    body = min(second * 0.62, 4.4)
    micro = body * 0.62

    parts: list[str] = []

    def zone(top: float, html: str, *, left: float | None = None,
             width: float | None = None, align: str = "center") -> None:
        x = f.x if left is None else left
        w = f.w if width is None else width
        parts.append(
            f'<div class="zone" style="left:{_mm(x)};top:{_mm(top)};'
            f'width:{_mm(w)};text-align:{align}">{html}</div>'
        )

    # --- AUTHORITY -----------------------------------------------------------
    # The institution, once, at the top, and never broken across lines.
    zone(f.y + 2, (
        f'<div class="display" style="font-size:{_mm(body * 1.5)};'
        f'letter-spacing:{_mm(body * 0.10)};line-height:1.1;'
        f'white-space:nowrap">{institution}</div>'
        + (f'<div class="arabic" style="font-size:{_mm(body * 1.35)};'
           f'margin-top:{_mm(body * 0.5)};color:{geo.tint(INK, 0.8)}">'
           f'{institution_ar}</div>' if institution_ar else "")
    ))

    # A hairline under the authority block: the one place a rule is doing
    # structural work rather than decorating.
    rule_y = f.y + body * 5.4
    parts.append(
        f'<div class="rule" style="left:{_mm(f.cx - f.w * 0.20)};'
        f'top:{_mm(rule_y)};width:{_mm(f.w * 0.40)};height:0.25mm"></div>'
    )
    parts.append(
        f'<div class="zone" style="left:{_mm(f.cx - 3)};top:{_mm(rule_y - 2.6)};'
        f'width:6mm">{geo.khatam(3, 3, 2.4, ink=GOLD, width=0.35)}</div>'
        .replace("<path", '<svg width="6mm" height="6mm" viewBox="0 0 6 6"><path')
        .replace("</div>", "</svg></div>")
    )

    # --- CONFERRAL -----------------------------------------------------------
    zone(peak_y - peak * 0.95, (
        f'<div class="label" style="font-size:{_mm(micro * 1.15)};'
        f'letter-spacing:{_mm(micro * 0.42)}">{conferral}</div>'
    ))

    # --- RECIPIENT: the one visual peak --------------------------------------
    zone(peak_y - peak * 0.36, (
        f'<div class="display" style="font-size:{_mm(peak)};line-height:1.05;'
        f'letter-spacing:{_mm(peak * 0.008)};font-weight:600">{recipient}</div>'
        + (f'<div class="arabic" style="font-size:{_mm(peak * 0.52)};'
           f'margin-top:{_mm(peak * 0.16)};color:{geo.tint(INK, 0.88)}">'
           f'{recipient_ar}</div>' if recipient_ar else "")
    ))

    # A serial microtext rule beneath the name — the one security element in
    # the ceremonial field, and it is a rule, which the composition wanted
    # anyway.
    # Below the Arabic, not through it. The first render drew this rule across
    # the Arabic descenders.
    name_rule_y = peak_y + peak * (1.28 if recipient_ar else 0.78)
    parts.append(
        f'<div class="rule" style="left:{_mm(f.cx - f.w * 0.28)};'
        f'top:{_mm(name_rule_y)};width:{_mm(f.w * 0.56)};height:0.2mm;'
        f'background:{geo.tint(INK, 0.45)}"></div>'
    )

    # --- QUALIFICATION -------------------------------------------------------
    zone(name_rule_y + body * 1.9, (
        f'<div class="serif" style="font-size:{_mm(second)};line-height:1.22;'
        f'font-style:italic">{qualification}</div>'
        + (f'<div class="label" style="font-size:{_mm(micro * 1.05)};'
           f'letter-spacing:{_mm(micro * 0.36)};margin-top:{_mm(body * 1.7)};'
           f'color:{GARNET}">{distinction}</div>' if distinction else "")
    ), left=f.x + f.w * 0.10, width=f.w * 0.80)

    # --- STATEMENT -----------------------------------------------------------
    statement_y = name_rule_y + body * (7.4 if distinction else 6.0)
    zone(statement_y, (
        f'<div class="serif" style="font-size:{_mm(body)};line-height:1.55;'
        f'color:{geo.tint(INK, 0.86)}">{statement}</div>'
    ), left=f.x + f.w * 0.17, width=f.w * 0.66)

    # --- EXECUTION -----------------------------------------------------------
    # Seal centred between the signatories: the institution presiding over its
    # own officers, which is the canonical arrangement and also the only one
    # that stays balanced when there are two signatures or four.
    exec_y = f.y + f.h - body * 8.4
    seal_r = min(f.w * 0.078, 19.0)
    if "seal" in budget.permits:
        parts.append(
            f'<div class="zone" style="left:{_mm(f.cx - seal_r)};'
            f'top:{_mm(exec_y - seal_r * 0.62)};width:{_mm(seal_r * 2)}">'
            f'<svg width="{_mm(seal_r * 2)}" height="{_mm(seal_r * 2)}" '
            f'viewBox="0 0 {seal_r * 2:.2f} {seal_r * 2:.2f}">'
            + geo.rosette(seal_r, seal_r, seal_r * 0.94, ink=INK, width=0.08,
                          strength=0.16, passes=2)
            + geo.seal_ring(seal_r, seal_r, seal_r * 0.82, ink=INK,
                            legend=institution.upper()[:28], identifier=serial)
            + "</svg></div>"
        )

    span = f.w * 0.30
    for index, (name, title) in enumerate(signatures[:2]):
        left = f.x + (f.w * 0.04 if index == 0 else f.w - f.w * 0.04 - span)
        parts.append(
            f'<div class="zone" style="left:{_mm(left)};top:{_mm(exec_y)};'
            f'width:{_mm(span)}">'
            f'<div class="serif" style="font-size:{_mm(body * 1.45)};'
            f'padding-bottom:{_mm(body * 0.55)}">{name}</div>'
            f'<div style="height:0.25mm;background:{geo.tint(INK, 0.78)}"></div>'
            f'<div class="label" style="font-size:{_mm(micro)};'
            f'letter-spacing:{_mm(micro * 0.34)};margin-top:{_mm(body * 0.5)}">'
            f'{title}</div></div>'
        )

    # --- IDENTITY and VERIFICATION: the sanctioned asymmetry -----------------
    foot_y = f.y + f.h - body * 1.5
    parts.append(
        f'<div class="zone mono" style="left:{_mm(f.x)};top:{_mm(foot_y)};'
        f'width:{_mm(f.w * 0.46)};text-align:left;font-size:{_mm(micro)};'
        f'color:{geo.tint(INK, 0.55)};letter-spacing:0.02em">'
        f'{serial} &nbsp;·&nbsp; {issued}</div>'
    )
    parts.append(
        f'<div class="zone mono" style="left:{_mm(f.x + f.w * 0.54)};'
        f'top:{_mm(foot_y)};width:{_mm(f.w * 0.46)};text-align:right;'
        f'font-size:{_mm(micro)};color:{geo.tint(INK, 0.55)};'
        f'letter-spacing:0.02em">VERIFY &nbsp;{code}</div>'
    )

    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{institution} — {qualification}</title><style>"
        + font_face_css(embed=True)
        + _css(plate)
        + "</style></head><body>"
        + f'<div class="sheet"><div class="plate">{plate.svg}</div>'
        + "".join(parts)
        + "</div></body></html>"
    )


DOCTORATE = dict(
    sheet_key="a4-landscape",
    level=4,
    institution="Meridian Institute for Advanced Study",
    institution_ar="معهد مريديان للدراسات العليا",
    conferral="The Senate of the Institute has conferred upon",
    recipient="Muhammad Abdulrahman Ibrahim Abdulwahid Al-Sulaimiy",
    recipient_ar="محمد عبد الرحمن إبراهيم عبد الواحد السليمي",
    qualification=(
        "Doctor of Philosophy in Educational Leadership "
        "and Institutional Development"
    ),
    statement=(
        "having pursued the prescribed programme of research, submitted a thesis "
        "examined and approved by the Board of Examiners, and satisfied the Senate "
        "in the oral examination held on the fourteenth day of March, two thousand "
        "and thirty-one."
    ),
    distinction="Awarded with the commendation of the Senate",
    signatures=(
        ("Prof. Amina Yusuf", "Vice-Chancellor"),
        ("Mr K. Balogun", "Registrar"),
    ),
    serial="PHD/2031/0007",
    code="BFJ7-DRNM-8VZ9",
    issued="14 March 2031",
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pages = {"01-doctorate-flagship": certificate(**DOCTORATE)}
    for name, html in pages.items():
        target = OUT / f"{name}.html"
        target.write_text(html, encoding="utf-8")
        print(f"{target.name}  {target.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
