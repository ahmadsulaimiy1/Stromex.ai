"""How much of the vocabulary a document may spend, and on what.

`geometry.py` and `architecture.py` are the vocabulary. This file is the rule
that a nursery completion certificate and a doctoral award are not the same
object — and it is a *constraint the code enforces* rather than a note in a
style guide.

**What increases with level is richness, and richness is architecture plus
ornament plus material.** An earlier draft of this file said the opposite: that
Level IV was "more disciplined, not busier", and that ornament belonged only at
the edge of the sheet. That was an overcorrection, and it produced flagship
plates that were technically exact and visually inexpensive. The corrected
reading, which this file now enforces:

    I    Elegant        A statement of results, a report card, a letter.
                        Genuinely well made — an engraved rule, a real metal,
                        generous margins, a considered masthead. Not ornate,
                        and not apologetic about it. A document at this level
                        should still look like it came from an institution
                        that knows what a document is.

    II   Premium        A diploma, a professional certificate. Clearly
                        luxurious: a multi-register frame, corner geometry, a
                        worked ground, metal rules that read as metal. Somebody
                        holding it can tell it cost money to produce.

    III  Ceremonial     A graduation, a distinction, a major award. Richly
                        ornamented: guilloché registers, strapwork, medallions,
                        an allover field, a cartouche or a crest architecture.
                        The composition acquires a ceremonial centre and the
                        metal becomes a major visual component.

    IV   Flagship       A doctorate, an honorary award, a royal or national
                        honour. Exceptional craftsmanship: the whole vocabulary
                        is available — corner blocks with inset medallions,
                        crested frames, multiple guilloché systems, dense
                        geometric registers, radiant fields, serial-bearing fine text, a
                        deterministic security substrate, two metals. It should
                        be capable of looking extraordinary, because what it
                        certifies is.

**The two constraints that survive, and why they are not asceticism.**

`content_ink` is the most ink any background construction may lay down *behind
the words*. It is a legibility guarantee, not a decoration ceiling: outside the
content field a Level IV plate may be as dense as the design calls for, and the
frame registers routinely are. What it forbids is a guilloché running behind a
recipient's name at a strength that fights it — which is a typography failure,
not an ornament failure, and it is measured rather than asserted.

`peak_ratio` is the rule that the composition has one dominant moment. That
remains true at every level and gets *stronger* as levels rise, because a rich
plate has more ways to lose its hierarchy. One peak does not mean one ornament;
it means the eye lands in one place first, and everything else is discovered
after.

**There is deliberately no whitespace floor.** An earlier version carried one,
expressed as a fraction of the sheet that had to be unmarked, and it was wrong
in principle: a richly worked ground with excellent hierarchy has no less
breathing space than a blank one, it simply spends it differently. Air is a
compositional decision made by eye against a rendered plate, and encoding it as
a number produced empty documents that passed.
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
    #: The perimeter register stack, outside→in, as `(width_mm, kind)` pairs
    #: understood by `architecture.register_stack`. This is what makes a frame
    #: an architecture rather than a set of concentric rectangles: each band has
    #: a stated job, and the sequence runs coarse to fine inwards.
    registers: tuple[tuple[float, str], ...]
    #: How far the content field sits inside the innermost frame element.
    field_inset: float
    #: The most ink, as a proportion of the content field's area, that a
    #: background construction may lay down *behind the words*. A legibility
    #: guarantee; see the module docstring. Measured, not asserted.
    content_ink: float
    #: How much larger the single peak must be than the next-largest element.
    peak_ratio: float
    #: The default metal for this level, by key into `gilding.METALS`. A
    #: composition may choose another; what the level fixes is how *much* metal
    #: is structurally available to it.
    metal: str = "royal"
    #: Whether this level may carry a second metal. Two metals is a real
    #: production decision — a second foil is a second pass on press — so it is
    #: granted at a level rather than taken by a template.
    second_metal: bool = False
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
        name="Elegant",
        permits=frozenset({"rule", "khatam", "spreader"}),
        frame=(13.0,),
        registers=((0.5, "rule"),),
        field_inset=8.0,
        content_ink=0.0,
        peak_ratio=1.5,
        metal="antique",
        description="Everyday academic documents: results, letters, statements.",
        notes=(
            "Elegant is not plain. The whole budget is spent on one engraved "
            "metal rule, a real masthead and a generous margin, because at "
            "this level those three are what separate an institution's "
            "document from a printout — and a statement of results that "
            "arrives looking like a prize is a statement nobody trusts.",
        ),
    ),
    Budget(
        level=2,
        name="Premium",
        permits=frozenset({
            "rule", "khatam", "spreader", "corner", "lattice", "arabesque",
            "tessellation", "cartouche",
        }),
        frame=(8.0, 14.0),
        registers=((0.5, "rule"), (3.2, "micro"), (1.4, "void"), (0.4, "rule")),
        field_inset=9.0,
        content_ink=0.030,
        peak_ratio=1.7,
        metal="antique",
        description="Diplomas, professional certificates, qualifications.",
        notes=(
            "Clearly luxurious. A worked register enters the frame and a "
            "lattice enters the ground; the metal starts behaving like metal "
            "rather than like a brown line.",
        ),
    ),
    Budget(
        level=3,
        name="Ceremonial",
        permits=frozenset({
            "rule", "khatam", "spreader", "corner", "lattice", "arabesque",
            "tessellation", "cartouche", "guilloche", "rosette", "seal",
            "girih", "medallion", "mandala", "spine", "arch",
        }),
        frame=(6.5, 11.0, 17.0),
        registers=(
            (0.6, "rule"), (2.6, "lathe"), (1.0, "void"),
            (5.0, "girih"), (1.0, "void"), (0.4, "rule"),
        ),
        field_inset=10.0,
        content_ink=0.045,
        peak_ratio=1.9,
        metal="royal",
        second_metal=True,
        description="Graduation, distinction, major awards.",
        notes=(
            "Richly ornamented. Lathe work and strapwork both enter the frame, "
            "the ground carries an allover mandala, and the composition "
            "acquires a ceremonial centre — a medallion, a cartouche or a "
            "crest architecture. The content field's ink ceiling is what keeps "
            "all of that behind the words rather than in front of them.",
        ),
    ),
    Budget(
        level=4,
        name="Flagship",
        permits=frozenset({
            "rule", "khatam", "spreader", "corner", "lattice", "arabesque",
            "tessellation", "cartouche", "guilloche", "rosette", "seal",
            "girih", "medallion", "mandala", "spine", "arch",
            "corner_block", "cresting", "radiant", "finetext", "fibres",
            "screen", "squares", "emboss", "foil",
        }),
        frame=(5.5, 9.5, 15.0, 21.0),
        registers=(
            (0.7, "rule"), (2.4, "lathe"), (0.8, "void"),
            (6.5, "micro"), (0.8, "void"), (4.6, "girih"),
            (1.2, "void"), (0.5, "rule"),
        ),
        field_inset=11.0,
        content_ink=0.050,
        peak_ratio=2.1,
        metal="royal",
        second_metal=True,
        description="Doctorates, highest honours, honorary and royal awards.",
        notes=(
            "Exceptional. Corner blocks with inset medallions, a crested "
            "frame, two guilloché systems, a dense geometric register, "
            "fine text carrying the document's own serial, a deterministic "
            "substrate and a second metal. The question at this level is not "
            "whether there is too much; it is whether every expensive-looking "
            "element has been designed well enough to deserve its place.",
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
