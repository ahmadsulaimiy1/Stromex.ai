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
#:
#: The four interface families come first; the four below them are the
#: **ceremonial** faces, and they exist because a certificate is not a screen.
#: A document family needs a display face with real stroke contrast — the thing
#: that makes engraved type look engraved — and an Arabic face heavy enough to
#: hold a title rather than a caption:
#:
#:   Fraunces 300/600/900   high-contrast display serif. The ceremonial name,
#:                          the title moment, the qualification.
#:   Archivo 400/700        a grotesque with enough width to be monumental at
#:                          display size, for the contemporary directions.
#:   Amiri 700              Naskh at title weight, so Arabic can be a principal
#:                          element instead of a translation underneath.
#:   Cairo 400/700          a modern Arabic sans, the counterpart to Archivo.
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
    ("Fraunces", "Fraunces-300.woff2", "300", "normal"),
    ("Fraunces", "Fraunces-600.woff2", "600", "normal"),
    ("Fraunces", "Fraunces-900.woff2", "900", "normal"),
    ("Archivo", "Archivo-400.woff2", "400", "normal"),
    ("Archivo", "Archivo-700.woff2", "700", "normal"),
    ("Amiri", "Amiri-700.woff2", "700", "normal"),
    ("Cairo", "Cairo-400.woff2", "400", "normal"),
    ("Cairo", "Cairo-700.woff2", "700", "normal"),
)

#: The document roles, and which real family fills each. Named because the
#: earlier flagship stylesheet asked for `'EdirasX Display'` — a family nothing
#: in this file ever declared — and silently set the whole certificate in
#: Georgia. A role table that resolves to declared families makes that class of
#: mistake impossible to write.
ROLES: dict[str, str] = {
    "display": "Fraunces",
    "display-alt": "Source Serif 4",
    "display-modern": "Archivo",
    "body": "Source Serif 4",
    "ui": "Inter",
    "arabic": "Amiri",
    "arabic-modern": "Cairo",
    "mono": "IBM Plex Mono",
}

_MIME = {"ttf": "font/ttf", "woff2": "font/woff2"}
_FORMAT = {"ttf": "truetype", "woff2": "woff2"}


@functools.cache
def _data_uri(name: str) -> str:
    raw = (fonts_root() / name).read_bytes()
    kind = name.rsplit(".", 1)[-1]
    return (
        f"data:{_MIME[kind]};base64," + base64.b64encode(raw).decode("ascii")
    )


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
        fmt = _FORMAT[filename.rsplit(".", 1)[-1]]
        blocks.append(
            f"@font-face{{font-family:'{family}';src:url('{source}') format('{fmt}');"
            f"font-weight:{weight};font-style:{style};font-display:swap;}}"
        )
    return "\n".join(blocks)


def stack(role: str, *, fallback: str = "serif") -> str:
    """A CSS font stack for a document role.

    Always resolves to a family this module actually declares. Asking for a role
    that does not exist raises rather than falling through to a system face,
    because a certificate set in the wrong typeface is a defect nobody notices
    until it is printed.
    """
    if role not in ROLES:
        raise ValueError(
            f"{role!r} is not a document type role. One of: "
            + ", ".join(sorted(ROLES))
        )
    return f"'{ROLES[role]}', {fallback}"
