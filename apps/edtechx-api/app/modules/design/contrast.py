"""Colour arithmetic, and the guardrails that stop an institution ruining itself.

A platform that lets a school choose its own colours and then renders whatever
it chose is not customizable; it is negligent. Somebody will pick a pale gold on
ivory because it looks lovely on their designer's monitor, and a parent reading
a report card on a phone in daylight will not be able to see their child's
grades.

So every institutional colour choice passes through here, and the answer is
never a silent yes or a flat no. It is a *verdict with a remedy*: this pairing
is at 2.4:1, the standard is 4.5:1, and here is the nearest tone of the colour
you chose that reaches it. That sentence is what makes EdirasX intelligent
rather than merely configurable, and it is the sentence the Design Studio will
eventually speak.

WCAG 2.2 relative luminance, because it is the standard an institution will be
audited against. APCA is better perceptual science and is not yet what a
procurement questionnaire asks about.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

__all__ = [
    "AAA_NORMAL",
    "AA_LARGE",
    "AA_NORMAL",
    "Verdict",
    "contrast",
    "darken",
    "is_light",
    "lighten",
    "luminance",
    "mix",
    "nearest_accessible",
    "parse",
    "to_hex",
]

AA_NORMAL: Final[float] = 4.5
AA_LARGE: Final[float] = 3.0
AAA_NORMAL: Final[float] = 7.0
#: The floor for a border, an icon or any other non-text visual boundary.
NON_TEXT: Final[float] = 3.0

_HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


class ColourError(ValueError):
    """Something that is not a colour was offered as one."""


def parse(value: str) -> tuple[int, int, int]:
    """`#C9A961` → `(201, 169, 97)`. Accepts 3-, 6- and 8-digit hex."""
    match = _HEX.match((value or "").strip())
    if not match:
        raise ColourError(
            f"{value!r} is not a colour EdirasX can use. Give a hex value such "
            "as #1A3566."
        )
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))


def to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def _channel(value: int) -> float:
    srgb = value / 255
    return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4


def luminance(value: str) -> float:
    r, g, b = parse(value)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast(foreground: str, background: str) -> float:
    """The WCAG ratio, 1.0–21.0."""
    a, b = luminance(foreground), luminance(background)
    lighter, darker = max(a, b), min(a, b)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def is_light(value: str) -> bool:
    return luminance(value) > 0.36


def mix(a: str, b: str, weight: float) -> str:
    """Blend `a` into `b`. `weight` is how much of `a` survives."""
    ra, ga, ba = parse(a)
    rb, gb, bb = parse(b)
    w = max(0.0, min(1.0, weight))
    return to_hex((ra * w + rb * (1 - w), ga * w + gb * (1 - w), ba * w + bb * (1 - w)))


def darken(value: str, amount: float) -> str:
    return mix("#000000", value, amount)


def lighten(value: str, amount: float) -> str:
    return mix("#FFFFFF", value, amount)


def nearest_accessible(
    colour: str, background: str, *, target: float = AA_NORMAL, steps: int = 48
) -> str | None:
    """The closest tone of `colour` that reaches `target` against `background`.

    Walks *towards* whichever end of the range the background is not, one
    perceptual step at a time, and returns the first tone that clears the
    threshold — so the suggestion is recognisably the colour the institution
    chose rather than a colour we preferred. Returns `None` when even black or
    white cannot reach the target, which happens on mid-grey backgrounds and is
    a real answer: the *background* is the problem.
    """
    if contrast(colour, background) >= target:
        return colour
    toward = "#000000" if is_light(background) else "#FFFFFF"
    for step in range(1, steps + 1):
        candidate = mix(toward, colour, step / steps)
        if contrast(candidate, background) >= target:
            return candidate
    return None


@dataclass(frozen=True, slots=True)
class Verdict:
    """One check on one pairing, with a sentence somebody can act on.

    `severity` is `error` when the pairing would fail an accessibility audit and
    `warning` when it is legal but poor — a 4.6:1 body text is technically
    compliant and still tiring to read for an hour, and an institution deserves
    to be told the difference rather than given a pass mark.
    """

    role: str
    foreground: str
    background: str
    ratio: float
    required: float
    severity: str          # "error" | "warning" | "ok"
    message: str
    suggestion: str | None = None

    @property
    def passes(self) -> bool:
        return self.severity == "ok"

    def __bool__(self) -> bool:
        return self.passes


def check(
    role: str,
    foreground: str,
    background: str,
    *,
    required: float = AA_NORMAL,
    comfortable: float | None = None,
    what: str = "text",
) -> Verdict:
    """Judge one pairing, and say what to do about it.

    `comfortable` is the higher bar below which the pairing is legal but worth
    mentioning. It defaults to a step above the requirement, because the
    interesting failure is not 4.4 against 4.5 — it is a school that clears
    every threshold by a hair and wonders why its interface feels harsh.
    """
    comfortable = comfortable if comfortable is not None else required + 2.5
    ratio = contrast(foreground, background)

    if ratio >= comfortable:
        return Verdict(role, foreground, background, ratio, required, "ok",
                       f"{role}: {ratio}:1 — comfortable.")
    if ratio >= required:
        return Verdict(
            role, foreground, background, ratio, required, "warning",
            f"{role}: {ratio}:1 clears the {required}:1 standard, but only just. "
            f"{what.capitalize()} at this contrast is legible and tiring; a "
            "slightly deeper tone would read better on a phone in daylight.",
            suggestion=nearest_accessible(foreground, background, target=comfortable),
        )

    suggestion = nearest_accessible(foreground, background, target=required)
    if suggestion is None:
        return Verdict(
            role, foreground, background, ratio, required, "error",
            f"{role}: {ratio}:1 against {required}:1, and no tone of this colour "
            f"reaches the standard on {background}. The background is the "
            "problem here rather than the colour — choose a lighter or darker "
            "surface and this colour will work.",
        )
    return Verdict(
        role, foreground, background, ratio, required, "error",
        f"{role}: {ratio}:1 against a {required}:1 standard. {suggestion} is the "
        "nearest tone of the colour you chose that meets it.",
        suggestion=suggestion,
    )
