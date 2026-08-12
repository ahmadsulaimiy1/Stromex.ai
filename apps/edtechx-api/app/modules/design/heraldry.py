"""Heraldic bays and the device-mounted seal — where an institution's own marks go.

Every benchmark sheet carries devices EdirasX must never draw: a national coat
of arms at the left, a state's arms at the right, the institution's crest on the
axis. Approximating a state emblem is not a thing to do quietly, and a generated
one is worse than an approximated one because nobody can say where it came from.

So this file builds the **bays**, not the emblems. A bay is a reserved area with
a stated size, a clear zone, a caption naming the authority, and a rule about
what may be placed in it. An institution supplies its own licensed device and it
is mounted; supply nothing and the bay is drawn empty and captioned, which is
honest. A placeholder emblem would not be.

**The seal is the same idea at a different scale.** EdirasX constructs the
gold — the turned field, the engraved rim, the legend ring carrying this
document's serial, the blind-embossed surround — and the institution's device
sits at the centre of it. The metal is ours and it is vector; the device is
theirs and it is theirs. Nothing here invents a mark.

**And a mounted device is not an approved seal.** A studio can mount a logo and
see what it looks like. Whether that device may actually seal an issued document
is governed by `documents.authority`, which holds approval, validity period and
revocation, and which will refuse to issue rather than substitute. The two are
deliberately separate: this file is about *appearance*, that one is about
*authority*, and conflating them is how a system ends up sealing documents with
a logo somebody uploaded on a Tuesday.

**The one place a raster is permitted, and what it costs.** An institution's
device may only exist as a bitmap. That is allowed — it is their mark, not our
artwork — but the resolution requirement is stated rather than discovered at the
printer: a device occupying 22mm on the sheet needs **260 pixels** to reach
300 DPI and **520** for 600. `device_resolution_note()` returns that sentence
for the production specification, and a studio should show it at upload time.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.design import geometry as geo
from app.modules.design.gilding import Scheme, emboss, engraved_metal_rule
from app.modules.design.signature import Motif

__all__ = [
    "Bay",
    "bay",
    "device_resolution_note",
    "heraldic_register",
    "institutional_crest",
    "seal_with_device",
    "shield_path",
]


@dataclass(frozen=True, slots=True)
class Bay:
    """One reserved position for a supplied device."""

    key: str
    #: What the device represents, printed beneath it in fine caps. Named
    #: because a coat of arms with no caption is decoration; with one it is a
    #: statement about who authorises the document.
    authority: str
    #: The device itself: an SVG fragment or an `<image>` element the caller
    #: has already built from a registered asset. Empty means an empty bay.
    device: str = ""


def bay(rect: geo.Rect, entry: Bay, *, scheme: Scheme, ink: str,
        clear: float = 0.14, show_empty: bool = True) -> str:
    """One bay: a clear zone, the device if supplied, and the caption.

    `clear` is the proportion of the bay kept free around the device on every
    side. It exists because a supplied logo has its own idea of its margins, and
    without an enforced clear zone one institution's tightly-cropped crest sits
    twice as large as another's on the same sheet.

    An empty bay draws a fine keyline and the caption, so a sheet designed
    before the arms arrive still composes correctly and visibly says what is
    missing.
    """
    # On a *finished* certificate an unsupplied bay draws nothing at all. The
    # dashed keyline and the words DEVICE NOT SUPPLIED are a studio affordance —
    # they tell a designer what is missing — and printing them on an issued
    # document would put "DEVICE NOT SUPPLIED" across the head of somebody's
    # doctorate.
    if not entry.device and not show_empty:
        return ""
    inner = rect.inset(min(rect.w, rect.h) * clear)
    caption = (
        f'<text x="{rect.cx:.2f}" y="{rect.y + rect.h + 2.4:.2f}"'
        f' text-anchor="middle" font-size="1.75" letter-spacing="0.14"'
        f' font-family="Inter, sans-serif" fill="{geo.tint(ink, 0.58)}">'
        f"{entry.authority}</text>"
    )
    if not entry.device:
        return (
            f'<rect {inner.attrs()} fill="none" stroke="{geo.tint(ink, 0.22)}"'
            ' stroke-width="0.18" stroke-dasharray="1.4 1.0"/>'
            f'<text x="{rect.cx:.2f}" y="{inner.cy + 0.8:.2f}"'
            f' text-anchor="middle" font-size="1.9"'
            f' font-family="Inter, sans-serif" fill="{geo.tint(ink, 0.40)}">'
            f"DEVICE NOT SUPPLIED</text>" + caption
        )
    # **A device is clipped to its bay, by transform and clip path.**
    #
    # This was a nested `<svg>` with a viewBox and `overflow`, and it did not
    # hold: inside a plate whose own root carries `preserveAspectRatio="none"`,
    # the nested viewport was not honoured and a 13mm bay put a shield across
    # half a certificate. Rendered in isolation the same fragment behaved; only
    # in place did it escape, which is the worst kind of bug to leave in.
    #
    # A `translate`/`scale` transform with an explicit `clipPath` has no such
    # ambiguity. The device is authored in a 100 × 100 space, scaled to the
    # clear zone, and clipped to it — and a device that draws outside its own
    # space is cropped rather than let loose.
    tag = f"bay-{abs(hash((rect.x, rect.y, entry.key))) % 999999}"
    scale = min(inner.w, inner.h) / 100.0
    offset_x = inner.x + (inner.w - 100 * scale) / 2
    offset_y = inner.y + (inner.h - 100 * scale) / 2
    return (
        f'<defs><clipPath id="{tag}"><rect {inner.attrs()}/></clipPath></defs>'
        f'<g clip-path="url(#{tag})">'
        f'<g transform="translate({offset_x:.3f} {offset_y:.3f}) '
        f'scale({scale:.5f})">{entry.device}</g></g>' + caption
    )


def heraldic_register(rect: geo.Rect, bays: tuple[Bay, ...], *,
                      scheme: Scheme, ink: str, size: float = 15.0,
                      show_empty: bool = True) -> str:
    """Devices across the head of the sheet, each with its authority named.

    Odd counts put a bay on the axis, which is where an institution's own crest
    belongs; even counts straddle it. The spacing is computed from the rect
    rather than fixed, so two bays and four bays are both correct compositions
    instead of one being a special case.
    """
    if not bays:
        return ""
    out: list[str] = []
    step = rect.w / len(bays)
    for index, entry in enumerate(bays):
        cx = rect.x + step * (index + 0.5)
        box = geo.Rect(cx - size / 2, rect.y, size, size)
        out.append(bay(box, entry, scheme=scheme, ink=ink,
                       show_empty=show_empty))
    return "".join(out)


def seal_with_device(cx: float, cy: float, radius: float, *, motif: Motif,
                     scheme: Scheme, ink: str, legend: str, identifier: str,
                     device: str = "") -> str:
    """A struck golden seal with the institution's own device at its centre.

    EdirasX builds everything except the device: a turned field cut from the
    document's own lathe specification, an engraved rim in three flat inks, the
    legend ring carrying the serial, a ring of the family's smallest star
    closing the outside, and a blind emboss.

    The device sits in a stated clear circle at 46 % of the radius. If none is
    supplied the motif's own rosette takes that position — which is a mark
    EdirasX may legitimately draw, because it is EdirasX's construction and not
    a claim to be anybody's arms.
    """
    from app.modules.design.architecture import legend_ring

    inner = radius * 0.46
    centre = (device and (
        f'<svg x="{cx - inner:.2f}" y="{cy - inner:.2f}"'
        f' width="{inner * 2:.2f}" height="{inner * 2:.2f}"'
        ' viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">'
        f"{device}</svg>"
    )) or emboss(
        motif.rosette(cx, cy, inner, ink=scheme.engraved.core, width=0.30),
        depth=0.22, light=scheme.primary.highlight,
        dark=scheme.engraved.shadow,
    )
    return (
        motif.guilloche(cx, cy, radius * 0.80, ink=scheme.security.core,
                        width=0.07, strength=0.85, passes=3)
        + f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="none"'
          f' stroke="{scheme.primary.face}" stroke-width="0.62"/>'
        + f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius * 0.955:.2f}"'
          f' fill="none" stroke="{scheme.primary.highlight}"'
          ' stroke-width="0.20"/>'
        + engraved_metal_rule(cx - radius * 0.62, cy, cx + radius * 0.62, cy,
                              metal=scheme.primary, weight=0.0)
        + f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius * 0.62:.2f}"'
          f' fill="none" stroke="{scheme.primary.shadow}" stroke-width="0.28"/>'
        + legend_ring(cx, cy, radius * 0.80, metal=scheme.primary,
                      legend=legend, identifier=identifier)
        + motif.medallion_ring(cx, cy, radius * 1.06,
                               ink=scheme.secondary.face, width=0.09)
        + centre
    )


def device_resolution_note(size_mm: float) -> str:
    """What a supplied bitmap device must measure, stated at upload time.

    Vector is always preferable and a studio should say so. Where an institution
    only has a bitmap, this is the sentence that stops the problem being
    discovered by a printer.
    """
    at_300 = round(size_mm / 25.4 * 300)
    at_600 = round(size_mm / 25.4 * 600)
    return (
        f"This device occupies {size_mm:.0f}mm on the sheet. A bitmap needs "
        f"at least {at_300} pixels across to reach 300 DPI, and {at_600} for "
        "600 DPI. Vector artwork has no such limit and is preferred: it is "
        "exact at any size and separates cleanly onto a plate."
    )


def shield_path(cx: float, cy: float, height: float) -> str:
    """A heater shield, constructed — the figure a watermark actually needs.

    A rosette makes a poor blind emboss and the render proved it twice: radial
    symmetry gives the light nothing to catch, so the mark read as a stain
    rather than as relief. Relief needs *flat areas separated by edges that
    change direction*, which is precisely what a shield is and why every
    institution in the world put its watermark on one.

    The proportions are the heater's own: width is 5/6 of height, the flanks
    run straight for the top two fifths, and the point is struck as two arcs
    from centres on the opposite flank. Nothing here is drawn by eye.
    """
    width = height * 5 / 6
    half = width / 2
    top = cy - height / 2
    straight = top + height * 0.42
    return (
        f"M{cx - half:.2f} {top:.2f} H{cx + half:.2f} V{straight:.2f} "
        f"C{cx + half:.2f} {top + height * 0.74:.2f} "
        f"{cx + half * 0.58:.2f} {top + height * 0.93:.2f} "
        f"{cx:.2f} {top + height:.2f} "
        f"C{cx - half * 0.58:.2f} {top + height * 0.93:.2f} "
        f"{cx - half:.2f} {top + height * 0.74:.2f} "
        f"{cx - half:.2f} {straight:.2f} Z"
    )


def institutional_crest(cx: float, cy: float, height: float, *, motif: Motif,
                        ink: str, strength: float = 0.030,
                        motto: str = "") -> str:
    """EdirasX's own armorial device: shield, chief, quartering, charges.

    Drawn as a *watermark* — one tone, no fills, at a few per cent above the
    paper — and it is EdirasX's construction rather than a claim to be anybody's
    arms, which is why the system may draw it when an institution has supplied
    nothing. A supplied device always displaces it.

    Five elements, each of which an emboss can catch: the shield's own outline,
    a chief across the top, a cross quartering the field, the motif's star in
    the honour point, and a small charge in each quarter.
    """
    stroke = geo.tint(ink, strength)
    width = height * 5 / 6
    half = width / 2
    top = cy - height / 2
    chief = top + height * 0.20
    quarter = top + height * 0.52
    out = [
        f'<path d="{shield_path(cx, cy, height)}" fill="none"'
        f' stroke="{stroke}" stroke-width="{height * 0.022:.3f}"'
        ' stroke-linejoin="round"/>',
        f'<path d="M{cx - half:.2f} {chief:.2f} H{cx + half:.2f}"'
        f' stroke="{stroke}" stroke-width="{height * 0.016:.3f}" fill="none"/>',
        f'<path d="M{cx:.2f} {chief:.2f} V{top + height * 0.86:.2f}"'
        f' stroke="{stroke}" stroke-width="{height * 0.013:.3f}" fill="none"/>',
        f'<path d="M{cx - half * 0.86:.2f} {quarter:.2f} '
        f'H{cx + half * 0.86:.2f}" stroke="{stroke}"'
        f' stroke-width="{height * 0.013:.3f}" fill="none"/>',
        motif.star(cx, chief + (quarter - chief) * 0.02 + height * 0.005,
                   height * 0.085, ink=stroke, width=height * 0.014),
    ]
    for sign in (-1, 1):
        out.append(motif.star(cx + sign * half * 0.44,
                              quarter + height * 0.16, height * 0.055,
                              ink=stroke, width=height * 0.011, sharpen=0.88))
    if motto:
        out.append(
            f'<text x="{cx:.2f}" y="{top + height * 1.12:.2f}"'
            f' text-anchor="middle" font-size="{height * 0.075:.2f}"'
            f' letter-spacing="{height * 0.012:.2f}"'
            f' font-family="Inter, sans-serif" fill="{stroke}">{motto}</text>'
        )
    return "".join(out)
