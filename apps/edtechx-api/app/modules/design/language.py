"""Language architecture: which scripts appear, where, and at what weight.

**Arabic plus English is not the EdirasX formula.** It was becoming one, and a
compulsory bilingual layout is exactly as templated as a compulsory ornament. An
international transcript is English. A Qur'an ijāzah is Arabic. A sovereign
award may set Arabic as the ceremonial voice and English as the legal one, or
the reverse, or run them as peers, or put them in different zones of the sheet.
All of those are correct documents, and none of them is a special case here.

So the language arrangement is a **design decision recorded on the template**,
resolved by this module, and every arrangement goes through the same code path.
There is no `if arabic:` anywhere below, and there must never be one: the moment
one script is a branch and another is the default, the system has an opinion it
was not asked for.

**Three things this module knows that a translation table does not.**

*Optical size is not nominal size.* Naskh set at the same nominal size as a
Latin capital reads smaller — its cap-equivalent sits lower in the em and its
counters are finer. So each script carries an optical multiplier and a line
height, and a "peer" lockup means *optically* equal, which is the only kind of
equal a reader perceives.

*Direction is a property of the run, not of the page.* A sheet can carry an RTL
masthead over an LTR body. Each rendered run declares its own direction and the
composition places the runs; nothing infers a page direction from a script.

*Absence is ordinary.* An institution that has not supplied an Arabic name is
not an error and not a gap to fill with a placeholder. The arrangement drops
that script for that phrase, the remaining runs re-balance, and the composition
does not acquire an empty element. A missing translation must never leave a
ghost — an empty rule, a stray bullet, a gap where something used to be.

**What this module does not do.** It does not translate, transliterate, or
choose a language. It arranges what the institution supplied. If a phrase has
one script, it renders one script; the design is expected to be good either way,
and that is what makes the arrangement a design decision rather than a fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

__all__ = [
    "ARCHITECTURES",
    "SCRIPTS",
    "Architecture",
    "Phrase",
    "Run",
    "Script",
    "architecture_for",
    "script_for",
]


@dataclass(frozen=True, slots=True)
class Script:
    """One writing system, with the facts a composition needs about it."""

    key: str
    name: str
    #: `ltr` or `rtl`. A property of the run.
    direction: str
    #: The document type role this script is set in — see `typeface.ROLES`.
    face: str
    #: Nominal-size multiplier that makes this script sit optically level with
    #: Latin at 1.0. Amiri needs ~1.18 against a Latin capital; Latin lowercase
    #: needs no correction against itself, which is why Latin is the datum.
    optical: float
    #: Line height. Arabic needs more leading than Latin at the same size
    #: because its ascenders and descenders are deeper and its marks sit above.
    leading: float
    #: Whether this script is normally set in capitals. Arabic has no case, so
    #: an arrangement that uppercases everything silently does nothing to it and
    #: the two runs stop matching.
    has_case: bool


SCRIPTS: Final[dict[str, Script]] = {
    "latin": Script("latin", "Latin", "ltr", "display", 1.00, 1.12, True),
    "arabic": Script("arabic", "Arabic", "rtl", "arabic", 1.18, 1.50, False),
    "arabic-modern": Script("arabic-modern", "Arabic (modern)", "rtl",
                            "arabic-modern", 1.10, 1.45, False),
}


@dataclass(frozen=True, slots=True)
class Phrase:
    """One piece of content, in whatever scripts the institution supplied.

    A mapping, not a pair. A phrase with one script is as ordinary as a phrase
    with three, and nothing here treats a single-script phrase as incomplete.
    """

    by_script: dict[str, str] = field(default_factory=dict)

    def get(self, script: str) -> str | None:
        value = self.by_script.get(script)
        return value.strip() if value and value.strip() else None

    def scripts(self, order: tuple[str, ...]) -> tuple[str, ...]:
        """The scripts actually present, in the arrangement's order."""
        return tuple(key for key in order if self.get(key))

    @property
    def is_empty(self) -> bool:
        return not any(self.get(key) for key in self.by_script)


@dataclass(frozen=True, slots=True)
class Run:
    """One script's text, resolved and ready to set."""

    script: Script
    text: str
    #: Size relative to the slot's base size, after the optical correction.
    scale: float
    #: `lead` is the run a reader meets first; the rest are subordinate. In a
    #: peer arrangement every run is a lead, which is what peer means.
    lead: bool

    @property
    def direction(self) -> str:
        return self.script.direction


@dataclass(frozen=True, slots=True)
class Architecture:
    """How a document arranges the scripts it carries.

    `mode` is what a *composition* does with the resolved runs, and the plate
    reads it rather than guessing from the script list:

        ``solo``        one run. The design must be complete without a second.
        ``stacked``     runs on successive lines, the lead dominant.
        ``peer``        runs side by side, optically equal, sharing an anchor.
        ``zoned``       runs placed in different zones of the sheet — a
                        ceremonial masthead in one script, the legal body in
                        another. The plate decides which zone; this names the
                        intent.
        ``integrated``  one run becomes part of the ornament: a calligraphic
                        band, a cartouche, a border. The plate must know this,
                        because integrated text is not laid out — it is drawn.
    """

    key: str
    name: str
    #: Scripts in order of precedence. Length 1 is a solo arrangement and is not
    #: a degenerate case of anything.
    order: tuple[str, ...]
    mode: str
    #: Relative size per script, before the optical correction. The lead is 1.0
    #: by convention; a subordinate at 0.55 is subordinate by design, not by
    #: accident of the face's metrics.
    weight: dict[str, float]
    description: str = ""

    def resolve(self, phrase: Phrase) -> tuple[Run, ...]:
        """The runs to set for one phrase, in order.

        Absence is handled here, once, for every arrangement: a script the
        phrase does not carry is dropped and the remaining runs are renormalised
        so the lead is still the lead. That is why a plate never needs to ask
        whether a translation exists.
        """
        present = phrase.scripts(self.order)
        if not present:
            return ()
        top = max(self.weight.get(key, 1.0) for key in present)
        runs: list[Run] = []
        for index, key in enumerate(present):
            script = SCRIPTS[key]
            relative = self.weight.get(key, 1.0) / top
            runs.append(Run(
                script=script,
                text=phrase.get(key) or "",
                scale=relative * script.optical,
                lead=(self.mode == "peer") or index == 0,
            ))
        return tuple(runs)

    @property
    def is_multiscript(self) -> bool:
        return len(self.order) > 1


#: The arrangements. Each is a real document that exists in the world, and the
#: renderer treats them identically — there is no default and no exception.
ARCHITECTURES: Final[dict[str, Architecture]] = {
    "latin-only": Architecture(
        key="latin-only", name="English only", order=("latin",), mode="solo",
        weight={"latin": 1.0},
        description=(
            "An international transcript, a professional certificate, a "
            "corporate award. Complete in one script and not missing anything."
        ),
    ),
    "arabic-only": Architecture(
        key="arabic-only", name="Arabic only", order=("arabic",), mode="solo",
        weight={"arabic": 1.0},
        description=(
            "A Qur'an ijāzah, an Arabic scholarly award, an Arabic "
            "institutional certificate. The whole sheet is set right-to-left, "
            "including the execution band and the verification register."
        ),
    ),
    "arabic-primary": Architecture(
        key="arabic-primary", name="Arabic primary, English secondary",
        order=("arabic", "latin"), mode="stacked",
        weight={"arabic": 1.0, "latin": 0.52},
        description=(
            "Arabic carries the ceremony; English carries the explanation. The "
            "first thing read on the sheet is Arabic."
        ),
    ),
    "latin-primary": Architecture(
        key="latin-primary", name="English primary, Arabic secondary",
        order=("latin", "arabic"), mode="stacked",
        weight={"latin": 1.0, "arabic": 0.50},
        description=(
            "The reverse. Common where the awarding body is international and "
            "the Arabic is the institution's own identity."
        ),
    ),
    "peer": Architecture(
        key="peer", name="Side by side, optically equal",
        order=("latin", "arabic"), mode="peer",
        weight={"latin": 1.0, "arabic": 1.0},
        description=(
            "Neither subordinate. The two runs flank a shared anchor — an "
            "institutional mark, a rule, a medallion — and removing either "
            "destroys the lockup, which is the test of whether a bilingual "
            "design is bilingual."
        ),
    ),
    "zoned": Architecture(
        key="zoned", name="Separate zones",
        order=("arabic", "latin"), mode="zoned",
        weight={"arabic": 1.0, "latin": 0.72},
        description=(
            "Arabic holds the ceremonial masthead; English holds the legal and "
            "academic body. Not a translation of each other, and the sheet "
            "reads as one document in two registers."
        ),
    ),
    "integrated": Architecture(
        key="integrated", name="Calligraphic integration",
        order=("arabic", "latin"), mode="integrated",
        weight={"arabic": 1.0, "latin": 0.58},
        description=(
            "The Arabic becomes part of the ornament — a band, a cartouche, a "
            "border — rather than a line of type. A plate must opt into this: "
            "integrated text is drawn, not laid out, and cannot reflow."
        ),
    ),
    "trilingual": Architecture(
        key="trilingual", name="Three runs",
        order=("arabic", "latin", "arabic-modern"), mode="stacked",
        weight={"arabic": 1.0, "latin": 0.66, "arabic-modern": 0.52},
        description=(
            "Where a jurisdiction requires a third run. Included so three is a "
            "supported number rather than a thing that breaks the layout — an "
            "institution supplying only two gets two, and the composition "
            "re-balances rather than reserving a gap.\n\n"
            "**A stated limitation.** This module models *scripts*, not "
            "languages. An English / French / Arabic document is three "
            "languages in two scripts, and there is currently no way to express "
            "two Latin runs that must not be collapsed. Naming this "
            "'trilingual' would overstate what it does, so it is named for what "
            "it is. Adding a language axis is a real change, not a rename, and "
            "it is not pretended here."
        ),
    ),
}


def script_for(key: str) -> Script:
    if key not in SCRIPTS:
        raise ValueError(
            f"{key!r} is not a script. One of: " + ", ".join(sorted(SCRIPTS))
        )
    return SCRIPTS[key]


def architecture_for(key: str) -> Architecture:
    if key not in ARCHITECTURES:
        raise ValueError(
            f"{key!r} is not a language architecture. One of: "
            + ", ".join(sorted(ARCHITECTURES))
        )
    return ARCHITECTURES[key]
