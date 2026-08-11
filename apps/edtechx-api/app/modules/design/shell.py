"""The application shell: the frame every EdirasX screen sits inside.

The shell's navigation is not a list somebody maintains. It is rendered from
`experience.resolve`, which already answers — per institution, per person, per
plan — what this world contains (ADR-031). A nursery administrator's rail has no
Programmes item because there is no programme row and no programme concept in
that institution, not because a template checked a flag.

That is worth stating because it is the thing most products get wrong in the
opposite direction: they build the navigation first and then try to hide parts
of it. Here the navigation is a *rendering* of a resolved answer, and the only
way to add an item to somebody's rail is to give them the capability.

**What the shell establishes visually.** A midnight rail carrying the
institution's identity and the seal lattice; an ivory canvas carrying the work;
one gold node marking where you are. The contrast between an authoritative dark
frame and a warm editorial page is the half-second signature — a person seeing a
screenshot should know it is EdirasX before reading a word.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.modules.design import components as ui
from app.modules.design import ornament
from app.modules.design.foundation import FOUNDATION, page_css
from app.modules.design.theme import Theme, stylesheet
from app.modules.design.typeface import font_face_css

__all__ = ["GROUP_LABELS", "document", "navigation", "shell"]


#: The institution's own words are used for the *items*; these name the
#: groups, which are the platform's structure rather than the institution's.
GROUP_LABELS: dict[str, str] = {
    "today": "Today",
    "people": "People",
    "academics": "Academic structure",
    "operations": "Operations",
    "finance": "Finance",
    "communication": "Communication",
    "insight": "Insight",
    "configuration": "Configuration",
}


def navigation(experience, *, current: str = "") -> str:
    """The rail's links, derived rather than declared.

    An unentitled capability that this person could actually buy is rendered as
    an item with a gold marker rather than a padlock — because a padlock is an
    advertisement placed in somebody's way, and an offer shown only to the
    person who could accept it is information.
    """
    groups = []
    for group, capabilities in experience.grouped().items():
        items = []
        for capability in capabilities:
            active = ' aria-current="page"' if capability.key == current else ""
            trailing = ""
            if capability.upgrade_from:
                trailing = '<span class="ed-nav__upgrade">Upgrade</span>'
            items.append(
                f'<a class="ed-nav__item" href="#{ui.e(capability.key)}"{active}>'
                f"{ornament.node(7, colour='var(--gold-500)')}"
                f"<span>{ui.e(capability.label_plural)}</span>"
                f"{trailing}</a>"
            )
        groups.append(
            '<div class="ed-nav__group">'
            f'<p class="ed-nav__label">{ui.e(GROUP_LABELS.get(group, group.title()))}</p>'
            f"{''.join(items)}"
            "</div>"
        )
    return f'<nav class="ed-nav" aria-label="Sections">{"".join(groups)}</nav>'


def _identity(experience, branding) -> str:
    return (
        '<div class="ed-identity">'
        + ornament.monogram(30, gold="var(--gold-500)", ink="var(--ivory-50)")
        + "<div>"
        + '<p class="ed-identity__name">'
        + ui.e(branding.display_name or experience.institution)
        + '</p>'
        + f'<p class="ed-identity__kind">{ui.e(experience.self_description)}</p>'
        + "</div></div>"
    )


def _account(name: str, role: str) -> str:
    return (
        '<div class="ed-rail__foot">'
        f'<a class="ed-account" href="#account">{ui.avatar(name)}'
        f'<span><p class="ed-account__name">{ui.e(name)}</p>'
        f'<p class="ed-account__role">{ui.e(role)}</p></span></a>'
        "</div>"
    )


def _topbar(*, search_hint: str, notifications: int, actions: str = "") -> str:
    bell = (
        '<span class="ed-bell">'
        + ui.button(
            "",
            variant="quiet",
            size="sm",
            icon='<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">'
            '<path d="M8 1.5a3.5 3.5 0 0 0-3.5 3.5v2.2L3 10h10l-1.5-2.8V5A3.5 3.5 0 0 0 8 1.5Z" '
            'fill="none" stroke="currentColor" stroke-width="1.2"/>'
            '<path d="M6.6 12a1.4 1.4 0 0 0 2.8 0" fill="none" stroke="currentColor" '
            'stroke-width="1.2"/></svg>',
            aria_label=f"{notifications} notifications",
        )
        + ('<span class="ed-bell__dot"></span>' if notifications else "")
        + "</span>"
    )
    return (
        '<div class="ed-topbar">'
        + ui.button(
            "",
            variant="quiet",
            size="sm",
            icon='<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">'
            '<path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="1.3"/></svg>',
            aria_label="Open navigation",
            class_="ed-mobile-only",
        )
        + '<div class="ed-search" role="search">'
        + '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">'
          '<circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.3"/>'
          '<path d="M10.4 10.4 14 14" stroke="currentColor" stroke-width="1.3"/></svg>'
        + f"<span>{ui.e(search_hint)}</span><kbd>⌘K</kbd></div>"
        + f'<div class="ed-topbar__actions">{actions}{bell}</div>'
        + "</div>"
    )


def shell(
    *,
    theme: Theme,
    experience,
    branding,
    body: str,
    current: str = "",
    person: str = "",
    role: str = "",
    search_hint: str = "Search students, classes, documents…",
    notifications: int = 0,
    topbar_actions: str = "",
    title: str = "EdirasX",
    embed_fonts: bool = False,
    font_base: str = "fonts",
) -> str:
    """A complete page.

    Emitted as one self-contained document because that is what makes it
    reviewable: a page that can be opened, screenshotted at three widths and
    argued about is worth more at this stage than a build pipeline.
    """
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{ui.e(title)}</title><style>"
        + font_face_css(embed=embed_fonts, base_url=font_base)
        + stylesheet(theme)
        + FOUNDATION
        + page_css()
        + "</style></head><body>"
        + '<a class="ed-skip" href="#main">Skip to content</a>'
        + '<div class="ed-app">'
        + '<aside class="ed-rail">'
        + f'<div class="ed-rail__ground">{ornament.lattice(cell=64)}</div>'
        + _identity(experience, branding)
        + navigation(experience, current=current)
        + _account(person or "Account", role)
        + "</aside>"
        + '<div class="ed-main">'
        + _topbar(
            search_hint=search_hint,
            notifications=notifications,
            actions=topbar_actions,
        )
        + f'<main class="ed-page" id="main">{body}</main>'
        + "</div></div></body></html>"
    )


def document(
    *,
    theme: Theme,
    body: str,
    title: str = "EdirasX",
    embed_fonts: bool = False,
    font_base: str = "fonts",
    extra_css: str = "",
) -> str:
    """A bare themed page, for the styleguide and for anything outside the shell."""
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{ui.e(title)}</title><style>"
        + font_face_css(embed=embed_fonts, base_url=font_base)
        + stylesheet(theme)
        + FOUNDATION
        + page_css()
        + extra_css
        + "</style></head><body>"
        + body
        + "</body></html>"
    )


def sequence_of(items: Sequence[Any]) -> str:  # pragma: no cover - trivial helper
    return "".join(str(item) for item in items)
