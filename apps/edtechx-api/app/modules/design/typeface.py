"""Where the type comes from.

Three families, chosen for a relationship rather than assembled from what was
available.

**Source Serif 4** carries identity. An institution's name, a page title and a
large figure are set in it, and that is most of why a screen reads as editorial
rather than as a form. It has real optical range and a genuine italic, which
matters at 60px.

**Inter** carries work. Tables, labels, controls, dense data. It is a common
choice and that is fine: the interface face should be invisible, and the
identity is carried by the display face, the gold, the geometry and the
proportions. A distinctive UI face is a distraction in a register of four
hundred children.

**Amiri** carries Arabic, and is not a fallback. It is a naskh face of genuine
quality, set at 1.15× to sit level with the Latin, with its own line height
because Arabic needs more. EdirasX is named from الدراسة; treating Arabic as
something the Latin stack falls through to would be the product contradicting
its own name.

**IBM Plex Mono** carries reference numbers, codes and verification strings —
anything a person reads aloud or types back.

Fonts are embedded as data URIs when a document has to survive on its own, and
linked when a page is served. The choice is the caller's because the trade is
real: a self-contained transcript that opens in 2031 is worth 1.5 MB, and a
dashboard reloaded forty times a day is not.
"""

from __future__ import annotations

import base64
import functools
import pathlib

__all__ = ["FACES", "font_face_css", "fonts_root"]


@functools.cache
def fonts_root() -> pathlib.Path:
    """The font directory, shared with the publisher rather than duplicated.

    One copy of Inter in the repository. Two copies is how a product ends up
    with a document set in a slightly different weight from its interface.
    """
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "tools" / "publisher" / "assets" / "fonts"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "The EdirasX typefaces are missing. They live in "
        "tools/publisher/assets/fonts and are shared between the interface and "
        "the publication pipeline."
    )


#: `(css family, file, weight, style)`.
FACES: tuple[tuple[str, str, str, str], ...] = (
    ("Source Serif 4", "SourceSerif4-400.ttf", "400", "normal"),
    ("Source Serif 4", "SourceSerif4-400i.ttf", "400", "italic"),
    ("Source Serif 4", "SourceSerif4-600.ttf", "600", "normal"),
    ("Source Serif 4", "SourceSerif4-700.ttf", "700", "normal"),
    ("Inter", "Inter-400.ttf", "400", "normal"),
    ("Inter", "Inter-500.ttf", "500", "normal"),
    ("Inter", "Inter-600.ttf", "600", "normal"),
    ("Inter", "Inter-700.ttf", "700", "normal"),
    ("IBM Plex Mono", "IBMPlexMono-400.ttf", "400", "normal"),
    ("IBM Plex Mono", "IBMPlexMono-600.ttf", "600", "normal"),
    ("Amiri", "Amiri-400.ttf", "400", "normal"),
)


@functools.cache
def _data_uri(name: str) -> str:
    raw = (fonts_root() / name).read_bytes()
    return "data:font/ttf;base64," + base64.b64encode(raw).decode("ascii")


def font_face_css(*, embed: bool = False, base_url: str = "/static/fonts") -> str:
    """`@font-face` rules for the whole system.

    `embed=True` inlines every face as a data URI, for an artefact that must
    render without the server it came from. `swap` on every face, because a page
    that shows nothing while a 300 KB serif downloads is a page that looks
    broken on a school's connection.
    """
    blocks: list[str] = []
    for family, filename, weight, style in FACES:
        source = _data_uri(filename) if embed else f"{base_url}/{filename}"
        blocks.append(
            f"@font-face{{font-family:'{family}';src:url('{source}') format('truetype');"
            f"font-weight:{weight};font-style:{style};font-display:swap;}}"
        )
    return "\n".join(blocks)
