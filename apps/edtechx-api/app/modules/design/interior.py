"""The ceremonial field: architecture for the inside of the frame.

Everything built so far happens at the *edge*. Register stacks, corner blocks,
strapwork, the dissolving lattice — all of it is perimeter, and the perimeter is
where a plate is easiest to make impressive. The consequence was visible the
moment somebody looked at the four finalists side by side: the dark border was
doing all the work and the cream field inside it was a stack of centred prose on
blank paper. Prestigious, and not manufactured.

This file is the interior. Its subject is the thing a border cannot fix — what
happens in the 200 × 130mm where the words actually are.

**Four relationships it exists to establish.**

*Corner to centre.* A field with small engraved brackets at its own corners,
struck from the same family as the plate's corner blocks, reads as an inner
architecture rather than as leftover space. The relationship between the two
scales is what makes a sheet feel composed at both.

*Ground beneath tone.* A lathe field at two per cent above the paper, inside the
content area, is the difference between cream paper and a security substrate
that happens to be cream. It is not seen; it is the reason the field does not
look empty. The ink ceiling in `ceremony.Budget.content_ink` is what keeps it
underneath the words rather than behind them.

*Title architecture.* A conferral line set in letterspaced sans on blank paper
is a caption. The same words between two engraved rules with the family's
medallion at each terminal is a *register* — and registers are what ceremonial
documents are built from.

*Execution as architecture.* Three rules and three names is a form. A spanning
engraved rule, an axis medallion, the signatures hung beneath it and the seal
anchoring one end is an execution band — the part of the document that carries
its authority, composed as though it did.

**Everything here is gated on the ceremonial level.** A routine completion
certificate gets an elegant field and none of this; a doctorate gets all of it.
That is the point of having levels at all, and it is why each function takes a
`Budget` and returns an empty string when the level does not permit it — the
caller does not branch, and a Level I plate cannot accidentally acquire a
cartouche because somebody copied a template.
"""

from __future__ import annotations

from app.modules.design import geometry as geo
from app.modules.design.architecture import spreader
from app.modules.design.ceremony import Budget
from app.modules.design.gilding import Scheme, engraved_metal_rule
from app.modules.design.signature import Motif

__all__ = [
    "execution_rule",
    "field_ground",
    "interior_corners",
    "name_cartouche_path",
    "title_register",
]


def field_ground(rect: geo.Rect, *, motif: Motif, scheme: Scheme,
                 budget: Budget, ink: str) -> str:
    """A lathe field beneath the content, under the level's ink ceiling.

    Held at a fraction of `budget.content_ink` rather than at it: the ceiling is
    the point at which a background starts to fight the words, and a ground
    should sit well below the point at which it starts to fight rather than just
    underneath it. At Level I the ceiling is zero and this draws nothing, which
    is the correct behaviour for a statement of results.
    """
    if budget.content_ink <= 0 or "guilloche" not in budget.permits:
        return ""
    strength = budget.content_ink * 0.55
    radius = max(rect.w, rect.h) * 0.62
    return (
        motif.guilloche(rect.cx, rect.cy, radius, ink=ink, width=0.07,
                        strength=strength, passes=3)
        + motif.guilloche(rect.cx, rect.cy, radius * 0.58, ink=scheme.security.core,
                          width=0.07, strength=strength * 1.15, passes=2)
    )


def interior_corners(rect: geo.Rect, *, motif: Motif, scheme: Scheme,
                     budget: Budget, size: float = 11.0) -> str:
    """Engraved brackets at the content field's own corners.

    The corner-to-centre relationship, made explicit. Each bracket is two fine
    rules and one member of the family at the elbow — small enough to be
    discovered at 20cm rather than announced at a metre, and struck from the
    same construction as the corner blocks at the trim, so the eye reads the
    sheet as one object seen at two scales.
    """
    if "corner" not in budget.permits:
        return ""
    metal = scheme.secondary
    out: list[str] = []
    for quadrant, (x, y) in enumerate((
        (rect.x, rect.y), (rect.x + rect.w, rect.y),
        (rect.x + rect.w, rect.y + rect.h), (rect.x, rect.y + rect.h),
    )):
        out.append(
            f'<g transform="translate({x:.2f} {y:.2f}) rotate({quadrant * 90})">'
            + engraved_metal_rule(0, 0, size, 0, metal=metal, weight=0.26)
            + engraved_metal_rule(0, 0, 0, size, metal=metal, weight=0.26)
            + engraved_metal_rule(2.4, 2.4, size * 0.62, 2.4, metal=metal,
                                  weight=0.14)
            + engraved_metal_rule(2.4, 2.4, 2.4, size * 0.62, metal=metal,
                                  weight=0.14)
            + motif.star(size * 0.30, size * 0.30, 1.9, ink=metal.face,
                         width=0.16, sharpen=0.88)
            + "</g>"
        )
    return "".join(out)


def title_register(width: float, height: float, *, motif: Motif,
                   scheme: Scheme, budget: Budget) -> str:
    """The band a conferral or a distinction is set *into*, not on.

    Two engraved rules the full measure, a medallion of the family at each
    terminal, and lozenge stops between. Drawn in its own box so it can sit in
    the flow behind the words rather than at a coordinate the words are free to
    move away from.

    Returns a complete `<svg>` sized in millimetres, because the caller places
    it with CSS and the two must not disagree about the unit.
    """
    if "spreader" not in budget.permits:
        return ""
    metal = scheme.secondary
    mid = height / 2
    inset = height * 0.92
    body = (
        spreader(mid, inset, width - inset, metal=metal, stops=2)
        + motif.rosette(inset * 0.5, mid, height * 0.34, ink=metal.face,
                        width=0.14)
        + motif.rosette(width - inset * 0.5, mid, height * 0.34,
                        ink=metal.face, width=0.14)
    )
    return (
        f'<svg class="titleband" viewBox="0 0 {width:.1f} {height:.1f}"'
        ' preserveAspectRatio="none" aria-hidden="true">' + body + "</svg>"
    )


def name_cartouche_path(rect: geo.Rect, *, motif: Motif, scheme: Scheme,
                        budget: Budget, paper: str) -> str:
    """An engraved cartouche for the peak: panel, double rule, corner family.

    The recipient's name is the one element on the sheet that is *about* a
    person, and mounting it rather than printing it is the oldest way a document
    says so. The panel is cut at the corners, double-ruled in two metals, and
    carries a member of the family at each cut — the same figure as the field's
    brackets, one size up.

    Returns the SVG body for a viewBox of `rect`; the caller wraps it.
    """
    if "cartouche" not in budget.permits:
        return ""
    from app.modules.design.architecture import cartouche_path

    outline = cartouche_path(rect, arch=rect.h * 0.16, cut=rect.h * 0.30)
    inner = cartouche_path(rect.inset(1.4), arch=rect.h * 0.14,
                           cut=rect.h * 0.26)
    corners = "".join(
        motif.star(x, y, 1.7, ink=scheme.primary.face, width=0.16,
                   sharpen=0.86)
        for x, y in (
            (rect.x + rect.h * 0.30, rect.y),
            (rect.x + rect.w - rect.h * 0.30, rect.y),
            (rect.x + rect.h * 0.30, rect.y + rect.h),
            (rect.x + rect.w - rect.h * 0.30, rect.y + rect.h),
        )
    )
    return (
        f'<path d="{outline}" fill="{paper}" stroke="{scheme.primary.face}"'
        ' stroke-width="0.55"/>'
        f'<path d="{inner}" fill="none" stroke="{scheme.engraved.shadow}"'
        ' stroke-width="0.18"/>' + corners
    )


def execution_rule(width: float, height: float, *, motif: Motif,
                   scheme: Scheme, budget: Budget) -> str:
    """The rule the signatures hang from, with the family on its axis.

    An execution band that begins with a full-measure engraved rule and a
    medallion on the axis reads as the part of the document that confers.
    Without it, three names over three short rules is a form somebody filled in.
    """
    if "medallion" not in budget.permits:
        return ""
    metal = scheme.primary
    mid = height * 0.44
    gap = height * 1.15
    body = (
        engraved_metal_rule(0, mid, width / 2 - gap, mid, metal=metal,
                            weight=0.34)
        + engraved_metal_rule(width / 2 + gap, mid, width, mid, metal=metal,
                              weight=0.34)
        + motif.rosette(width / 2, mid, height * 0.40, ink=metal.face,
                        width=0.16)
        + motif.medallion_ring(width / 2, mid, height * 0.52,
                               ink=scheme.secondary.face, width=0.10)
    )
    return (
        f'<svg class="execrule" viewBox="0 0 {width:.1f} {height:.1f}"'
        ' preserveAspectRatio="none" aria-hidden="true">' + body + "</svg>"
    )
