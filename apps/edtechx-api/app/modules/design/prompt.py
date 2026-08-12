"""Plain words to a design brief — and no route to a cheap one.

An institution types *"royal, midnight blue and gold, Arabic first, for our
PhD"* and gets a finished premium design. That is the whole surface. This file
is the vocabulary that makes it work, and it is deliberately not a model: it is
a table of terms a real registrar would type, each mapping to a patch on a
brief, resolved deterministically.

**Why a table rather than a model.** Three reasons, and the third is the one
that matters.

*It works offline.* No key, no network, no per-request cost, no latency. An
institution onboarding at 2am in Ikorodu gets the same studio as one onboarding
in a demo.

*It is repeatable.* The same words give the same brief, forever. A model gives
a different design on Tuesday, and an institution that approved a design on
Monday would not recognise it.

*It cannot fail downward.* Every term in this table lands on a premium
construction, because there are no others in it. A person can type "simple",
"clean", "minimal", "flat" or "modern" and what they get is the most *restrained
premium* design — laid paper, one metal, engraved rules, real typography — never
a flat one, because a flat one is not in the vocabulary and there is no code path
that reaches it. That is the product rule made structural rather than advisory:
**the cheap option does not exist to be chosen.**

An assistant is still welcome on top of this — `studio.AssistPort` — and it does
the same job better for unusual requests. But it is an accelerator, never a
dependency, and it hands back the same `Brief` this file does.

**What "premium only" means concretely.** Every brief this module can produce
carries: a real metal scheme with five roles; a ceremonial level of at least I,
which is an engraved metal rule, a real masthead and generous margins; the
document's own derived geometric family; and the full administrative
architecture. What it can *never* produce: a sheet with no metal, a web-flat
composition, a stock border, or a design at a level below what its purpose
deserves. `test_prompt.py` asserts all four for every reachable resolution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Final

from app.modules.design.ceremony import level_of
from app.modules.design.studio import SUGGESTIONS, Brief, review

#: Words a person writes round their design words. Reporting these as
#: "unrecognised" is noise that makes the real report — "letterpress was
#: ignored" — impossible to see.
_STOPWORDS: Final[frozenset[str]] = frozenset(
    "and the for our with that this from very please make design designs "
    "want need like look looks style styled certificate document sheet "
    "something more less all any some use using".split()
)

__all__ = [
    "PURPOSE_BASE",
    "VOCABULARY",
    "Resolution",
    "Term",
    "resolve",
    "vocabulary_for",
]


@dataclass(frozen=True, slots=True)
class Term:
    """One thing a person might type, and what it does to the brief."""

    key: str
    #: The words that select it. Matched whole, case-folded, so "gold" does not
    #: fire on "golden retriever" and "green" does not fire on "greenwich".
    words: tuple[str, ...]
    #: What it changes. A partial brief, applied in `kind` precedence order.
    patch: dict
    #: Which axis this term speaks to. One term per axis wins — the *last* one
    #: typed — so "midnight blue, actually crimson" does what a person means.
    kind: str
    note: str


def _t(key: str, words: str, kind: str, note: str, **patch) -> Term:
    return Term(key=key, words=tuple(words.split("|")), patch=patch,
                kind=kind, note=note)


#: The vocabulary. Every entry lands on a premium construction; there is nothing
#: in this table that produces a flat, stock or web-styled sheet, which is what
#: makes "premium only" a property of the code rather than a promise.
VOCABULARY: Final[tuple[Term, ...]] = (
    # --- character: the overall world the sheet belongs to -------------------
    _t("royal", "royal|regal|palace|majestic|grand", "character",
       "Ivory, navy and royal gold; a doorcase frame with mass at the corners.",
       ground="engine-turn", ground_strength=0.055, scheme="palace",
       ground_colour="#F7F2E6", ink="#101826", accent="#14294C",
       second_metal=True),
    _t("imperial", "imperial|islamic|geometric|girih|khatam", "character",
       "A midnight strapwork border with an ivory field cut into it.",
       ground="girih-diaper", ground_strength=0.055, scheme="imperial",
       ground_colour="#F5F0E2", ink="#0E1B33", accent="#0E1B33",
       second_metal=True),
    _t("crimson", "crimson|burgundy|maroon|wine|red", "character",
       "Crimson mass, gold architecture, one bright ceremonial centre.",
       ground="damask", ground_strength=0.060, scheme="crimson",
       ground_colour="#F7F1E4", ink="#2A0E18", accent="#5A1226",
       second_metal=True),
    _t("heritage", "heritage|manuscript|illuminated|classical|antique|old", "character",
       "Parchment, warm gold and an illuminated border architecture.",
       ground="arabesque-scroll", ground_strength=0.060, scheme="imperial",
       ground_colour="#EFE6CE", ink="#2A2214", accent="#6B4E1E",
       second_metal=True),
    _t("emerald", "green|emerald|arabian|gulf", "character",
       "Deep green, ivory and deep gold — the Arabian royal register.",
       ground="ogee-lattice", ground_strength=0.055, scheme="imperial",
       ground_colour="#F7F3E7", ink="#0F2620", accent="#123A2E",
       second_metal=True),
    _t("midnight", "midnight blue|midnight|royal blue|navy|deep blue|dark blue|sapphire",
       "character",
       "A midnight ground with gold behaving as light rather than pigment.",
       ground="engine-turn", ground_strength=0.050, scheme="signature",
       ground_colour="#F7F2E6", ink="#0A101C", accent="#132038",
       second_metal=True),
    # "Simple" does not reach a simple design. It reaches the most restrained
    # *premium* one: laid paper, one metal, engraved rules, and the typography
    # carrying the sheet. There is no flatter option in this table.
    _t("executive", "executive|simple|clean|minimal|modern|plain|professional|"
       "corporate|contemporary", "character",
       "The most restrained premium register: laid paper, one metal register, "
       "and the typography doing the work. Not a flat design — there is none.",
       ground="laid", ground_strength=0.040, scheme="signature",
       ground_colour="#F8F5EC", ink="#14202E", accent="#1E3A5C",
       second_metal=False),
    _t("scholarly", "scholarly|scholar|ijaza|ijazah|quran|qur'an|tajweed|"
       "islamic studies", "character",
       "A scholarly register set entirely right-to-left, on parchment.",
       ground="arabesque-scroll", ground_strength=0.060, scheme="imperial",
       ground_colour="#EFE6CE", ink="#2A2214", accent="#6B4E1E",
       language="arabic-only", second_metal=True),

    # --- metal ---------------------------------------------------------------
    _t("gold-royal", "gold|golden|royal gold", "metal",
       "Royal gold carries the architecture.", scheme="palace"),
    _t("gold-antique", "antique gold|aged gold|bronze", "metal",
       "Antique gold: browner in the face than in the core.", scheme="imperial"),
    _t("gold-champagne", "champagne|pale gold|light gold", "metal",
       "Champagne: metal without brass.", scheme="imperial"),
    _t("silver", "silver|platinum|steel", "metal",
       "Royal gold against silver — two metals that are not two golds.",
       scheme="signature", second_metal=True),
    _t("copper", "copper|rose gold|warm metal", "metal",
       "Copper as the warm counter-metal.", scheme="crimson"),

    # --- ground --------------------------------------------------------------
    _t("g-guilloche", "guilloche|guilloché|engine turned|banknote|security print",
       "ground", "Engine turning: overlapping closed lathe roses.",
       ground="engine-turn", ground_strength=0.055),
    _t("g-damask", "damask|brocade|textile|fabric", "ground",
       "The pointed-oval diaper of a court hanging.",
       ground="damask", ground_strength=0.060),
    _t("g-laid", "laid|watermark|mould made|paper", "ground",
       "Laid lines and chain lines — mould-made paper against the light.",
       ground="laid", ground_strength=0.045),
    _t("g-vellum", "vellum|parchment|skin", "ground",
       "Irregular short fibres; a skin rather than a sheet.",
       ground="vellum", ground_strength=0.055),
    _t("g-marble", "marble|marbled|endpaper", "ground",
       "Combed veins as line rather than wash.",
       ground="marbled", ground_strength=0.070),
    _t("g-arabesque", "arabesque|scroll|vine|floral", "ground",
       "Counter-curved stems with leaf terminals.",
       ground="arabesque-scroll", ground_strength=0.060),
    _t("g-star", "stars|starfield|powdered", "ground",
       "The powdered ground of an illuminated page.",
       ground="starfield", ground_strength=0.070),

    # --- language ------------------------------------------------------------
    _t("l-arabic-only", "arabic only|only arabic|arabic alone|all arabic",
       "language", "The whole sheet set right-to-left.",
       language="arabic-only"),
    _t("l-latin-only", "english only|only english|latin only|no arabic",
       "language", "Complete in one script, and not missing anything.",
       language="latin-only"),
    _t("l-arabic-first", "arabic first|arabic primary|arabic leading|"
       "arabic dominant", "language",
       "Arabic carries the ceremony; English carries the explanation.",
       language="arabic-primary"),
    _t("l-latin-first", "english first|english primary|english leading|"
       "latin primary", "language",
       "English leads; the Arabic is the institution's own identity.",
       language="latin-primary"),
    _t("l-peer", "bilingual|side by side|both languages|two languages|"
       "arabic and english|english and arabic", "language",
       "Optically equal, flanking the institutional mark.", language="peer"),

    # --- level ---------------------------------------------------------------
    _t("lv4", "phd|doctorate|doctoral|honorary|fellowship|highest|flagship",
       "level", "Level IV: the whole vocabulary is available.", level=4),
    _t("lv3", "graduation|degree|bachelor|master|masters|distinction|award|"
       "ceremonial", "level",
       "Level III: richly ornamented, with a ceremonial centre.", level=3),
    _t("lv2", "diploma|certificate|professional|transcript|qualification",
       "level", "Level II: clearly luxurious.", level=2),
    _t("lv1", "report card|statement of results|letter|enrolment|attendance|"
       "completion|participation", "level",
       "Level I: elegant, and not apologetic about it.", level=1,
       ground_strength=0.0),

    # --- geometry ------------------------------------------------------------
    _t("o8", "eight fold|eight-fold|octagonal|8 fold", "geometry",
       "An eight-fold family — the khatam.", motif_order=8),
    _t("o10", "ten fold|ten-fold|decagonal|10 fold", "geometry",
       "A ten-fold family — decagonal girih.", motif_order=10),
    _t("o12", "twelve fold|twelve-fold|dodecagonal|12 fold", "geometry",
       "A twelve-fold family.", motif_order=12),
)

#: Precedence. A character term sets the whole world; the axes after it refine
#: that world. So "royal, but silver" gives the royal architecture with the
#: two-metal scheme, which is what a person means by it.
_ORDER: Final[tuple[str, ...]] = (
    "character", "ground", "metal", "language", "level", "geometry",
)

#: Where a resolution starts when the words say nothing about the level. Keyed
#: on the document's purpose, because a doctorate and a report card are not the
#: same object and neither is a downgrade of the other.
PURPOSE_BASE: Final[dict[str, str]] = {
    "doctoral": "imperial-islamic",
    "honorary": "royal-palace",
    "certificate": "crimson-imperial",
    "transcript": "executive",
    "document": "executive",
    "report_card": "completion",
}


@dataclass(frozen=True, slots=True)
class Resolution:
    """What a prompt produced, and why — so a person can disagree with it."""

    brief: Brief
    #: The terms that fired, in the order they were applied.
    matched: tuple[Term, ...] = field(default_factory=tuple)
    #: Words the vocabulary did not recognise. Reported rather than swallowed:
    #: an institution that typed "letterpress" should be told it was ignored,
    #: not left to wonder why the design did not change.
    unmatched: tuple[str, ...] = field(default_factory=tuple)

    @property
    def explanation(self) -> str:
        """One line per decision, for the studio to show beside the preview."""
        if not self.matched:
            return "No design words recognised — the purpose's own premium " \
                   "starting point was used unchanged."
        return "\n".join(f"· {term.note}" for term in self.matched)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold().replace("’", "'")).strip()


def vocabulary_for(kind: str) -> tuple[Term, ...]:
    """Every term on one axis — for a studio that wants to show chips."""
    return tuple(term for term in VOCABULARY if term.kind == kind)


def resolve(text: str, *, purpose: str = "document") -> Resolution:
    """Turn plain words into a reviewed premium brief.

    Never raises for unrecognised input and never returns something cheap: an
    empty prompt gives the purpose's own premium starting point, and unknown
    words are reported rather than acted on. The last term on each axis wins,
    so "midnight blue — actually crimson" does what a person means.
    """
    words = _normalise(text)
    base_key = PURPOSE_BASE.get(purpose, "executive")
    brief = SUGGESTIONS[base_key]

    # Keyed on where the term appears in *the text*, not on where it appears in
    # this file's table. Iterating the vocabulary and overwriting meant the last
    # row in the table won rather than the last word typed, so "midnight blue,
    # actually crimson" produced midnight — the opposite of what it says.
    chosen: dict[str, tuple[int, Term]] = {}
    hit_spans: list[tuple[int, int]] = []
    for term in VOCABULARY:
        for phrase in term.words:
            for match in re.finditer(rf"(?<!\w){re.escape(phrase)}(?!\w)", words):
                hit_spans.append(match.span())
                seen = chosen.get(term.kind)
                if seen is None or match.start() > seen[0]:
                    chosen[term.kind] = (match.start(), term)

    applied: list[Term] = []
    for kind in _ORDER:
        found = chosen.get(kind)
        if found is None:
            continue
        term = found[1]
        brief = replace(brief, **term.patch)
        applied.append(term)

    # A Level I sheet permits no ink behind the words, whatever ground a
    # character term chose. Resolving that here rather than letting the gate
    # refuse it is the difference between a studio that works and one that
    # argues.
    # No level word: the *purpose* decides, not the character term's own
    # level. A certificate asked for in crimson is a Level III document in
    # crimson, not a doctorate in crimson.
    if "level" not in chosen:
        class _Purpose:
            custom = None

        _Purpose.purpose = purpose
        brief = replace(brief, level=level_of(_Purpose).level)
        if brief.level < 3:
            brief = replace(brief, second_metal=False)

    if brief.level == 1:
        brief = replace(brief, ground_strength=0.0, second_metal=False)
    elif brief.level == 2 and brief.second_metal:
        brief = replace(brief, second_metal=False)

    # Which characters a term consumed, so a word inside a matched phrase is
    # not also reported as unrecognised.
    covered = bytearray(len(words))
    for start, end in hit_spans:
        covered[start:end] = b"\x01" * (end - start)
    leftovers = [
        found.group()
        for found in re.finditer(r"[a-z']{3,}", words)
        if not any(covered[found.start():found.end()])
        and found.group() not in _STOPWORDS
    ]

    return Resolution(brief=review(brief), matched=tuple(applied),
                      unmatched=tuple(dict.fromkeys(leftovers)))
