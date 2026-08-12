"""The administrative architecture: identifiers, barcode, verification panel.

This is where EdirasX was short, and the shortfall was not ornamental. Put an
EdirasX plate beside an issued Sultan Hanafi sheet and the EdirasX one is
*ceremonial* — frame, cartouche, seal, engraving — while the other is
**official**. The difference is almost entirely in this file's subject matter:
five labelled identifiers instead of two unlabelled ones, a verification panel
with a masthead of its own, a machine-readable mark, a labelled data register
where the issue date is a *field* rather than a clause in a sentence, and a legal
void warning printed on the sheet.

A reader looking for the date of award should find a field. A registrar checking
the archive should find a reference. A machine should find a barcode. None of
that is decoration and none of it is optional on an instrument.

**The barcode is real.** `code128c` implements Code 128 subset C properly —
the 107-symbol width table, the modulo-103 running checksum, the 13-module stop
— and emits bars in millimetres at a stated module width. It is verifiable by
arithmetic rather than by hoping: `test_credential.py` checks the checksum
against the worked example in the specification and counts the modules.

**The QR is deliberately not drawn.** A correct QR needs Reed–Solomon over
GF(256), a mask evaluation and format/version information, and this environment
has no decoder to prove the result scans. Drawing a plausible grid of squares
that is not a valid QR would be precisely the theatre this codebase refuses — a
mark that *looks* machine-readable and is not is worse than no mark, because
somebody will rely on it. So the bay is reserved, captioned, and dimensioned,
and `qr_bay()` says in its own output that it is a reservation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.modules.design import geometry as geo
from app.modules.design.gilding import Scheme, engraved_metal_rule

__all__ = [
    "Credential",
    "code128c",
    "number_cartouche",
    "qr_bay",
    "verification_cartouche",
]


@dataclass(frozen=True, slots=True)
class Credential:
    """Everything a sheet must carry so it can be checked without being trusted.

    Five identifiers, because the benchmark sheets carry five and each answers a
    different question:

        document_id        which record in the issuing system
        verification_code  what a member of the public types in
        archive_reference  where the paper copy is filed
        identity_number    which person, across every document they hold
        certificate_number the number printed on this class of certificate

    The identity number appears twice on a finished sheet — once in the
    ceremonial field beneath the recipient's name, tying the person to the
    record, and once in the administrative panel, tying the sheet to the archive.
    That repetition is deliberate and is not a duplication to be tidied away.
    """

    document_id: str
    verification_code: str
    archive_reference: str
    identity_number: str
    certificate_number: str
    verify_url: str = "edirasx.com/verify"
    #: Printed on every sheet, in the panel's footer. A legal statement, not a
    #: decorative one, and the wording is deliberately about the *sheet* rather
    #: than about the holder.
    void_notice: str = "VOID IF ALTERED, ERASED OR REPRODUCED"

    @property
    def barcode_digits(self) -> str:
        """The digits Code 128-C carries: the identity number, even-length.

        Subset C encodes pairs, so an odd-length value cannot be represented
        without a subset switch. Rather than switch — which changes the symbol
        and the checksum, and is a decision a printer needs to know about — the
        value is zero-padded on the left, which preserves it numerically.
        """
        digits = "".join(c for c in self.identity_number if c.isdigit())
        return digits if len(digits) % 2 == 0 else "0" + digits


#: Code 128 element widths, symbol 0 → 106. Six elements per symbol (bar, space,
#: bar, space, bar, space) except the stop, which has seven. Reproduced from the
#: specification; the checksum test is what proves it was reproduced correctly.
_C128: Final[tuple[str, ...]] = (
    "212222", "222122", "222221", "121223", "121322", "131222", "122213",
    "122312", "132212", "221213", "221312", "231212", "112232", "122132",
    "122231", "113222", "123122", "123221", "223211", "221132", "221231",
    "213212", "223112", "312131", "311222", "321122", "321221", "312212",
    "322112", "322211", "212123", "212321", "232121", "111323", "131123",
    "131321", "112313", "132113", "132311", "211313", "231113", "231311",
    "112133", "112331", "132131", "113123", "113321", "133121", "313121",
    "211331", "231131", "213113", "213311", "213131", "311123", "311321",
    "331121", "312113", "312311", "332111", "314111", "221411", "431111",
    "111224", "111422", "121124", "121421", "141122", "141221", "112214",
    "112412", "122114", "122411", "142112", "142211", "241211", "221114",
    "413111", "241112", "134111", "111242", "121142", "121241", "114212",
    "124112", "124211", "411212", "421112", "421211", "212141", "214121",
    "412121", "111143", "111341", "131141", "114113", "114311", "411113",
    "411311", "113141", "114131", "311141", "411131", "211412", "211214",
    "211232", "2331112",
)

_START_C: Final[int] = 105
_STOP: Final[int] = 106


def code128c(digits: str, *, x: float, y: float, height: float,
             module: float = 0.33, ink: str = "#000000") -> str:
    """A Code 128 subset C barcode, in millimetres.

    Subset C encodes two digits per symbol, which is why an identity number is
    the right payload for it: fifteen digits become eight symbols rather than
    fifteen, and the symbol is short enough to sit inside a 62mm panel.

    The checksum is the specification's: start value plus the sum of each data
    value times its one-based position, modulo 103. It is emitted, not omitted —
    a Code 128 symbol without its check character is not a Code 128 symbol.

    `module` is the narrow-element width. **0.33mm is the floor**: below about
    0.25mm the bars close up under ink gain on an offset press and the symbol
    stops scanning, and the mark is worthless the moment it stops scanning.
    Drawn in pure black, and the production specification asks the printer to
    keep it 100 % K for the same reason.
    """
    if len(digits) % 2 or not digits.isdigit():
        raise ValueError(
            "Code 128-C carries pairs of digits; pad to an even length first "
            "(see Credential.barcode_digits)."
        )
    values = [int(digits[i:i + 2]) for i in range(0, len(digits), 2)]
    checksum = _START_C
    for position, value in enumerate(values, start=1):
        checksum += position * value
    symbols = [_START_C, *values, checksum % 103, _STOP]

    bars: list[str] = []
    cursor = x
    for symbol in symbols:
        for index, width in enumerate(_C128[symbol]):
            span = int(width) * module
            if index % 2 == 0:  # even elements are bars
                bars.append(
                    f'<rect x="{cursor:.3f}" y="{y:.2f}" width="{span:.3f}"'
                    f' height="{height:.2f}" fill="{ink}"/>'
                )
            cursor += span
    return "".join(bars)


def code128c_width(digits: str, *, module: float = 0.33) -> float:
    """The symbol's width in mm, so a panel can be laid out before it is drawn."""
    symbol_count = len(digits) // 2 + 3  # start + data + check + stop
    return (symbol_count * 11 + 2) * module


def qr_bay(rect: geo.Rect, *, scheme: Scheme, ink: str,
           caption: str = "VERIFY AUTHENTICITY") -> str:
    """A reserved, dimensioned bay for a QR — **not a QR**.

    Drawn as an empty panel with its three finder-pattern positions marked as
    outlines and the words `QR RESERVED` set inside it, so nobody can mistake it
    for a scannable mark or ship it believing one is present. A correct QR needs
    Reed–Solomon over GF(256), mask evaluation and format information, and this
    environment has no decoder to prove the result scans; a grid of squares that
    looks like a QR and is not one is worse than an empty bay, because somebody
    will rely on it.

    The bay is real work all the same: it fixes the size, the quiet zone and the
    caption, so the encoder drops in without the composition moving.
    """
    # Drawn as one quiet tinted panel with a diagonal rule and a single line of
    # text. The first version outlined three finder-pattern positions, which on
    # a finished sheet read as empty checkboxes — a form somebody forgot to
    # fill in rather than a bay held open on purpose.
    inner = rect.inset(min(rect.w, rect.h) * 0.08)
    return (
        f'<rect {rect.attrs()} fill="none" stroke="{scheme.secondary.face}"'
        ' stroke-width="0.34"/>'
        f'<rect {inner.attrs()} fill="{geo.tint(ink, 0.055)}"/>'
        f'<path d="M{inner.x:.2f} {inner.y + inner.h:.2f} '
        f'L{inner.x + inner.w:.2f} {inner.y:.2f}" stroke="{geo.tint(ink, 0.16)}"'
        ' stroke-width="0.20"/>'
        + f'<text x="{rect.cx:.2f}" y="{inner.cy + 0.7:.2f}"'
        f' text-anchor="middle" font-size="1.85" letter-spacing="0.10"'
        f' font-family="Inter, sans-serif" fill="{geo.tint(ink, 0.50)}">'
        f'QR BAY RESERVED</text>'
        + f'<text x="{rect.cx:.2f}" y="{rect.y + rect.h + 2.6:.2f}"'
        f' text-anchor="middle" font-size="1.7" letter-spacing="0.30"'
        f' font-family="Inter, sans-serif" fill="{geo.tint(ink, 0.55)}">'
        f"{caption}</text>"
    )


def verification_cartouche(rect: geo.Rect, credential: Credential, *,
                           scheme: Scheme, ink: str, institution: str,
                           mark: str = "", paper: str = "#F7F2E6") -> str:
    """The verification panel: a document within the document.

    A masthead of its own, a 2 × 2 grid of labelled identifiers, the barcode
    across the full inner measure, and a footer carrying the verification URL
    and the void notice. That structure is what makes it read as an instrument
    rather than as a caption — the benchmark sheets all carry it and it is the
    single largest thing EdirasX was missing.

    Laid out in millimetres against `rect` so it can be placed by a plate and
    separated by a printer; the barcode's module width is checked against the
    space available and the panel refuses to draw a symbol it would have to
    squeeze, because a squeezed Code 128 does not scan.
    """
    metal = scheme.secondary
    label = geo.tint(ink, 0.52)
    body = geo.tint(ink, 0.92)
    out: list[str] = [
        f'<rect {rect.attrs()} fill="none" stroke="{metal.face}"'
        ' stroke-width="0.42"/>',
        f'<rect {rect.inset(0.9).attrs()} fill="none"'
        f' stroke="{scheme.engraved.shadow}" stroke-width="0.14"/>',
    ]

    # --- masthead ---
    head_y = rect.y + 4.4
    out.append(engraved_metal_rule(rect.x + 2.2, head_y, rect.x + rect.w - 2.2,
                                   head_y, metal=metal, weight=0.22))
    out.append(
        # The masthead knocks the rule out behind itself, and it must knock it
        # out in the *paper*, not in white: on an ivory ground a white patch
        # is a visible rectangle, which is how a knockout announces itself.
        f'<rect x="{rect.cx - 17:.2f}" y="{head_y - 3.2:.2f}" width="34"'
        f' height="4.2" fill="{paper}"/>'
        f'<text x="{rect.cx:.2f}" y="{head_y - 0.2:.2f}" text-anchor="middle"'
        f' font-size="1.95" letter-spacing="0.34"'
        f' font-family="Inter, sans-serif" font-weight="600" fill="{label}">'
        f"{mark or 'CERTIFICATE VERIFICATION'}</text>"
    )

    # --- the 2 x 2 identifier grid ---
    cells = (
        ("DOCUMENT ID", credential.document_id),
        ("VERIFICATION CODE", credential.verification_code),
        ("ARCHIVE REFERENCE", credential.archive_reference),
        ("STUDENT IDENTITY NO.", credential.identity_number),
    )
    col = (rect.w - 5.0) / 2
    for index, (name, value) in enumerate(cells):
        cx = rect.x + 2.6 + (index % 2) * (col + 2.4)
        cy = rect.y + 7.8 + (index // 2) * 6.0
        out.append(
            f'<text x="{cx:.2f}" y="{cy:.2f}" font-size="1.65"'
            f' letter-spacing="0.20" font-family="Inter, sans-serif"'
            f' fill="{label}">{name}</text>'
            f'<text x="{cx:.2f}" y="{cy + 3.3:.2f}" font-size="2.05"'
            f' font-family="IBM Plex Mono, monospace" fill="{body}">'
            f"{value}</text>"
        )

    # --- the barcode, sized to the panel rather than squeezed into it ---
    digits = credential.barcode_digits
    available = rect.w - 6.0
    module = min(0.40, available / max(1.0, code128c_width(digits, module=1.0)))
    if module >= 0.33:
        symbol = code128c_width(digits, module=module)
        out.append(code128c(digits, x=rect.cx - symbol / 2,
                            y=rect.y + 18.2, height=3.5, module=module))
    else:
        # Stated, not silently dropped: a Code 128 below a 0.33mm module closes
        # up under ink gain and stops scanning, and a mark that does not scan is
        # worse than an absent one.
        out.append(
            f'<text x="{rect.cx:.2f}" y="{rect.y + 26.0:.2f}"'
            f' text-anchor="middle" font-size="1.9"'
            f' font-family="Inter, sans-serif" fill="{label}">'
            "BARCODE OMITTED — PANEL TOO NARROW FOR A 0.33 MM MODULE</text>"
        )

    # --- footer: the URL and the void notice ---
    foot_y = rect.y + rect.h - 2.0
    out.append(engraved_metal_rule(rect.x + 2.2, foot_y - 1.9,
                                   rect.x + rect.w - 2.2, foot_y - 1.9,
                                   metal=metal, weight=0.18))
    out.append(
        f'<text x="{rect.cx:.2f}" y="{foot_y:.2f}" text-anchor="middle"'
        f' font-size="1.50" letter-spacing="0.10"'
        f' font-family="Inter, sans-serif" fill="{label}">'
        f"{credential.verify_url.upper()} · {credential.void_notice}</text>"
    )
    return "".join(out)


def number_cartouche(rect: geo.Rect, number: str, *, scheme: Scheme,
                     ink: str, motif=None,
                     paper: str = "#F7F2E6") -> str:
    """The certificate number, in a guilloché-filled panel of its own.

    Separate from the verification cartouche on purpose: on the benchmark sheets
    it sits opposite the seal and balances it, and keeping the *printed* number
    away from the *machine-readable* panel means a torn corner does not take
    both. The lathe fill is what stops it reading as a box with a number in it.
    """
    metal = scheme.secondary
    out = [
        f'<rect {rect.attrs()} fill="none" stroke="{metal.face}"'
        ' stroke-width="0.40"/>',
        f'<rect {rect.inset(0.8).attrs()} fill="none"'
        f' stroke="{scheme.engraved.shadow}" stroke-width="0.14"/>',
    ]
    if motif is not None:
        # The fill has to *read*, or the panel is a box with a number in it —
        # which is what the first render produced. A lathe figure wider than
        # the panel, clipped by it, fills the whole field instead of sitting as
        # a small rosette in the middle of it.
        tag = f"num-{abs(hash((rect.x, rect.y, number))) % 999999}"
        out.append(
            f'<defs><clipPath id="{tag}"><rect {rect.inset(1.2).attrs()}/>'
            "</clipPath></defs>"
            f'<g clip-path="url(#{tag})">'
            + motif.guilloche(rect.cx, rect.cy, rect.w * 0.62,
                              ink=scheme.security.core, width=0.07,
                              strength=0.85, passes=3)
            + motif.guilloche(rect.cx, rect.cy, rect.w * 0.34,
                              ink=scheme.primary.core, width=0.07,
                              strength=0.55, passes=2)
            + "</g>"
        )
        # A knockout behind the number, so the lathe does not run through it.
        out.append(
            f'<rect x="{rect.cx - rect.w * 0.34:.2f}"'
            f' y="{rect.y + rect.h * 0.42:.2f}" width="{rect.w * 0.68:.2f}"'
            f' height="{rect.h * 0.44:.2f}" fill="{paper}" opacity="0.88"/>'
        )
    out.append(
        f'<text x="{rect.cx:.2f}" y="{rect.y + 3.4:.2f}" text-anchor="middle"'
        f' font-size="1.62" letter-spacing="0.30"'
        f' font-family="Inter, sans-serif" fill="{geo.tint(ink, 0.52)}">'
        "CERTIFICATE NUMBER</text>"
        f'<text x="{rect.cx:.2f}" y="{rect.y + rect.h - 2.2:.2f}"'
        f' text-anchor="middle" font-size="3.4" letter-spacing="0.06"'
        f' font-family="IBM Plex Mono, monospace" fill="{geo.tint(ink, 0.94)}">'
        f"{number}</text>"
    )
    return "".join(out)
