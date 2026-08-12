"""Plain words to a premium brief — and the proof there is no cheap route out."""

from __future__ import annotations

import io
import itertools

import pytest

from app.modules.design.ceremony import budget_for
from app.modules.design.gilding import scheme_for
from app.modules.design.prompt import (
    PURPOSE_BASE,
    VOCABULARY,
    resolve,
    vocabulary_for,
)
from app.modules.design.signature_asset import (
    assess,
    signature_resolution_note,
    strip_background,
)
from app.modules.design.studio import review


def test_every_term_produces_a_brief_that_passes_the_gate():
    """A vocabulary entry that cannot be rendered is a broken promise."""
    for term in VOCABULARY:
        for purpose in PURPOSE_BASE:
            resolution = resolve(term.words[0], purpose=purpose)
            assert review(resolution.brief) is not None, (term.key, purpose)


def test_no_pair_of_terms_can_reach_an_unrenderable_design():
    """Combinations are where a vocabulary usually breaks. All of them are
    checked rather than a sample, because a registrar will find the one pair
    that was not."""
    for a, b in itertools.combinations(VOCABULARY, 2):
        resolution = resolve(f"{a.words[0]} {b.words[0]}", purpose="certificate")
        assert review(resolution.brief) is not None, (a.key, b.key)


@pytest.mark.parametrize("words", [
    "simple", "clean", "minimal", "plain", "modern", "corporate",
    "professional", "contemporary",
])
def test_asking_for_simple_does_not_produce_something_cheap(words):
    """The product rule, made structural: there is no flat option to reach.

    A person typing "minimal" gets the most restrained *premium* register —
    laid paper, one metal, engraved rules — and never a flat sheet, because a
    flat sheet is not in the vocabulary.
    """
    brief = resolve(words, purpose="certificate").brief
    assert brief.level >= 2
    assert brief.metals.primary.process, "a real metal, with a stated process"
    assert brief.field.suggested > 0, "a real ground construction"
    assert brief.ground_colour != brief.ink


def test_every_reachable_brief_carries_a_real_metal_and_a_real_level():
    for term in VOCABULARY:
        brief = resolve(term.words[0], purpose="doctoral").brief
        scheme = scheme_for(brief.scheme)
        assert len({scheme.primary.key, scheme.secondary.key,
                    scheme.engraved.key, scheme.security.key}) >= 3
        assert budget_for(brief.level).permits, "a level that permits something"


def test_the_purpose_decides_the_level_not_the_colour():
    """A certificate asked for in crimson is a Level III document in crimson,
    not a doctorate in crimson."""
    assert resolve("crimson", purpose="certificate").brief.level == 3
    assert resolve("crimson", purpose="doctoral").brief.level == 4
    assert resolve("crimson", purpose="report_card").brief.level == 1


def test_a_stated_level_beats_the_purpose():
    assert resolve("phd", purpose="report_card").brief.level == 4


def test_level_one_never_carries_ink_behind_the_words():
    """Whatever ground a character term chose."""
    brief = resolve("royal crimson damask report card", purpose="doctoral").brief
    assert brief.level == 1
    assert brief.ground_strength == 0.0
    assert brief.second_metal is False


def test_the_last_term_on_an_axis_wins():
    """"Midnight blue — actually crimson" does what a person means."""
    assert resolve("midnight blue, actually crimson").brief.accent == "#5A1226"


def test_an_empty_prompt_gives_the_purposes_own_premium_start():
    resolution = resolve("", purpose="doctoral")
    assert resolution.brief.level == 4
    assert "No design words recognised" in resolution.explanation


def test_unrecognised_design_words_are_reported_not_swallowed():
    """An institution that typed "letterpress" should be told it was ignored."""
    resolution = resolve("royal with letterpress and holograms")
    assert "letterpress" in resolution.unmatched
    assert "holograms" in resolution.unmatched
    assert "with" not in resolution.unmatched, "stopwords are not findings"


def test_every_matched_term_explains_itself():
    resolution = resolve("crimson, silver, arabic only, phd")
    assert len(resolution.matched) == 4
    for line in resolution.explanation.splitlines():
        assert line.startswith("· ") and len(line) > 20


def test_the_axes_are_all_reachable_from_the_studio():
    for kind in ("character", "ground", "metal", "language", "level", "geometry"):
        assert vocabulary_for(kind), kind


# --- signature preparation ----------------------------------------------------


def _capture(*, paper: int, ink: int, stroke: int = 30) -> bytes:
    """A synthetic capture: a light field with a dark mark on it."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (900, 300), (paper, paper, paper))
    draw = ImageDraw.Draw(image)
    draw.line([(120, 200), (300, 90), (480, 210), (700, 100)],
              fill=(ink, ink, ink), width=stroke)
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def test_a_good_capture_is_accepted():
    report = assess(_capture(paper=246, ink=20))
    assert report.usable, report.problems
    assert report.contrast > 40


def test_an_underexposed_capture_is_refused_with_something_to_do():
    report = assess(_capture(paper=90, ink=40))
    assert not report.usable
    assert any("brighter" in p for p in report.problems)


def test_a_low_contrast_capture_is_refused():
    report = assess(_capture(paper=200, ink=185))
    assert not report.usable
    assert any("too close in tone" in p for p in report.problems)


def test_a_small_capture_says_how_many_pixels_it_needed():
    from PIL import Image

    small = io.BytesIO()
    Image.new("RGB", (300, 120), (250, 250, 250)).save(small, format="PNG")
    report = assess(small.getvalue())
    assert any("710px" in p for p in report.problems)


def test_the_paper_becomes_transparent_and_the_ink_takes_the_documents_colour():
    from PIL import Image

    out = Image.open(io.BytesIO(
        strip_background(_capture(paper=246, ink=18), ink="#101826")))
    assert out.mode == "RGBA"
    pixels = out.load()
    # A corner is paper: fully transparent.
    assert pixels[0, 0][3] == 0
    # Somewhere on the stroke is opaque, and midnight rather than black.
    opaque = [
        pixels[x, y] for x in range(0, out.width, 7)
        for y in range(0, out.height, 7) if pixels[x, y][3] > 200
    ]
    assert opaque, "the stroke survived"
    assert opaque[0][:3] == (0x10, 0x18, 0x26)


def test_the_result_is_trimmed_to_the_strokes():
    """A signature photographed in the middle of an A4 sheet must not arrive as
    a mostly-empty image — that is how it ends up rendering at 4mm in a 60mm
    box."""
    trimmed = strip_background(_capture(paper=246, ink=18))
    loose = strip_background(_capture(paper=246, ink=18), trim=False)
    from PIL import Image

    assert Image.open(io.BytesIO(trimmed)).width < 900
    assert Image.open(io.BytesIO(loose)).width == 900


def test_a_softer_ramp_keeps_more_of_the_pens_antialiasing():
    """Tested on a graded field, because a hard-edged synthetic stroke has no
    antialiasing to preserve and would pass either way."""
    from PIL import Image

    graded = Image.linear_gradient("L").resize((256, 64))
    buffer = io.BytesIO()
    graded.convert("RGB").save(buffer, format="PNG")

    def partial(softness: float) -> int:
        data = strip_background(buffer.getvalue(), softness=softness, trim=False)
        alpha = Image.open(io.BytesIO(data)).getchannel("A").histogram()
        return sum(alpha[1:255])

    assert partial(0.90) > partial(0.05)


def test_the_resolution_verdict_is_stated_not_implied():
    assert "TOO SMALL" in signature_resolution_note(60, 300)
    assert "300 DPI" in signature_resolution_note(60, 800)
    assert "600 DPI" in signature_resolution_note(60, 1500)
