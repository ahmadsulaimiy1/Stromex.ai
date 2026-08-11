"""Resolving a theme, judging it, and emitting it as CSS custom properties.

Three things happen here and they are kept apart on purpose.

**Resolution** merges an institution's overrides onto the EdirasX defaults and
produces a complete token set. It never fails: a theme is data, and half a
theme still has to render something.

**Review** judges the resolved theme against the guardrails and returns
verdicts. It never changes anything. An institution is told what is wrong and
what to do about it; the platform does not quietly substitute a colour somebody
chose, because a school that finds its brand silently corrected will trust
nothing else the product tells it.

**Emission** turns the resolved theme into CSS custom properties. This is the
only place in EdirasX that writes a colour into a stylesheet.

The separation is what makes an AI Design Studio possible. "Make this more
royal" becomes: propose overrides → resolve → review → show both → let a human
approve. Every step is data, and the only thing the model is permitted to emit
is a set of token overrides validated against `ThemeShape` — never CSS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.design import contrast as ink
from app.modules.design.tokens import (
    DENSITIES,
    EDIRASX,
    PRIMITIVES,
    SEMANTICS,
    ThemeShape,
)

__all__ = [
    "Review",
    "Theme",
    "ThemeError",
    "css_variables",
    "for_institution",
    "resolve",
    "review",
    "stylesheet",
]


class ThemeError(ValueError):
    """A theme that names something outside the system's vocabulary."""


@dataclass(frozen=True, slots=True)
class Theme:
    """A complete, resolved token set. Everything the interface needs to render."""

    key: str
    name: str
    mode: str
    density: str
    ornament: str
    primitives: dict[str, dict[str, str]]
    roles: dict[str, str]          # semantic role -> resolved literal value
    families: dict[str, str]
    source: dict[str, Any] = field(default_factory=dict)

    def colour(self, role: str) -> str:
        """The literal value bound to a semantic role."""
        try:
            return self.roles[role]
        except KeyError:
            raise ThemeError(f"{role!r} is not a semantic role in this theme.") from None

    @property
    def is_dark(self) -> bool:
        return not ink.is_light(self.colour("surface.canvas"))


# --- resolution -------------------------------------------------------------


def _merge_primitives(overrides: dict[str, Any]) -> dict[str, dict[str, str]]:
    merged = {group: dict(scale) for group, scale in PRIMITIVES.items()}
    for group, scale in (overrides or {}).items():
        if group not in ThemeShape.OPEN_RAMPS:
            raise ThemeError(
                f"{group!r} is not a ramp an institution may replace. Open ramps: "
                + ", ".join(sorted(ThemeShape.OPEN_RAMPS))
            )
        if group not in merged:  # pragma: no cover - OPEN_RAMPS ⊂ PRIMITIVES
            raise ThemeError(f"{group!r} is not a primitive ramp.")
        for step, value in (scale or {}).items():
            if step not in merged[group]:
                raise ThemeError(
                    f"{group}.{step} is not a step of the {group} ramp. Steps: "
                    + ", ".join(merged[group])
                )
            ink.parse(str(value))
            merged[group][str(step)] = str(value)
    return merged


def _dereference(reference: str, primitives: dict[str, dict[str, str]]) -> str:
    """`gold.500` → `#C9A961`. A literal hex passes through unchanged."""
    if reference.startswith("#"):
        ink.parse(reference)
        return reference.upper()
    group, _, step = reference.partition(".")
    try:
        return primitives[group][step]
    except KeyError:
        raise ThemeError(
            f"{reference!r} names no token. Use `ramp.step` — for example "
            "`royal.600` — or a hex value."
        ) from None


def resolve(overrides: dict[str, Any] | None = None) -> Theme:
    """Merge an institution's choices onto the EdirasX defaults.

    Deliberately total: it either produces a complete theme or refuses the
    input as malformed. There is no partial resolution, because a component
    reaching for `--border-hairline` and finding nothing is a rendering bug
    somewhere far away from the theme that caused it.
    """
    source = {**EDIRASX, **(overrides or {})}

    mode = str(source.get("mode") or "ivory")
    if mode not in ThemeShape.MODES:
        raise ThemeError(
            f"{mode!r} is not a mode. One of: " + ", ".join(ThemeShape.MODES)
        )
    density = str(source.get("density") or "default")
    if density not in DENSITIES:
        raise ThemeError(
            f"{density!r} is not a density. One of: " + ", ".join(DENSITIES)
        )
    ornament = str(source.get("ornament") or "restrained")
    if ornament not in ThemeShape.ORNAMENT:
        raise ThemeError(
            f"{ornament!r} is not an ornament level. One of: "
            + ", ".join(ThemeShape.ORNAMENT)
        )

    primitives = _merge_primitives(source.get("primitives") or {})

    roles: dict[str, str] = {}
    for role, reference in SEMANTICS[mode].items():
        roles[role] = _dereference(reference, primitives)
    for role, reference in (source.get("roles") or {}).items():
        if role not in ThemeShape.OPEN_ROLES:
            raise ThemeError(
                f"{role!r} is not a role an institution may rebind. Open roles: "
                + ", ".join(sorted(ThemeShape.OPEN_ROLES))
            )
        roles[role] = _dereference(str(reference), primitives)

    families = dict(PRIMITIVES["family"])
    for slot, stack in (source.get("families") or {}).items():
        if slot not in ThemeShape.OPEN_FAMILIES:
            raise ThemeError(
                f"{slot!r} is not a font slot. One of: "
                + ", ".join(sorted(ThemeShape.OPEN_FAMILIES))
            )
        families[slot] = str(stack)

    return Theme(
        key=str(source.get("key") or "edirasx"),
        name=str(source.get("name") or "EdirasX Royal"),
        mode=mode,
        density=density,
        ornament=ornament,
        primitives=primitives,
        roles=roles,
        families=families,
        source=source,
    )


# --- review -----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Review:
    """Everything the guardrails have to say about a theme."""

    verdicts: tuple[ink.Verdict, ...]

    @property
    def errors(self) -> tuple[ink.Verdict, ...]:
        return tuple(v for v in self.verdicts if v.severity == "error")

    @property
    def warnings(self) -> tuple[ink.Verdict, ...]:
        return tuple(v for v in self.verdicts if v.severity == "warning")

    @property
    def is_publishable(self) -> bool:
        """Whether this theme may be published to an institution's users."""
        return not self.errors

    def summary(self) -> str:
        if self.errors:
            return (
                f"{len(self.errors)} accessibility failure"
                f"{'s' if len(self.errors) > 1 else ''} — this theme cannot be "
                "published as it stands."
            )
        if self.warnings:
            return (
                f"Meets the standard, with {len(self.warnings)} pairing"
                f"{'s' if len(self.warnings) > 1 else ''} worth improving."
            )
        return "Every pairing is comfortably readable."


#: The pairings that actually decide whether an institution's interface is
#: usable. Each is `(role, foreground, background, required, description)`.
_PAIRINGS: tuple[tuple[str, str, str, float, str], ...] = (
    ("Body text on the page", "text.primary", "surface.canvas", ink.AA_NORMAL, "text"),
    ("Body text on a panel", "text.primary", "surface.raised", ink.AA_NORMAL, "text"),
    ("Secondary text", "text.secondary", "surface.canvas", ink.AA_NORMAL, "text"),
    ("Link and action text", "text.accent", "surface.canvas", ink.AA_NORMAL, "text"),
    ("Gold text", "text.gold", "surface.canvas", ink.AA_NORMAL, "text"),
    ("Text on a primary button", "text.on-accent", "accent.strong", ink.AA_NORMAL, "text"),
    ("Error text", "text.danger", "surface.canvas", ink.AA_NORMAL, "text"),
    ("Success text", "text.success", "surface.canvas", ink.AA_NORMAL, "text"),
    # Non-text, held to WCAG 1.4.11's 3:1 — but only for the things that
    # standard is actually about: visual information required to identify a
    # component or a state.
    #
    # A control's border is such a thing: it is what tells somebody where a
    # field is. A *divider* is not, and neither is the gold at the origin of a
    # section rule — checking those at 3:1 would demand heavy dark lines and
    # destroy the restraint that makes the product look composed. An earlier
    # version checked them anyway and reported two failures against its own
    # palette, which is how a check that is merely strict turns into one that is
    # ignored.
    #
    # Gold *is* used on active states, and there the rule is different and
    # stronger: it may never be the only signal. `test_design.py` asserts that
    # structurally rather than by contrast, because contrast cannot express it.
    ("Input and control borders", "border.control", "surface.raised", ink.NON_TEXT, "border"),
    ("Input borders on the page", "border.control", "surface.canvas", ink.NON_TEXT, "border"),
    ("Focus and selection", "accent.strong", "surface.canvas", ink.NON_TEXT, "indicator"),
)


def review(theme: Theme) -> Review:
    """Judge a theme. Changes nothing; says everything.

    The list is short on purpose. Checking every possible pairing produces a
    report nobody reads; checking the eleven that decide whether a parent can
    read a grade on a phone produces one somebody acts on.
    """
    verdicts = []
    for label, fg, bg, required, what in _PAIRINGS:
        verdicts.append(
            ink.check(
                label,
                theme.colour(fg),
                theme.colour(bg),
                required=required,
                comfortable=required + (2.5 if required >= ink.AA_NORMAL else 1.5),
                what=what,
            )
        )
    return Review(tuple(verdicts))


# --- emission ---------------------------------------------------------------


def css_variables(theme: Theme) -> dict[str, str]:
    """The complete custom-property set for one theme.

    Primitives are emitted as well as semantics, because a themed institution's
    own stylesheet — and eventually its Design Studio preview — needs to be able
    to reach a ramp step directly. Components still may not.
    """
    variables: dict[str, str] = {}

    for group, scale in theme.primitives.items():
        if group in {"family", "layer"}:
            continue
        for step, value in scale.items():
            variables[f"--{group}-{step}"] = value

    for role, value in theme.roles.items():
        variables[f"--{role.replace('.', '-')}"] = value

    for slot, stack in theme.families.items():
        variables[f"--font-{slot}"] = stack
    for slot, value in PRIMITIVES["layer"].items():
        variables[f"--layer-{slot}"] = value

    density = DENSITIES[theme.density]
    for name, value in density.items():
        variables[f"--{name}"] = value

    # Spacing is emitted through the density multiplier so one setting rescales
    # the whole system rather than each component knowing about density.
    scale_factor = float(density["space-scale"])
    for step, value in PRIMITIVES["space"].items():
        if value.endswith("rem"):
            variables[f"--space-{step}"] = f"{round(float(value[:-3]) * scale_factor, 4)}rem"
        else:
            variables[f"--space-{step}"] = value

    variables["--ornament-level"] = theme.ornament
    # Deliberately low. A lattice at 14% read as noise across a transcript and
    # competed with the grades — the point of a watermark is that a reader
    # notices it only when they look for it.
    variables["--ornament-opacity"] = {
        "none": "0", "restrained": "0.05", "full": "0.07", "ceremonial": "0.05",
    }[theme.ornament]
    # Arabic needs about 1.15× to sit level with Latin at the same nominal size.
    variables["--font-size-arabic-adjust"] = "1.15"
    return variables


def stylesheet(theme: Theme, *, selector: str = ":root") -> str:
    """The theme as a CSS block, ready to inline."""
    body = "\n".join(f"  {name}: {value};" for name, value in css_variables(theme).items())
    return f"{selector} {{\n{body}\n}}"


# --- an institution's own theme --------------------------------------------


def for_institution(db) -> Theme:
    """The theme this school has actually chosen.

    Built from the branding profile it already fills in for its documents,
    rather than from a second parallel table: an institution that has told us
    its colours once should not be asked again because the screen and the
    transcript are rendered by different modules.

    An institution that has set nothing gets EdirasX itself, which is the right
    default — a school on its first morning should look distinguished before it
    has made a single decision.
    """
    from app.modules.customization import branding as branding_module

    identity = branding_module.resolve(db)
    overrides: dict[str, Any] = {"name": identity.display_name or "EdirasX Royal"}

    primitives: dict[str, dict[str, str]] = {}
    if identity.primary_colour:
        primitives.setdefault("royal", {})["600"] = identity.primary_colour
        primitives["royal"]["700"] = ink.darken(identity.primary_colour, 0.18)
        primitives["royal"]["500"] = ink.lighten(identity.primary_colour, 0.12)
    if identity.accent_colour:
        primitives.setdefault("gold", {})["500"] = identity.accent_colour
        # The *text* step is derived rather than taken, because an institution
        # choosing a light champagne has chosen an ornament colour and not a
        # text colour, and rendering their choice as body text would be
        # obeying them into an accessibility failure.
        # Through the guardrail rather than by a fixed darkening. A fixed 34%
        # produced 3.24:1 for a pale champagne, which is the exact failure the
        # guardrails exist to prevent — and the platform would have shipped it
        # while telling the institution its theme was fine.
        canvas = _dereference(SEMANTICS["ivory"]["surface.canvas"], PRIMITIVES)
        primitives["gold"]["700"] = (
            ink.nearest_accessible(identity.accent_colour, canvas, target=ink.AA_NORMAL + 1)
            or ink.darken(identity.accent_colour, 0.55)
        )
        primitives["gold"]["400"] = ink.lighten(identity.accent_colour, 0.22)
    if identity.ink_colour:
        primitives.setdefault("charcoal", {})["900"] = identity.ink_colour

    if primitives:
        overrides["primitives"] = primitives

    families: dict[str, str] = {}
    if identity.heading_font:
        families["display"] = identity.heading_font
    if identity.body_font:
        families["sans"] = identity.body_font
    if families:
        overrides["families"] = families

    return resolve(overrides)
