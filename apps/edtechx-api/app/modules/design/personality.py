"""Institutional personality: six architectures, not six palettes.

The criticism this module answers is that the design decisions were internally
derived — twenty-four documents that were one composition in six colourways.
Changing an accent is not designing for an institution. What differs between a
collegiate diploma and a state instrument is not the gold; it is **where
authority sits on the sheet**, and everything else follows from that.

So each personality below states, first, where its authority sits, and only then
what it is made of. Two of the six have no border at all. One has no foil at
all. One puts the guilloché in front rather than behind. If two of these were
rendered with the text removed they would still not be mistakable for each
other, and that is the test this module exists to pass.

---

**Why these six, and what each is derived from.**

These are compositional traditions, analysed structurally. No institution's
artwork is reproduced here and none is fetched: what is carried across is *why
the composition works*, which is the part that is transferable and the part that
tracing would miss anyway.

**COLLEGIATE** — the old university diploma. Its striking property is
subtraction: **no border, no ornament, no colour.** A vast margin, one column of
centred text in a single face, the arms small at the head, and a wafer seal that
is the only object on the sheet. It works because the authority is *institutional
rather than graphical* — a document confident enough to leave four-fifths of
itself empty is making a claim about who issued it. The whole security burden
falls on the substrate and the seal, which is honest for a sheet held in one
registry and verified by letter. **Hardest for a generative engine**, because
every instinct is to add and this one requires the discipline to remove.

**CHANCERY** — the state and diplomatic instrument. Authority sits in the
**arms**, which take a third of the sheet and are the peak; the text is
subordinate, administrative, and set as a block rather than a display. One heavy
rule rather than a frame. An intaglio-feel guilloché panel sits *behind the
arms* and nowhere else, so the security is where the authority is. Signature and
counter-signature at the foot, because a state instrument is made by two offices,
not one.

**COURT** — the illuminated manuscript tradition. Here the frame **is** the
document: an illuminated border in registers of decreasing scale, a shamsa
medallion at the head, and the text held in a cartouche floating in a field.
Hierarchy is vertical and the composition reads inward rather than downward. The
script leads and the Latin follows, because the sheet was composed for it.

**INTAGLIO** — the bank-note and security-printer tradition. Its identity **is**
the guilloché: the lathe work is in front, at full strength, and the type sits
in reserved panels cut out of it. A vault oval where a portrait would be, a
numeral treated as a denomination, microtext rails as visible structure rather
than a hidden register, and a security thread. The most *printed* of the six and
the one whose expense is most visibly in the plate rather than in the paper.

**LETTERPRESS** — the archival tradition. **No foil at all**, one ink, deep
deboss, laid paper, an engraved crest, wide letterspaced small capitals. The
luxury is entirely tactile: the value is in what a hand feels when it crosses
the sheet, which is why the expense goes on dies rather than on metal. Restraint
that is expensive rather than restraint that is cheap, and the difference is
whether the deboss is deep enough to catch a shadow.

**MERIDIAN** — the modern institutional register. Swiss discipline: an
asymmetric grid, one enormous field of white, type as the only ornament, a single
hairline, and exactly one foil element so that the one is unmistakable. Optical
alignment carried to the point where it is felt rather than seen. This is the
register a contemporary research institution actually commissions, and it fails
instantly if the spacing is approximate.

---

**The rule that governs all six.** Ornament is not decoration and may not be
chosen. Every border, medallion, lattice and guilloché on a sheet descends from
the institution's own motif — `signature.motif_for()` — so the geometry is a
consequence of *which institution* rather than of taste. The test is literal:
render the sheet with every word removed and it must still be identifiably that
institution's. `tools/design/masterpieces.py` renders exactly that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = ["PERSONALITIES", "Personality", "personality_for"]


@dataclass(frozen=True, slots=True)
class Personality:
    """One institutional architecture, stated as decisions rather than colours."""

    key: str
    name: str
    #: The one sentence that decides everything else.
    thesis: str
    #: What the tradition is, structurally, and why the composition works.
    derivation: str

    # --- architecture --------------------------------------------------------
    #: Where the eye is meant to go first: "name", "arms", "seal", "title",
    #: "guilloche". This is the single decision the rest of the sheet serves.
    authority: str
    #: "none" | "rule" | "band" | "illuminated" | "engine"
    enclosure: str
    #: Margin as a proportion of the sheet's short side. A collegiate sheet
    #: spends a quarter of itself on margin; an intaglio sheet spends a
    #: fifteenth, because its edge is doing work.
    margin: float
    #: Where the composition's axis sits horizontally, 0.5 being centred. Only
    #: MERIDIAN is off-centre, and it is off-centre by conviction.
    axis: float
    #: Where the peak sits vertically as a proportion of the field.
    peak_height: float
    #: Proportion of the sheet the eye should read as inked. Measured by the
    #: proof tool rather than trusted.
    ink_target: float

    # --- production ----------------------------------------------------------
    #: The plates this personality spends on, in the order it spends them. The
    #: *first* is where the money goes and is the one the eye must land on.
    plates: tuple[str, ...]
    #: What the foil is for, in one phrase. A personality that cannot say what
    #: its foil is for should not have foil.
    foil_intent: str

    # --- typography ----------------------------------------------------------
    #: Faces by role, keyed on the script — never on a language.
    faces: dict[str, str]
    #: Tracking of the display face, in ems. Letterspaced small capitals are a
    #: letterpress signature and a modern-register mistake.
    display_tracking: float

    # --- material ------------------------------------------------------------
    paper: str
    ink: str
    #: The metal scheme key in `gilding.SCHEMES`, or "" where there is no metal.
    scheme: str

    @property
    def spends_on(self) -> str:
        return self.plates[0] if self.plates else "line"

    @property
    def has_foil(self) -> bool:
        return any(p.startswith("foil") for p in self.plates)


PERSONALITIES: Final[dict[str, Personality]] = {
    p.key: p for p in (
        Personality(
            key="collegiate",
            name="Collegiate",
            thesis="A document confident enough to leave four-fifths of itself "
                   "empty is making a claim about who issued it.",
            derivation=(
                "The old university diploma. Its striking property is "
                "subtraction: no border, no ornament, no colour. The authority "
                "is institutional rather than graphical, so the sheet carries "
                "one column of centred text, the arms small at the head, and a "
                "seal that is the only object on it. The security burden falls "
                "on the substrate and the seal — honest for a sheet held in one "
                "registry and verified by letter."
            ),
            authority="seal",
            enclosure="none",
            margin=0.24,
            axis=0.5,
            peak_height=0.42,
            ink_target=0.06,
            # No foil, no guilloché. The expense is the deboss of the seal and
            # the substrate, and there is nowhere for a reader's eye to go but
            # the words.
            plates=("emboss", "line", "substrate", "microtext", "numbering",
                    "variable"),
            foil_intent="",
            faces={"latin": "Source Serif 4", "arabic": "Amiri",
                   "ui": "Source Serif 4", "mono": "IBM Plex Mono"},
            display_tracking=0.02,
            paper="#FBF7EC",
            ink="#1A1A17",
            scheme="",
        ),
        Personality(
            key="chancery",
            name="Chancery",
            thesis="The arms are the document; the text is the administration "
                   "of it.",
            derivation=(
                "The state and diplomatic instrument. Authority sits in the "
                "arms, which take a third of the sheet and are the peak, and "
                "the text is subordinate and set as a block. One heavy rule "
                "rather than a frame. The guilloché sits behind the arms and "
                "nowhere else, so the security is where the authority is. "
                "Signature and counter-signature at the foot, because a state "
                "instrument is made by two offices."
            ),
            authority="arms",
            enclosure="rule",
            margin=0.15,
            axis=0.5,
            peak_height=0.30,
            ink_target=0.14,
            plates=("foil_primary", "guilloche", "line", "emboss", "process",
                    "microtext", "antipathy", "numbering", "variable"),
            foil_intent="the arms, and nothing else on the sheet",
            faces={"latin": "Fraunces", "arabic": "Amiri",
                   "ui": "Inter", "mono": "IBM Plex Mono"},
            display_tracking=0.06,
            paper="#F6F1E2",
            ink="#171C2A",
            scheme="imperial",
        ),
        Personality(
            key="court",
            name="Court",
            thesis="The frame is the document, and the text is what the frame "
                   "encloses.",
            derivation=(
                "The illuminated manuscript tradition. An illuminated border in "
                "registers of decreasing scale, a shamsa medallion at the head, "
                "and the text held in a cartouche floating in a field. "
                "Hierarchy is vertical and the composition reads inward rather "
                "than downward. The script leads and the Latin follows, because "
                "the sheet was composed for it."
            ),
            authority="title",
            enclosure="illuminated",
            margin=0.13,
            axis=0.5,
            peak_height=0.46,
            ink_target=0.30,
            plates=("foil_primary", "foil_second", "guilloche", "process",
                    "line", "emboss", "microtext", "antipathy", "uv",
                    "numbering", "variable"),
            foil_intent="the border registers and the shamsa, in two metals",
            faces={"latin": "Cormorant Garamond", "arabic": "Amiri",
                   "ui": "Inter", "mono": "IBM Plex Mono"},
            display_tracking=0.0,
            paper="#F7EFDA",
            ink="#231708",
            scheme="palace",
        ),
        Personality(
            key="intaglio",
            name="Intaglio",
            thesis="The lathe work is not behind the document. It is the "
                   "document.",
            derivation=(
                "The bank-note and security-printer tradition. The guilloché is "
                "in front, at full strength, and the type sits in reserved "
                "panels cut out of it. A vault oval where a portrait would be, "
                "a numeral treated as a denomination, microtext rails as "
                "visible structure rather than a hidden register, and a "
                "security thread. The expense is visibly in the plate rather "
                "than in the paper."
            ),
            authority="guilloche",
            enclosure="engine",
            margin=0.07,
            axis=0.5,
            peak_height=0.44,
            ink_target=0.42,
            plates=("guilloche", "line", "microtext", "antipathy",
                    "foil_primary", "uv", "process", "numbering", "variable"),
            foil_intent="the denomination numeral and the vault rim",
            faces={"latin": "Archivo", "arabic": "Cairo",
                   "ui": "Inter", "mono": "IBM Plex Mono"},
            display_tracking=0.10,
            paper="#F4F1E6",
            ink="#10233A",
            scheme="signature",
        ),
        Personality(
            key="letterpress",
            name="Letterpress",
            thesis="The value is in what a hand feels crossing the sheet, so "
                   "the money goes on dies rather than on metal.",
            derivation=(
                "The archival tradition. No foil at all, one ink, deep deboss, "
                "laid paper, an engraved crest, wide letterspaced small "
                "capitals. Restraint that is expensive rather than restraint "
                "that is cheap — and the difference is whether the deboss is "
                "deep enough to catch a shadow."
            ),
            authority="title",
            enclosure="rule",
            margin=0.19,
            axis=0.5,
            peak_height=0.40,
            ink_target=0.10,
            plates=("deboss", "emboss", "line", "substrate", "varnish",
                    "microtext", "numbering", "variable"),
            foil_intent="",
            faces={"latin": "Source Serif 4", "arabic": "Amiri",
                   "ui": "Source Serif 4", "mono": "IBM Plex Mono"},
            display_tracking=0.22,
            paper="#F2EDE0",
            ink="#2A2118",
            scheme="",
        ),
        Personality(
            key="meridian",
            name="Meridian",
            thesis="One foil element, so that the one is unmistakable.",
            derivation=(
                "The modern institutional register. An asymmetric grid, one "
                "enormous field of white, type as the only ornament, a single "
                "hairline, and exactly one foil element. Optical alignment "
                "carried to the point where it is felt rather than seen. This "
                "is what a contemporary research institution actually "
                "commissions, and it fails instantly if the spacing is "
                "approximate."
            ),
            authority="name",
            enclosure="none",
            margin=0.16,
            # The only off-centre axis in the set, and off-centre by conviction:
            # a modern composition that centres everything is a classical
            # composition with the ornament deleted.
            axis=0.38,
            peak_height=0.38,
            ink_target=0.08,
            plates=("foil_primary", "line", "substrate", "varnish",
                    "microtext", "numbering", "variable"),
            foil_intent="the institutional mark, once, at the head",
            faces={"latin": "Archivo", "arabic": "Cairo",
                   "ui": "Inter", "mono": "IBM Plex Mono"},
            display_tracking=-0.01,
            paper="#FAFAF7",
            ink="#14161A",
            scheme="signature",
        ),
    )
}


def personality_for(key: str) -> Personality:
    try:
        return PERSONALITIES[key]
    except KeyError:
        raise KeyError(
            f"No personality named {key!r}. The six are: "
            + ", ".join(sorted(PERSONALITIES))
        ) from None
