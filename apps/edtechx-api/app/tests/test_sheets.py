"""Sheet sizes: whether a document fits one, and what happens when it does not.

A sheet size is a brief, not a scale factor, and everything asserted here is
about the difference. The catalogue must hold real stocks at real millimetres;
the band architecture must agree with the ground that actually draws it; a
composition must be *refused* on a sheet that cannot carry it rather than
squeezed onto it; and the refusal must carry the arithmetic, because "does not
fit" without a number is an opinion.
"""

from __future__ import annotations

import pytest

from app.modules.design.heritage import Bands
from app.modules.design.sheets import (
    FLOORS,
    SHEETS,
    fits,
    rotate,
    sheet_for,
    sheets_in,
    usable_sheets,
)
from app.modules.documents.library import TEMPLATES, fill, template_for
from app.modules.documents.library_sheet import SheetTooSmall, sheet_for_template


def test_the_catalogue_holds_both_orientations_of_every_stock():
    stems = {key.rsplit("-", 1)[0] for key in SHEETS}
    for stem in stems:
        assert f"{stem}-portrait" in SHEETS
        assert f"{stem}-landscape" in SHEETS
    assert len(SHEETS) == len(stems) * 2


@pytest.mark.parametrize("key,width,height", [
    ("a4-portrait", 210.0, 297.0),
    ("a3-landscape", 420.0, 297.0),
    ("letter-portrait", 215.9, 279.4),
    ("legal-portrait", 215.9, 355.6),
    ("tabloid-landscape", 431.8, 279.4),
    ("b5-portrait", 176.0, 250.0),
])
def test_the_stocks_are_the_real_dimensions(key, width, height):
    """Letter is not A4 and Legal is not Letter. Pretending crops a foot off."""
    sheet = sheet_for(key)
    assert (sheet.width, sheet.height) == (width, height)


def test_rotating_a_sheet_gives_the_other_composition_not_a_transform():
    landscape = sheet_for("a4-landscape")
    portrait = rotate(landscape)
    assert portrait.key == "a4-portrait"
    assert rotate(portrait) is landscape
    assert portrait.short == landscape.short


def test_every_sheet_belongs_to_a_named_series():
    for sheet in SHEETS.values():
        assert sheet.series in {"iso-a", "iso-b", "north-american"}
    assert len(sheets_in("iso-a")) == 8   # A3–A6, both ways
    assert len(sheets_in("iso-b")) == 4


def test_the_fit_field_agrees_with_the_ground_that_actually_draws_it():
    """Two modules compute the field. They must not drift apart.

    `sheets.fits` answers without constructing a ground, which is what lets a
    catalogue page say which sizes a document offers. That shortcut is only
    safe while the arithmetic matches `heritage.Bands`, so it is asserted
    rather than trusted.
    """
    for key in ("a4-landscape", "a3-portrait", "letter-landscape", "b5-portrait"):
        sheet = sheet_for(key)
        for weight in (1.0, 0.86, 0.74):
            verdict = fits(family="stage", sheet=sheet, border_weight=weight)
            bands = Bands.for_sheet(sheet.width, sheet.height, weight=weight)
            expected = sheet.width - (bands.rule_inner + sheet.short * 0.012) * 2
            assert verdict.field_width == pytest.approx(expected, abs=0.01)


def test_a_sheet_too_small_for_the_instruments_is_refused_with_numbers():
    verdict = fits(family="stage", sheet=sheet_for("a6-landscape"))
    assert not verdict.ok
    assert verdict.reasons
    # Every reason names a measurement. A refusal without one is an opinion.
    assert any(any(ch.isdigit() for ch in reason) for reason in verdict.reasons)


def test_the_refusal_is_about_the_instruments_not_about_taste():
    """The foot is the binding constraint, and it is the part that cannot shrink."""
    verdict = fits(family="stage", sheet=sheet_for("a5-landscape"))
    assert not verdict.ok
    joined = " ".join(verdict.reasons)
    assert "verification panel" in joined or "Code 128" in joined \
        or "execution row" in joined or "foot" in joined


def test_a4_portrait_and_both_a3s_carry_every_family():
    for family in ("stage", "college", "record", "ledger", "award"):
        for key in ("a4-portrait", "a3-portrait", "a3-landscape"):
            assert fits(family=family, sheet=sheet_for(key),
                        border_weight=0.74).ok, (family, key)


def test_a_ledger_does_not_fit_a4_landscape_and_says_why():
    """The one honest gap in A4, and it is a gap for a reason.

    A transcript is a portrait document. Turned on its side, A4 leaves 151mm of
    height for a masthead, a holder block, a results table, an end-of-record
    rule, a grading key and a 27mm verification instrument — and the measured
    content column is 154.5mm. The three millimetres are not negotiable at the
    bottom of the sheet, because the bottom of the sheet is the panel.
    """
    verdict = fits(family="ledger", sheet=sheet_for("a4-landscape"),
                   border_weight=0.74)
    assert not verdict.ok
    assert "151mm tall" in verdict.reasons[0]
    # ...and the same document on A4 portrait is fine, which is the point.
    assert fits(family="ledger", sheet=sheet_for("a4-portrait"),
                border_weight=0.74).ok


def test_type_grows_with_the_sheet_but_sublinearly():
    """A3 type is bigger than A4 type, and not twice as big."""
    small = fits(family="stage", sheet=sheet_for("a4-landscape"),
                 border_weight=0.86)
    large = fits(family="stage", sheet=sheet_for("a3-landscape"),
                 border_weight=0.86)
    assert large.type_scale > small.type_scale
    assert large.type_scale < small.type_scale * (
        large.field_height / small.field_height
    )


def test_the_type_scale_is_clamped_at_both_ends():
    for sheet in SHEETS.values():
        for family in ("stage", "record", "ledger", "award", "college"):
            verdict = fits(family=family, sheet=sheet, border_weight=0.74)
            assert 0.72 <= verdict.type_scale <= 1.45


def test_every_template_offers_more_than_one_size():
    for template in TEMPLATES.values():
        offered = template.sheets()
        assert len(offered) >= 8, (template.key, offered)
        assert template.sheet in offered, template.key


def test_a5_and_a6_are_offered_by_nobody():
    """Not an oversight — the arithmetic refuses them, and it should."""
    for template in TEMPLATES.values():
        offered = set(template.sheets())
        assert not offered & {"a5-portrait", "a5-landscape",
                              "a6-portrait", "a6-landscape",
                              "half-letter-portrait", "half-letter-landscape"}


def test_rendering_on_a_refused_sheet_raises_rather_than_shrinking():
    template = template_for("stage-primary")
    with pytest.raises(SheetTooSmall) as caught:
        sheet_for_template(fill(template, {}), sheet="a6-portrait")
    message = str(caught.value)
    assert "A6" in message
    # The exception has to be actionable: it names the sizes that do work.
    assert "a4-landscape" in message


@pytest.mark.parametrize("key", ["a4-landscape", "a3-landscape",
                                 "letter-landscape", "b5-portrait"])
def test_a_template_renders_on_every_size_it_claims(key):
    template = template_for("stage-primary")
    if key not in template.sheets():
        pytest.skip(f"{template.key} does not offer {key}")
    built = sheet_for_template(fill(template, {}), sheet=key)
    assert built.sheet.key == key
    assert built.width == sheet_for(key).width
    assert built.field.w < built.width


def test_usable_sheets_are_ordered_largest_first():
    good = usable_sheets("stage", border_weight=0.86)
    areas = [sheet.area_cm2 for sheet in good]
    assert areas == sorted(areas, reverse=True)


def test_the_floors_are_documented_physical_limits_not_round_numbers():
    """Each floor is a property of a press, a scanner or an eye."""
    assert FLOORS["panel_height"] == 27.0    # the cartouche's own contents
    assert FLOORS["seal"] >= 18.0            # a legend ring at 600 DPI
    assert FLOORS["body"] >= 1.8             # readable serif at arm's length


def test_a_measured_overflow_overrides_the_arithmetic():
    """The proof wins over the prediction, and says so.

    A linear model cannot see a line wrap: a citation that sets on one line at
    ×1.00 takes two at ×1.02, and the column jumps 7mm for a 2 % change in
    scale. Where the audit caught that, the size is refused by measurement even
    though the arithmetic accepts it — and the refusal names the millimetres.
    """
    from app.modules.documents.library import MEASURED_OVERFLOWS

    assert MEASURED_OVERFLOWS, "the audit's findings must not be silently dropped"
    for (key, sheet_key), reason in MEASURED_OVERFLOWS.items():
        template = template_for(key)
        # The arithmetic accepts it — that is the whole point of the record.
        assert fits(family=template.family, sheet=sheet_for(sheet_key),
                    border_weight=template.border_weight).ok, (key, sheet_key)
        assert sheet_key not in template.sheets()
        assert "mm over" in reason
        with pytest.raises(SheetTooSmall) as caught:
            sheet_for_template(fill(template, _values(template)),
                               sheet=sheet_key)
        assert "the proof wins" in str(caught.value)


def _values(template):
    supplied = {
        "testimonial_text": "x", "clearance_rows": "A|B|C|D",
        "register_rows": "1|A|B|C|D", "rows": "2025|Arabic|3|82|A",
        "citation": "For excellence.",
    }
    return {k: v for k, v in supplied.items() if k in template.slot_keys}
