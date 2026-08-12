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

import pathlib
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
def _load_vocabulary() -> tuple[Term, ...]:
    """The vocabulary, read from data rather than compiled into the product.

    It used to be a tuple of literals here, and that was wrong for a reason a
    test caught rather than a reviewer: the level terms named *one* credential
    ladder — doctorate, masters, bachelor, diploma — inside product code. A
    French institution says licence, a German one Diplom, an Islamic seminary
    says ijāzah, and none of them should need EdirasX redeployed to be
    understood. A synonym table is content.

    So it is a data file, shipped as a default and replaceable per deployment.
    The *structure* — that a term names an axis, that the last one typed wins,
    that every entry lands on a premium construction — stays here, because that
    is architecture.
    """
    import tomllib

    path = pathlib.Path(__file__).resolve().parents[2] / "data" / _VOCABULARY_FILE
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return tuple(
        Term(key=entry["key"], words=tuple(entry["words"]),
             patch=dict(entry.get("patch", {})), kind=entry["kind"],
             note=entry["note"])
        for entry in raw["term"]
    )


#: The default vocabulary file. Every entry in it lands on a premium
#: construction; there is nothing in the table that produces a flat, stock or
#: web-styled sheet, which is what makes "premium only" a property of the
#: system rather than a promise. Replacing the file replaces the words, never
#: the constructions they reach.
_VOCABULARY_FILE: Final[str] = "prompt-vocabulary.toml"

VOCABULARY: Final[tuple[Term, ...]] = _load_vocabulary()

#: Precedence. A character term sets the whole world; the axes after it refine
#: that world. So "royal, but silver" gives the royal architecture with the
#: two-metal scheme, which is what a person means by it.
#:
#: This stays in the product where the vocabulary does not: which words mean
#: "royal" is content, but the fact that character is decided before metal is
#: how the resolver works.
_ORDER: Final[tuple[str, ...]] = (
    "character", "ground", "metal", "language", "level", "geometry",
)


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
