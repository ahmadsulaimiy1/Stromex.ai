"""Flagship F — the institutional rule, developed, and built on flow.

Two things are being fixed here at once, and the first is the reason the second
is possible.

**The composition is a flow, not a set of offsets.** Every prototype pinned its
zones at fixed millimetre offsets from a single anchor, so a recipient name that
wrapped to two lines drove the Arabic, the degree and the field of study into
one another — in five of the six. The fix is structural rather than
arithmetical: the field is one flex column, bands are its children, and the
space between them is `gap` and two flexible spacers. Overlap is not avoided
here; it is *unrepresentable*. A name that takes three lines pushes what follows
down, and the spacers absorb the difference.

That also removes the temptation the brief warns about. There is no global
shrink-to-fit: the recipient is sized within a stated safe range and is allowed
to wrap, because a doctoral candidate's name should not become small because
their institution has a long one.

**And F is developed rather than merely rendered.** Its authority comes from
proportion and alignment, so this pass is about the left axis being exact, the
rules doing architectural work, the seal acting as a counterweight rather than
sitting somewhere, and the Arabic participating in the hierarchy instead of
trailing beneath it. No decoration has been added. The empty space is the
composition.
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

#: The recipient's size range. Within it the name is fitted to its own length;
#: outside it the name wraps and the flow absorbs it. Never below the floor —
#: the peak stays the peak.
NAME_MAX, NAME_MIN = 12.4, 8.2


def _mm(v: float) -> str:
    return f"{v:.2f}mm"


def _legend(name: str, limit: int = 30) -> str:
    """Truncate a seal legend on a word boundary. The first render read
    "MERIDIAN INSTITUTE FOR ADVANCE", which is a typo the institution did not
    make."""
    if len(name) <= limit:
        return name
    cut = name[:limit].rsplit(" ", 1)[0]
    return cut or name[:limit]


def _fit(text: str, measure: float, *, cap: float, floor: float,
         per_char: float = 1.63) -> float:
    """A size for one line of display type in a known measure.

    Deliberately *not* a shrink-to-fit: it returns a size inside a stated range
    and lets long content wrap, because the alternative — reducing the peak
    until the longest possible name fits on one line — makes every ordinary
    name look timid to protect an extraordinary one.
    """
    return max(floor, min(cap, measure / max(len(text), 1) * per_char))


def flagship_f(
    *,
    institution: str,
    institution_ar: str,
    conferral: str,
    recipient: str,
    recipient_ar: str,
    qualification: str,
    field_of_study: str,
    statement: str,
    signatures: tuple[tuple[str, str], ...],
    serial: str,
    code: str,
    issued: str,
    distinction: str = "",
    seal: bool = True,
    sheet_key: str = "a4-landscape",
    label: str = "",
) -> str:
    sheet = SHEETS[sheet_key]
    # Level I's budget: F earns its authority without an enclosing frame, so the
    # plate contributes the substrate and nothing else. This is the composition
    # the contact sheet said was strongest, and adding registers to it because
    # "it is a doctorate" would be exactly the mistake.
    # `frameless` because F's authority comes from the two rules and the
    # margin. The Level I plate draws one engraved register, and on the first
    # render it appeared as a gold rectangle sitting inside them — a frame F
    # had specifically been chosen for not having.
    plate = build(sheet=sheet, budget=budget_for(1), ink=INK, gold=GOLD,
                  serial=serial, institution=institution, frameless=True)
    s = sheet
    margin = s.width * 0.088          # the widest measure on the sheet
    top, bottom = s.height * 0.093, s.height * 0.093
    w = s.width - margin * 2
    name_size = _fit(recipient, w * 0.94, cap=NAME_MAX, floor=NAME_MIN)
    paper = geo.tint("#FFFFFF", 0.30)

    sig_cells = "".join(
        f'<div class="sig">'
        f'<div class="d nm">{name}</div>'
        f'<div class="sigrule"></div>'
        f'<div class="label office">{office}</div></div>'
        for name, office in signatures
    )
    seal_svg = ""
    if seal:
        r = 17.0
        seal_svg = (
            f'<div class="sealbox"><svg width="{_mm(r * 2)}" height="{_mm(r * 2)}" '
            f'viewBox="0 0 {r * 2:.2f} {r * 2:.2f}">'
            + geo.seal_ring(r, r, r * 0.80, ink=INK,
                            legend=_legend(institution), identifier=serial)
            + "</svg></div>"
        )

    css = f"""
@page {{ size: {s.width}mm {s.height}mm; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #DED8CA;
  font-family: 'EdirasX Sans', system-ui, sans-serif; }}
.wrap {{ padding: 6mm; }}
.tag {{ font-size: 3.2mm; letter-spacing: 0.18em; text-transform: uppercase;
  color: #4B5361; margin: 0 0 3mm 2mm; font-weight: 600; }}
.sheet {{ position: relative; width: {s.width}mm; height: {s.height}mm;
  background: {paper}; box-shadow: 0 2mm 7mm rgba(10,16,28,0.20);
  overflow: hidden; }}
.plate {{ position: absolute; inset: 0; }}
.plate svg {{ display: block; width: 100%; height: 100%; }}

/* The composition: one flex column. Every band is a child; the two spacers
   absorb whatever the content does not use. There is no fixed offset anywhere
   below this line, which is the whole point. */
.field {{ position: absolute; left: {_mm(margin)}; right: {_mm(margin)};
  top: {_mm(top)}; bottom: {_mm(bottom)};
  display: flex; flex-direction: column; }}
.spacer {{ flex: 1 1 auto; min-height: 4mm; }}
.spacer--wide {{ flex: 1.45 1 auto; }}

.d {{ font-family: 'EdirasX Display', Georgia, serif; color: {INK}; }}
.ar {{ font-family: 'EdirasX Arabic', serif; direction: rtl; }}
.m {{ font-family: 'EdirasX Mono', monospace; color: {geo.tint(INK, 0.52)}; }}
.label {{ text-transform: uppercase; font-weight: 600;
  color: {geo.tint(INK, 0.58)}; }}

/* The two architectural rules. Full measure, and the only two on the sheet —
   which is what lets them carry the whole frame's job. */
.rule-top {{ height: 0.65mm; background: {INK}; flex: none; }}
.rule-foot {{ height: 0.65mm; background: {INK}; flex: none; }}

/* Masthead: mark, institution, Arabic. One row, baseline-aligned, on the same
   left axis as everything beneath it. */
.masthead {{ display: flex; align-items: baseline; gap: 5mm;
  padding-block: 5.5mm 0; flex: none; }}
.mark {{ flex: none; width: 9mm; height: 9mm; align-self: center; }}
.masthead .en {{ font-size: 5.0mm; letter-spacing: 0.085em; line-height: 1.15; }}
.masthead .ar {{ font-size: 5.2mm; margin-left: auto; text-align: right;
  color: {geo.tint(INK, 0.90)}; }}

.conferral {{ font-size: 2.7mm; letter-spacing: 0.40em; flex: none; }}

/* The peak. Allowed to wrap; the flow takes care of what follows. */
.name {{ font-size: {_mm(name_size)}; font-weight: 600; line-height: 1.03;
  letter-spacing: -0.005em; margin-top: 3.2mm; flex: none;
  max-width: 96%; }}
.name-ar {{ font-size: {_mm(name_size * 0.46)}; margin-top: 2.6mm;
  color: {geo.tint(INK, 0.88)}; flex: none; line-height: 1.45; }}

/* A short rule at the left axis: the hinge between identity and award. It is
   28% of the measure, which is the same proportion as the mark's offset — the
   alignment is the ornament. */
.hinge {{ width: 28%; height: 0.32mm; background: {geo.tint(GOLD, 0.95)};
  margin-top: 7.5mm; flex: none; }}

.degree {{ font-size: 7.6mm; letter-spacing: 0.135em; text-transform: uppercase;
  margin-top: 5.0mm; line-height: 1.12; flex: none; }}
.study {{ font-size: 4.6mm; font-style: italic; margin-top: 2.2mm;
  color: {geo.tint(INK, 0.86)}; flex: none; max-width: 78%; line-height: 1.3; }}
.degree-ar {{ font-size: 4.6mm; margin-top: 2.4mm; flex: none;
  color: {geo.tint(INK, 0.86)}; }}
.distinction {{ font-size: 2.6mm; letter-spacing: 0.30em; margin-top: 4.0mm;
  color: #5C1A2B; flex: none; }}

.statement {{ font-size: 3.3mm; line-height: 1.72; max-width: 56%;
  color: {geo.tint(INK, 0.80)}; margin-top: 6.0mm; flex: none; }}

/* Execution: signatures on the left axis, seal as the right counterweight.
   One row, bottom-aligned, so a third signatory changes the row and not the
   composition. */
.execution {{ display: flex; align-items: flex-end; gap: 9mm;
  padding-bottom: 5.0mm; flex: none; }}
.sig {{ flex: 0 0 {_mm(w * 0.235)}; }}
.sig .nm {{ font-size: 4.2mm; padding-bottom: 1.4mm; }}
.sigrule {{ height: 0.22mm; background: {geo.tint(INK, 0.75)}; }}
.office {{ font-size: 2.2mm; letter-spacing: 0.28em; margin-top: 1.5mm; }}
.sealbox {{ margin-left: auto; flex: none; }}

.foot {{ display: flex; justify-content: space-between; padding-top: 2.4mm;
  flex: none; font-size: 2.4mm; }}
"""

    body = f"""
<div class="field">
  <div class="rule-top"></div>
  <div class="masthead">
    <div class="mark"><svg width="100%" height="100%" viewBox="0 0 9 9">
      {geo.khatam(4.5, 4.5, 4.1, ink=GOLD, width=0.38)}</svg></div>
    <div class="d en">{institution}</div>
    <div class="ar">{institution_ar}</div>
  </div>
  <div class="spacer spacer--wide"></div>
  <div class="label conferral">{conferral}</div>
  <div class="d name">{recipient}</div>
  {f'<div class="ar name-ar">{recipient_ar}</div>' if recipient_ar else ''}
  <div class="hinge"></div>
  <div class="d degree">{qualification}</div>
  {f'<div class="d study">{field_of_study}</div>' if field_of_study else ''}
  {f'<div class="label distinction">{distinction}</div>' if distinction else ''}
  <div class="d statement">{statement}</div>
  <div class="spacer"></div>
  <div class="execution">
    {sig_cells}
    {seal_svg}
  </div>
  <div class="rule-foot"></div>
  <div class="foot">
    <div class="m">{serial} &nbsp;·&nbsp; {issued}</div>
    <div class="m">VERIFY &nbsp;{code}</div>
  </div>
</div>
"""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{institution} — {qualification}</title><style>"
        + font_face_css(embed=True) + css + "</style></head><body>"
        '<div class="wrap">'
        + (f'<p class="tag">{label}</p>' if label else "")
        + f'<div class="sheet"><div class="plate">{plate.svg}</div>{body}</div>'
        + "</div></body></html>"
    )


BASE = dict(
    institution="Meridian Institute for Advanced Study",
    institution_ar="معهد مريديان للدراسات العليا",
    conferral="The Senate of the Institute has conferred upon",
    recipient="Muhammad Abdulrahman Ibrahim Abdulwahid Al-Sulaimiy",
    recipient_ar="محمد عبد الرحمن إبراهيم عبد الواحد السليمي",
    qualification="Doctor of Philosophy",
    field_of_study="Educational Leadership and Institutional Development",
    statement=(
        "having pursued the prescribed programme of research, submitted a thesis "
        "examined and approved by the Board of Examiners, and satisfied the "
        "Senate in the oral examination held on the fourteenth day of March, "
        "two thousand and thirty-one."
    ),
    distinction="With the commendation of the Senate",
    signatures=(("Prof. Amina Yusuf", "Vice-Chancellor"),
                ("Mr K. Balogun", "Registrar")),
    serial="PHD/2031/0007",
    code="BFJ7-DRNM-8VZ9",
    issued="14 March 2031",
)

#: The hostile set. Each entry changes one thing that has broken a certificate
#: composition somewhere in the world.
VARIANTS: dict[str, dict] = {
    "f1-hostile-baseline": dict(label="F · hostile baseline"),
    "f2-short-name": dict(
        label="F · an ordinary name (the peak must not look timid)",
        recipient="Ada Nwosu", recipient_ar="آدا نوسو",
    ),
    "f3-long-institution": dict(
        label="F · long institution, three signatories",
        institution="The Meridian Institute for Advanced Study and Research",
        institution_ar="معهد مريديان للدراسات العليا والبحث العلمي",
        signatures=(("Prof. Amina Yusuf", "Vice-Chancellor"),
                    ("Dr Tomas Reinholt", "Dean of the Graduate School"),
                    ("Mr K. Balogun", "Registrar")),
    ),
    "f4-minimal": dict(
        label="F · no Arabic, no distinction, no seal, one signatory",
        recipient_ar="", distinction="", seal=False,
        signatures=(("Mr K. Balogun", "Registrar"),),
        field_of_study="",
        statement=("having satisfied the requirements of the Institute for the "
                   "degree named above."),
    ),
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, overrides in VARIANTS.items():
        html = flagship_f(**{**BASE, **overrides})
        target = OUT / f"{name}.html"
        target.write_text(html, encoding="utf-8")
        print(f"{target.name}  {target.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
