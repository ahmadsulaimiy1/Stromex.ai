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
    "seal_with_device",
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
        clear: float = 0.14) -> str:
    """One bay: a clear zone, the device if supplied, and the caption.

    `clear` is the proportion of the bay kept free around the device on every
    side. It exists because a supplied logo has its own idea of its margins, and
    without an enforced clear zone one institution's tightly-cropped crest sits
    twice as large as another's on the same sheet.

    An empty bay draws a fine keyline and the caption, so a sheet designed
    before the arms arrive still composes correctly and visibly says what is
    missing.
    """
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
    return (
        f'<svg x="{inner.x:.2f}" y="{inner.y:.2f}" width="{inner.w:.2f}"'
        f' height="{inner.h:.2f}" viewBox="0 0 100 100"'
        ' preserveAspectRatio="xMidYMid meet" overflow="visible">'
        f"{entry.device}</svg>" + caption
    )


def heraldic_register(rect: geo.Rect, bays: tuple[Bay, ...], *,
                      scheme: Scheme, ink: str, size: float = 15.0) -> str:
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
        out.append(bay(box, entry, scheme=scheme, ink=ink))
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
