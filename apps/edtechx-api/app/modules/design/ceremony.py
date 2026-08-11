"""How much of the geometry a document may spend.

`geometry.py` is a vocabulary of fourteen constructions. This file is the rule
that no document uses all of them — and it is a *constraint the code enforces*
rather than a note in a style guide, because the failure mode it prevents is the
one every certificate system falls into: having built an ornament library,
putting the whole library on every page.

**Four levels, and the thing that increases is architecture, not decoration.**

    I   Institutional  a report card, an enrolment letter, a statement of
                       results. One engraved rule and air. Nothing else earns
                       its place on a document somebody files.
    II  Premium        a diploma, a professional certificate. A frame with two
                       registers, corner geometry, a lattice at the threshold
                       of visibility.
    III Ceremonial     a graduation, a distinction, a major award. Lathe work
                       enters — a guilloché band in the frame, a rosette behind
                       the seal. The composition acquires a centre.
    IV  Flagship       a doctorate, an honorary award. Everything III has, plus
                       the sheet-scale field, the deterministic substrate, and
                       microtext carrying the document's own serial.

**Maximum sophistication is not maximum ornament.** A Level IV plate obeys the
same two rules a Level I plate does — one visual peak, and ink coverage inside
the content field below the ceiling — and it is *more* disciplined about them,
not less, because it has more ways to break them. What Level IV buys is
precision at the edge of the sheet and in the substrate: places the eye does not
go first and a loupe goes immediately.

**Ornament stays at the architectural edge.** Every level's budget names a
`field_ink` ceiling, and the only constructions permitted inside the content
field at any level are ones that stay under it. Guilloché behind a name, a
lattice behind a table, a corner colliding with a signature: these are the
specific failures the ceiling exists to make impossible rather than
discouraged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

__all__ = ["LEVELS", "Budget", "budget_for", "level_of"]


@dataclass(frozen=True, slots=True)
class Budget:
    """What one ceremonial level permits, in millimetres and proportions."""

    level: int
    name: str
    #: The constructions this level may draw. A name absent here is not drawn,
    #: whatever a template asks for.
    permits: frozenset[str]
    #: Sheet margins, outside→in. Each entry is an inset in mm from the trim.
    frame: tuple[float, ...]
    #: How far the content field sits inside the innermost frame element.
    field_inset: float
    #: The most ink, as a proportion of the content field's area, that any
    #: background construction may lay down inside it. Measured, not asserted —
    #: see `test_plates.py`.
    field_ink: float
    #: The floor for unmarked area across the whole sheet. Air is the most
    #: expensive material on paper and the defining absence in cheap work.
    whitespace_floor: float
    #: How much larger the single peak must be than the next-largest element.
    peak_ratio: float
    description: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    def permits_all(self, *names: str) -> bool:
        return all(name in self.permits for name in names)


#: The four levels. Read the `permits` sets downward: each is a superset of the
#: one above, which is what makes "more ceremonial" a coherent claim rather than
#: a different design.
LEVELS: Final[tuple[Budget, ...]] = (
    Budget(
        level=1,
        name="Institutional",
        permits=frozenset({"rule", "khatam"}),
        # One inset. A document at this level is a sheet of paper with a rule
        # on it, and the rule is there to say where the institution's page
        # ends rather than to decorate it.
        frame=(14.0,),
        field_inset=8.0,
        field_ink=0.0,
        whitespace_floor=0.55,
        peak_ratio=1.5,
        description="Everyday academic documents: results, letters, statements.",
        notes=(
            "No ornament at all inside the field, and none in the frame beyond "
            "a single engraved rule. A statement of results that arrives "
            "looking like a prize is a statement nobody trusts.",
        ),
    ),
    Budget(
        level=2,
        name="Premium",
        permits=frozenset({"rule", "khatam", "corner", "lattice", "arabesque"}),
        frame=(9.0, 15.0),
        field_inset=9.0,
        # A lattice may enter the field, and only just: this ceiling is the
        # difference between a watermark milled into the sheet and a pattern
        # printed over a certificate.
        field_ink=0.030,
        whitespace_floor=0.50,
        peak_ratio=1.7,
        description="Diplomas, professional certificates, qualifications.",
    ),
    Budget(
        level=3,
        name="Ceremonial",
        permits=frozenset({
            "rule", "khatam", "corner", "lattice", "arabesque",
            "guilloche", "rosette", "seal",
        }),
        frame=(7.0, 12.0, 18.0),
        field_inset=10.0,
        field_ink=0.045,
        whitespace_floor=0.46,
        peak_ratio=1.9,
        description="Graduation, distinction, major awards.",
        notes=(
            "Lathe work enters here and stays in the frame and behind the "
            "seal. A rosette behind a name is the single fastest way to make "
            "an expensive document look like a printed novelty.",
        ),
    ),
    Budget(
        level=4,
        name="Flagship",
        permits=frozenset({
            "rule", "khatam", "corner", "lattice", "arabesque",
            "guilloche", "rosette", "seal", "microtext", "fibres",
            "screen", "squares",
        }),
        frame=(6.0, 10.5, 16.0, 22.0),
        field_inset=11.0,
        field_ink=0.050,
        # Deliberately *not* lower than Level III's. What Level IV adds sits at
        # the edge of the sheet and in the substrate, not in the field, so the
        # field's discipline does not change — the whole point of the level is
        # that it is more precise, not busier.
        whitespace_floor=0.44,
        peak_ratio=2.1,
        description="Doctorates, highest honours, honorary and royal awards.",
        notes=(
            "Everything Level IV adds is at the edge or in the substrate: "
            "microtext carrying the document's own serial, deterministic "
            "fibres, an anti-copy screen, the interlocking-squares "
            "construction shown rather than resolved. A person reads the same "
            "page as at Level III and a loupe reads a different one.",
        ),
    ),
)

_BY_LEVEL = {budget.level: budget for budget in LEVELS}

#: A sensible level for each document purpose and qualification category, used
#: when a template does not state one. An institution may raise or lower it; it
#: may not exceed IV, and a report card that asks for IV gets an argument in the
#: review rather than a silent grant.
_DEFAULTS: Final[dict[str, int]] = {
    "report_card": 1,
    "transcript": 2,
    "document": 2,
    "certificate": 3,
    "doctoral": 4,
    "honorary": 4,
}


def budget_for(level: int) -> Budget:
    if level not in _BY_LEVEL:
        raise ValueError(
            f"{level!r} is not a ceremonial level. One of: "
            + ", ".join(f"{b.level} ({b.name})" for b in LEVELS)
        )
    return _BY_LEVEL[level]


def level_of(template) -> Budget:
    """The level a template asks for, or the sensible default for its purpose.

    Read from `custom['ceremony']` so it is a design decision recorded on the
    template version — a document issued in 2027 keeps the level it was
    designed at when the institution raises the level of new ones in 2029.
    """
    declared = (getattr(template, "custom", None) or {}).get("ceremony")
    if declared is not None:
        return budget_for(int(declared))
    purpose = getattr(template, "purpose", "document")
    return budget_for(_DEFAULTS.get(purpose, 2))
