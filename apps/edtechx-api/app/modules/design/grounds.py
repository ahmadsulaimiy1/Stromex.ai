"""A library of premium grounds — the fields a ceremonial sheet is printed on.

Twenty-five backgrounds, in five families, every one a construction rather than
an image. They are the answer to "bring in many premium backgrounds, in many
different styles", built the way this codebase can actually use them.

**Why these are generated and not collected.** Three reasons, in order of how
much they cost:

*Resolution.* A collected background is a raster. The reference implementation
this project learned from records exactly what that costs: its supplied master
was a 1080 × 772 JPEG, which over a 297 × 210mm sheet is 92 DPI, and only 17 %
of its spectral energy sat inside 12 % of Nyquist — so there was no latent
detail to recover and no enlargement that would produce 300 DPI. Every ground
here is exact at 300 DPI, at 600 and at 2400, because it has no resolution to
begin with.

*Press behaviour.* A ground has to separate. These are flat inks at stated
stroke widths with no opacity anywhere, so a printer can pull them onto a plate;
a JPEG of a pattern has to be screened, and a screened fine ground fills in.

*Provenance.* A certificate is a legal instrument that an embassy or a
credential evaluator may have to stand behind, so every element on it needs a
known origin and a known licence. A pinboard is an index of other people's
copyrighted work rather than a source, so nothing is taken from one. Where an
institution holds a licence for third-party artwork, that asset should come in
through a register recording source, licence and attribution — and this
environment has no outbound network access to fetch anything from anywhere in
any case.

**Five families, because "background" is not one thing.**

    security     engine-turning, wave lathe, moiré guard, ripple, pinstripe.
                 What a banknote or a share certificate is printed on.
    textile      damask, basketweave, herringbone, scale, chevron, lozenge.
                 What a bookbinder's endpaper or a court hanging looks like.
    paper        laid, vellum, marbled veins, starfield. The substrate itself,
                 rather than something printed on it.
    geometric    girih diaper, ogee lattice, strapwork, rosette grid, honeycomb,
                 medallion field. The Islamic geometric families.
    illumination arabesque scroll, crosshatch, sunburst, diaper of stars.
                 What an illuminated page carries behind its text block.

**Every ground takes a strength and means it.** A ground at 0.03 is a substrate;
at 0.15 it is a pattern; at 0.4 it is a wallpaper and the document is ruined.
The `suggested` field on each entry is where it belongs for a ceremonial sheet,
and `ceremony.Budget.content_ink` is what enforces it behind the words.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from app.modules.design import geometry as geo

__all__ = ["GROUNDS", "Ground", "catalogue", "ground_for"]


def _rng(seed: str) -> Callable[[], float]:
    """The same deterministic LCG the rest of the package uses.

    Randomness in a document is a contradiction: two printings of one
    certificate must be the same plate, so anything that looks scattered is
    seeded on something stable.
    """
    state = 0
    for character in str(seed):
        state = (state * 31 + ord(character)) & 0xFFFFFFFF

    def draw() -> float:
        nonlocal state
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        return state / 4294967296.0

    return draw


def _clip(rect: geo.Rect, body: str, tag: str) -> str:
    return (
        f'<defs><clipPath id="{tag}"><rect {rect.attrs()}/></clipPath></defs>'
        f'<g clip-path="url(#{tag})">{body}</g>'
    )


def _path(d: str, ink: str, width: float) -> str:
    return (
        f'<path d="{d}" fill="none" stroke="{ink}"'
        f' stroke-width="{max(0.07, width):.3f}"/>'
    )


# --- security -----------------------------------------------------------------


def engine_turn(rect: geo.Rect, *, ink: str, strength: float,
                scale: float = 1.0) -> str:
    """Engine-turning: overlapping lathe roses on a lattice.

    The field a share certificate is printed on. Each rose is a closed
    epitrochoid, so the pattern is describable in three integers and has to be
    solved rather than traced.
    """
    stroke = geo.tint(ink, strength)
    pitch = 22.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / pitch) + 2):
        for column in range(int(rect.w / pitch) + 2):
            cx = rect.x + column * pitch - pitch / 2
            cy = rect.y + row * pitch - pitch / 2
            out.append(
                f'<path d="{geo.epitrochoid(cx, cy, 31, 5, 5.7, scale=pitch / 84)}"'
                f' fill="none" stroke="{stroke}" stroke-width="0.08"/>'
            )
    return _clip(rect, "".join(out), f"eng-{abs(hash((rect.x, pitch))) % 99999}")


def wave_lathe(rect: geo.Rect, *, ink: str, strength: float,
               scale: float = 1.0) -> str:
    """Two interfering sine rulings — the banknote wave field."""
    stroke = geo.tint(ink, strength)
    step = 1.6 * scale
    out: list[str] = []
    for index in range(int(rect.h / step) + 1):
        y = rect.y + index * step
        points = []
        for i in range(0, int(rect.w) + 2, 2):
            x = rect.x + i
            offset = (math.sin(x / (9.0 * scale) + index * 0.42) * 1.1 * scale
                      + math.sin(x / (23.0 * scale) - index * 0.17) * 1.7 * scale)
            points.append(f"{'L' if i else 'M'}{x:.2f} {y + offset:.2f}")
        out.append(_path("".join(points), stroke, 0.08))
    return _clip(rect, "".join(out), f"wav-{abs(hash((rect.y, step))) % 99999}")


def moire_guard(rect: geo.Rect, *, ink: str, strength: float,
                scale: float = 1.0) -> str:
    """Two rulings at beat angles — a copier's screen fights this, not the eye."""
    stroke = geo.tint(ink, strength)
    out: list[str] = []
    # 0.5mm pitch put ~190 rulings each way across a 96mm swatch and the field
    # rendered as a flat grey wash — a tone, not a guard. A guard has to *read*
    # as two rulings for the beat to be visible at all.
    for degrees, pitch in ((7.0, 2.6 * scale), (52.0, 3.1 * scale)):
        angle = math.radians(degrees)
        span = rect.w + rect.h
        count = int(span / pitch)
        for index in range(count):
            offset = index * pitch - rect.h
            x1 = rect.x + offset
            out.append(_path(
                f"M{x1:.2f} {rect.y:.2f} "
                f"L{x1 + rect.h * math.tan(angle):.2f} {rect.y + rect.h:.2f}",
                stroke, 0.07))
    return _clip(rect, "".join(out), f"moi-{abs(hash((rect.w, scale))) % 99999}")


def ripple(rect: geo.Rect, *, ink: str, strength: float,
           scale: float = 1.0) -> str:
    """Concentric fine circles from an off-centre origin."""
    stroke = geo.tint(ink, strength)
    cx, cy = rect.x + rect.w * 0.34, rect.y + rect.h * 0.42
    step = 1.5 * scale
    limit = max(rect.w, rect.h) * 1.3
    out = [
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none"'
        f' stroke="{stroke}" stroke-width="0.08"/>'
        for r in [step * i for i in range(1, int(limit / step))]
    ]
    return _clip(rect, "".join(out), f"rip-{abs(hash((cx, step))) % 99999}")


def pinstripe(rect: geo.Rect, *, ink: str, strength: float,
              scale: float = 1.0) -> str:
    """A metal pinstripe: paired rules, one heavy one fine."""
    stroke = geo.tint(ink, strength)
    fine = geo.tint(ink, strength * 0.45)
    pitch = 3.4 * scale
    out: list[str] = []
    for index in range(int(rect.w / pitch) + 1):
        x = rect.x + index * pitch
        out.append(_path(f"M{x:.2f} {rect.y:.2f} V{rect.y + rect.h:.2f}", stroke, 0.10))
        out.append(_path(f"M{x + pitch * 0.32:.2f} {rect.y:.2f} "
                         f"V{rect.y + rect.h:.2f}", fine, 0.07))
    return _clip(rect, "".join(out), f"pin-{abs(hash((rect.x, pitch))) % 99999}")


# --- textile ------------------------------------------------------------------


def damask(rect: geo.Rect, *, ink: str, strength: float,
           scale: float = 1.0) -> str:
    """An ogee damask: the pointed-oval diaper of a court hanging."""
    stroke = geo.tint(ink, strength)
    w, h = 18.0 * scale, 26.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / h) + 2):
        for column in range(int(rect.w / w) + 2):
            cx = rect.x + column * w + (w / 2 if row % 2 else 0) - w
            cy = rect.y + row * h - h
            out.append(_path(
                f"M{cx:.2f} {cy:.2f} "
                f"C{cx + w * 0.55:.2f} {cy + h * 0.18:.2f} "
                f"{cx + w * 0.55:.2f} {cy + h * 0.82:.2f} {cx:.2f} {cy + h:.2f} "
                f"C{cx - w * 0.55:.2f} {cy + h * 0.82:.2f} "
                f"{cx - w * 0.55:.2f} {cy + h * 0.18:.2f} {cx:.2f} {cy:.2f} Z",
                stroke, 0.09))
            out.append(_path(
                f"M{cx - w * 0.16:.2f} {cy + h * 0.5:.2f} "
                f"q{w * 0.16:.2f} {-h * 0.13:.2f} {w * 0.32:.2f} 0 "
                f"q{-w * 0.16:.2f} {h * 0.13:.2f} {-w * 0.32:.2f} 0",
                stroke, 0.08))
    return _clip(rect, "".join(out), f"dam-{abs(hash((w, h))) % 99999}")


def basketweave(rect: geo.Rect, *, ink: str, strength: float,
                scale: float = 1.0) -> str:
    """Over-and-under: three rules one way, three the other, alternating."""
    stroke = geo.tint(ink, strength)
    cell = 7.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / cell) + 1):
        for column in range(int(rect.w / cell) + 1):
            x, y = rect.x + column * cell, rect.y + row * cell
            horizontal = (row + column) % 2 == 0
            for index in range(3):
                offset = cell * (0.25 + index * 0.25)
                if horizontal:
                    out.append(_path(f"M{x:.2f} {y + offset:.2f} h{cell:.2f}",
                                     stroke, 0.09))
                else:
                    out.append(_path(f"M{x + offset:.2f} {y:.2f} v{cell:.2f}",
                                     stroke, 0.09))
    return _clip(rect, "".join(out), f"bas-{abs(hash((cell, rect.w))) % 99999}")


def herringbone(rect: geo.Rect, *, ink: str, strength: float,
                scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    cell = 5.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / cell) + 1):
        for column in range(int(rect.w / (cell * 2)) + 1):
            x = rect.x + column * cell * 2 + (cell if row % 2 else 0)
            y = rect.y + row * cell
            out.append(_path(f"M{x:.2f} {y + cell:.2f} l{cell:.2f} {-cell:.2f} "
                             f"l{cell:.2f} {cell:.2f}", stroke, 0.09))
    return _clip(rect, "".join(out), f"her-{abs(hash((cell, rect.h))) % 99999}")


def scales(rect: geo.Rect, *, ink: str, strength: float,
           scale: float = 1.0) -> str:
    """Imbricated scales — the oldest diaper there is."""
    stroke = geo.tint(ink, strength)
    r = 5.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / r) + 2):
        for column in range(int(rect.w / (r * 2)) + 2):
            cx = rect.x + column * r * 2 + (r if row % 2 else 0) - r
            cy = rect.y + row * r
            out.append(_path(
                f"M{cx - r:.2f} {cy:.2f} a{r:.2f} {r:.2f} 0 0 0 {r * 2:.2f} 0",
                stroke, 0.09))
    return _clip(rect, "".join(out), f"sca-{abs(hash((r, rect.x))) % 99999}")


def chevron(rect: geo.Rect, *, ink: str, strength: float,
            scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    step = 3.2 * scale
    out: list[str] = []
    for index in range(int(rect.h / step) + int(rect.w / step) + 2):
        y = rect.y + index * step - rect.w / 2
        points = []
        for i in range(0, int(rect.w) + 8, 8):
            x = rect.x + i
            points.append(f"{'L' if i else 'M'}{x:.2f} "
                          f"{y + (i % 16) * 0.5 * scale:.2f}")
        out.append(_path("".join(points), stroke, 0.08))
    return _clip(rect, "".join(out), f"chv-{abs(hash((step, rect.y))) % 99999}")


def lozenge(rect: geo.Rect, *, ink: str, strength: float,
            scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    w, h = 9.0 * scale, 13.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / h) + 2):
        for column in range(int(rect.w / w) + 2):
            cx = rect.x + column * w + (w / 2 if row % 2 else 0) - w
            cy = rect.y + row * h - h
            out.append(_path(
                f"M{cx:.2f} {cy - h / 2:.2f} L{cx + w / 2:.2f} {cy:.2f} "
                f"L{cx:.2f} {cy + h / 2:.2f} L{cx - w / 2:.2f} {cy:.2f} Z",
                stroke, 0.09))
    return _clip(rect, "".join(out), f"loz-{abs(hash((w, h, rect.x))) % 99999}")


# --- paper --------------------------------------------------------------------


def laid(rect: geo.Rect, *, ink: str, strength: float,
         scale: float = 1.0) -> str:
    """Laid lines and chain lines — mould-made paper, seen against the light."""
    stroke = geo.tint(ink, strength)
    chain = geo.tint(ink, strength * 1.7)
    out: list[str] = []
    pitch = 1.05 * scale
    for index in range(int(rect.h / pitch) + 1):
        y = rect.y + index * pitch
        out.append(_path(f"M{rect.x:.2f} {y:.2f} h{rect.w:.2f}", stroke, 0.07))
    for index in range(int(rect.w / (26.0 * scale)) + 1):
        x = rect.x + index * 26.0 * scale
        out.append(_path(f"M{x:.2f} {rect.y:.2f} v{rect.h:.2f}", chain, 0.12))
    return _clip(rect, "".join(out), f"lai-{abs(hash((pitch, rect.w))) % 99999}")


def vellum(rect: geo.Rect, *, ink: str, strength: float,
           scale: float = 1.0, seed: str = "vellum") -> str:
    """Irregular short fibres and a soft mottle — a skin rather than a sheet."""
    draw = _rng(seed)
    stroke = geo.tint(ink, strength)
    out: list[str] = []
    for _ in range(int(rect.w * rect.h / 90)):
        x = rect.x + draw() * rect.w
        y = rect.y + draw() * rect.h
        angle = draw() * math.tau
        length = (0.9 + draw() * 2.6) * scale
        out.append(_path(
            f"M{x:.2f} {y:.2f} l{math.cos(angle) * length:.2f} "
            f"{math.sin(angle) * length:.2f}", stroke, 0.07))
    return _clip(rect, "".join(out), f"vel-{abs(hash(seed)) % 99999}")


def marbled(rect: geo.Rect, *, ink: str, strength: float,
            scale: float = 1.0, seed: str = "marble") -> str:
    """Combed veins — a bookbinder's marbled endpaper, as line rather than wash."""
    draw = _rng(seed)
    out: list[str] = []
    for band in range(26):
        tone = geo.tint(ink, strength * (0.55 + draw() * 0.75))
        y0 = rect.y + (band / 26) * rect.h
        points = []
        for i in range(0, int(rect.w) + 4, 4):
            x = rect.x + i
            wave = (math.sin(x / (17.0 * scale) + band) * 2.6 * scale
                    + math.sin(x / (5.5 * scale) + band * 2.1) * 0.9 * scale)
            points.append(f"{'L' if i else 'M'}{x:.2f} {y0 + wave:.2f}")
        out.append(_path("".join(points), tone, 0.10))
    return _clip(rect, "".join(out), f"mar-{abs(hash(seed)) % 99999}")


def starfield(rect: geo.Rect, *, ink: str, strength: float,
              scale: float = 1.0, seed: str = "stars") -> str:
    """Small scattered stars — the powdered ground of an illuminated page."""
    draw = _rng(seed)
    stroke = geo.tint(ink, strength)
    out: list[str] = []
    for _ in range(int(rect.w * rect.h / 320)):
        cx = rect.x + draw() * rect.w
        cy = rect.y + draw() * rect.h
        r = (0.7 + draw() * 0.9) * scale
        out.append(_path(geo.star_polygon(cx, cy, 6, r, r * 0.42), stroke, 0.08))
    return _clip(rect, "".join(out), f"str-{abs(hash(seed)) % 99999}")


# --- geometric ----------------------------------------------------------------


def ogee_lattice(rect: geo.Rect, *, ink: str, strength: float,
                 scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    w, h = 14.0 * scale, 16.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / h) + 2):
        for column in range(int(rect.w / w) + 2):
            cx = rect.x + column * w + (w / 2 if row % 2 else 0) - w
            cy = rect.y + row * h - h
            out.append(_path(
                f"M{cx - w / 2:.2f} {cy:.2f} "
                f"q{w / 4:.2f} {-h / 2:.2f} {w / 2:.2f} 0 "
                f"q{w / 4:.2f} {h / 2:.2f} {w / 2:.2f} 0", stroke, 0.09))
    return _clip(rect, "".join(out), f"oge-{abs(hash((w, h))) % 99999}")


def honeycomb(rect: geo.Rect, *, ink: str, strength: float,
              scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    r = 4.2 * scale
    dx, dy = r * 1.5, r * math.sqrt(3)
    out: list[str] = []
    for row in range(int(rect.h / dy) + 2):
        for column in range(int(rect.w / dx) + 2):
            cx = rect.x + column * dx - dx
            cy = rect.y + row * dy + (dy / 2 if column % 2 else 0) - dy
            points = "".join(
                f"{'L' if i else 'M'}{cx + r * math.cos(i * math.tau / 6):.2f} "
                f"{cy + r * math.sin(i * math.tau / 6):.2f}" for i in range(6)
            )
            out.append(_path(points + "Z", stroke, 0.08))
    return _clip(rect, "".join(out), f"hon-{abs(hash((r, rect.w))) % 99999}")


def strapwork(rect: geo.Rect, *, ink: str, strength: float,
              scale: float = 1.0) -> str:
    """Interlaced straps: one path stroked wide, then narrow, to read as ribbon."""
    wide = geo.tint(ink, strength)
    core = geo.tint(ink, strength * 0.35)
    cell = 11.0 * scale
    figures: list[str] = []
    for row in range(int(rect.h / cell) + 2):
        for column in range(int(rect.w / cell) + 2):
            cx = rect.x + column * cell - cell
            cy = rect.y + row * cell - cell
            figures.append(geo.star_polygon(cx, cy, 8, cell * 0.46,
                                            cell * 0.46 * geo.INNER_RATIO))
    body = "".join(figures)
    return _clip(rect, _path(body, wide, 0.28 * scale) + _path(body, core, 0.10),
                 f"stp-{abs(hash((cell, rect.h))) % 99999}")


def rosette_grid(rect: geo.Rect, *, ink: str, strength: float,
                 scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    cell = 15.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / cell) + 2):
        for column in range(int(rect.w / cell) + 2):
            cx = rect.x + column * cell - cell
            cy = rect.y + row * cell - cell
            for radius in (cell * 0.42, cell * 0.26, cell * 0.12):
                out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}"'
                           f' fill="none" stroke="{stroke}" stroke-width="0.08"/>')
            out.append(_path(geo.star_polygon(cx, cy, 8, cell * 0.34,
                                              cell * 0.16), stroke, 0.08))
    return _clip(rect, "".join(out), f"ros-{abs(hash((cell, rect.x))) % 99999}")


def medallion_field(rect: geo.Rect, *, ink: str, strength: float,
                    scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    cell = 26.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / cell) + 2):
        for column in range(int(rect.w / cell) + 2):
            cx = rect.x + column * cell + (cell / 2 if row % 2 else 0) - cell
            cy = rect.y + row * cell - cell
            out.append(geo.khatam(cx, cy, cell * 0.30, ink=stroke, width=0.10))
            out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}"'
                       f' r="{cell * 0.36:.2f}" fill="none" stroke="{stroke}"'
                       ' stroke-width="0.08"/>')
    return _clip(rect, "".join(out), f"med-{abs(hash((cell, rect.h))) % 99999}")


def girih_diaper(rect: geo.Rect, *, ink: str, strength: float,
                 scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    cell = 12.0 * scale
    radius = cell / (2 * math.cos(math.pi / 8))
    out: list[str] = []
    for row in range(int(rect.h / cell) + 2):
        for column in range(int(rect.w / cell) + 2):
            cx = rect.x + column * cell - cell
            cy = rect.y + row * cell - cell
            points = "".join(
                f"{'L' if i else 'M'}"
                f"{cx + radius * math.cos(math.pi / 8 + i * math.tau / 8):.2f} "
                f"{cy + radius * math.sin(math.pi / 8 + i * math.tau / 8):.2f}"
                for i in range(8)
            )
            out.append(_path(points + "Z", stroke, 0.08))
            out.append(_path(geo.star_polygon(cx, cy, 8, radius * 0.94,
                                              radius * 0.94 * geo.INNER_RATIO),
                             stroke, 0.08))
    return _clip(rect, "".join(out), f"gir-{abs(hash((cell, rect.w))) % 99999}")


# --- illumination -------------------------------------------------------------


def arabesque_scroll(rect: geo.Rect, *, ink: str, strength: float,
                     scale: float = 1.0) -> str:
    """A running scroll of counter-curved stems with leaf terminals."""
    stroke = geo.tint(ink, strength)
    period = 20.0 * scale
    row_h = 14.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / row_h) + 2):
        y = rect.y + row * row_h
        for column in range(int(rect.w / period) + 2):
            x = rect.x + column * period + (period / 2 if row % 2 else 0) - period
            out.append(_path(
                f"M{x:.2f} {y:.2f} "
                f"c{period * 0.18:.2f} {-row_h * 0.34:.2f} "
                f"{period * 0.34:.2f} {-row_h * 0.34:.2f} "
                f"{period * 0.5:.2f} 0 "
                f"c{period * 0.16:.2f} {row_h * 0.34:.2f} "
                f"{period * 0.32:.2f} {row_h * 0.34:.2f} "
                f"{period * 0.5:.2f} 0", stroke, 0.09))
            out.append(_path(
                f"M{x + period * 0.5:.2f} {y - row_h * 0.16:.2f} "
                f"q{period * 0.08:.2f} {-row_h * 0.22:.2f} "
                f"{period * 0.02:.2f} {-row_h * 0.34:.2f}", stroke, 0.08))
    return _clip(rect, "".join(out), f"ara-{abs(hash((period, row_h))) % 99999}")


def crosshatch(rect: geo.Rect, *, ink: str, strength: float,
               scale: float = 1.0) -> str:
    """Engraver's crosshatch: two rulings at 45° and 135°."""
    stroke = geo.tint(ink, strength)
    pitch = 1.3 * scale
    out: list[str] = []
    span = rect.w + rect.h
    for sign in (1, -1):
        for index in range(int(span / pitch)):
            offset = index * pitch - rect.h
            out.append(_path(
                f"M{rect.x + offset:.2f} {rect.y:.2f} "
                f"l{sign * rect.h:.2f} {rect.h:.2f}", stroke, 0.07))
    return _clip(rect, "".join(out), f"cro-{abs(hash((pitch, rect.x))) % 99999}")


def sunburst(rect: geo.Rect, *, ink: str, strength: float,
             scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    cx, cy = rect.cx, rect.cy
    reach = max(rect.w, rect.h)
    rays = max(48, int(160 / scale))
    out = [
        _path(f"M{cx:.2f} {cy:.2f} "
              f"L{cx + reach * math.cos(i * math.tau / rays):.2f} "
              f"{cy + reach * math.sin(i * math.tau / rays):.2f}", stroke, 0.08)
        for i in range(rays)
    ]
    return _clip(rect, "".join(out), f"sun-{abs(hash((rays, rect.w))) % 99999}")


def diaper_of_stars(rect: geo.Rect, *, ink: str, strength: float,
                    scale: float = 1.0) -> str:
    stroke = geo.tint(ink, strength)
    cell = 8.0 * scale
    out: list[str] = []
    for row in range(int(rect.h / cell) + 2):
        for column in range(int(rect.w / cell) + 2):
            cx = rect.x + column * cell + (cell / 2 if row % 2 else 0) - cell
            cy = rect.y + row * cell - cell
            out.append(_path(geo.star_polygon(cx, cy, 6, cell * 0.30,
                                              cell * 0.13), stroke, 0.08))
            out.append(_path(f"M{cx + cell / 2:.2f} {cy:.2f} h0.6", stroke, 0.08))
    return _clip(rect, "".join(out), f"dia-{abs(hash((cell, rect.y))) % 99999}")


@dataclass(frozen=True, slots=True)
class Ground:
    key: str
    name: str
    family: str
    draw: Callable[..., str]
    #: Where this belongs on a ceremonial sheet. Above it, the ground stops
    #: being a substrate and starts being wallpaper.
    suggested: float
    note: str


GROUNDS: Final[dict[str, Ground]] = {
    g.key: g for g in (
        Ground("engine-turn", "Engine turning", "security", engine_turn, 0.055,
               "Overlapping closed lathe roses. The share-certificate field."),
        Ground("wave-lathe", "Wave lathe", "security", wave_lathe, 0.050,
               "Two interfering sine rulings; the banknote wave."),
        Ground("moire-guard", "Moiré guard", "security", moire_guard, 0.040,
               "Two rulings at beat angles. Not a latent image."),
        Ground("ripple", "Ripple", "security", ripple, 0.045,
               "Concentric fine circles from an off-centre origin."),
        Ground("pinstripe", "Metal pinstripe", "security", pinstripe, 0.045,
               "Paired rules, one heavy one fine — reads as brushed metal."),
        Ground("damask", "Ogee damask", "textile", damask, 0.060,
               "The pointed-oval diaper of a court hanging."),
        Ground("basketweave", "Basketweave", "textile", basketweave, 0.055,
               "Over-and-under; three rules each way, alternating."),
        Ground("herringbone", "Herringbone", "textile", herringbone, 0.055,
               "A tailoring ground; quiet at small scale, strong at large."),
        Ground("scales", "Imbricated scales", "textile", scales, 0.055,
               "The oldest diaper there is."),
        Ground("chevron", "Chevron", "textile", chevron, 0.045,
               "A running zigzag ruling."),
        Ground("lozenge", "Lozenge diaper", "textile", lozenge, 0.055,
               "Diamond lattice; the heraldic ground."),
        Ground("laid", "Laid paper", "paper", laid, 0.045,
               "Laid lines and chain lines — mould-made paper against light."),
        Ground("vellum", "Vellum", "paper", vellum, 0.055,
               "Irregular short fibres; a skin rather than a sheet."),
        Ground("marbled", "Marbled veins", "paper", marbled, 0.070,
               "Combed veins as line rather than wash; a bookbinder's endpaper."),
        Ground("starfield", "Powdered stars", "paper", starfield, 0.070,
               "The powdered ground of an illuminated page."),
        Ground("ogee-lattice", "Ogee lattice", "geometric", ogee_lattice, 0.055,
               "Counter-curved arcs meeting at the ogee."),
        Ground("honeycomb", "Honeycomb", "geometric", honeycomb, 0.045,
               "Hexagonal close-pack; the densest quiet ground."),
        Ground("strapwork", "Strapwork", "geometric", strapwork, 0.070,
               "Interlaced ribbon: one path stroked wide, then narrow."),
        Ground("rosette-grid", "Rosette grid", "geometric", rosette_grid, 0.055,
               "Concentric rings with an eight-point star at each node."),
        Ground("medallion-field", "Medallion field", "geometric",
               medallion_field, 0.060,
               "Khatam medallions on a staggered lattice."),
        Ground("girih-diaper", "Girih diaper", "geometric", girih_diaper, 0.055,
               "The octagon-and-square tiling with its star."),
        Ground("arabesque-scroll", "Arabesque scroll", "illumination",
               arabesque_scroll, 0.060,
               "Counter-curved stems with leaf terminals."),
        Ground("crosshatch", "Engraver's crosshatch", "illumination",
               crosshatch, 0.035,
               "Two rulings at 45° and 135°; the shading of an engraving."),
        Ground("sunburst", "Sunburst", "illumination", sunburst, 0.035,
               "Radiating hairlines. Loud on ivory; correct on a dark ground."),
        Ground("diaper-of-stars", "Diaper of stars", "illumination",
               diaper_of_stars, 0.055,
               "Six-point stars on a staggered lattice with stops between."),
    )
}


def ground_for(key: str) -> Ground:
    if key not in GROUNDS:
        raise ValueError(
            f"{key!r} is not a ground. One of: " + ", ".join(sorted(GROUNDS))
        )
    return GROUNDS[key]


def catalogue(family: str = "") -> tuple[Ground, ...]:
    """Every ground, or every ground in one family, in declaration order."""
    return tuple(g for g in GROUNDS.values() if not family or g.family == family)
