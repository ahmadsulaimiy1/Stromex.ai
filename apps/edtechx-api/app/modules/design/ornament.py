"""The EdirasX geometric system, constructed rather than drawn.

EdirasX takes its name from الدراسة. The identity therefore comes from Islamic
geometric construction rather than from calligraphy pasted onto a screen, and
the construction is the actual one: two squares rotated 45° to each other,
producing the eight-point star — خاتم سليمان, the seal — whose *central negative
space is a cross*. So the X of EdirasX is the void at the centre of the star.
The Latin letterform is produced by the Arabic geometry rather than placed
beside it, which is the whole idea and the reason this module computes the
points instead of shipping a picture of them.

Everything below derives from one function, `star_points`. That is the
discipline: a mark, a rule terminator, a bullet, a watermark lattice and a
loading indicator that are all the same construction at different scales read
as one identity. Five separately-drawn decorations read as a moodboard.

**How much of it appears is a theme setting.** `none` for an institution that
wants only its own marks; `restrained` — the default — for rule terminators and
active indicators; `full` adds section markers and empty-state figures;
`ceremonial` adds the watermark lattice to documents. An institution never has
to accept our geometry to use the product.
"""

from __future__ import annotations

import math
from typing import Final

__all__ = [
    "corner",
    "lattice",
    "monogram",
    "node",
    "rule",
    "spinner",
    "star_path",
    "star_points",
]

#: Ratio of the inner radius to the outer, derived from the construction rather
#: than chosen. Square A's edge from (R,0) to (0,R) is the line x + y = R;
#: square B's edge from (R/√2, R/√2) to (−R/√2, R/√2) is y = R/√2. They cross at
#: (R − R/√2, R/√2), whose distance from the centre is √(2 − √2) · R.
#:
#: This was wrong once, at 1/(1+√2) ≈ 0.414, and the difference is not academic:
#: the mark rendered as a spiky starburst rather than as a seal, and looked like
#: a decorative asterisk in every place the identity appears. Broad points are
#: what make it read as a seal.
INNER_RATIO: Final[float] = math.sqrt(2 - math.sqrt(2))


def star_points(
    cx: float, cy: float, radius: float, *, points: int = 8, rotation: float = 0.0
) -> list[tuple[float, float]]:
    """The vertices of the seal, alternating outer and inner.

    `rotation` is in degrees. At 0 the star sits point-up; at 22.5 it sits
    flat-topped, which is what the rule terminator wants so the horizontal
    hairline meets a horizontal edge rather than a spike.
    """
    inner = radius * INNER_RATIO
    step = math.pi / points
    offset = math.radians(rotation) - math.pi / 2
    vertices: list[tuple[float, float]] = []
    for index in range(points * 2):
        r = radius if index % 2 == 0 else inner
        angle = offset + index * step
        vertices.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return vertices


def star_path(
    cx: float, cy: float, radius: float, *, points: int = 8, rotation: float = 0.0
) -> str:
    vertices = star_points(cx, cy, radius, points=points, rotation=rotation)
    head = f"M {vertices[0][0]:.3f} {vertices[0][1]:.3f}"
    tail = " ".join(f"L {x:.3f} {y:.3f}" for x, y in vertices[1:])
    return f"{head} {tail} Z"


def node(size: float = 8, *, colour: str = "currentColor", rotation: float = 22.5) -> str:
    """The signature mark at small scale.

    Appears at the origin of every section rule, on the active navigation item,
    as a list bullet on ceremonial documents, and nowhere else. Its job is to be
    noticed on the fourth screen rather than the first.
    """
    half = size / 2
    return (
        f'<svg class="ed-node" width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'aria-hidden="true" focusable="false">'
        f'<path d="{star_path(half, half, half, rotation=rotation)}" fill="{colour}"/>'
        f"</svg>"
    )


def rule(*, gold: bool = True, width: str = "100%") -> str:
    """A hairline with the seal at its origin — the system's most repeated move.

    A rule that begins with a node instead of simply beginning is the difference
    between a divider and a piece of design, and it costs eight pixels.
    """
    tone = "var(--accent-metal)" if gold else "var(--border-strong)"
    return (
        f'<div class="ed-rule" style="--rule-width:{width}">'
        f'{node(7, colour=tone)}'
        f'<span class="ed-rule__line"></span>'
        f"</div>"
    )


def monogram(size: float = 40, *, gold: str = "var(--accent-metal)",
             ink: str = "var(--text-primary)") -> str:
    """The EdirasX mark: the seal, with the X drawn by its own construction.

    Two elements. The seal in gold, outlined. Then the X — not placed in the
    middle, but drawn *between opposite inner vertices of the star itself*.
    Those vertices are where the two squares cross, so the X is a line the
    construction already contains; the mark reveals it rather than adding it.
    That is the whole conceit of the identity, and it is why this is computed
    from `star_points` rather than drawn.

    An earlier version filled a black octagon in the centre and cut the X out of
    it. It read as a target rather than as a seal — the ink mass overwhelmed the
    gold — which is the sort of thing only looking at it will tell you.
    """
    half = size / 2
    outer = half * 0.94
    vertices = star_points(half, half, outer, rotation=22.5)
    inner = [v for index, v in enumerate(vertices) if index % 2 == 1]
    # Inner vertices sit at 22.5° + 45k. The pairs 45° apart from the vertical
    # are the diagonals, and the two strokes between opposite ones are the X.
    stroke = max(1.1, size * 0.085)
    bars = "".join(
        f'<path d="M {inner[a][0]:.3f} {inner[a][1]:.3f} '
        f'L {inner[b][0]:.3f} {inner[b][1]:.3f}" stroke="{ink}" '
        f'stroke-width="{stroke:.2f}" stroke-linecap="butt"/>'
        for a, b in ((0, 4), (2, 6))
    )
    return (
        f'<svg class="ed-monogram" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" role="img" aria-label="EdirasX" fill="none">'
        f'<path d="{star_path(half, half, outer, rotation=22.5)}" stroke="{gold}" '
        f'stroke-width="{max(0.9, size * 0.05):.2f}" stroke-linejoin="miter"/>'
        f"{bars}"
        f"</svg>"
    )


def lattice(*, cell: float = 72, colour: str = "var(--accent-metal)") -> str:
    """A tessellation of the seal, for ceremonial grounds and watermarks.

    Emitted as an SVG `<pattern>` so it tiles at any size without a raster
    asset. Opacity is a theme variable rather than an argument: an institution
    sets how present its ornament is once, and every surface obeys.
    """
    half = cell / 2
    return (
        f'<svg class="ed-lattice" aria-hidden="true" focusable="false" '
        f'width="100%" height="100%">'
        f'<defs><pattern id="ed-seal" width="{cell}" height="{cell}" '
        f'patternUnits="userSpaceOnUse">'
        f'<path d="{star_path(half, half, cell * 0.21, rotation=22.5)}" '
        f'fill="none" stroke="{colour}" stroke-width="0.8"/>'
        f'<path d="{star_path(0, 0, cell * 0.21, rotation=22.5)}" '
        f'fill="none" stroke="{colour}" stroke-width="0.8"/>'
        f'<path d="{star_path(cell, 0, cell * 0.21, rotation=22.5)}" '
        f'fill="none" stroke="{colour}" stroke-width="0.8"/>'
        f'<path d="{star_path(0, cell, cell * 0.21, rotation=22.5)}" '
        f'fill="none" stroke="{colour}" stroke-width="0.8"/>'
        f'<path d="{star_path(cell, cell, cell * 0.21, rotation=22.5)}" '
        f'fill="none" stroke="{colour}" stroke-width="0.8"/>'
        f"</pattern></defs>"
        f'<rect width="100%" height="100%" fill="url(#ed-seal)"/>'
        f"</svg>"
    )


def corner(size: float = 34, *, colour: str = "var(--accent-metal)") -> str:
    """An L-bracket meeting the seal. Frames a ceremonial document.

    Four of these at the corners of a certificate do what an ornamental border
    would do, at a fraction of the visual noise — which is the argument of the
    whole system in one component. The bracket *meets* the node rather than
    floating near it; a gap there reads as a mistake rather than as restraint.
    """
    inset = 1.5
    node_r = size * 0.155
    stop = size * 0.62
    return (
        f'<svg class="ed-corner" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" aria-hidden="true" focusable="false">'
        f'<path d="M {inset} {stop:.2f} L {inset} {inset} L {stop:.2f} {inset}" '
        f'fill="none" stroke="{colour}" stroke-width="0.8"/>'
        f'<path d="{star_path(stop, stop, node_r, rotation=22.5)}" fill="{colour}"/>'
        f'<path d="M {inset} {stop:.2f} L {stop - node_r:.2f} {stop - node_r:.2f}" '
        f'fill="none" stroke="{colour}" stroke-width="0.75" opacity="0.5"/>'
        f"</svg>"
    )


def spinner(size: float = 20, *, colour: str = "var(--accent-metal)") -> str:
    """The loading indicator: a node travelling the seal's own circle.

    A dashed outline of a broad-pointed star reads as a broken shape rather than
    as motion, which is what the first attempt did. A single node orbiting a
    faint seal is unambiguous, and it turns at 1.6s rather than the usual 0.8s —
    a fast spinner communicates anxiety, and an institution's software should not
    appear to be panicking.
    """
    half = size / 2
    orbit = half * 0.86
    dot = max(1.6, size * 0.11)
    return (
        f'<svg class="ed-spinner" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" role="status" aria-label="Loading">'
        f'<path d="{star_path(half, half, half * 0.9, rotation=22.5)}" '
        f'fill="none" stroke="{colour}" stroke-width="0.9" opacity="0.3"/>'
        f'<path d="{star_path(half - orbit, half, dot, rotation=22.5)}" fill="{colour}"/>'
        f"</svg>"
    )
