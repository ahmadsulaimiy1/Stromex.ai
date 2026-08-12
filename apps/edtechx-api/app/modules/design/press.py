"""The press: a document as a set of plates, not as a picture.

A security printer does not receive artwork. It receives a **plate list** — one
separation per operation the press will perform — plus a specification saying
what each is made of, what registration tolerance it holds, and what it costs.
This module is that list, made first-class, so a design is composed *onto plates*
from the first stroke rather than drawn and separated afterwards.

The difference is not bookkeeping. Separating afterwards is how a hairline ends
up on the foil plate, where 0.07mm cannot be struck; how a gradient ends up on a
spot colour that has no gradient; how an emboss die is asked to raise a form with
a 0.2mm neck that the die will simply tear. Composing onto plates makes those
impossible, because `Press.mark()` refuses them at the point of drawing.

**The plate list, in press order.** Substrate first because everything sits on
it, litho before foil because foil is struck onto printed work, emboss last
because it deforms the sheet and nothing registers to a deformed sheet
afterwards.

    1  substrate     the paper itself: shade, fibre, watermark
    2  antipathy     anti-copy rulings and the void pantograph
    3  guilloche     lathe work — the security ground proper
    4  process       CMYK: everything with tone in it
    5  line          solid line and type: the black plate, 100% K
    6  microtext     fine text, on its own plate because its ink film differs
    7  foil_primary  the ceremonial architecture: one metal, struck hot
    8  foil_second   fine ornamental registers: a second metal or a second pass
    9  varnish       tactile spot varnish — felt, not seen
    10 emboss        raised relief from a male/female die pair
    11 deboss        sunk relief; a separate die, never the same one inverted
    12 uv            invisible fluorescent ink, revealed under 365nm
    13 numbering     the serial: applied by a numbering box, per sheet
    14 variable      per-document data printed digitally after the run

**What this module refuses, and why each refusal is a real press fact.**

*Hairlines on foil.* Hot foil needs a shoulder to grip. Below about 0.15mm the
foil bridges rather than adheres and the line comes off on the release liner in
patches. The floor here is 0.20mm and it is not negotiable by wanting it.

*Tone on a spot plate.* A foil, varnish, emboss or UV plate is binary — the
operation either happens at a point or it does not. A gradient on one of these
is a request the press cannot express, and what arrives is the plate at 100%.

*Screens on the fine-text plate.* Microtext is already at the resolution floor;
screening it removes half of every stroke.

*Emboss forms with thin necks.* A die with a neck below about 0.6mm tears the
sheet rather than raising it, and tears it on the tenth impression rather than
the first, which is worse.

**What this module does not do.** It does not claim any of these operations has
been performed. Every plate here is a specification until a press has run it,
and `production_note()` says so on every sheet it describes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

__all__ = [
    "PLATES",
    "Plate",
    "PlateError",
    "Press",
    "Separation",
    "plate_for",
]


class PlateError(ValueError):
    """A mark was asked for that the named plate physically cannot carry."""


@dataclass(frozen=True, slots=True)
class Plate:
    """One press operation, and what it can physically do."""

    key: str
    name: str
    #: Position in the press order. Lower runs first.
    order: int
    #: What the operation is: "print", "foil", "relief", "coating", "invisible".
    kind: str
    #: The narrowest stroke this operation holds, in millimetres.
    stroke_floor: float
    #: Whether the plate can carry a gradient, a screen or an alpha. A foil die
    #: is a shape: it is struck or it is not.
    tonal: bool
    #: Registration tolerance to the previous plate, in millimetres. Nothing
    #: narrower than this may *depend* on aligning with another plate.
    registration: float
    #: What it costs relative to a single litho pass, roughly. Stated so a
    #: composition can be judged on whether its expense is where the eye is.
    cost: float
    note: str = ""


#: The plate list. Order is press order and is not a preference.
PLATES: Final[dict[str, Plate]] = {
    plate.key: plate for plate in (
        Plate("substrate", "Substrate", 1, "print", 0.05, True, 0.30, 0.0,
              "The sheet: shade, fibre, and any true watermark in the mould."),
        Plate("antipathy", "Anti-copy ruling", 2, "print", 0.07, False, 0.30, 0.4,
              "Rulings set off a copier's screen angles, and the void "
              "pantograph. Not a latent image unless two rulings at matched "
              "ink fraction define a shape between them."),
        Plate("guilloche", "Guilloché", 3, "print", 0.07, False, 0.20, 1.2,
              "Lathe work. The security ground proper, and on a bank-note "
              "architecture the identity itself."),
        Plate("process", "Process (CMYK)", 4, "print", 0.10, True, 0.15, 1.0,
              "Everything with tone in it. Four passes, or one on a digital "
              "press with a wider registration tolerance."),
        Plate("line", "Line and type", 5, "print", 0.07, False, 0.10, 1.0,
              "Solid line and type at 100% K. The plate a reader reads."),
        Plate("microtext", "Fine text", 6, "print", 0.06, False, 0.10, 0.6,
              "On its own plate because its ink film is thinner: printed with "
              "the line plate it fills in and becomes a grey band."),
        Plate("foil_primary", "Foil — primary", 7, "foil", 0.20, False, 0.25, 3.5,
              "Hot foil, one metal, the ceremonial architecture. The single "
              "most expensive-looking operation on a sheet and the one most "
              "often spent on the wrong element."),
        Plate("foil_second", "Foil — secondary", 8, "foil", 0.25, False, 0.35, 3.0,
              "A second metal or a second pass. Its registration to the first "
              "is 0.35mm, so the two may abut and may never interlock."),
        Plate("varnish", "Tactile varnish", 9, "coating", 0.40, False, 0.30, 1.4,
              "Raised spot varnish. Felt rather than seen, which is why it is "
              "spent on a field a hand crosses, not on a hairline."),
        Plate("emboss", "Emboss die", 10, "relief", 0.60, False, 0.40, 4.0,
              "Male and female dies. Raises the sheet; nothing registers to a "
              "deformed sheet afterwards, which is why it runs last but one."),
        Plate("deboss", "Deboss die", 11, "relief", 0.60, False, 0.40, 4.0,
              "Sunk relief. A separate die — an emboss die run inverted "
              "produces a bruised sheet, not a deboss."),
        Plate("uv", "UV fluorescent", 12, "invisible", 0.25, False, 0.40, 1.8,
              "Invisible under daylight, fluorescing under 365nm. A covert "
              "layer, so nothing on it may be load-bearing in daylight."),
        Plate("numbering", "Numbering", 13, "print", 0.12, False, 0.50, 0.8,
              "Applied by a numbering box as the sheet leaves the press. One "
              "sheet, one number, mechanically — which is why a numbering box "
              "is harder to defeat than a plate."),
        Plate("variable", "Variable data", 14, "print", 0.10, True, 0.60, 0.5,
              "Per-document data printed digitally after the run. Its "
              "registration is the loosest on the sheet, so nothing "
              "structural may depend on where it lands."),
    )
}


def plate_for(key: str) -> Plate:
    try:
        return PLATES[key]
    except KeyError:
        raise PlateError(
            f"No plate named {key!r}. The press runs: "
            + ", ".join(p.key for p in sorted(PLATES.values(), key=lambda x: x.order))
        ) from None


@dataclass(frozen=True, slots=True)
class Separation:
    """One plate's worth of marks, and what the printer is being asked for."""

    plate: Plate
    fragments: tuple[str, ...]
    #: The narrowest stroke actually emitted onto this plate.
    finest: float

    @property
    def used(self) -> bool:
        return bool(self.fragments)


@dataclass
class Press:
    """A sheet under composition, held as plates.

    Every drawing call names the plate it is for, and the plate decides whether
    the call is possible. A composition that wants a 0.09mm foil rule finds out
    here, at the moment of drawing, rather than from a printer three weeks later
    with a proof that has patchy lines on it.
    """

    width: float
    height: float
    marks: dict[str, list[str]] = field(default_factory=dict)
    finest: dict[str, float] = field(default_factory=dict)
    defs: list[str] = field(default_factory=list)

    def mark(self, plate_key: str, fragment: str, *,
             stroke: float | None = None, tonal: bool = False) -> None:
        """Put a fragment on a plate, or refuse and say what the press cannot do.

        `stroke` is the narrowest stroke in the fragment, in millimetres.
        Passing it is what lets the floor be enforced; omitting it on a fragment
        that has strokes is how the floor stops meaning anything, so a fragment
        with no stated stroke is treated as an area and is only checked for tone.
        """
        plate = plate_for(plate_key)
        if stroke is not None and stroke < plate.stroke_floor:
            raise PlateError(
                f"A {stroke:.3f}mm stroke was asked for on the {plate.name} "
                f"plate, whose floor is {plate.stroke_floor:.2f}mm. "
                f"{plate.note} Either thicken the stroke or move it to a plate "
                "that can hold it — moving it is usually the right answer, "
                "because a fine line wanting to be gold usually wants to be "
                "the line plate in a metal ink."
            )
        if tonal and not plate.tonal:
            raise PlateError(
                f"A tonal fill was asked for on the {plate.name} plate, which "
                "is binary: the operation either happens at a point or it does "
                "not. What arrives from the press is the plate at 100%, which "
                "is never what the gradient was for. Put the tone on `process` "
                "and the shape on this plate."
            )
        self.marks.setdefault(plate_key, []).append(fragment)
        if stroke is not None:
            current = self.finest.get(plate_key)
            self.finest[plate_key] = stroke if current is None else min(current, stroke)

    def separation(self, plate_key: str) -> Separation:
        return Separation(
            plate=plate_for(plate_key),
            fragments=tuple(self.marks.get(plate_key, ())),
            finest=self.finest.get(plate_key, 0.0),
        )

    def used_plates(self) -> tuple[Plate, ...]:
        return tuple(
            plate for plate in sorted(PLATES.values(), key=lambda p: p.order)
            if self.marks.get(plate.key)
        )

    @property
    def relative_cost(self) -> float:
        """Roughly what this sheet costs against a single litho pass.

        Stated so a composition can be judged on *where* its expense sits. A
        sheet that spends 3.5 on a foil plate carrying a hairline nobody sees at
        arm's length has bought the wrong thing, and the number is the fastest
        way to notice.
        """
        return round(sum(plate.cost for plate in self.used_plates()), 2)

    @staticmethod
    def _recolour(fragment: str, colour: str) -> str:
        for token in ('fill="#000000"', 'fill="#000"',
                      'stroke="#000000"', 'stroke="#000"'):
            attribute, _ = token.split("=")
            fragment = fragment.replace(token, f'{attribute}="{colour}"')
        return fragment

    def _as_seen(self, plate: Plate, fragment: str) -> str:
        """One plate's marks as the **eye** sees them on a finished sheet.

        This is the distinction the first render of these plates got wrong, and
        it produced solid black rectangles across two of the six: a composite is
        a simulation of a printed sheet, and a separation is an instruction to a
        press. They are different pictures of the same plate and neither is the
        other.

        - *print* and *foil* appear as drawn. Ink and metal are visible.
        - *relief* — emboss and deboss — has **no colour at all**. What the eye
          sees is a lit wall on one side and a shadow wall on the other, which
          is why it is drawn twice offset and never once in black.
        - *coating* is felt, not seen. A tactile varnish on an uncoated sheet
          is a change in sheen of a few per cent; drawn at any strength that
          reads on screen it is a lie about what arrives.
        - *invisible* is invisible. UV ink under daylight is nothing, and
          drawing it in the composite would put a mark on the sheet that a
          holder will never see.
        """
        if plate.kind == "invisible":
            return ""
        if plate.kind == "relief":
            lit = self._recolour(fragment, "#FFFFFF")
            shadow = self._recolour(fragment, "#8C8377")
            direction = 0.22 if plate.key == "emboss" else -0.22
            return (
                f'<g opacity="0.85" transform="translate({direction:.2f}'
                f' {direction:.2f})">{shadow}</g>'
                f'<g opacity="0.9" transform="translate({-direction:.2f}'
                f' {-direction:.2f})">{lit}</g>'
            )
        if plate.kind == "coating":
            return f'<g opacity="0.045">{self._recolour(fragment, "#FFFFFF")}</g>'
        return fragment

    def svg(self, only: str | None = None, *, ground: str = "",
            separation: bool = False) -> str:
        """The sheet as the eye sees it, or one plate as the press receives it.

        `separation=True` renders the marks raw, in their own colours, on white:
        that is what a printer looks at, and judging a foil plate in gold on
        ivory is judging the simulation rather than the plate.
        """
        order = [p.key for p in sorted(PLATES.values(), key=lambda x: x.order)]
        keys = [k for k in order if only in (None, k)]
        body = "".join(
            "".join(self.marks.get(k, ())) if separation
            else self._as_seen(plate_for(k), "".join(self.marks.get(k, ())))
            for k in keys
        )
        backdrop = (
            f'<rect x="0" y="0" width="{self.width:g}" height="{self.height:g}"'
            f' fill="{ground}"/>' if ground else ""
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg"'
            f' viewBox="0 0 {self.width:g} {self.height:g}"'
            f' width="{self.width:g}mm" height="{self.height:g}mm"'
            ' preserveAspectRatio="none" aria-hidden="true" focusable="false">'
            + (f"<defs>{''.join(self.defs)}</defs>" if self.defs else "")
            + backdrop + body + "</svg>"
        )

    def specification(self) -> str:
        """The plate list as a printer would be handed it."""
        lines = [
            f"SHEET  {self.width:g} × {self.height:g}mm",
            f"PLATES {len(self.used_plates())}   "
            f"relative cost ≈ {self.relative_cost:g}× a single litho pass",
            "",
            f"{'#':>2}  {'PLATE':<16} {'KIND':<10} {'FINEST':>8}  {'FLOOR':>6}  "
            f"{'REG':>5}",
        ]
        for plate in self.used_plates():
            finest = self.finest.get(plate.key)
            shown = f"{finest:.3f}mm" if finest else "areas"
            lines.append(
                f"{plate.order:>2}  {plate.name:<16} {plate.kind:<10} "
                f"{shown:>8}  {plate.stroke_floor:.2f}mm  {plate.registration:.2f}"
            )
        lines += [
            "",
            "NOT YET PROVEN. Every operation above is a specification. None has",
            "been run on a press, on paper, in this project. Foil adhesion,",
            "emboss depth, varnish relief, hairline survival and the fluorescent",
            "response are stated from the operations' known behaviour and are",
            "not measurements of these plates.",
        ]
        return "\n".join(lines)
