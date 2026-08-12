"""Six plates that could become an institution's permanent visual identity.

Not concepts. Six finished architectures, each composed **onto press plates**
from the first stroke, each derived from a compositional tradition rather than
from the engine's own habits, and each judged by one question:

    If this institution ordered ten thousand copies on premium cotton stock
    with foil and emboss, would it arrive looking like a final production piece
    from a world-class security printer?

Three proofs are produced for each, and the second is the one that matters most.

1. **The sheet.** Full size, on paper geometry, with the specimen data.
2. **The identity proof — every word removed.** If two of the six are
   indistinguishable with the text gone, the ornament was decoration and the
   personality was a colourway. This is the test the previous work would have
   failed: twenty-four documents that were one composition six times.
3. **The separations.** Each plate alone, in black on white, because that is
   what a printer looks at. A foil plate judged in gold on ivory is a
   simulation being judged, not a plate.

Run: ``python tools/design/masterpieces.py``
"""

from __future__ import annotations

import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))

from app.modules.design import geometry as geo
from app.modules.design.gilding import SCHEMES, foil_gradient
from app.modules.design.personality import PERSONALITIES, Personality
from app.modules.design.press import Press
from app.modules.design.signature import Motif, motif_for
from app.modules.design.typeface import font_face_css

sys.path.insert(0, str(ROOT))
from tools.design.render import contact, shoot

OUT = ROOT / "docs" / "edtechx" / "design" / "masterpieces-vi"
W, H = 297.0, 210.0

INSTITUTION = "Meridian Institute of Advanced Study"
RECIPIENT = "Fatimah Adenike Oyelaran-Balogun"
SERIAL = "MIA/2026/000417"


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# --- ornament that descends from the institution -----------------------------


def arms(motif: Motif, cx: float, cy: float, r: float, ink: str) -> str:
    """The institution's arms, constructed from its own motif.

    Not a shield with a shape put inside it. The shield's proportions, the
    charge, the ordinary and the ring all come from one `Motif`, so two
    institutions cannot arrive at the same arms and one institution's arms are
    the same object at every scale it is drawn.
    """
    width = r * 5 / 3
    top, bottom = cy - r, cy + r * 1.28
    flank = top + (bottom - top) * 0.42
    shield = (
        f"M{cx - width / 2:.2f} {top:.2f} H{cx + width / 2:.2f} "
        f"V{flank:.2f} Q{cx + width / 2:.2f} {bottom - r * 0.22:.2f} "
        f"{cx:.2f} {bottom:.2f} "
        f"Q{cx - width / 2:.2f} {bottom - r * 0.22:.2f} "
        f"{cx - width / 2:.2f} {flank:.2f} Z"
    )
    parts = [
        f'<path d="{shield}" fill="none" stroke="{ink}" stroke-width="0.5"/>',
        # A chief, and the motif's own star on it — the charge is derived,
        # never chosen.
        f'<path d="M{cx - width / 2:.2f} {top + r * 0.34:.2f} '
        f'H{cx + width / 2:.2f}" stroke="{ink}" stroke-width="0.32"/>',
        motif.star(cx, top + r * 0.17, r * 0.14, ink=ink, width=0.26),
        motif.rosette(cx, cy + r * 0.18, r * 0.62, ink=ink, width=0.13),
    ]
    return "".join(parts)


def shamsa(motif: Motif, cx: float, cy: float, r: float, ink: str,
           metal: str) -> str:
    """A sun medallion: the motif's polygram inside its own ring of stars."""
    parts = [
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none"'
        f' stroke="{metal}" stroke-width="0.55"/>',
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * 0.88:.2f}" fill="none"'
        f' stroke="{ink}" stroke-width="0.16"/>',
        motif.polygram(cx, cy, r * 0.80, ink=metal, width=0.30),
        motif.rosette(cx, cy, r * 0.58, ink=ink, width=0.12),
        motif.star(cx, cy, r * 0.26, ink=metal, width=0.34),
    ]
    count = motif.order * 2
    for index in range(count):
        angle = index * math.tau / count
        parts.append(motif.star(cx + math.cos(angle) * r * 1.10,
                                cy + math.sin(angle) * r * 1.10,
                                r * 0.075, ink=metal, width=0.16))
    return "".join(parts)


def illuminated_border(motif: Motif, rect: geo.Rect, ink: str, metal: str,
                       second: str) -> str:
    """Registers of decreasing scale — the frame that *is* the document."""
    parts: list[str] = []
    for index, (inset, weight, colour) in enumerate((
        (0.0, 0.60, metal), (3.2, 0.18, ink), (4.6, 2.40, second),
        (7.4, 0.18, ink), (8.8, 0.36, metal),
    )):
        band = rect.inset(inset)
        parts.append(
            f'<rect {band.attrs()} fill="none" stroke="{colour}"'
            f' stroke-width="{weight:.2f}"/>'
        )
        if index == 2:
            parts.append(motif.field(band, cell=band.h / 5, ink=ink,
                                     width=0.10, strength=0.5))
    return "".join(parts)


def engine_field(motif: Motif, rect: geo.Rect, ink: str) -> str:
    """Lathe work in front, at full strength — the intaglio thesis."""
    parts = [
        motif.guilloche(rect.cx, rect.cy, rect.h * 0.62, ink=ink,
                        width=0.085, strength=0.42, passes=4)
    ]
    for cx in (rect.x + rect.w * 0.20, rect.x + rect.w * 0.80):
        parts.append(motif.guilloche(cx, rect.cy, rect.h * 0.34, ink=ink,
                                     width=0.075, strength=0.34, passes=3))
    return "".join(parts)


# --- the six compositions ----------------------------------------------------
#
# Each is written out. Nothing here is one function with a personality switch,
# because the whole argument of this pass is that these are different objects.


def compose(person: Personality) -> tuple[Press, str, str]:
    """Compose one personality. Returns the press, the content, and the CSS."""
    return _COMPOSERS[person.key](person)


def _frame(person: Personality) -> tuple[Press, Motif, geo.Rect, dict]:
    press = Press(width=W, height=H)
    motif = motif_for(institution=INSTITUTION, family=person.key)
    margin = min(W, H) * person.margin
    field = geo.Rect(margin, margin, W - margin * 2, H - margin * 2)
    scheme = SCHEMES.get(person.scheme) if person.scheme else None
    metals = {
        "primary": scheme.role("primary").core if scheme else person.ink,
        "face": scheme.role("primary").face if scheme else person.ink,
        "second": scheme.role("secondary").core if scheme else person.ink,
        "engraved": scheme.role("engraved").shadow if scheme else person.ink,
    }
    press.mark("substrate",
               f'<rect x="0" y="0" width="{W:g}" height="{H:g}"'
               f' fill="{person.paper}"/>', tonal=True)
    return press, motif, field, metals


def _collegiate(person: Personality) -> tuple[Press, str, str]:
    """No border. No ornament. The seal is the only object on the sheet."""
    press, motif, field, _ = _frame(person)
    ink = person.ink

    # The single deboss: the institution's seal, blind. It is the whole of the
    # sheet's expense and the only thing on it that is not a word.
    seal_r = min(W, H) * 0.088
    cx, cy = field.x + field.w * 0.845, field.y + field.h * 0.80
    press.mark("emboss",
               f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{seal_r:.2f}"'
               f' fill="none" stroke="#000" stroke-width="0.9"/>'
               + motif.polygram(cx, cy, seal_r * 0.72, ink="#000000",
                                width=0.7)
               + motif.star(cx, cy, seal_r * 0.30, ink="#000000", width=0.8),
               stroke=0.70)
    # Arms at the head, small, and drawn on the line plate: a collegiate sheet
    # has no metal, so the arms are engraved rather than struck.
    press.mark("line", arms(motif, field.cx, field.y + 9, 6.2,
                            geo.tint(ink, 0.9)), stroke=0.13)
    press.mark("microtext",
               geo.fine_text_ring(field.inset(-3), identifier="col",
                                  text=f"{INSTITUTION.upper()} · {SERIAL} · ",
                                  ink=ink, size=0.64, strength=0.30),
               stroke=0.066)

    body = f'''
    <div class="col">
      <div class="crest"></div>
      <div class="inst">{esc(INSTITUTION)}</div>
      <div class="lede">The Chancellor, Masters and Scholars certify that</div>
      <div class="peak">{esc(RECIPIENT)}</div>
      <div class="body">having satisfied the examiners in every part of the
        prescribed course, was admitted to the degree in the presence of the
        Congregation assembled, on the fourteenth day of March in the year two
        thousand and twenty-six.</div>
      <div class="foot">
        <div class="sig"><span></span>Registrar</div>
        <div class="sig"><span></span>Vice-Chancellor</div>
      </div>
    </div>'''
    css = f'''
    .col {{ position:absolute; left:{field.x:.1f}mm; top:{field.y:.1f}mm;
      width:{field.w:.1f}mm; height:{field.h:.1f}mm; text-align:center;
      display:flex; flex-direction:column; align-items:center;
      color:{ink}; font-family:'Source Serif 4',serif; }}
    .col .crest {{ height:17mm; }}
    .col .inst {{ font-size:3.4mm; letter-spacing:0.22em; text-transform:uppercase;
      color:{geo.tint(ink, 0.62)}; margin-bottom:14mm; }}
    .col .lede {{ font-size:3.3mm; font-style:italic;
      color:{geo.tint(ink, 0.72)}; }}
    .col .peak {{ font-size:9.6mm; margin:5mm 0 6mm; letter-spacing:-0.004em; }}
    .col .body {{ font-size:3.5mm; line-height:1.85; max-width:74%;
      color:{geo.tint(ink, 0.82)}; }}
    .col .foot {{ margin-top:auto; display:flex; gap:34mm; font-size:2.4mm;
      letter-spacing:0.16em; text-transform:uppercase;
      color:{geo.tint(ink, 0.6)}; }}
    .col .sig span {{ display:block; width:44mm; border-top:0.2mm solid
      {geo.tint(ink, 0.45)}; margin-bottom:1.4mm; }}'''
    return press, body, css


def _chancery(person: Personality) -> tuple[Press, str, str]:
    """The arms take a third of the sheet and are the peak."""
    press, motif, field, m = _frame(person)
    ink = person.ink
    press.defs.append(foil_gradient(SCHEMES[person.scheme].role("primary"),
                                    "chancery-foil", bands=2))

    # The guilloché sits behind the arms and nowhere else: the security is
    # where the authority is, which is the whole argument of this architecture.
    panel = geo.Rect(field.cx - 38, field.y + 2, 76, 62)
    press.mark("guilloche",
               motif.guilloche(panel.cx, panel.cy, panel.h * 0.52, ink=ink,
                               width=0.08, strength=0.30), stroke=0.08)
    press.mark("line",
               f'<rect {panel.attrs()} fill="none" stroke="{geo.tint(ink, 0.4)}"'
               ' stroke-width="0.14"/>', stroke=0.14)
    press.mark("foil_primary", arms(motif, field.cx, field.y + 26, 20,
                                    "url(#chancery-foil)"), stroke=0.26)
    press.mark("emboss", arms(motif, field.cx, field.y + 26, 20, "#000"),
               stroke=0.62)
    # One heavy rule. Not a frame: a state instrument is not enclosed, it is
    # underwritten.
    rule_y = field.y + 70
    press.mark("line",
               f'<rect x="{field.x:.2f}" y="{rule_y:.2f}" width="{field.w:.2f}"'
               f' height="1.6" fill="{m["engraved"]}"/>'
               f'<rect x="{field.x:.2f}" y="{rule_y + 2.4:.2f}"'
               f' width="{field.w:.2f}" height="0.35" fill="{m["primary"]}"/>')
    press.mark("antipathy",
               geo.line_screen("chan", degrees=8, pitch=0.44, width=0.07,
                               ink=ink, strength=0.10))
    press.defs.append(geo.line_screen("chan", degrees=8, pitch=0.44,
                                      width=0.07, ink=ink, strength=0.10))
    press.mark("microtext",
               geo.fine_text_ring(field.inset(-4), identifier="chan",
                                  text=f"{INSTITUTION.upper()} · {SERIAL} · ",
                                  ink=ink, size=0.62, strength=0.34),
               stroke=0.064)

    body = f'''
    <div class="chn">
      <div class="void"></div>
      <div class="ttl">Instrument of Award</div>
      <div class="txt">By the authority vested in it, the Institute has this day
        conferred upon <b>{esc(RECIPIENT)}</b>, having fulfilled every condition
        prescribed by its Statutes, the degree to which this instrument attests;
        and directs that this be entered in the Register.</div>
      <div class="foot">
        <div class="sig"><span></span>Registrar</div>
        <div class="sig"><span></span>Countersigned · President</div>
      </div>
    </div>'''
    css = f'''
    .chn {{ position:absolute; left:{field.x:.1f}mm; top:{field.y:.1f}mm;
      width:{field.w:.1f}mm; height:{field.h:.1f}mm; color:{ink};
      font-family:'Fraunces',serif; display:flex; flex-direction:column; }}
    .chn .void {{ height:76mm; flex:none; }}
    .chn .ttl {{ font-size:6.2mm; letter-spacing:0.06em; text-align:center;
      margin-bottom:5mm; }}
    .chn .txt {{ font-size:3.3mm; line-height:1.8; text-align:justify;
      max-width:82%; margin:0 auto; color:{geo.tint(ink, 0.86)}; }}
    .chn .txt b {{ font-weight:600; }}
    .chn .foot {{ margin-top:auto; display:flex; justify-content:space-between;
      font-family:'Inter',sans-serif; font-size:2.2mm; letter-spacing:0.16em;
      text-transform:uppercase; color:{geo.tint(ink, 0.6)}; }}
    .chn .sig span {{ display:block; width:58mm;
      border-top:0.25mm solid {m["primary"]}; margin-bottom:1.4mm; }}'''
    return press, body, css


def _court(person: Personality) -> tuple[Press, str, str]:
    """The frame is the document; the text is what it encloses."""
    press, motif, field, m = _frame(person)
    ink = person.ink
    press.mark("guilloche",
               motif.field(geo.Rect(0, 0, W, H), cell=17.0, ink=ink,
                           width=0.07, strength=0.16), stroke=0.07)
    press.mark("foil_primary",
               illuminated_border(motif, geo.Rect(6, 6, W - 12, H - 12),
                                  geo.tint(ink, 0.5), m["primary"], m["second"]),
               stroke=0.36)
    press.mark("foil_second",
               shamsa(motif, W / 2, 27, 15.5, geo.tint(ink, 0.6), m["second"]),
               stroke=0.30)
    inner = geo.Rect(field.x + 6, field.y + 32, field.w - 12, field.h - 48)
    press.mark("line",
               f'<rect {inner.attrs()} rx="4" fill="none"'
               f' stroke="{m["engraved"]}" stroke-width="0.3"/>', stroke=0.30)
    press.mark("emboss", motif.polygram(W / 2, 27, 11, ink="#000", width=0.7),
               stroke=0.70)
    press.mark("uv", motif.star(W / 2, H - 22, 7, ink="#000", width=0.4),
               stroke=0.40)
    press.mark("microtext",
               geo.fine_text_ring(geo.Rect(11, 11, W - 22, H - 22),
                                  identifier="crt",
                                  text=f"{INSTITUTION.upper()} · {SERIAL} · ",
                                  ink=ink, size=0.64, strength=0.40),
               stroke=0.066)

    body = f'''
    <div class="crt">
      <div class="ar" dir="rtl">شهادة إتمام المرحلة الجامعية</div>
      <div class="ttl">Certificate of Completion</div>
      <div class="peak">{esc(RECIPIENT)}</div>
      <div class="rule"></div>
      <div class="ar sm" dir="rtl">قد أتمّ بنجاحٍ متطلبات البرنامج الدراسي
        وفقًا للمناهج المعتمدة والمعايير الأكاديمية المعمول بها.</div>
    </div>'''
    css = f'''
    .crt {{ position:absolute; left:{inner.x:.1f}mm; top:{inner.y:.1f}mm;
      width:{inner.w:.1f}mm; height:{inner.h:.1f}mm; color:{ink};
      text-align:center; display:flex; flex-direction:column;
      align-items:center; justify-content:center;
      font-family:'Cormorant Garamond',serif; }}
    .crt .ar {{ font-family:'Amiri',serif; font-size:7.4mm; line-height:1.5; }}
    .crt .ar.sm {{ font-size:3.2mm; line-height:1.9; max-width:76%;
      color:{geo.tint(ink, 0.8)}; margin-top:5mm; }}
    .crt .ttl {{ font-size:4.6mm; letter-spacing:0.24em; text-transform:uppercase;
      color:{m["engraved"]}; margin:3mm 0 6mm; }}
    .crt .peak {{ font-size:8.4mm; font-weight:600; }}
    .crt .rule {{ width:52%; height:0.3mm; background:{m["primary"]};
      margin-top:4mm; }}'''
    return press, body, css


def _intaglio(person: Personality) -> tuple[Press, str, str]:
    """The lathe work is in front; the type sits in panels cut out of it."""
    press, motif, field, m = _frame(person)
    ink = person.ink
    press.mark("guilloche", engine_field(motif, geo.Rect(0, 0, W, H), ink),
               stroke=0.075)
    # Reserved panels: knocked out in the paper, so the type sits on paper
    # rather than on the lathe. This is how a note does it.
    vault = geo.Rect(field.cx - 52, field.y + 26, 104, 44)
    for panel in (geo.Rect(field.x, field.y, field.w, 20), vault,
                  geo.Rect(field.x, field.y + field.h - 26, field.w, 26)):
        press.mark("guilloche",
                   f'<rect {panel.attrs()} rx="2" fill="{person.paper}"/>',
                   tonal=False)
        press.mark("line",
                   f'<rect {panel.attrs()} rx="2" fill="none"'
                   f' stroke="{geo.tint(ink, 0.55)}" stroke-width="0.22"/>',
                   stroke=0.22)
    press.mark("line", motif.medallion_ring(field.cx, vault.cy, 19,
                                            ink=ink, width=0.12), stroke=0.12)
    press.defs.append(foil_gradient(SCHEMES[person.scheme].role("primary"),
                                    "int-foil", bands=1))
    press.mark("foil_primary",
               f'<circle cx="{field.x + field.w - 26:.1f}"'
               f' cy="{field.y + field.h - 13:.1f}" r="10.5" fill="none"'
               ' stroke="url(#int-foil)" stroke-width="1.1"/>', stroke=1.10)
    # A security thread: a broken vertical, as a windowed thread appears.
    thread = "".join(
        f'<rect x="{W * 0.30:.1f}" y="{y:.1f}" width="0.9" height="7"'
        f' fill="{geo.tint(ink, 0.30)}"/>' for y in range(14, int(H) - 12, 12)
    )
    press.mark("line", thread)
    press.mark("microtext",
               geo.fine_text_ring(field.inset(2), identifier="int",
                                  text=f"{SERIAL} · {INSTITUTION.upper()} · ",
                                  ink=ink, size=0.64, strength=0.55),
               stroke=0.066)
    press.mark("uv", motif.rosette(W / 2, H / 2, 44, ink="#000", width=0.35),
               stroke=0.35)
    press.mark("antipathy",
               geo.line_screen("int", degrees=53, pitch=0.42, width=0.07,
                               ink=ink, strength=0.12))
    press.defs.append(geo.line_screen("int", degrees=53, pitch=0.42,
                                      width=0.07, ink=ink, strength=0.12))

    body = f'''
    <div class="int">
      <div class="head"><span>{esc(INSTITUTION)}</span><b>{esc(SERIAL)}</b></div>
      <div class="vault">
        <div class="lede">Certified</div>
        <div class="peak">{esc(RECIPIENT)}</div>
      </div>
      <div class="foot"><span>Registrar</span><span>Verify · verify.example.edu</span></div>
    </div>'''
    css = f'''
    .int {{ position:absolute; left:{field.x:.1f}mm; top:{field.y:.1f}mm;
      width:{field.w:.1f}mm; height:{field.h:.1f}mm; color:{ink};
      font-family:'Archivo',sans-serif; display:flex; flex-direction:column; }}
    .int .head {{ height:20mm; display:flex; align-items:center;
      justify-content:space-between; padding:0 6mm; font-size:2.9mm;
      letter-spacing:0.22em; text-transform:uppercase; }}
    .int .head b {{ font-family:'IBM Plex Mono',monospace; letter-spacing:0.06em; }}
    .int .vault {{ margin-top:6mm; height:44mm; display:flex;
      flex-direction:column; align-items:center; justify-content:center; }}
    .int .lede {{ font-size:2.6mm; letter-spacing:0.42em; text-transform:uppercase;
      color:{geo.tint(ink, 0.6)}; }}
    .int .peak {{ font-size:7.6mm; font-weight:600; margin-top:3mm;
      letter-spacing:-0.01em; }}
    .int .foot {{ margin-top:auto; height:26mm; display:flex;
      align-items:center; justify-content:space-between; padding:0 6mm;
      font-size:2.3mm; letter-spacing:0.18em; text-transform:uppercase;
      color:{geo.tint(ink, 0.66)}; }}'''
    return press, body, css


def _letterpress(person: Personality) -> tuple[Press, str, str]:
    """No foil. One ink. The value is what a hand feels."""
    press, motif, field, _ = _frame(person)
    ink = person.ink
    # Deep deboss carries the entire ornament: the crest, and a single rule.
    press.mark("deboss", arms(motif, field.cx, field.y + 14, 9.5, "#000"),
               stroke=0.62)
    press.mark("deboss",
               f'<rect x="{field.x:.2f}" y="{field.y + 34:.2f}"'
               f' width="{field.w:.2f}" height="0.9" fill="#000"/>', stroke=0.90)
    press.mark("emboss", motif.star(field.cx, field.y + field.h - 12, 6.5,
                                    ink="#000", width=0.8), stroke=0.80)
    press.mark("varnish",
               f'<rect x="{field.x:.2f}" y="{field.y + 40:.2f}"'
               f' width="{field.w:.2f}" height="46" fill="#000"/>')
    press.mark("microtext",
               geo.fine_text_ring(field.inset(-2), identifier="ltr",
                                  text=f"{INSTITUTION.upper()} · {SERIAL} · ",
                                  ink=ink, size=0.62, strength=0.26),
               stroke=0.064)

    body = f'''
    <div class="ltp">
      <div class="void"></div>
      <div class="ttl">Certificate of Award</div>
      <div class="peak">{esc(RECIPIENT)}</div>
      <div class="body">is recorded in the Register of the Institute as having
        completed the course of study prescribed, and is commended to all whom
        it may concern.</div>
      <div class="foot"><span>{esc(SERIAL)}</span><span>Registrar</span></div>
    </div>'''
    css = f'''
    .ltp {{ position:absolute; left:{field.x:.1f}mm; top:{field.y:.1f}mm;
      width:{field.w:.1f}mm; height:{field.h:.1f}mm; color:{ink};
      font-family:'Source Serif 4',serif; text-align:center; display:flex;
      flex-direction:column; align-items:center; }}
    .ltp .void {{ height:40mm; }}
    .ltp .ttl {{ font-size:3.4mm; letter-spacing:0.40em; text-transform:uppercase;
      color:{geo.tint(ink, 0.66)}; }}
    .ltp .peak {{ font-size:8.8mm; margin:6mm 0 7mm; }}
    .ltp .body {{ font-size:3.3mm; line-height:1.9; max-width:66%;
      color:{geo.tint(ink, 0.8)}; }}
    .ltp .foot {{ margin-top:auto; width:100%; display:flex;
      justify-content:space-between; font-size:2.2mm; letter-spacing:0.20em;
      text-transform:uppercase; color:{geo.tint(ink, 0.55)};
      font-family:'IBM Plex Mono',monospace; }}'''
    return press, body, css


def _meridian(person: Personality) -> tuple[Press, str, str]:
    """Asymmetric. One hairline. Exactly one foil element."""
    press, motif, field, m = _frame(person)
    ink = person.ink
    press.defs.append(foil_gradient(SCHEMES[person.scheme].role("primary"),
                                    "mer-foil", bands=1))
    axis = field.x + field.w * person.axis
    # The one hairline, and it is structural: it marks the axis the whole
    # composition hangs from, which is why it runs the full height.
    press.mark("line",
               f'<rect x="{axis:.2f}" y="{field.y:.2f}" width="0.18"'
               f' height="{field.h:.2f}" fill="{geo.tint(ink, 0.28)}"/>',
               stroke=0.18)
    # The one foil element. Once, at the head, and nowhere else.
    press.mark("foil_primary",
               motif.polygram(axis, field.y + 10, 7.4, ink="url(#mer-foil)",
                              width=0.55), stroke=0.55)
    press.mark("varnish",
               f'<rect x="{axis:.2f}" y="{field.y + 24:.2f}"'
               f' width="{field.w - (axis - field.x):.2f}" height="34"'
               ' fill="#000"/>')
    press.mark("microtext",
               f'<text x="{field.x:.2f}" y="{field.y + field.h + 3:.2f}"'
               f' font-size="0.64" letter-spacing="0.04"'
               f' fill="{geo.tint(ink, 0.42)}"'
               f' font-family="Inter, sans-serif">'
               f'{esc((INSTITUTION.upper() + " · " + SERIAL + " · ") * 6)}</text>',
               stroke=0.066)

    body = f'''
    <div class="mer">
      <div class="mark"></div>
      <div class="inst">{esc(INSTITUTION)}</div>
      <div class="peak">{esc(RECIPIENT)}</div>
      <div class="meta"><span>Doctor of Philosophy</span><span>14 March 2026</span>
        <span>{esc(SERIAL)}</span></div>
      <div class="foot">Registrar</div>
    </div>'''
    css = f'''
    .mer {{ position:absolute; left:{axis:.1f}mm; top:{field.y:.1f}mm;
      width:{field.w - (axis - field.x):.1f}mm; height:{field.h:.1f}mm;
      color:{ink}; font-family:'Archivo',sans-serif; padding-left:9mm;
      display:flex; flex-direction:column; }}
    .mer .mark {{ height:22mm; }}
    .mer .inst {{ font-size:2.7mm; letter-spacing:0.30em; text-transform:uppercase;
      color:{geo.tint(ink, 0.55)}; }}
    .mer .peak {{ font-size:11.4mm; font-weight:600; letter-spacing:-0.02em;
      line-height:1.06; margin-top:6mm; max-width:96%; }}
    .mer .meta {{ margin-top:12mm; display:flex; flex-direction:column;
      gap:2.2mm; font-size:2.8mm; color:{geo.tint(ink, 0.72)}; }}
    .mer .meta span:last-child {{ font-family:'IBM Plex Mono',monospace;
      color:{geo.tint(ink, 0.5)}; }}
    .mer .foot {{ margin-top:auto; font-size:2.3mm; letter-spacing:0.22em;
      text-transform:uppercase; color:{m["primary"]}; }}'''
    return press, body, css


_COMPOSERS = {
    "collegiate": _collegiate, "chancery": _chancery, "court": _court,
    "intaglio": _intaglio, "letterpress": _letterpress, "meridian": _meridian,
}


# --- output ------------------------------------------------------------------


BASE_CSS = """
* { box-sizing:border-box; }
html,body { margin:0; padding:0; background:#1C1A17; }
.wrap { padding:8mm; }
.tag { font-family:'Inter',sans-serif; font-size:3mm; letter-spacing:0.14em;
  text-transform:uppercase; color:#A79E8E; margin:0 0 3mm 1mm; font-weight:600; }
.tag b { color:#F2E9D8; }
.sheet { position:relative; width:297mm; height:210mm; overflow:hidden;
  box-shadow:0 4mm 12mm rgba(0,0,0,0.45); }
.plate { position:absolute; inset:0; }
.plate svg { display:block; width:100%; height:100%; }
"""


def page(person: Personality, press: Press, body: str, css: str, *,
         silent: bool = False) -> str:
    tag = (f'<p class="tag"><b>{person.key} · {person.name}</b> — '
           f'{esc(person.thesis)} · {len(press.used_plates())} plates · '
           f'≈{press.relative_cost:g}× litho</p>')
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{person.name}</title><style>"
        "@page { size:297mm 210mm; margin:0; }"
        + font_face_css(embed=True) + BASE_CSS + ("" if silent else css)
        + '</style></head><body><div class="wrap">' + tag
        + f'<div class="sheet" style="background:{person.paper}">'
        f'<div class="plate">{press.svg()}</div>'
        + ("" if silent else body) + "</div></div></body></html>"
    )


def separation_page(person: Personality, press: Press) -> str:
    """Every plate alone, in black on white — what a printer looks at."""
    cards = []
    for plate in press.used_plates():
        svg = press.svg(only=plate.key, ground="#FFFFFF", separation=True)
        cards.append(
            f'<figure><figcaption><b>{plate.order}. {plate.name}</b> · '
            f'{plate.kind} · floor {plate.stroke_floor:.2f}mm · '
            f'reg {plate.registration:.2f}mm</figcaption>'
            f'<div class="sep">{svg}</div></figure>'
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{person.name} — separations</title><style>"
        + font_face_css(embed=True) + BASE_CSS +
        "figure{margin:0 0 6mm;} figcaption{font-family:'Inter',sans-serif;"
        "font-size:2.6mm;color:#D8CFBE;margin-bottom:1.5mm;letter-spacing:0.06em;}"
        "figcaption b{color:#F6EFE0;}"
        ".sep{width:297mm;height:210mm;background:#fff;}"
        ".sep svg{display:block;width:100%;height:100%;}"
        "pre{font-family:'IBM Plex Mono',monospace;font-size:2.6mm;color:#CFC6B4;"
        "background:#26231F;padding:5mm;white-space:pre-wrap;}"
        '</style></head><body><div class="wrap">'
        f'<p class="tag"><b>{person.name}</b> — separations</p>'
        + "".join(cards)
        + f"<pre>{esc(press.specification())}</pre>"
        + "</div></body></html>"
    )


def ink_coverage(page_path: pathlib.Path) -> float:
    """What proportion of the sheet reads as inked, measured not estimated."""
    from PIL import Image

    image = Image.open(page_path).convert("L")
    small = image.resize((360, 254))
    pixels = list(small.getdata())
    paper = sorted(pixels)[int(len(pixels) * 0.92)]
    inked = sum(1 for p in pixels if p < paper - 26)
    return inked / len(pixels)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sheets, silents = [], []
    for key, person in PERSONALITIES.items():
        press, body, css = compose(person)
        (OUT / f"{key}.html").write_text(page(person, press, body, css),
                                         encoding="utf-8")
        (OUT / f"{key}-identity.html").write_text(
            page(person, press, body, css, silent=True), encoding="utf-8")
        (OUT / f"{key}-separations.html").write_text(
            separation_page(person, press), encoding="utf-8")
        sheets.append(OUT / f"{key}.html")
        silents.append(OUT / f"{key}-identity.html")
        print(f"{person.name:12s} {len(press.used_plates()):2d} plates  "
              f"≈{press.relative_cost:5.2f}× litho  spends on {person.spends_on}")

    shots = shoot(sheets, OUT / "shots")
    quiet = shoot(silents, OUT / "identity")
    contact(shots, OUT / "contact-sheet.png", columns=2, width=880)
    contact(quiet, OUT / "identity-sheet.png", columns=2, width=880)

    print("\nInk coverage — measured against each personality's own target:")
    for shot, (key, person) in zip(shots, PERSONALITIES.items()):
        measured = ink_coverage(shot)
        delta = measured - person.ink_target
        flag = "ok" if abs(delta) <= 0.09 else "OFF TARGET"
        print(f"  {person.name:12s} target {person.ink_target:.2f}  "
              f"measured {measured:.2f}  {flag}")
    print(f"\ncontact → {OUT / 'contact-sheet.png'}")
    print(f"identity → {OUT / 'identity-sheet.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
