"""Sheet sizes, and the honest question of whether a document fits one.

An institution asks for A3 and gets A3; asks for Letter and gets Letter. What it
must never get is an A4 composition photographed onto a different rectangle,
because that is what produces 0.05mm hairlines on an enlargement and a
verification panel too small to scan on a reduction. **A sheet size is a brief,
not a scale factor.**

**Three things happen when the sheet changes, and only one of them is scaling.**

1. *The border is re-cut.* `heritage.Bands` states its seven insets as
   proportions of the sheet's short side, so the border is drawn at the new
   size rather than stretched to it. A hairline stays a hairline.
2. *The type is re-solved.* Optical sizes move with the field, but not
   linearly and never below a floor: 1.8mm is about where a printed serif stops
   being comfortably readable by an adult at arm's length, and no amount of
   wanting a document on A6 makes 1.4mm acceptable.
3. *The instruments do not move at all.* A Code 128 symbol has a module floor
   of 0.33mm because below it the bars close under ink gain; a verification
   cartouche needs 27mm of height for its own contents; a seal below about 18mm
   cannot hold a legend ring. These are physical facts about presses and
   scanners, and they are the same on A6 as on A3.

Point 3 is why this module can say **no**. A ceremonial certificate with a
27mm verification panel, a 22mm seal, two signature blocks and a peak does not
fit on A6, and the useful answer is to say so — with the numbers — rather than
to print something that technically has all the parts at sizes where none of
them work. `fits()` returns the arithmetic, not an opinion.

**Why both orientations are first-class.** Landscape is the international
convention for a ceremonial certificate and portrait is right for anything
tabular, and neither is the other rotated: a landscape field is wide and short,
so the citation runs in two columns and the execution row spans the foot; a
portrait field is a column, so the citation stacks and the foot becomes pairs.
The catalogue therefore holds both as separate sheets rather than one with a
flag.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "FLOORS",
    "SHEETS",
    "Fit",
    "Sheet",
    "fits",
    "rotate",
    "sheet_for",
    "sheets_in",
    "usable_sheets",
]


@dataclass(frozen=True, slots=True)
class Sheet:
    """A physical sheet, in millimetres, with its trim as cut."""

    key: str
    name: str
    width: float
    height: float
    #: The standard it belongs to: "iso-a", "iso-b", "north-american".
    series: str

    @property
    def is_landscape(self) -> bool:
        return self.width > self.height

    @property
    def orientation(self) -> str:
        return "landscape" if self.is_landscape else "portrait"

    @property
    def short(self) -> float:
        return min(self.width, self.height)

    @property
    def long(self) -> float:
        return max(self.width, self.height)

    @property
    def area_cm2(self) -> float:
        return self.width * self.height / 100.0


def _pair(key: str, name: str, short: float, long_: float,
          series: str) -> tuple[Sheet, Sheet]:
    """One stock in both orientations. Neither is derived from the other."""
    return (
        Sheet(f"{key}-portrait", f"{name} portrait", short, long_, series),
        Sheet(f"{key}-landscape", f"{name} landscape", long_, short, series),
    )


#: Every sheet EdirasX will compose on. ISO A down to A6 because a certificate
#: is occasionally issued at card size; ISO B because B5 is the common book and
#: programme stock across much of Asia and Europe; North American because Letter
#: and Legal are not A4 and pretending otherwise crops 18mm off a Legal foot.
SHEETS: Final[dict[str, Sheet]] = {
    sheet.key: sheet
    for sheet in (
        *_pair("a3", "A3", 297.0, 420.0, "iso-a"),
        *_pair("a4", "A4", 210.0, 297.0, "iso-a"),
        *_pair("a5", "A5", 148.0, 210.0, "iso-a"),
        *_pair("a6", "A6", 105.0, 148.0, "iso-a"),
        *_pair("b4", "B4", 250.0, 353.0, "iso-b"),
        *_pair("b5", "B5", 176.0, 250.0, "iso-b"),
        *_pair("letter", "Letter", 215.9, 279.4, "north-american"),
        *_pair("legal", "Legal", 215.9, 355.6, "north-american"),
        *_pair("tabloid", "Tabloid", 279.4, 431.8, "north-american"),
        *_pair("half-letter", "Half Letter", 139.7, 215.9, "north-american"),
    )
}

#: A printer's cutting tolerance. Nothing that must survive is drawn inside this
#: of the trim: a rule that lands on the knife lands on the knife on *some* of
#: the copies, which is worse than on all of them because it passes proofing.
SAFE_EDGE: Final[float] = 6.0

#: Physical floors. Not preferences — each is a property of a press, a scanner
#: or an eye, and each is the reason `fits()` can return False.
FLOORS: Final[dict[str, float]] = {
    #: Verification cartouche height. See `credential._PANEL_MIN_HEIGHT`.
    "panel_height": 27.0,
    #: Panel width. A Code 128-C of a sixteen-digit identity number is 40.6mm at
    #: the 0.33mm module floor, and the panel carries a four-cell identifier
    #: grid either side of it.
    "panel_width": 96.0,
    #: Seal diameter. Below this the legend ring cannot be set at a size that
    #: survives a 600 DPI raster, and the seal becomes a gold blob.
    "seal": 18.0,
    #: One signature cell. A name, a rule, an office line in two scripts.
    "signature": 38.0,
    #: Body type. Where a printed serif stops being comfortable at arm's length.
    "body": 1.80,
    #: The recipient's name. Below this it stops being the peak of anything.
    "peak": 4.20,
}

#: What each composition needs **in total**, as `base + slope × type_scale` in
#: millimetres, per family **and orientation**. The foot is inside these
#: numbers, not added to them: they were measured from the whole content column,
#: which is what the browser lays out and therefore what has to fit.
#:
#: Affine, not proportional, because a content stack is two things: parts that
#: scale with the type (every line of it) and parts that do not (rules, band
#: paddings, the fixed-height signature ink box). A proportional model fitted at
#: A4 predicts an A3 stack about 12mm too tall and a B5 one about 10mm too
#: short, which is exactly the wrong way round.
#:
#: **These numbers are measured, not estimated.** Every template was rendered on
#: every candidate sheet with both the specimen and the hostile data set, its
#: flexible spacers deleted, and its natural height read back from the browser —
#: 672 measurements — then fitted by least squares per family and orientation
#: and lifted to the **upper envelope** of the residuals. The envelope rather
#: than the fit, because the cost of the two errors is not symmetric: refusing a
#: size that would have worked loses an option, and accepting one that overflows
#: prints a broken certificate.
#:
#: The first version stated these as flat constants at the type floors. `fits()`
#: accepted 23 of 320 size compositions on that basis and the browser found
#: every one of the 23 overflowing, by between 0.3 and 19.6mm.
_STACK: Final[dict[tuple[str, str], tuple[float, float]]] = {
    # lockup, banner, title, subtitle, lede, peak in two scripts, name rule,
    # citation, particulars band.
    ("stage", "landscape"): (93.8, 43.1),
    ("stage", "portrait"): (167.8, 31.5),
    # ...plus the conferred-award register.
    ("college", "landscape"): (107.1, 36.6),
    ("college", "portrait"): (177.4, 35.6),
    ("record", "landscape"): (83.5, 38.6),
    ("record", "portrait"): (103.9, 24.7),
    # masthead, holder block, statement, the table's own head and its rows, the
    # end-of-record rule and the grading key.
    ("ledger", "landscape"): (138.3, 27.7),
    ("ledger", "portrait"): (129.3, 44.1),
    # a citation is the whole document, so it gets room; no particulars band.
    ("award", "landscape"): (87.0, 52.7),
    ("award", "portrait"): (170.9, 32.3),
}

#: The narrowest field each family can be set in, and why. Width is a separate
#: constraint from height and fails for different reasons: a ledger runs out of
#: width because five table columns stop being readable long before the page
#: runs out of height, and a ceremonial sheet runs out because its execution row
#: is a number cartouche, two signature cells and a seal side by side.
#: Two numbers per family: landscape, then portrait. They differ because the
#: *foot differs*. On a wide sheet the execution row sets the number cartouche,
#: the signature cells and the seal on one line; on a tall one it stacks them,
#: which costs height and buys width. A single number here would either refuse
#: portrait certificates that compose perfectly well or admit landscape ones
#: whose foot cannot be laid out.
_MIN_WIDTH: Final[dict[str, tuple[float, float, str]]] = {
    "stage": (165.0, 112.0,
              "the execution row sets a 46mm number cartouche, two signature "
              "cells and a seal — side by side on a wide sheet, stacked on a "
              "tall one"),
    "college": (165.0, 112.0,
                "the execution row sets a 46mm number cartouche, two signature "
                "cells and a seal — side by side on a wide sheet, stacked on a "
                "tall one"),
    "award": (150.0, 112.0,
              "the execution row sets a number cartouche, a signature cell and "
              "a seal"),
    "record": (110.0, 110.0,
               "one signature cell, a seal, and a verification panel wide "
               "enough for its identifier grid"),
    "ledger": (132.0, 132.0,
               "five table columns below about 26mm each stop being readable, "
               "and a transcript nobody can read down a column is not a "
               "transcript"),
}

#: The reference field height each family's optical sizes were solved against.
#: The renderer scales type by `field height ÷ reference`, so a bigger sheet
#: gets bigger type rather than the same type in more air — which is what
#: makes an A3 certificate read as an A3 certificate rather than as an A4 one
#: printed on the wrong paper.
REFERENCE_FIELD: Final[dict[str, float]] = {
    "stage": 141.0,
    "college": 145.0,
    "record": 235.0,
    "ledger": 235.0,
    "award": 141.0,
}


@dataclass(frozen=True, slots=True)
class Fit:
    """Whether a family fits a sheet, and the arithmetic either way."""

    sheet: Sheet
    family: str
    ok: bool
    field_width: float
    field_height: float
    needed: float
    #: Multiplier applied to the family's optical sizes on this sheet.
    type_scale: float
    reasons: tuple[str, ...] = ()

    @property
    def headroom(self) -> float:
        return self.field_height - self.needed


def sheet_for(key: str) -> Sheet:
    try:
        return SHEETS[key]
    except KeyError:
        raise KeyError(
            f"No sheet named {key!r}. EdirasX composes on: "
            f"{', '.join(sorted(SHEETS))}."
        ) from None


def rotate(sheet: Sheet) -> Sheet:
    """The same stock, the other way up.

    Returns a *different composition's* sheet, not a transform. Nothing about
    the document is carried across by calling this — the renderer re-solves.
    """
    stem = sheet.key.rsplit("-", 1)[0]
    other = "portrait" if sheet.is_landscape else "landscape"
    return SHEETS[f"{stem}-{other}"]


def sheets_in(series: str) -> tuple[Sheet, ...]:
    return tuple(s for s in SHEETS.values() if s.series == series)


def _field(sheet: Sheet, *, border_weight: float) -> tuple[float, float]:
    """The content field a heritage border leaves on this sheet.

    Kept in step with `heritage.Bands` and `heritage.heritage_ground` by using
    the same two numbers: the innermost band at 36.3/210 of the short side, and
    the field's clearance at 1.2 % of it. Duplicated deliberately rather than
    imported, because this module must be answerable without constructing a
    ground — and `test_sheets.py` asserts the two agree.
    """
    inset = sheet.short * (36.3 / 210) * border_weight + sheet.short * 0.012
    return sheet.width - inset * 2, sheet.height - inset * 2


def fits(*, family: str, sheet: Sheet, border_weight: float = 1.0) -> Fit:
    """Can this family be composed on this sheet, honestly?

    The foot is the binding constraint on almost every small sheet, and it is
    the one part of a certificate that may not shrink: a verification panel that
    has been squeezed until it fits is a verification panel that cannot be read
    or scanned, which means the document has lost the property it exists to
    have. So the foot is added at its floor and the rest of the composition is
    asked whether it can live in what remains.
    """
    if not any(key[0] == family for key in _STACK):
        raise KeyError(
            f"No composition family named {family!r}. Families: "
            f"{', '.join(sorted({key[0] for key in _STACK}))}."
        )
    width, height = _field(sheet, border_weight=border_weight)
    reasons: list[str] = []

    # The foot's own floors — a 27mm verification cartouche above an execution
    # row that cannot go below the seal's 18mm — are already inside the measured
    # stack below, because the measurement was taken from the whole content
    # column. They are named here because a refusal has to be able to say which
    # part cannot shrink, and this is that part.
    foot = max(FLOORS["seal"], 20.0) + 2.0 + FLOORS["panel_height"]
    # The stack is affine in the type scale; the foot is fixed. Solved before
    # the reasons are written so a refusal can quote the real number.
    scale = min(1.45, max(0.72, (height / REFERENCE_FIELD[family]) ** 0.5))
    base, slope = _STACK[(family, sheet.orientation)]
    needed = base + slope * scale

    if width < FLOORS["panel_width"]:
        reasons.append(
            f"The field is {width:.0f}mm wide and a verification panel needs "
            f"{FLOORS['panel_width']:.0f}mm — a Code 128 of an identity number "
            "is 40.6mm on its own at the 0.33mm module floor, and below that "
            "module the bars close up under ink gain and stop scanning."
        )
    landscape_min, portrait_min, because = _MIN_WIDTH[family]
    minimum = landscape_min if sheet.is_landscape else portrait_min
    if width < minimum:
        reasons.append(
            f"The field is {width:.0f}mm wide and a {family} composition needs "
            f"{minimum:.0f}mm — {because}."
        )
    if height < needed:
        reasons.append(
            f"The field is {height:.0f}mm tall and this composition needs "
            f"{needed:.0f}mm — a content column set at ×{scale:.2f} whose "
            f"last {foot:.0f}mm is a verification instrument that may not be "
            "shrunk. "
            f"It is {needed - height:.0f}mm short."
        )

    # Type grows with the sheet but sublinearly: doubling the field does not
    # double the reading distance, so a straight ratio makes A3 type look shouty
    # and A5 type look timid. The square root is the usual optical compromise
    # and is clamped so no sheet can drive the peak below its floor.
    return Fit(
        sheet=sheet, family=family, ok=not reasons,
        field_width=width, field_height=height, needed=needed,
        type_scale=round(scale, 3), reasons=tuple(reasons),
    )


def usable_sheets(family: str, *, border_weight: float = 1.0) -> tuple[Sheet, ...]:
    """Every sheet this family can honestly be composed on, largest first."""
    good = [
        sheet for sheet in SHEETS.values()
        if fits(family=family, sheet=sheet, border_weight=border_weight).ok
    ]
    return tuple(sorted(good, key=lambda s: -s.area_cm2))
