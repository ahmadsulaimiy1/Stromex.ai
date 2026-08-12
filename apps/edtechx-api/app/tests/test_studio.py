"""The studio gate, and the rule that an assistant proposes briefs not artwork."""

from __future__ import annotations

import inspect

import pytest

from app.modules.design import geometry as geo
from app.modules.design.gilding import scheme_for
from app.modules.design.heraldry import (
    Bay,
    bay,
    device_resolution_note,
    heraldic_register,
    seal_with_device,
)
from app.modules.design.signature import motif_for
from app.modules.design.studio import (
    SUGGESTIONS,
    AssistPort,
    Brief,
    BriefRejected,
    review,
)

SCHEME = scheme_for("imperial")
MOTIF = motif_for(institution="Meridian Institute", family="doctoral")
GOOD = SUGGESTIONS["imperial-islamic"]


def test_every_suggestion_passes_its_own_gate():
    """A starting point an institution cannot render is not a starting point."""
    for key, brief in SUGGESTIONS.items():
        assert review(brief) is brief, key


def test_a_ground_loud_enough_to_be_wallpaper_is_refused():
    with pytest.raises(BriefRejected) as raised:
        review(Brief(**{**vars_of(GOOD), "ground_strength": 0.40}))
    assert "wallpaper" in str(raised.value)


def test_level_one_refuses_ink_behind_the_words():
    """A statement of results that arrives on a worked ground is not trusted."""
    with pytest.raises(BriefRejected) as raised:
        review(Brief(**{**vars_of(GOOD), "level": 1, "scheme": "palace"}))
    assert "Level I permits no ink" in str(raised.value)


def test_a_second_metal_below_level_three_is_refused():
    """A second foil is a second pass and a second die, so it is priced by
    level — and it is an explicit choice, not something inferred from the
    scheme. Inferring it refused every Level I and II design, because every
    scheme names five metal roles."""
    with pytest.raises(BriefRejected) as raised:
        review(Brief(**{**vars_of(GOOD), "level": 2, "ground_strength": 0.02,
                        "second_metal": True}))
    assert "one foil pass" in str(raised.value)


def test_one_foil_at_level_two_is_fine():
    review(Brief(**{**vars_of(GOOD), "level": 2, "ground_strength": 0.02,
                    "second_metal": False}))


def test_an_order_that_does_not_tile_is_refused_with_the_reason():
    with pytest.raises(BriefRejected) as raised:
        review(Brief(**{**vars_of(GOOD), "motif_order": 7}))
    assert "does not tile" in str(raised.value)


def test_every_reason_is_reported_at_once():
    """An institution correcting a design should not find its mistakes one
    render at a time."""
    with pytest.raises(BriefRejected) as raised:
        review(Brief(**{**vars_of(GOOD), "ground": "nope", "scheme": "nope",
                        "language": "nope", "level": 9}))
    assert len(raised.value.reasons) >= 4


def test_type_may_not_be_set_in_the_colour_of_the_paper():
    with pytest.raises(BriefRejected) as raised:
        review(Brief(**{**vars_of(GOOD), "ink": GOOD.ground_colour}))
    assert "nothing printed on this sheet would be visible" in str(raised.value)


def test_ink_and_accent_may_coincide():
    """A two-colour scheme is a decision, not a missing register — EdirasX's
    own Imperial Islamic plate sets its text and its border mass in one
    midnight, and the first version of this gate refused it."""
    assert review(Brief(**{**vars_of(GOOD), "accent": GOOD.ink})) is not None


def test_a_brief_can_override_the_derived_order_and_stays_consistent():
    """Changing the order must recompute the density and the ratio with it —
    an 8-fold ratio on a 12-fold star is a cog, not a star."""
    twelve = Brief(**{**vars_of(GOOD), "motif_order": 12})
    motif = twelve.motif(institution="Meridian Institute", family="doctoral")
    assert motif.order == 12
    assert motif.density == 4
    assert motif.ratio == pytest.approx(0.7071, abs=0.001)


# --- the assistant contract ---------------------------------------------------


def test_an_assistant_can_only_hand_back_a_brief():
    """The signature is the enforcement: there is nowhere to put artwork."""
    signature = inspect.signature(AssistPort.propose)
    assert signature.return_annotation in ("Brief", Brief)
    assert set(signature.parameters) == {"self", "institution", "purpose", "wishes"}


def test_the_credential_layer_is_not_in_a_brief():
    """Identifiers, the verification panel and the seal's authority are not
    design decisions and an assistant has no business proposing them."""
    fields = set(vars_of(GOOD))
    for forbidden in ("document_id", "verification_code", "archive_reference",
                      "identity_number", "certificate_number", "serial",
                      "signature", "hmac"):
        assert forbidden not in fields


# --- heraldry -----------------------------------------------------------------


def test_an_unsupplied_bay_says_so_rather_than_drawing_a_placeholder():
    svg = bay(geo.Rect(0, 0, 15, 15), Bay("nation", "FEDERAL REPUBLIC"),
              scheme=SCHEME, ink="#0E1B33")
    assert "DEVICE NOT SUPPLIED" in svg
    assert "FEDERAL REPUBLIC" in svg


def test_a_supplied_device_is_mounted_inside_a_clear_zone():
    svg = bay(geo.Rect(0, 0, 20, 20), Bay("crest", "THE INSTITUTE",
                                          device="<circle r='40' cx='50' cy='50'/>"),
              scheme=SCHEME, ink="#0E1B33")
    assert "preserveAspectRatio=\"xMidYMid meet\"" in svg
    # 14% clear on each side of a 20mm bay leaves 14.4mm for the device.
    assert 'width="14.40"' in svg


def test_the_register_spaces_itself_for_any_count():
    for count in (2, 3, 4):
        bays = tuple(Bay(f"b{i}", f"AUTHORITY {i}") for i in range(count))
        svg = heraldic_register(geo.Rect(0, 0, 200, 15), bays, scheme=SCHEME,
                                ink="#0E1B33")
        assert svg.count("DEVICE NOT SUPPLIED") == count


def test_a_seal_without_a_device_uses_edirasxs_own_construction():
    """Not a claim to be anybody's arms — it is our geometry."""
    svg = seal_with_device(30, 30, 15, motif=MOTIF, scheme=SCHEME,
                           ink="#0E1B33", legend="MERIDIAN", identifier="X1")
    assert "MERIDIAN" in svg
    assert "<image" not in svg


def test_a_supplied_device_lands_in_the_seal_and_the_gold_stays_ours():
    svg = seal_with_device(30, 30, 15, motif=MOTIF, scheme=SCHEME,
                           ink="#0E1B33", legend="MERIDIAN", identifier="X1",
                           device="<rect width='100' height='100'/>")
    assert "<rect width='100' height='100'/>" in svg
    assert SCHEME.primary.face in svg


def test_the_bitmap_resolution_requirement_is_stated_not_discovered():
    note = device_resolution_note(22.0)
    assert "260 pixels" in note
    assert "520" in note
    assert "Vector" in note


def vars_of(brief: Brief) -> dict:
    return {name: getattr(brief, name) for name in (
        "ground", "ground_strength", "scheme", "level", "language",
        "ground_colour", "ink", "accent", "device_ref", "arms_left_ref",
        "arms_right_ref", "second_metal", "motif_order", "notes",
    )}
