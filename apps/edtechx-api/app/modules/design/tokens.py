"""The EdirasX design tokens — the whole visual language, as data.

Nothing in the interface may name a colour, a size, or a duration directly.
Everything reads a token, and a token is a row here. That is not tidiness: it is
the mechanism by which an institution can eventually make EdirasX its own
without anybody rewriting a component, and by which an AI Design Studio can be
given a *validated schema* to manipulate rather than permission to emit CSS.

**Two layers, deliberately.** `PRIMITIVES` are the raw scales — `gold.500`,
`space.6`, `text.lg`. `SEMANTICS` say what a thing is *for* — `surface.canvas`,
`border.hairline`, `accent.strong`. Components only ever reference semantics. An
institution retheming EdirasX changes primitives and a handful of semantic
bindings; it never has to know which component used which grey.

---

**The visual direction, stated so that it can be argued with.**

EdirasX is a *royal institution* rendered by a *precision instrument*. The
reference points are a university's charter, an annual report set by somebody
who cares about type, and a private bank's statement — not a dashboard.

*Prestige comes from restraint.* There is no gradient in this file. There is one
shadow, and it exists for things that genuinely float above the page. Radii are
2–4px, never a pill and never a 16px card, because a sharp edge reads as
institutional and a soft one reads as consumer software. Depth is made from
surface value and a hairline, the way it is made on paper.

*Gold behaves like jewellery.* It is never a background and never a large fill.
It marks: the origin of a rule, an active state, a key figure, a ceremonial
element. A gold-coloured interface is a cheap one; a navy interface with gold at
the joints is not.

*Two grounds.* **Midnight** carries the institution's chrome — the rail, the
masthead, the login, ceremonial surfaces. **Ivory** carries the work. The
contrast between an authoritative dark frame and a warm editorial page is the
half-second signature.

**The Arabic DNA is structural, not decorative.** EdirasX takes its name from
الدراسة. The identity therefore derives from Islamic geometric construction: an
eight-point star built from two squares at 45°, whose central negative space is
a cross — so the X of EdirasX is the void at the centre of the star rather than
a letter placed beside it. The star appears at 6–10px as a rule terminator, an
active marker and a list node, and as a 4%-opacity lattice on ceremonial
surfaces. See `ornament.py`. Nothing here places calligraphy on a screen.
"""

from __future__ import annotations

from typing import Any, Final

__all__ = [
    "DENSITIES",
    "EDIRASX",
    "PRIMITIVES",
    "SEMANTICS",
    "ThemeShape",
    "flatten",
]


# --- primitives -------------------------------------------------------------
#
# Scales, not decisions. Every ramp is perceptually spaced rather than
# arithmetically: a 10% lightness step near white is a different amount of
# change from a 10% step near black, and ramps built by dividing a number
# produce the muddy middles that make a palette look machine-made.

PRIMITIVES: Final[dict[str, dict[str, Any]]] = {
    # Midnight — the institutional ground. Blue-black rather than grey-black:
    # a neutral dark reads as a developer tool, and a warm dark reads as a
    # restaurant menu.
    "midnight": {
        "900": "#060A12",
        "800": "#0A101C",
        "700": "#0F1728",
        "600": "#152036",
        "500": "#1C2A45",
        "400": "#2A3B5C",
    },
    # Royal — authority, and the interactive colour. Deliberately not the
    # cobalt every product uses; this is closer to a doctoral hood.
    "royal": {
        "800": "#12294F",
        "700": "#1A3566",
        "600": "#204480",
        "500": "#2A579E",
        "400": "#4A7BC8",
        "300": "#88AADD",
        "200": "#C3D6F0",
        "100": "#E6EEF9",
    },
    # Champagne gold. `500` is the signature; the darker steps exist so gold can
    # be used as *text* on ivory without failing contrast, which is the usual
    # way a gold accent turns into an accessibility problem.
    "gold": {
        "800": "#5E4A21",
        "700": "#7E6530",
        "600": "#9C7E3E",
        "500": "#C9A961",
        "400": "#DCC48A",
        "300": "#EBDCB6",
        "200": "#F5EDD9",
        "100": "#FBF7EC",
    },
    # Warm ivory — the page. Not white. A pure-white canvas beside a midnight
    # rail reads as a screenshot of two different products.
    "ivory": {
        "50": "#FFFDF8",
        "100": "#FAF6EE",
        "200": "#F3EDE1",
        "300": "#E8DFCE",
        "400": "#D8CCB4",
    },
    # Charcoal — text and neutral structure, warmed very slightly so it sits on
    # ivory without looking like it was pasted from another palette.
    "charcoal": {
        "900": "#14171D",
        "800": "#1E222A",
        "700": "#2B303A",
        "600": "#3E4553",
        "500": "#5A6273",
        "400": "#7C8494",
        "300": "#A6ACB8",
        "200": "#CDD1D9",
        "100": "#E7E9ED",
    },
    # Garnet — ceremonial, and the error colour. A university's red, not a
    # notification's red.
    "garnet": {
        "800": "#571622",
        "700": "#6E1F2E",
        "600": "#8E2A3C",
        "500": "#A8394D",
        "400": "#C86E7E",
        "200": "#F0D8DD",
    },
    # Verdant and amber, chosen to sit inside the same world. The usual
    # traffic-light green and orange are the fastest way to make a considered
    # palette look like a bootstrap theme.
    "verdant": {
        "700": "#14543A",
        "600": "#1F6B4A",
        "500": "#2E8560",
        "200": "#D3E7DC",
    },
    "amber": {
        "700": "#7A5310",
        "600": "#9A6A12",
        "500": "#BE871F",
        "200": "#F5E6C4",
    },
    # --- type -------------------------------------------------------------
    #
    # A 1.20 minor-third ramp through the interface sizes, opening to 1.25 at
    # display sizes where the jumps have to be felt rather than measured.
    "text": {
        "3xs": "0.6875rem",   # 11px — micro-labels, letter-spaced
        "2xs": "0.75rem",     # 12px
        "xs": "0.8125rem",    # 13px — dense table text
        "sm": "0.875rem",     # 14px
        "base": "0.9375rem",  # 15px — body. 16 is a shade loose for data work.
        "md": "1.0625rem",    # 17px
        "lg": "1.25rem",      # 20px
        "xl": "1.5rem",       # 24px
        "2xl": "1.875rem",    # 30px
        "3xl": "2.375rem",    # 38px
        "4xl": "3rem",        # 48px
        "5xl": "3.75rem",     # 60px — editorial metrics
        "6xl": "4.75rem",     # 76px — the one hero size
    },
    "leading": {
        "tight": "1.08",
        "snug": "1.22",
        "normal": "1.5",
        "relaxed": "1.62",
        "loose": "1.75",
    },
    "tracking": {
        # Negative at display sizes, positive at micro sizes. A single tracking
        # value across a type system is the reason most of them look untuned.
        "tighter": "-0.022em",
        "tight": "-0.012em",
        "normal": "0",
        "wide": "0.02em",
        "wider": "0.08em",
        "widest": "0.16em",
    },
    "weight": {
        "regular": "400",
        "medium": "500",
        "semibold": "600",
        "bold": "700",
    },
    # --- space ------------------------------------------------------------
    #
    # A 4px base. Named by step rather than by size so a density change can
    # rescale the whole system from one multiplier.
    "space": {
        "0": "0",
        "px": "1px",
        "1": "0.25rem",
        "2": "0.5rem",
        "3": "0.75rem",
        "4": "1rem",
        "5": "1.25rem",
        "6": "1.5rem",
        "7": "2rem",
        "8": "2.5rem",
        "9": "3rem",
        "10": "4rem",
        "11": "5rem",
        "12": "6.5rem",
        "13": "8rem",
    },
    # --- form -------------------------------------------------------------
    "radius": {
        # Institutional, not consumer. The largest radius in the system is 4px,
        # and `full` exists for avatars and nothing else.
        "none": "0",
        "sm": "2px",
        "md": "3px",
        "lg": "4px",
        "full": "999px",
    },
    "border": {
        "hair": "1px",
        "thin": "1.5px",
        "thick": "2px",
        "rule": "3px",
    },
    # One real shadow, for things that float. Everything else gets depth from
    # surface value and a hairline, the way depth is made on paper.
    "shadow": {
        "none": "none",
        "overlay": "0 24px 48px -12px rgba(6, 10, 18, 0.28), 0 2px 6px rgba(6, 10, 18, 0.10)",
        "raised": "0 1px 2px rgba(6, 10, 18, 0.06)",
        "ring": "0 0 0 3px rgba(42, 87, 158, 0.28)",
        "ring-gold": "0 0 0 3px rgba(201, 169, 97, 0.34)",
    },
    # --- motion -----------------------------------------------------------
    #
    # Motion indicates; it does not entertain. One easing curve, three
    # durations, and nothing loops except a genuine progress indicator.
    "duration": {
        "instant": "90ms",
        "fast": "150ms",
        "normal": "220ms",
        "slow": "340ms",
    },
    "easing": {
        # A decelerating curve with no overshoot. Springy easing on an
        # institutional interface reads as a toy.
        "standard": "cubic-bezier(0.2, 0, 0, 1)",
        "exit": "cubic-bezier(0.4, 0, 1, 1)",
        "enter": "cubic-bezier(0, 0, 0.2, 1)",
    },
    # --- type families ----------------------------------------------------
    "family": {
        "display": "'Source Serif 4', 'Iowan Old Style', Georgia, serif",
        "sans": "'Inter', 'SF Pro Text', -apple-system, 'Segoe UI', sans-serif",
        "mono": "'IBM Plex Mono', 'SF Mono', ui-monospace, monospace",
        # Arabic is a first-class family, not a fallback appended to the Latin
        # stack. Amiri is a naskh face of genuine quality and is set at a larger
        # optical size (`--font-size-arabic-adjust`) because Arabic needs about
        # 1.15× to sit level with Latin at the same nominal size.
        "arabic": "'Amiri', 'Noto Naskh Arabic', serif",
    },
    "layer": {
        "base": "0",
        "raised": "10",
        "sticky": "100",
        "drawer": "300",
        "overlay": "400",
        "toast": "500",
    },
}


# --- semantics --------------------------------------------------------------
#
# What a token is *for*. Components reference only these. Each value is a
# reference into `PRIMITIVES` written as `{group}.{step}`, resolved by
# `theme.py` — so an institution overriding `gold.500` moves every semantic
# built on it, and one overriding `accent.strong` moves only that role.

SEMANTICS: Final[dict[str, dict[str, str]]] = {
    # --- ivory mode: the working surface ---------------------------------
    "ivory": {
        "surface.canvas": "ivory.100",
        "surface.raised": "ivory.50",
        "surface.sunken": "ivory.200",
        "surface.inverse": "midnight.800",
        "surface.selected": "gold.100",
        "surface.accent-wash": "royal.100",
        "surface.overlay": "ivory.50",

        "text.primary": "charcoal.900",
        "text.secondary": "charcoal.500",
        "text.tertiary": "charcoal.400",
        "text.inverse": "ivory.50",
        "text.accent": "royal.700",
        "text.on-accent": "ivory.50",
        # Gold *text* uses a darkened step. This is the single most common way
        # a gold accent becomes an accessibility failure, so the system simply
        # does not offer the light one for text.
        "text.gold": "gold.700",
        "text.success": "verdant.700",
        "text.warning": "amber.700",
        "text.danger": "garnet.700",

        "border.hairline": "ivory.300",
        "border.strong": "ivory.400",
        # Deliberately much darker than `border.strong`. A divider between two
        # table rows is decorative and may be a whisper; the edge of a text
        # field is what tells somebody where to type, and WCAG 1.4.11 requires
        # 3:1 for it. They were one token, which made the fields nearly
        # invisible while the page looked pleasantly quiet.
        "border.control": "charcoal.400",
        "border.accent": "royal.600",
        "border.gold": "gold.500",
        "border.inverse": "midnight.600",

        "accent.strong": "royal.600",
        "accent.hover": "royal.700",
        "accent.subtle": "royal.100",
        "accent.metal": "gold.500",
        "accent.metal-deep": "gold.700",
        "accent.ceremonial": "garnet.700",

        "state.success": "verdant.600",
        "state.success-wash": "verdant.200",
        "state.warning": "amber.600",
        "state.warning-wash": "amber.200",
        "state.danger": "garnet.600",
        "state.danger-wash": "garnet.200",
        "state.info": "royal.500",
        "state.info-wash": "royal.100",
        "state.disabled": "charcoal.300",
        "state.disabled-surface": "ivory.200",
    },
    # --- midnight mode: the institution's chrome -------------------------
    "midnight": {
        "surface.canvas": "midnight.800",
        "surface.raised": "midnight.700",
        "surface.sunken": "midnight.900",
        "surface.inverse": "ivory.100",
        "surface.selected": "midnight.600",
        "surface.accent-wash": "midnight.600",
        "surface.overlay": "midnight.700",

        "text.primary": "ivory.50",
        "text.secondary": "charcoal.300",
        "text.tertiary": "charcoal.400",
        "text.inverse": "charcoal.900",
        "text.accent": "royal.300",
        "text.on-accent": "ivory.50",
        "text.gold": "gold.400",
        "text.success": "verdant.500",
        "text.warning": "amber.500",
        "text.danger": "garnet.400",

        "border.hairline": "midnight.500",
        "border.strong": "midnight.400",
        "border.control": "charcoal.500",
        "border.accent": "royal.400",
        "border.gold": "gold.600",
        "border.inverse": "ivory.300",

        "accent.strong": "royal.500",
        "accent.hover": "royal.400",
        "accent.subtle": "midnight.600",
        "accent.metal": "gold.500",
        "accent.metal-deep": "gold.400",
        "accent.ceremonial": "garnet.500",

        "state.success": "verdant.500",
        "state.success-wash": "verdant.700",
        "state.warning": "amber.500",
        "state.warning-wash": "amber.700",
        "state.danger": "garnet.500",
        "state.danger-wash": "garnet.800",
        "state.info": "royal.400",
        "state.info-wash": "midnight.600",
        "state.disabled": "charcoal.600",
        "state.disabled-surface": "midnight.700",
    },
}


# --- density ----------------------------------------------------------------
#
# One multiplier on the spacing scale and one on the control heights. An
# institution running a two-thousand-row register wants `compact`; a nursery
# with eleven children wants `comfortable`, and neither should be given a
# different design system to get it.

DENSITIES: Final[dict[str, dict[str, str]]] = {
    "compact": {"space-scale": "0.8", "control-height": "1.875rem", "row-height": "2.125rem"},
    "default": {"space-scale": "1", "control-height": "2.25rem", "row-height": "2.75rem"},
    "comfortable": {"space-scale": "1.15", "control-height": "2.625rem", "row-height": "3.25rem"},
}


# --- the shape a theme may take --------------------------------------------


class ThemeShape:
    """What an institution — or a Design Studio — is allowed to change.

    Named explicitly so the validation, the API and the eventual AI have one
    definition to agree on. Anything outside this is not a theme; it is a fork.
    """

    #: Primitive ramps an institution may replace wholesale.
    OPEN_RAMPS: Final[frozenset[str]] = frozenset(
        {"royal", "gold", "ivory", "midnight", "garnet", "charcoal"}
    )
    #: Semantic roles an institution may rebind to a different primitive.
    OPEN_ROLES: Final[frozenset[str]] = frozenset(
        {
            "accent.strong",
            "accent.hover",
            "accent.metal",
            "accent.metal-deep",
            "accent.ceremonial",
            "surface.canvas",
            "surface.raised",
            "text.gold",
            "border.gold",
        }
    )
    #: Families an institution may substitute.
    OPEN_FAMILIES: Final[frozenset[str]] = frozenset({"display", "sans", "mono", "arabic"})
    #: Modes the shell may be set to.
    MODES: Final[tuple[str, ...]] = ("ivory", "midnight")
    #: Ornament levels — how much of the geometric system is expressed.
    ORNAMENT: Final[tuple[str, ...]] = ("none", "restrained", "full", "ceremonial")


#: The EdirasX theme itself: the default every institution starts from.
EDIRASX: Final[dict[str, Any]] = {
    "key": "edirasx",
    "name": "EdirasX Royal",
    "mode": "ivory",
    "density": "default",
    "ornament": "restrained",
    "primitives": {},   # no overrides: this *is* the primitive set
    "roles": {},
    "families": {},
}


def flatten(group: str, scale: dict[str, Any], prefix: str = "") -> dict[str, str]:
    """`{"gold": {"500": "#C9A961"}}` → `{"--gold-500": "#C9A961"}`."""
    return {f"--{prefix}{group}-{step}": str(value) for step, value in scale.items()}
