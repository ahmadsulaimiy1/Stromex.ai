"""Frame architecture: the constructions that make a sheet read as an artefact.

`geometry.py` is the vocabulary — curves, stars, rules, substrate. This file is
the *architecture*: the elements a ceremonial document is actually built from,
at the scale a person perceives them from a metre away.

The distinction matters because the failure this file exists to correct was
real. A frame made of four concentric rectangles is not an architecture; it is
four rectangles, and no amount of precision inside them changes what the eye
reads at arm's length. The finest physical documents do something else, and it
is entirely describable:

**The frame has mass, and the mass is at the corners.** A dark, substantial
corner block carrying a metal medallion, with the lighter registers running
between the corners, is why a plate looks *built* rather than drawn. The corner
is where a frame is structurally weakest and visually most important, and giving
it weight is the oldest move in the discipline.

**The perimeter is a sequence of registers, each doing a different job.** A
security field, an ornamental field, a metal register, a geometric register, a
ceremonial inner frame. Five registers of 4mm each is a different object from one
register of 20mm, and it is the sequence — coarse to fine, inwards — that reads
as craftsmanship.

**Corners are cut, not square.** A stepped or chamfered inner frame is the
signature of a plate that was composed rather than stroked. A re-entrant corner
also gives the geometry somewhere to resolve, which a right angle does not.

**The field is not empty; it is quiet.** An allover mandala at the threshold of
visibility, a blind-embossed mark at the optical centre, a spreader rule with
lozenge stops — the field is worked, and reads as air only because the working
is held two or three per cent above the paper.

Everything here is constructed. There are no traced assets and no rasters, and
every function returns SVG in millimetre user units, so a plate is exact at 300
DPI and at 2400 alike.
"""

from __future__ import annotations

import math
from typing import Final

from app.modules.design import geometry as geo
from app.modules.design.gilding import Metal, emboss, engraved_metal_rule

__all__ = [
    "arch_niche_path",
    "cartouche_path",
    "corner_block",
    "cresting",
    "girih_band",
    "legend_ring",
    "mandala",
    "medallion",
    "radiant_field",
    "register_stack",
    "spreader",
    "stepped_rect_path",
    "tessellation_field",
    "vertical_spine",
]

#: Circumradius-to-pitch for the octagon–square tiling: regular octagons on a
#: square lattice meet flat-to-flat when the pitch is twice the apothem, and the
#: gaps are squares on the diagonal. This constant is what makes the tiling a
#: real tiling rather than octagons scattered on a grid.
_OCT: Final[float] = 2 * math.cos(math.pi / 8)


# --- shaped outlines ---------------------------------------------------------


def stepped_rect_path(rect: geo.Rect, *, cut: float = 6.0,
                      step: float = 0.0) -> str:
    """A rectangle whose corners are cut, and optionally stepped.

    `cut` chamfers each corner by that distance along both edges — an octagonal
    outline, and the reason a ceremonial inner frame reads as a plate rather
    than as a box. `step` adds a shoulder before the chamfer, which is the
    profile a die-stamped frame actually has: the eye reads two changes of
    direction at the corner instead of one, and two is what looks machined.
    """
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    c, s = cut, step
    if s <= 0:
        return (
            f"M{x + c:.2f} {y:.2f} H{x + w - c:.2f} L{x + w:.2f} {y + c:.2f} "
            f"V{y + h - c:.2f} L{x + w - c:.2f} {y + h:.2f} H{x + c:.2f} "
            f"L{x:.2f} {y + h - c:.2f} V{y + c:.2f} Z"
        )
    # With a shoulder: edge → in by `s` → along by `s` → chamfer → next edge.
    return (
        f"M{x + c + s:.2f} {y:.2f} H{x + w - c - s:.2f} "
        f"V{y + s:.2f} H{x + w - c:.2f} L{x + w:.2f} {y + c:.2f} "
        f"H{x + w - s:.2f} V{y + h - c:.2f} H{x + w:.2f} "
        f"L{x + w - c:.2f} {y + h:.2f} V{y + h - s:.2f} H{x + c:.2f} "
        f"V{y + h:.2f} L{x:.2f} {y + h - c:.2f} H{x + s:.2f} "
        f"V{y + c:.2f} H{x:.2f} L{x + c:.2f} {y:.2f} "
        f"V{y + s:.2f} H{x + c + s:.2f} Z"
    )


def cartouche_path(rect: geo.Rect, *, arch: float = 4.0,
                   cut: float = 5.0) -> str:
    """A shaped ceremonial panel: cut corners, arched top and bottom.

    The plaque a name or a qualification is set on when the composition wants
    the text to be *mounted* rather than placed. The arch is a single quadratic
    on each long edge, so the panel keeps one continuous curvature instead of
    reading as a rectangle with bumps.
    """
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    return (
        f"M{x + cut:.2f} {y:.2f} "
        f"Q{x + w / 2:.2f} {y - arch:.2f} {x + w - cut:.2f} {y:.2f} "
        f"L{x + w:.2f} {y + cut:.2f} V{y + h - cut:.2f} "
        f"L{x + w - cut:.2f} {y + h:.2f} "
        f"Q{x + w / 2:.2f} {y + h + arch:.2f} {x + cut:.2f} {y + h:.2f} "
        f"L{x:.2f} {y + h - cut:.2f} V{y + cut:.2f} Z"
    )


def arch_niche_path(rect: geo.Rect, *, offset: float = 0.17,
                    rise: float | None = None) -> str:
    """A two-centred pointed arch over a rectangular base — a mihrab profile.

    Constructed, not drawn. The two arc centres sit on the springing line,
    displaced from the axis by `d = offset · w`, and each arc has radius
    `w/2 + d`; the left half of the curve is struck from the *right* centre and
    vice versa, which is what puts a genuine point at the apex instead of two
    curves that nearly meet. The apex height then follows from the construction
    — `√(R² − d²)` above the springing — rather than being a number somebody
    liked, so a wider niche is automatically a taller one.

    The springing line is placed so the arch occupies the top of `rect` and the
    straight jambs the rest, giving the whole outline in one path.

    `rise` inverts the construction: state how tall the arch should be and the
    displacement follows, `d = (rise² − a²) / 2a`. That matters on a landscape
    sheet, where a mihrab struck from its natural proportion is 131mm tall on a
    150mm field and reads as a balloon rather than as architecture. A rise below
    the half-width puts the centres on the far side of the axis and the figure
    becomes a segmental canopy, which is the correct form over a wide opening
    and is still a two-centred arch rather than a drawn curve.
    """
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    half = w / 2
    if rise is not None:
        d = (rise * rise - half * half) / (2 * half)
        radius = half + d
        height = rise
    else:
        d = w * offset
        radius = half + d
        height = math.sqrt(max(radius ** 2 - d ** 2, 0.0))
    spring = y + height
    return (
        f"M{x:.2f} {y + h:.2f} V{spring:.2f} "
        f"A{radius:.2f} {radius:.2f} 0 0 1 {x + w / 2:.2f} {y:.2f} "
        f"A{radius:.2f} {radius:.2f} 0 0 1 {x + w:.2f} {spring:.2f} "
        f"V{y + h:.2f} Z"
    )


# --- the corner --------------------------------------------------------------


def corner_block(x: float, y: float, size: float, *, quadrant: int,
                 mass: str, metal: Metal, ink: str,
                 inset_medallion: bool = True) -> str:
    """The substantial corner: a stepped bracket of mass with a metal medallion.

    This is the single element that most separates a plate that looks
    manufactured from one that looks stroked. The bracket is an L with a
    *stepped* inner corner — two changes of direction, not one — traced by a
    metal hairline, and carrying a small lathe medallion near the outer corner.

    Drawn once at the origin and rotated into the other three quadrants, so all
    four are provably the same shape rather than four attempts at it.
    """
    arm = size * 0.42
    chamfer = size * 0.13

    def bracket(scale: float) -> str:
        """An L of arm thickness with a mitred inner elbow.

        The first version stepped the inner edge twice, which at plate scale
        read as a mis-registered corner rather than as a machined one — the
        notch looked like a printing fault. One 45° mitre at the elbow is what
        a die actually leaves, and it is the difference between a corner that
        looks made and one that looks broken.
        """
        s, a, c = size * scale, arm * scale, chamfer * scale
        return (
            f"M0 0 H{s:.2f} V{a:.2f} H{a + c:.2f} L{a:.2f} {a + c:.2f} "
            f"V{s:.2f} H0 Z"
        )

    parts = [
        f'<path d="{bracket(1.0)}" fill="{mass}"/>',
        f'<path d="{bracket(1.0)}" fill="none" stroke="{metal.face}"'
        ' stroke-width="0.45"/>',
        # An inner keyline, held off the mass edge, so the bracket reads as a
        # pressed plate rather than a filled shape with a border.
        f'<g transform="translate({size * 0.075:.2f} {size * 0.075:.2f})">'
        f'<path d="{bracket(0.86)}" fill="none" stroke="{metal.shadow}"'
        ' stroke-width="0.18"/></g>',
    ]
    if inset_medallion:
        mx = my = size * 0.30
        parts.append(
            geo.rosette(mx, my, size * 0.19, ink=metal.face, width=0.10,
                        strength=1.0, passes=3, pitch=1.9)
        )
        parts.append(
            geo.khatam(mx, my, size * 0.155, ink=metal.highlight, width=0.24)
        )
        parts.append(
            f'<circle cx="{mx:.2f}" cy="{my:.2f}" r="{size * 0.205:.2f}"'
            f' fill="none" stroke="{metal.highlight}" stroke-width="0.22"/>'
        )
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) rotate({quadrant * 90})">'
        + "".join(parts)
        + "</g>"
    )


# --- perimeter registers -----------------------------------------------------


def register_stack(rect: geo.Rect, registers: tuple[tuple[float, str], ...], *,
                   metal: Metal, ink: str) -> tuple[str, geo.Rect]:
    """A sequence of perimeter registers, outside → in.

    Each entry is `(width_mm, kind)`. The kinds are the jobs a register can do,
    and the point of naming them is that a register with no job is the thing
    this whole file exists to prevent:

        ``rule``    a single engraved metal line, the register's own edge
        ``field``   a flat band of mass — where the plate gets its weight
        ``girih``   strapwork: the geometric register
        ``lathe``   a guilloché wave band: the security register
        ``micro``   a texture register at the threshold of visibility
        ``void``    deliberate air between two worked registers

    Returns the SVG and the rectangle left inside, so a composition can keep
    stacking without arithmetic.
    """
    out: list[str] = []
    cursor = rect
    for width, kind in registers:
        band = cursor
        if kind == "rule":
            out.append(_perimeter_rule(band, metal=metal, weight=width))
        elif kind == "field":
            out.append(
                f'<path d="M{band.x:.2f} {band.y:.2f} h{band.w:.2f} v{band.h:.2f} '
                f'h{-band.w:.2f} Z M{band.x + width:.2f} {band.y + width:.2f} '
                f'v{band.h - width * 2:.2f} h{band.w - width * 2:.2f} '
                f'v{-(band.h - width * 2):.2f} Z" fill="{ink}"'
                ' fill-rule="evenodd"/>'
            )
        elif kind == "girih":
            out.append(girih_band(band, depth=width, metal=metal))
        elif kind == "lathe":
            out.append(
                geo.guilloche_band(
                    band.inset(width / 2), ink=metal.core, width=0.09,
                    strength=1.0, amplitude=width * 0.40,
                    waves=int(band.w / 2.2),
                )
            )
        elif kind == "micro":
            out.append(
                tessellation_field(band, cell=width * 1.35, ink=metal.core,
                                   strength=0.28, width=0.07,
                                   hollow=width)
            )
        elif kind != "void":
            raise ValueError(f"{kind!r} is not a register kind")
        cursor = cursor.inset(width)
    return "".join(out), cursor


def _perimeter_rule(rect: geo.Rect, *, metal: Metal, weight: float) -> str:
    corners = (
        (rect.x, rect.y, rect.x + rect.w, rect.y),
        (rect.x + rect.w, rect.y, rect.x + rect.w, rect.y + rect.h),
        (rect.x + rect.w, rect.y + rect.h, rect.x, rect.y + rect.h),
        (rect.x, rect.y + rect.h, rect.x, rect.y),
    )
    return "".join(
        engraved_metal_rule(x1, y1, x2, y2, metal=metal, weight=weight)
        for x1, y1, x2, y2 in corners
    )


def tessellation_field(rect: geo.Rect, *, cell: float, ink: str,
                       strength: float = 0.30, width: float = 0.08,
                       hollow: float = 0.0) -> str:
    """The octagon-and-square tiling, allover, at the threshold of visibility.

    A real tiling rather than a scatter: regular octagons on a square lattice
    meet flat-to-flat when the pitch is twice the apothem, and the residual gaps
    are squares standing on the diagonal. Each octagon carries its eight-point
    star, which is the khatam resolving out of the tiling it belongs to.

    `hollow` clears a rectangle of that inset from the centre, so the field can
    be a *band* around a frame rather than a fill behind the words.
    """
    stroke = geo.tint(ink, strength)
    radius = cell / _OCT
    star_r = radius * 0.94
    out: list[str] = []
    columns = int(rect.w // cell) + 2
    rows = int(rect.h // cell) + 2
    for row in range(rows):
        for column in range(columns):
            cx = rect.x + column * cell - cell * 0.5
            cy = rect.y + row * cell - cell * 0.5
            out.append(
                f'<path d="{_ngon(cx, cy, 8, radius, math.pi / 8)}" fill="none"'
                f' stroke="{stroke}" stroke-width="{width:.3f}"/>'
            )
            out.append(
                f'<path d="{geo.star_polygon(cx, cy, 8, star_r, star_r * geo.INNER_RATIO)}"'
                f' fill="none" stroke="{stroke}" stroke-width="{width:.3f}"/>'
            )
            # The square in the gap, standing on its diagonal.
            gx, gy = cx + cell / 2, cy + cell / 2
            side = 2 * radius * math.sin(math.pi / 8)
            out.append(
                f'<path d="{_ngon(gx, gy, 4, side * 0.707, math.pi / 4)}"'
                f' fill="none" stroke="{stroke}" stroke-width="{width:.3f}"/>'
            )
    tag = abs(hash((rect.x, rect.y, rect.w, rect.h, cell, hollow))) % 1000000
    clip = f"tess-{tag}"
    if hollow > 0:
        inner = rect.inset(hollow)
        shape = (
            f'<path d="M{rect.x:.2f} {rect.y:.2f} h{rect.w:.2f} v{rect.h:.2f} '
            f'h{-rect.w:.2f} Z M{inner.x:.2f} {inner.y:.2f} v{inner.h:.2f} '
            f'h{inner.w:.2f} v{-inner.h:.2f} Z" fill-rule="evenodd"/>'
        )
    else:
        shape = f'<rect {rect.attrs()}/>'
    return (
        f'<defs><clipPath id="{clip}">{shape}</clipPath></defs>'
        f'<g clip-path="url(#{clip})">' + "".join(out) + "</g>"
    )


def girih_band(rect: geo.Rect, *, depth: float, metal: Metal,
               pitch: float | None = None) -> str:
    """Strapwork: the geometric register, drawn as ribbon rather than as line.

    A strap is two edges and a face. Here that is one path stroked wide in the
    metal's shadow and stroked again narrow in its face — two flat inks, no
    opacity, and the result reads as an interlaced band because the geometry
    genuinely interlaces. The construction is the same octagon lattice as
    `tessellation_field`, run as a band of one cell.
    """
    step = pitch or depth * 1.6
    radius = step / _OCT
    out_wide: list[str] = []
    out_thin: list[str] = []
    runs = (
        (rect.x, rect.y, rect.w, True),
        (rect.x, rect.y + rect.h - depth, rect.w, True),
        (rect.x, rect.y, rect.h, False),
        (rect.x + rect.w - depth, rect.y, rect.h, False),
    )
    for ox, oy, length, horizontal in runs:
        count = max(1, int(length // step))
        for index in range(count + 1):
            along = index * step + step * 0.5
            cx = ox + (along if horizontal else depth / 2)
            cy = oy + (depth / 2 if horizontal else along)
            figure = (
                f'{_ngon(cx, cy, 8, radius * 0.72, math.pi / 8)}'
                f'{geo.star_polygon(cx, cy, 8, radius * 0.68, radius * 0.68 * geo.INNER_RATIO)}'
            )
            out_wide.append(figure)
            out_thin.append(figure)
    tag = abs(hash((rect.x, rect.y, rect.w, rect.h, depth))) % 1000000
    clip = f"girih-{tag}"
    inner = rect.inset(depth)
    return (
        f'<defs><clipPath id="{clip}">'
        f'<path d="M{rect.x:.2f} {rect.y:.2f} h{rect.w:.2f} v{rect.h:.2f} '
        f'h{-rect.w:.2f} Z M{inner.x:.2f} {inner.y:.2f} v{inner.h:.2f} '
        f'h{inner.w:.2f} v{-inner.h:.2f} Z" fill-rule="evenodd"/>'
        f'</clipPath></defs><g clip-path="url(#{clip})">'
        f'<path d="{"".join(out_wide)}" fill="none" stroke="{metal.shadow}"'
        f' stroke-width="{depth * 0.20:.3f}"/>'
        f'<path d="{"".join(out_thin)}" fill="none" stroke="{metal.highlight}"'
        f' stroke-width="{depth * 0.075:.3f}"/></g>'
    )


# --- field elements ----------------------------------------------------------


def mandala(cx: float, cy: float, radius: float, *, ink: str,
            strength: float = 0.06, rings: int = 5) -> str:
    """The allover central figure: concentric star rings of decreasing order.

    Sixteen points outside, then twelve, then twelve, then eight, then the
    khatam — which is how an illuminated shamsa is actually organised, coarse
    at the rim and resolving towards a centre. Held at a few per cent above the
    paper: this is the thing that makes a field read as *worked* rather than
    blank, and the moment it is legible at arm's length it has become a graphic
    competing with the recipient's name.
    """
    stroke = geo.tint(ink, strength)
    orders = (16, 12, 12, 8, 8)[:rings]
    out: list[str] = []
    for index, points in enumerate(orders):
        outer = radius * (1.0 - index * 0.18)
        inner = outer * (0.74 if points > 8 else geo.INNER_RATIO)
        out.append(
            f'<path d="{geo.star_polygon(cx, cy, points, outer, inner, rotation=index * 0.13)}"'
            f' fill="none" stroke="{stroke}" stroke-width="{0.32 - index * 0.03:.3f}"/>'
        )
    out.append(
        geo.rosette(cx, cy, radius * 0.92, ink=ink, width=0.11,
                    strength=strength * 0.9, passes=3)
    )
    return "".join(out)


def medallion(cx: float, cy: float, radius: float, *, metal: Metal, ink: str,
              legend: str = "", identifier: str = "",
              points: int = 8) -> str:
    """A ceremonial medallion: lathe field, engraved rings, star, emboss.

    Layered the way a struck medal is layered — a turned field, a raised rim, a
    device at the centre — rather than a circle with a star in it. The emboss is
    applied to the device alone, because a medal's rim is struck and its device
    is raised, and doing both makes the whole thing read as a sticker.
    """
    pip = geo.star_polygon(cx, cy, points, radius * 0.30,
                           radius * 0.30 * geo.INNER_RATIO,
                           rotation=math.pi / points)
    device = (
        geo.khatam(cx, cy, radius * 0.46, ink=metal.core, width=0.34)
        + f'<path d="{pip}" fill="none" stroke="{metal.shadow}"'
        ' stroke-width="0.22"/>'
    )
    parts = [
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}"'
        f' fill="none" stroke="{metal.face}" stroke-width="0.62"/>',
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius * 0.965:.2f}"'
        f' fill="none" stroke="{metal.highlight}" stroke-width="0.20"/>',
        geo.rosette(cx, cy, radius * 0.86, ink=metal.core, width=0.09,
                    strength=0.62, passes=3, pitch=2.4),
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius * 0.60:.2f}"'
        f' fill="none" stroke="{metal.shadow}" stroke-width="0.30"/>',
        emboss(device, depth=0.22, light=metal.highlight, dark=metal.shadow),
    ]
    if legend:
        parts.append(
            legend_ring(cx, cy, radius * 0.78, metal=metal, legend=legend,
                        identifier=identifier)
        )
    return "".join(parts)


def legend_ring(cx: float, cy: float, radius: float, *, metal: Metal,
                legend: str, identifier: str = "") -> str:
    """The institution's name and the document's serial, set round a circle.

    Separate from `geometry.seal_ring` because that function draws a *blind
    emboss* — three offset copies in ink tones — and stacking it inside a struck
    metal medallion produced a grey doubled ring that read as a printing fault
    rather than as a seal. A medallion's legend is engraved into the metal, so
    it is set once, in the metal's shadow ink, on a real circular path.
    """
    tag = f"legend-{abs(hash((cx, cy, radius, legend))) % 1000000}"
    text = f"{legend} · {identifier} · " if identifier else f"{legend} · "
    circumference = math.tau * radius
    size = radius * 0.17
    # A whole number of repeats, then stretched to the exact circumference with
    # `textLength`. Over-repeating and letting the path drop the overflow left a
    # visible seam where the tail of one copy sat against the head of the next —
    # the first render read "INSMERIDIAN INSTITUTE", which is a defect on the
    # one element whose whole job is to look precisely made.
    repeats = max(1, round(circumference / max(1.0, len(text) * size * 0.62)))
    body = text * repeats
    return (
        f'<defs><path id="{tag}" fill="none"'
        f' d="M{cx - radius:.2f} {cy:.2f}'
        f' a{radius:.2f} {radius:.2f} 0 1 1 0 0.01"/></defs>'
        f'<text font-size="{size:.2f}" font-family="Inter, sans-serif"'
        f' textLength="{circumference - 0.4:.2f}" lengthAdjust="spacing"'
        f' fill="{metal.shadow}">'
        f'<textPath href="#{tag}">{body}</textPath></text>'
    )


def cresting(cx: float, y: float, width: float, height: float, *,
             metal: Metal) -> str:
    """The ornament that sits above a frame and breaks its top line.

    A palmette: a central lobe rising to a finial, two counter-scrolled wings,
    and a base rule. It exists to stop the frame's top edge from being the
    highest thing on the sheet — which is the difference between a document that
    is framed and one that is *crowned*.
    """
    half = width / 2
    # Filled, not stroked. A stroked outline at this size reads as a tent
    # pitched on the frame; a palmette is a *shape*, and its silhouette against
    # the paper is the whole effect.
    body = (
        f"M{cx - half:.2f} {y:.2f} "
        f"C{cx - half * 0.72:.2f} {y - height * 0.14:.2f} "
        f"{cx - half * 0.58:.2f} {y - height * 0.46:.2f} "
        f"{cx - half * 0.34:.2f} {y - height * 0.40:.2f} "
        f"C{cx - half * 0.22:.2f} {y - height * 0.38:.2f} "
        f"{cx - half * 0.16:.2f} {y - height * 0.72:.2f} {cx:.2f} {y - height:.2f} "
        f"C{cx + half * 0.16:.2f} {y - height * 0.72:.2f} "
        f"{cx + half * 0.22:.2f} {y - height * 0.38:.2f} "
        f"{cx + half * 0.34:.2f} {y - height * 0.40:.2f} "
        f"C{cx + half * 0.58:.2f} {y - height * 0.46:.2f} "
        f"{cx + half * 0.72:.2f} {y - height * 0.14:.2f} {cx + half:.2f} {y:.2f} Z"
    )
    return (
        f'<path d="{body}" fill="{metal.face}" stroke="{metal.shadow}"'
        ' stroke-width="0.22" stroke-linejoin="round"/>'
        f'<path d="M{cx:.2f} {y - height * 0.10:.2f} V{y - height * 0.82:.2f}"'
        f' stroke="{metal.shadow}" stroke-width="0.18"/>'
        + geo.khatam(cx, y - height * 1.24, height * 0.26, ink=metal.face,
                     width=0.36)
        + engraved_metal_rule(cx - half, y, cx + half, y, metal=metal,
                              weight=0.42)
    )


def spreader(y: float, x1: float, x2: float, *, metal: Metal,
             stops: int = 2) -> str:
    """A hairline with lozenge stops — the rule that separates without dividing.

    Used to run left and right from a crest or a title. The lozenges are what
    stop it reading as an underline: a rule that terminates in a diamond has
    been *placed*, and one that simply ends has been drawn to a margin.
    """
    out = [engraved_metal_rule(x1, y, x2, y, metal=metal, weight=0.30)]
    span = x2 - x1
    for index in range(stops + 1):
        cx = x1 + span * (index / stops if stops else 0.5)
        size = 0.95 if index in (0, stops) else 1.35
        out.append(
            f'<path d="{geo.star_polygon(cx, y, 4, size, size * 0.34)}"'
            f' fill="{metal.face}" stroke="{metal.shadow}"'
            ' stroke-width="0.10"/>'
        )
    return "".join(out)


def vertical_spine(x: float, y1: float, y2: float, *, metal: Metal,
                   nodes: int = 3) -> str:
    """The ornament that runs down the inside of a left or right register.

    A thin rule with lozenge nodes and a small khatam at each terminal. It gives
    a tall register something to be about, and it is the reason the left and
    right edges of a landscape plate do not read as leftover.
    """
    out = [engraved_metal_rule(x, y1, x, y2, metal=metal, weight=0.26)]
    for index in range(nodes):
        cy = y1 + (y2 - y1) * ((index + 1) / (nodes + 1))
        out.append(
            f'<path d="{geo.star_polygon(x, cy, 4, 1.5, 0.5)}"'
            f' fill="{metal.face}" stroke="{metal.shadow}" stroke-width="0.10"/>'
        )
    for cy in (y1, y2):
        out.append(geo.khatam(x, cy, 1.9, ink=metal.face, width=0.22))
    return "".join(out)


def radiant_field(cx: float, cy: float, radius: float, *, metal: Metal,
                  rays: int = 48, inner: float = 0.22) -> str:
    """Tapered rays from a centre — the luminous field for a dark ground.

    Each ray is a real triangle rather than a stroked line, so the taper is
    geometric and holds at any scale. On a midnight ground this is what a metal
    register looks like when it is lit from the centre; on ivory it is far too
    loud, and the compositions that use it say so.
    """
    out: list[str] = []
    for index in range(rays):
        angle = (index / rays) * math.tau
        spread = (math.tau / rays) * 0.38
        tip = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        a = (cx + radius * inner * math.cos(angle - spread),
             cy + radius * inner * math.sin(angle - spread))
        b = (cx + radius * inner * math.cos(angle + spread),
             cy + radius * inner * math.sin(angle + spread))
        colour = metal.shadow if index % 2 else metal.core
        out.append(
            f'<path d="M{a[0]:.2f} {a[1]:.2f} L{tip[0]:.2f} {tip[1]:.2f} '
            f'L{b[0]:.2f} {b[1]:.2f} Z" fill="{colour}"/>'
        )
    return "".join(out)


def _ngon(cx: float, cy: float, sides: int, radius: float,
          rotation: float = 0.0) -> str:
    parts: list[str] = []
    for index in range(sides):
        angle = rotation + (index / sides) * math.tau
        parts.append(
            f"{'L' if index else 'M'}{cx + radius * math.cos(angle):.3f} "
            f"{cy + radius * math.sin(angle):.3f}"
        )
    return "".join(parts) + "Z"
