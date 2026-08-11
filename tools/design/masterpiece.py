"""Four finalists, developed individually — and separated for manufacture.

A concept is a proposal. This file is what a proposal becomes when somebody has
to make it: every millimetre placed against a named zone, every ornament a
member of the document's own geometric family, every metal a *role* rather than
a colour, and the artwork split into the plates a printer actually receives.

**The separations are the point.** A luxury certificate is not one image. It is
a substrate, a security underprint, one or two foil plates, an embossing die,
a fine-text layer and a variable data layer, and they are made by different
machines in a fixed order. So each plate here is built as named layers, the
preview is those layers composited, and each layer is also written out on its
own. If a layer cannot be produced alone it was never a separation — it was a
picture with a caption.

**The four zones rule.** Every plate declares its zones as millimetre bands and
nothing may cross one. The zones are: trim, security margin, register stack,
architectural frame, ceremonial field, execution band. A composition that needs
to break a zone changes the zone, in the open, rather than nudging an element.

**Depth is designed, not accidental.** Each plate places elements at four
viewing distances, and the assignment is deliberate:

    1 m     the frame's mass, the ground colour, the ceremonial centre
    50 cm   the hierarchy, the corner architecture, the medallion, the metal
    20 cm   the interlace, the engraved rules, the kites, the seal's device
    5 cm    the lathe petals, the fine text, the construction lines, the fibres

Something that reads at every distance is a poster. Something that reads at one
is a diagram. A document worth keeping resolves *differently* four times, and
the code below says which register belongs to which distance.

**Asymmetry with a reason.** The major architecture is symmetrical because a
ceremonial document is. Three things are deliberately not: the seal sits at one
end of the execution band, the verification panel at the other, and the
institution's mark on the axis above both — a three-point balance rather than a
mirror. Nothing else is asymmetric, so those three read as decisions.
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))
OUT = ROOT / "docs" / "edtechx" / "design" / "masterpieces"

from app.modules.design import architecture as arch  # noqa: E402
from app.modules.design import geometry as geo  # noqa: E402
from app.modules.design.gilding import Scheme, scheme_for  # noqa: E402
from app.modules.design.signature import Motif, motif_for  # noqa: E402
from app.modules.design.typeface import font_face_css  # noqa: E402

W, H = 297.0, 210.0

# --- the record ---------------------------------------------------------------

INSTITUTION = "The Meridian Institute for Advanced Study and Research"
INSTITUTION_AR = "معهد مريديان للدراسات العليا والبحث العلمي"
RECIPIENT = "Muhammad Abdulrahman Ibrahim Abdulwahid Al-Sulaimiy"
RECIPIENT_AR = "محمد عبد الرحمن إبراهيم عبد الواحد السليمي"
DEGREE = "Doctor of Philosophy"
DEGREE_AR = "درجة الدكتوراه في الفلسفة"
STUDY = "Educational Leadership and Institutional Development"
CONFERRAL = "The Senate of the Institute has conferred upon"
STATEMENT = (
    "having pursued the prescribed programme of research, submitted a thesis "
    "examined and approved by the Board of Examiners, and satisfied the Senate "
    "in the oral examination held on the fourteenth day of March, two thousand "
    "and thirty-one."
)
DISTINCTION = "With the commendation of the Senate"
SIGNATORIES = (
    ("Prof. Amina Yusuf", "Vice-Chancellor", "Presiding authority of the Senate"),
    ("Dr Tomas Reinholt", "Dean of the Graduate School", "Board of Examiners"),
    ("Mr K. Balogun", "Registrar", "Custodian of the record"),
)
SERIAL = "PHD/2031/0007"
CODE = "BFJ7-DRNM-8VZ9"
ISSUED = "14 March 2031"
SEAL_LEGEND = "MERIDIAN INSTITUTE"

#: The document's own geometry. One family for every doctoral award this
#: institution issues; the security layer is what varies per sheet.
MOTIF: Motif = motif_for(institution=INSTITUTION, family="doctoral")


#: Separation order. This is the order a press lays them down, and the preview
#: composites in the same order so what is on screen is what comes off the
#: machine rather than a different stack that happens to look similar.
SEPARATIONS: tuple[tuple[str, str], ...] = (
    ("substrate", "Paper colour and deterministic fibre field"),
    ("security", "Guilloché registers, anti-copy ruling, ground figure"),
    ("process", "Structural colour — the CMYK plate"),
    ("foil-primary", "Foil plate 1: ceremonial architecture"),
    ("foil-secondary", "Foil plate 2: fine ornamental registers"),
    ("emboss", "Blind emboss die: seal and institutional mark"),
    ("finetext", "Fine text ring — serial-bearing, 0.58mm (see spec §6)"),
    ("variable", "Variable data: serial, verification code, issue date"),
)


@dataclass
class Plate:
    """One finalist: named layers plus the type that sits on them."""

    key: str
    name: str
    intent: str
    scheme: Scheme
    ground: str
    ink: str
    accent: str
    paper: str = "#F7F2E6"
    layers: dict[str, list[str]] = field(default_factory=dict)
    defs: list[str] = field(default_factory=list)

    def add(self, separation: str, fragment: str) -> None:
        self.layers.setdefault(separation, []).append(fragment)

    def svg(self, only: str | None = None, *, backdrop: bool = True) -> str:
        order = [name for name, _ in SEPARATIONS if only in (None, name)]
        body = "".join("".join(self.layers.get(name, ())) for name in order)
        ground = (
            f'<rect x="0" y="0" width="{W}" height="{H}" fill="{self.ground}"/>'
            if backdrop else ""
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:g} {H:g}"'
            f' width="{W:g}mm" height="{H:g}mm" preserveAspectRatio="none"'
            ' aria-hidden="true" focusable="false">'
            + (f"<defs>{''.join(self.defs)}</defs>" if self.defs else "")
            + ground + body + "</svg>"
        )


def keep(text: str) -> str:
    """Non-breaking hyphen, so a surname never breaks across the peak line."""
    return text.replace("-", "‑")


# --- shared construction ------------------------------------------------------


def substrate(plate: Plate, *, screen: bool = True) -> None:
    """The layers under everything: fibres, and an anti-copy ruling.

    Both are honest about what they are — a cosmetic fibre field and a line
    screen set off a copier's own angles. Neither is a security guarantee, and
    both are on their own separations so a standard-print edition can simply not
    buy them.
    """
    sheet = geo.Rect(0, 0, W, H)
    plate.add("substrate", geo.fibres(sheet, seed=SERIAL, count=170))
    if screen:
        plate.defs.append(
            geo.line_screen("screen", degrees=8, pitch=0.46, width=0.07,
                            ink=plate.scheme.security.core, strength=0.16)
        )
        plate.add("security", f'<rect {sheet.attrs()} fill="url(#screen)"/>')


#: The content field, per plate, in sheet millimetres. Ornament is clipped out
#: of it by construction — see `Motif.field(keep_out=…)`. Kept beside the CSS
#: that positions the field so the two cannot drift apart unnoticed.
def content_field(left: float, right: float, top: float, bottom: float) -> geo.Rect:
    return geo.Rect(left, top, W - left - right, H - top - bottom)


def ground_figure(plate: Plate, cx: float, cy: float, radius: float,
                  *, strength: float = 0.030) -> None:
    """The family, at the optical centre, at the threshold of visibility.

    Reads at 5cm and disappears at 50cm, which is its job. It is the motif's
    largest appearance and the one nobody is meant to notice first.
    """
    plate.add("security", MOTIF.rosette(
        cx, cy, radius, ink=geo.tint(plate.accent, strength), width=0.30))
    plate.add("security", MOTIF.guilloche(
        cx, cy, radius * 0.82, ink=plate.accent, width=0.09,
        strength=strength * 1.15, passes=3))


def corner_architecture(plate: Plate, inset: float, size: float, *,
                        mass: str | None = None) -> None:
    """Four corners, each a manufactured object rather than a decoration.

    Three constructions, one family: a mitred bracket of mass, the motif's own
    rosette inset into it at 14mm, and a ring of the family's smallest star
    orbiting that. The bracket reads at 50cm, the rosette at 20cm and the ring
    at 5cm — one corner, three viewing distances.
    """
    s = plate.scheme
    for quadrant, (x, y) in enumerate((
        (inset, inset), (W - inset, inset),
        (W - inset, H - inset), (inset, H - inset),
    )):
        plate.add("process", arch.corner_block(
            x, y, size, quadrant=quadrant,
            mass=mass or geo.blend(plate.ink, plate.accent, 0.55),
            metal=s.primary, ink=plate.ink, inset_medallion=False))
        local = f'<g transform="translate({x:.2f} {y:.2f}) rotate({quadrant * 90})">'
        cxy = size * 0.30
        plate.add("foil-primary", local + MOTIF.rosette(
            cxy, cxy, size * 0.20, ink=s.primary.face, width=0.16) + "</g>")
        plate.add("foil-secondary", local + MOTIF.medallion_ring(
            cxy, cxy, size * 0.255, ink=s.secondary.face, width=0.10) + "</g>")


def seal(plate: Plate, cx: float, cy: float, radius: float) -> str:
    """The institutional seal, built into the architecture rather than placed.

    Five concentric jobs, on four separations, in the order a press lays them:
    a lathe field cut from the document's own specification, an embossed device
    that is the motif at seal scale, a struck metal rim, the legend engraved
    into the rim carrying this document's serial, and a ring of the family's
    smallest star closing the outside.

    Returned rather than added, so a plate can place it inside the flow of its
    execution band instead of pinning it to a coordinate.
    """
    s = plate.scheme
    device = MOTIF.rosette(cx, cy, radius * 0.46, ink=s.engraved.core,
                           width=0.30)
    return (
        MOTIF.guilloche(cx, cy, radius * 0.80, ink=s.security.core, width=0.07,
                        strength=0.85, passes=3)
        + f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="none"'
          f' stroke="{s.primary.face}" stroke-width="0.62"/>'
        + f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius * 0.955:.2f}"'
          f' fill="none" stroke="{s.primary.highlight}" stroke-width="0.20"/>'
        + f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius * 0.62:.2f}"'
          f' fill="none" stroke="{s.primary.shadow}" stroke-width="0.28"/>'
        + arch.legend_ring(cx, cy, radius * 0.80, metal=s.primary,
                           legend=SEAL_LEGEND, identifier=SERIAL)
        + MOTIF.medallion_ring(cx, cy, radius * 1.06, ink=s.secondary.face,
                               width=0.09)
        + arch.emboss(device, depth=0.22, light=s.primary.highlight,
                      dark=s.engraved.shadow)
    )


def institutional_mark(plate: Plate, cx: float, cy: float,
                       radius: float) -> str:
    """The motif at title scale, blind-embossed on the axis.

    The one place the family appears uninked. An emboss is the only mark on the
    sheet that is not a colour, which is why it is reserved for the institution
    rather than spent on ornament.
    """
    s = plate.scheme
    figure = (
        MOTIF.star(cx, cy, radius, ink=s.engraved.core, width=0.42)
        + MOTIF.polygram(cx, cy, radius * 0.74, ink=s.primary.core, width=0.26)
    )
    return arch.emboss(figure, depth=0.24, light=s.primary.highlight,
                       dark=s.engraved.shadow)


def divider(plate: Plate, *, width: float = 44.0) -> str:
    m = plate.scheme.secondary
    return (
        f'<svg class="divider" style="width:{width}%" viewBox="0 0 100 4"'
        ' preserveAspectRatio="none">'
        + arch.spreader(2.0, 1.0, 99.0, metal=m, stops=4)
        + "</svg>"
    )


def execution(plate: Plate, *, seal_radius: float = 15.0) -> str:
    """Seal, signatories, offices, authorities — and the verification panel.

    The band is a three-point balance, not a mirror: the seal anchors one end,
    the verification panel the other, three signatures between them. Each
    signatory carries a name in the display face, an engraved rule in the
    primary metal, the office at equal seriousness, and the authority under
    which that office signs — which is the line a foreign registrar actually
    reads and the line most certificates leave out.
    """
    s = plate.scheme
    d = seal_radius * 2 + 3
    cells = "".join(
        f'<div class="sig"><div class="disp nm">{name}</div>'
        f'<svg class="srule" viewBox="0 0 60 1.6" preserveAspectRatio="none">'
        f'{arch.engraved_metal_rule(1, 0.8, 59, 0.8, metal=s.primary, weight=0.34)}'
        "</svg>"
        f'<div class="lab of">{office}</div>'
        f'<div class="auth">{authority}</div></div>'
        for name, office, authority in SIGNATORIES
    )
    return (
        '<div class="exec">'
        f'<div class="sealbox"><svg viewBox="0 0 {d:.1f} {d:.1f}">'
        + seal(plate, d / 2, d / 2, seal_radius) + "</svg></div>"
        f'<div class="sigrow">{cells}</div>'
        '<div class="vpanel">'
        f'<div class="k">Credential</div><div class="v">{SERIAL}</div>'
        f'<div class="k">Issued</div><div class="v">{ISSUED}</div>'
        f'<div class="k">Verify</div><div class="v">{CODE}</div>'
        "</div></div>"
    )


def fine_text(plate: Plate, rect: geo.Rect, tag: str) -> None:
    """Serial-bearing text at 0.58mm around the register.

    **Not called microprint.** Security microprint is text at or below about
    0.25mm cap height, which is the size a photocopier cannot resolve; this is
    more than twice that and has not been measured on any press. It is a
    serial-bearing fine-text register, which is a real and useful thing — it
    ties the sheet to the record and it is tedious to reproduce — and it is not
    the thing the word microprint denotes. See the production specification §6.
    """
    plate.add("finetext", geo.fine_text_ring(
        rect, identifier=tag,
        text=f"{INSTITUTION.upper()} · {SERIAL} · {CODE} · ",
        ink=plate.ink, size=0.58, strength=0.30))


# --- the shell ----------------------------------------------------------------

BASE_CSS = """
@page { size: 297mm 210mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #221F1B; }
.wrap { padding: 8mm; }
.tag { font-family: 'Inter', sans-serif; font-size: 3.0mm; letter-spacing: 0.15em;
  text-transform: uppercase; color: #A79E8E; margin: 0 0 3mm 1mm; font-weight: 600; }
.tag b { color: #F2E9D8; font-weight: 700; }
.sheet { position: relative; width: 297mm; height: 210mm; overflow: hidden;
  box-shadow: 0 4mm 12mm rgba(0,0,0,0.45); }
.plate { position: absolute; inset: 0; }
.plate svg { display: block; width: 100%; height: 100%; }
.field { position: absolute; display: flex; flex-direction: column; }
.spacer { flex: 1 1 auto; min-height: 2.5mm; }
.divider { display: block; flex: none; height: 3mm; }
.mono { font-family: 'IBM Plex Mono', monospace; }
.lab { font-family: 'Inter', sans-serif; text-transform: uppercase; font-weight: 600; }
.exec { display: flex; align-items: flex-end; gap: 6mm; width: 100%; flex: none; }
.sigrow { flex: 1 1 auto; display: flex; align-items: flex-start; gap: 6mm; }
.sealbox { flex: none; width: 33mm; }
.sealbox svg { display: block; width: 100%; height: auto; }
.sig { flex: 1 1 0; text-align: center; }
/* A fixed box for the name, so the three engraved rules land on one
   baseline. Bottom-aligning the cells instead put the middle rule 4mm high
   the moment "Dean of the Graduate School" wrapped to two lines. */
.sig .nm { font-size: 3.8mm; height: 6.4mm; display: flex; align-items: flex-end;
  justify-content: center; white-space: nowrap; letter-spacing: 0.004em; }
.sig .srule { display: block; width: 100%; height: 1.6mm; }
.sig .of { font-family: 'Inter', sans-serif; text-transform: uppercase;
  font-weight: 600; font-size: 2.0mm; letter-spacing: 0.20em; margin-top: 1.2mm; }
.sig .auth { font-family: 'Source Serif 4', serif; font-size: 1.85mm;
  font-style: italic; margin-top: 0.6mm; }
.vpanel { flex: none; width: 34mm; text-align: right; }
.vpanel .k { font-family: 'Inter', sans-serif; font-size: 1.7mm;
  letter-spacing: 0.24em; text-transform: uppercase; }
.vpanel .v { font-family: 'IBM Plex Mono', monospace; font-size: 2.5mm;
  margin: 0.3mm 0 1.1mm; letter-spacing: 0.02em; }
.vpanel .v:last-child { margin-bottom: 0; }
.name, .name-ar { text-wrap: balance; }
.lockup { display: flex; align-items: center; justify-content: center;
  gap: 6mm; flex: none; width: 124%; margin: 0 -12%; }
.lockup .mark { flex: none; width: 15mm; }
.lockup .mark svg { display: block; width: 100%; height: auto; }
.lockup .en { text-align: right; flex: 1 1 0; }
.lockup .ar { text-align: left; flex: 1 1 0; direction: rtl; }
"""


def page(plate: Plate, body: str, css: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{plate.name} — {DEGREE}</title><style>"
        + font_face_css(embed=True) + BASE_CSS + css
        + '</style></head><body><div class="wrap">'
        + f'<p class="tag"><b>{plate.key} · {plate.name}</b> — {plate.intent}'
        f' · motif {{{MOTIF.order}/{MOTIF.density}}} · lathe {MOTIF.lathe}</p>'
        + f'<div class="sheet" style="background:{plate.ground}">'
        f'<div class="plate">{plate.svg()}</div>{body}</div>'
        + "</div></body></html>"
    )


def lockup(plate: Plate, *, en_size: float, ar_size: float,
           mark_radius: float = 6.4) -> str:
    """Arabic and Latin as one object, either side of the institution's mark.

    Not English with a translation beneath it. The two names sit on one
    baseline at optically matched sizes — the Arabic set larger, because naskh
    at the same nominal size reads smaller than a Latin capital — flanking the
    embossed mark. Neither script can be removed without destroying the lockup,
    which is the test of whether a bilingual design is bilingual.
    """
    d = mark_radius * 2 + 3
    return (
        '<div class="lockup">'
        f'<div class="disp en" style="font-size:{en_size:.2f}mm">{INSTITUTION}</div>'
        f'<div class="mark"><svg viewBox="0 0 {d:.1f} {d:.1f}">'
        + institutional_mark(plate, d / 2, d / 2, mark_radius) + "</svg></div>"
        f'<div class="ar" style="font-size:{ar_size:.2f}mm">{INSTITUTION_AR}</div>'
        "</div>"
    )


# =============================================================================
# M02 — IMPERIAL ISLAMIC
# =============================================================================
#
# ZONES (mm from trim)     0–6 security margin · 6–7 metal rule · 7–20 motif
# field in midnight · 20–25 interlace register · 25–28 rule and quiet · 28+
# ivory ceremonial panel on cut corners. Nothing crosses a boundary.
#
# DEPTH   1 m: the midnight band and the ivory panel cut into it.
#         50 cm: the corner rosettes, the lockup, the peak.
#         20 cm: the interlace straps, the kites, the seal's rim.
#         5 cm: the lathe petals, the construction polygram, the fine text.


def m02() -> tuple[Plate, str, str]:
    plate = Plate(
        key="M02", name="Imperial Islamic",
        intent="a midnight strapwork border with an ivory field cut into it",
        scheme=scheme_for("imperial"), ground="#F5F0E2", ink="#0E1B33",
        accent="#0E1B33",
    )
    s = plate.scheme
    sheet = geo.Rect(0, 0, W, H)
    substrate(plate)

    band = sheet.inset(6.0)
    plate.add("process", f'<rect {band.attrs()} fill="{plate.accent}"/>')
    # The border is the document's own family, not a pattern applied to it.
    plate.add("foil-primary", MOTIF.field(
        band, cell=11.5, ink=s.primary.face, strength=1.0, width=0.17,
        hollow=22.0))
    plate.add("foil-secondary", MOTIF.field(
        band.inset(13.0), cell=6.4, ink=s.secondary.face, strength=1.0,
        width=0.09, hollow=9.0))
    plate.add("foil-primary", arch._perimeter_rule(band, metal=s.primary,
                                                   weight=0.55))
    plate.add("security", geo.guilloche_band(
        band.inset(20.4), ink=s.security.core, width=0.07, strength=0.9,
        amplitude=1.0, waves=int(W / 1.9)))

    panel = band.inset(22.0)
    plate.add("process", (
        f'<path d="{arch.stepped_rect_path(panel, cut=13.0)}"'
        f' fill="{plate.ground}"/>'
    ))
    plate.add("foil-primary", (
        f'<path d="{arch.stepped_rect_path(panel, cut=13.0)}" fill="none"'
        f' stroke="{s.primary.face}" stroke-width="0.70"/>'
        f'<path d="{arch.stepped_rect_path(panel.inset(1.5), cut=12.0)}"'
        f' fill="none" stroke="{s.engraved.shadow}" stroke-width="0.22"/>'
    ))
    # The panel's four cut corners are where the family resolves: a rosette on
    # the mitre, a construction polygram inside it, a ring of stars outside.
    for quadrant, (x, y) in enumerate((
        (panel.x, panel.y), (panel.x + panel.w, panel.y),
        (panel.x + panel.w, panel.y + panel.h), (panel.x, panel.y + panel.h),
    )):
        local = f'<g transform="translate({x:.2f} {y:.2f}) rotate({quadrant * 90})">'
        plate.add("foil-primary", local + MOTIF.rosette(
            0, 0, 7.4, ink=s.primary.face, width=0.26) + "</g>")
        plate.add("foil-secondary", local + MOTIF.polygram(
            0, 0, 4.4, ink=s.secondary.face, width=0.16) + "</g>")

    ground_figure(plate, W / 2, H * 0.50, 52, strength=0.026)
    fine_text(plate, sheet.inset(9.0), "m02")

    css = f"""
.field {{ left: 47mm; right: 47mm; top: 37mm; bottom: 37mm; align-items: center;
  text-align: center; }}
.disp {{ font-family: 'Fraunces', Georgia, serif; }}
.ar {{ font-family: 'Amiri', serif; direction: rtl; }}
.lockup .en {{ letter-spacing: 0.11em; text-transform: uppercase;
  color: {plate.accent}; font-weight: 600; line-height: 1.24; }}
.lockup .ar {{ color: {plate.accent}; font-weight: 700; line-height: 1.5; }}
.conf {{ font-size: 2.5mm; letter-spacing: 0.36em; color: {geo.tint(plate.ink, 0.58)};
  flex: none; }}
.name {{ font-family: 'Fraunces', Georgia, serif; font-size: 12.6mm;
  font-weight: 600; line-height: 1.08; letter-spacing: -0.006em;
  color: {plate.ink}; flex: none; margin-top: 2.2mm; }}
.name-ar {{ font-family: 'Amiri', serif; direction: rtl; font-size: 5.8mm;
  font-weight: 700; color: {plate.accent}; line-height: 1.5; flex: none;
  margin-top: 2.0mm; }}
.degwrap {{ display: flex; align-items: baseline; justify-content: center;
  gap: 6mm; flex: none; margin-top: 3.4mm; }}
.deg {{ font-family: 'Fraunces', Georgia, serif; font-size: 6.6mm;
  letter-spacing: 0.155em; text-transform: uppercase; font-weight: 600;
  color: {s.engraved.shadow}; }}
.deg-ar {{ font-family: 'Amiri', serif; direction: rtl; font-size: 5.6mm;
  font-weight: 700; color: {s.engraved.shadow}; }}
.study {{ font-family: 'Fraunces', Georgia, serif; font-size: 4.0mm;
  font-style: italic; color: {geo.tint(plate.ink, 0.84)}; flex: none;
  margin-top: 1.6mm; letter-spacing: 0.008em; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.95mm;
  line-height: 1.68; max-width: 74%; color: {geo.tint(plate.ink, 0.78)};
  flex: none; margin-top: 3.0mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm, .vpanel .v {{ color: {plate.ink}; }}
.sig .of {{ color: {geo.tint(plate.accent, 0.95)}; }}
.sig .auth, .vpanel .k {{ color: {geo.tint(plate.ink, 0.52)}; }}
"""
    body = f"""
<div class="field">
  {lockup(plate, en_size=3.5, ar_size=4.6)}
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="name-ar">{RECIPIENT_AR}</div>
  <div class="degwrap"><span class="deg">{DEGREE}</span>
    <span class="deg-ar">{DEGREE_AR}</span></div>
  <div class="study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(plate)}
  <div class="spacer"></div>
  {execution(plate)}
</div>
"""
    return plate, body, css


# =============================================================================
# M11 — CRIMSON IMPERIAL
# =============================================================================
#
# ZONES  0–5.5 security margin · 5.5–6 metal rule · 6–24 crimson motif field ·
# 24–25 quiet · 25+ ivory ceremonial panel with shouldered corners. Corner
# brackets straddle 5.5–30 and are the only element allowed to.
#
# DEPTH  1 m: crimson mass, gold architecture, the ivory cartouche.
#        50 cm: corner brackets, the cresting medallion, the peak.
#        20 cm: the spines, the kites, the engraved shoulders.
#        5 cm: the lathe, the polygram, the fine text, the fibres.


def m11() -> tuple[Plate, str, str]:
    plate = Plate(
        key="M11", name="Crimson Imperial",
        intent="crimson mass, gold architecture, one bright ceremonial centre",
        scheme=scheme_for("crimson"), ground="#F7F1E4", ink="#2A0E18",
        accent="#5A1226",
    )
    s = plate.scheme
    sheet = geo.Rect(0, 0, W, H)
    substrate(plate, screen=False)

    band = sheet.inset(5.5)
    plate.add("process", f'<rect {band.attrs()} fill="{plate.accent}"/>')
    plate.add("foil-secondary", MOTIF.field(
        band, cell=8.8, ink=s.secondary.highlight, strength=0.80, width=0.11,
        hollow=19.0))
    plate.add("foil-primary", arch._perimeter_rule(band, metal=s.primary,
                                                   weight=0.62))
    inner = band.inset(19.0)
    plate.add("process", (
        f'<path d="{arch.stepped_rect_path(inner, cut=11.0, step=2.4)}"'
        f' fill="{plate.ground}"/>'
    ))
    plate.add("foil-primary", (
        f'<path d="{arch.stepped_rect_path(inner, cut=11.0, step=2.4)}"'
        f' fill="none" stroke="{s.primary.face}" stroke-width="0.72"/>'
        f'<path d="{arch.stepped_rect_path(inner.inset(1.7), cut=10.2, step=2.2)}"'
        f' fill="none" stroke="{s.engraved.shadow}" stroke-width="0.22"/>'
    ))
    corner_architecture(plate, 5.5, 26.0,
                        mass=geo.blend(plate.ink, plate.accent, 0.60))
    for cx in (band.x + 9.5, band.x + band.w - 9.5):
        plate.add("foil-secondary", arch.vertical_spine(
            cx, band.y + 36, band.y + band.h - 36, metal=s.secondary, nodes=3))
    plate.add("foil-primary", arch.cresting(W / 2, inner.y, 58, 12.5,
                                            metal=s.primary))
    ground_figure(plate, W / 2, H * 0.52, 50, strength=0.028)
    fine_text(plate, sheet.inset(8.4), "m11")

    cart = geo.Rect(3.0, 3.0, 170.0, 22.0)
    plaque = (
        '<svg class="cart" viewBox="0 0 176 28" preserveAspectRatio="none">'
        f'<path d="{arch.cartouche_path(cart, arch=3.6, cut=7.0)}"'
        f' fill="{plate.paper}" stroke="{s.primary.face}" stroke-width="0.6"/>'
        f'<path d="{arch.cartouche_path(cart.inset(1.5), arch=3.2, cut=6.2)}"'
        f' fill="none" stroke="{s.engraved.shadow}" stroke-width="0.2"/></svg>'
    )
    css = f"""
.field {{ left: 42mm; right: 42mm; top: 34mm; bottom: 28mm; align-items: center;
  text-align: center; }}
.disp {{ font-family: 'Fraunces', Georgia, serif; }}
.ar {{ font-family: 'Amiri', serif; direction: rtl; }}
.lockup .en {{ letter-spacing: 0.13em; text-transform: uppercase;
  color: {plate.accent}; font-weight: 600; line-height: 1.24; }}
.lockup .ar {{ color: {plate.accent}; font-weight: 700; line-height: 1.5; }}
.conf {{ font-size: 2.4mm; letter-spacing: 0.36em; color: {geo.tint(plate.ink, 0.58)};
  flex: none; }}
.namewrap {{ position: relative; flex: none; margin-top: 2.4mm; width: 106%;
  display: flex; align-items: center; justify-content: center; }}
.cart {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
.name {{ position: relative; font-family: 'Fraunces', Georgia, serif;
  font-size: 12.2mm; font-weight: 600; line-height: 1.06; color: {plate.ink};
  padding: 3.2mm 7mm; letter-spacing: -0.006em; }}
.name-ar {{ font-family: 'Amiri', serif; direction: rtl; font-size: 5.5mm;
  color: {plate.accent}; line-height: 1.5; flex: none; margin-top: 2.0mm; }}
.deg {{ font-family: 'Fraunces', Georgia, serif; font-size: 6.4mm;
  letter-spacing: 0.16em; text-transform: uppercase; font-weight: 600;
  color: {s.engraved.shadow}; flex: none; margin-top: 3.0mm; }}
.study {{ font-family: 'Fraunces', Georgia, serif; font-size: 3.9mm;
  font-style: italic; color: {geo.tint(plate.ink, 0.84)}; flex: none;
  margin-top: 1.5mm; }}
.dist {{ font-size: 2.2mm; letter-spacing: 0.26em; color: {plate.accent};
  flex: none; margin-top: 2.2mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.85mm;
  line-height: 1.66; max-width: 92%; color: {geo.tint(plate.ink, 0.76)};
  flex: none; margin-top: 2.4mm; }}
.exec {{ margin-top: 3mm; }}
.sig .nm, .vpanel .v {{ color: {plate.ink}; }}
.sig .of {{ color: {geo.tint(plate.accent, 0.92)}; }}
.sig .auth, .vpanel .k {{ color: {geo.tint(plate.ink, 0.52)}; }}
"""
    body = f"""
<div class="field">
  {lockup(plate, en_size=3.8, ar_size=4.7)}
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="namewrap">{plaque}<span class="disp name">{keep(RECIPIENT)}</span></div>
  <div class="name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="study">{STUDY}</div>
  <div class="lab dist">{DISTINCTION}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(plate)}
  <div class="spacer"></div>
  {execution(plate)}
</div>
"""
    return plate, body, css


# =============================================================================
# M12 — EDIRASX SIGNATURE
# =============================================================================
#
# ZONES  0–5 security margin · 5–16 dense lattice · 16–28 second density ·
# 28–42 third · 42+ fourth, dissolving into the ceremonial field. The frame has
# no inner edge; it thins. Corner brackets are the only hard boundary.
#
# DEPTH  1 m: the density gradient — dark at the trim, open at the centre.
#        50 cm: the corner blocks, the embossed mark, the credential register.
#        20 cm: the individual rosettes resolving out of the field.
#        5 cm: the polygram construction inside each rosette, the fine text.


def m12() -> tuple[Plate, str, str]:
    plate = Plate(
        key="M12", name="EdirasX Signature",
        intent="one construction for frame and field: the lattice dissolving "
               "from trim to centre",
        scheme=scheme_for("signature"), ground="#F7F2E6", ink="#0A101C",
        accent="#132038",
    )
    s = plate.scheme
    sheet = geo.Rect(0, 0, W, H)
    substrate(plate)

    # Four densities. The value range is what makes the dissolve legible; when
    # the bands sat within a factor of six of each other the frame read as one
    # even lattice and the concept did not appear at all.
    field = content_field(43, 43, 33, 30)
    for inset, cell, strength, width, metal in (
        (5.0, 7.0, 1.000, 0.20, s.primary),
        (15.0, 12.0, 0.460, 0.13, s.primary),
        (27.0, 21.0, 0.200, 0.09, s.secondary),
        (39.0, 33.0, 0.085, 0.075, s.secondary),
    ):
        target = "foil-primary" if metal is s.primary else "foil-secondary"
        plate.add(target, MOTIF.field(
            sheet.inset(inset), cell=cell, ink=metal.core, strength=strength,
            width=width, hollow=11.0, keep_out=field.inset(-3.0)))
    plate.add("foil-primary", arch._perimeter_rule(sheet.inset(5.0),
                                                   metal=s.primary, weight=0.62))
    plate.add("foil-secondary", arch._perimeter_rule(sheet.inset(15.0),
                                                     metal=s.secondary,
                                                     weight=0.28))
    corner_architecture(plate, 5.0, 23.0)
    ground_figure(plate, W / 2, H * 0.47, 54, strength=0.028)
    fine_text(plate, sheet.inset(9.6), "m12")

    css = f"""
.field {{ left: 43mm; right: 43mm; top: 33mm; bottom: 30mm; align-items: center;
  text-align: center; }}
.disp {{ font-family: 'Source Serif 4', Georgia, serif; }}
.ar {{ font-family: 'Amiri', serif; direction: rtl; }}
.lockup .en {{ letter-spacing: 0.14em; text-transform: uppercase;
  color: {plate.accent}; font-weight: 700; line-height: 1.26;
  font-family: 'Source Serif 4', serif; }}
.lockup .ar {{ color: {plate.accent}; font-weight: 700; line-height: 1.5; }}
.conf {{ font-size: 2.4mm; letter-spacing: 0.36em; color: {geo.tint(plate.ink, 0.58)};
  flex: none; }}
.name {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 13.2mm;
  font-weight: 600; line-height: 1.06; letter-spacing: -0.010em;
  color: {plate.ink}; flex: none; margin-top: 2.4mm; }}
.name-ar {{ font-family: 'Amiri', serif; direction: rtl; font-size: 6.0mm;
  font-weight: 700; color: {plate.accent}; line-height: 1.5; flex: none;
  margin-top: 2.0mm; }}
.deg {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 6.8mm;
  letter-spacing: 0.15em; text-transform: uppercase; font-weight: 600;
  color: {s.engraved.shadow}; flex: none; margin-top: 3.2mm; }}
.study {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 4.0mm;
  font-style: italic; color: {geo.tint(plate.ink, 0.84)}; flex: none;
  margin-top: 1.6mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 2.9mm;
  line-height: 1.66; max-width: 76%; color: {geo.tint(plate.ink, 0.78)};
  flex: none; margin-top: 2.8mm; }}
.exec {{ margin-top: 3mm; padding-top: 2.4mm;
  border-top: 0.28mm solid {s.secondary.face}; }}
.sig .nm, .vpanel .v {{ color: {plate.ink}; }}
.sig .of {{ color: {geo.tint(plate.accent, 0.92)}; }}
.sig .auth, .vpanel .k {{ color: {geo.tint(plate.ink, 0.52)}; }}
"""
    body = f"""
<div class="field">
  {lockup(plate, en_size=3.6, ar_size=4.7, mark_radius=7.4)}
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="study">{STUDY}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(plate)}
  <div class="spacer"></div>
  {execution(plate)}
</div>
"""
    return plate, body, css


# =============================================================================
# M01 — ROYAL PALACE
# =============================================================================
#
# ZONES  0–5.5 security margin · 5.5–6.2 metal rule · 6.2–8.2 quiet ·
# 8.2–12.6 navy field register · 12.6–13.1 rule · 13.1–19.1 motif register ·
# 19.1–20.5 quiet and rule · 20.5–24 quiet · 24+ stepped architrave, then the
# ceremonial field. Six registers, each with a job, none of equal weight.
#
# DEPTH  1 m: the doorcase — navy mass, gold architrave, the crest on the axis.
#        50 cm: corner brackets, cresting medallion, spreaders, the peak.
#        20 cm: the architrave's shoulders, the corner rosettes, the seal rim.
#        5 cm: the motif register, the lathe, the fine text.


def m01() -> tuple[Plate, str, str]:
    plate = Plate(
        key="M01", name="Royal Palace",
        intent="a palace doorcase: mass at the corners, a stepped architrave, "
               "a crest breaking the line",
        scheme=scheme_for("palace"), ground="#F7F2E6", ink="#101826",
        accent="#14294C",
    )
    s = plate.scheme
    sheet = geo.Rect(0, 0, W, H)
    substrate(plate)

    stack, inner = arch.register_stack(
        sheet.inset(5.5),
        ((0.7, "rule"), (2.0, "void"), (4.4, "field"), (0.5, "rule"),
         (6.0, "void"), (1.4, "void"), (0.45, "rule")),
        metal=s.primary, ink=plate.accent,
    )
    plate.add("process", stack)
    # The register the stack left as `void` is the motif's, drawn here so it
    # lands on the ornamental foil rather than on the structural plate.
    plate.add("foil-secondary", MOTIF.field(
        sheet.inset(13.1), cell=6.0, ink=s.secondary.core, strength=0.62,
        width=0.085, hollow=6.0,
        keep_out=content_field(37, 37, 44, 34).inset(-3.0)))

    architrave = inner.inset(2.6)
    plate.add("foil-primary", (
        f'<path d="{arch.stepped_rect_path(architrave, cut=9.0, step=2.2)}"'
        f' fill="none" stroke="{s.primary.face}" stroke-width="0.62"/>'
        f'<path d="{arch.stepped_rect_path(architrave.inset(1.1), cut=8.2, step=2.0)}"'
        f' fill="none" stroke="{s.engraved.shadow}" stroke-width="0.20"/>'
    ))
    corner_architecture(plate, 5.5, 30.0)
    plate.add("foil-primary", arch.cresting(W / 2, inner.y, 62, 13.0,
                                            metal=s.primary))
    plate.add("foil-secondary", arch.spreader(
        inner.y + 17.0, inner.x + 18, W / 2 - 30, metal=s.secondary, stops=3))
    plate.add("foil-secondary", arch.spreader(
        inner.y + 17.0, W / 2 + 30, inner.x + inner.w - 18, metal=s.secondary,
        stops=3))
    ground_figure(plate, W / 2, H * 0.50, 56, strength=0.026)
    fine_text(plate, sheet.inset(9.0), "m01")

    css = f"""
.field {{ left: 37mm; right: 37mm; top: 44mm; bottom: 34mm; align-items: center;
  text-align: center; }}
.disp {{ font-family: 'Fraunces', Georgia, serif; }}
.ar {{ font-family: 'Amiri', serif; direction: rtl; }}
.lockup .en {{ letter-spacing: 0.12em; text-transform: uppercase;
  color: {plate.accent}; font-weight: 600; line-height: 1.24; }}
.lockup .ar {{ color: {plate.accent}; font-weight: 700; line-height: 1.5; }}
.conf {{ font-size: 2.5mm; letter-spacing: 0.38em; color: {geo.tint(plate.ink, 0.60)};
  flex: none; }}
.name {{ font-family: 'Fraunces', Georgia, serif; font-size: 13.0mm;
  font-weight: 600; line-height: 1.07; letter-spacing: -0.006em;
  color: {plate.ink}; flex: none; margin-top: 2.4mm; }}
.name-ar {{ font-family: 'Amiri', serif; direction: rtl; font-size: 5.8mm;
  color: {geo.tint(plate.accent, 0.94)}; line-height: 1.5; flex: none;
  margin-top: 2.0mm; }}
.deg {{ font-family: 'Fraunces', Georgia, serif; font-size: 7.0mm;
  letter-spacing: 0.145em; text-transform: uppercase; font-weight: 600;
  color: {s.engraved.shadow}; flex: none; margin-top: 3.4mm; }}
.study {{ font-family: 'Fraunces', Georgia, serif; font-size: 4.1mm;
  font-style: italic; color: {geo.tint(plate.ink, 0.84)}; flex: none;
  margin-top: 1.7mm; }}
.dist {{ font-size: 2.3mm; letter-spacing: 0.28em; color: {plate.accent};
  flex: none; margin-top: 2.4mm; }}
.stmt {{ font-family: 'Source Serif 4', serif; font-size: 3.0mm;
  line-height: 1.68; max-width: 72%; color: {geo.tint(plate.ink, 0.80)};
  flex: none; margin-top: 3.0mm; }}
.exec {{ margin-top: 3.5mm; }}
.sig .nm, .vpanel .v {{ color: {plate.ink}; }}
.sig .of {{ color: {geo.tint(plate.accent, 0.92)}; }}
.sig .auth, .vpanel .k {{ color: {geo.tint(plate.ink, 0.52)}; }}
"""
    body = f"""
<div class="field">
  {lockup(plate, en_size=3.7, ar_size=4.7)}
  <div class="spacer"></div>
  <div class="lab conf">{CONFERRAL}</div>
  <div class="disp name">{keep(RECIPIENT)}</div>
  <div class="name-ar">{RECIPIENT_AR}</div>
  <div class="disp deg">{DEGREE}</div>
  <div class="study">{STUDY}</div>
  <div class="lab dist">{DISTINCTION}</div>
  <div class="stmt">{STATEMENT}</div>
  <div class="spacer"></div>
  {divider(plate)}
  <div class="spacer"></div>
  {execution(plate)}
</div>
"""
    return plate, body, css


FINALISTS = (m02, m11, m12, m01)


def measured_separations(page_path: pathlib.Path, plate: Plate) -> None:
    """The emboss die and the variable-data layer, at their *measured* positions.

    The seal, the institutional mark and the verification panel are placed by
    the flow, not by a coordinate — which is exactly what keeps a long name from
    landing on top of them. That means their sheet positions are a *result*, and
    a separation drawn from guessed coordinates would be a separation of a
    different document.

    So the page is rendered, the boxes are read back in CSS pixels, converted at
    96 px per inch to millimetres, and the die geometry is emitted where it
    actually sits. A printer receiving `--emboss.svg` gets the die outline in
    register with the artwork rather than approximately near it.
    """
    from playwright.sync_api import sync_playwright

    chrome = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
    per_mm = 96.0 / 25.4
    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=chrome)
        context = browser.new_context(viewport={"width": 1400, "height": 1000})
        view = context.new_page()
        view.goto(page_path.resolve().as_uri())
        view.wait_for_timeout(700)
        sheet = view.locator(".sheet").first.bounding_box()
        boxes = {}
        for key, selector in (("seal", ".sealbox svg"),
                              ("mark", ".lockup .mark svg"),
                              ("vpanel", ".vpanel")):
            found = view.locator(selector).first
            boxes[key] = found.bounding_box() if found.count() else None
        browser.close()

    def to_mm(box):
        return geo.Rect((box["x"] - sheet["x"]) / per_mm,
                        (box["y"] - sheet["y"]) / per_mm,
                        box["width"] / per_mm, box["height"] / per_mm)

    s = plate.scheme
    if boxes["seal"]:
        r = to_mm(boxes["seal"])
        radius = min(r.w, r.h) / 2 * 0.87
        plate.add("emboss", arch.emboss(
            MOTIF.rosette(r.cx, r.cy, radius * 0.46, ink=s.engraved.core,
                          width=0.30),
            depth=0.24, light=s.primary.highlight, dark=s.engraved.shadow))
        plate.add("emboss",
                  f'<circle cx="{r.cx:.2f}" cy="{r.cy:.2f}" r="{radius:.2f}"'
                  f' fill="none" stroke="{s.engraved.shadow}"'
                  ' stroke-width="0.30" stroke-dasharray="1.2 0.8"/>')
    if boxes["mark"]:
        r = to_mm(boxes["mark"])
        radius = min(r.w, r.h) / 2 * 0.86
        plate.add("emboss", arch.emboss(
            MOTIF.star(r.cx, r.cy, radius, ink=s.engraved.core, width=0.42)
            + MOTIF.polygram(r.cx, r.cy, radius * 0.74, ink=s.primary.core,
                             width=0.26),
            depth=0.24, light=s.primary.highlight, dark=s.engraved.shadow))
    if boxes["vpanel"]:
        r = to_mm(boxes["vpanel"])
        plate.add("variable", (
            f'<rect {r.attrs()} fill="none" stroke="{s.engraved.shadow}"'
            ' stroke-width="0.20" stroke-dasharray="1.5 1.0"/>'
            f'<text x="{r.x:.2f}" y="{r.y - 1.4:.2f}" font-size="1.9"'
            f' font-family="Inter, sans-serif" fill="{s.engraved.shadow}">'
            f'VARIABLE DATA · {SERIAL} · {CODE} · {ISSUED}</text>'
        ))


def specification(plate: Plate) -> str:
    """The print specification, generated from the plate the artwork is.

    Not written alongside the design — *derived from it*. A specification
    maintained by hand drifts from the artwork within two revisions, and the
    drift is discovered by a printer, at cost. Everything below is read off the
    same objects the plate is drawn from.
    """
    s = plate.scheme
    rows = "\n".join(
        f"| {name} | {description} |"
        for name, description in SEPARATIONS if plate.layers.get(name)
    )
    metals = "\n".join(
        f"| {role} | {metal.name} | `{metal.face}` | {metal.process} | "
        f"{metal.foil_reference} |"
        for role, metal in (
            ("Primary — ceremonial architecture", s.primary),
            ("Secondary — fine ornamental registers", s.secondary),
            ("Engraved — shadow and relief", s.engraved),
            ("Security — fine ruling and text", s.security),
            ("Heritage — ornament", s.heritage),
        )
    )
    return f"""# {plate.key} · {plate.name} — production specification

*{plate.intent}*

Generated from `tools/design/masterpiece.py`. Do not edit by hand: regenerate.

## 1 · Finished piece

| | |
|---|---|
| Trim | {W:g} × {H:g} mm (A4 landscape) |
| Bleed | 3 mm all round |
| Safe edge | 6 mm from trim — nothing is drawn inside it |
| Cutting tolerance | ±1.5 mm |
| Recommended edition | Royal or Flagship (see EDTECHX_PRODUCTION_SPEC.md §2) |

## 2 · Geometric family

This document's ornament is one family, appearing at six scales. A printer
replacing a damaged plate needs these six numbers, not a traced outline.

| | |
|---|---|
| Order | {MOTIF.order}-fold |
| Star | {{{MOTIF.order}/{MOTIF.density}}} — inner/outer radius {MOTIF.ratio:.4f} |
| Phase | {MOTIF.phase:.4f} rad off the sheet axis |
| Lathe | R={MOTIF.lathe[0]}, r={MOTIF.lathe[1]}, pen={MOTIF.lathe[2]} |
| Lathe result | {MOTIF.lobes} lobes, closing after {MOTIF.lathe[1]} turns |
| Interlace | {MOTIF.braid} crossings per repeat |
| Derived from | {MOTIF.provenance} |

The lobe count is a whole multiple of the order
({MOTIF.lobes} = {MOTIF.lobes // MOTIF.order} × {MOTIF.order}), which is why the lathe work and the
star work read as one hand. R and r are coprime, so the figure closes only
after {MOTIF.lathe[1]} turns and cannot be approximated by a shorter one.

## 3 · Structural colour

| Role | Value |
|---|---|
| Ground | `{plate.ground}` |
| Ink | `{plate.ink}` |
| Accent | `{plate.accent}` |

Three structural colours, plus the metals. No fourth.

## 4 · Metals

| Role | Metal | Face | Process | Reference |
|---|---|---|---|---|
{metals}

Two foil passes: primary and secondary. Everything else is process ink or a die.

## 5 · Separations supplied

| File suffix | Contents |
|---|---|
{rows}

Each is a standalone SVG in millimetre user units at the trim size, in register.
The emboss and variable-data layers are emitted at *measured* positions read
back from the rendered page, because those elements are placed by the layout and
their coordinates are a result rather than an input.

## 6 · Linework

| Element | Weight |
|---|---|
| Fine text and micro-texture | 0.07–0.09 mm |
| Fine register | 0.09–0.20 mm |
| Engraved rule | three flat strokes, 0.28–0.72 mm overall |
| Frame register | 0.55–0.72 mm |

No opacity on any line, at any weight. Every pale tone is a flat pre-mixed ink.

## 7 · Fine text — measured, and not microprint

The serial-bearing ring is set at 0.58 mm, ≈0.41 mm cap height. Rasterised from
this artwork:

* **300 DPI** — 6.85 px per em. Illegible; the register reads as grey texture.
* **600 DPI** — 13.7 px per em. Legible; serial and verification code read back.

It is therefore **fine text, not microprint**. Security microprint means a cap
height at or below about 0.25 mm, chosen so a loupe resolves it and a copier
cannot; this is well above that and does not have that property. Any 300 DPI
edition must not describe this register as carrying readable data. No press test
has been run — see §9.

## 8 · Finishing

| Process | Where | Die |
|---|---|---|
| Hot foil, pass 1 | `--foil-primary.svg` | Yes |
| Hot foil, pass 2 | `--foil-secondary.svg` | Yes |
| Blind emboss | `--emboss.svg` — seal and institutional mark | Male/female pair |
| Serial numbering | `--variable.svg` | Numbering box |

## 9 · Not yet validated

Nothing here has been printed. This environment has no press, no paper and no
loupe, so the following are **unverified**: foil adhesion and register on cotton
stock; emboss depth and whether the die holds the {MOTIF.order}-fold device at
seal scale; whether any press holds the 0.07 mm hairlines; whether the fine-text ring
survives a real 600 DPI output rather than a rasterised preview; how the metals
read under daylight, warm indoor light and raking light; and what the sheet
looks like from the back. Until a proof exists, every statement in §7 and §8 is
a specification, not a result.
"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for build in FINALISTS:
        plate, body, css = build()
        slug = f"{plate.key.lower()}-{plate.name.lower().replace(' ', '-')}"
        page_path = OUT / f"{slug}.html"
        page_path.write_text(page(plate, body, css), encoding="utf-8")
        measured_separations(page_path, plate)
        # Every separation on its own, as a printer receives it. A layer that
        # cannot stand alone was never a separation.
        for name, description in SEPARATIONS:
            if not plate.layers.get(name):
                continue
            (OUT / f"{slug}--{name}.svg").write_text(
                f"<!-- {plate.name}: {description} -->"
                + plate.svg(only=name, backdrop=False),
                encoding="utf-8",
            )
        (OUT / f"{slug}--specification.md").write_text(
            specification(plate), encoding="utf-8")
        made = [n for n, _ in SEPARATIONS if plate.layers.get(n)]
        print(f"{slug:32s} {len(made)} separations + specification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
