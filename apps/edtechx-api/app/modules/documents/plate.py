"""The plate: a certificate's architecture, built from the geometry budget.

A plate is the sheet before any words are on it — frame, field, substrate — and
it is generated, not drawn. `geometry.py` supplies the constructions,
`ceremony.py` decides which of them this document may spend, and this file
arranges them into a composition that has a reason for every element.

**The architecture, outside → in.**

    TRIM      the paper's edge. Nothing within 6mm of it, ever: a printer's
              cutting tolerance is ±1.5mm and a rule that lands on the knife
              is a rule that lands on the knife on some of the copies.
    FRAME     one to four engraved registers, per level. The outermost is a
              hairline; the innermost is the one the eye reads as the edge of
              the document.
    MARGIN    the widest single measure on the sheet, and the reason a plate
              reads as engraved rather than as clipart. A frame pressed
              against its content is a border; a frame with air inside it is
              an architecture.
    FIELD     where the words go. Ornament enters here only under the level's
              ink ceiling, and `test_plates.py` measures it rather than
              trusting it.

**One visual peak.** The composition has exactly one dominant moment, and on a
certificate it is the recipient's name — not the institution, not the title, not
the seal. This is stated here because it is a *layout* rule as much as a
typographic one: the peak sits on the sheet's optical centre, which is above the
geometric centre, and every other zone is positioned relative to it.

**Symmetry, with one sanctioned asymmetry.** The ceremonial heart is mirrored
about the vertical axis. The verification block is not: it sits at the
administrative edge, where a verifier looks for it and a reader's eye does not.
That asymmetry has a reason; no other is permitted.

**Landscape and portrait are different compositions, not one stretched.** A
landscape sheet has a wide field and a short one: the peak can be large, the
statement runs on two or three long lines, and the execution row spans the foot.
A portrait sheet is a column: the peak is smaller relative to the sheet, the
statement stacks, and the execution row becomes two pairs. Nothing here scales
one into the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.modules.design import geometry as geo
from app.modules.design.ceremony import Budget

__all__ = ["SHEETS", "Plate", "Sheet", "build"]


@dataclass(frozen=True, slots=True)
class Sheet:
    """A physical sheet, in millimetres."""

    key: str
    name: str
    width: float
    height: float

    @property
    def is_landscape(self) -> bool:
        return self.width > self.height

    @property
    def rect(self) -> geo.Rect:
        return geo.Rect(0, 0, self.width, self.height)


#: The five sizes a certificate is actually printed on. A3 is here because a
#: doctoral award genuinely is framed at that size in some institutions, and
#: because designing it deliberately is the alternative to somebody scaling an
#: A4 plate by 141% and shipping hairlines at 0.14mm.
SHEETS: Final[dict[str, Sheet]] = {
    "a4-landscape": Sheet("a4-landscape", "A4 landscape", 297.0, 210.0),
    "a4-portrait": Sheet("a4-portrait", "A4 portrait", 210.0, 297.0),
    "a3-landscape": Sheet("a3-landscape", "A3 landscape", 420.0, 297.0),
    "letter-landscape": Sheet("letter-landscape", "Letter landscape", 279.4, 215.9),
    "letter-portrait": Sheet("letter-portrait", "Letter portrait", 215.9, 279.4),
}

#: A printer's cutting tolerance. Nothing is drawn inside this of the trim.
SAFE_EDGE: Final[float] = 6.0


@dataclass(frozen=True, slots=True)
class Plate:
    """A rendered plate and the field it leaves for the words."""

    svg: str
    field: geo.Rect
    sheet: Sheet
    budget: Budget

    @property
    def optical_centre(self) -> float:
        """Where the peak sits: above the geometric centre.

        The eye reads the centre of a sheet as slightly high, which is why a
        picture hung at true centre looks low. On a certificate the difference
        is the difference between a name that sits in the composition and one
        that sags in it.
        """
        return self.field.y + self.field.h * 0.455


def _frame_registers(sheet: Sheet, budget: Budget, ink: str, gold: str) -> str:
    """The engraved registers, outside → in.

    Weights step *up* inwards. The outermost line is a hairline that says where
    the paper ends; the innermost is the document's own edge and is the one a
    reader perceives. Reversing that — a heavy outer band and a thin inner rule
    — is the single most common way a certificate frame reads as a border
    somebody bought.
    """
    out: list[str] = []
    count = len(budget.frame)
    for index, inset in enumerate(budget.frame):
        rect = sheet.rect.inset(inset)
        last = index == count - 1
        if last:
            out.append(geo.engraved_rule(rect, ink=gold, weight=0.55))
        else:
            weight = 0.16 + index * 0.05
            out.append(
                f'<rect {rect.attrs()} fill="none" '
                f'stroke="{geo.tint(ink, 0.55 + index * 0.12)}" '
                f'stroke-width="{weight:.3f}"/>'
            )
    return "".join(out)


def build(
    *,
    sheet: Sheet,
    budget: Budget,
    ink: str = "#0A101C",
    gold: str = "#B08D57",
    serial: str = "",
    institution: str = "",
    frameless: bool = False,
) -> Plate:
    """Generate the plate for one sheet at one ceremonial level.

    Every construction below is gated on `budget.permits`. A template cannot
    ask for guilloché on a report card: the name is simply not in the Level I
    set, and the branch does not run.
    """
    layers: list[str] = []
    defs: list[str] = []
    outermost = budget.frame[0]
    innermost = budget.frame[-1]
    field = sheet.rect.inset(innermost + budget.field_inset)

    # --- the substrate ---
    # Flagship only, and both named for what they are: an anti-copy ruling and
    # a cosmetic fibre field. Neither is a security guarantee (ADR-041).
    if "screen" in budget.permits:
        defs.append(
            geo.line_screen("anticopy", degrees=8, pitch=0.44, width=0.07,
                            ink=gold, strength=0.20)
        )
        layers.append(
            f'<rect {sheet.rect.attrs()} fill="url(#anticopy)"/>'
        )
    if "fibres" in budget.permits and serial:
        layers.append(geo.fibres(sheet.rect, seed=serial, count=120))

    # --- the sheet-scale field ---
    # A single lathe pass across the whole sheet at a whisper of ink. It is not
    # meant to be seen at arm's length; it is meant to be there when somebody
    # looks closely, which is a different job.
    if "rosette" in budget.permits:
        layers.append(
            geo.rosette(
                sheet.rect.cx, sheet.rect.cy,
                # Wider than the sheet's short side, so its envelope is
                # cropped by the trim rather than sitting on the page as a
                # visible oval — the first render read as a smudge with a
                # shape, and a sheet field must have neither.
                min(sheet.width, sheet.height) * 0.86,
                ink=ink, width=0.09, strength=0.030, passes=2,
            )
        )

    # --- the lattice, inside the field and only just ---
    if "lattice" in budget.permits:
        layers.append(
            geo.lattice_field(field, cell=26, ink=ink, width=0.07, strength=0.055)
        )

    # --- the frame registers ---
    # A composition may decline them. F establishes its edge with two full-width
    # rules and a wide margin, and an engraved register drawn inside those is
    # the enclosure it was chosen for not having.
    if not frameless:
        layers.append(_frame_registers(sheet, budget, ink, gold))

    # --- lathe work between the registers ---
    if "guilloche" in budget.permits and len(budget.frame) >= 3:
        band = sheet.rect.inset((budget.frame[0] + budget.frame[1]) / 2)
        layers.append(
            geo.guilloche_band(band, ink=gold, width=0.09, strength=0.50,
                               amplitude=1.3, waves=int(sheet.width / 2.4))
        )
    if "arabesque" in budget.permits and len(budget.frame) >= 2:
        layers.append(
            geo.arabesque_band(
                sheet.rect.inset(budget.frame[-1] + budget.field_inset * 0.42),
                ink=gold, width=0.12, strength=0.42,
                period=sheet.width / 22, depth=1.5,
            )
        )

    # --- corners ---
    if "corner" in budget.permits:
        size = 17.0 if sheet.width > 250 else 14.0
        inset = innermost + 1.5
        for quadrant, (x, y) in enumerate((
            (inset, inset),
            (sheet.width - inset, inset),
            (sheet.width - inset, sheet.height - inset),
            (inset, sheet.height - inset),
        )):
            layers.append(
                geo.corner_frame(x, y, size, ink=gold, quadrant=quadrant,
                                 strength=0.62)
            )

    # --- microtext, carrying this document's own serial ---
    if "microtext" in budget.permits and serial:
        text = f"{institution.upper()} · {serial} · " if institution else f"{serial} · "
        layers.append(
            geo.microtext_ring(
                sheet.rect.inset(outermost - 1.6), identifier="edge",
                # Quiet. Microtext that is legible as a texture at arm's
                # length is not microtext, it is a grey band along the edge of
                # the sheet — which is what the first flagship render produced.
                text=text, ink=ink, size=0.58, strength=0.26,
            )
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {sheet.width:g} {sheet.height:g}" '
        f'width="{sheet.width:g}mm" height="{sheet.height:g}mm" '
        f'preserveAspectRatio="none" aria-hidden="true" focusable="false">'
        + (f"<defs>{''.join(defs)}</defs>" if defs else "")
        + "".join(layers)
        + "</svg>"
    )
    return Plate(svg=svg, field=field, sheet=sheet, budget=budget)
