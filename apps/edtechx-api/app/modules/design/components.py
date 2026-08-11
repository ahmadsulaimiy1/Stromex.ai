"""The component library, as functions that return markup.

Plain functions rather than a framework, deliberately. What has to be settled in
Phase 4 is the *visual contract* — what a button is, which states it has, how a
table behaves on a phone, what an empty state says. A contract expressed as
composable functions over semantic tokens transfers to React, to a template
language, or to a native client, and a contract expressed as a React component
transfers to React.

Two rules hold throughout.

**No component names a colour.** Everything reads a semantic token, which is
what lets an institution's theme move the whole product.

**Every component states its states.** Default, hover, focus, active, disabled,
loading, and — where it holds data — empty. The states live in `foundation.py`
as CSS; the functions here take the arguments that select them, so a caller
cannot render a control that has no disabled treatment.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from html import escape
from typing import Any, Literal

from app.modules.design import ornament

__all__ = [
    "alert",
    "avatar",
    "badge",
    "breadcrumbs",
    "button",
    "candidature_axis",
    "caseload_row",
    "checkbox",
    "command_palette",
    "data_table",
    "dialog",
    "drawer",
    "empty",
    "error_state",
    "field",
    "figure",
    "figures",
    "list_item",
    "milestone_row",
    "milestone_track",
    "notification",
    "page_header",
    "pagination",
    "panel",
    "progress",
    "register_row",
    "section",
    "skeleton",
    "switch",
    "tabs",
]


def e(value: Any) -> str:
    return escape("" if value is None else str(value))


def _attrs(**pairs: Any) -> str:
    out = []
    for name, value in pairs.items():
        if value in (None, False, ""):
            continue
        key = name.rstrip("_").replace("_", "-")
        out.append(key if value is True else f'{key}="{e(value)}"')
    return (" " + " ".join(out)) if out else ""


def _classes(base: list[str], attrs: dict[str, Any]) -> str:
    """Merge a caller's `class_` into the component's own classes.

    Emitting both produces two `class` attributes, of which a browser honours
    the first — so a caller adding `ed-mobile-only` to a component silently got
    nothing. That is exactly how a hamburger ended up visible on a 1440px
    desktop, and no assertion would ever have noticed.
    """
    extra = attrs.pop("class_", "") or attrs.pop("class", "")
    if extra:
        base = base + str(extra).split()
    return " ".join(base)


# --- structure --------------------------------------------------------------


def section(
    label: str,
    body: str,
    *,
    aside: str = "",
    gold: bool = True,
    heading: str = "",
) -> str:
    """A micro-label, the signature rule, and content.

    The most repeated composition in EdirasX, and the reason a dozen unrelated
    screens read as one product. The rule is what carries the identity; the
    label is what makes a person able to scan a page in two seconds.

    The label is an `<h2>`, not a paragraph. It reads as a heading, it is used
    as one, and rendering it as a paragraph meant a page went from `<h1>` to
    the `<h3>` inside a panel with nothing in between — which is how somebody
    navigating by heading loses the structure of the page entirely. Found by an
    audit, on five journeys at once.
    """
    title = f'<h3 class="ed-heading">{e(heading)}</h3>' if heading else ""
    return (
        '<section class="ed-section">'
        '<div class="ed-section__head">'
        f'<h2 class="ed-label">{e(label)}</h2>'
        f"{ornament.rule(gold=gold)}"
        + (f'<span class="ed-section__aside">{aside}</span>' if aside else "")
        + "</div>"
        + title
        + body
        + "</section>"
    )


def panel(body: str, *, crowned: bool = False, quiet: bool = False,
          sunken: bool = False, inverse: bool = False, **attrs: Any) -> str:
    """A bounded surface — used when there is genuinely a boundary.

    `crowned` puts a 2px gold edge along the top and is for the one panel on a
    screen that matters most. A grid of six crowned panels is six panels that
    matter equally, which is another way of saying none of them does.
    """
    classes = ["ed-panel"]
    if crowned:
        classes.append("ed-panel--crowned")
    if quiet:
        classes.append("ed-panel--quiet")
    if sunken:
        classes.append("ed-panel--sunken")
    if inverse:
        classes.append("ed-panel--inverse")
    rendered = _classes(classes, attrs)
    return f'<div class="{rendered}"{_attrs(**attrs)}>{body}</div>'


def page_header(
    title: str,
    *,
    eyebrow: str = "",
    lede: str = "",
    crumbs: Sequence[tuple[str, str]] = (),
    actions: str = "",
) -> str:
    return (
        '<header class="ed-page__head">'
        + (breadcrumbs(crumbs) if crumbs else "")
        + (f'<p class="ed-label ed-label--gold">{e(eyebrow)}</p>' if eyebrow else "")
        + '<div class="ed-page__title-row">'
        + f'<h1 class="ed-page__title">{e(title)}</h1>'
        + (f'<div class="ed-page__actions">{actions}</div>' if actions else "")
        + "</div>"
        + (f'<p class="ed-lede ed-page__lede">{e(lede)}</p>' if lede else "")
        + "</header>"
    )


def breadcrumbs(items: Sequence[tuple[str, str]]) -> str:
    parts = []
    for index, (label, href) in enumerate(items):
        if index:
            parts.append('<span class="ed-crumbs__sep">/</span>')
        parts.append(
            f'<a href="{e(href)}">{e(label)}</a>' if href else f"<span>{e(label)}</span>"
        )
    return f'<nav class="ed-crumbs" aria-label="Breadcrumb">{"".join(parts)}</nav>'


# --- figures ----------------------------------------------------------------


def figure(
    label: str,
    value: str,
    *,
    unit: str = "",
    delta: str = "",
    direction: Literal["up", "down", "flat"] = "flat",
    note: str = "",
) -> str:
    """One editorial metric.

    Set in the display serif because a large serif number reads as considered
    and the same number in the interface sans reads as a readout. The label
    goes *above* in micro-caps, which is how a report does it and how a
    dashboard usually does not.
    """
    trend = ""
    if delta:
        arrow = {"up": "▲", "down": "▼", "flat": "—"}[direction]
        trend = (
            f'<p class="ed-figures__delta ed-figures__delta--{e(direction)}">'
            f"{arrow} {e(delta)}</p>"
        )
    return (
        '<div class="ed-figures__item">'
        f'<p class="ed-label">{e(label)}</p>'
        f'<span class="ed-figure">{e(value)}'
        + (f'<span class="ed-figure__unit">{e(unit)}</span>' if unit else "")
        + "</span>"
        + trend
        + (f'<p class="ed-figures__delta ed-quiet">{e(note)}</p>' if note else "")
        + "</div>"
    )


def figures(items: Iterable[str]) -> str:
    """A row of metrics separated by rules rather than boxed in cards.

    The single biggest departure from a generic dashboard, and the cheapest: the
    same numbers in six bordered rectangles look assembled, and separated by
    hairlines they look composed.
    """
    return f'<div class="ed-figures">{"".join(items)}</div>'


# --- controls ---------------------------------------------------------------


def button(
    label: str,
    *,
    variant: Literal["default", "primary", "ceremonial", "quiet", "danger"] = "default",
    size: Literal["md", "sm"] = "md",
    href: str = "",
    disabled: bool = False,
    loading: bool = False,
    icon: str = "",
    **attrs: Any,
) -> str:
    """`ceremonial` is the gold one, and there is at most one on a screen.

    Gold is earned by consequence rather than by prominence: publishing results
    and issuing a transcript get it; Save does not.
    """
    classes = ["ed-btn"]
    if variant != "default":
        classes.append(f"ed-btn--{variant}")
    if size != "md":
        classes.append(f"ed-btn--{size}")
    body = (icon or "") + e(label)
    if loading:
        body += ornament.spinner(16)
    tag = "a" if href else "button"
    rendered = _classes(classes, attrs)
    extra = _attrs(
        href=href or None,
        type=None if href else "button",
        disabled=disabled and not href,
        aria_disabled="true" if disabled and href else None,
        data_loading="true" if loading else None,
        **attrs,
    )
    return f'<{tag} class="{rendered}"{extra}>{body}</{tag}>'


def field(
    label: str,
    control: str,
    *,
    hint: str = "",
    error: str = "",
    required: bool = False,
) -> str:
    marker = ' <span class="ed-label--gold" aria-hidden="true">•</span>' if required else ""
    # The label wraps the control rather than sitting beside it. A `<label>`
    # with no `for` and no child input is a paragraph in a smaller font: an
    # audit reported three unlabelled inputs on the styleguide, and it was the
    # component at fault rather than the page.
    return (
        '<div class="ed-field">'
        f'<label class="ed-field__label">{e(label)}{marker}'
        + control
        + "</label>"
        + (f'<p class="ed-field__hint">{e(hint)}</p>' if hint and not error else "")
        + (f'<p class="ed-field__error">{e(error)}</p>' if error else "")
        + "</div>"
    )


def text_input(
    *, value: str = "", placeholder: str = "", disabled: bool = False,
    invalid: bool = False, kind: str = "text", **attrs: Any,
) -> str:
    return (
        f'<input class="ed-input" type="{e(kind)}"'
        + _attrs(
            value=value or None, placeholder=placeholder or None,
            disabled=disabled, aria_invalid="true" if invalid else None, **attrs
        )
        + ">"
    )


def select(options: Sequence[tuple[str, str]], *, value: str = "",
           disabled: bool = False, **attrs: Any) -> str:
    body = "".join(
        f'<option value="{e(v)}"{" selected" if v == value else ""}>{e(text)}</option>'
        for v, text in options
    )
    return f'<select class="ed-select"{_attrs(disabled=disabled, **attrs)}>{body}</select>'


def textarea(*, value: str = "", placeholder: str = "", disabled: bool = False,
             **attrs: Any) -> str:
    return (
        '<textarea class="ed-textarea"'
        + _attrs(placeholder=placeholder or None, disabled=disabled, **attrs)
        + f">{e(value)}</textarea>"
    )


def checkbox(label: str, *, checked: bool = False, disabled: bool = False,
             radio: bool = False, name: str = "") -> str:
    shape = " ed-check__box--round" if radio else ""
    return (
        '<label class="ed-check">'
        f'<input type="{"radio" if radio else "checkbox"}"'
        + _attrs(checked=checked, disabled=disabled, name=name or None)
        + ">"
        f'<span class="ed-check__box{shape}"></span>'
        f"<span>{e(label)}</span>"
        "</label>"
    )


def switch(label: str, *, on: bool = False, disabled: bool = False) -> str:
    return (
        '<label class="ed-switch">'
        f'<input type="checkbox"{_attrs(checked=on, disabled=disabled)}>'
        '<span class="ed-switch__track"><span class="ed-switch__thumb"></span></span>'
        f"<span>{e(label)}</span>"
        "</label>"
    )


def badge(
    label: str,
    *,
    tone: Literal["neutral", "accent", "gold", "success", "warning", "danger"] = "neutral",
) -> str:
    return f'<span class="ed-badge ed-badge--{tone}">{e(label)}</span>'


def avatar(name: str, *, large: bool = False) -> str:
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "?"
    size = " ed-avatar--lg" if large else ""
    return (
        f'<span class="ed-avatar{size}" role="img" aria-label="{e(name)}">'
        f"{e(initials)}</span>"
    )


def tabs(items: Sequence[tuple[str, bool]]) -> str:
    body = "".join(
        f'<button class="ed-tab" role="tab" aria-selected="{"true" if active else "false"}">'
        f"{e(label)}</button>"
        for label, active in items
    )
    return f'<div class="ed-tabs" role="tablist">{body}</div>'


def pagination(*, page: int, pages: int, total: int) -> str:
    items = []
    for number in range(1, min(pages, 5) + 1):
        current = ' aria-current="page"' if number == page else ""
        items.append(f'<a class="ed-pager__item" href="#"{current}>{number}</a>')
    if pages > 5:
        items.append('<span class="ed-pager__item ed-quiet">…</span>')
        items.append(f'<a class="ed-pager__item" href="#">{pages}</a>')
    return (
        '<div style="display:flex;align-items:center;gap:var(--space-4);'
        'justify-content:space-between;padding-block-start:var(--space-4)">'
        f'<p class="ed-label">{total:,} records</p>'
        f'<div class="ed-pager">{"".join(items)}</div>'
        "</div>"
    )


# --- feedback ---------------------------------------------------------------


def alert(
    body: str,
    *,
    title: str = "",
    tone: Literal["info", "success", "warning", "danger"] = "info",
) -> str:
    variant = "" if tone == "info" else f" ed-alert--{tone}"
    return (
        f'<div class="ed-alert{variant}" role="{"alert" if tone == "danger" else "status"}">'
        "<div>"
        + (f'<p class="ed-alert__title">{e(title)}</p>' if title else "")
        + f"<p>{body}</p>"
        + "</div></div>"
    )


def progress(value: float, *, label: str = "") -> str:
    """A determinate bar, which must say what it is measuring.

    `aria-valuenow` alone tells a screen-reader user "68 percent" and not 68
    percent *of what*. An audit reported this as an unnamed progressbar on
    every page that used one, which was fair: the visible label was beside the
    bar and not attached to it.
    """
    pct = max(0.0, min(100.0, value))
    return (
        "<div>"
        + (
            f'<div style="display:flex;justify-content:space-between;'
            f'margin-block-end:var(--space-2)">'
            f'<p class="ed-label">{e(label)}</p>'
            f'<p class="ed-label ed-numeric">{pct:.0f}%</p></div>'
            if label else ""
        )
        + f'<div class="ed-progress" role="progressbar" aria-valuenow="{pct:.0f}" '
          f'aria-valuemin="0" aria-valuemax="100" '
          f'aria-label="{e(label or "Progress")}">'
          f'<div class="ed-progress__bar" style="width:{pct:.1f}%"></div></div>'
        + "</div>"
    )


def skeleton(*, lines: int = 3) -> str:
    widths = ("100%", "84%", "62%", "92%", "70%")
    body = "".join(
        f'<div class="ed-skeleton" style="width:{widths[i % len(widths)]};'
        f'margin-block-end:var(--space-3)"></div>'
        for i in range(lines)
    )
    return f'<div aria-busy="true" aria-live="polite">{body}</div>'


def empty(title: str, body: str, *, action: str = "") -> str:
    """A composition, not an apology.

    "No data" teaches a person that they have done something wrong. A sentence
    saying what this place is *for*, and the action that fills it, teaches them
    what to do next — which is the difference between an empty state and a dead
    end (ADR-031).
    """
    return (
        '<div class="ed-empty">'
        f'<span class="ed-empty__mark">{ornament.node(44, colour="var(--accent-metal)")}</span>'
        f'<h3 class="ed-empty__title">{e(title)}</h3>'
        f'<p class="ed-empty__body">{e(body)}</p>'
        + (f"<div>{action}</div>" if action else "")
        + "</div>"
    )


def dialog(title: str, body: str, *, actions: str = "") -> str:
    return (
        '<div class="ed-dialog" role="dialog" aria-modal="true">'
        f'<h2 class="ed-title" style="margin-block-end:var(--space-3)">{e(title)}</h2>'
        f"{body}"
        + (
            f'<div style="display:flex;gap:var(--space-2);justify-content:flex-end;'
            f'margin-block-start:var(--space-6)">{actions}</div>'
            if actions else ""
        )
        + "</div>"
    )


def list_item(title: str, meta: str, *, lead: str = "", trail: str = "") -> str:
    return (
        '<li class="ed-list__item">'
        + (lead or "")
        + '<div class="ed-list__body">'
        + f'<p class="ed-list__title">{e(title)}</p>'
        + f'<p class="ed-list__meta">{e(meta)}</p>'
        + "</div>"
        + (trail or "")
        + "</li>"
    )


# --- data -------------------------------------------------------------------

DataShape = Literal["ledger", "matrix", "roster", "schedule"]


def data_table(
    columns: Sequence[tuple[str, str]],
    rows: Sequence[Sequence[str]],
    *,
    shape: DataShape,
    caption: str = "",
    empty_state: str = "",
) -> str:
    """A table that knows what kind of data it holds.

    `shape` is the whole point. A dense desktop table pushed onto a phone is the
    failure this argument exists to prevent, and the fix is not one responsive
    rule — it is four, because an academic history, a set of results, a roster
    of people and a timetable want four different things on a small screen:

      `ledger`   stacks into labelled records, nothing hidden
      `matrix`   becomes course-with-grade, the grade held large at the right
      `roster`   becomes a people list with one meta line
      `schedule` scrolls horizontally with the time column pinned, because a
                 timetable is genuinely two-dimensional and pretending otherwise
                 destroys it

    Column headings travel down to the stacked layouts through `data-label`, so
    the small-screen view is generated from this markup rather than from a
    second template that will drift out of step with it.
    """
    if not rows:
        return empty_state or empty(
            "Nothing here yet",
            "When there is something to show, it will appear here.",
        )

    head = "".join(
        f'<th class="{"num" if align == "num" else ""}" scope="col">{e(label)}</th>'
        for label, align in columns
    )
    body = []
    for row in rows:
        cells = []
        for (label, align), value in zip(columns, row, strict=False):
            classes = "num" if align == "num" else ""
            cells.append(
                f'<td class="{classes}" data-label="{e(label)}">{value}</td>'
            )
        body.append(f"<tr>{''.join(cells)}</tr>")

    return (
        f'<div class="ed-data__scroll"><table class="ed-table ed-data" data-shape="{shape}">'
        + (f"<caption>{e(caption)}</caption>" if caption else "")
        + f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def matrix_row(
    *, subject: str, grade: str, details: Sequence[tuple[str, str]], note: str = ""
) -> str:
    """One row of a results matrix, carrying its own small-screen composition.

    On a wide screen this is an ordinary table row. On a phone the grade moves
    to the right at display size and the details become a wrapped caption
    beneath the subject — because a parent opening a report card on a phone came
    to see the grade, and everything else is supporting it.
    """
    # The runs live inside a wrapper rather than making the `<td>` itself a
    # flex container. A cell with `display: flex` is no longer a table-cell, so
    # `border-collapse` stops governing it: on the last row of a matrix every
    # other cell's rule was collapsed away and this one's was not, leaving a
    # 270px hairline floating under one column. Visible only at tablet width,
    # which is where it was found.
    detail_cells = (
        '<span class="ed-detail">'
        + "".join(
            f'<span data-label="{e(label)}">{e(value)}</span>'
            for label, value in details
        )
        + "</span>"
    )
    return (
        "<tr>"
        f'<td data-role="subject" class="ed-table__primary">{e(subject)}</td>'
        f'<td data-role="detail">{detail_cells}</td>'
        f'<td data-role="grade" class="num">{e(grade)}</td>'
        + (f'<td data-role="note">{e(note)}</td>' if note else '<td data-role="note"></td>')
        + "</tr>"
    )


# --- workflows --------------------------------------------------------------
#
# The components below exist because a journey needed them, not because a
# component library ought to have them. Each one is used in `tools/design`.


def command_palette(
    query: str,
    groups: Sequence[tuple[str, Sequence[tuple[str, str, str]]]],
    *,
    selected: tuple[int, int] = (0, 0),
    hint: str = "Search people, classes, documents and actions",
) -> str:
    """The acceleration layer, and never an authorization bypass.

    What it finds is whatever the caller's own scoped queries returned. That is
    not a convention this component can enforce — but it is why the caller
    passes *results* rather than a query: there is no path here that reaches a
    table, so there is no path here that reaches past a scope.

    `groups` is `[(label, [(title, meta, href), …]), …]`, already in the order
    the person is most likely to want.
    """
    if not any(items for _label, items in groups):
        body = empty(
            "Nothing matches that",
            "Try a name, a class code, or the beginning of a document number. "
            "Only what you have access to appears here.",
        )
    else:
        blocks = []
        for group_index, (label, items) in enumerate(groups):
            if not items:
                continue
            rows = "".join(
                f'<a class="ed-palette__item" href="{e(href)}" role="option" '
                f'aria-selected="{"true" if (group_index, row) == selected else "false"}">'
                + ornament.node(6, colour="var(--accent-metal)")
                + f"<span>{e(title)}</span>"
                + (f'<span class="ed-palette__meta">{e(meta)}</span>' if meta else "")
                + "</a>"
                for row, (title, meta, href) in enumerate(items)
            )
            blocks.append(
                '<div class="ed-palette__group">'
                f'<p class="ed-palette__label">{e(label)}</p>{rows}</div>'
            )
        body = "".join(blocks)

    return (
        '<div class="ed-palette__scrim">'
        '<div class="ed-palette" role="dialog" aria-modal="true" aria-label="Search">'
        '<div class="ed-palette__field">'
        '<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">'
        '<circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.3"/>'
        '<path d="M10.4 10.4 14 14" stroke="currentColor" stroke-width="1.3"/></svg>'
        f'<input class="ed-palette__input" value="{e(query)}" '
        f'placeholder="{e(hint)}" aria-label="{e(hint)}" role="combobox" '
        'aria-expanded="true" aria-controls="ed-palette-results">'
        "</div>"
        f'<div class="ed-palette__results" id="ed-palette-results" role="listbox">{body}</div>'
        '<div class="ed-palette__foot">'
        "<span><kbd>&uarr;</kbd><kbd>&darr;</kbd> to move</span>"
        "<span><kbd>&crarr;</kbd> to open</span>"
        "<span><kbd>esc</kbd> to close</span>"
        "</div></div></div>"
    )


def notification(
    title: str,
    body: str,
    when: str,
    *,
    priority: Literal["urgent", "important", "informational"] = "informational",
    category: str = "",
    unread: bool = False,
    href: str = "#",
) -> str:
    """One notification.

    Priority is carried by a rule, a marker *and* a word. Colour alone excludes
    a reader who cannot distinguish it, and fails again the moment somebody
    prints the page.
    """
    label = ""
    if priority != "informational":
        label = badge(priority, tone="danger" if priority == "urgent" else "gold")
    return (
        f'<a class="ed-notice" href="{e(href)}" data-priority="{priority}" '
        f'data-unread="{"true" if unread else "false"}">'
        '<span class="ed-notice__dot" aria-hidden="true"></span>'
        "<span>"
        + (f"{label} " if label else "")
        + (f'<span class="ed-label">{e(category)}</span>' if category else "")
        + f'<p class="ed-notice__title">{e(title)}</p>'
        + f'<p class="ed-notice__body">{e(body)}</p>'
        + "</span>"
        + f'<span class="ed-notice__when"><span class="ed-sr">Received </span>{e(when)}</span>'
        + "</a>"
    )


def drawer(title: str, body: str, *, meta: str = "", actions: str = "") -> str:
    """Contextual inspection and lightweight editing.

    A complex workflow does not belong in one. Neither does it belong in a
    dialog, which is the mistake this component exists to make unnecessary.
    """
    return (
        '<div class="ed-drawer__scrim">'
        '<div class="ed-drawer" role="dialog" aria-modal="true" '
        'aria-labelledby="ed-drawer-title">'
        '<header class="ed-drawer__head"><div>'
        f'<h2 class="ed-title" id="ed-drawer-title">{e(title)}</h2>'
        + (f'<p class="ed-list__meta">{e(meta)}</p>' if meta else "")
        + "</div>"
        + button(
            "", variant="quiet", size="sm", aria_label="Close",
            icon='<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">'
            '<path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.4"/></svg>',
            style="margin-inline-start:auto",
        )
        + "</header>"
        # `tabindex="0"` because the body scrolls: a region a mouse can scroll
        # and a keyboard cannot is unreachable content, and axe is right to
        # call it a failure rather than a nicety.
        + f'<div class="ed-drawer__body" tabindex="0" role="group" '
          f'aria-label="{e(title)} details">{body}</div>'
        + (f'<div class="ed-drawer__foot">{actions}</div>' if actions else "")
        + "</div></div>"
    )


def error_state(
    title: str, body: str, *, action: str = "", reference: str = ""
) -> str:
    """Understandable, actionable, calm — and saying nothing protected.

    An authorization failure in particular never explains what sits behind it.
    "You do not have access to this class" tells somebody the class exists;
    "This is not available to you" does not, and is the same sentence for a
    record that is out of scope and one that never existed (ADR-004).
    """
    return (
        '<div class="ed-error" role="alert">'
        f'<span class="ed-error__mark">{ornament.node(40, colour="currentColor")}</span>'
        f'<h2 class="ed-error__title">{e(title)}</h2>'
        f'<p class="ed-error__body">{e(body)}</p>'
        + (f"<div>{action}</div>" if action else "")
        + (
            f'<p class="ed-error__ref">Reference {e(reference)} &mdash; quote this if '
            "you contact your institution.</p>"
            if reference else ""
        )
        + "</div>"
    )


def register_row(
    name: str, *, meta: str, codes: Sequence[tuple[str, str, bool]]
) -> str:
    """One child in a register.

    The marks are 40px targets on a desktop and 44px on a phone, because this is
    the screen a teacher taps thirty times in ninety seconds while standing up,
    and a 24px target is why registers get taken later "properly" and then not
    at all (ADR-032).
    """
    marks = "".join(
        f'<button type="button" class="ed-mark" data-code="{e(code)}" '
        f'aria-pressed="{"true" if on else "false"}" aria-label="{e(label)}">'
        f"{e(code)}</button>"
        for code, label, on in codes
    )
    return (
        '<div class="ed-register__row">'
        + avatar(name)
        + f'<div><p class="ed-register__name">{e(name)}</p>'
        f'<p class="ed-register__meta">{e(meta)}</p></div>'
        + f'<div class="ed-marks" role="group" aria-label="Attendance for {e(name)}">'
        + marks
        + "</div></div>"
    )


# --- candidature ------------------------------------------------------------
#
# The one part of EdirasX where the unit of time is the year. A research
# candidate's screen cannot be built from the components above without lying
# about the shape of the thing: a doctorate is not a list of items due this
# week, and rendering it as one is how every student-information system ends up
# telling a fourth-year candidate that they have nothing on today.
#
# So the primary object is an *axis*. It is drawn from arithmetic — months
# elapsed over the horizon the programme itself set — and the milestones sit on
# it at their own offsets. Nothing here is decorative: every position on the
# line is a date somebody will be held to.


def _pct(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return max(0.0, min(100.0, value / total * 100.0))


def candidature_axis(
    *,
    months: int,
    elapsed: int,
    marks: Sequence[tuple[str, int, str]] = (),
    summary: str,
    compact: bool = False,
) -> str:
    """Position along a candidature, drawn to scale.

    `marks` are `(label, month, state)`, where state is one of `done`, `due`,
    `late` or `ahead`. The axis itself is hidden from assistive technology and
    `summary` carries the same facts in a sentence — a screen reader user gets
    "Month 20 of 48" rather than a list of unlabelled positions, and the
    milestone names are in the track below where they read properly.
    """
    ticks = ""
    if not compact and months:
        years = months // 12
        ticks = "".join(
            f'<span class="ed-axis__tick" style="inset-inline-start:{_pct(y * 12, months):.4f}%">'
            f'<span class="ed-axis__tick-label">Year {y + 1}</span></span>'
            for y in range(years)
        )
    nodes = "".join(
        f'<span class="ed-axis__mark" data-state="{e(state)}" '
        f'style="inset-inline-start:{_pct(month, months):.4f}%" '
        f'title="{e(label)}">{ornament.node(7 if compact else 9)}</span>'
        for label, month, state in marks
    )
    here = _pct(elapsed, months)
    return (
        f'<div class="ed-axis{" ed-axis--compact" if compact else ""}">'
        + f'<p class="ed-sr">{e(summary)}</p>'
        + '<div class="ed-axis__line" aria-hidden="true">'
        + f'<span class="ed-axis__elapsed" style="inline-size:{here:.4f}%"></span>'
        + ticks
        + nodes
        + f'<span class="ed-axis__now" style="inset-inline-start:{here:.4f}%"></span>'
        + "</div>"
        + (
            ""
            if compact
            else f'<p class="ed-axis__caption ed-quiet">{e(summary)}</p>'
        )
        + "</div>"
    )


def milestone_row(
    name: str,
    *,
    state: str,
    when: str,
    detail: str = "",
    trail: str = "",
) -> str:
    """One checkpoint on the vertical track.

    The node is filled for what has happened, hollow for what has not, and
    garnet for what is late — and the state is *also* written in words beside
    it, because a colour that is the only carrier of meaning is not a signal to
    somebody who cannot see it.
    """
    return (
        f'<li class="ed-track__item" data-state="{e(state)}">'
        + '<span class="ed-track__node" aria-hidden="true"></span>'
        + '<div class="ed-track__body">'
        + f'<p class="ed-track__name">{e(name)}</p>'
        + (f'<p class="ed-track__detail">{e(detail)}</p>' if detail else "")
        + "</div>"
        + f'<div class="ed-track__when"><p class="ed-track__date">{e(when)}</p>'
        + (f'<div class="ed-track__trail">{trail}</div>' if trail else "")
        + "</div></li>"
    )


def milestone_track(rows: Iterable[str]) -> str:
    return f'<ol class="ed-track">{"".join(rows)}</ol>'


def caseload_row(
    name: str,
    *,
    meta: str,
    axis: str,
    contact: str,
    contact_state: str = "",
    next_up: str,
    next_state: str = "",
    actions: str = "",
) -> str:
    """One researcher, as the person responsible for them needs to see them.

    Two facts get their own columns and neither appears on any other screen in
    the product: how long since this candidate was last seen, and what the next
    requirement is. They are the two numbers that go wrong months before a
    research degree formally fails.
    """
    return (
        '<div class="ed-caseload__row">'
        + '<div class="ed-caseload__who">'
        + avatar(name)
        + f'<div><p class="ed-caseload__name">{e(name)}</p>'
        + f'<p class="ed-caseload__meta">{e(meta)}</p></div>'
        + "</div>"
        + f'<div class="ed-caseload__axis">{axis}</div>'
        + '<div class="ed-caseload__facts">'
        + '<div class="ed-caseload__fact">'
        + '<p class="ed-label">Last met</p>'
        + f'<p class="ed-caseload__value" data-state="{e(contact_state)}">{e(contact)}</p>'
        + "</div>"
        + '<div class="ed-caseload__fact">'
        + '<p class="ed-label">Next</p>'
        + f'<p class="ed-caseload__value" data-state="{e(next_state)}">{e(next_up)}</p>'
        + "</div></div>"
        + (f'<div class="ed-caseload__actions">{actions}</div>' if actions else "")
        + "</div>"
    )
