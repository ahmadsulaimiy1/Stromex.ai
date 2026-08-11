"""The document geometry, pinned as construction rather than as appearance.

Each assertion below is a property a printer or a forger would care about, and
several of them exist because the reference implementation this vocabulary was
learned from had written down what breaking them costs.
"""

from __future__ import annotations

import math
import re

import pytest

from app.modules.design import geometry as g

SHEET = g.Rect(0, 0, 297, 210)
FIELD = SHEET.inset(18)


def _every_drawing() -> dict[str, str]:
    return {
        "rosette": g.rosette(148, 105, 90, ink="#0A101C", width=0.12, strength=0.06),
        "guilloche": g.guilloche_band(FIELD, ink="#0A101C"),
        "khatam": g.khatam(50, 50, 20, ink="#C9A961"),
        "squares": g.interlocking_squares(50, 50, 20, ink="#0A101C"),
        "lattice": g.lattice_field(FIELD, cell=24, ink="#0A101C"),
        "arabesque": g.arabesque_band(FIELD, ink="#C9A961"),
        "rule": g.engraved_rule(FIELD, ink="#C9A961"),
        "corner": g.corner_frame(10, 10, 22, ink="#C9A961"),
        "seal": g.seal_ring(60, 60, 16, ink="#0A101C", legend="EDIRASX", identifier="X"),
        "fibres": g.fibres(SHEET, seed="TR/2027/0001"),
        "screen": g.line_screen("s", degrees=8, pitch=0.42, width=0.07,
                                ink="#C9A961", strength=0.4),
        "microtext": g.microtext_ring(FIELD, identifier="m", text="TR/2027/0001 · ",
                                      ink="#0A101C"),
    }


@pytest.mark.parametrize("name", sorted(_every_drawing()))
def test_no_construction_ever_uses_an_opacity(name: str) -> None:
    """The rule that decides whether the hairlines exist on the printed sheet.

    A 0.1mm stroke at 40% opacity is a *screen percentage* at separation, and a
    screened hairline is the first thing to drop off press. Every pale tone in
    this module is mixed against the paper and emitted flat, and this is the
    test that keeps it that way when somebody reaches for the quick fix.
    """
    drawing = _every_drawing()[name]
    assert "opacity" not in drawing, f"{name} would print as a screen, not an ink"


@pytest.mark.parametrize("name", sorted(_every_drawing()))
def test_no_construction_ever_uses_a_raster_or_a_blur(name: str) -> None:
    """Vector throughout, or the plate has a resolution and the claim is false."""
    drawing = _every_drawing()[name]
    for forbidden in ("<image", "filter=", "feGaussian", "data:image"):
        assert forbidden not in drawing, f"{name} is not resolution-free"


def test_the_lathe_specifications_are_coprime() -> None:
    """Coprimality is the security property, not an aesthetic preference.

    A figure whose R and r share a factor closes early and repeats; one where
    they do not closes only after r turns, which is what a forger has to solve
    rather than trace.
    """
    for big, small, _pen in g.LATHE:
        assert math.gcd(big, small) == 1, f"{big}:{small} closes early"


def test_a_rosette_is_cut_at_the_same_grain_at_every_scale() -> None:
    """A fixed lobe count is a beautiful sheet field and an illegible medallion.

    The petal pitch at the outer radius is what a rose engine holds constant,
    so that is what the specification is chosen by. Asserted across two orders
    of magnitude because the failure only shows at the extremes.
    """
    for radius in (4, 12, 40, 110):
        wanted = (math.tau * radius) / 3.0
        chosen = min(g.LATHE, key=lambda spec: abs(spec[0] - wanted))
        pitch = (math.tau * radius) / chosen[0]
        assert 1.5 < pitch < 6.0, f"at {radius}mm the pitch is {pitch:.2f}mm"


def test_the_step_count_follows_the_lobe_count() -> None:
    """Otherwise a 61-lobe figure prints faceted at twenty-three points a petal."""
    coarse = g.epitrochoid(0, 0, 11, 2, 2.3)
    fine = g.epitrochoid(0, 0, 89, 9, 11.0)
    assert fine.count("L") > coarse.count("L") * 3


def test_the_eight_point_star_comes_from_the_two_square_construction() -> None:
    """√(2−√2), which is arithmetic. Anything else is a spiky asterisk."""
    assert g.INNER_RATIO == pytest.approx(0.7653668647301796)
    path = g.khatam(0, 0, 10, ink="#000000")
    radii = {
        round(math.hypot(float(x), float(y)), 3)
        for x, y in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", path)
    }
    assert radii == {10.0, round(10 * g.INNER_RATIO, 3)}


def test_a_plate_is_deterministic_and_keyed_to_its_own_document() -> None:
    """Two printings of one plate are one plate; two documents are two plates."""
    first = g.fibres(SHEET, seed="TR/2027/0001")
    assert first == g.fibres(SHEET, seed="TR/2027/0001")
    assert first != g.fibres(SHEET, seed="TR/2027/0002")


def test_microtext_carries_the_documents_own_serial() -> None:
    """A ring repeating the institution's name distinguishes nothing."""
    ring = g.microtext_ring(FIELD, identifier="m", text="TR/2027/0044 · ",
                            ink="#0A101C")
    assert ring.count("TR/2027/0044") > 20
    assert "<textPath" in ring


def test_an_engraved_rule_is_three_solid_strokes() -> None:
    """Lit edge, ink, shadow wall. One stroke with a gradient is a screen."""
    rule = g.engraved_rule(g.Rect(10, 10, 100, 50), ink="#C9A961")
    assert rule.count("<rect") == 3
    assert "url(#" not in rule


def test_a_seal_is_relief_and_never_a_fill() -> None:
    """An emboss is felt, not seen. Tinting one turns governance into a sticker."""
    seal = g.seal_ring(50, 50, 16, ink="#0A101C", legend="EDIRASX")
    assert 'fill="none"' in seal
    assert not re.search(r'<circle[^>]*fill="#', seal)


def test_a_line_screen_is_not_called_a_latent_image() -> None:
    """The honesty rule, asserted rather than trusted to a comment.

    A latent image needs two rulings at matched ink fraction with a shape
    between them. This is one ruling. Naming it latent would be a claim the
    construction cannot support, and this test fails if the name drifts.
    """
    source = (g.line_screen.__doc__ or "") + (g.__doc__ or "")
    assert "Not a latent image" in source
    assert "latent" not in g.line_screen("s", degrees=8, pitch=0.4, width=0.07,
                                         ink="#C9A961", strength=0.4)


def test_the_hairline_floor_is_held() -> None:
    """0.07mm is the practical screen floor; below it the ruling is a rumour."""
    screen = g.line_screen("s", degrees=8, pitch=0.4, width=0.01,
                           ink="#C9A961", strength=0.4)
    width = float(re.search(r'stroke-width="([\d.]+)"', screen).group(1))
    assert width >= 0.07


def test_a_quiet_tint_is_still_a_real_ink() -> None:
    assert g.tint("#0A101C", 1.0) == "#0A101C"
    quiet = g.tint("#0A101C", 0.05)
    assert quiet.startswith("#") and quiet != "#0A101C"
    # And it is nearer the paper than the ink, which is the whole point.
    assert int(quiet[1:3], 16) > 0xC0
