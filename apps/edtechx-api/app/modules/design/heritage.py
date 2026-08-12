"""The heritage ground: the security substrate the benchmark sheets are printed on.

This is the background of the imported templates, and the first thing to say
about it is what it is *not*. It is not a scan, a trace, or an enlargement of
anybody's artwork. It is constructed geometry — epitrochoid lathe work,
parametric rosettes, star polygons on an n-fold rotation, engraved rules, real
text on a path — assembled in the layer order and at the band positions the
benchmark plate uses. It therefore has no resolution: it is exact at 300 DPI, at
600, and at 2400, and it can be re-cut for any sheet size without a resampling
step.

**Why it is redrawn rather than copied.** The benchmark's own master artwork is
a 1080×772 raster. Across a 297×210mm sheet that is 92 DPI — a quarter of the
300 DPI floor a press needs and a seventh of the 600 an engraved register needs.
There is nothing to recover by enlarging it: the fine detail is not in the file,
so an upscale would manufacture detail that was never there and print invented
ornament on a permanent record. Redrawing is what a security printer does, and
it is the only honest way to carry a plate forward.

**The band architecture.** Outside → in, seven measured insets:

    hair          the outer gold hairline; says where the paper ends
    band_outer    the engraved ornamental band, outer engraved rule
    band_inner    ...and its inner engraved rule. Lathe strapwork between.
    strip_outer   the iridescent security strip, outer edge
    strip_inner   ...and its inner edge
    rule_outer    the inner double rule closing the margin
    rule_inner    the innermost line. Everything a reader perceives as the
                  document's own edge, and the boundary of the content field.

They are stated as a *proportion of the sheet's short side*, not as absolute
millimetres, because a border measured for a 297×210 sheet and pasted onto a
210×297 one puts a 36mm margin down a 210mm width and leaves a column. The
proportions come from the 297×210 master; every other size is re-cut from them.

**What the security registers are, and are not.** The anti-copy screens are
anti-copy screens: two rulings set off a copier's own angles so a copy beats
against them. They are not a latent image — that needs a coarse and a fine
ruling at matched ink fraction with a shape defined between them, and neither
ruling here is doing that. The fine-text rails are fine text, not microprint;
`geometry.fine_text_ring` carries the measurement and the threshold. The fibres
are a cosmetic fibre field, not a substrate guarantee: a real security paper's
fibres are *in* the sheet and fluoresce, and printed ones do neither. Nothing
here has been on a press yet, so every one of these is a specification.

**Wording rule.** The only text this module will put on a plate is what the
caller hands it. It composes no slogan, title or claim of its own.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from app.modules.design import geometry as geo
from app.modules.design.gilding import Scheme, foil_gradient

__all__ = [
    "BAND_PROPORTIONS",
    "Bands",
    "Ground",
    "heritage_ground",
    "registration_mark",
    "watermark",
]

#: The measured insets of the master plate, divided by its 210mm short side.
#: Re-cut rather than reused: see the module docstring.
BAND_PROPORTIONS: Final[dict[str, float]] = {
    "hair": 4.7 / 210,
    "band_outer": 10.2 / 210,
    "band_inner": 14.0 / 210,
    "strip_outer": 21.7 / 210,
    "strip_inner": 28.1 / 210,
    "rule_outer": 32.7 / 210,
    "rule_inner": 36.3 / 210,
}


@dataclass(frozen=True, slots=True)
class Bands:
    """The seven insets, in millimetres, for one sheet."""

    hair: float
    band_outer: float
    band_inner: float
    strip_outer: float
    strip_inner: float
    rule_outer: float
    rule_inner: float

    @classmethod
    def for_sheet(cls, width: float, height: float, *,
                  weight: float = 1.0) -> Bands:
        """Cut the band architecture for a sheet.

        `weight` narrows or widens the whole border together. A register sheet
        that has to hold thirty rows of a table cannot spend 36mm on a margin;
        it spends 26 and keeps every proportion between the bands intact, which
        is a different thing from deleting two of them.
        """
        short = min(width, height)
        return cls(**{
            name: short * proportion * weight
            for name, proportion in BAND_PROPORTIONS.items()
        })


@dataclass(frozen=True, slots=True)
class Ground:
    """A rendered ground and the field it leaves for the words."""

    svg: str
    field: geo.Rect
    bands: Bands
    width: float
    height: float


def _iridescent(identifier: str) -> str:
    """The security strip's ramp.

    Iridescent ink shifts hue with viewing angle, so it is drawn as a hue walk
    at near-constant lightness rather than a light-to-dark gradient. Held pale:
    the strip is substrate, and a strip that competes with the ornament in front
    of it has stopped being substrate.
    """
    stops = ("#E7D9E8", "#D8E2F0", "#DFEDE2", "#F2E8D4",
             "#EADCE8", "#D9E4F2", "#E9DFE6")
    body = "".join(
        f'<stop offset="{index / (len(stops) - 1):.4f}" stop-color="{colour}"/>'
        for index, colour in enumerate(stops)
    )
    return (
        f'<linearGradient id="{identifier}" x1="0" y1="0" x2="1" y2="0.35">'
        f"{body}</linearGradient>"
    )


def watermark(cx: float, cy: float, radius: float, *, ink: str,
              strength: float = 0.055) -> str:
    """The central khatam: four concentric n-fold rosettes, softly embossed.

    The emboss is a pale copy offset down-right *under* the ink copy, which is
    how a blind emboss actually reads — a lit wall on one side and a shadow wall
    on the other. It is not a drop shadow, and the difference is visible.

    Held deliberately near the threshold of visibility, because this sits
    directly behind the recipient's name. A watermark that can be read as a
    graphic is competing with the text rather than sitting in the sheet.
    """
    rings = ((16, 1.00, 0.74, 0.30), (12, 0.80, 0.55, 0.26),
             (12, 0.58, 0.34, 0.22), (8, 0.36, 0.18, 0.20))

    def draw(dx: float, dy: float, colour: str) -> str:
        parts = []
        for index, (points, outer, inner, weight) in enumerate(rings):
            path = geo.star_polygon(cx + dx, cy + dy, points, radius * outer,
                                    radius * inner, rotation=index * 0.13)
            parts.append(
                f'<path d="{path}" fill="none" stroke="{colour}"'
                f' stroke-width="{max(weight, 0.07):.3f}"/>'
            )
        parts.append(
            f'<circle cx="{cx + dx:.2f}" cy="{cy + dy:.2f}"'
            f' r="{radius * 0.12:.2f}" fill="none" stroke="{colour}"'
            ' stroke-width="0.22"/>'
        )
        return "".join(parts)

    return (
        "<g>"
        + draw(0.30, 0.30, geo.tint("#FFFFFF", 0.34))
        + draw(0.0, 0.0, geo.tint(ink, strength))
        + geo.rosette(cx, cy, radius * 0.92, ink=ink, width=0.12,
                      strength=strength * 0.9, passes=3)
        + "</g>"
    )


def registration_mark(x: float, y: float, *, ink: str,
                      strength: float = 0.42) -> str:
    """A press registration target: crosshair, ring, centre dot.

    Solid ink at every weight. A registration mark that is screened is a
    registration mark the pressman cannot use, which makes it decoration
    pretending to be an instruction.
    """
    stroke = geo.tint(ink, strength)
    return (
        f'<g><circle cx="{x:.2f}" cy="{y:.2f}" r="1.15" fill="none"'
        f' stroke="{stroke}" stroke-width="0.10"/>'
        f'<line x1="{x - 1.8:.2f}" y1="{y:.2f}" x2="{x + 1.8:.2f}" y2="{y:.2f}"'
        f' stroke="{stroke}" stroke-width="0.10"/>'
        f'<line x1="{x:.2f}" y1="{y - 1.8:.2f}" x2="{x:.2f}" y2="{y + 1.8:.2f}"'
        f' stroke="{stroke}" stroke-width="0.10"/>'
        f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.26" fill="{stroke}"/></g>'
    )


def _corner(x: float, y: float, size: float, *, scheme: Scheme,
            flip_x: bool, flip_y: bool) -> str:
    """One corner engraving, mirrored into place by transform.

    Drawn once and reflected, so all four are provably the same construction
    rather than four attempts at it — which is what a reader sees when they are
    not, even if they could not say why.
    """
    inner = scheme.role("secondary")
    engraved = scheme.role("engraved")
    parts: list[str] = []
    for index in range(1, 7):
        r = (size * index) / 7
        parts.append(
            f'<path d="M0 {r:.2f} A {r:.2f} {r:.2f} 0 0 1 {r:.2f} 0" fill="none"'
            f' stroke="{geo.tint(inner.core, 0.72)}"'
            f' stroke-width="{max(0.14 + index * 0.012, 0.07):.3f}"/>'
        )
    cx = cy = size * 0.42
    parts.append(geo.star_polygon(cx, cy, 8, size * 0.20, size * 0.10))
    parts[-1] = (
        f'<path d="{parts[-1]}" fill="none" stroke="{engraved.core}"'
        ' stroke-width="0.20"/>'
    )
    parts.append(
        f'<path d="{geo.star_polygon(cx, cy, 8, size * 0.13, size * 0.065, rotation=0.39)}"'
        f' fill="none" stroke="{inner.face}" stroke-width="0.14"/>'
    )
    parts.append(
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{size * 0.035:.2f}"'
        f' fill="{engraved.core}"/>'
    )
    parts.append(
        geo.rosette(cx, cy, size * 0.30, ink=inner.core, width=0.10,
                    strength=0.42, passes=2, pitch=2.4)
    )
    scale = f"scale({-1 if flip_x else 1} {-1 if flip_y else 1})"
    return f'<g transform="translate({x:.2f} {y:.2f}) {scale}">' + "".join(parts) + "</g>"


def heritage_ground(*, width: float, height: float, scheme: Scheme,
                    rail_text: str = "", seed: str = "EDIRASX",
                    paper: str = "#F4ECDC", ink: str = "#8C6516",
                    border_weight: float = 1.0,
                    fibre_count: int = 150,
                    show_watermark: bool = True) -> Ground:
    """Cut the full ground for one sheet.

    The layer order below is the order the benchmark plate builds in, and it is
    not arbitrary: the screens go under the lathe work so the lathe reads as
    engraving on a substrate rather than as line art on a screen; the fibres go
    over both because fibres are *in* the paper, above whatever was printed on
    it; the border goes over the fibres because ink is on top of paper; and the
    fine-text rails go last because they are the finest thing on the sheet and
    nothing may cross them.

    `rail_text` is what runs the two fine-text rails. Hand it the institution's
    own name and this document's own serial: a rail carrying the live serial is
    the reason a sheet photocopied from another student's certificate
    contradicts itself in its own border.
    """
    bands = Bands.for_sheet(width, height, weight=border_weight)
    sheet = geo.Rect(0, 0, width, height)
    primary = scheme.role("primary")
    secondary = scheme.role("secondary")
    security = scheme.role("security")

    def band(inset: float) -> geo.Rect:
        return sheet.inset(inset)

    defs = [
        foil_gradient(primary, "heritage-engrave", angle=42.0, bands=1),
        foil_gradient(primary, "heritage-warm", angle=90.0, bands=1),
        foil_gradient(secondary, "heritage-cool", angle=200.0, bands=1),
        _iridescent("heritage-iris"),
        geo.line_screen("heritage-copy-a", degrees=8, pitch=0.42, width=0.07,
                        ink=security.core, strength=0.39),
        geo.line_screen("heritage-copy-b", degrees=53, pitch=0.44, width=0.07,
                        ink=security.core, strength=0.28),
        geo.line_screen("heritage-band", degrees=68, pitch=0.30, width=0.08,
                        ink=scheme.role("engraved").core, strength=1.0),
        '<radialGradient id="heritage-paper" cx="0.5" cy="0.46" r="0.78">'
        f'<stop offset="0" stop-color="{geo.tint(paper, 0.55)}"/>'
        f'<stop offset="0.62" stop-color="{paper}"/>'
        f'<stop offset="1" stop-color="{geo.blend(ink, paper, 0.13)}"/>'
        "</radialGradient>",
    ]

    layers: list[str] = [
        # 1. the sheet, with a warm centre falloff. Flat paper reads as screen.
        f'<rect {sheet.attrs()} fill="url(#heritage-paper)"/>',
        # 2. anti-copy ruling, full bleed
        f'<rect {sheet.attrs()} fill="url(#heritage-copy-a)"/>',
        # 3. the sheet-scale lathe field
        geo.rosette(sheet.cx, sheet.cy, min(width, height) * 0.562,
                    ink=ink, width=0.13, strength=0.055, passes=4),
    ]
    if show_watermark:
        # 4. the embossed khatam, behind the name
        layers.append(watermark(sheet.cx, sheet.cy, min(width, height) * 0.248,
                                ink=ink))
    # 5. fibres — over the print, because fibres are in the paper
    if fibre_count:
        layers.append(geo.fibres(sheet, seed=seed, count=fibre_count))

    # 6. the outer hairline pair
    layers.append(
        f'<rect {band(bands.hair).attrs()} fill="none"'
        ' stroke="url(#heritage-warm)" stroke-width="0.35"/>'
        f'<rect {band(bands.hair + 1.1).attrs()} fill="none"'
        f' stroke="{geo.tint(ink, 0.86)}" stroke-width="0.12"/>'
    )

    # 7. the ornamental band: strapwork between two engraved rules
    thickness = max(0.8, bands.band_inner - bands.band_outer - 1.0)
    mid = band((bands.band_outer + bands.band_inner) / 2)
    layers.append(
        "<g>"
        + geo.engraved_rule(band(bands.band_outer), ink=primary.core,
                            weight=0.50, shadow=primary.shadow)
        + f'<rect {mid.attrs()} fill="none" stroke="url(#heritage-cool)"'
          f' stroke-width="{thickness:.2f}"/>'
        + f'<rect {mid.attrs()} fill="none" stroke="url(#heritage-band)"'
          f' stroke-width="{thickness:.2f}"/>'
        + geo.engraved_rule(band(bands.band_inner), ink=primary.core,
                            weight=0.42, shadow=primary.shadow)
        + "</g>"
    )

    # 8. the iridescent security strip
    strip = band((bands.strip_outer + bands.strip_inner) / 2)
    strip_w = max(0.8, bands.strip_inner - bands.strip_outer)
    layers.append(
        "<g>"
        f'<rect {strip.attrs()} fill="none" stroke="url(#heritage-iris)"'
        f' stroke-width="{strip_w:.2f}"/>'
        f'<rect {strip.attrs()} fill="none" stroke="url(#heritage-copy-b)"'
        f' stroke-width="{strip_w:.2f}"/>'
        f'<rect {band(bands.strip_outer).attrs()} fill="none"'
        f' stroke="{geo.tint(security.core, 0.75)}" stroke-width="0.13"/>'
        f'<rect {band(bands.strip_inner).attrs()} fill="none"'
        f' stroke="{geo.tint(security.core, 0.75)}" stroke-width="0.13"/>'
        "</g>"
    )

    # 9. the inner double rule, closing the margin
    layers.append(
        f'<rect {band(bands.rule_outer).attrs()} fill="none"'
        ' stroke="url(#heritage-warm)" stroke-width="0.38"/>'
        f'<rect {band(bands.rule_inner).attrs()} fill="none"'
        f' stroke="{geo.tint(ink, 0.86)}" stroke-width="0.12"/>'
    )

    # 10. corner engravings — one construction, four reflections
    size = min(width, height) * 0.081
    offset = bands.band_inner + 0.6
    layers.extend((
        _corner(offset, offset, size, scheme=scheme, flip_x=False, flip_y=False),
        _corner(width - offset, offset, size, scheme=scheme, flip_x=True, flip_y=False),
        _corner(width - offset, height - offset, size, scheme=scheme, flip_x=True, flip_y=True),
        _corner(offset, height - offset, size, scheme=scheme, flip_x=False, flip_y=True),
    ))

    # 11. mid-edge security medallions
    medallion = min(width, height) * 0.0257
    seat = bands.band_inner + 1.9
    for cx, cy in ((width / 2, seat), (width / 2, height - seat),
                   (seat, height / 2), (width - seat, height / 2)):
        layers.append(geo.rosette(cx, cy, medallion, ink=ink, width=0.11,
                                  strength=0.50, passes=3, pitch=2.2))

    # 12. registration targets
    for cx, cy in ((width / 2, bands.hair + 2.6), (width / 2, height - bands.hair - 2.6),
                   (bands.hair + 2.6, height / 2), (width - bands.hair - 2.6, height / 2)):
        layers.append(registration_mark(cx, cy, ink=security.core))

    # 13. the fine-text rails, last and finest
    if rail_text:
        text = f"{rail_text} · "
        layers.append(
            geo.fine_text_ring(band(bands.hair + 4.0), identifier="heritage-outer",
                               text=text, ink=security.core, size=0.90 * 0.35278,
                               strength=0.62)
        )
        layers.append(
            geo.fine_text_ring(band(bands.rule_inner + 2.3), identifier="heritage-inner",
                               text=text, ink=security.core, size=0.80 * 0.35278,
                               strength=0.55)
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}"'
        f' width="{width:g}mm" height="{height:g}mm" aria-hidden="true"'
        ' focusable="false">'
        f"<defs>{''.join(defs)}</defs>"
        + "".join(layers)
        + "</svg>"
    )
    # The field clears the innermost rule by a hair, not by a second margin.
    # The margin *is* the border: the band architecture already spends 17 % of
    # the short side on it, and adding another 3 % on top left a landscape
    # ceremonial field 125mm tall for a composition that needs 137 — which the
    # collision audit reported as a 34mm overflow on every stage sheet before
    # anything was looked at.
    field = sheet.inset(bands.rule_inner + min(width, height) * 0.012)
    return Ground(svg=svg, field=field, bands=bands, width=width, height=height)


def press_note(width: float, height: float, *, dpi: int = 600) -> str:
    """What this ground costs to output at a given resolution, stated honestly."""
    px_w = round(width / 25.4 * dpi)
    px_h = round(height / 25.4 * dpi)
    hairline_px = 0.07 / 25.4 * dpi
    verdict = (
        "holds the 0.07mm hairline floor" if hairline_px >= 1.5
        else "CANNOT resolve the 0.07mm hairline — raise the output resolution"
    )
    return (
        f"At {dpi} DPI this ground rasterises to {px_w}×{px_h}px and its finest "
        f"stroke lands on {hairline_px:.2f}px: {verdict}. The construction "
        f"itself is resolution-free — it is cut in millimetres and re-solved at "
        f"every output size, so {math.floor(dpi)} is a choice about the raster, "
        "not a limit of the plate."
    )
