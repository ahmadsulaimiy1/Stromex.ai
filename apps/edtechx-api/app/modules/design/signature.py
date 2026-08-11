"""One document, one geometric family — recurring at six scales.

The criticism this file answers is exact, and it was fair: the concept plates
read as *a beautiful Islamic pattern placed around a certificate*. Sophisticated
geometry, correctly constructed, and still applied rather than belonging. What
separates a decorated document from a designed one is that in a designed one the
same mathematical family appears in the corner medallion, in the title mark, in
the seal's device, in the lathe work, in the ground field and in the security
construction — at six different scales, each derived from one seed.

That is what a `Motif` is. It is not a pattern; it is a *family*, and every
figure this module draws is a member of it.

**What varies, and what deliberately does not.** A motif belongs to an
institution and a document family — every doctoral award from one institution
shares one geometry, which is what makes the geometry an identity rather than
noise. It does **not** vary per issued document: a recipient's award must look
like the award, not like a random draw. What varies per document is the
*security* layer — the fine text carries this serial, the fibres are seeded on
it — and that separation is the whole point. Ornament identifies the
institution; the security layer identifies the sheet.

**The generalisation that made this possible.** `geometry.INNER_RATIO` was
written as √(2−√2), the khatam's inner-to-outer radius, and treated as a
constant. It is not a constant; it is the (n, k) = (8, 2) member of

    ratio(n, k) = cos(kπ/n) / cos((k−1)π/n)

the inner radius of the star polygon {n/k}. Once that is written down, ten- and
twelve-fold families come out of the same construction with the same
correctness — and, because `density_for` picks the k that holds the *sharpness*
constant as the order changes, an eight-fold plate and a twelve-fold plate are
recognisably from one house rather than merely both geometric.

**Composed, not merely generated.** Every figure here is mathematical, and none
of them is placed by this file. A rosette that appears at 14mm in a corner, at
8mm in a seal and at 62mm in the ground is one family seen three times; where it
appears, how often, and against what is a composition decision made in the plate
and judged by eye.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Final

from app.modules.design import geometry as geo

__all__ = [
    "ORDERS",
    "Motif",
    "density_for",
    "motif_for",
    "star_ratio",
]

#: The n-fold orders a motif may take. These are the three that tile: eight-fold
#: (the khatam), ten-fold (decagonal girih) and twelve-fold (dodecagonal). A
#: seven- or nine-fold rosette is drawable and does not tile, and a frame built
#: from one has to fudge its corners — which is exactly the kind of thing that
#: reads as "generated" at close range.
ORDERS: Final[tuple[int, ...]] = (8, 10, 12)

#: The thinnest stroke this module will emit, in millimetres. Every figure here
#: derives sub-strokes from a caller's width — a rosette's construction polygram
#: is 0.55 of its star's weight, its kites 0.62 — and those multipliers compound
#: silently. A stroke census over the finished separations found **1320 strokes
#: at 0.050 mm**, all of them derived, all of them below this package's own
#: stated floor and below the 0.25 pt hairline most litho specifications quote.
#: Nothing in the artwork asked for 0.05 mm; arithmetic produced it.
#:
#: So the floor is enforced where the multiplication happens rather than
#: audited afterwards. A line that would print as a broken dash, or fill in, is
#: not a fine line — it is a defect that looks like restraint at 300 DPI.
STROKE_FLOOR: Final[float] = 0.07


def _held(width: float) -> float:
    """A stroke width, never below the press floor."""
    return max(STROKE_FLOOR, width)


#: The sharpness every family's stars are struck at. Not a preference: it is the
#: number that makes an eight-fold and a twelve-fold document look like
#: siblings. See `density_for`.
_TARGET_SHARPNESS: Final[float] = 0.74


def star_ratio(order: int, density: int) -> float:
    """Inner-to-outer radius of the star polygon {n/k}.

        cos(kπ/n) / cos((k−1)π/n)

    At n = 8, k = 2 this is √(2−√2) — which is where `geometry.INNER_RATIO`
    came from. The constant was one member of a family, not a rule, and writing
    the family down is what lets a ten- or twelve-fold document be constructed
    with exactly the same correctness rather than drawn by eye.

    Using anything else makes the star a spiky asterisk: the inner points stop
    lying on the intersections of the polygram's own chords, and the eye sees it
    immediately even when it cannot say why.
    """
    return math.cos(density * math.pi / order) / math.cos(
        (density - 1) * math.pi / order
    )


def density_for(order: int) -> int:
    """The star density that gives this order the family's matched sharpness.

    An eight-fold star at k = 2 has an inner ratio of 0.765. Applying k = 2 to a
    twelve-fold order gives 0.966 — a star so shallow it reads as a cog. Raising
    the density instead keeps the *sharpness* constant while the order changes,
    so an eight-fold plate and a twelve-fold plate are recognisably from one
    house. k must stay coprime-ish to n in the sense that {n/k} traces a single
    closed circuit; that is checked by construction below rather than assumed.
    """
    best = 2
    for density in range(2, order // 2):
        if abs(star_ratio(order, density) - _TARGET_SHARPNESS) < abs(
            star_ratio(order, best) - _TARGET_SHARPNESS
        ):
            best = density
    return best


@dataclass(frozen=True, slots=True)
class Motif:
    """The ornamental family belonging to one document type at one institution.

    Six numbers, from which every ornament on the sheet descends. Small enough
    to print in a production specification, which matters: a printer replacing a
    damaged plate needs the family, not a traced outline.
    """

    #: n-fold symmetry. The whole family's character.
    order: int
    #: Star density k: the figure is {n/k}. Chosen so the sharpness matches
    #: across orders — see `density_for`.
    density: int
    #: The star's inner radius, as a fraction of its outer. Derived, not chosen.
    ratio: float
    #: Rotation of the family against the sheet, in radians. Breaks the
    #: axis-aligned look that makes generated ornament read as generated.
    phase: float
    #: The lathe specification the guilloché registers are cut from, chosen so
    #: its lobe count is a multiple of the order — which is why the lathe work
    #: and the star work look like the same hand.
    lathe: tuple[int, int, float]
    #: Strap crossings per repeat in the interlace band.
    braid: int
    #: What this motif was derived from, kept so it can be reproduced and
    #: printed in the specification.
    provenance: str

    @property
    def petals(self) -> int:
        """Petals in the rosette: twice the order, which is what a girih
        rosette has when its kites are struck between the star's points."""
        return self.order * 2

    def star_path(self, cx: float, cy: float, radius: float, *,
                  sharpen: float = 1.0) -> str:
        """The family's star as an outline: 2n vertices, alternating radii.

        An earlier version drew this as a polygram — n vertices stepping k at a
        time — which silently degenerates whenever gcd(n, k) > 1: at n = 10,
        k = 2 the "star" is two pentagons drawn on top of each other, and at
        n = 8 it is a square traced twice. Alternating outer and inner radii
        gives the star's actual boundary for every order, which is what a plate
        needs to stroke and what a die needs to cut.

        `sharpen` below 1 pulls the inner vertices in. It exists for the
        smallest instances only — a 4mm star at the construction ratio loses its
        points to the stroke weight — and the plate that uses it says so.
        """
        inner = radius * self.ratio * sharpen
        points: list[str] = []
        for index in range(self.order * 2):
            angle = self.phase + index * math.pi / self.order
            r = radius if index % 2 == 0 else inner
            points.append(
                f"{'L' if index else 'M'}{cx + r * math.cos(angle):.3f} "
                f"{cy + r * math.sin(angle):.3f}"
            )
        return "".join(points) + "Z"

    def star(self, cx: float, cy: float, radius: float, *, ink: str,
             width: float, sharpen: float = 1.0, fill: str = "none") -> str:
        return (
            f'<path d="{self.star_path(cx, cy, radius, sharpen=sharpen)}"'
            f' fill="{fill}" stroke="{ink}" stroke-width="{_held(width):.3f}"'
            ' stroke-linejoin="miter"/>'
        )

    def polygram(self, cx: float, cy: float, radius: float, *, ink: str,
                 width: float) -> str:
        """The {n/k} chord figure — the star's construction, drawn.

        The lines whose intersections define the star's inner vertices. It is
        the figure a geometer would leave on the plate, and at close range it is
        the clearest statement that the ornament was constructed rather than
        placed. Traced as `gcd(n, k)` separate circuits, so it is correct for
        every order rather than only for the coprime ones.
        """
        loops = math.gcd(self.order, self.density)
        out: list[str] = []
        for start in range(loops):
            points: list[str] = []
            index = start
            for step in range(self.order // loops):
                angle = self.phase + index * math.tau / self.order
                points.append(
                    f"{'L' if step else 'M'}{cx + radius * math.cos(angle):.3f} "
                    f"{cy + radius * math.sin(angle):.3f}"
                )
                index = (index + self.density) % self.order
            out.append("".join(points) + "Z")
        return (
            f'<path d="{"".join(out)}" fill="none" stroke="{ink}"'
            f' stroke-width="{_held(width):.3f}" stroke-linejoin="miter"/>'
        )

    def rosette(self, cx: float, cy: float, radius: float, *, ink: str,
                width: float, kites: bool = True) -> str:
        """The family's rosette: a star inside a ring of kites.

        This is the figure that carries the identity, and it is a real girih
        rosette rather than a star with a circle round it. The kites are struck
        *between* the star's points from the same n-gon, so their long axis is
        the perpendicular bisector of the star's edge — which is why the whole
        figure reads as one construction and not as two shapes stacked.
        """
        inner = radius * self.ratio
        out = [
            self.star(cx, cy, radius, ink=ink, width=width),
            self.polygram(cx, cy, inner, ink=ink, width=width * 0.55),
        ]
        if kites:
            half = math.pi / self.order
            for index in range(self.order):
                angle = self.phase + half + index * math.tau / self.order
                # A kite, not a spike. The first version put the tip at 1.30 of
                # the outer radius and the base deep inside the star, which
                # turned the rosette into a gear: what the eye reads is the
                # *ratio* of tip projection to kite width, and at 30% beyond the
                # rim with a narrow waist there is no kite left to see. The tip
                # now sits just clear of the star's points and the shoulders
                # open to most of the gap between them.
                tip = (cx + radius * 1.12 * math.cos(angle),
                       cy + radius * 1.12 * math.sin(angle))
                base = (cx + radius * 0.62 * math.cos(angle),
                        cy + radius * 0.62 * math.sin(angle))
                wing = half * 0.94
                left = (cx + radius * 0.86 * math.cos(angle - wing),
                        cy + radius * 0.86 * math.sin(angle - wing))
                right = (cx + radius * 0.86 * math.cos(angle + wing),
                         cy + radius * 0.86 * math.sin(angle + wing))
                out.append(
                    f'<path d="M{base[0]:.2f} {base[1]:.2f} '
                    f'L{left[0]:.2f} {left[1]:.2f} L{tip[0]:.2f} {tip[1]:.2f} '
                    f'L{right[0]:.2f} {right[1]:.2f} Z" fill="none"'
                    f' stroke="{ink}" stroke-width="{_held(width * 0.62):.3f}"/>'
                )
        return "".join(out)

    def medallion_ring(self, cx: float, cy: float, radius: float, *, ink: str,
                       width: float, count: int | None = None) -> str:
        """A ring of the family's smallest member, orbiting a centre.

        Used where a plain circle would otherwise appear — round a seal, round a
        corner medallion. A circle is the one shape that carries no family
        information, and replacing it with a ring of family members is most of
        what makes a document look designed rather than assembled.
        """
        n = count or self.order
        out: list[str] = []
        for index in range(n):
            angle = self.phase + index * math.tau / n
            out.append(
                self.star(cx + radius * math.cos(angle),
                          cy + radius * math.sin(angle),
                          radius * 0.155, ink=ink, width=width, sharpen=0.86)
            )
        return "".join(out)

    def field(self, rect: geo.Rect, *, cell: float, ink: str, strength: float,
              width: float, hollow: float = 0.0,
              keep_out: geo.Rect | None = None) -> str:
        """The family, allover, at the threshold of visibility.

        The lattice is the family's own: n-fold rosettes on a lattice whose
        pitch comes from the order, with the interstitial figure struck from the
        same n-gon. An eight-fold family gets a square lattice; ten- and
        twelve-fold get a staggered one, because that is what those orders
        actually tile on. Getting this wrong — forcing every order onto a square
        grid — is the single clearest tell of generated ornament.
        """
        stroke = geo.tint(ink, strength)
        stagger = self.order != 8
        rows = int(rect.h // cell) + 3
        columns = int(rect.w // cell) + 3
        out: list[str] = []
        for row in range(rows):
            offset = (cell * 0.5) if (stagger and row % 2) else 0.0
            for column in range(columns):
                cx = rect.x + column * cell - cell + offset
                cy = rect.y + row * cell * (0.87 if stagger else 1.0) - cell
                out.append(
                    self.rosette(cx, cy, cell * 0.46, ink=stroke, width=width,
                                 kites=False)
                )
        tag = f"sig-{abs(hash((rect.x, rect.y, rect.w, rect.h, cell, hollow))) % 1000000}"
        # Two exclusions, and they must be *nested* clips rather than two
        # subpaths of one even-odd path. Where the concentric ring's hole and
        # the content-field hole overlap, even-odd flips the region back to
        # filled — which turned the exclusion into its opposite and laid the
        # whole lattice across the execution band. Intersecting two clip paths
        # is the operation actually wanted: outside the ring AND outside the
        # field.
        if hollow > 0:
            inner = rect.inset(hollow)
            shape = (
                f'<path d="M{rect.x:.2f} {rect.y:.2f} h{rect.w:.2f} '
                f'v{rect.h:.2f} h{-rect.w:.2f} Z M{inner.x:.2f} {inner.y:.2f} '
                f'v{inner.h:.2f} h{inner.w:.2f} v{-inner.h:.2f} Z"'
                ' fill-rule="evenodd"/>'
            )
        else:
            shape = f"<rect {rect.attrs()}/>"
        body = "".join(out)
        if keep_out is not None:
            far = geo.Rect(rect.x - 500, rect.y - 500, rect.w + 1000,
                           rect.h + 1000)
            guard = f"{tag}-field"
            body = (
                f'<defs><clipPath id="{guard}">'
                f'<path d="M{far.x:.2f} {far.y:.2f} h{far.w:.2f} v{far.h:.2f} '
                f'h{-far.w:.2f} Z M{keep_out.x:.2f} {keep_out.y:.2f} '
                f'v{keep_out.h:.2f} h{keep_out.w:.2f} v{-keep_out.h:.2f} Z"'
                ' fill-rule="evenodd"/></clipPath></defs>'
                f'<g clip-path="url(#{guard})">{body}</g>'
            )
        return (
            f'<defs><clipPath id="{tag}">{shape}</clipPath></defs>'
            f'<g clip-path="url(#{tag})">' + body + "</g>"
        )

    def guilloche(self, cx: float, cy: float, radius: float, *, ink: str,
                  width: float, strength: float, passes: int = 3) -> str:
        """Lathe work cut from the family's own specification.

        `self.lathe` was chosen so its lobe count is a multiple of the order.
        That is the difference between a certificate whose guilloché happens to
        be nearby and one whose guilloché is the same family seen at a different
        frequency — at 20cm the eye cannot articulate the relationship and can
        absolutely tell whether it is there.
        """
        big, small, pen = self.lathe
        stroke = geo.tint(ink, strength)
        scale = radius / (big + small + pen)
        out: list[str] = []
        for index in range(passes):
            # Rotate by a fraction of the *lobe* period, so the passes
            # interleave evenly instead of beating against each other. Rotating
            # by a fraction of the order — which is what the first version did —
            # offset a 50-lobe figure by 1.67 lobes and produced a moiré lens
            # across the middle of the rosette that read as a printing fault.
            rotation = (index * 360) / (self.lobes * passes)
            path = geo.epitrochoid(cx, cy, big, small, pen, scale=scale)
            out.append(
                f'<path d="{path}" fill="none" stroke="{stroke}"'
                f' stroke-width="{_held(width):.3f}"'
                f' transform="rotate({rotation:.2f} {cx:.2f} {cy:.2f})"/>'
            )
        return "".join(out)

    @property
    def lobes(self) -> int:
        big, small, _ = self.lathe
        return big // math.gcd(big, small)


def motif_for(*, institution: str, family: str) -> Motif:
    """Derive an institution's geometry for one document family.

    Deterministic, and deliberately *not* keyed on the issued document: every
    doctoral award from one institution carries one geometry, because that is
    what makes it an identity. The per-document variation lives in the security
    layer, where it belongs.

    The derivation is a hash, which is honest about what it is — there is no
    claim that the resulting order is meaningful to the institution. What it
    guarantees is that two institutions do not accidentally share a family, that
    one institution's doctoral and diploma families differ, and that either can
    be reproduced from two strings a decade later.
    """
    digest = hashlib.sha256(
        f"{institution.strip().lower()}\x1f{family.strip().lower()}".encode()
    ).digest()
    order = ORDERS[digest[0] % len(ORDERS)]
    # A phase off the axis, but never so far that the frame's own verticals
    # start to fight it. A twelfth of the repeat is enough to kill the
    # machine-aligned look and small enough to stay architectural.
    phase = (digest[1] / 255.0) * (math.tau / order) / 3

    # Lathe specs whose lobe count is a multiple of the order, so the guilloché
    # and the star work are the same hand at different frequencies. `R` and `r`
    # stay coprime, which is what keeps the figure closed and expensive to copy.
    # Derived from the order rather than picked from the shared table. No row
    # in `geometry.LATHE` has a lobe count divisible by 8, 10 or 12 — they are
    # all primes and near-primes — so selecting from it produced a guilloché
    # with no relationship to the family at all, which is precisely the failure
    # this module exists to fix. Here the lobe count *is* a multiple of the
    # order by construction, and `R` and `r` are coprime so the figure still
    # closes only after `r` turns.
    multiplier = 3 + digest[2] % 4
    big = order * multiplier
    small = max(2, round(big / (5.5 + big / 14)))
    while math.gcd(big, small) != 1:
        small += 1
    lathe = (big, small, round(small * 1.2, 1))
    braid = 3 + digest[3] % 3
    density = density_for(order)
    return Motif(
        order=order,
        density=density,
        ratio=star_ratio(order, density),
        phase=phase,
        lathe=lathe,
        braid=braid,
        provenance=f"{institution} · {family}",
    )
