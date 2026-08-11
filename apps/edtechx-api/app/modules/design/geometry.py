"""Constructed geometry for documents, in millimetres.

Everything a ceremonial EdirasX document draws is generated here from a closed
mathematical construction. Nothing is traced, nothing is a stock asset, and
nothing is a raster: a plate built from this module is exact at 300 DPI, at 600,
and at 2400, because it has no resolution to begin with.

The unit is the **millimetre**, not the pixel, and that is the whole posture of
this file. A document is a physical object that will be printed, photographed,
scanned by an embassy, and looked at under a loupe by somebody deciding whether
to believe it. Designing it in pixels and converting at the end is how the
hairlines end up at three-quarters of the press's minimum stroke.

Four rules govern every function below. Each was learned from studying a
security-print implementation that had already made the mistake and written
down what it cost.

**No opacity on a hairline. Ever.** A 0.1mm stroke at 40% opacity becomes a
*screen percentage* at separation, and a screened hairline is the first thing to
drop off press — the line simply is not there on the printed sheet. So every
pale tone here is pre-mixed against the paper by `tint()` and emitted as a flat
hex. The ink is specified, not a tint of it.

**Guilloché is lathe work, not swirls.** An epitrochoid with `R` and `r`
coprime closes only after `r/gcd(R,r)` turns, and its lobe count is
`R/gcd(R,r)`. That regularity *is* the security property: a curve you can
describe in three integers is one a forger has to solve rather than trace. The
lathe spec is chosen **by scale**, so a 5mm medallion and a 100mm field are cut
at the same visual grain — a fixed 61-lobe figure that reads beautifully across
a sheet collapses into a smudge at medallion size.

**An engraved line is three strokes, not one.** A lit edge, the ink, and a
shadow wall. One stroke with a gradient is a screen effect; three solid strokes
is how an engraving actually reflects light, and it survives being printed in
one colour.

**Determinism, so two printings are the same plate.** Anything that looks
random — paper fibres, ornament phase — comes from a seeded LCG keyed on the
document's own serial. The same document renders identically forever, which is
what makes "this is not the sheet we issued" a statement anybody can check.

**And one honesty rule, which is the reason this docstring is long.** The names
in this file describe constructions, not protections. An anti-copy screen is a
line screen chosen to beat against a copier's own screen angles; it is *not* a
latent image, which needs a coarse and a fine ruling at matched ink fraction
with a shape defined between them. Microtext here is real vector text on a
path carrying the live serial — whether it survives a given printer is a
question about that printer, answered in `EDTECHX_DOCUMENT_SECURITY.md`, not a
claim this module makes. Nothing here is cryptography. The cryptography is in
`documents/integrity.py`, and conflating the two is exactly the theatre this
codebase refuses.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

__all__ = [
    "INNER_RATIO",
    "LATHE",
    "PAPER",
    "Rect",
    "arabesque_band",
    "corner_frame",
    "engraved_rule",
    "epitrochoid",
    "fibres",
    "guilloche_band",
    "interlocking_squares",
    "khatam",
    "lattice_field",
    "line_screen",
    "microtext_ring",
    "rosette",
    "seal_ring",
    "star_polygon",
    "tint",
]

#: The two-square construction EdirasX is drawn from: a square and its 45°
#: rotation, whose eight intersections give the star. The inner radius is
#: √(2−√2) of the outer, which is arithmetic rather than taste — it is what the
#: construction produces, and using anything else makes the star a spiky
#: asterisk rather than a khatam. Shared with `ornament.py`, which draws the
#: same figure at interface scale.
INNER_RATIO: Final[float] = math.sqrt(2 - math.sqrt(2))

#: Warm ivory, as ink on paper rather than as a screen colour. Every pale tone
#: in this module is mixed towards this and emitted flat.
PAPER: Final[tuple[int, int, int]] = (0xF7, 0xF2, 0xE6)

#: Lathe specifications, ordered by lobe count. `R` and `r` are coprime in every
#: row, so each figure closes only after `r` turns and cannot be approximated by
#: a shorter one. Chosen by scale rather than fixed — see `rosette`.
LATHE: Final[tuple[tuple[int, int, float], ...]] = (
    (11, 2, 2.3),
    (17, 3, 3.4),
    (23, 4, 4.6),
    (31, 5, 5.7),
    (43, 6, 6.9),
    (61, 7, 8.0),
    (73, 8, 9.0),
    (89, 9, 11.0),
    # Added when the grain test ran the table at sheet scale: at a 110mm field
    # the 89-lobe figure comes out at a 7.8mm petal pitch, which is a different
    # visual grain from every medallion on the same sheet. A rose engine does
    # not change its cut because the plate got bigger.
    (127, 10, 13.0),
)


@dataclass(frozen=True, slots=True)
class Rect:
    """A rectangle in millimetres from the sheet's top-left corner."""

    x: float
    y: float
    w: float
    h: float

    def inset(self, by: float) -> Rect:
        return Rect(self.x + by, self.y + by, self.w - by * 2, self.h - by * 2)

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def attrs(self) -> str:
        return (
            f'x="{self.x:.2f}" y="{self.y:.2f}" '
            f'width="{self.w:.2f}" height="{self.h:.2f}"'
        )


def tint(hex_colour: str, strength: float) -> str:
    """Mix an ink towards the paper and return a flat hex.

    `strength` is how far from the paper towards the ink: 1.0 is the ink itself,
    0.05 is a whisper. The point of returning a *colour* rather than an opacity
    is stated in the module docstring and is the single most consequential rule
    in this file.
    """
    value = int(hex_colour.lstrip("#"), 16)
    channels = ((value >> 16) & 255, (value >> 8) & 255, value & 255)
    mixed = (
        max(0, min(255, round(PAPER[i] + (channels[i] - PAPER[i]) * strength)))
        for i in range(3)
    )
    return "#" + "".join(f"{c:02X}" for c in mixed).upper()


def _gcd(a: int, b: int) -> int:
    return math.gcd(int(a), int(b)) or 1


# --- the curves -------------------------------------------------------------


def epitrochoid(cx: float, cy: float, big: float, small: float, pen: float,
                *, steps: int | None = None) -> str:
    """One lathe pass, as an SVG path.

    `big` is the fixed wheel, `small` the rolling wheel, `pen` the pen offset —
    the three numbers on a rose engine. The step count is derived from the lobe
    count rather than fixed: at a flat 1440 steps a 61-lobe figure gets
    twenty-three points per petal and prints faceted.
    """
    lobes = big / _gcd(round(big), round(small)) if small else 1
    count = steps or max(720, round(lobes * 28))
    ratio = (big + small) / small if small else 1
    turns = small / _gcd(round(big), round(small)) if small else 1

    parts: list[str] = []
    for index in range(count + 1):
        t = (index / count) * math.tau * turns
        x = (big + small) * math.cos(t) - pen * math.cos(ratio * t)
        y = (big + small) * math.sin(t) - pen * math.sin(ratio * t)
        parts.append(f"{'L' if index else 'M'}{cx + x:.2f} {cy + y:.2f}")
    return "".join(parts) + "Z"


def rosette(cx: float, cy: float, radius: float, *, ink: str, width: float,
            strength: float, passes: int = 3, pitch: float = 3.0) -> str:
    """Several counter-phased lathe passes. Depth comes from the crossing.

    The specification is chosen so the petal pitch at the outer radius lands
    near `pitch` millimetres whatever the scale, which is what keeps every
    rosette on a sheet cut at the same visual grain. One fixed spec across a
    document gives you a beautiful sheet field and four illegible medallions.
    """
    if radius <= 0:
        return ""
    wanted = (math.tau * radius) / pitch
    base = min(range(len(LATHE)), key=lambda i: abs(LATHE[i][0] - wanted))
    stroke = tint(ink, strength)

    out: list[str] = []
    for index in range(passes):
        spec = LATHE[max(0, min(len(LATHE) - 1, base - index))]
        big, small, pen = spec
        scale = radius / (big + small + pen)
        rotation = (index * 360) / (passes * 7)
        out.append(
            f'<path d="{epitrochoid(cx, cy, big * scale, small * scale, pen * scale)}"'
            f' fill="none" stroke="{stroke}" stroke-width="{width:.3f}"'
            f' transform="rotate({rotation:.2f} {cx:.2f} {cy:.2f})"/>'
        )
    return "".join(out)


def guilloche_band(rect: Rect, *, ink: str, width: float = 0.10,
                   strength: float = 0.42, amplitude: float = 1.6,
                   waves: int = 96, passes: int = 3) -> str:
    """A wave band running the perimeter — the border register of lathe work.

    Three counter-phased sine passes rather than one, for the same reason a
    rosette has three: a single wave is a decoration and three that cross are a
    pattern with a period somebody would have to derive.
    """
    stroke = tint(ink, strength)
    out: list[str] = []
    for index in range(passes):
        phase = (index / passes) * math.tau
        parts: list[str] = []
        # Walk the perimeter as four runs so the wave keeps its phase round
        # the corners instead of restarting on each side.
        edges = (
            ((rect.x, rect.y), (rect.x + rect.w, rect.y), 0.0, 1.0),
            ((rect.x + rect.w, rect.y), (rect.x + rect.w, rect.y + rect.h), -1.0, 0.0),
            ((rect.x + rect.w, rect.y + rect.h), (rect.x, rect.y + rect.h), 0.0, -1.0),
            ((rect.x, rect.y + rect.h), (rect.x, rect.y), 1.0, 0.0),
        )
        travelled = 0.0
        perimeter = 2 * (rect.w + rect.h)
        for (x1, y1), (x2, y2), nx, ny in edges:
            length = math.hypot(x2 - x1, y2 - y1)
            steps = max(24, round(length * 2))
            for step in range(steps + 1):
                fraction = step / steps
                along = travelled + length * fraction
                offset = amplitude * math.sin(
                    (along / perimeter) * math.tau * waves + phase
                )
                px = x1 + (x2 - x1) * fraction + nx * offset
                py = y1 + (y2 - y1) * fraction + ny * offset
                parts.append(f"{'L' if parts else 'M'}{px:.2f} {py:.2f}")
            travelled += length
        out.append(
            f'<path d="{"".join(parts)}Z" fill="none" stroke="{stroke}"'
            f' stroke-width="{width:.3f}"/>'
        )
    return "".join(out)


# --- the star vocabulary ----------------------------------------------------


def star_polygon(cx: float, cy: float, points: int, outer: float, inner: float,
                 *, rotation: float = 0.0) -> str:
    """An n-fold star, from rotation rather than from a drawing."""
    parts: list[str] = []
    for index in range(points * 2):
        angle = (index * math.pi) / points + rotation
        radius = inner if index % 2 else outer
        parts.append(
            f"{'L' if index else 'M'}{cx + radius * math.cos(angle):.3f} "
            f"{cy + radius * math.sin(angle):.3f}"
        )
    return "".join(parts) + "Z"


def khatam(cx: float, cy: float, radius: float, *, ink: str, width: float = 0.2,
           strength: float = 1.0, rotation: float = 0.0) -> str:
    """EdirasX's own mark: the eight-point seal from two squares.

    Not a star drawn with eight arms. A square and its 45° rotation, whose
    intersections define the points — which is why `INNER_RATIO` is
    √(2−√2) and not a number somebody liked the look of.
    """
    stroke = tint(ink, strength)
    return (
        f'<path d="{star_polygon(cx, cy, 8, radius, radius * INNER_RATIO, rotation=rotation)}"'
        f' fill="none" stroke="{stroke}" stroke-width="{width:.3f}"'
        ' stroke-linejoin="miter"/>'
    )


def interlocking_squares(cx: float, cy: float, radius: float, *, ink: str,
                         width: float = 0.2, strength: float = 1.0,
                         rotation: float = 0.0) -> str:
    """The construction itself, shown rather than resolved.

    Used where a document wants to say *how* its geometry is made — a
    ceremonial register, and one that only earns its place on the most
    formal documents.
    """
    stroke = tint(ink, strength)
    side = radius * math.sqrt(2)
    out: list[str] = []
    for turn in (0.0, 45.0):
        out.append(
            f'<rect x="{cx - side / 2:.2f}" y="{cy - side / 2:.2f}"'
            f' width="{side:.2f}" height="{side:.2f}" fill="none"'
            f' stroke="{stroke}" stroke-width="{width:.3f}"'
            f' transform="rotate({turn + rotation:.2f} {cx:.2f} {cy:.2f})"/>'
        )
    return "".join(out)


def lattice_field(rect: Rect, *, cell: float, ink: str, width: float = 0.08,
                  strength: float = 0.10, rotation: float = 0.0) -> str:
    """A khatam lattice across a field, at the threshold of visibility.

    Deliberately quiet. A watermark that competes with the text is a graphic;
    one that is noticed on the second look is a watermark. The first render of
    this at four times the strength read as a pattern printed *over* a
    certificate rather than milled into its paper.
    """
    stroke = tint(ink, strength)
    out: list[str] = []
    radius = cell / 2
    rows = int(rect.h // cell) + 2
    columns = int(rect.w // cell) + 2
    for row in range(rows):
        for column in range(columns):
            cx = rect.x + column * cell - cell / 2
            cy = rect.y + row * cell - cell / 2
            out.append(
                f'<path d="{star_polygon(cx, cy, 8, radius * 0.86, radius * 0.86 * INNER_RATIO)}"'
                f' fill="none" stroke="{stroke}" stroke-width="{width:.3f}"/>'
            )
    clip = f"clip-{abs(hash((rect.x, rect.y, rect.w, rect.h, cell))) % 100000}"
    return (
        f'<defs><clipPath id="{clip}"><rect {rect.attrs()}/></clipPath></defs>'
        f'<g clip-path="url(#{clip})"'
        f' transform="rotate({rotation:.2f} {rect.cx:.2f} {rect.cy:.2f})">'
        + "".join(out)
        + "</g>"
    )


def arabesque_band(rect: Rect, *, ink: str, width: float = 0.14,
                   strength: float = 0.6, period: float = 12.0,
                   depth: float = 2.2) -> str:
    """A curve band: two counter-running arcs meeting at each node.

    The one curved element in the vocabulary, and the reason it is a
    *construction* rather than a drawn scroll is that it has to tile round a
    corner without a seam. Each period is a pair of quadratic arcs mirrored
    about the node, so the tangent at every junction is horizontal and two
    adjacent periods meet smoothly by definition rather than by adjustment.
    """
    stroke = tint(ink, strength)
    out: list[str] = []
    for x1, y1, x2, _y2 in (
        (rect.x, rect.y, rect.x + rect.w, rect.y),
        (rect.x, rect.y + rect.h, rect.x + rect.w, rect.y + rect.h),
    ):
        length = x2 - x1
        count = max(2, round(length / period))
        step = length / count
        parts = [f"M{x1:.2f} {y1:.2f}"]
        for index in range(count):
            sx = x1 + step * index
            sign = 1 if index % 2 == 0 else -1
            parts.append(
                f"Q{sx + step / 2:.2f} {y1 + depth * sign:.2f} {sx + step:.2f} {y1:.2f}"
            )
        out.append(
            f'<path d="{"".join(parts)}" fill="none" stroke="{stroke}"'
            f' stroke-width="{width:.3f}"/>'
        )
    return "".join(out)


# --- engraving ---------------------------------------------------------------


def engraved_rule(rect: Rect, *, ink: str, weight: float = 0.5,
                  lit: str = "#FFFFFF", shadow: str | None = None) -> str:
    """A rule that reads as cut into the sheet: lit edge, ink, shadow wall.

    Three solid strokes. One stroke with a gradient is a screen effect that
    prints as a muddy band; this survives being separated into one colour
    because each of the three is a real ink at a real weight.
    """
    shadow_ink = shadow or ink
    return (
        f'<rect {rect.inset(-weight * 0.75).attrs()} fill="none"'
        f' stroke="{tint(lit, 0.55)}" stroke-width="{weight * 0.45:.3f}"/>'
        f'<rect {rect.attrs()} fill="none" stroke="{tint(ink, 1.0)}"'
        f' stroke-width="{weight:.3f}"/>'
        f'<rect {rect.inset(weight * 0.6).attrs()} fill="none"'
        f' stroke="{tint(shadow_ink, 0.55)}" stroke-width="{weight * 0.30:.3f}"/>'
    )


def corner_frame(x: float, y: float, size: float, *, ink: str,
                 quadrant: int = 0, strength: float = 0.8,
                 arcs: int = 6) -> str:
    """A corner: concentric quarter-arcs under the institution's own star.

    Drawn once and mirrored by transform into the other three corners, so all
    four are provably identical rather than four attempts at the same thing.
    """
    stroke = tint(ink, strength)
    parts: list[str] = []
    for index in range(1, arcs + 1):
        radius = (size * index) / (arcs + 1)
        parts.append(
            f'<path d="M0 {radius:.2f} A {radius:.2f} {radius:.2f} 0 0 1 {radius:.2f} 0"'
            f' fill="none" stroke="{stroke}"'
            f' stroke-width="{0.10 + index * 0.010:.3f}"/>'
        )
    parts.append(khatam(size * 0.40, size * 0.40, size * 0.17, ink=ink, width=0.18))
    rotation = quadrant * 90
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) rotate({rotation})">'
        + "".join(parts)
        + "</g>"
    )


def seal_ring(cx: float, cy: float, radius: float, *, ink: str,
              legend: str = "", identifier: str = "") -> str:
    """A blind-embossed seal: relief only, no colour fill.

    An emboss is felt more than seen. Simulated with light — a pale copy offset
    down-right beneath the ink copy, giving a lit wall on one side and a shadow
    wall on the other. Never a drop shadow, and never tinted: filling an emboss
    with colour destroys both the illusion and the dignity, and turns a
    governance mark into a sticker.
    """
    def figure(dx: float, dy: float, colour: str) -> str:
        return (
            f'<circle cx="{cx + dx:.2f}" cy="{cy + dy:.2f}" r="{radius:.2f}"'
            f' fill="none" stroke="{colour}" stroke-width="0.45"/>'
            f'<circle cx="{cx + dx:.2f}" cy="{cy + dy:.2f}" r="{radius * 0.87:.2f}"'
            f' fill="none" stroke="{colour}" stroke-width="0.18"/>'
            + khatam(cx + dx, cy + dy, radius * 0.52, ink="#000000", width=0.28,
                     strength=0.0).replace('stroke="' + tint("#000000", 0.0) + '"',
                                           f'stroke="{colour}"')
        )

    legend_svg = ""
    if legend:
        path_id = f"seal-{abs(hash((cx, cy, legend))) % 100000}"
        text = f"{legend} · {identifier} · " if identifier else f"{legend} · "
        legend_svg = (
            f'<defs><path id="{path_id}" fill="none"'
            f' d="M{cx - radius * 0.72:.2f} {cy:.2f}'
            f' a{radius * 0.72:.2f} {radius * 0.72:.2f} 0 1 1 0 0.01"/></defs>'
            f'<text font-size="{radius * 0.15:.2f}"'
            f' letter-spacing="{radius * 0.03:.2f}" fill="{tint(ink, 0.42)}">'
            f'<textPath href="#{path_id}">{text * 3}</textPath></text>'
        )
    return (
        "<g>"
        + figure(0.35, 0.35, tint(ink, 0.30))
        + figure(-0.15, -0.15, tint("#FFFFFF", 0.75))
        + figure(0, 0, tint(ink, 0.48))
        + legend_svg
        + "</g>"
    )


# --- the substrate -----------------------------------------------------------


def _lcg(seed: str):
    """A seeded generator, so two printings of one plate are one plate."""
    state = 0
    for character in str(seed):
        state = (state * 31 + ord(character)) & 0xFFFFFFFF
    def rnd() -> float:
        nonlocal state
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        return state / 4294967296
    return rnd


def fibres(rect: Rect, *, seed: str, count: int = 140) -> str:
    """Paper fibres, deterministic from the document's own serial.

    Cosmetic — and named as cosmetic. A fibre drawn in ink is not a fibre
    embedded in a substrate, and this makes a sheet *look* like security paper
    without being any. It is here because a ceremonial document printed on
    ordinary stock should still read as considered, and it is documented as
    appearance in `EDTECHX_DOCUMENT_SECURITY.md` so nobody later mistakes it
    for a feature.
    """
    rnd = _lcg(seed)
    tints = [tint(c, 0.34) for c in
             ("#C9B6D8", "#B8C9D8", "#D8C9B0", "#C0D0BC", "#D6BCC2")]
    out: list[str] = []
    for index in range(count):
        x = rect.x + rnd() * rect.w
        y = rect.y + rnd() * rect.h
        angle = rnd() * math.tau
        length = 1.4 + rnd() * 3.4
        bow = (rnd() - 0.5) * 1.5
        x2 = x + math.cos(angle) * length
        y2 = y + math.sin(angle) * length
        mx = (x + x2) / 2 - math.sin(angle) * bow
        my = (y + y2) / 2 + math.cos(angle) * bow
        out.append(
            f'<path d="M{x:.2f} {y:.2f} Q{mx:.2f} {my:.2f} {x2:.2f} {y2:.2f}"'
            f' fill="none" stroke="{tints[index % len(tints)]}"'
            ' stroke-width="0.09"/>'
        )
    return "".join(out)


def line_screen(identifier: str, *, degrees: float, pitch: float,
                width: float, ink: str, strength: float) -> str:
    """An anti-copy line screen, set off a copier's own angles.

    **Not a latent image.** A latent image needs a coarse and a fine ruling at
    matched ink fraction with a shape defined between them, so that the shape
    appears only when the copier's screen beats against one ruling and not the
    other. This is a single ruling, and calling it latent would be a claim the
    construction does not support.

    The stroke is held at or above 0.07mm — the practical screen floor — and
    the ink is pre-tinted, so the pattern never needs an opacity.
    """
    return (
        f'<pattern id="{identifier}" width="{pitch}" height="{pitch}"'
        f' patternUnits="userSpaceOnUse" patternTransform="rotate({degrees})">'
        f'<line x1="0" y1="0" x2="0" y2="{pitch}"'
        f' stroke="{tint(ink, strength)}" stroke-width="{max(width, 0.07):.3f}"/>'
        "</pattern>"
    )


def microtext_ring(rect: Rect, *, identifier: str, text: str, ink: str,
                   size: float = 0.62, strength: float = 0.55) -> str:
    """Real vector text on the perimeter, carrying the live serial.

    Text rather than a texture, and the document's *own* serial rather than the
    institution's name, because a ring that repeats the same string on every
    sheet distinguishes nothing. Whether it survives a particular printer is a
    question about that printer; this module guarantees only that the character
    data is there at the specified size, and the assessment lives in
    `EDTECHX_DOCUMENT_SECURITY.md`.
    """
    path_id = f"micro-{identifier}"
    perimeter = 2 * (rect.w + rect.h)
    # Roughly 0.52mm per character at this size; over-repeat and let the path
    # clip rather than leave a gap somebody would read as a defect.
    repeats = max(1, int(perimeter / max(1.0, len(text) * 0.52)) + 1)
    return (
        f'<defs><path id="{path_id}" fill="none" d="M{rect.x + 2:.2f} {rect.y:.2f}'
        f' H{rect.x + rect.w:.2f} V{rect.y + rect.h:.2f}'
        f' H{rect.x:.2f} V{rect.y:.2f} Z"/></defs>'
        f'<text font-size="{size:.2f}" font-family="monospace"'
        f' fill="{tint(ink, strength)}" aria-hidden="true">'
        f'<textPath href="#{path_id}">{text * repeats}</textPath></text>'
    )
