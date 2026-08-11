"""Six architectures for one certificate, so the choice is a comparison.

The first flagship plate was calculated rather than designed, and the honest
reason is that it was the *only* arrangement anybody drew. A single design is
never chosen; it is defaulted to and then defended. So: six genuinely different
spatial architectures, identical data, identical palette, identical geometry
budget — and the comparison is therefore about composition and nothing else.

What "different" has to mean here, because six colour variants would be a waste
of everybody's time:

    A  Architectural axis   a continuous vertical spine the frame opens for;
                            every zone locks onto it or hangs from it.
    B  Ceremonial band      a bounded horizontal register carrying the whole
                            identity relationship; quiet field above and below.
    C  Administrative edge  ceremonial symmetry, with a full-height column of
                            document identity down one edge. A passport page.
    D  Heraldic lintel      the seal and the institution form an upper
                            architecture; content hangs beneath it.
    E  Geometric field      the khatam construction *is* the layout; content
                            occupies the negative space the geometry leaves.
    F  Institutional rule   no enclosing frame at all. Two full-width rules,
                            a left-aligned hierarchy, restraint through
                            alignment rather than through centring.

Each is rendered at Level IV against the same hostile data, and the contact
sheet is the deliverable — you rank them by looking, not by reading this.
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

DATA = dict(
    institution="Meridian Institute for Advanced Study",
    institution_ar="معهد مريديان للدراسات العليا",
    conferral="The Senate of the Institute has conferred upon",
    recipient="Muhammad Abdulrahman Ibrahim Abdulwahid Al-Sulaimiy",
    recipient_ar="محمد عبد الرحمن إبراهيم عبد الواحد السليمي",
    qualification="Doctor of Philosophy",
    field_of_study="Educational Leadership and Institutional Development",
    qualification_ar="دكتوراه الفلسفة",
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


def _mm(v: float) -> str:
    return f"{v:.2f}mm"


def _css(plate, label: str) -> str:
    return f"""
@page {{ size: {plate.sheet.width}mm {plate.sheet.height}mm; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #DED8CA;
  font-family: 'EdirasX Sans', system-ui, sans-serif; }}
.wrap {{ padding: 6mm; }}
.tag {{ font-size: 3.4mm; letter-spacing: 0.18em; text-transform: uppercase;
  color: #4B5361; margin: 0 0 3mm 2mm; font-weight: 600; }}
.sheet {{ position: relative; width: {plate.sheet.width}mm;
  height: {plate.sheet.height}mm; background: {geo.tint("#FFFFFF", 0.30)};
  box-shadow: 0 2mm 7mm rgba(10,16,28,0.20); overflow: hidden; }}
.plate {{ position: absolute; inset: 0; }}
.plate svg {{ display: block; width: 100%; height: 100%; }}
.z {{ position: absolute; }}
.label {{ text-transform: uppercase; color: {geo.tint(INK, 0.60)};
  font-weight: 600; }}
.d {{ font-family: 'EdirasX Display', Georgia, serif; color: {INK}; }}
.ar {{ font-family: 'EdirasX Arabic', serif; direction: rtl; }}
.m {{ font-family: 'EdirasX Mono', monospace; color: {geo.tint(INK, 0.55)}; }}
.r {{ position: absolute; }}
"""


def _page(plate, body: str, label: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{label}</title><style>"
        + font_face_css(embed=True) + _css(plate, label)
        + "</style></head><body><div class=\"wrap\">"
        f'<p class="tag">{label}</p>'
        f'<div class="sheet"><div class="plate">{plate.svg}</div>{body}</div>'
        "</div></body></html>"
    )


def _rule(x: float, y: float, w: float, h: float, colour: str) -> str:
    return (f'<div class="r" style="left:{_mm(x)};top:{_mm(y)};width:{_mm(w)};'
            f'height:{_mm(h)};background:{colour}"></div>')


def _svg(x: float, y: float, size: float, inner: str) -> str:
    return (f'<div class="z" style="left:{_mm(x)};top:{_mm(y)};width:{_mm(size)};'
            f'height:{_mm(size)}"><svg width="100%" height="100%" '
            f'viewBox="0 0 {size:.2f} {size:.2f}">{inner}</svg></div>')


def _seal(cx: float, cy: float, r: float, *, legend: str, serial: str,
          rosette: bool = True) -> str:
    inner = ""
    if rosette:
        inner += geo.rosette(r, r, r * 0.95, ink=INK, width=0.07,
                             strength=0.14, passes=2)
    inner += geo.seal_ring(r, r, r * 0.80, ink=INK, legend=legend[:30],
                           identifier=serial)
    return _svg(cx - r, cy - r, r * 2, inner)


def _text(x: float, y: float, w: float, html: str, align: str = "center") -> str:
    return (f'<div class="z" style="left:{_mm(x)};top:{_mm(y)};width:{_mm(w)};'
            f'text-align:{align}">{html}</div>')


# --- A · architectural axis --------------------------------------------------


def composition_a() -> str:
    """A continuous vertical spine, and a frame that opens to let it through.

    The relationship the first plate lacked: the frame is interrupted at top
    and bottom centre exactly where the spine crosses it, so the border is
    plainly built *for* this content rather than drawn around it. Every zone
    either sits on the spine or is measured from it.
    """
    plate = build(sheet=SHEETS["a4-landscape"], budget=budget_for(4),
                  ink=INK, gold=GOLD, serial=DATA["serial"],
                  institution=DATA["institution"])
    f, s = plate.field, plate.sheet.rect
    d = DATA
    parts: list[str] = []

    # The spine, and the two openings in the frame it passes through. The
    # openings are painted in the paper colour over the frame — an interrupted
    # rule, which is how an engraved frame admits an axis.
    paper = geo.tint("#FFFFFF", 0.30)
    parts.append(_rule(s.cx - 4.5, 3.0, 9.0, 20.0, paper))
    parts.append(_rule(s.cx - 4.5, s.h - 23.0, 9.0, 20.0, paper))
    parts.append(_rule(s.cx - 0.12, 8.0, 0.24, s.h - 16.0,
                       geo.tint(GOLD, 0.55)))
    for y in (10.0, s.h - 10.0):
        parts.append(_svg(s.cx - 3.2, y - 3.2, 6.4,
                          geo.khatam(3.2, 3.2, 2.9, ink=GOLD, width=0.32)))

    # Institution: locked to the spine, with a clear band of paper behind it.
    parts.append(_rule(f.x, f.y + 6.2, f.w, 9.0, paper))
    parts.append(_text(f.x, f.y + 4.0, f.w,
        f'<div class="d" style="font-size:5.6mm;letter-spacing:0.10em;'
        f'white-space:nowrap">{d["institution"]}</div>'
        f'<div class="ar" style="font-size:4.6mm;margin-top:1.6mm;'
        f'color:{geo.tint(INK, 0.78)}">{d["institution_ar"]}</div>'))

    # The ceremonial moment: name and degree as ONE relationship, bracketed by
    # two rules that stop short of the spine's full width.
    top = f.y + f.h * 0.30
    parts.append(_rule(f.cx - f.w * 0.34, top, f.w * 0.68, 0.28,
                       geo.tint(GOLD, 0.85)))
    parts.append(_text(f.x, top + 5.0, f.w,
        f'<div class="label" style="font-size:2.5mm;letter-spacing:0.36em">'
        f'{d["conferral"]}</div>'))
    parts.append(_text(f.x, top + 11.0, f.w,
        f'<div class="d" style="font-size:9.6mm;font-weight:600;'
        f'letter-spacing:0.006em;line-height:1.06">{d["recipient"]}</div>'
        f'<div class="ar" style="font-size:5.4mm;margin-top:2.4mm;'
        f'color:{geo.tint(INK, 0.86)}">{d["recipient_ar"]}</div>'))
    parts.append(_text(f.x, top + 30.0, f.w,
        f'<div class="d" style="font-size:7.0mm;letter-spacing:0.16em;'
        f'text-transform:uppercase">{d["qualification"]}</div>'
        f'<div class="d" style="font-size:4.4mm;font-style:italic;'
        f'margin-top:1.8mm;color:{geo.tint(INK, 0.86)}">'
        f'{d["field_of_study"]}</div>'))
    parts.append(_rule(f.cx - f.w * 0.20, top + 43.5, f.w * 0.40, 0.22,
                       geo.tint(GOLD, 0.70)))
    parts.append(_text(f.x + f.w * 0.19, top + 47.0, f.w * 0.62,
        f'<div class="d" style="font-size:3.3mm;line-height:1.62;'
        f'color:{geo.tint(INK, 0.82)}">{d["statement"]}</div>'))

    # Execution: the seal ON the spine, signatures measured from it.
    exec_y = f.y + f.h - 26.0
    parts.append(_rule(s.cx - 11.0, exec_y - 12.0, 22.0, 30.0, paper))
    parts.append(_seal(s.cx, exec_y + 1.0, 12.5, legend=d["institution"],
                       serial=d["serial"]))
    for i, (name, office) in enumerate(d["signatures"]):
        w = f.w * 0.26
        x = f.x + (f.w * 0.06 if i == 0 else f.w - f.w * 0.06 - w)
        parts.append(_text(x, exec_y - 6.0, w,
            f'<div class="d" style="font-size:4.4mm">{name}</div>'))
        parts.append(_rule(x, exec_y + 1.4, w, 0.22, geo.tint(INK, 0.72)))
        parts.append(_text(x, exec_y + 3.0, w,
            f'<div class="label" style="font-size:2.3mm;letter-spacing:0.30em">'
            f'{office}</div>'))

    parts.append(_text(f.x, f.y + f.h - 3.0, f.w * 0.46,
        f'<div class="m" style="font-size:2.3mm">{d["serial"]} · {d["issued"]}'
        f'</div>', align="left"))
    parts.append(_text(f.x + f.w * 0.54, f.y + f.h - 3.0, f.w * 0.46,
        f'<div class="m" style="font-size:2.3mm">VERIFY {d["code"]}</div>',
        align="right"))
    return _page(plate, "".join(parts), "A · architectural axis")


# --- B · ceremonial band -----------------------------------------------------


def composition_b() -> str:
    """One bounded register carries the whole identity relationship.

    The band is the document. Above it the institution; below it the execution;
    inside it, on a slightly deeper ground, the name and the degree with
    nothing else competing. The band's rules run the full sheet width and meet
    the frame, which is what ties the two together.
    """
    plate = build(sheet=SHEETS["a4-landscape"], budget=budget_for(3),
                  ink=INK, gold=GOLD, serial=DATA["serial"],
                  institution=DATA["institution"])
    f, s = plate.field, plate.sheet.rect
    d = DATA
    parts: list[str] = []

    band_y, band_h = f.y + f.h * 0.235, f.h * 0.40
    parts.append(f'<div class="r" style="left:0mm;'
                 f'top:{_mm(band_y)};width:{_mm(s.w)};height:{_mm(band_h)};'
                 f'background:{geo.tint(GOLD, 0.055)}"></div>')
    for y in (band_y, band_y + band_h):
        parts.append(_rule(0, y, s.w, 0.45, geo.tint(GOLD, 0.85)))
        parts.append(_rule(0, y + 0.9, s.w, 0.16, geo.tint(INK, 0.35)))

    parts.append(_text(f.x, f.y + 3.0, f.w,
        f'<div class="d" style="font-size:5.2mm;letter-spacing:0.11em;'
        f'white-space:nowrap">{d["institution"]}</div>'
        f'<div class="ar" style="font-size:4.4mm;margin-top:1.4mm;'
        f'color:{geo.tint(INK, 0.78)}">{d["institution_ar"]}</div>'))

    parts.append(_text(f.x, band_y + 6.0, f.w,
        f'<div class="label" style="font-size:2.5mm;letter-spacing:0.36em">'
        f'{d["conferral"]}</div>'))
    parts.append(_text(f.x, band_y + 12.5, f.w,
        f'<div class="d" style="font-size:10.0mm;font-weight:600;line-height:1.05">'
        f'{d["recipient"]}</div>'
        f'<div class="ar" style="font-size:5.6mm;margin-top:2.2mm;'
        f'color:{geo.tint(INK, 0.86)}">{d["recipient_ar"]}</div>'))
    parts.append(_svg(f.cx - 24, band_y + 33.0, 4.0,
                      geo.khatam(2, 2, 1.8, ink=GOLD, width=0.28)))
    parts.append(_svg(f.cx + 20, band_y + 33.0, 4.0,
                      geo.khatam(2, 2, 1.8, ink=GOLD, width=0.28)))
    parts.append(_text(f.x, band_y + 32.0, f.w,
        f'<div class="d" style="font-size:6.4mm;letter-spacing:0.18em;'
        f'text-transform:uppercase">{d["qualification"]}</div>'))
    parts.append(_text(f.x + f.w * 0.15, band_y + 41.5, f.w * 0.70,
        f'<div class="d" style="font-size:4.2mm;font-style:italic;'
        f'color:{geo.tint(INK, 0.88)}">{d["field_of_study"]}</div>'))

    below = band_y + band_h + 5.0
    parts.append(_text(f.x + f.w * 0.17, below, f.w * 0.66,
        f'<div class="d" style="font-size:3.2mm;line-height:1.6;'
        f'color:{geo.tint(INK, 0.82)}">{d["statement"]}</div>'))

    exec_y = f.y + f.h - 24.0
    parts.append(_seal(s.cx, exec_y + 2.0, 12.0, legend=d["institution"],
                       serial=d["serial"], rosette=False))
    for i, (name, office) in enumerate(d["signatures"]):
        w = f.w * 0.24
        x = f.x + (f.w * 0.08 if i == 0 else f.w - f.w * 0.08 - w)
        parts.append(_text(x, exec_y - 5.0, w,
            f'<div class="d" style="font-size:4.2mm">{name}</div>'))
        parts.append(_rule(x, exec_y + 1.8, w, 0.22, geo.tint(INK, 0.72)))
        parts.append(_text(x, exec_y + 3.4, w,
            f'<div class="label" style="font-size:2.2mm;letter-spacing:0.30em">'
            f'{office}</div>'))

    parts.append(_text(f.x, f.y + f.h - 3.0, f.w,
        f'<div class="m" style="font-size:2.3mm">{d["serial"]} · {d["issued"]}'
        f' · VERIFY {d["code"]}</div>'))
    return _page(plate, "".join(parts), "B · ceremonial band")


# --- C · administrative edge -------------------------------------------------


def composition_c() -> str:
    """Ceremonial symmetry, with the document's identity down one edge.

    The sanctioned asymmetry taken seriously rather than tucked into a
    footline: a full-height column carrying serial, verification, seal and
    microtext, separated from the ceremonial field by a single rule. A passport
    data page does exactly this, and for the same reason — the administrative
    apparatus is *not* part of the ceremony and should not pretend to be.
    """
    plate = build(sheet=SHEETS["a4-landscape"], budget=budget_for(4),
                  ink=INK, gold=GOLD, serial=DATA["serial"],
                  institution=DATA["institution"])
    f = plate.field
    d = DATA
    parts: list[str] = []

    col_w = f.w * 0.20
    col_x = f.x + f.w - col_w
    cer = geo.Rect(f.x, f.y, f.w - col_w - 8.0, f.h)
    parts.append(_rule(col_x - 5.0, f.y, 0.22, f.h, geo.tint(INK, 0.42)))

    parts.append(_text(cer.x, cer.y + 3.0, cer.w,
        f'<div class="d" style="font-size:5.0mm;letter-spacing:0.10em;'
        f'white-space:nowrap">{d["institution"]}</div>'
        f'<div class="ar" style="font-size:4.2mm;margin-top:1.4mm;'
        f'color:{geo.tint(INK, 0.78)}">{d["institution_ar"]}</div>'))
    parts.append(_rule(cer.cx - cer.w * 0.16, cer.y + 15.5, cer.w * 0.32, 0.24,
                       geo.tint(GOLD, 0.85)))

    top = cer.y + cer.h * 0.30
    parts.append(_text(cer.x, top, cer.w,
        f'<div class="label" style="font-size:2.4mm;letter-spacing:0.34em">'
        f'{d["conferral"]}</div>'))
    parts.append(_text(cer.x, top + 6.0, cer.w,
        f'<div class="d" style="font-size:8.6mm;font-weight:600;line-height:1.06">'
        f'{d["recipient"]}</div>'
        f'<div class="ar" style="font-size:5.0mm;margin-top:2.2mm;'
        f'color:{geo.tint(INK, 0.86)}">{d["recipient_ar"]}</div>'))
    parts.append(_rule(cer.cx - cer.w * 0.30, top + 24.0, cer.w * 0.60, 0.20,
                       geo.tint(INK, 0.40)))
    parts.append(_text(cer.x, top + 27.5, cer.w,
        f'<div class="d" style="font-size:6.2mm;letter-spacing:0.17em;'
        f'text-transform:uppercase">{d["qualification"]}</div>'
        f'<div class="d" style="font-size:4.0mm;font-style:italic;'
        f'margin-top:1.6mm;color:{geo.tint(INK, 0.86)}">'
        f'{d["field_of_study"]}</div>'))
    parts.append(_text(cer.x + cer.w * 0.08, top + 43.0, cer.w * 0.84,
        f'<div class="d" style="font-size:3.1mm;line-height:1.6;'
        f'color:{geo.tint(INK, 0.82)}">{d["statement"]}</div>'))

    exec_y = cer.y + cer.h - 20.0
    for i, (name, office) in enumerate(d["signatures"]):
        w = cer.w * 0.36
        x = cer.x + (cer.w * 0.04 if i == 0 else cer.w - cer.w * 0.04 - w)
        parts.append(_text(x, exec_y - 5.0, w,
            f'<div class="d" style="font-size:4.2mm">{name}</div>'))
        parts.append(_rule(x, exec_y + 1.6, w, 0.22, geo.tint(INK, 0.72)))
        parts.append(_text(x, exec_y + 3.2, w,
            f'<div class="label" style="font-size:2.2mm;letter-spacing:0.28em">'
            f'{office}</div>'))

    # The column.
    parts.append(_seal(col_x + col_w / 2, f.y + 18.0, 13.0,
                       legend=d["institution"], serial=d["serial"]))
    rows = (("Document", d["serial"]), ("Issued", d["issued"]),
            ("Verification", d["code"]), ("Level", "Doctoral · IV"))
    for i, (k, v) in enumerate(rows):
        y = f.y + 40.0 + i * 11.0
        parts.append(_text(col_x, y, col_w,
            f'<div class="label" style="font-size:2.1mm;letter-spacing:0.26em">'
            f'{k}</div>'
            f'<div class="m" style="font-size:2.9mm;margin-top:1.0mm;'
            f'color:{INK}">{v}</div>', align="left"))
    parts.append(_svg(col_x, f.y + f.h - 34.0, col_w,
                      geo.rosette(col_w / 2, col_w / 2, col_w * 0.46, ink=INK,
                                  width=0.09, strength=0.30, passes=3)))
    return _page(plate, "".join(parts), "C · administrative edge")


# --- D · heraldic lintel -----------------------------------------------------


def composition_d() -> str:
    """The seal and the institution form an upper architecture. Content hangs.

    A lintel: the seal at the centre of the top register with the institution's
    two names either side of it, carried on a full-width rule. Everything below
    is suspended from that structure rather than floating in a field, which is
    the specific failure of a centred stack.
    """
    plate = build(sheet=SHEETS["a4-landscape"], budget=budget_for(3),
                  ink=INK, gold=GOLD, serial=DATA["serial"],
                  institution=DATA["institution"])
    f, s = plate.field, plate.sheet.rect
    d = DATA
    parts: list[str] = []

    lintel = f.y + 22.0
    parts.append(_seal(s.cx, f.y + 11.0, 13.5, legend=d["institution"],
                       serial=d["serial"]))
    parts.append(_text(f.x, f.y + 6.0, f.w * 0.38,
        f'<div class="d" style="font-size:4.8mm;letter-spacing:0.09em;'
        f'line-height:1.25">{d["institution"]}</div>', align="left"))
    parts.append(_text(f.x + f.w * 0.62, f.y + 6.0, f.w * 0.38,
        f'<div class="ar" style="font-size:5.4mm;line-height:1.5">'
        f'{d["institution_ar"]}</div>', align="right"))
    parts.append(_rule(f.x, lintel, f.w, 0.50, geo.tint(GOLD, 0.9)))
    parts.append(_rule(f.x, lintel + 1.1, f.w, 0.18, geo.tint(INK, 0.40)))

    parts.append(_text(f.x, lintel + 8.0, f.w,
        f'<div class="label" style="font-size:2.5mm;letter-spacing:0.36em">'
        f'{d["conferral"]}</div>'))
    parts.append(_text(f.x, lintel + 15.0, f.w,
        f'<div class="d" style="font-size:9.4mm;font-weight:600;line-height:1.06">'
        f'{d["recipient"]}</div>'
        f'<div class="ar" style="font-size:5.2mm;margin-top:2.2mm;'
        f'color:{geo.tint(INK, 0.86)}">{d["recipient_ar"]}</div>'))

    # The degree in a khatam-bounded cartouche: the one moment ornament is
    # doing structural work rather than sitting beside the words.
    cart_y = lintel + 35.0
    parts.append(_rule(f.cx - f.w * 0.30, cart_y, f.w * 0.60, 0.24,
                       geo.tint(GOLD, 0.80)))
    parts.append(_rule(f.cx - f.w * 0.30, cart_y + 17.0, f.w * 0.60, 0.24,
                       geo.tint(GOLD, 0.80)))
    for x in (f.cx - f.w * 0.30, f.cx + f.w * 0.30):
        parts.append(_svg(x - 2.6, cart_y + 5.9, 5.2,
                          geo.khatam(2.6, 2.6, 2.4, ink=GOLD, width=0.30)))
    parts.append(_text(f.x, cart_y + 3.4, f.w,
        f'<div class="d" style="font-size:6.6mm;letter-spacing:0.18em;'
        f'text-transform:uppercase">{d["qualification"]}</div>'
        f'<div class="d" style="font-size:4.0mm;font-style:italic;'
        f'margin-top:1.2mm;color:{geo.tint(INK, 0.86)}">'
        f'{d["field_of_study"]}</div>'))

    parts.append(_text(f.x + f.w * 0.17, cart_y + 22.0, f.w * 0.66,
        f'<div class="d" style="font-size:3.2mm;line-height:1.6;'
        f'color:{geo.tint(INK, 0.82)}">{d["statement"]}</div>'))

    exec_y = f.y + f.h - 18.0
    parts.append(_rule(f.x, exec_y - 9.0, f.w, 0.18, geo.tint(INK, 0.30)))
    for i, (name, office) in enumerate(d["signatures"]):
        w = f.w * 0.30
        x = f.x + (f.w * 0.05 if i == 0 else f.w - f.w * 0.05 - w)
        parts.append(_text(x, exec_y - 5.0, w,
            f'<div class="d" style="font-size:4.4mm">{name}</div>'))
        parts.append(_rule(x, exec_y + 1.6, w, 0.22, geo.tint(INK, 0.72)))
        parts.append(_text(x, exec_y + 3.2, w,
            f'<div class="label" style="font-size:2.2mm;letter-spacing:0.28em">'
            f'{office}</div>'))
    parts.append(_text(f.x + f.w * 0.35, exec_y - 5.0, f.w * 0.30,
        f'<div class="m" style="font-size:2.3mm">{d["serial"]}</div>'
        f'<div class="m" style="font-size:2.3mm;margin-top:1.2mm">'
        f'VERIFY {d["code"]}</div>'))
    return _page(plate, "".join(parts), "D · heraldic lintel")


# --- E · geometric field -----------------------------------------------------


def composition_e() -> str:
    """The khatam construction is the layout. Content occupies its negatives.

    An eight-fold radial construction centred on the sheet, drawn at a legible
    weight rather than as a watermark, whose rays and rings *define* the zones.
    This is the one composition where the geometry is structural — and the test
    of it is whether the page still reads calmly, or whether the ornament has
    taken over, which is exactly what the ceremonial budget exists to prevent.
    """
    plate = build(sheet=SHEETS["a4-landscape"], budget=budget_for(4),
                  ink=INK, gold=GOLD, serial=DATA["serial"],
                  institution=DATA["institution"])
    f, s = plate.field, plate.sheet.rect
    d = DATA
    parts: list[str] = []

    # The construction, at the sheet's optical centre and large enough to be
    # architecture rather than decoration.
    R = f.h * 0.46
    inner = (
        geo.interlocking_squares(R, R, R * 0.92, ink=GOLD, width=0.30,
                                 strength=0.55)
        + geo.khatam(R, R, R * 0.92, ink=GOLD, width=0.22, strength=0.42)
        + geo.khatam(R, R, R * 0.52, ink=INK, width=0.18, strength=0.28)
        + f'<circle cx="{R}" cy="{R}" r="{R * 0.985:.2f}" fill="none" '
          f'stroke="{geo.tint(INK, 0.32)}" stroke-width="0.22"/>'
    )
    parts.append(_svg(s.cx - R, f.y + f.h * 0.50 - R, R * 2, inner))

    parts.append(_text(f.x, f.y + 2.0, f.w,
        f'<div class="d" style="font-size:5.0mm;letter-spacing:0.11em;'
        f'white-space:nowrap">{d["institution"]}</div>'
        f'<div class="ar" style="font-size:4.2mm;margin-top:1.2mm;'
        f'color:{geo.tint(INK, 0.78)}">{d["institution_ar"]}</div>'))

    mid = f.y + f.h * 0.50
    paper = geo.tint("#FFFFFF", 0.30)
    parts.append(_rule(f.cx - f.w * 0.36, mid - 15.0, f.w * 0.72, 30.0, paper))
    parts.append(_text(f.x, mid - 13.5, f.w,
        f'<div class="label" style="font-size:2.4mm;letter-spacing:0.34em">'
        f'{d["conferral"]}</div>'))
    parts.append(_text(f.x, mid - 8.5, f.w,
        f'<div class="d" style="font-size:8.4mm;font-weight:600;line-height:1.06">'
        f'{d["recipient"]}</div>'
        f'<div class="ar" style="font-size:4.8mm;margin-top:1.8mm;'
        f'color:{geo.tint(INK, 0.86)}">{d["recipient_ar"]}</div>'))
    parts.append(_text(f.x, mid + 7.5, f.w,
        f'<div class="d" style="font-size:5.6mm;letter-spacing:0.18em;'
        f'text-transform:uppercase">{d["qualification"]}</div>'))

    parts.append(_text(f.x + f.w * 0.05, f.y + f.h * 0.50 + R - 2.0, f.w * 0.90,
        f'<div class="d" style="font-size:4.0mm;font-style:italic;'
        f'color:{geo.tint(INK, 0.88)}">{d["field_of_study"]}</div>'))

    exec_y = f.y + f.h - 16.0
    for i, (name, office) in enumerate(d["signatures"]):
        w = f.w * 0.26
        x = f.x + (f.w * 0.03 if i == 0 else f.w - f.w * 0.03 - w)
        parts.append(_text(x, exec_y - 5.0, w,
            f'<div class="d" style="font-size:4.0mm">{name}</div>'))
        parts.append(_rule(x, exec_y + 1.2, w, 0.22, geo.tint(INK, 0.72)))
        parts.append(_text(x, exec_y + 2.8, w,
            f'<div class="label" style="font-size:2.1mm;letter-spacing:0.28em">'
            f'{office}</div>'))
    parts.append(_text(f.x + f.w * 0.36, exec_y - 2.0, f.w * 0.28,
        f'<div class="m" style="font-size:2.2mm">{d["serial"]} · '
        f'VERIFY {d["code"]}</div>'))
    return _page(plate, "".join(parts), "E · geometric field")


# --- F · institutional rule --------------------------------------------------


def composition_f() -> str:
    """No enclosing frame. Two rules, wide margins, a left-aligned hierarchy.

    The most restrained of the six and the hardest to get right: with nothing
    holding the page together but alignment and air, every measure has to be
    correct. It is here because the brief asks for luxury without ornament, and
    this is what that actually looks like — the register a modern research
    university or a professional body would recognise instantly.
    """
    plate = build(sheet=SHEETS["a4-landscape"], budget=budget_for(1),
                  ink=INK, gold=GOLD, serial=DATA["serial"],
                  institution=DATA["institution"])
    s = plate.sheet.rect
    d = DATA
    m = 26.0
    x, w = m, s.w - m * 2
    parts: list[str] = []

    parts.append(_rule(m, 20.0, w, 0.7, INK))
    parts.append(_rule(m, s.h - 20.0, w, 0.7, INK))

    parts.append(_svg(x, 27.0, 11.0, geo.khatam(5.5, 5.5, 5.0, ink=GOLD,
                                                width=0.42)))
    parts.append(_text(x + 15.0, 28.0, w * 0.5,
        f'<div class="d" style="font-size:5.0mm;letter-spacing:0.10em">'
        f'{d["institution"]}</div>', align="left"))
    parts.append(_text(x + w * 0.5, 28.0, w * 0.5,
        f'<div class="ar" style="font-size:5.0mm">{d["institution_ar"]}</div>',
        align="right"))

    parts.append(_text(x, 62.0, w,
        f'<div class="label" style="font-size:2.6mm;letter-spacing:0.40em">'
        f'{d["conferral"]}</div>', align="left"))
    parts.append(_text(x, 69.0, w,
        f'<div class="d" style="font-size:11.0mm;font-weight:600;'
        f'line-height:1.04;letter-spacing:-0.004em">{d["recipient"]}</div>',
        align="left"))
    parts.append(_text(x, 84.0, w * 0.6,
        f'<div class="ar" style="font-size:5.4mm;color:{geo.tint(INK, 0.86)}">'
        f'{d["recipient_ar"]}</div>', align="left"))

    parts.append(_rule(x, 100.0, w * 0.30, 0.30, geo.tint(GOLD, 0.9)))
    parts.append(_text(x, 105.0, w,
        f'<div class="d" style="font-size:7.4mm;letter-spacing:0.14em;'
        f'text-transform:uppercase">{d["qualification"]}</div>'
        f'<div class="d" style="font-size:4.6mm;font-style:italic;'
        f'margin-top:2.0mm;color:{geo.tint(INK, 0.86)}">'
        f'{d["field_of_study"]}</div>', align="left"))

    parts.append(_text(x, 132.0, w * 0.56,
        f'<div class="d" style="font-size:3.3mm;line-height:1.68;'
        f'color:{geo.tint(INK, 0.80)}">{d["statement"]}</div>', align="left"))

    parts.append(_seal(x + w - 22.0, 145.0, 18.0, legend=d["institution"],
                       serial=d["serial"], rosette=False))

    exec_y = s.h - 34.0
    for i, (name, office) in enumerate(d["signatures"]):
        cw = w * 0.26
        cx = x + i * (cw + 10.0)
        parts.append(_text(cx, exec_y - 5.0, cw,
            f'<div class="d" style="font-size:4.2mm">{name}</div>', align="left"))
        parts.append(_rule(cx, exec_y + 1.4, cw, 0.22, geo.tint(INK, 0.72)))
        parts.append(_text(cx, exec_y + 3.0, cw,
            f'<div class="label" style="font-size:2.2mm;letter-spacing:0.28em">'
            f'{office}</div>', align="left"))
    parts.append(_text(x + w * 0.60, exec_y + 1.0, w * 0.40,
        f'<div class="m" style="font-size:2.4mm">{d["serial"]} · {d["issued"]}'
        f'</div><div class="m" style="font-size:2.4mm;margin-top:1.2mm">'
        f'VERIFY {d["code"]}</div>', align="right"))
    return _page(plate, "".join(parts), "F · institutional rule")


COMPOSITIONS = {
    "A-architectural-axis": composition_a,
    "B-ceremonial-band": composition_b,
    "C-administrative-edge": composition_c,
    "D-heraldic-lintel": composition_d,
    "E-geometric-field": composition_e,
    "F-institutional-rule": composition_f,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, make in COMPOSITIONS.items():
        target = OUT / f"comp-{name}.html"
        target.write_text(make(), encoding="utf-8")
        print(f"{target.name}  {target.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
