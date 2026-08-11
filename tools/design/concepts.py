"""Twelve luxury directions for a doctoral plate — one design philosophy each.

This is a design review board, not a template set. Every concept below takes the
same hostile candidate record and answers a different question about what a
ceremonial academic document *is*: a palace door, a page from an illuminated
manuscript, a banknote, a struck medal, a sovereign university's warrant.

Three rules govern the set, and they are the reason it is twelve rather than one
with twelve palettes.

**No concept may differ from another only in colour.** Each owns its ground, its
frame architecture, its central composition, its typographic pairing, its metal,
and the job it gives Arabic. If two of them could be produced from each other by
changing hex values, one of them is not a concept.

**The composition is a flow.** Every field is a flex column whose bands are its
children and whose spacers absorb the difference, so a name that wraps to three
lines pushes what follows down instead of landing on top of it. There is no
fixed millimetre offset in any layout here — that defect was found by hostile
data in a previous round and it is not being reintroduced.

**Richness is not licence.** A dense plate has more ways to lose its hierarchy
than a sparse one, so the peak — the recipient's name — is the largest single
element on every sheet, the verification band is the quietest register on every
sheet, and no ornament crosses the words. What varies is how much is on the
page; what does not vary is that the eye lands in one place first.

What is drawn here is vector geometry in millimetres, and what is *simulated* —
foil, emboss, raised type — is named as simulation in `gilding.SIMULATION` and
carried into the production specification rather than left to look like a claim.
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass
from dataclasses import field as dc_field

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))
OUT = ROOT / "docs" / "edtechx" / "design" / "concepts"

from app.modules.design import architecture as arch  # noqa: E402
from app.modules.design import geometry as geo  # noqa: E402
from app.modules.design.gilding import (  # noqa: E402
    METALS,
    Metal,
    emboss,
    engraved_metal_rule,
    foil_gradient,
)
from app.modules.design.typeface import font_face_css  # noqa: E402

SHEET_W, SHEET_H = 297.0, 210.0

# --- the hostile record ------------------------------------------------------
# One long institution name, one very long recipient name in two scripts, a long
# qualification, three signatories, a seal, a distinction and a verification
# block. Every concept is judged on this and only this.

INSTITUTION = "The Meridian Institute for Advanced Study and Research"
INSTITUTION_AR = "معهد مريديان للدراسات العليا والبحث العلمي"
RECIPIENT = "Muhammad Abdulrahman Ibrahim Abdulwahid Al-Sulaimiy"
RECIPIENT_AR = "محمد عبد الرحمن إبراهيم عبد الواحد السليمي"
DEGREE = "Doctor of Philosophy"
DEGREE_AR = "درجة الدكتوراه في الفلسفة"
STUDY = "Educational Leadership and Institutional Development"
STUDY_AR = "القيادة التربوية والتطوير المؤسسي"
CONFERRAL = "The Senate of the Institute has conferred upon"
STATEMENT = (
    "having pursued the prescribed programme of research, submitted a thesis "
    "examined and approved by the Board of Examiners, and satisfied the Senate "
    "in the oral examination held on the fourteenth day of March, two thousand "
    "and thirty-one."
)
DISTINCTION = "With the commendation of the Senate"
SIGNATURES = (
    ("Prof. Amina Yusuf", "Vice-Chancellor", "Presiding authority of the Senate"),
    ("Dr Tomas Reinholt", "Dean of the Graduate School", "Board of Examiners"),
    ("Mr K. Balogun", "Registrar", "Custodian of the record"),
)
SEAL_LEGEND = "MERIDIAN INSTITUTE"
SERIAL = "PHD/2031/0007"
CODE = "BFJ7-DRNM-8VZ9"
ISSUED = "14 March 2031"


@dataclass(frozen=True, slots=True)
class Palette:
    """A concept's structural colours.

    Three and only three carry structure — a ground, an ink and one accent —
    plus the metals. That discipline is inherited and it survives the move to
    royal maximalism unchanged: what makes a rich plate look cheap is rarely the
    amount of ornament, it is the fourth colour.
    """

    ground: str
    ink: str
    accent: str
    metal: str
    metal2: str = ""
    #: The paper the tints are mixed against, when it is not the default ivory.
    paper: str = "#F7F2E6"

    @property
    def m(self) -> Metal:
        return METALS[self.metal]

    @property
    def m2(self) -> Metal:
        return METALS[self.metal2 or self.metal]


@dataclass(frozen=True, slots=True)
class Concept:
    key: str
    name: str
    #: One sentence a person could disagree with. If two concepts could share
    #: this sentence, they are not two concepts.
    philosophy: str
    palette: Palette
    display: str
    arabic: str
    #: What Arabic is doing here — not decoration, a stated role.
    arabic_role: str
    build: object = dc_field(repr=False, default=None)


def mm(v: float) -> str:
    return f"{v:.2f}mm"


# --- shared shell ------------------------------------------------------------


def svg(layers: str, defs: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SHEET_W:g} {SHEET_H:g}"'
        f' width="{SHEET_W:g}mm" height="{SHEET_H:g}mm" preserveAspectRatio="none"'
        ' aria-hidden="true" focusable="false">'
        + (f"<defs>{defs}</defs>" if defs else "")
        + layers
        + "</svg>"
    )


def page(concept: Concept, plate: str, body: str, css: str) -> str:
    """The document shell every concept shares — and nothing else."""
    p = concept.palette
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{concept.name} — {DEGREE}</title><style>"
        + font_face_css(embed=True)
        + f"""
@page {{ size: {SHEET_W}mm {SHEET_H}mm; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #2A2622; }}
.wrap {{ padding: 7mm; }}
.tag {{ font-family: 'Inter', sans-serif; font-size: 3.0mm; letter-spacing: 0.16em;
  text-transform: uppercase; color: #B7AE9E; margin: 0 0 3mm 1mm; font-weight: 600; }}
.tag b {{ color: #F2E9D8; font-weight: 700; }}
.sheet {{ position: relative; width: {SHEET_W}mm; height: {SHEET_H}mm;
  background: {p.ground}; overflow: hidden;
  box-shadow: 0 3mm 10mm rgba(0,0,0,0.42); }}
.plate {{ position: absolute; inset: 0; }}
.plate svg {{ display: block; width: 100%; height: 100%; }}
.field {{ position: absolute; display: flex; flex-direction: column; }}
.spacer {{ flex: 1 1 auto; min-height: 3mm; }}
.ar {{ font-family: '{concept.arabic}', serif; direction: rtl; }}
.mono {{ font-family: 'IBM Plex Mono', monospace; }}
.ui {{ font-family: 'Inter', sans-serif; }}
.disp {{ font-family: '{concept.display}', Georgia, serif; }}
.lab {{ font-family: 'Inter', sans-serif; text-transform: uppercase;
  font-weight: 600; }}
.sig {{ flex: 1 1 0; text-align: center; }}
.sig .nm {{ font-size: 3.9mm; padding-bottom: 1.2mm; white-space: nowrap; }}
.sig .of {{ font-size: 2.05mm; letter-spacing: 0.22em; margin-top: 1.3mm; }}
.sig .auth {{ color: {geo.tint(p.ink, 0.50)}; }}
.name, .name-ar {{ text-wrap: balance; }}
.verify {{ display: flex; justify-content: space-between; align-items: baseline;
  flex: none; font-size: 2.35mm; letter-spacing: 0.06em; }}
"""
        + css
        + "</style></head><body><div class=\"wrap\">"
        + f'<p class="tag"><b>{concept.key} · {concept.name}</b> — {concept.philosophy}</p>'
        + f'<div class="sheet"><div class="plate">{plate}</div>{body}</div>'
        + "</div></body></html>"
    )


def keep(text: str) -> str:
    """Stop a display line breaking at a hyphen inside a name.

    `Al-Sulaimiy` broke as `Al-` / `Sulaimiy` in eleven of the twelve first
    renders — on the peak element, which is the one place a bad break is not
    survivable. The fix is a non-breaking hyphen at *render* time: the stored
    name is untouched, and what changes is only what the line-breaker is told
    it may do. Nothing here rewrites a person's name.
    """
    return text.replace("-", "\u2011")


def execution(metal: Metal, ink: str, *, ground: str | None = None,
              side: str = "left", seal_r: float = 14.5,
              legend: str = SEAL_LEGEND) -> str:
    """The execution architecture: seal, signatures, offices, authorities.

    Not two lines on a form. Each signatory carries a name set in the display
    face, an engraved metal rule, the office in the label face at equal
    seriousness, and the authority under which that office signs — which is the
    thing that actually confers, and the thing a registrar in another country
    reads. The institutional seal is a struck medallion at the head of the row,
    blind-embossed rather than filled, so a physically embossed edition and this
    one read as the same document.
    """
    cells = "".join(
        f'<div class="sig"><div class="disp nm">{name}</div>'
        f'<svg class="srule" viewBox="0 0 60 1.6" preserveAspectRatio="none">'
        f'{engraved_metal_rule(1, 0.8, 59, 0.8, metal=metal, weight=0.34)}</svg>'
        f'<div class="lab of">{office}</div>'
        f'<div class="auth">{authority}</div></div>'
        for name, office, authority in SIGNATURES
    )
    seal = ""
    if side != "none":
        d = seal_r * 2 + 2
        seal = (
            f'<div class="sealbox"><svg viewBox="0 0 {d:.1f} {d:.1f}">'
            + arch.medallion(d / 2, d / 2, seal_r, metal=metal, ink=ink,
                             legend=legend, identifier=SERIAL)
            + "</svg></div>"
        )
    order = (seal + f'<div class="sigrow">{cells}</div>') if side == "left" \
        else (f'<div class="sigrow">{cells}</div>' + seal)
    return f'<div class="exec">{order}</div>'


def divider(metal: Metal, *, width: float = 46.0, stops: int = 4) -> str:
    """A spreader rule placed between two spacers — the ceremonial pause, given
    a reason to exist.

    The gap between the conferring statement and the execution row is the
    largest void on a ceremonial sheet and it is deliberate: it is the pause
    before the signatures. Left entirely blank it reads as a layout that ran out
    of content. A lozenge-stopped rule floating in the middle of it reads as
    what it is.

    In the flow, between two flexible spacers, so it stays centred in the void
    whatever the recipient's name does above it.
    """
    return (
        f'<svg class="divider" style="width:{width}%" viewBox="0 0 100 4"'
        ' preserveAspectRatio="none">'
        + arch.spreader(2.0, 1.0, 99.0, metal=metal, stops=stops)
        + "</svg>"
    )


EXEC_CSS = """
.divider { display: block; flex: none; height: 3mm; }
.exec { display: flex; align-items: flex-end; gap: 8mm; width: 100%; flex: none; }
.sigrow { flex: 1 1 auto; display: flex; align-items: flex-end; gap: 7mm; }
.sealbox { flex: none; width: 31mm; }
.sealbox svg { display: block; width: 100%; height: auto; }
.sig .srule { display: block; width: 100%; height: 1.6mm; }
.sig .auth { font-family: 'Source Serif 4', serif; font-size: 1.85mm;
  font-style: italic; margin-top: 0.7mm; }
"""


def verify_band(*, ink: str, label: str = "VERIFY") -> str:
    return (
        '<div class="verify">'
        f'<span class="mono">{SERIAL}</span>'
        f'<span class="lab" style="letter-spacing:0.30em;font-size:2.0mm">{ISSUED}</span>'
        f'<span class="mono">{label}&nbsp; {CODE}</span>'
        "</div>"
    )


def fit(text: str, measure: float, *, cap: float, floor: float,
        per_char: float = 1.62) -> float:
    """A display size inside a stated range — never a shrink-to-fit.

    Long content wraps and the flow absorbs it. Reducing the peak until the
    longest possible name fits on one line makes every ordinary name look timid
    in order to protect an extraordinary one.
    """
    return max(floor, min(cap, measure / max(len(text), 1) * per_char))


def substrate(p: Palette, *, fibre: bool = True, screen: bool = False) -> tuple[str, str]:
    """The security substrate every concept sits on. Returns `(defs, layers)`."""
    defs = layers = ""
    if screen:
        defs += geo.line_screen("anticopy", degrees=8, pitch=0.46, width=0.07,
                                ink=p.m.core, strength=0.18)
        layers += f'<rect x="0" y="0" width="{SHEET_W}" height="{SHEET_H}" fill="url(#anticopy)"/>'
    if fibre:
        layers += geo.fibres(geo.Rect(0, 0, SHEET_W, SHEET_H), seed=SERIAL, count=150)
    return defs, layers


# =============================================================================
# 01 — ROYAL PALACE
# =============================================================================


def c01(c: Concept) -> str:
    """Ivory ground, navy mass, royal gold. The frame is a palace doorcase: a
    heavy corner block at each angle, a stepped ceremonial architrave between
    them, and a crest breaking the top line."""
    p = c.palette
    m = p.m
    defs, layers = substrate(p, screen=True)
    defs += foil_gradient(m, "royal-foil", angle=18)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    stack, inner = arch.register_stack(
        sheet.inset(5.5),
        ((0.7, "rule"), (2.0, "void"), (4.4, "field"), (0.5, "rule"),
         (6.0, "micro"), (1.0, "void"), (0.45, "rule")),
        metal=m, ink=p.accent,
    )
    layers += stack
    # The ceremonial architrave: a stepped inner frame, not a rectangle.
    layers += (
        f'<path d="{arch.stepped_rect_path(inner.inset(2.6), cut=9.0, step=2.2)}"'
        f' fill="none" stroke="{m.face}" stroke-width="0.62"/>'
        f'<path d="{arch.stepped_rect_path(inner.inset(3.7), cut=8.2, step=2.0)}"'
        f' fill="none" stroke="{m.shadow}" stroke-width="0.20"/>'
    )
    for quadrant, (x, y) in enumerate((
        (5.5, 5.5), (SHEET_W - 5.5, 5.5),
        (SHEET_W - 5.5, SHEET_H - 5.5), (5.5, SHEET_H - 5.5),
    )):
        layers += arch.corner_block(x, y, 30.0, quadrant=quadrant,
                                    mass=geo.blend(p.ink, p.accent, 0.55), metal=m, ink=p.ink)
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.50, 62, ink=p.accent,
                           strength=0.025, rings=5)
    layers += arch.cresting(SHEET_W / 2, inner.y, 62, 13.0, metal=m)
    layers += arch.spreader(inner.y + 15.0, inner.x + 16, SHEET_W / 2 - 26, metal=m)
    layers += arch.spreader(inner.y + 15.0, SHEET_W / 2 + 26, inner.x + inner.w - 16, metal=m)
    layers += geo.microtext_ring(sheet.inset(8.4), identifier="c01",
                                 text=f"{INSTITUTION.upper()} · {SERIAL} · ",
                                 ink=p.ink, size=0.58, strength=0.26)

    name_size = fit(RECIPIENT, 196, cap=13.0, floor=8.6)
    css = EXEC_CSS + f"""
.field {{ left: 36mm; right: 36mm; top: 47mm; bottom: 39mm; align-items: center;
  text-align: center; }}
.inst {{ font-size: 5.0mm; letter-spacing: 0.16em; color: {p.accent};
  font-weight: 600; text-transform: uppercase; flex: none; }}
.inst-ar {{ font-size: 4.6mm; margin-top: 1.6mm; color: {geo.tint(p.accent, 0.80)};
  flex: none; }}
.conf {{ font-size: 2.6mm; letter-spacing: 0.38em; color: {geo.tint(p.ink, 0.62)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.06; font-weight: 900;
  color: {p.ink}; flex: none; margin-top: 2.6mm; max-width: 100%; }}
.name-ar {{ font-size: {mm(name_size * 0.44)}; margin-top: 2.2mm; flex: none;
  color: {geo.tint(p.accent, 0.92)}; line-height: 1.5; }}
.deg {{ font-size: 7.0mm; letter-spacing: 0.14em; text-transform: uppercase;
  color: {m.shadow}; flex: none; margin-top: 3.4mm; font-weight: 600; }}
.study {{ font-size: 4.2mm; font-style: italic; color: {geo.tint(p.ink, 0.84)};
  flex: none; margin-top: 1.8mm; }}
.dist {{ font-size: 2.4mm; letter-spacing: 0.28em; color: {p.accent};
  flex: none; margin-top: 2.6mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 3.1mm; line-height: 1.66;
  max-width: 74%; color: {geo.tint(p.ink, 0.80)}; flex: none; margin-top: 3.4mm; }}
.exec {{ margin-top: 4mm; }}
.sig .nm {{ color: {p.ink}; }}
.sig .of {{ color: {geo.tint(p.accent, 0.90)}; }}
.verify {{ width: 100%; margin-top: 3.4mm; color: {geo.tint(p.ink, 0.56)}; }}
"""
    body = f"""
<div class="field">
  <div class="disp inst">{INSTITUTION}</div>
  <div class="ar inst-ar">{INSTITUTION_AR}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="lab dist">{DISTINCTION}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 02 — IMPERIAL ISLAMIC
# =============================================================================


def c02(c: Concept) -> str:
    """A midnight geometric border of real strapwork, an ivory field with cut
    corners inside it, and Arabic as a peer band rather than a translation."""
    p = c.palette
    m, m2 = p.m, p.m2
    defs, layers = substrate(p)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    band = sheet.inset(6.0)
    layers += f'<rect {band.attrs()} fill="{p.accent}"/>'
    layers += arch.tessellation_field(band, cell=11.0, ink=m.face,
                                      strength=1.0, width=0.16, hollow=22.0)
    layers += arch.girih_band(band.inset(1.2), depth=6.0, metal=m2)
    layers += arch._perimeter_rule(band, metal=m, weight=0.55)
    inner = band.inset(22.0)
    layers += (
        f'<path d="{arch.stepped_rect_path(inner, cut=12.0)}" fill="{p.ground}"'
        f' stroke="{m.face}" stroke-width="0.70"/>'
        f'<path d="{arch.stepped_rect_path(inner.inset(1.5), cut=11.0)}"'
        f' fill="none" stroke="{m.shadow}" stroke-width="0.22"/>'
    )
    for quadrant, (x, y) in enumerate((
        (inner.x, inner.y), (inner.x + inner.w, inner.y),
        (inner.x + inner.w, inner.y + inner.h), (inner.x, inner.y + inner.h),
    )):
        layers += (
            f'<g transform="translate({x:.2f} {y:.2f}) rotate({quadrant * 90})">'
            + geo.khatam(0, 0, 7.0, ink=m.face, width=0.40)
            + geo.khatam(0, 0, 4.4, ink=m2.face, width=0.26)
            + f'<circle r="7.8" fill="none" stroke="{m.shadow}" stroke-width="0.18"/>'
            + "</g>"
        )
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.52, 54, ink=p.accent,
                           strength=0.025, rings=5)
    layers += geo.microtext_ring(sheet.inset(8.4), identifier="c02",
                                 text=f"{SERIAL} · {INSTITUTION.upper()} · ",
                                 ink=p.accent, size=0.58, strength=0.30)

    name_size = fit(RECIPIENT, 188, cap=12.4, floor=8.4)
    css = EXEC_CSS + f"""
.field {{ left: 47mm; right: 47mm; top: 38mm; bottom: 37mm; align-items: center;
  text-align: center; }}
.crown {{ display: flex; align-items: baseline; justify-content: space-between;
  width: 100%; flex: none; gap: 6mm; }}
.crown .ar {{ font-size: 4.7mm; font-weight: 700; color: {p.accent};
  white-space: nowrap; }}
.crown .en {{ font-size: 3.0mm; letter-spacing: 0.12em; text-transform: uppercase;
  color: {p.accent}; font-weight: 600; text-align: left; white-space: nowrap; }}
.conf {{ font-size: 2.5mm; letter-spacing: 0.36em; color: {geo.tint(p.ink, 0.60)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.06; font-weight: 700;
  color: {p.ink}; flex: none; margin-top: 2.4mm; }}
.name-ar {{ font-size: {mm(name_size * 0.46)}; margin-top: 2.0mm; flex: none;
  color: {p.accent}; line-height: 1.5; font-weight: 700; }}
.degwrap {{ display: flex; align-items: baseline; justify-content: center;
  gap: 5mm; flex: none; margin-top: 3.6mm; }}
.deg {{ font-size: 6.4mm; letter-spacing: 0.13em; text-transform: uppercase;
  color: {m.shadow}; font-weight: 600; }}
.deg-ar {{ font-size: 5.2mm; color: {m.shadow}; font-weight: 700; }}
.study {{ font-size: 4.0mm; font-style: italic; color: {geo.tint(p.ink, 0.84)};
  flex: none; margin-top: 1.6mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.95mm; line-height: 1.64;
  max-width: 78%; color: {geo.tint(p.ink, 0.78)}; flex: none; margin-top: 3.0mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm {{ color: {p.ink}; }}
.sig .of {{ color: {geo.tint(p.accent, 0.95)}; }}
.verify {{ width: 100%; margin-top: 3.0mm; color: {geo.tint(p.ink, 0.54)}; }}
"""
    body = f"""
<div class="field">
  <div class="crown">
    <div class="disp en">{INSTITUTION}</div>
    <div class="ar">{INSTITUTION_AR}</div>
  </div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="degwrap">
    <span class="disp deg">{DEGREE}</span>
    <span class="ar deg-ar">{DEGREE_AR}</span>
  </div>
  <div class="disp study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 03 — OTTOMAN ACADEMIC
# =============================================================================


def c03(c: Concept) -> str:
    """Burgundy and antique gold. An arabesque-and-medallion register, and the
    qualification mounted on a shaped cartouche — the Ottoman tuğra instinct:
    the important words are not written on the page, they are set into a plate."""
    p = c.palette
    m = p.m
    defs, layers = substrate(p)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    band = sheet.inset(6.5)
    layers += f'<rect {band.attrs()} fill="{p.accent}"/>'
    layers += f'<rect {band.inset(15.0).attrs()} fill="{p.ground}"/>'
    layers += arch.tessellation_field(band, cell=7.4, ink=m.highlight,
                                      strength=0.9, width=0.10, hollow=15.0)
    layers += arch._perimeter_rule(band, metal=m, weight=0.60)
    layers += arch._perimeter_rule(band.inset(15.0), metal=m, weight=0.50)
    layers += geo.arabesque_band(band.inset(7.5), ink=m.highlight, width=0.30,
                                 strength=1.0, period=13.0, depth=3.2)
    # Mid-edge medallions: the register acquires four events instead of running
    # blank for 280mm.
    for cx, cy in ((SHEET_W / 2, band.y + 7.5), (SHEET_W / 2, band.y + band.h - 7.5),
                   (band.x + 7.5, SHEET_H / 2), (band.x + band.w - 7.5, SHEET_H / 2)):
        layers += f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="6.6" fill="{p.accent}"/>'
        layers += arch.medallion(cx, cy, 6.0, metal=m, ink=p.ink)
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.54, 58, ink=p.accent,
                           strength=0.025, rings=5)

    name_size = fit(RECIPIENT, 182, cap=12.6, floor=8.4)
    # The plaque is drawn in its own box at its own size. The first render put
    # a 224-unit viewBox into a 152mm frame under `meet`, and the cartouche
    # shrank to a pill sitting across the middle of the qualification.
    cart = geo.Rect(3.0, 3.0, 158.0, 16.0)
    cartouche = (
        '<svg class="cart" viewBox="0 0 164 22" preserveAspectRatio="none">'
        f'<path d="{arch.cartouche_path(cart, arch=3.4, cut=6.0)}"'
        f' fill="{p.accent}" stroke="{m.face}" stroke-width="0.55"/>'
        f'<path d="{arch.cartouche_path(cart.inset(1.6), arch=3.0, cut=5.2)}"'
        f' fill="none" stroke="{m.highlight}" stroke-width="0.18"/>'
        "</svg>"
    )
    css = EXEC_CSS + f"""
.field {{ left: 42mm; right: 42mm; top: 32mm; bottom: 27mm; align-items: center;
  text-align: center; }}
.inst {{ font-size: 4.6mm; letter-spacing: 0.20em; color: {p.accent};
  text-transform: uppercase; font-weight: 600; flex: none; }}
.inst-ar {{ font-size: 4.2mm; margin-top: 1.4mm; color: {geo.tint(p.accent, 0.78)};
  flex: none; }}
.conf {{ font-size: 2.5mm; letter-spacing: 0.36em; color: {geo.tint(p.ink, 0.58)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.05; font-weight: 600;
  color: {p.ink}; flex: none; margin-top: 2.4mm; }}
.name-ar {{ font-size: {mm(name_size * 0.44)}; margin-top: 2.0mm; flex: none;
  color: {p.accent}; line-height: 1.5; }}
.plaque {{ position: relative; flex: none; margin-top: 4.0mm;
  width: 164mm; height: 22mm; display: flex; align-items: center;
  justify-content: center; }}
.cart {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
.deg {{ position: relative; font-size: 6.2mm; letter-spacing: 0.16em;
  text-transform: uppercase; color: {m.highlight}; font-weight: 600;
  line-height: 1; }}
.study {{ font-size: 4.0mm; font-style: italic; color: {geo.tint(p.ink, 0.84)};
  flex: none; margin-top: 2.4mm; }}
.dist {{ font-size: 2.3mm; letter-spacing: 0.26em; color: {p.accent};
  flex: none; margin-top: 2.2mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.9mm; line-height: 1.62;
  max-width: 80%; color: {geo.tint(p.ink, 0.78)}; flex: none; margin-top: 2.6mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm {{ color: {p.ink}; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; }}
.verify {{ width: 100%; margin-top: 2.8mm; color: {geo.tint(p.ink, 0.54)}; }}
"""
    body = f"""
<div class="field">
  <div class="disp inst">{INSTITUTION}</div>
  <div class="ar inst-ar">{INSTITUTION_AR}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="plaque">{cartouche}<span class="disp deg">{DEGREE}</span></div>
  <div class="disp study">{STUDY}</div>
  <div class="lab dist">{DISTINCTION}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 04 — ARABIAN ROYAL
# =============================================================================


def c04(c: Concept) -> str:
    """Deep green, ivory and deep gold, composed as a mihrab: a two-centred
    arch is the architecture, Arabic crowns it, and the Latin sits within it."""
    p = c.palette
    m = p.m
    defs, layers = substrate(p)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    layers += f'<rect {sheet.attrs()} fill="{p.accent}"/>'
    stack, inner = arch.register_stack(
        sheet.inset(5.0),
        ((0.6, "rule"), (7.5, "micro"), (1.0, "void"), (0.4, "rule")),
        metal=m, ink=p.accent,
    )
    layers += stack
    niche = geo.Rect(inner.x + 9.0, inner.y + 7.0, inner.w - 18.0, inner.h - 12.0)
    layers += (
        f'<path d="{arch.arch_niche_path(niche, rise=44.0)}" fill="{p.ground}"'
        f' stroke="{m.face}" stroke-width="0.85"/>'
        f'<path d="{arch.arch_niche_path(niche.inset(1.8), rise=42.0)}"'
        f' fill="none" stroke="{m.shadow}" stroke-width="0.25"/>'
        f'<path d="{arch.arch_niche_path(niche.inset(4.4), rise=39.0)}"'
        f' fill="none" stroke="{geo.blend(m.core, p.ground, 0.42)}" stroke-width="0.16"/>'
    )
    # Spandrels: the geometry fills the corners the arch leaves, which is
    # exactly what spandrels are for.
    for sx, mirror in ((niche.x, 1), (niche.x + niche.w, -1)):
        layers += (
            f'<g transform="translate({sx:.2f} {niche.y:.2f}) scale({mirror} 1)">'
            + geo.khatam(-8.0, 12.0, 6.4, ink=m.face, width=0.30)
            + geo.rosette(-8.0, 12.0, 5.0, ink=m.core, width=0.09, strength=1.0,
                          passes=2, pitch=1.8)
            + "</g>"
        )
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.56, 50, ink=p.accent,
                           strength=0.025, rings=5)
    layers += arch.spreader(SHEET_H * 0.815, niche.x + 26, niche.x + niche.w - 26,
                            metal=m, stops=4)
    layers += geo.microtext_ring(sheet.inset(8.4), identifier="c04",
                                 text=f"{SERIAL} · ", ink=m.highlight,
                                 size=0.58, strength=0.85)

    name_size = fit(RECIPIENT, 176, cap=12.0, floor=8.2)
    css = EXEC_CSS + f"""
.field {{ left: 44mm; right: 44mm; top: 32mm; bottom: 25mm; align-items: center;
  text-align: center; }}
.crown-ar {{ font-size: 6.6mm; font-weight: 700; color: {m.shadow}; flex: none;
  line-height: 1.4; }}
.inst {{ font-size: 3.8mm; letter-spacing: 0.22em; text-transform: uppercase;
  color: {p.accent}; font-weight: 600; flex: none; margin-top: 1.6mm; }}
.conf {{ font-size: 2.4mm; letter-spacing: 0.34em; color: {geo.tint(p.ink, 0.58)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.06; font-weight: 600;
  color: {p.ink}; flex: none; margin-top: 2.2mm; }}
.name-ar {{ font-size: {mm(name_size * 0.48)}; margin-top: 1.8mm; flex: none;
  color: {p.accent}; line-height: 1.5; font-weight: 700; }}
.deg {{ font-size: 6.0mm; letter-spacing: 0.14em; text-transform: uppercase;
  color: {m.shadow}; font-weight: 600; flex: none; margin-top: 3.2mm; }}
.study {{ font-size: 3.8mm; font-style: italic; color: {geo.tint(p.ink, 0.84)};
  flex: none; margin-top: 1.6mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.85mm; line-height: 1.6;
  max-width: 82%; color: {geo.tint(p.ink, 0.76)}; flex: none; margin-top: 2.6mm; }}
.exec {{ width: 94%; margin-top: 3mm; }}
.sig .nm {{ color: {p.ink}; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; }}
.verify {{ width: 86%; margin-top: 2.6mm; color: {geo.tint(p.ink, 0.54)}; }}
"""
    body = f"""
<div class="field">
  <div class="ar crown-ar">{INSTITUTION_AR}</div>
  <div class="disp inst">{INSTITUTION}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 05 — ROYAL UNIVERSITY
# =============================================================================


def c05(c: Concept) -> str:
    """The sovereign-university warrant: navy and champagne, a double-rule
    frame with nothing in it, and every drop of the budget spent on the crest
    architecture, the type and the execution row."""
    p = c.palette
    m = p.m
    defs, layers = substrate(p)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    stack, inner = arch.register_stack(
        sheet.inset(7.0),
        ((0.75, "rule"), (2.2, "void"), (0.30, "rule"), (3.0, "micro"),
         (0.9, "void"), (0.40, "rule")),
        metal=m, ink=p.accent,
    )
    layers += stack
    for quadrant, (x, y) in enumerate((
        (inner.x, inner.y), (inner.x + inner.w, inner.y),
        (inner.x + inner.w, inner.y + inner.h), (inner.x, inner.y + inner.h),
    )):
        layers += (
            f'<g transform="translate({x:.2f} {y:.2f}) rotate({quadrant * 90})">'
            + geo.corner_frame(0, 0, 15.0, ink=m.core, quadrant=0, strength=1.0)
            + "</g>"
        )
    layers += arch.vertical_spine(inner.x - 3.0, inner.y + 26, inner.y + inner.h - 26,
                                  metal=m, nodes=3)
    layers += arch.vertical_spine(inner.x + inner.w + 3.0, inner.y + 26,
                                  inner.y + inner.h - 26, metal=m, nodes=3)
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.50, 46, ink=p.accent,
                           strength=0.025, rings=5)
    crest = (
        geo.interlocking_squares(SHEET_W / 2, 30.0, 10.4, ink=p.accent, width=0.42)
        + geo.khatam(SHEET_W / 2, 30.0, 8.2, ink=m.core, width=0.5)
        + f'<circle cx="{SHEET_W / 2:.2f}" cy="30.0" r="12.6" fill="none"'
        f' stroke="{m.face}" stroke-width="0.55"/>'
        f'<circle cx="{SHEET_W / 2:.2f}" cy="30.0" r="13.6" fill="none"'
        f' stroke="{m.shadow}" stroke-width="0.18"/>'
    )
    layers += emboss(crest, depth=0.26, light=m.highlight, dark=m.shadow)
    layers += arch.spreader(30.0, inner.x + 14, SHEET_W / 2 - 17, metal=m, stops=3)
    layers += arch.spreader(30.0, SHEET_W / 2 + 17, inner.x + inner.w - 14,
                            metal=m, stops=3)

    name_size = fit(RECIPIENT, 200, cap=13.6, floor=9.0)
    css = EXEC_CSS + f"""
.field {{ left: 32mm; right: 32mm; top: 46mm; bottom: 24mm; align-items: center;
  text-align: center; }}
.inst {{ font-size: 5.6mm; letter-spacing: 0.10em; color: {p.accent};
  font-weight: 700; flex: none; line-height: 1.2; }}
.inst-ar {{ font-size: 4.4mm; margin-top: 1.6mm; color: {geo.tint(p.accent, 0.80)};
  flex: none; }}
.conf {{ font-size: 2.6mm; letter-spacing: 0.40em; color: {geo.tint(p.ink, 0.58)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.04; font-weight: 600;
  color: {p.ink}; flex: none; margin-top: 2.4mm; letter-spacing: -0.004em; }}
.name-ar {{ font-size: {mm(name_size * 0.42)}; margin-top: 2.0mm; flex: none;
  color: {geo.tint(p.accent, 0.90)}; line-height: 1.5; }}
.deg {{ font-size: 6.8mm; letter-spacing: 0.15em; text-transform: uppercase;
  color: {p.accent}; font-weight: 600; flex: none; margin-top: 3.6mm; }}
.study {{ font-size: 4.0mm; font-style: italic; color: {geo.tint(p.ink, 0.84)};
  flex: none; margin-top: 1.7mm; }}
.dist {{ font-size: 2.3mm; letter-spacing: 0.28em; color: {m.shadow};
  flex: none; margin-top: 2.4mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 3.0mm; line-height: 1.66;
  max-width: 72%; color: {geo.tint(p.ink, 0.80)}; flex: none; margin-top: 3.0mm; }}
.exec {{ margin-top: 4mm; }}
.sig .nm {{ color: {p.ink}; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; }}
.verify {{ width: 100%; margin-top: 3.2mm; color: {geo.tint(p.ink, 0.54)}; }}
"""
    body = f"""
<div class="field">
  <div class="disp inst">{INSTITUTION}</div>
  <div class="ar inst-ar">{INSTITUTION_AR}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="lab dist">{DISTINCTION}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 06 — GRAND MEDALLION
# =============================================================================


def c06(c: Concept) -> str:
    """No frame worth the name. One monumental struck medallion fills the sheet
    and the words are set across it — the document as a medal, not as a page."""
    p = c.palette
    m = p.m
    defs, layers = substrate(p)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)
    cx, cy = SHEET_W / 2, SHEET_H * 0.50

    layers += arch._perimeter_rule(sheet.inset(6.0), metal=m, weight=0.55)
    layers += arch._perimeter_rule(sheet.inset(8.4), metal=m, weight=0.22)
    layers += arch.radiant_field(cx, cy, 128, metal=METALS["pale"], rays=96,
                                 inner=0.42)
    layers += f'<circle cx="{cx}" cy="{cy}" r="86" fill="{p.ground}"/>'
    layers += geo.rosette(cx, cy, 84, ink=m.core, width=0.10, strength=0.16,
                          passes=3)
    for radius, weight, ink in ((84.0, 0.60, m.face), (82.0, 0.20, m.shadow),
                                (70.0, 0.34, m.face), (68.6, 0.14, m.shadow)):
        layers += (f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none"'
                   f' stroke="{ink}" stroke-width="{weight}"/>')
    layers += geo.microtext_ring(geo.Rect(cx - 88, cy - 88, 176, 176),
                                 identifier="c06",
                                 text=f"{INSTITUTION.upper()} · {SERIAL} · ",
                                 ink=p.ink, size=0.62, strength=0.30)
    for index in range(4):
        angle = 45 + index * 90
        layers += (
            f'<g transform="rotate({angle} {cx} {cy})">'
            + geo.khatam(cx, cy - 77, 4.6, ink=m.face, width=0.34)
            + "</g>"
        )
    layers += arch.mandala(cx, cy, 44, ink=p.accent, strength=0.025, rings=4)

    name_size = fit(RECIPIENT, 150, cap=12.0, floor=8.0)
    css = EXEC_CSS + f"""
.field {{ left: 62mm; right: 62mm; top: 40mm; bottom: 40mm; align-items: center;
  text-align: center; }}
.inst {{ font-size: 3.6mm; letter-spacing: 0.30em; text-transform: uppercase;
  color: {p.accent}; font-weight: 700; flex: none; }}
.inst-ar {{ font-size: 3.6mm; margin-top: 1.2mm; color: {geo.tint(p.accent, 0.78)};
  flex: none; }}
.conf {{ font-size: 2.3mm; letter-spacing: 0.34em; color: {geo.tint(p.ink, 0.56)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.08; font-weight: 700;
  color: {p.ink}; flex: none; margin-top: 2.2mm; letter-spacing: -0.012em; }}
.name-ar {{ font-size: {mm(name_size * 0.44)}; margin-top: 1.8mm; flex: none;
  color: {p.accent}; line-height: 1.5; }}
.deg {{ font-size: 5.4mm; letter-spacing: 0.20em; text-transform: uppercase;
  color: {m.shadow}; font-weight: 700; flex: none; margin-top: 3.0mm; }}
.study {{ font-size: 3.5mm; color: {geo.tint(p.ink, 0.82)}; flex: none;
  margin-top: 1.5mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.75mm; line-height: 1.58;
  max-width: 88%; color: {geo.tint(p.ink, 0.74)}; flex: none; margin-top: 2.4mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm {{ color: {p.ink}; font-size: 3.6mm; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; }}
.verify {{ width: 100%; margin-top: 3.0mm; color: {geo.tint(p.ink, 0.54)}; }}
"""
    body = f"""
<div class="field">
  <div class="disp inst">{INSTITUTION}</div>
  <div class="ar inst-ar">{INSTITUTION_AR}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 07 — GUILLOCHÉ PALACE
# =============================================================================


def c07(c: Concept) -> str:
    """The security-document aesthetic taken seriously: three lathe registers,
    a turned field, a portrait-position rosette, and the verification block
    designed as the composition's right-hand counterweight rather than hidden."""
    p = c.palette
    m = p.m
    defs, layers = substrate(p, screen=True)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    stack, inner = arch.register_stack(
        sheet.inset(5.0),
        ((0.55, "rule"), (2.8, "lathe"), (0.30, "rule"), (0.9, "void"),
         (3.4, "lathe"), (0.35, "rule")),
        metal=m, ink=p.accent,
    )
    layers += stack
    layers += geo.guilloche_band(inner.inset(3.0), ink=m.core, width=0.08,
                                 strength=0.55, amplitude=1.1,
                                 waves=int(SHEET_W / 1.9))
    layers += geo.rosette(SHEET_W * 0.795, SHEET_H * 0.50, 46, ink=m.core,
                          width=0.085, strength=0.42, passes=3)
    layers += geo.rosette(SHEET_W * 0.795, SHEET_H * 0.50, 28, ink=p.accent,
                          width=0.075, strength=0.30, passes=3)
    layers += arch.medallion(SHEET_W * 0.795, SHEET_H * 0.50, 17.5, metal=m,
                             ink=p.ink, legend="MERIDIAN INSTITUTE",
                             identifier=SERIAL)
    layers += arch.mandala(SHEET_W * 0.36, SHEET_H * 0.50, 52, ink=p.accent,
                           strength=0.025, rings=5)
    layers += geo.microtext_ring(sheet.inset(8.4), identifier="c07",
                                 text=f"{SERIAL} · {CODE} · ", ink=p.ink,
                                 size=0.56, strength=0.30)

    name_size = fit(RECIPIENT, 152, cap=11.6, floor=8.0)
    css = EXEC_CSS + f"""
.field {{ left: 22mm; right: 96mm; top: 24mm; bottom: 22mm; align-items: flex-start;
  text-align: left; }}
.inst {{ font-size: 4.4mm; letter-spacing: 0.11em; color: {p.accent};
  font-weight: 700; flex: none; line-height: 1.18; }}
.inst-ar {{ font-size: 4.0mm; margin-top: 1.3mm; color: {geo.tint(p.accent, 0.82)};
  flex: none; }}
.conf {{ font-size: 2.3mm; letter-spacing: 0.32em; color: {geo.tint(p.ink, 0.56)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.06; font-weight: 600;
  color: {p.ink}; flex: none; margin-top: 2.0mm; }}
.name-ar {{ font-size: {mm(name_size * 0.46)}; margin-top: 1.7mm; flex: none;
  color: {p.accent}; line-height: 1.5; text-align: right; width: 100%; }}
.deg {{ font-size: 5.8mm; letter-spacing: 0.14em; text-transform: uppercase;
  color: {m.shadow}; font-weight: 600; flex: none; margin-top: 3.0mm; }}
.study {{ font-size: 3.6mm; font-style: italic; color: {geo.tint(p.ink, 0.82)};
  flex: none; margin-top: 1.4mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.8mm; line-height: 1.6;
  max-width: 96%; color: {geo.tint(p.ink, 0.76)}; flex: none; margin-top: 2.6mm; }}
.exec {{ margin-top: 3mm; }}
.sigrow {{ gap: 5mm; }}
.sig {{ text-align: left; }}
.sig .nm {{ color: {p.ink}; font-size: 3.4mm; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; font-size: 1.9mm; }}
.verify {{ width: 100%; margin-top: 2.6mm; color: {geo.tint(p.ink, 0.54)}; }}
.vblock {{ position: absolute; right: 20mm; bottom: 26mm; width: 56mm;
  text-align: center; }}
.vblock .cap {{ font-family: 'Inter', sans-serif; font-size: 2.0mm;
  letter-spacing: 0.26em; text-transform: uppercase; color: {geo.tint(p.ink, 0.62)}; }}
.vblock .code {{ font-family: 'IBM Plex Mono', monospace; font-size: 3.4mm;
  letter-spacing: 0.10em; color: {p.accent}; margin-top: 1.4mm; }}
"""
    body = f"""
<div class="field">
  <div class="disp inst">{INSTITUTION}</div>
  <div class="ar inst-ar">{INSTITUTION_AR}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
<div class="vblock">
  <div class="cap">Credential verification</div>
  <div class="code">{CODE}</div>
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 08 — HERITAGE MANUSCRIPT
# =============================================================================


def c08(c: Concept) -> str:
    """A page from an illuminated codex: a wide illuminated border of interlace
    and gold blocks, a shamsa in the margin, and Arabic as the principal
    display — the Latin is the gloss, not the other way round."""
    p = c.palette
    m, m2 = p.m, p.m2
    defs, layers = substrate(p)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    border = sheet.inset(6.0)
    layers += f'<rect {border.attrs()} fill="{p.accent}"/>'
    layers += arch.tessellation_field(border, cell=9.0, ink=m.highlight,
                                      strength=0.85, width=0.13, hollow=17.0)
    layers += arch.girih_band(border.inset(0.8), depth=5.2, metal=m2)
    layers += arch._perimeter_rule(border, metal=m, weight=0.55)
    text_block = border.inset(17.0)
    layers += (
        f'<rect {text_block.attrs()} fill="{p.ground}"/>'
        + arch._perimeter_rule(text_block, metal=m, weight=0.48)
        + arch._perimeter_rule(text_block.inset(1.6), metal=m2, weight=0.18)
    )
    # The shamsa: an illuminated rosette in the outer margin, which is where a
    # codex puts it — a marker for the reader, not a decoration for the page.
    for cx in (border.x + 8.5, border.x + border.w - 8.5):
        layers += f'<circle cx="{cx:.2f}" cy="{SHEET_H / 2:.2f}" r="7.6" fill="{p.accent}"/>'
        layers += arch.medallion(cx, SHEET_H / 2, 7.0, metal=m, ink=p.ink)
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.50, 52, ink=m.shadow,
                           strength=0.025, rings=5)
    layers += geo.microtext_ring(text_block.inset(-2.6), identifier="c08",
                                 text=f"{SERIAL} · ", ink=m.highlight,
                                 size=0.58, strength=0.9)

    name_size = fit(RECIPIENT, 176, cap=11.4, floor=7.8)
    css = EXEC_CSS + f"""
.field {{ left: 44mm; right: 44mm; top: 32mm; bottom: 30mm; align-items: center;
  text-align: center; }}
.crown-ar {{ font-size: 7.4mm; font-weight: 700; color: {m.shadow}; flex: none;
  line-height: 1.45; }}
.inst {{ font-size: 3.4mm; letter-spacing: 0.24em; text-transform: uppercase;
  color: {geo.tint(p.ink, 0.66)}; font-weight: 600; flex: none; margin-top: 1.4mm; }}
.conf {{ font-size: 2.3mm; letter-spacing: 0.30em; color: {geo.tint(p.ink, 0.56)};
  flex: none; }}
.name-ar {{ font-size: {mm(name_size * 0.86)}; flex: none; color: {p.ink};
  line-height: 1.5; font-weight: 700; margin-top: 1.8mm; }}
.name {{ font-size: {mm(name_size * 0.62)}; line-height: 1.12; font-weight: 600;
  color: {geo.tint(p.ink, 0.86)}; flex: none; margin-top: 1.8mm; }}
.deg-ar {{ font-size: 5.6mm; color: {m.shadow}; font-weight: 700; flex: none;
  margin-top: 3.0mm; }}
.deg {{ font-size: 4.2mm; letter-spacing: 0.16em; text-transform: uppercase;
  color: {m.shadow}; font-weight: 600; flex: none; margin-top: 1.2mm; }}
.study {{ font-size: 3.4mm; font-style: italic; color: {geo.tint(p.ink, 0.80)};
  flex: none; margin-top: 1.4mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.75mm; line-height: 1.6;
  max-width: 86%; color: {geo.tint(p.ink, 0.74)}; flex: none; margin-top: 2.4mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm {{ color: {p.ink}; font-size: 3.5mm; }}
.sig .of {{ color: {geo.tint(m.shadow, 0.95)}; }}
.verify {{ width: 100%; margin-top: 2.6mm; color: {geo.tint(p.ink, 0.54)}; }}
"""
    body = f"""
<div class="field">
  <div class="ar crown-ar">{INSTITUTION_AR}</div>
  <div class="disp inst">{INSTITUTION}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar deg-ar">{DEGREE_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 09 — MODERN ROYAL
# =============================================================================


def c09(c: Concept) -> str:
    """Contemporary grotesque type at monumental scale against an elaborate
    gold architecture, composed asymmetrically. Royal without being historical:
    the ornament is dense, the typography is 2031."""
    p = c.palette
    m = p.m
    defs, layers = substrate(p)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    layers += f'<rect {sheet.attrs()} fill="{p.ground}"/>'
    # A heavy worked band on the right third — the architecture is a wall, not
    # a frame, and the composition leans against it.
    wall = geo.Rect(SHEET_W * 0.665, 0, SHEET_W * 0.335, SHEET_H)
    layers += f'<rect {wall.attrs()} fill="{p.accent}"/>'
    layers += arch.tessellation_field(wall, cell=13.5, ink=m.face, strength=1.0,
                                      width=0.30)
    layers += arch.tessellation_field(wall, cell=27.0, ink=m.highlight,
                                      strength=1.0, width=0.16)
    layers += (
        f'<path d="{arch.stepped_rect_path(wall.inset(6.0), cut=9.0)}"'
        f' fill="none" stroke="{m.face}" stroke-width="0.45"/>'
    )
    layers += geo.rosette(wall.cx, SHEET_H * 0.50, 42, ink=m.highlight,
                          width=0.14, strength=1.0, passes=3)
    layers += arch.medallion(wall.cx, SHEET_H * 0.50, 24.0, metal=m, ink=p.ink)
    layers += engraved_metal_rule(wall.x, 0, wall.x, SHEET_H, metal=m, weight=0.75)
    layers += arch.vertical_spine(wall.x - 4.2, 26, SHEET_H - 26, metal=m, nodes=4)
    layers += arch._perimeter_rule(sheet.inset(5.0), metal=m, weight=0.42)
    layers += arch.mandala(SHEET_W * 0.31, SHEET_H * 0.50, 60, ink=p.accent,
                           strength=0.025, rings=5)
    layers += geo.microtext_ring(sheet.inset(8.4), identifier="c09",
                                 text=f"{SERIAL} · ", ink=p.accent, size=0.56,
                                 strength=0.28)

    name_size = fit(RECIPIENT, 168, cap=12.2, floor=8.0, per_char=1.42)
    css = EXEC_CSS + f"""
.field {{ left: 20mm; right: 112mm; top: 22mm; bottom: 20mm; align-items: flex-start;
  text-align: left; }}
.inst {{ font-size: 4.0mm; letter-spacing: 0.02em; color: {p.accent};
  font-weight: 700; flex: none; line-height: 1.16; }}
.inst-ar {{ font-size: 4.0mm; margin-top: 1.3mm; color: {geo.tint(p.accent, 0.82)};
  flex: none; }}
.conf {{ font-size: 2.2mm; letter-spacing: 0.30em; color: {geo.tint(p.ink, 0.56)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.02; font-weight: 700;
  color: {p.ink}; flex: none; margin-top: 2.0mm; letter-spacing: -0.020em; }}
.name-ar {{ font-size: {mm(name_size * 0.44)}; margin-top: 1.8mm; flex: none;
  color: {p.accent}; line-height: 1.5; font-weight: 700; }}
.hinge {{ width: 34%; height: 1.1mm; background: {m.face}; flex: none;
  margin-top: 4.0mm; border-top: 0.2mm solid {m.highlight};
  border-bottom: 0.2mm solid {m.shadow}; }}
.deg {{ font-size: 6.6mm; letter-spacing: 0.04em; text-transform: uppercase;
  color: {m.shadow}; font-weight: 700; flex: none; margin-top: 3.2mm;
  line-height: 1.08; }}
.study {{ font-size: 3.7mm; color: {geo.tint(p.ink, 0.82)}; flex: none;
  margin-top: 1.6mm; max-width: 92%; }}
.dist {{ font-size: 2.2mm; letter-spacing: 0.24em; color: {p.accent};
  flex: none; margin-top: 2.2mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.8mm; line-height: 1.6;
  max-width: 94%; color: {geo.tint(p.ink, 0.76)}; flex: none; margin-top: 2.6mm; }}
.exec {{ margin-top: 3mm; }}
.sigrow {{ gap: 5mm; }}
.sig {{ text-align: left; }}
.sig .nm {{ color: {p.ink}; font-size: 3.4mm; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; font-size: 1.9mm; }}
.verify {{ width: 100%; margin-top: 2.6mm; color: {geo.tint(p.ink, 0.54)}; }}
"""
    body = f"""
<div class="field">
  <div class="disp inst">{INSTITUTION}</div>
  <div class="ar inst-ar">{INSTITUTION_AR}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="hinge"></div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="lab dist">{DISTINCTION}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 10 — MIDNIGHT ROYAL
# =============================================================================


def c10(c: Concept) -> str:
    """The inversion: a full-bleed midnight ground, gold that behaves as light
    rather than as pigment, and an ivory ceremonial plaque mounted on it."""
    p = c.palette
    m = p.m
    defs, layers = "", ""
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    layers += f'<rect {sheet.attrs()} fill="{p.ground}"/>'
    layers += arch.radiant_field(SHEET_W / 2, SHEET_H * 0.50, 168,
                                 metal=METALS["deep"], rays=120, inner=0.30)
    layers += f'<rect {sheet.attrs()} fill="{p.ground}" opacity="0.72"/>'
    layers += arch.tessellation_field(sheet.inset(5.0), cell=15.0, ink=m.core,
                                      strength=1.0, width=0.10, hollow=13.0)
    stack, inner = arch.register_stack(
        sheet.inset(5.0),
        ((0.65, "rule"), (13.0, "void"), (0.35, "rule")),
        metal=m, ink=p.accent,
    )
    layers += stack
    for quadrant, (x, y) in enumerate((
        (inner.x, inner.y), (inner.x + inner.w, inner.y),
        (inner.x + inner.w, inner.y + inner.h), (inner.x, inner.y + inner.h),
    )):
        layers += (
            f'<g transform="translate({x:.2f} {y:.2f}) rotate({quadrant * 90})">'
            + geo.khatam(0, 0, 8.4, ink=m.face, width=0.46)
            + geo.rosette(0, 0, 6.6, ink=m.core, width=0.09, strength=0.8,
                          passes=2, pitch=1.8)
            + "</g>"
        )
    plaque = geo.Rect(SHEET_W * 0.115, SHEET_H * 0.155, SHEET_W * 0.77,
                      SHEET_H * 0.665)
    layers += (
        f'<path d="{arch.cartouche_path(plaque, arch=5.0, cut=9.0)}"'
        f' fill="{p.paper}" stroke="{m.face}" stroke-width="0.80"/>'
        f'<path d="{arch.cartouche_path(plaque.inset(2.0), arch=4.4, cut=8.0)}"'
        f' fill="none" stroke="{m.shadow}" stroke-width="0.22"/>'
    )
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.50, 46, ink=p.accent,
                           strength=0.025, rings=5)
    layers += arch.cresting(SHEET_W / 2, plaque.y, 54, 11.5, metal=m)
    layers += geo.microtext_ring(sheet.inset(8.4), identifier="c10",
                                 text=f"{SERIAL} · {CODE} · ", ink=m.core,
                                 size=0.56, strength=1.0)

    name_size = fit(RECIPIENT, 176, cap=12.4, floor=8.4)
    css = EXEC_CSS + f"""
.field {{ left: 44mm; right: 44mm; top: 42mm; bottom: 40mm; align-items: center;
  text-align: center; }}
.inst {{ font-size: 4.6mm; letter-spacing: 0.16em; text-transform: uppercase;
  color: {p.accent}; font-weight: 600; flex: none; }}
.inst-ar {{ font-size: 4.2mm; margin-top: 1.4mm; color: {geo.tint(p.accent, 0.80)};
  flex: none; }}
.conf {{ font-size: 2.4mm; letter-spacing: 0.36em; color: {geo.tint(p.ink, 0.58)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.05; font-weight: 600;
  color: {p.ink}; flex: none; margin-top: 2.2mm; }}
.name-ar {{ font-size: {mm(name_size * 0.45)}; margin-top: 1.8mm; flex: none;
  color: {p.accent}; line-height: 1.5; }}
.deg {{ font-size: 6.4mm; letter-spacing: 0.15em; text-transform: uppercase;
  color: {METALS["deep"].shadow}; font-weight: 600; flex: none; margin-top: 3.0mm; }}
.study {{ font-size: 3.8mm; font-style: italic; color: {geo.tint(p.ink, 0.84)};
  flex: none; margin-top: 1.5mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.85mm; line-height: 1.62;
  max-width: 80%; color: {geo.tint(p.ink, 0.76)}; flex: none; margin-top: 2.6mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm {{ color: {p.ink}; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; }}
.verify {{ position: absolute; left: 20mm; right: 20mm; bottom: 9mm;
  color: {m.face}; }}
"""
    body = f"""
<div class="field">
  <div class="disp inst">{INSTITUTION}</div>
  <div class="ar inst-ar">{INSTITUTION_AR}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
</div>
{verify_band(ink=p.ink)}
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 11 — CRIMSON IMPERIAL
# =============================================================================


def c11(c: Concept) -> str:
    """Crimson mass, gold architecture, an ivory cartouche carrying the name.
    The most frankly imperial of the twelve: weight at the corners, weight at
    the edges, and one bright ceremonial centre."""
    p = c.palette
    m = p.m
    defs, layers = substrate(p)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    band = sheet.inset(5.5)
    layers += f'<rect {band.attrs()} fill="{p.accent}"/>'
    layers += arch.tessellation_field(band, cell=8.6, ink=m.highlight,
                                      strength=0.75, width=0.11, hollow=19.0)
    layers += arch._perimeter_rule(band, metal=m, weight=0.62)
    inner = band.inset(19.0)
    layers += (
        f'<path d="{arch.stepped_rect_path(inner, cut=10.0, step=2.4)}"'
        f' fill="{p.ground}" stroke="{m.face}" stroke-width="0.72"/>'
        f'<path d="{arch.stepped_rect_path(inner.inset(1.7), cut=9.2, step=2.2)}"'
        f' fill="none" stroke="{m.shadow}" stroke-width="0.22"/>'
    )
    for quadrant, (x, y) in enumerate((
        (5.5, 5.5), (SHEET_W - 5.5, 5.5),
        (SHEET_W - 5.5, SHEET_H - 5.5), (5.5, SHEET_H - 5.5),
    )):
        layers += arch.corner_block(x, y, 25.0, quadrant=quadrant,
                                    mass=geo.blend(p.ink, p.accent, 0.55), metal=m, ink=p.ink)
    for cx in (band.x + 9.5, band.x + band.w - 9.5):
        layers += arch.vertical_spine(cx, band.y + 34, band.y + band.h - 34,
                                      metal=m, nodes=3)
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.52, 52, ink=p.accent,
                           strength=0.025, rings=5)
    layers += arch.cresting(SHEET_W / 2, inner.y, 58, 12.5, metal=m)
    layers += geo.microtext_ring(sheet.inset(8.4), identifier="c11",
                                 text=f"{INSTITUTION.upper()} · {SERIAL} · ",
                                 ink=m.highlight, size=0.56, strength=0.8)

    name_size = fit(RECIPIENT, 172, cap=12.2, floor=8.2)
    plate_rect = geo.Rect(4, 3, 168, 22)
    name_plate = (
        f'<svg class="cart" viewBox="0 0 176 28" preserveAspectRatio="none">'
        f'<path d="{arch.cartouche_path(plate_rect, arch=3.6, cut=7.0)}"'
        f' fill="{p.paper}" stroke="{m.face}" stroke-width="0.6"/>'
        f'<path d="{arch.cartouche_path(plate_rect.inset(1.5), arch=3.2, cut=6.2)}"'
        f' fill="none" stroke="{m.shadow}" stroke-width="0.2"/></svg>'
    )
    css = EXEC_CSS + f"""
.field {{ left: 42mm; right: 42mm; top: 36mm; bottom: 33mm; align-items: center;
  text-align: center; }}
.inst {{ font-size: 4.8mm; letter-spacing: 0.16em; text-transform: uppercase;
  color: {p.accent}; font-weight: 600; flex: none; }}
.inst-ar {{ font-size: 4.3mm; margin-top: 1.4mm; color: {geo.tint(p.accent, 0.80)};
  flex: none; }}
.conf {{ font-size: 2.4mm; letter-spacing: 0.36em; color: {geo.tint(p.ink, 0.58)};
  flex: none; }}
.namewrap {{ position: relative; flex: none; margin-top: 2.4mm; width: 104%;
  display: flex; align-items: center; justify-content: center; }}
.cart {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
.name {{ position: relative; font-size: {mm(name_size)}; line-height: 1.05;
  font-weight: 600; color: {p.ink}; padding: 3.4mm 6mm; }}
.name-ar {{ font-size: {mm(name_size * 0.45)}; margin-top: 2.0mm; flex: none;
  color: {p.accent}; line-height: 1.5; }}
.deg {{ font-size: 6.4mm; letter-spacing: 0.15em; text-transform: uppercase;
  color: {m.shadow}; font-weight: 600; flex: none; margin-top: 3.0mm; }}
.study {{ font-size: 3.9mm; font-style: italic; color: {geo.tint(p.ink, 0.84)};
  flex: none; margin-top: 1.5mm; }}
.dist {{ font-size: 2.3mm; letter-spacing: 0.26em; color: {p.accent};
  flex: none; margin-top: 2.2mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.85mm; line-height: 1.62;
  max-width: 82%; color: {geo.tint(p.ink, 0.76)}; flex: none; margin-top: 2.6mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm {{ color: {p.ink}; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; }}
.verify {{ width: 100%; margin-top: 2.8mm; color: {geo.tint(p.ink, 0.54)}; }}
"""
    body = f"""
<div class="field">
  <div class="disp inst">{INSTITUTION}</div>
  <div class="ar inst-ar">{INSTITUTION_AR}</div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="namewrap">{name_plate}<span class="disp name">{keep(RECIPIENT)}</span></div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="lab dist">{DISTINCTION}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  {verify_band(ink=p.ink)}
</div>
"""
    return page(c, svg(layers, defs), body, css)


# =============================================================================
# 12 — EDIRASX SIGNATURE
# =============================================================================


def c12(c: Concept) -> str:
    """EdirasX's own geometry as the entire structural system: the khatam
    lattice resolves from dense at the trim to open at the centre, so the frame
    and the field are one construction rather than two. Two metals, and the
    verification architecture designed as a visible register instead of a
    footnote."""
    p = c.palette
    m, m2 = p.m, p.m2
    defs, layers = substrate(p, screen=True)
    sheet = geo.Rect(0, 0, SHEET_W, SHEET_H)

    # The density gradient: four bands, each with a larger cell and a lighter
    # ink than the one outside it. This is the concept — a frame that does not
    # end, it dissolves.
    for inset, cell, strength, width in (
        (5.0, 6.5, 1.00, 0.20),
        (15.0, 11.5, 0.46, 0.13),
        (27.0, 20.0, 0.20, 0.09),
        (41.0, 34.0, 0.085, 0.075),
    ):
        layers += arch.tessellation_field(
            sheet.inset(inset), cell=cell, ink=m.core, strength=strength,
            width=width, hollow=11.0,
        )
    layers += arch._perimeter_rule(sheet.inset(5.0), metal=m, weight=0.62)
    layers += arch._perimeter_rule(sheet.inset(16.0), metal=m2, weight=0.30)
    for quadrant, (x, y) in enumerate((
        (5.0, 5.0), (SHEET_W - 5.0, 5.0),
        (SHEET_W - 5.0, SHEET_H - 5.0), (5.0, SHEET_H - 5.0),
    )):
        layers += arch.corner_block(x, y, 22.0, quadrant=quadrant,
                                    mass=geo.blend(p.ink, p.accent, 0.55), metal=m, ink=p.ink)
    layers += arch.mandala(SHEET_W / 2, SHEET_H * 0.46, 56, ink=p.accent,
                           strength=0.025, rings=5)
    # The institutional mark, blind-embossed on the axis: the one figure the
    # whole lattice resolves into.
    mark = (
        geo.interlocking_squares(SHEET_W / 2, 32.0, 9.0, ink=p.accent, width=0.40)
        + geo.khatam(SHEET_W / 2, 32.0, 7.2, ink=m.core, width=0.52)
        + geo.khatam(SHEET_W / 2, 32.0, 4.0, ink=m2.core, width=0.30)
    )
    layers += emboss(mark, depth=0.24, light=m.highlight, dark=m.shadow)
    layers += geo.microtext_ring(sheet.inset(8.4), identifier="c12",
                                 text=f"EDIRASX · {SERIAL} · {CODE} · ",
                                 ink=p.ink, size=0.56, strength=0.32)

    name_size = fit(RECIPIENT, 186, cap=13.0, floor=8.6)
    css = EXEC_CSS + f"""
.field {{ left: 42mm; right: 42mm; top: 44mm; bottom: 22mm; align-items: center;
  text-align: center; }}
.bihead {{ display: flex; flex-direction: column; align-items: center; flex: none; }}
.inst {{ font-size: 4.4mm; letter-spacing: 0.18em; text-transform: uppercase;
  color: {p.accent}; font-weight: 600; }}
.inst-ar {{ font-size: 4.6mm; margin-top: 1.5mm; color: {p.accent};
  font-weight: 700; }}
.conf {{ font-size: 2.4mm; letter-spacing: 0.36em; color: {geo.tint(p.ink, 0.58)};
  flex: none; }}
.name {{ font-size: {mm(name_size)}; line-height: 1.04; font-weight: 600;
  color: {p.ink}; flex: none; margin-top: 2.4mm; }}
.name-ar {{ font-size: {mm(name_size * 0.46)}; margin-top: 2.0mm; flex: none;
  color: {p.accent}; line-height: 1.5; font-weight: 700; }}
.deg {{ font-size: 6.8mm; letter-spacing: 0.14em; text-transform: uppercase;
  color: {m.shadow}; font-weight: 600; flex: none; margin-top: 3.2mm; }}
.study {{ font-size: 4.0mm; font-style: italic; color: {geo.tint(p.ink, 0.84)};
  flex: none; margin-top: 1.6mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.9mm; line-height: 1.62;
  max-width: 78%; color: {geo.tint(p.ink, 0.78)}; flex: none; margin-top: 2.8mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm {{ color: {p.ink}; }}
.sig .of {{ color: {geo.tint(p.accent, 0.92)}; }}
.credential {{ display: flex; justify-content: space-between; align-items: center;
  width: 100%; flex: none; margin-top: 3.4mm; padding-top: 2.2mm;
  border-top: 0.28mm solid {m2.face}; }}
.credential .k {{ font-family: 'Inter', sans-serif; font-size: 1.85mm;
  letter-spacing: 0.24em; text-transform: uppercase; color: {geo.tint(p.ink, 0.55)}; }}
.credential .v {{ font-family: 'IBM Plex Mono', monospace; font-size: 2.9mm;
  color: {p.accent}; margin-top: 0.7mm; letter-spacing: 0.05em; }}
.credential > div {{ text-align: left; }}
.credential > div:last-child {{ text-align: right; }}
"""
    body = f"""
<div class="field">
  <div class="bihead">
    <div class="disp inst">{INSTITUTION}</div>
    <div class="ar inst-ar">{INSTITUTION_AR}</div>
  </div>
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="ar name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="disp study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(m)}
  <div class="spacer"></div>
  {execution(m, p.ink)}
  <div class="credential">
    <div><div class="k">Credential</div><div class="v">{SERIAL}</div></div>
    <div><div class="k">Issued</div><div class="v">{ISSUED}</div></div>
    <div><div class="k">Verify</div><div class="v">{CODE}</div></div>
  </div>
</div>
"""
    return page(c, svg(layers, defs), body, css)


# --- the board ---------------------------------------------------------------

CONCEPTS: tuple[Concept, ...] = (
    Concept("01", "Royal Palace",
            "a palace doorcase: mass at the corners, a stepped architrave, a crest "
            "breaking the line",
            Palette("#F7F2E6", "#101826", "#14294C", "royal"),
            "Fraunces", "Amiri",
            "peer under the Latin masthead and again under the name", c01),
    Concept("02", "Imperial Islamic",
            "a midnight strapwork border with an ivory field cut into it",
            Palette("#F5F0E2", "#0E1B33", "#0E1B33", "royal", "champagne"),
            "Source Serif 4", "Amiri",
            "a peer band: Arabic and Latin share the masthead and the degree", c02),
    Concept("03", "Ottoman Academic",
            "the tuğra instinct — the important words are set into a plate, not "
            "written on the page",
            Palette("#F6F0E1", "#2A1016", "#4A1220", "antique"),
            "Fraunces", "Amiri",
            "a full-measure counterpart beneath each Latin line", c03),
    Concept("04", "Arabian Royal",
            "a mihrab: the two-centred arch is the architecture and Arabic crowns it",
            Palette("#F7F3E7", "#0F2620", "#123A2E", "deep"),
            "Source Serif 4", "Amiri",
            "the crown — Arabic is the first thing read on the sheet", c04),
    Concept("05", "Royal University",
            "a sovereign warrant: an empty double-rule frame, everything spent on crest, "
            "type and execution",
            Palette("#F8F4EA", "#111A2C", "#16294A", "champagne"),
            "Source Serif 4", "Amiri",
            "a quiet peer line — this direction is deliberately Latin-forward", c05),
    Concept("06", "Grand Medallion",
            "the document as a struck medal: one monumental turned field and the words across it",
            Palette("#F7F2E6", "#151312", "#4A3714", "antique"),
            "Archivo", "Amiri",
            "set inside the medallion field with the Latin, at equal weight", c06),
    Concept("07", "Guilloché Palace",
            "a security instrument: three lathe registers and the verification block as "
            "counterweight",
            Palette("#F8F5EC", "#14202E", "#1E3A5C", "champagne"),
            "Source Serif 4", "Amiri",
            "right-aligned against the Latin's left axis — the two scripts bracket the field", c07),
    Concept("08", "Heritage Manuscript",
            "a page from an illuminated codex, where the Latin is the gloss and Arabic is the text",
            Palette("#EFE6CE", "#2A2214", "#6B4E1E", "royal", "copper",
                    paper="#EFE6CE"),
            "Fraunces", "Amiri",
            "the principal display: largest, first, and set as text rather than translation", c08),
    Concept("09", "Modern Royal",
            "2031 typography against a dense gold wall, composed asymmetrically",
            Palette("#F6F3EC", "#111318", "#1A1D24", "champagne"),
            "Archivo", "Cairo",
            "a modern Arabic sans matched to the grotesque, not a naskh borrowed for it", c09),
    Concept("10", "Midnight Royal",
            "the inversion: gold as light on a midnight ground, with an ivory plaque mounted on it",
            Palette("#0A1428", "#111A2C", "#B08D57", "pale", paper="#F7F2E6"),
            "Fraunces", "Amiri",
            "a peer line on the plaque; the ground carries no text at all", c10),
    Concept("11", "Crimson Imperial",
            "frankly imperial: crimson mass, gold architecture, one bright ceremonial centre",
            Palette("#F7F1E4", "#2A0E18", "#5A1226", "royal"),
            "Fraunces", "Amiri",
            "a peer line under the cartouche, in the accent rather than the ink", c11),
    Concept("12", "EdirasX Signature",
            "one construction for frame and field: the khatam lattice dissolving "
            "from trim to centre",
            Palette("#F7F2E6", "#0A101C", "#132038", "royal", "silver"),
            "Source Serif 4", "Amiri",
            "co-equal masthead, co-equal name — the bilingual identity is the mark", c12),
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for concept in CONCEPTS:
        html = concept.build(concept)
        target = OUT / f"{concept.key}-{concept.name.lower().replace(' ', '-')}.html"
        target.write_text(html, encoding="utf-8")
        print(f"{target.name:44s} {target.stat().st_size / 1024:6.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
