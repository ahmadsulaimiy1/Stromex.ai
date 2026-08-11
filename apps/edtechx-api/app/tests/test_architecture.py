"""The frame architecture and the metals, checked as constructions.

A plate is judged by eye — that is what the contact sheet is for — but the
constructions underneath it are arithmetic, and arithmetic can be checked. What
these tests defend is the set of properties that a rendered PNG will not reveal
until it is on a press: that the octagon tiling is a tiling, that a stated arch
rise is the rise you get, that no metal treatment emits an opacity on a
hairline, and that the honesty ledger covers every treatment that exists.
"""

from __future__ import annotations

import itertools
import math
import re

import pytest

from app.modules.design import architecture as arch
from app.modules.design import geometry as geo
from app.modules.design.ceremony import LEVELS, budget_for
from app.modules.design.gilding import (
    METALS,
    SIMULATION,
    emboss,
    engraved_metal_rule,
    foil_gradient,
    metal_for,
    production_note,
    raised_type_css,
)

ROYAL = METALS["royal"]


# --- the metals --------------------------------------------------------------


def test_every_metal_has_a_four_stop_ramp_that_actually_descends():
    """Highlight → face → core → shadow must get darker, or it is not a metal.

    A palette whose "shadow" is lighter than its face reads as a colour with
    noise on it. This is the arithmetic behind the difference between gold and
    yellow.
    """
    for metal in METALS.values():
        luminance = [
            sum(int(colour[i:i + 2], 16) for i in (1, 3, 5))
            for colour in metal.ramp
        ]
        assert luminance == sorted(luminance, reverse=True), metal.key


def test_every_metal_names_a_physical_process_and_a_foil_reference():
    for metal in METALS.values():
        assert metal.process.strip(), metal.key
        assert metal.foil_reference.strip(), metal.key


def test_metal_for_refuses_an_unknown_key_and_lists_the_real_ones():
    with pytest.raises(ValueError) as raised:
        metal_for("shiny")
    assert "royal" in str(raised.value)


def test_the_honesty_ledger_covers_every_treatment_this_module_can_produce():
    """Every visual treatment has a ledger entry, and every entry states a limit.

    The rule is ASSERT → PROVE → ENDURE: a simulation that is not written down
    as a simulation becomes, over a few releases, a claim.
    """
    treatments = {"foil_gradient", "engraved_metal_rule", "emboss", "raised_type"}
    assert treatments <= set(SIMULATION)
    for name in treatments:
        what, limit = SIMULATION[name]
        assert what.strip() and limit.strip()
        assert name in production_note(name) or what[:20] in production_note(name)


def test_no_metal_treatment_puts_an_opacity_on_a_line():
    """The hairline rule from `geometry.py`, enforced on the metal treatments.

    A stroke with an opacity separates into a screen percentage and is the
    first thing to drop off press. Every pale tone must be a flat ink.
    """
    fragments = [
        engraved_metal_rule(0, 0, 50, 0, metal=ROYAL, weight=0.5),
        emboss(geo.khatam(10, 10, 5, ink="#000000", width=0.3)),
    ]
    for fragment in fragments:
        assert "opacity" not in fragment
        assert "stroke-opacity" not in fragment
        for colour in re.findall(r'stroke="([^"]+)"', fragment):
            assert colour == "none" or re.fullmatch(r"#[0-9A-Fa-f]{6}", colour)


def test_an_engraved_rule_is_three_strokes_in_three_of_the_metals_inks():
    fragment = engraved_metal_rule(0, 0, 40, 0, metal=ROYAL, weight=0.6)
    assert fragment.count("<line") == 3
    for colour in (ROYAL.highlight, ROYAL.face, ROYAL.shadow):
        assert colour in fragment


def test_foil_is_a_banded_ramp_rather_than_a_two_stop_gradient():
    """Foil returns to its highlight more than once; that is what reads as metal."""
    fragment = foil_gradient(ROYAL, "f", bands=2)
    assert fragment.count(f'stop-color="{ROYAL.highlight}"') == 2
    assert fragment.count("<stop") > 6


def test_raised_type_has_an_edge_and_never_a_blur():
    css = raised_type_css(ROYAL)
    assert ROYAL.highlight in css and ROYAL.shadow in css
    # Every shadow is `x y 0 colour` — a third value above zero is a blur, and a
    # blurred heading is the clearest signal a document was made in a browser.
    for offset in re.findall(r"(-?[\d.]+mm) (-?[\d.]+mm) ([\d.]+) ", css):
        assert offset[2] == "0"


# --- the tiling --------------------------------------------------------------


def test_the_octagon_lattice_is_a_real_tiling():
    """Regular octagons meet flat-to-flat when the pitch is twice the apothem.

    If this constant drifts the pattern becomes octagons scattered on a grid,
    which is what generic "Islamic-style" artwork looks like on inspection.
    """
    pitch = 10.0
    radius = pitch / arch._OCT
    apothem = radius * math.cos(math.pi / 8)
    assert apothem * 2 == pytest.approx(pitch)


def test_a_tessellation_band_clears_its_hollow():
    """A band must be a band: the clip has to carry the even-odd hole."""
    band = arch.tessellation_field(geo.Rect(0, 0, 100, 80), cell=8, ink="#B08D57",
                                   hollow=12.0)
    assert 'fill-rule="evenodd"' in band
    assert "clipPath" in band


def test_the_tiling_and_the_khatam_share_one_construction():
    """The star inside each octagon is the same figure the mark is drawn from."""
    field = arch.tessellation_field(geo.Rect(0, 0, 40, 40), cell=10,
                                    ink="#B08D57")
    assert field.count("M") > 10
    assert geo.INNER_RATIO == pytest.approx(math.sqrt(2 - math.sqrt(2)))


# --- the arch ----------------------------------------------------------------


@pytest.mark.parametrize("rise", [24.0, 44.0, 90.0, 140.0])
def test_a_stated_arch_rise_is_the_rise_you_get(rise):
    """`rise` inverts the two-centred construction, and the apex must land on it.

    A mihrab struck from its natural proportion is 131mm tall over a 237mm
    opening, which on a landscape sheet is a balloon. Stating the rise is how a
    landscape composition gets a canopy that is still a two-centred arch.
    """
    rect = geo.Rect(30, 20, 237, 150)
    path = arch.arch_niche_path(rect, rise=rise)
    apex = re.search(r"A[\d.]+ [\d.]+ 0 0 1 ([\d.]+) ([\d.]+)", path)
    assert apex is not None
    assert float(apex.group(1)) == pytest.approx(rect.cx, abs=0.02)
    assert float(apex.group(2)) == pytest.approx(rect.y, abs=0.02)
    springing = re.search(r"M[\d.]+ [\d.]+ V([\d.]+)", path)
    assert float(springing.group(1)) == pytest.approx(rect.y + rise, abs=0.02)


def test_the_arch_radius_satisfies_its_own_construction():
    """R = a + d, and the apex sits √(R² − d²) above the springing."""
    rect = geo.Rect(0, 0, 200, 150)
    rise = 40.0
    half = rect.w / 2
    d = (rise * rise - half * half) / (2 * half)
    radius = half + d
    assert math.sqrt(radius ** 2 - d ** 2) == pytest.approx(rise, abs=1e-6)
    assert f"A{radius:.2f}" in arch.arch_niche_path(rect, rise=rise)


# --- the corner --------------------------------------------------------------


def test_the_corner_bracket_has_one_mitre_and_not_two_steps():
    """Two changes of direction at the elbow read as a mis-registered plate.

    Found by looking at a render: the stepped profile produced a notch that
    looked like a printing fault at exactly the place a frame is most closely
    examined.
    """
    block = arch.corner_block(0, 0, 30, quadrant=0, mass="#4A1220",
                              metal=ROYAL, ink="#101826")
    outline = re.search(r'<path d="(M0 0 H[^"]+)"', block).group(1)
    # M, H, V, H, L, V, H, Z — the single L is the mitre.
    assert outline.count("L") == 1
    assert outline.count("V") == 2


def test_all_four_corners_are_one_shape_rotated():
    shapes = {
        re.search(r'<path d="(M0 0 H[^"]+)"',
                  arch.corner_block(0, 0, 30, quadrant=q, mass="#000",
                                    metal=ROYAL, ink="#000")).group(1)
        for q in range(4)
    }
    assert len(shapes) == 1


# --- registers ---------------------------------------------------------------


def test_register_stack_returns_the_rectangle_it_leaves():
    rect = geo.Rect(0, 0, 297, 210)
    _, inner = arch.register_stack(
        rect, ((0.5, "rule"), (4.0, "micro"), (1.0, "void")),
        metal=ROYAL, ink="#14294C",
    )
    assert inner.x == pytest.approx(5.5)
    assert inner.w == pytest.approx(297 - 11.0)


def test_an_unnamed_register_kind_is_refused_rather_than_ignored():
    with pytest.raises(ValueError):
        arch.register_stack(geo.Rect(0, 0, 100, 100), ((2.0, "sparkle"),),
                            metal=ROYAL, ink="#000000")


def test_a_legend_ring_fills_its_circumference_exactly():
    """No seam. The first render read "INSMERIDIAN INSTITUTE"."""
    ring = arch.legend_ring(50, 50, 12, metal=ROYAL, legend="MERIDIAN INSTITUTE",
                            identifier="PHD/2031/0007")
    length = float(re.search(r'textLength="([\d.]+)"', ring).group(1))
    assert length == pytest.approx(math.tau * 12 - 0.4, abs=0.01)
    assert 'lengthAdjust="spacing"' in ring


# --- the levels --------------------------------------------------------------


def test_each_level_permits_everything_the_level_above_it_does():
    for lower, higher in itertools.pairwise(LEVELS):
        assert lower.permits <= higher.permits, higher.name


def test_richness_increases_with_level():
    """More registers, more constructions, a stronger peak — in that order.

    This is the corrected reading of the ceremonial scale: what rises is
    architecture and ornament, not restraint. An earlier version had Level IV
    holding *more* air than Level III, which produced flagship plates that were
    exact and inexpensive.
    """
    assert [len(b.registers) for b in LEVELS] == sorted(
        len(b.registers) for b in LEVELS
    )
    assert [b.peak_ratio for b in LEVELS] == sorted(b.peak_ratio for b in LEVELS)
    assert [len(b.permits) for b in LEVELS] == sorted(len(b.permits) for b in LEVELS)


def test_the_content_ink_ceiling_is_a_legibility_floor_not_an_ornament_ban():
    """Level I forbids ink behind the words; every richer level allows a little.

    The ceiling exists so a guilloché never fights a recipient's name. It says
    nothing about the frame, where a Level IV plate is routinely dense.
    """
    assert budget_for(1).content_ink == 0.0
    assert 0 < budget_for(2).content_ink < budget_for(4).content_ink < 0.10


def test_only_the_ceremonial_levels_may_spend_a_second_metal():
    """A second foil is a second pass on press, so it is granted by level."""
    assert not budget_for(1).second_metal
    assert not budget_for(2).second_metal
    assert budget_for(3).second_metal and budget_for(4).second_metal


def test_there_is_no_global_whitespace_floor():
    """Deliberately absent — see the module docstring.

    Encoding air as a fraction of the sheet produced documents that were empty
    and passed. Air is judged by eye against a rendered plate.
    """
    assert not hasattr(budget_for(4), "whitespace_floor")


# --- blend -------------------------------------------------------------------


def test_blend_mixes_towards_the_ground_it_is_given():
    """`tint()` mixes towards ivory; on a midnight plate that is backwards."""
    midnight = "#0A1428"
    pale = geo.blend("#FFFFFF", midnight, 0.20)
    assert geo.blend("#FFFFFF", midnight, 0.0) == midnight.upper()
    assert geo.blend("#FFFFFF", midnight, 1.0) == "#FFFFFF"
    # Darker than the same request through `tint`, which is the whole point.
    assert int(pale[1:3], 16) < int(geo.tint("#FFFFFF", 0.20)[1:3], 16)
