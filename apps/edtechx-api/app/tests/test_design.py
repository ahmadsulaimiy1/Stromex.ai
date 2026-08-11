"""The design system, tested where a test can actually help.

Most of a visual language is judged by looking at it, and the review that
produced this file is in `tools/design` and `docs/edtechx/design/shots`. What
follows are the parts that *can* be asserted, and they are the parts that fail
silently: geometry that is subtly wrong, a token nobody reads, a colour pairing
that would fail an audit, an institution's theme quietly breaking its own
readability, and markup contracts that a screenshot only catches by luck.

Every test here corresponds to something the design review actually found.
"""

from __future__ import annotations

import math
import re

import pytest

from app.modules.design import components as ui
from app.modules.design import contrast as ink
from app.modules.design import ornament
from app.modules.design.foundation import FOUNDATION, page_css
from app.modules.design.theme import (
    ThemeError,
    css_variables,
    resolve,
    review,
    stylesheet,
)
from app.modules.design.tokens import PRIMITIVES, SEMANTICS, ThemeShape

# --- geometry ---------------------------------------------------------------


def test_the_seal_is_the_two_square_construction() -> None:
    """The inner radius is derived, not chosen — and was once wrong.

    Square A's edge from (R,0) to (0,R) is x + y = R; square B's edge is
    y = R/√2. They cross at √(2−√2)·R. The mark shipped briefly at 1/(1+√2),
    which renders as a spiky asterisk rather than as a seal, and looked like a
    decorative starburst everywhere the identity appears.
    """
    assert ornament.INNER_RATIO == pytest.approx(math.sqrt(2 - math.sqrt(2)))
    assert ornament.INNER_RATIO == pytest.approx(0.7653668, abs=1e-6)
    assert ornament.INNER_RATIO > 0.7, "broad points are what make it a seal"


def test_every_ornament_derives_from_one_construction() -> None:
    """A mark, a node, a lattice and a spinner drawn separately read as a
    moodboard. These all come from `star_points`, at different scales."""
    points = ornament.star_points(50, 50, 20)
    assert len(points) == 16
    radii = [math.hypot(x - 50, y - 50) for x, y in points]
    outer, inner = radii[0::2], radii[1::2]
    assert all(r == pytest.approx(20) for r in outer)
    assert all(r == pytest.approx(20 * ornament.INNER_RATIO) for r in inner)


def test_the_marks_render_as_valid_self_contained_svg() -> None:
    for markup in (
        ornament.node(8), ornament.rule(), ornament.monogram(48),
        ornament.lattice(), ornament.corner(30), ornament.spinner(20),
    ):
        assert markup.count("<svg") == markup.count("</svg>")
        assert "http" not in markup, "an ornament must not fetch anything"
        assert "NaN" not in markup


def test_the_monogram_holds_the_x_in_the_seals_own_vertices() -> None:
    """The X is drawn between opposite inner vertices — a line the construction
    already contains — rather than placed in the middle of it."""
    markup = ornament.monogram(100)
    vertices = ornament.star_points(50, 50, 47.0, rotation=22.5)
    inner = [v for index, v in enumerate(vertices) if index % 2 == 1]
    for a, b in ((0, 4), (2, 6)):
        assert f"M {inner[a][0]:.3f} {inner[a][1]:.3f}" in markup
        assert f"L {inner[b][0]:.3f} {inner[b][1]:.3f}" in markup


# --- tokens -----------------------------------------------------------------


def test_no_component_names_a_colour() -> None:
    """The mechanism the whole customization promise rests on.

    A single literal `#1A3566` in a component is a colour an institution's theme
    cannot move, and it will be the one on the page they care about.
    """
    stylesheets = FOUNDATION + page_css()
    literals = re.findall(r"#[0-9a-fA-F]{3,8}\b", stylesheets)
    assert not literals, (
        "the foundation stylesheet names colours directly: " + ", ".join(sorted(set(literals)))
    )
    rgba = re.findall(r"rgba?\((?!\s*var)[^)]*\)", stylesheets)
    # One exception, stated rather than hidden: the modal scrim is a black at a
    # fixed alpha and is not an institution's decision.
    assert [value for value in rgba if "6, 10, 18" not in value] == []


def test_the_system_has_no_decorative_gradient_and_one_shadow() -> None:
    """Restraint, asserted.

    A gradient is how software manufactures the impression of depth it has not
    earned through hierarchy, and a stack of shadows is how it manufactures
    importance. Two gradients survive and both are *mechanisms* rather than
    decoration: the select chevron, which is the standard two-gradient arrow,
    and the loading shimmer, which is the animation itself. Anything else
    appearing here is a decision somebody has to defend.
    """
    blocks = re.findall(r"([^{}]+)\{([^{}]*)\}", FOUNDATION + page_css())
    decorated = sorted({
        selector.strip().splitlines()[-1].strip()
        for selector, body in blocks if "gradient(" in body
    })
    assert decorated == [".ed-select", ".ed-skeleton"], decorated

    shadows = {
        name for name, value in PRIMITIVES["shadow"].items()
        if value != "none" and not value.startswith("0 0 0")
    }
    assert shadows == {"overlay", "raised"}


def test_radii_stay_institutional() -> None:
    """2–4px reads as institutional; 16px reads as a consumer app. `full` exists
    for avatars and nothing else."""
    for step, value in PRIMITIVES["radius"].items():
        if step in ("none", "full"):
            continue
        assert int(value.removesuffix("px")) <= 4, f"radius.{step} is {value}"


def test_every_semantic_role_exists_in_both_modes() -> None:
    """A component reaching for a token that one mode lacks renders untinted
    text on an untinted background, and only in that mode."""
    assert set(SEMANTICS["ivory"]) == set(SEMANTICS["midnight"])


def test_every_semantic_reference_resolves() -> None:
    theme = resolve()
    for role, value in theme.roles.items():
        assert value.startswith("#"), f"{role} did not resolve to a colour"
        ink.parse(value)


def test_the_emitted_stylesheet_covers_every_variable_the_foundation_reads() -> None:
    """The failure this catches is invisible: an undefined custom property makes
    a rule *do nothing*, so a page renders looking almost right."""
    declared = set(css_variables(resolve()))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", FOUNDATION + page_css()))
    # Locals a component defines for itself.
    local = {"--btn-bg", "--btn-fg", "--btn-border", "--rule-width"}
    missing = used - declared - local
    assert not missing, f"the foundation reads undeclared tokens: {sorted(missing)}"


# --- guardrails -------------------------------------------------------------


def test_the_edirasx_theme_passes_its_own_accessibility_review() -> None:
    verdict = review(resolve())
    assert verdict.is_publishable, "\n".join(v.message for v in verdict.errors)


def test_a_pale_gold_on_ivory_is_refused_with_a_remedy() -> None:
    """The failure a customizable product invites, and the sentence that makes
    EdirasX intelligent rather than merely configurable."""
    pale = ink.check("Gold text", "#E3CE9B", "#FAF6EE")
    assert pale.severity == "error"
    assert pale.suggestion is not None
    assert ink.contrast(pale.suggestion, "#FAF6EE") >= ink.AA_NORMAL
    assert "nearest tone" in pale.message


def test_a_suggestion_is_recognisably_the_colour_that_was_chosen() -> None:
    """Darkening a champagne must produce a darker champagne, not a brown."""
    suggestion = ink.nearest_accessible("#E3CE9B", "#FAF6EE")
    r, _g, b = ink.parse(suggestion)
    assert r > b, "the suggestion lost the warmth of the colour it came from"


def test_a_background_that_cannot_work_says_so() -> None:
    """On a mid-grey nothing reaches 4.5:1, and the honest answer names the
    background rather than blaming the colour."""
    verdict = ink.check("Body text", "#808080", "#7F7F7F")
    assert verdict.severity == "error"
    assert verdict.suggestion is None
    assert "background is the problem" in verdict.message


def test_an_institutions_choices_are_judged_not_silently_corrected() -> None:
    """A school that finds its brand quietly changed will trust nothing else the
    product tells it. Resolution obeys; review reports."""
    theme = resolve({"primitives": {"gold": {"700": "#F0E6C8"}}})
    assert theme.colour("text.gold") == "#F0E6C8"
    verdict = review(theme)
    assert not verdict.is_publishable
    assert any("Gold text" in v.role for v in verdict.errors)


def test_a_theme_may_only_change_what_a_theme_may_change() -> None:
    """The schema an AI Design Studio is eventually handed. It emits validated
    token overrides, never CSS."""
    with pytest.raises(ThemeError):
        resolve({"primitives": {"verdant": {"600": "#000000"}}})
    with pytest.raises(ThemeError):
        resolve({"primitives": {"gold": {"999": "#000000"}}})
    with pytest.raises(ThemeError):
        resolve({"roles": {"text.primary": "gold.500"}})
    with pytest.raises(ThemeError):
        resolve({"mode": "neon"})
    with pytest.raises(ThemeError):
        resolve({"families": {"handwriting": "Comic Sans"}})
    with pytest.raises(ink.ColourError):
        resolve({"primitives": {"royal": {"600": "octarine"}}})


def test_every_open_ramp_and_role_is_real() -> None:
    for ramp in ThemeShape.OPEN_RAMPS:
        assert ramp in PRIMITIVES
    for role in ThemeShape.OPEN_ROLES:
        assert role in SEMANTICS["ivory"]


def test_density_rescales_the_whole_spacing_scale() -> None:
    """One institutional setting, not a density argument on every component."""
    compact = css_variables(resolve({"density": "compact"}))
    roomy = css_variables(resolve({"density": "comfortable"}))
    assert float(compact["--space-6"][:-3]) < float(roomy["--space-6"][:-3])
    assert compact["--control-height"] != roomy["--control-height"]


# --- component contracts ----------------------------------------------------


def test_a_caller_can_add_a_class_without_losing_the_components_own() -> None:
    """Emitting two `class` attributes silently drops the second, which is how a
    hamburger ended up visible on a 1440px desktop. No assertion noticed; a
    screenshot did."""
    markup = ui.button("Menu", variant="quiet", class_="ed-mobile-only")
    assert markup.count("class=") == 1
    assert "ed-btn" in markup and "ed-mobile-only" in markup


def test_a_loading_button_actually_reads_as_loading() -> None:
    """`data_loading=""` was dropped by the attribute filter, so the label stayed
    visible beside the spinner."""
    assert 'data-loading="true"' in ui.button("Publishing", loading=True)
    assert "ed-spinner" in ui.button("Publishing", loading=True)


def test_every_data_shape_carries_its_column_headings_into_the_stack() -> None:
    """The small-screen composition is generated from the same markup, so it
    cannot drift from a second template."""
    markup = ui.data_table(
        [("Year", "text"), ("Programme", "text")],
        [("2026/27", "BSc Computer Science")],
        shape="ledger",
    )
    assert 'data-shape="ledger"' in markup
    assert 'data-label="Year"' in markup
    assert 'data-label="Programme"' in markup


def test_a_results_row_names_the_part_the_phone_promotes() -> None:
    row = ui.matrix_row(subject="Chemistry", grade="A",
                        details=[("Mark", "82 / 100")], note="Good work.")
    for role in ("subject", "detail", "grade", "note"):
        assert f'data-role="{role}"' in row


def test_a_table_with_no_rows_becomes_an_empty_state_rather_than_a_header() -> None:
    markup = ui.data_table([("Course", "text")], [], shape="matrix")
    assert "ed-empty" in markup
    assert "<table" not in markup


def test_the_empty_state_says_what_the_place_is_for() -> None:
    """"No data" teaches a person they have done something wrong (ADR-031)."""
    markup = ui.empty("No programmes yet",
                      "A programme is what a student is admitted to.",
                      action=ui.button("Create a programme"))
    assert "No programmes yet" in markup
    assert "admitted to" in markup
    assert "ed-btn" in markup


def test_user_supplied_text_is_escaped_everywhere() -> None:
    hostile = "<script>alert(1)</script>"
    for markup in (
        ui.badge(hostile), ui.avatar(hostile), ui.button(hostile),
        ui.field(hostile, ui.text_input(value=hostile)),
        ui.empty(hostile, hostile),
        ui.data_table([("A", "text")], [(ui.e(hostile),)], shape="ledger"),
    ):
        assert "<script>" not in markup


def test_the_disabled_and_focus_states_exist_for_every_control() -> None:
    """Declared rather than discovered: a control shipped without a disabled
    treatment gets one that looks like an enabled one."""
    for selector in (
        ".ed-btn[disabled]", ".ed-btn:focus-visible",
        ".ed-input:focus", ".ed-input[disabled]",
        ".ed-check input:focus-visible", ".ed-switch input:focus-visible",
        ".ed-tab:focus-visible", ".ed-link:focus-visible",
    ):
        assert selector in FOUNDATION, f"{selector} has no treatment"


def test_motion_yields_to_a_person_who_asked_for_less() -> None:
    assert "prefers-reduced-motion" in FOUNDATION


def test_a_keyboard_user_can_skip_the_navigation() -> None:
    assert ".ed-skip" in FOUNDATION


# --- an institution's own theme ---------------------------------------------


def test_a_school_colour_moves_the_product_without_being_used_as_text() -> None:
    """An institution choosing a light champagne has chosen an *ornament*
    colour. Rendering it as body text would be obeying them into a failure, so
    the text step is derived rather than taken."""
    from app.modules.design.theme import for_institution

    class Identity:
        display_name = "Willowbrook Early Years"
        primary_colour = "#2F5D50"
        accent_colour = "#E3CE9B"
        ink_colour = ""
        heading_font = ""
        body_font = ""

    class FakeSession:
        pass

    import app.modules.customization.branding as branding_module

    original = branding_module.resolve
    branding_module.resolve = lambda db: Identity()  # type: ignore[assignment]
    try:
        theme = for_institution(FakeSession())
    finally:
        branding_module.resolve = original

    assert theme.colour("accent.strong") == "#2F5D50"
    assert theme.colour("accent.metal") == "#E3CE9B"
    assert theme.colour("text.gold") != "#E3CE9B"
    assert ink.contrast(theme.colour("text.gold"),
                        theme.colour("surface.canvas")) >= ink.AA_NORMAL
    assert review(theme).is_publishable


def test_a_stylesheet_is_emitted_once_and_completely() -> None:
    css = stylesheet(resolve())
    assert css.startswith(":root {")
    assert "--surface-canvas" in css
    assert "--font-display" in css
    assert "--ornament-opacity" in css


def test_gold_is_never_the_only_signal_of_a_state() -> None:
    """The rule that replaces a contrast check that could not express it.

    Champagne on ivory is 2.09:1 and will never reach the 3:1 that WCAG 1.4.11
    asks of a state indicator. That is fine — and only fine because gold is
    never carrying the state alone. Every place it marks one, something else
    marks it too: a background change, a weight change, or a text colour change.
    Checking the contrast would have forced a heavier gold and destroyed the
    restraint; checking the redundancy is the honest form of the same concern.
    """
    css = FOUNDATION + page_css()
    blocks = {
        selector.strip().splitlines()[-1].strip(): body
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
    }

    # The active tab: gold underline, and also a colour and a weight change.
    active_tab = blocks.get('.ed-tab[aria-selected="true"]', "")
    assert "color:" in active_tab and "font-weight:" in active_tab

    # The current navigation item: a gold node, and also a background and a
    # weight change.
    current = blocks.get('.ed-nav__item[aria-current="page"]', "")
    assert "background:" in current and "font-weight:" in current

    # The current page in a pager: a gold rule, and also a colour and a weight.
    pager = blocks.get('.ed-pager__item[aria-current="page"]', "")
    assert "color:" in pager and "font-weight:" in pager
