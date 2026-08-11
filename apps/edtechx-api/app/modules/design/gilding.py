"""Gold as a material, not a hex value.

`#D4AF37` is not gold. It is the colour of gold under one lighting condition,
flattened, and a document that uses it reads as a web page that decided to be
expensive. Real gilding on paper is a *surface*: a hot-stamped foil, a raised
thermographic ink, an engraved plate whose walls catch light differently from
its floor. What the eye recognises as gold is the **banded specular ramp** —
a bright crest, a broad reflecting face, a body colour, and a wall the light
does not reach — repeated across the form.

So every metal in this file is four inks and a role for each, and the treatments
below place those four inks the way a physical process would place them.

**What is real and what is simulated, stated once and carried in the data.**
Every `Metal` names the physical process it is drawn to represent, and every
treatment function says in its docstring what a press would actually have to do.
A `<linearGradient>` on a title is a *simulation of foil*; it is not foil, it
does not survive a photocopier the way foil does, and it carries no security
property whatsoever. `SIMULATION` is the ledger, and `production_note()` returns
the line that belongs in a print specification so the claim travels with the
artwork instead of living in somebody's memory.

**The hairline rule from `geometry.py` still governs here.** A gradient is legal
on an *area* — a title fill, a corner block, a medallion face — because area
screens survive press. It is never legal on a hairline: a 0.1mm stroke with a
gradient separates into a screen percentage and drops off press. Fine metal
linework therefore uses `engraved_metal_rule()`, which is three *flat* strokes
in three of the metal's four inks, and which is what an engraver would cut.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "METALS",
    "SCHEMES",
    "SIMULATION",
    "Metal",
    "Scheme",
    "emboss",
    "engraved_metal_rule",
    "foil_gradient",
    "metal_for",
    "production_note",
    "raised_type_css",
    "scheme_for",
]


@dataclass(frozen=True, slots=True)
class Metal:
    """One metal, as the four inks a press would actually lay down.

    The names are the positions on a struck foil, outermost first: the crest the
    light hits, the face that carries most of the area, the body colour, and the
    wall in shadow. A treatment that uses fewer than three of these is a colour,
    not a metal.
    """

    key: str
    name: str
    #: The lit crest. Used sparingly — a raised edge, a highlight stop.
    highlight: str
    #: The broad reflecting face. This is the one most of the artwork is in.
    face: str
    #: The body colour, and the safest single flat value if only one is possible.
    core: str
    #: The wall the light does not reach. Gives the form its depth.
    shadow: str
    #: The physical process this palette is drawn from.
    process: str
    #: A foil reference a print vendor can actually order against. Named
    #: honestly as a *reference*: the exact shade is the vendor's to match.
    foil_reference: str

    @property
    def ramp(self) -> tuple[str, ...]:
        """Crest → face → core → shadow. The order light travels."""
        return (self.highlight, self.face, self.core, self.shadow)


#: The metals. Each is a genuinely different material rather than a lightness
#: variation: champagne is cooler and lower in chroma than royal gold, antique
#: is browner and darker in the face than in the core (which is what oxidation
#: does), and silver's shadow is blue rather than brown because silver reflects
#: a cool environment.
METALS: Final[dict[str, Metal]] = {
    "royal": Metal(
        key="royal", name="Royal gold",
        highlight="#FBEFC2", face="#E3C169", core="#B08D57", shadow="#6B4E1E",
        process="Hot-stamped gold foil on ivory stock",
        foil_reference="Kurz Luxor 220 / API 501 gold — vendor to match",
    ),
    "antique": Metal(
        key="antique", name="Antique gold",
        highlight="#E8D6A6", face="#C0A059", core="#8E7238", shadow="#4A3714",
        process="Oxidised gold foil, or gold ink over a warm grey underprint",
        foil_reference="Kurz Luxor 355 antique — vendor to match",
    ),
    "champagne": Metal(
        key="champagne", name="Champagne gold",
        highlight="#F6EEDC", face="#DCCBA6", core="#B9A87F", shadow="#736546",
        process="Pale champagne foil; reads as metal without reading as brass",
        foil_reference="API 220 champagne — vendor to match",
    ),
    "pale": Metal(
        key="pale", name="Pale gold",
        highlight="#FBF3D8", face="#EADFAE", core="#CBBB7F", shadow="#877A45",
        process="Pale gold foil on a dark ground; the low-contrast register",
        foil_reference="Kurz Luxor 380 pale — vendor to match",
    ),
    "deep": Metal(
        key="deep", name="Deep gold",
        highlight="#EFCE85", face="#C99B3C", core="#9A6F1C", shadow="#553B0A",
        process="Deep gold foil or metallic ink; the highest-chroma register",
        foil_reference="Pantone 872 C metallic / deep gold foil",
    ),
    "brushed": Metal(
        key="brushed", name="Brushed gold",
        highlight="#E4D6B0", face="#C6B489", core="#9E8C63", shadow="#5F5335",
        process="Brushed/satin foil — a diffuse face rather than a mirror",
        foil_reference="Satin-finish gold foil — vendor to match",
    ),
    "copper": Metal(
        key="copper", name="Copper",
        highlight="#F3CDAA", face="#D08E5F", core="#9E6234", shadow="#5A3418",
        process="Copper foil; the warm counter-metal in a two-tone scheme",
        foil_reference="Kurz Luxor 440 copper — vendor to match",
    ),
    "silver": Metal(
        key="silver", name="Silver",
        highlight="#F4F6F8", face="#CFD6DD", core="#A2ACB6", shadow="#5C666F",
        process="Silver foil; cool shadow because silver reflects a cool room",
        foil_reference="Kurz Luxor 700 silver — vendor to match",
    ),
}


#: The honesty ledger. Every visual treatment this module can produce, and what
#: it is and is not. Read by `production_note()` and reproduced verbatim in the
#: production specification, so an institution never learns from a forger that
#: its "foil" was a gradient.
SIMULATION: Final[dict[str, tuple[str, str]]] = {
    "foil_gradient": (
        "A banded linear gradient standing in for a struck metallic foil.",
        "Visual simulation only. It is ink on a screen or a flat press sheet; "
        "it has no metallic reflectance, no tactile relief, and no "
        "anti-copy property. Physical foil requires a hot-stamping die.",
    ),
    "engraved_metal_rule": (
        "Three flat strokes in the metal's highlight, face and shadow inks, "
        "reading as a line cut into the sheet.",
        "Printable as specified in metallic or process ink. Becomes a genuine "
        "engraving only if produced by intaglio or die-stamping, which is a "
        "vendor process, not something this artwork performs.",
    ),
    "emboss": (
        "A pale copy offset towards the light and an ink copy offset away, "
        "beneath the drawn figure — how a blind emboss reads on paper.",
        "Visual simulation. A true blind emboss is uninked relief and needs a "
        "male/female die pair. The simulation is deliberately uninked in "
        "appearance so that a physically embossed edition and the digital "
        "edition read as the same document.",
    ),
    "raised_type": (
        "Paired light and dark offsets on display type, standing in for raised "
        "foil or thermographic ink.",
        "Visual simulation. Raised type is a physical process (thermography or "
        "raised foil) and cannot be produced by a renderer.",
    ),
}


def metal_for(key: str) -> Metal:
    if key not in METALS:
        raise ValueError(
            f"{key!r} is not a metal. One of: " + ", ".join(sorted(METALS))
        )
    return METALS[key]


def production_note(treatment: str) -> str:
    """The sentence that belongs in the print specification for a treatment."""
    what, limit = SIMULATION[treatment]
    return f"{what} {limit}"


# --- treatments --------------------------------------------------------------


def foil_gradient(metal: Metal, identifier: str, *, angle: float = 22.0,
                  bands: int = 2) -> str:
    """A banded specular ramp — the simulation of struck foil.

    Not a two-stop gradient. Foil catches light in *bands*, because the die
    presses the foil into a surface that is not optically flat, and the ramp
    therefore returns to the highlight more than once across a broad form. The
    difference between one band and three is most of the difference between
    "yellow" and "metal".

    **Areas only.** See the module docstring: a gradient on a hairline becomes a
    screen percentage at separation. For linework use `engraved_metal_rule`.
    """
    stops: list[str] = []
    ramp = (metal.shadow, metal.core, metal.face, metal.highlight,
            metal.face, metal.core)
    total = bands * len(ramp)
    for index in range(total + 1):
        colour = ramp[index % len(ramp)]
        stops.append(
            f'<stop offset="{index / total:.4f}" stop-color="{colour}"/>'
        )
    return (
        f'<linearGradient id="{identifier}" x1="0" y1="0" x2="1" y2="0"'
        f' gradientTransform="rotate({angle:.1f} 0.5 0.5)">'
        + "".join(stops)
        + "</linearGradient>"
    )


def engraved_metal_rule(x1: float, y1: float, x2: float, y2: float, *,
                        metal: Metal, weight: float = 0.5) -> str:
    """A metal rule as an engraver would cut it: three flat strokes.

    Highlight above, face in the middle, shadow below — perpendicular to the
    run, so the rule reads as a channel with a lit wall and a dark one. Every
    stroke is a flat ink at a real weight, which is what lets this survive being
    separated into a single metallic plate.
    """
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 or 1.0
    # The normal, so the three strokes stack across the rule rather than along.
    nx, ny = -(y2 - y1) / length, (x2 - x1) / length
    offset = weight * 0.62

    def stroke(shift: float, colour: str, w: float) -> str:
        return (
            f'<line x1="{x1 + nx * shift:.2f}" y1="{y1 + ny * shift:.2f}"'
            f' x2="{x2 + nx * shift:.2f}" y2="{y2 + ny * shift:.2f}"'
            f' stroke="{colour}" stroke-width="{w:.3f}" stroke-linecap="butt"/>'
        )

    return (
        stroke(-offset, metal.highlight, weight * 0.34)
        + stroke(0.0, metal.face, weight)
        + stroke(offset, metal.shadow, weight * 0.40)
    )


def emboss(figure: str, *, depth: float = 0.32, light: str = "#FFFFFF",
           dark: str = "#7A705C", face: str | None = None) -> str:
    """Blind emboss: relief, not colour.

    `figure` is any SVG fragment; it is drawn three times — a light copy towards
    the light source (up-left), a dark copy away from it, and the figure itself
    on top. The offsets are deliberately small relative to the stroke weights,
    because an emboss that reads at arm's length is a drop shadow, and a drop
    shadow is the single clearest signal that a document was made in a browser.

    Uninked on purpose: `face=None` leaves the top copy as the caller drew it.
    Filling an emboss with metal turns a governance mark into a sticker.
    """
    def shifted(dx: float, dy: float, colour: str) -> str:
        recoloured = _recolour(figure, colour)
        return f'<g transform="translate({dx:.2f} {dy:.2f})">{recoloured}</g>'

    top = _recolour(figure, face) if face else figure
    return (
        "<g>"
        + shifted(depth, depth, dark)
        + shifted(-depth * 0.55, -depth * 0.55, light)
        + top
        + "</g>"
    )


def raised_type_css(metal: Metal, *, depth: float = 0.14) -> str:
    """CSS for display type that reads as raised foil.

    Two shadows, no blur: a highlight towards the light and the metal's shadow
    ink away from it. Blur is what makes a heading look like a games menu; a
    physical raised surface has an *edge*, and the edge is the whole effect.
    """
    return (
        f"color: {metal.face}; "
        f"text-shadow: -{depth:.2f}mm -{depth:.2f}mm 0 {metal.highlight}, "
        f"{depth:.2f}mm {depth:.2f}mm 0 {metal.shadow};"
    )


def _recolour(figure: str, colour: str) -> str:
    """Force every stroke and fill in a fragment to one ink.

    Used only by the emboss, where the three copies must be the same geometry in
    three tones. Deliberately blunt: it operates on the attribute text this
    package generates and is not a general SVG rewriter.
    """
    import re

    figure = re.sub(r'stroke="(?!none)[^"]*"', f'stroke="{colour}"', figure)
    return re.sub(r'fill="(?!none)[^"]*"', f'fill="{colour}"', figure)


# --- gold as a compositional system ------------------------------------------


@dataclass(frozen=True, slots=True)
class Scheme:
    """Five gold *roles*, so a plate never asks for "gold".

    Colouring existing lines gold produces yellow graphics. What produces metal
    is a hierarchy: one metal carries the ceremonial architecture and is the
    only one allowed to be large; a second carries the fine ornamental
    registers; a third is only ever a shadow or a relief wall; a fourth is
    reserved for the security ruling, where it must be pale enough to read as
    substrate rather than as decoration; a fifth carries heritage elements where
    a plate wants an older metal than its primary.

    Every drawing call in a masterpiece plate names a role. That is what makes
    the metals a system instead of a palette, and it is what stops the fine
    registers competing with the architecture — they are *different metals*, not
    the same metal at a different weight.
    """

    key: str
    #: The ceremonial architecture. Frame rules, cresting, seal rim, title mark.
    primary: Metal
    #: Fine ornamental registers. Interlace, spines, corner filigree.
    secondary: Metal
    #: Engraved shadow and relief. Never used as a face; only as a wall.
    engraved: Metal
    #: The security ruling and fine text. Pale by requirement, not by taste.
    security: Metal
    #: Heritage and ornament where the plate wants an older metal.
    heritage: Metal

    def role(self, name: str) -> Metal:
        try:
            return getattr(self, name)
        except AttributeError:
            raise ValueError(
                f"{name!r} is not a gold role. One of: primary, secondary, "
                "engraved, security, heritage"
            ) from None


#: The schemes the four finalists are built from. Each is a real decision about
#: how many foils a job buys and which surfaces get them, not a colourway.
SCHEMES: Final[dict[str, Scheme]] = {
    # Ivory and midnight. Royal gold does the architecture; champagne keeps the
    # fine registers from competing with it; deep gold is the wall.
    "imperial": Scheme(
        key="imperial",
        primary=METALS["royal"], secondary=METALS["champagne"],
        engraved=METALS["deep"], security=METALS["pale"],
        heritage=METALS["antique"],
    ),
    # Crimson mass. The primary has to hold against a saturated ground, so it is
    # deep rather than royal, and the security ruling goes pale to stay legible
    # as substrate on a dark field.
    "crimson": Scheme(
        key="crimson",
        primary=METALS["deep"], secondary=METALS["royal"],
        engraved=METALS["antique"], security=METALS["pale"],
        heritage=METALS["copper"],
    ),
    # The house scheme: royal gold against silver. Two metals that are not two
    # golds is what makes a two-pass job look like a two-pass job.
    "signature": Scheme(
        key="signature",
        primary=METALS["royal"], secondary=METALS["silver"],
        engraved=METALS["deep"], security=METALS["champagne"],
        heritage=METALS["antique"],
    ),
    # Navy and ivory, warmer throughout: antique carries the ornament so the
    # plate reads as an older instrument than the imperial scheme.
    "palace": Scheme(
        key="palace",
        primary=METALS["royal"], secondary=METALS["antique"],
        engraved=METALS["deep"], security=METALS["champagne"],
        heritage=METALS["brushed"],
    ),
}


def scheme_for(key: str) -> Scheme:
    if key not in SCHEMES:
        raise ValueError(
            f"{key!r} is not a gilding scheme. One of: " + ", ".join(sorted(SCHEMES))
        )
    return SCHEMES[key]
