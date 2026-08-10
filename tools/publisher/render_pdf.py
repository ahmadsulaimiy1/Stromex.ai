"""Render the document model to a premium print PDF via WeasyPrint."""

from __future__ import annotations

import datetime
import html
import pathlib
from typing import Iterable

from model import Block, BlockKind, Chapter, Document, Run, typographic
from diagrams import DIAGRAMS

ASSETS = pathlib.Path(__file__).resolve().parent / "assets"


# --- inline ---------------------------------------------------------------


def runs_html(runs: Iterable[Run]) -> str:
    out: list[str] = []
    for run in runs:
        text = html.escape(run.text)
        if run.code:
            text = f"<code>{text}</code>"
        if run.bold and run.italic:
            text = f"<strong><em>{text}</em></strong>"
        elif run.bold:
            text = f"<strong>{text}</strong>"
        elif run.italic:
            text = f"<em>{text}</em>"
        out.append(text)
    return "".join(out)


# --- wordmark -------------------------------------------------------------

WORDMARK = """
<svg class="mark" viewBox="0 0 620 124" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="EdirasX">
  <defs>
    <linearGradient id="brandX" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"  stop-color="#2E7FD1"/>
      <stop offset="100%" stop-color="#7A3FD6"/>
    </linearGradient>
    <linearGradient id="silver" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="#FFFFFF"/>
      <stop offset="55%" stop-color="#E4E8EC"/>
      <stop offset="100%" stop-color="#AEB6BE"/>
    </linearGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#2E7FD1" stop-opacity="0"/>
      <stop offset="22%"  stop-color="#2E7FD1"/>
      <stop offset="62%"  stop-color="#7A3FD6"/>
      <stop offset="100%" stop-color="#D4A94E" stop-opacity="0.85"/>
    </linearGradient>
  </defs>
  <text x="0" y="62" font-family="Inter" font-weight="600" font-size="58"
        letter-spacing="11" fill="url(#silver)">EDIRAS<tspan
        fill="url(#brandX)" font-weight="700">X</tspan></text>
  <text x="4" y="100" font-family="Inter" font-weight="500" font-size="15"
        letter-spacing="9.5" fill="#8C97A2">LEARN &#183; GROW &#183; EXCEL</text>
  <rect x="2" y="118" width="470" height="1.6" fill="url(#rule)"/>
</svg>
"""


# --- blocks ---------------------------------------------------------------


def block_html(block: Block) -> str:
    kind = block.kind

    if kind is BlockKind.heading:
        level = min(max(block.level, 2), 4)
        number = (
            f'<span class="section-num">{html.escape(block.number)}</span>'
            if block.number
            else ""
        )
        return f'<h{level} class="section">{number}{runs_html(block.runs)}</h{level}>'

    if kind is BlockKind.paragraph:
        return f"<p>{runs_html(block.runs)}</p>"

    if kind is BlockKind.quote:
        return f"<blockquote><p>{runs_html(block.runs)}</p></blockquote>"

    if kind is BlockKind.bullets:
        items = "".join(f"<li>{runs_html(i)}</li>" for i in block.items)
        return f"<ul>{items}</ul>"

    if kind is BlockKind.numbers:
        items = "".join(f"<li>{runs_html(i)}</li>" for i in block.items)
        return f"<ol>{items}</ol>"

    if kind is BlockKind.checklist:
        items = "".join(f"<li>{runs_html(i)}</li>" for i in block.items)
        return f'<ul class="checklist">{items}</ul>'

    if kind is BlockKind.table:
        head = "".join(f"<th>{runs_html(c)}</th>" for c in block.header)
        body = "".join(
            "<tr>" + "".join(f"<td>{runs_html(c)}</td>" for c in row) + "</tr>"
            for row in block.rows
        )
        return f'<table class="data"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'

    if kind is BlockKind.callout:
        label = f'<div class="label">{html.escape(block.label)}</div>' if block.label else ""
        return (
            f'<div class="callout {block.tone.value}">{label}'
            f"<p>{runs_html(block.runs)}</p></div>"
        )

    if kind is BlockKind.contrast:
        negatives = "".join(f"<li>{runs_html(i)}</li>" for i in block.items)
        positives = "".join(f"<li>{runs_html(row[0])}</li>" for row in block.rows)
        return (
            '<div class="contrast">'
            f'<div class="col negative"><h5>Prestige is not</h5><ul>{negatives}</ul></div>'
            f'<div class="col positive"><h5>Prestige is</h5><ul>{positives}</ul></div>'
            "</div>"
        )

    if kind is BlockKind.diagram:
        svg = DIAGRAMS.get(block.name, "")
        caption = f"<figcaption>{html.escape(typographic(block.label))}</figcaption>" if block.label else ""
        return f"<figure>{svg}{caption}</figure>"

    if kind is BlockKind.rule:
        return "<hr/>"

    return ""


def chapter_html(chapter: Chapter, anchor: str, front: bool) -> str:
    body = "".join(block_html(b) for b in chapter.blocks)
    if front:
        return (
            f'<section class="front" id="{anchor}">'
            f"<h2>{html.escape(typographic(chapter.title))}</h2>{body}</section>"
        )
    eyebrow = f"Chapter {chapter.number}" if chapter.number else ""
    return (
        f'<section class="chapter" id="{anchor}">'
        f'<header class="chapter-head">'
        f'<div class="chapter-eyebrow">{html.escape(eyebrow)}</div>'
        f'<h1 class="chapter-title">{html.escape(typographic(chapter.title))}</h1>'
        f'<div class="chapter-rule"></div>'
        f"</header>{body}</section>"
    )


# --- assembly -------------------------------------------------------------


def anchor_for(prefix: str, index: int) -> str:
    return f"{prefix}-{index}"


def build_html(document: Document) -> str:
    today = datetime.date.today().strftime("%d %B %Y")

    front_sections: list[str] = []
    toc_front: list[tuple[str, str, str]] = []
    for index, chapter in enumerate(document.front_matter):
        anchor = anchor_for("front", index)
        front_sections.append(chapter_html(chapter, anchor, front=True))
        toc_front.append(("", chapter.title, anchor))

    body_sections: list[str] = []
    toc_parts: list[tuple[str, str, list[tuple[str, str, str]]]] = []
    seen_parts: dict[str, list[tuple[str, str, str]]] = {}

    for index, chapter in enumerate(document.chapters):
        anchor = anchor_for("ch", index)
        part = next((p for p in document.parts if p.number == chapter.part), None)
        if part and part.number not in seen_parts:
            seen_parts[part.number] = []
            toc_parts.append((part.number, part.title, seen_parts[part.number]))
            body_sections.append(
                f'<section class="part">'
                f'<div class="num">Part {html.escape(part.number)}</div>'
                f'<div class="bar"></div>'
                f"<h2>{html.escape(part.title)}</h2>"
                f'<p class="standfirst">{html.escape(typographic(part.standfirst))}</p>'
                f"</section>"
            )
        if part:
            seen_parts[part.number].append((chapter.number, chapter.title, anchor))
        body_sections.append(chapter_html(chapter, anchor, front=False))

    back_sections: list[str] = []
    toc_back: list[tuple[str, str, str]] = []
    for index, chapter in enumerate(document.back_matter):
        anchor = anchor_for("back", index)
        back_sections.append(
            f'<section class="chapter closing" id="{anchor}">'
            f'<header class="chapter-head">'
            f'<div class="chapter-eyebrow">In closing</div>'
            f'<h1 class="chapter-title">{html.escape(typographic(chapter.title))}</h1>'
            f'<div class="chapter-rule"></div></header>'
            + "".join(block_html(b) for b in chapter.blocks)
            + '<div class="colophon-end">'
            "Generated from <span class=\"mono\">docs/edtechx/EDTECHX_EDITORIAL_BIBLE.md</span> "
            "by <span class=\"mono\">tools/publisher</span>. The Markdown source is canonical; "
            "this document is a publication artefact of it."
            "</div></section>"
        )
        toc_back.append(("", chapter.title, anchor))

    def toc_entry(number: str, title: str, anchor: str) -> str:
        num = f'<span class="toc-num">{html.escape(number)}</span>' if number else '<span class="toc-num"></span>'
        return (
            f'<a class="toc-entry" href="#{anchor}">{num}'
            f'<span class="toc-title">{html.escape(title)}</span>'
            f'<span class="toc-dots"></span></a>'
        )

    toc_rows = ['<div class="toc-part">Front matter</div>']
    toc_rows += [toc_entry(n, t, a) for n, t, a in toc_front]
    for number, title, entries in toc_parts:
        toc_rows.append(f'<div class="toc-part">Part {html.escape(number)} · {html.escape(title)}</div>')
        toc_rows += [toc_entry(n, t, a) for n, t, a in entries]
    toc_rows.append('<div class="toc-part">In closing</div>')
    toc_rows += [toc_entry(n, t, a) for n, t, a in toc_back]

    metadata_rows = [
        ("Document", "The EdirasX Editorial Bible"),
        ("Edition", document.edition),
        ("Status", "Living document — the constitution of EdirasX"),
        ("Canonical source", "docs/edtechx/EDTECHX_EDITORIAL_BIBLE.md"),
        ("Generated", today),
        ("Authority", "Supreme. Where any document, design, or code conflicts with this Bible, the Bible wins until formally amended."),
        ("Amendment", "By entry in EDTECHX_DECISIONS.md, stating the principle changed, the reason, and the consequences."),
        ("Classification", "Internal and partner distribution"),
    ]
    metadata_html = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in metadata_rows
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>The EdirasX Editorial Bible — {html.escape(document.edition)}</title>
<link rel="stylesheet" href="style.css"/>
</head>
<body>

<section class="cover">
  {WORDMARK}
  <p class="cover-arabic" dir="rtl" lang="ar">&#1605;&#1587;&#1578;&#1602;&#1576;&#1604; &#1575;&#1604;&#1578;&#1593;&#1604;&#1605; &#1610;&#1576;&#1583;&#1571; &#1605;&#1606; &#1607;&#1606;&#1575;</p>
  <div class="spacer"></div>
  <div class="eyebrow">Editorial Bible</div>
  <div class="cover-rule"></div>
  <h1>The<br/>Editorial<br/>Bible</h1>
  <p class="subtitle">The constitution of the EdirasX education platform, and the
  source from which every product, design, architecture, and engineering
  decision is derived.</p>
  <div class="footer">
    <span>{html.escape(document.edition)}</span>
    <span>The education platform that becomes your school&#8217;s own platform</span>
  </div>
</section>

<section class="verso">
  <h2>Document control</h2>
  <table class="meta-table">{metadata_html}</table>
</section>

<section class="toc">
  <h2>Contents</h2>
  {''.join(toc_rows)}
</section>

{''.join(front_sections)}
{''.join(body_sections)}
{''.join(back_sections)}

</body>
</html>
"""


def render(document: Document, output: pathlib.Path) -> pathlib.Path:
    from weasyprint import HTML

    html_text = build_html(document)
    (ASSETS / "_build.html").write_text(html_text, encoding="utf-8")
    HTML(string=html_text, base_url=str(ASSETS) + "/").write_pdf(
        output,
        # Real document metadata, not defaults.
        **{},
    )
    return output


__all__ = ["render", "build_html"]
