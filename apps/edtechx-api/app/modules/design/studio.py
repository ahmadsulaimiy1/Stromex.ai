"""The institution's design studio: a brief, not a canvas.

An institution onboarding to EdirasX should be able to sit down and design its
own document family — choose a ground, choose a metal scheme, place its arms in
the heraldic bays, upload its device and get a struck golden seal round it, and
ask an assistant for suggestions when it does not know what it wants. This file
is what that studio actually manipulates.

**The studio edits a `Brief`, and the engine renders it.** Nothing in the studio
draws. A brief is twelve or so values — a ground key, a gilding scheme, a
ceremonial level, a language arrangement, a motif order, references to the
institution's own supplied assets — and the deterministic plate engine turns
that into artwork. That separation is the whole design:

* a brief is small enough to store, diff, review and approve;
* two renders of one brief are the same plate, forever;
* the artwork stays vector, stays press-legal, and stays exact at 2400 DPI;
* and an institution cannot, by any sequence of studio actions, produce a sheet
  that violates the press rules, because the studio never touches the artwork.

**What an assistant may and may not do.** This is the important part and it is
enforced rather than advised.

An assistant — Claude, GPT, anything — may propose a **brief**. "A deep green
ground with antique gold, twelve-fold geometry, Arabic-primary, ceremonial
level III" is a design opinion, it is checkable, and a human approves it before
anything is issued. `AssistPort` is that contract, and it returns a `Brief` or
it fails.

An assistant may **not** produce artwork that lands on a certificate. Not the
ground, not the frame, not the seal, and above all not the security layer. Three
reasons, none of them aesthetic:

*It would be a raster.* A generated image is pixels. Over a 297mm sheet a
1024-pixel image is 87 DPI, and this codebase has already measured what that
costs — see `grounds.py`. Everything on an EdirasX plate is constructed so it
has no resolution; dropping a generated bitmap into it throws that away at the
one place it matters.

*It would be unaccountable.* A certificate is a legal instrument. Every mark on
it needs a known origin, and "a model produced it" is not a provenance an
embassy can act on.

*It would be unrepeatable.* Two runs of a generative model are not the same
plate. A reissued document must be byte-identical to the original or the whole
verification argument collapses.

**An uploaded logo is mounted, never generated.** An institution's device is a
supplied asset with a provenance record, and the studio *mounts* it into a seal
that EdirasX constructs around it — turned field, engraved rim, legend ring
carrying the document's serial, blind-embossed device. The gold is EdirasX's and
it is constructed; the device in the middle is the institution's and it is
theirs. Nothing here invents an institution's mark, and nothing here makes a
seal official: an uploaded device becomes a usable seal only by going through
`documents.authority`, which already governs approval, validity and revocation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Final, Protocol

from app.modules.design.ceremony import LEVELS, Budget, budget_for
from app.modules.design.gilding import SCHEMES, Scheme, scheme_for
from app.modules.design.grounds import GROUNDS, Ground, ground_for
from app.modules.design.language import (
    ARCHITECTURES,
    Architecture,
    architecture_for,
)
from app.modules.design.signature import ORDERS, Motif, motif_for

__all__ = [
    "SUGGESTIONS",
    "AssistPort",
    "AssistUnavailable",
    "Brief",
    "BriefRejected",
    "review",
]


class BriefRejected(ValueError):
    """A brief that would produce an unprintable or dishonest sheet.

    Raised with every reason at once rather than the first, because an
    institution correcting a design should not have to discover its mistakes one
    render at a time.
    """

    def __init__(self, reasons: list[str]) -> None:
        self.reasons = reasons
        super().__init__("; ".join(reasons))


class AssistUnavailable(RuntimeError):
    """No assistant is configured, or the one configured did not answer.

    A first-class outcome, not an error to swallow: the studio works without an
    assistant, and a design that cannot be suggested can always be chosen.
    """


@dataclass(frozen=True, slots=True)
class Brief:
    """One institution's document design, as data.

    Small on purpose. Everything here is a *choice* — the constructions it
    selects live in the design package and cannot be edited from the studio,
    which is what stops a well-meaning administrator producing a sheet with
    0.04mm hairlines on it.
    """

    #: Which ground the sheet is printed on. A key into `grounds.GROUNDS`.
    ground: str
    #: How dark that ground is allowed to be. Held separately from the ground
    #: because the same construction is a substrate at 0.03 and wallpaper at 0.4.
    ground_strength: float
    #: The metal roles. A key into `gilding.SCHEMES`.
    scheme: str
    #: Ceremonial level, I–IV. Governs how much of the vocabulary is spendable.
    level: int
    #: Which scripts, where, at what weight. A key into `language.ARCHITECTURES`.
    language: str
    #: Structural colours. Three and only three; the metals are separate.
    ground_colour: str
    ink: str
    accent: str
    #: The institution's own supplied assets, by reference into the asset
    #: register — never inline, never generated. An empty reference means the
    #: bay is drawn empty and captioned, which is honest; a placeholder emblem
    #: would not be.
    device_ref: str = ""
    arms_left_ref: str = ""
    arms_right_ref: str = ""
    #: Whether this design buys a *second foil pass*. Explicit because it is a
    #: real cost at the printer, not a styling flag. Every gilding scheme names
    #: five metal roles; what this decides is whether the plate is separated
    #: onto one foil or two. The first version of the studio gate inferred it
    #: from the scheme and consequently refused every Level I and II design,
    #: because every scheme names more than one metal.
    second_metal: bool = False
    #: Override the derived geometric family's order. Left at zero the motif is
    #: derived from the institution's name, which is what makes it an identity.
    motif_order: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)

    # --- resolved views, so a caller never re-looks-up ------------------------

    @property
    def budget(self) -> Budget:
        return budget_for(self.level)

    @property
    def metals(self) -> Scheme:
        return scheme_for(self.scheme)

    @property
    def field(self) -> Ground:
        return ground_for(self.ground)

    @property
    def arrangement(self) -> Architecture:
        return architecture_for(self.language)

    def motif(self, *, institution: str, family: str) -> Motif:
        derived = motif_for(institution=institution, family=family)
        if self.motif_order and self.motif_order != derived.order:
            from app.modules.design.signature import density_for, star_ratio

            order = self.motif_order
            density = density_for(order)
            return replace(derived, order=order, density=density,
                           ratio=star_ratio(order, density))
        return derived


#: The ground strength above which a field stops being a substrate. Taken from
#: the ground library's own guidance, doubled: the library's `suggested` value is
#: where a ground belongs, and twice that is where it starts to fight the words.
_GROUND_CEILING: Final[float] = 2.0


def review(brief: Brief) -> Brief:
    """Check a brief and return it, or raise with every reason.

    This is the studio's only gate and it is deliberately narrow. It does not
    have opinions about taste — an institution may choose a ground this author
    would not — and it has no opinions it cannot justify in one sentence to the
    person whose design is being refused.
    """
    reasons: list[str] = []

    if brief.ground not in GROUNDS:
        reasons.append(
            f"{brief.ground!r} is not a ground. One of: "
            + ", ".join(sorted(GROUNDS))
        )
    if brief.scheme not in SCHEMES:
        reasons.append(
            f"{brief.scheme!r} is not a gilding scheme. One of: "
            + ", ".join(sorted(SCHEMES))
        )
    if brief.language not in ARCHITECTURES:
        reasons.append(
            f"{brief.language!r} is not a language arrangement. One of: "
            + ", ".join(sorted(ARCHITECTURES))
        )
    if brief.level not in {b.level for b in LEVELS}:
        reasons.append(
            f"{brief.level!r} is not a ceremonial level; levels are 1–4."
        )
    if brief.motif_order and brief.motif_order not in ORDERS:
        reasons.append(
            f"A {brief.motif_order}-fold family does not tile; EdirasX supports "
            + ", ".join(f"{n}-fold" for n in ORDERS)
            + ". A frame built from an order that does not tile has to fudge "
            "its corners, and that is visible at close range."
        )

    if brief.ground in GROUNDS:
        ceiling = GROUNDS[brief.ground].suggested * _GROUND_CEILING
        if brief.ground_strength > ceiling:
            reasons.append(
                f"A {GROUNDS[brief.ground].name.lower()} ground at "
                f"{brief.ground_strength:.3f} is wallpaper, not a substrate. "
                f"The ceiling for this ground is {ceiling:.3f}; it belongs "
                f"around {GROUNDS[brief.ground].suggested:.3f}."
            )
        if brief.ground_strength < 0:
            reasons.append("A ground strength below zero is not a design.")

    if brief.level in {b.level for b in LEVELS}:
        budget = budget_for(brief.level)
        if brief.ground_strength > 0 and budget.content_ink <= 0:
            reasons.append(
                "Level I permits no ink behind the words. A statement of "
                "results that arrives on a worked ground is a statement "
                "nobody trusts — raise the level or drop the ground."
            )
        if brief.second_metal and not budget.second_metal:
            reasons.append(
                f"Level {brief.level} buys one foil pass. A second foil is a "
                "second pass on press and a second die, and it is granted at "
                "level III — raise the level or drop the second metal."
            )

    # The ground must differ from what is printed on it; ink and accent may
    # legitimately coincide. This gate originally demanded three distinct
    # colours and immediately refused one of EdirasX's own flagship plates,
    # where the text and the border mass are deliberately one midnight. A
    # two-colour scheme is a decision, not a missing register — what is never a
    # decision is setting type in the colour of the paper.
    if brief.ink == brief.ground_colour:
        reasons.append(
            "The ink and the ground are the same colour, so nothing printed on "
            "this sheet would be visible."
        )
    if brief.accent == brief.ground_colour:
        reasons.append(
            "The accent and the ground are the same colour, so the accent "
            "would not appear."
        )

    if reasons:
        raise BriefRejected(reasons)
    return brief


#: Starting points an institution can pick from before it knows what it wants.
#: Not templates — briefs. Each renders through the same engine as everything
#: else and each can be edited in every field.
SUGGESTIONS: Final[dict[str, Brief]] = {
    "royal-palace": Brief(second_metal=True,
        ground="engine-turn", ground_strength=0.055, scheme="palace", level=4,
        language="latin-only", ground_colour="#F7F2E6", ink="#101826",
        accent="#14294C",
        notes=("Ivory, navy and royal gold. A doorcase: mass at the corners, a "
               "stepped architrave, a crest breaking the line.",),
    ),
    "imperial-islamic": Brief(second_metal=True,
        ground="girih-diaper", ground_strength=0.055, scheme="imperial",
        level=4, language="peer", ground_colour="#F5F0E2", ink="#0E1B33",
        accent="#0E1B33",
        notes=("A midnight strapwork border with an ivory field cut into it. "
               "Arabic and Latin as optical peers.",),
    ),
    "crimson-imperial": Brief(second_metal=True,
        ground="damask", ground_strength=0.060, scheme="crimson", level=4,
        language="latin-primary", ground_colour="#F7F1E4", ink="#2A0E18",
        accent="#5A1226",
        notes=("Crimson mass, gold architecture, one bright ceremonial centre.",),
    ),
    "scholarly-ijaza": Brief(second_metal=True,
        ground="arabesque-scroll", ground_strength=0.060, scheme="imperial",
        level=3, language="arabic-only", ground_colour="#EFE6CE",
        ink="#2A2214", accent="#6B4E1E",
        notes=("Parchment and warm gold, set entirely right-to-left. A "
               "scholarly ijāzah is not a bilingual sheet with the English "
               "removed.",),
    ),
    "executive": Brief(
        ground="laid", ground_strength=0.040, scheme="signature", level=2,
        language="latin-only", ground_colour="#F8F5EC", ink="#14202E",
        accent="#1E3A5C",
        notes=("A professional certificate with no overt ornament: laid paper, "
               "one metal register, and the typography doing the work.",),
    ),
    "completion": Brief(
        ground="laid", ground_strength=0.0, scheme="palace", level=1,
        language="latin-only", ground_colour="#F8F5EC", ink="#1A1D24",
        accent="#3A4A64",
        notes=("Level I. One engraved metal rule, a real masthead, a generous "
               "margin, and nothing behind the words.",),
    ),
}


class AssistPort(Protocol):
    """What an assistant is allowed to do: propose a brief.

    Deliberately provider-agnostic — Claude, GPT, a rules engine or nothing at
    all satisfies this, and the studio works when it is unimplemented. The
    return type is the enforcement: an implementation *cannot* hand back
    artwork, because the signature has nowhere to put it.

    An implementation should:

      * turn the institution's words into a `Brief` and nothing else;
      * pass it through `review()` before returning it, so a suggestion that
        cannot be printed never reaches a human as though it could;
      * raise `AssistUnavailable` rather than inventing a brief when it has no
        answer, because a wrong suggestion costs more than an absent one.

    It must never be given the credential layer. Identifiers, the verification
    panel, the barcode and the seal's authority are not design decisions and are
    not in a brief; they come from `documents.authority` and
    `design.credential`, and an assistant has no business proposing them.
    """

    def propose(self, *, institution: str, purpose: str,
                wishes: str) -> Brief:  # pragma: no cover - a protocol
        """Return a reviewed `Brief`, or raise `AssistUnavailable`."""
        ...
