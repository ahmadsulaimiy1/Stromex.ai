"""Book -> PDF export, rendered with WeasyPrint against the StromeX
publication design system (see docs/brand/editorial-system.md): Fraunces for
display, Archivo for Latin body copy, Amiri/Cairo for Arabic, brass/ink/stone
palette. Fonts are embedded from local files so output is identical
regardless of what is installed on the server.
"""

import html
import re
from pathlib import Path

import markdown as md
from weasyprint import HTML

from app.db.models.book import Book, BookLanguage

_FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

_INK = "#17140F"
_MUTED = "#55543F"
_BRASS = "#8A6526"
_STONE = "#E7EAE2"
_RULE = "#C8CABF"


def _font_face(family: str, filename: str, weight: int) -> str:
    path = _FONTS_DIR / filename
    return f"""
    @font-face {{
        font-family: '{family}';
        src: url('{path.as_uri()}') format('woff2');
        font-weight: {weight};
        font-style: normal;
    }}"""


def _base_css() -> str:
    faces = "".join([
        _font_face("Fraunces", "Fraunces-300-normal.woff2", 300),
        _font_face("Fraunces", "Fraunces-600-normal.woff2", 600),
        _font_face("Fraunces", "Fraunces-900-normal.woff2", 900),
        _font_face("Archivo", "Archivo-400-normal.woff2", 400),
        _font_face("Archivo", "Archivo-700-normal.woff2", 700),
        _font_face("Amiri", "Amiri-400-normal.woff2", 400),
        _font_face("Amiri", "Amiri-700-normal.woff2", 700),
        _font_face("Cairo", "Cairo-400-normal.woff2", 400),
        _font_face("Cairo", "Cairo-700-normal.woff2", 700),
    ])
    return f"""
    {faces}
    @page {{
        size: A4;
        margin: 2.4cm 2cm;
        @bottom-center {{
            content: counter(page);
            font-family: Archivo, sans-serif;
            font-size: 9pt;
            color: {_MUTED};
        }}
    }}
    body {{ font-family: Archivo, sans-serif; color: {_INK}; font-size: 11pt; line-height: 1.6; }}
    h1, h2, h3 {{ font-family: Fraunces, serif; color: {_INK}; }}
    .cover {{ page-break-after: always; text-align: center; padding-top: 30%; }}
    .cover .title {{ font-family: Fraunces, serif; font-weight: 300; font-size: 34pt; margin: 0; }}
    .cover .subtitle {{ font-family: Fraunces, serif; font-weight: 600; font-size: 16pt; color: {_BRASS}; margin-top: 0.4cm; }}
    .cover .author {{ margin-top: 2cm; font-size: 12pt; color: {_MUTED}; }}
    .chapter {{ page-break-before: always; }}
    .chapter .kicker {{ font-size: 9pt; letter-spacing: 0.1em; text-transform: uppercase; color: {_MUTED}; }}
    .chapter h1 {{ font-weight: 600; font-size: 22pt; border-bottom: 1pt solid {_RULE}; padding-bottom: 0.3cm; }}
    p {{ margin: 0 0 0.4cm 0; text-align: justify; }}
    .rtl {{ direction: rtl; text-align: right; font-family: Cairo, sans-serif; }}
    .rtl h1, .rtl h2, .rtl h3 {{ font-family: Amiri, serif; }}
    """


def _render_content(content_markdown: str, language: BookLanguage) -> str:
    body_html = md.markdown(content_markdown, extensions=["extra", "sane_lists"])
    css_class = "rtl" if language == BookLanguage.AR else ""
    return f'<div class="{css_class}">{body_html}</div>'


def render_book_pdf(book: Book) -> bytes:
    """Render every chapter (in order) to a single paginated PDF. Raises
    whatever WeasyPrint raises on malformed input — callers must not swallow
    that silently, per the no-placeholder-failure-modes rule."""

    cover = f"""
    <div class="cover">
        <p class="title">{html.escape(book.title)}</p>
        {f'<p class="subtitle">{html.escape(book.subtitle)}</p>' if book.subtitle else ""}
        <p class="author">{html.escape(book.author_name)}</p>
    </div>
    """

    chapters_html = []
    for chapter in book.chapters:
        rendered = _render_content(chapter.content_markdown, book.language)
        chapters_html.append(f"""
        <section class="chapter">
            <p class="kicker">Chapter {chapter.order_index + 1}</p>
            <h1>{html.escape(chapter.title)}</h1>
            {rendered}
        </section>
        """)

    document_html = f"""
    <html>
    <head><meta charset="utf-8"><style>{_base_css()}</style></head>
    <body>
        {cover}
        {"".join(chapters_html)}
    </body>
    </html>
    """

    return HTML(string=document_html).write_pdf()
