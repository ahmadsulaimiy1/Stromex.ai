"""Rendering an imported template: from a filled `Template` to a printable sheet.

`library.py` holds what each imported document *is*. This file turns one into a
sheet: the heritage ground underneath, the ceremonial field flowed over it, the
verification instrument pinned to the foot.

**Three compositions, not one with switches.** A landscape ceremonial sheet and
a portrait administrative record are different objects, and the difference is
not a parameter. The stage sheet puts one name at the optical centre with a
two-column citation beneath it; the college sheet adds a conferred-award
register between the citation and the foot, because the award is a different
statement from the citation; the record sheet is a column under a masthead with
a pinned administrative foot. Each is written out. Nothing here scales one into
another.

**Flow, not coordinates.** The field is a flex column with flexible spacers, so
a long name or a two-line office title pushes the composition rather than
overprinting it. The administrative foot is pinned — it is the last thing on
the sheet and it may not be moved by the length of a citation above it. This is
the arrangement that survived the collision audit; a coordinate-placed field
passes on the specimen data and fails on the real data, which is the failure
mode nobody catches until it is printed.

**No script tests.** Every content slot goes through the document's language
architecture, which returns runs. There is no `if arabic:` in this file, and a
template that sets one script produces the one-run layout as the same rule with
one run — not as a fallback.

**Nothing is claimed that is not drawn.** The security registers listed on a
template are the registers this renderer actually emits. Where a template
declares a QR, the sheet carries a reserved, dimensioned QR bay rather than a
picture of a QR code: EdirasX does not mint the code here, the issuing service
does, and drawing a decorative substitute would put an unscannable square on a
document whose whole purpose is to be scanned.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.design import geometry as geo
from app.modules.design.ceremony import budget_for
from app.modules.design.credential import (
    Credential,
    number_cartouche,
    qr_bay,
    verification_cartouche,
)
from app.modules.design.gilding import scheme_for
from app.modules.design.heraldry import seal_with_device
from app.modules.design.heritage import heritage_ground
from app.modules.design.language import Architecture, Phrase, architecture_for
from app.modules.design.sheets import Fit, Sheet, fits, sheet_for
from app.modules.design.signature import motif_for
from app.modules.design.typeface import font_face_css
from app.modules.documents.library import (
    MEASURED_OVERFLOWS,
    Filled,
    Template,
    Wording,
)

__all__ = ["Rendered", "SheetTooSmall", "credential_for", "render",
           "sheet_for_template"]


class SheetTooSmall(ValueError):
    """This document cannot honestly be printed at this size.

    Raised rather than shrunk. A verification panel squeezed until it
    fits is a panel that cannot be scanned, and a document that has lost
    the property it exists to have is not a smaller version of itself.
    The message carries the arithmetic so the caller can choose a sheet
    rather than guess at one.
    """

#: Faces, by the role the language architecture names. Keyed on the *script*,
#: never on a language: a Latin display face applied to an Arabic run is how a
#: bilingual document ends up with one script beautifully set and the other in
#: the browser's default.
_FACE = {
    "display": "Fraunces", "display-alt": "Source Serif 4",
    "display-modern": "Archivo", "body": "Source Serif 4",
    "arabic": "Amiri", "arabic-modern": "Cairo", "ui": "Inter",
    "mono": "IBM Plex Mono",
}


def _escape(value: str) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


@dataclass(frozen=True, slots=True)
class Rendered:
    """A rendered sheet and the facts a caller needs about it."""

    html: str
    width: float
    height: float
    field: geo.Rect
    template: Template
    sheet: Sheet
    fit: Fit

    @property
    def type_scale(self) -> float:
        return self.fit.type_scale


def credential_for(filled: Filled) -> Credential:
    """Build the credential from the template's own slots.

    The five identifiers are read off the filled template rather than composed
    here, because the issuing register mints them and a renderer that invents
    one has printed a number that verifies against nothing.
    """
    return Credential(
        document_id=filled.value("document_id"),
        verification_code=filled.value("verification_code"),
        archive_reference=filled.value("archive_reference"),
        identity_number=filled.value("student_id"),
        certificate_number=filled.value("serial"),
        verify_url=filled.value("verify_url") or "verify.example.edu",
        void_notice=filled.template.verification.void_en.upper(),
    )


def _phrase(filled: Filled, wording: Wording) -> Phrase:
    """One bilingual slot, resolved into the architecture's script keys."""
    text = filled.text(wording)
    out: dict[str, str] = {}
    if text.en.strip():
        out["latin"] = text.en.strip()
    if text.ar.strip():
        out["arabic"] = text.ar.strip()
    return Phrase(out)


def _runs(architecture: Architecture, filled: Filled, wording: Wording, *,
          cls: str, base: float, lead_only: bool = False,
          inline: bool = False) -> str:
    """Set one slot. Returns nothing at all when the slot is empty.

    Not an empty element and not a placeholder: an empty `<div>` with a margin
    is a gap on the sheet that a reader reads as a missing line, and a
    placeholder is how `{recipient}` gets printed on a real certificate.
    """
    runs = architecture.resolve(_phrase(filled, wording))
    if lead_only:
        runs = tuple(run for run in runs if run.lead)[:1]
    if not runs:
        return ""
    cells: list[str] = []
    for run in runs:
        family = _FACE[run.script.face]
        style = (
            f"font-size:{base * run.scale:.2f}mm;"
            f"line-height:{run.script.leading};"
            f"direction:{run.direction};"
            f"font-family:'{family}',Georgia,serif"
        )
        lead = "is-lead" if run.lead else "is-sub"
        cells.append(
            f'<div class="{cls} {cls}--{run.script.key} {lead}"'
            f' style="{style}">{_escape(run.text)}</div>'
        )
    if inline and len(cells) > 1:
        return f'<div class="{cls}-row">' + "".join(cells) + "</div>"
    return "".join(cells)


def _peak(template: Template) -> Wording:
    """The slots the template names as its visual peak."""
    return Wording(
        en="{" + template.peak_slot + "}" if template.peak_slot else "",
        ar="{" + template.peak_slot_ar + "}" if template.peak_slot_ar else "",
    )


def _value_phrase(filled: Filled, key_en: str, key_ar: str = "") -> Wording:
    """A slot pair — the Latin value and its Arabic counterpart — as wording."""
    return Wording(en="{" + key_en + "}", ar=("{" + key_ar + "}") if key_ar else "")


# --- the pieces --------------------------------------------------------------


def _lockup(architecture: Architecture, filled: Filled, *, base: float,
            mark: str) -> str:
    """The institution's identity, arranged by the document's architecture.

    Peer puts the runs either side of the mark and removing either destroys the
    lockup, which is the test of whether a bilingual design is bilingual. One
    run produces the solo layout — the same rule, one run — and the design is
    complete rather than waiting for something that was never coming.
    """
    runs = architecture.resolve(
        _phrase(filled, Wording(en="{institution}", ar="{institution_ar}"))
    )
    if not runs:
        return ""

    def cell(run, align: str) -> str:
        return (
            f'<div class="lk lk--{run.script.key}" style="'
            f"font-size:{base * run.scale:.2f}mm;"
            f"line-height:{run.script.leading};direction:{run.direction};"
            f"text-align:{align};"
            f"font-family:'{_FACE[run.script.face]}',Georgia,serif\">"
            f"{_escape(run.text)}</div>"
        )

    if architecture.mode == "peer" and len(runs) >= 2:
        return (
            '<div class="lockup">'
            + cell(runs[0], "right") + mark + cell(runs[1], "left")
            + "</div>"
        )
    body = "".join(cell(run, "center") for run in runs)
    return f'<div class="lockup lockup--stack">{mark}<div class="lkcol">{body}</div></div>'


def _name_rule(width: float, *, scheme, ink: str) -> str:
    """The engraved rule under the recipient's name.

    Two flat strokes and a lozenge at the centre. The lozenge is not
    decoration: it marks the axis, which is what tells the eye the name above it
    is centred on the sheet rather than merely near the middle.
    """
    metal = scheme.role("primary")
    half = width / 2
    return (
        f'<svg class="namerule" viewBox="0 0 {width:.1f} 3" '
        f'preserveAspectRatio="none">'
        f'<line x1="0" y1="1.5" x2="{half - 3.2:.2f}" y2="1.5"'
        f' stroke="{metal.core}" stroke-width="0.30"/>'
        f'<line x1="{half + 3.2:.2f}" y1="1.5" x2="{width:.2f}" y2="1.5"'
        f' stroke="{metal.core}" stroke-width="0.30"/>'
        f'<path d="M{half:.2f} 0.3 L{half + 2.2:.2f} 1.5 L{half:.2f} 2.7'
        f' L{half - 2.2:.2f} 1.5 Z" fill="none" stroke="{metal.face}"'
        ' stroke-width="0.24"/>'
        f'<circle cx="{half:.2f}" cy="1.5" r="0.34" fill="{geo.tint(ink, 0.7)}"/>'
        "</svg>"
    )


def _register_band(architecture: Architecture, filled: Filled,
                   pairs: tuple[tuple[Wording, Wording], ...], *,
                   scheme, ink: str) -> str:
    """The particulars band: labelled values across the sheet's waist.

    Each cell carries its label in both scripts and its value once. The label
    is the thing that is bilingual; a date does not need translating, and
    setting it twice is how a band that fits becomes a band that does not.
    """
    cells: list[str] = []
    for label, value in pairs:
        text = filled.text(value)
        shown = (text.en or text.ar).strip()
        if not shown:
            continue
        heads = architecture.resolve(_phrase(filled, label))
        head = "".join(
            f'<span class="bk bk--{run.script.key}"'
            f' style="direction:{run.direction};'
            f"font-family:'{_FACE[run.script.face]}',sans-serif\">"
            f"{_escape(run.text)}</span>"
            for run in heads
        )
        both = " · ".join(p for p in (text.en.strip(), text.ar.strip()) if p)
        cells.append(
            f'<div class="bcell"><div class="bhead">{head}</div>'
            f'<div class="bval">{_escape(both if text.ar.strip() else shown)}</div></div>'
        )
    if not cells:
        return ""
    divider = (
        f'<i class="bdiv" style="background:{geo.tint(scheme.role("primary").core, 0.6)}"></i>'
    )
    return f'<div class="band">{divider.join(cells)}</div>'


def _signature_block(filled: Filled, template: Template, *, scheme, ink: str,
                     assets: dict[str, str]) -> str:
    """One cell per signatory: prepared ink, a rule, a name, an office.

    The ink box is a fixed height whether or not an asset was supplied, so the
    engraved rules across every signatory land on one baseline. Bottom-aligning
    them instead puts the middle rule high the moment one office title wraps —
    which is a defect a proof shows and a specification does not.

    Nothing is synthesised. A signatory with no prepared asset gets the rule and
    the name and an empty ink box, because a generated squiggle over a real
    person's name is a forgery of a signature, not a placeholder for one.
    """
    metal = scheme.role("primary")
    cells: list[str] = []
    for signatory in template.signatories:
        name = filled.value(signatory.name_slot)
        name_ar = filled.value(f"{signatory.key}_name_ar")
        asset = assets.get(signatory.ink_slot) or filled.value(signatory.ink_slot)
        ink_html = (
            f'<img class="ink" src="{_escape(asset)}" alt="">' if asset
            else '<span class="ink"></span>'
        )
        arabic = (
            f'<div class="nm-ar" dir="rtl">{_escape(name_ar)}</div>'
            if name_ar.strip() else ""
        )
        cells.append(
            f'<div class="sig">{ink_html}'
            f'<div class="nm">{_escape(name)}</div>{arabic}'
            f'<svg class="srule" viewBox="0 0 60 1.6" preserveAspectRatio="none">'
            f'<line x1="0" y1="0.7" x2="60" y2="0.7" stroke="{metal.core}"'
            ' stroke-width="0.22"/>'
            f'<line x1="0" y1="1.15" x2="60" y2="1.15"'
            f' stroke="{geo.tint(ink, 0.30)}" stroke-width="0.10"/></svg>'
            f'<div class="of">{_escape(signatory.role_en)}</div>'
            + (f'<div class="of-ar" dir="rtl">{_escape(signatory.role_ar)}</div>'
               if signatory.role_ar else "")
            + "</div>"
        )
    return "".join(cells)


def _seal(filled: Filled, template: Template, *, scheme, ink: str,
          radius: float, device: str) -> str:
    """The institution's seal, with its own device fitted inside the architecture.

    The device goes in a stated clear circle at 46 % of the radius, inside a
    turned field, an engraved rim and a legend ring carrying this document's
    serial. An uploaded logo therefore becomes part of a struck seal rather than
    a picture placed on top of one — which is the difference the institution
    studio was asked for.
    """
    motif = motif_for(institution=filled.value("institution") or template.key,
                      family=template.family)
    diameter = radius * 2 + 4
    body = seal_with_device(
        diameter / 2, diameter / 2, radius, motif=motif, scheme=scheme, ink=ink,
        legend=(filled.value("institution") or "").upper(),
        identifier=filled.value("serial"), device=device,
    )
    return (
        f'<div class="sealbox"><svg viewBox="0 0 {diameter:.1f} {diameter:.1f}">'
        f"{body}</svg></div>"
    )


def _verification(filled: Filled, template: Template, *, scheme, ink: str,
                  width: float, height: float, paper: str) -> str:
    """The verification instrument: cartouche, and a dimensioned QR bay beside it.

    The bay is reserved rather than filled. The code belongs to the issuing
    service and is minted against the record; a renderer that drew a
    placeholder square there would ship a certificate carrying an unscannable
    QR, and the one thing worse than no QR is a QR that fails.
    """
    credential = credential_for(filled)
    # The panel's masthead carries the institution's own short mark — its
    # initials — rather than the template's key. A verification panel headed
    # STAGE tells a reader which of our layouts it is, which is the one fact
    # about the document that is nobody's business but ours.
    initials = "".join(
        word[0] for word in filled.value("institution").split()
        if word[:1].isalpha()
    )[:5].upper()
    mark = initials or "VERIFICATION"
    bay = height
    panel = geo.Rect(0, 0, width - bay - 2.4, height)
    fragments = [
        verification_cartouche(
            panel, credential, scheme=scheme, ink=ink,
            institution=filled.value("institution"), mark=mark, paper=paper,
        ),
        qr_bay(geo.Rect(width - bay, 0, bay, bay), scheme=scheme, ink=ink),
    ] if template.verification.qr else [
        verification_cartouche(
            geo.Rect(0, 0, width, height), credential, scheme=scheme, ink=ink,
            institution=filled.value("institution"), mark=mark, paper=paper,
        )
    ]
    return (
        f'<div class="vbox"><svg viewBox="0 0 {width:.1f} {height:.1f}">'
        + "".join(fragments) + "</svg></div>"
    )


def _number(filled: Filled, template: Template, *, scheme, ink: str,
            width: float, height: float, paper: str) -> str:
    motif = motif_for(institution=filled.value("institution") or template.key,
                      family=template.family)
    body = number_cartouche(
        geo.Rect(0, 0, width, height), filled.value("serial"),
        scheme=scheme, ink=ink, motif=motif, paper=paper,
    )
    return (
        f'<div class="nbox"><svg viewBox="0 0 {width:.1f} {height:.1f}">'
        f"{body}</svg></div>"
    )


def _table(filled: Filled, template: Template, key: str, *, ink: str,
           scheme) -> str:
    """The tabular body of a register or a clearance sheet.

    Rows arrive as newline-separated, pipe-delimited text — the plainest thing
    an institution can paste in and the plainest thing to check by eye. A row
    with the wrong number of cells is padded rather than dropped, because a
    dropped row on a register is a graduand who is not on the register.
    """
    raw = filled.value(key).strip()
    heads = [filled.text(w).en for w in template.registers]
    if not raw:
        return ""
    body: list[str] = []
    for line in raw.splitlines():
        cells = [c.strip() for c in line.split("|")]
        cells += [""] * (len(heads) - len(cells))
        body.append(
            "<tr>" + "".join(f"<td>{_escape(c)}</td>" for c in cells[:len(heads)])
            + "</tr>"
        )
    head = "".join(f"<th>{_escape(h)}</th>" for h in heads)
    rule = geo.tint(scheme.role("primary").core, 0.45)
    return (
        f'<table class="rows" style="--rule:{rule}">'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


# --- the compositions --------------------------------------------------------


def _ceremonial(filled: Filled, *, architecture: Architecture, scheme, ink: str,
                paper: str, width: float, field: geo.Rect, device: str,
                assets: dict[str, str], award: bool, scale: float = 1.0) -> str:
    """The landscape ceremonial field: stage and college sheets.

    One peak, one citation, one award register where the family has one, one
    particulars band, one pinned foot. The spacers between them are flexible and
    the foot is not: a long citation costs the composition air, never the
    verification instrument.
    """
    template = filled.template
    measure = field.w
    mark = ""
    # Optical sizes, not chosen sizes. The field a full heritage border leaves
    # on an A4 landscape sheet is 221 × 134mm, and the composition below is
    # solved against that height rather than against a look — which is why the
    # peak is 7.6mm rather than the 9.2 it wants to be. A peak that has to be
    # shrunk after the fact is a composition that did not fit.
    parts = [
        _lockup(architecture, filled, base=3.3 * scale, mark=mark),
        _banner(architecture, filled, scale=scale),
        '<div class="spacer"></div>',
        _runs(architecture, filled, template.title, cls="ttl", base=5.8 * scale,
              inline=architecture.mode == "peer"),
        # The subtitle is the stage gloss on a stage sheet. A college sheet's
        # award is set once, in the conferred-award register below, and setting
        # it here as well cost 7.8mm of a 132mm field to say the same words
        # twice at two sizes.
        "" if award else _runs(architecture, filled, template.subtitle,
                              cls="sub", base=2.7 * scale),
        '<div class="spacer"></div>',
        _runs(architecture, filled, template.lede, cls="lede", base=2.9 * scale),
        _runs(architecture, filled, _peak(template), cls="name", base=7.2 * scale),
        _name_rule(measure * 0.62, scheme=scheme, ink=ink),
        '<div class="spacer"></div>',
        '<div class="cite">'
        + _runs(architecture, filled, template.statement, cls="stmt", base=2.75 * scale)
        + "</div>",
    ]
    if award:
        parts.append(
            '<div class="award">'
            + _runs(architecture, filled, template.award, cls="awd", base=2.9 * scale,
                    inline=True)
            + "</div>"
        )
    parts.append('<div class="spacer"></div>')
    # Stated explicitly rather than indexed out of `template.registers`. The
    # first version took the label from `registers[-3]`, which is "Student ID"
    # on a stage sheet and "Award" on an award sheet — so an award printed the
    # word AWARD over the holder's identity number. A label that is derived
    # from a position rather than named is a label that will eventually
    # describe the wrong value.
    parts.append(_register_band(
        architecture, filled,
        (
            (Wording(en="Student Identity Number",
                     ar="الرقم التعريفي للطالب"),
             _value_phrase(filled, "student_id")),
            (Wording(en="Date of Issue", ar="تاريخ الإصدار"),
             Wording(en="{issued_on}", ar="{issued_on_hijri}")),
            (Wording(en="Place of Issue", ar="مكان الإصدار"),
             Wording(en="{place}", ar="{place_ar}")),
        ),
        scheme=scheme, ink=ink,
    ))
    parts.append('<div class="spacer"></div>')

    # The foot is pinned and its height is fixed. Everything above it competes
    # for what is left; the verification instrument competes for nothing,
    # because a sheet that ran out of room and dropped its verification panel
    # is a sheet that cannot be checked.
    #
    # **Landscape and portrait are different feet, not one squeezed.** A wide
    # sheet sets the number cartouche, the signatures and the seal on one line.
    # A tall one has not got the width for that — 112mm of field cannot hold a
    # 46mm cartouche, two 38mm signature cells and a 22mm seal side by side —
    # so it stacks: the cartouche takes its own line, and the signatures pair
    # beneath it with the seal. This is the same rule that makes the citation
    # run in columns on one and stack on the other, applied to the foot.
    tall = field.h > field.w
    number = _number(filled, template, scheme=scheme, ink=ink,
                     width=46, height=14, paper=paper)
    signatures = (
        '<div class="sigrow">'
        + _signature_block(filled, template, scheme=scheme, ink=ink,
                           assets=assets)
        + "</div>"
    )
    seal = _seal(filled, template, scheme=scheme, ink=ink, radius=9.2,
                 device=device)
    execution = (
        f'<div class="numrow">{number}</div>'
        f'<div class="exec">{signatures}{seal}</div>'
        if tall else
        f'<div class="exec">{number}{signatures}{seal}</div>'
    )
    foot = (
        execution
        + '<div class="vrow">'
        + _verification(filled, template, scheme=scheme, ink=ink, width=measure,
                        height=27, paper=paper)
        + "</div>"
    )
    return "".join(parts) + foot


def _administrative(filled: Filled, *, architecture: Architecture, scheme,
                    ink: str, paper: str, field: geo.Rect, device: str,
                    assets: dict[str, str], scale: float = 1.0) -> str:
    """The portrait record: masthead, statement, body or table, pinned foot."""
    template = filled.template
    measure = field.w
    body_key = next(
        (slot.key for slot in template.slots if slot.kind == "table"), ""
    )
    parts = [
        _lockup(architecture, filled, base=3.2 * scale, mark=""),
        _banner(architecture, filled, scale=scale),
        _runs(architecture, filled, template.title, cls="ttl ttl--rec", base=5.2 * scale,
              inline=architecture.mode == "peer"),
        # Uneven on purpose. Two equal spacers put the block on the sheet's
        # geometric centre, which the eye reads as low — the same reason a
        # picture hung at true centre looks like it has slipped. 0.62 above and
        # 1 below lands it on the optical centre.
        '<div class="spacer spacer--high"></div>',
        _runs(architecture, filled, template.lede, cls="lede", base=2.9 * scale),
        _runs(architecture, filled, _peak(template), cls="name name--rec",
              base=6.6 * scale),
        _name_rule(measure * 0.52, scheme=scheme, ink=ink),
        '<div class="cite cite--rec">'
        + _runs(architecture, filled, template.statement, cls="stmt",
                base=2.85 * scale, lead_only=bool(body_key))
        + "</div>",
    ]
    if body_key:
        parts.append(_table(filled, template, body_key, ink=ink, scheme=scheme))
    parts.append('<div class="spacer"></div>')
    parts.append(_register_band(
        architecture, filled,
        (
            (Wording(en="Date of Issue", ar="تاريخ الإصدار"),
             Wording(en="{issued_on}", ar="{issued_on_hijri}")),
            (Wording(en="Place of Issue", ar="مكان الإصدار"),
             Wording(en="{place}", ar="{place_ar}")),
        ),
        scheme=scheme, ink=ink,
    ))
    foot = (
        '<div class="exec exec--rec">'
        + '<div class="sigrow">'
        + _signature_block(filled, template, scheme=scheme, ink=ink,
                           assets=assets)
        + "</div>"
        + _seal(filled, template, scheme=scheme, ink=ink, radius=11.0,
                device=device)
        + "</div>"
        + '<div class="vrow">'
        + _verification(filled, template, scheme=scheme, ink=ink, width=measure,
                        height=27, paper=paper)
        + "</div>"
    )
    return "".join(parts) + foot


def _banner(architecture: Architecture, filled: Filled, *,
            scale: float) -> str:
    """A permanent banner the document always carries.

    Not an edition and not a watermark. A Statement of Results without INTERIM
    on it reads as a final academic record, and a Provisional Certificate
    without its banner reads as the certificate it is standing in for — so the
    banner is part of the composition, set in the flow above the title where it
    is read *before* the document is, rather than laid over it where a reader
    can take it for decoration.
    """
    if not filled.template.banner.en and not filled.template.banner.ar:
        return ""
    return (
        '<div class="banner">'
        + _runs(architecture, filled, filled.template.banner, cls="bnr",
                base=2.6 * scale, inline=True)
        + "</div>"
    )


def _overprint(filled: Filled, *, width: float, height: float, scheme) -> str:
    """The reissuance overprint: CERTIFIED TRUE COPY, or DUPLICATE.

    Laid across the sheet at an angle, in a colour reserved for exactly this
    and nothing else, and drawn *over* the ground rather than under the content
    — a copy notice that content can obscure is a copy notice a forger can
    obscure. Deliberately impossible to mistake for ornament, and deliberately
    ugly next to the engraving: this sheet is not the original and the reader
    must not have to look for that.

    An original renders nothing at all. There is no faint "ORIGINAL" stamp,
    because a document that has to announce it is genuine has already conceded
    the question.
    """
    text = filled.overprint
    if not text.en and not text.ar:
        return ""
    # Oxblood, and reserved: this is the only place in the entire library where
    # it appears, which is what makes it mean something when it does.
    alert = "#6E1F2B"
    size = min(width, height) * 0.052
    lines = [line for line in (text.en, text.ar) if line]
    body = "".join(
        f'<text x="{width / 2:.1f}"'
        f' y="{height / 2 + (index - (len(lines) - 1) / 2) * size * 1.5:.1f}"'
        f' text-anchor="middle" font-size="{size * (0.62 if index else 1):.2f}"'
        f' font-family="Inter, sans-serif" font-weight="700"'
        f' letter-spacing="{size * 0.06:.2f}" fill="{alert}"'
        f' fill-opacity="0.22">{_escape(line)}</text>'
        for index, line in enumerate(lines)
    )
    return (
        f'<div class="overprint"><svg viewBox="0 0 {width:g} {height:g}"'
        f' preserveAspectRatio="none" aria-hidden="true">'
        f'<g transform="rotate(-16 {width / 2:.1f} {height / 2:.1f})">{body}</g>'
        "</svg></div>"
    )


def _end_of_record(architecture: Architecture, filled: Filled, *,
                   scale: float) -> str:
    """The rule that closes a tabular record against later addition."""
    if not filled.value("rows").strip():
        return ""
    return (
        '<div class="endrule">'
        + _runs(architecture, filled,
                Wording(en="End of record", ar="نهاية السجل"),
                cls="endr", base=1.9 * scale, inline=True)
        + "</div>"
    )


def _ledger(filled: Filled, *, architecture: Architecture, scheme, ink: str,
            paper: str, field: geo.Rect, device: str,
            assets: dict[str, str], scale: float = 1.0) -> str:
    """The portrait tabular record: transcript, supplement, statement.

    The rows are the document, so they get the room and the peak does not. A
    transcript whose holder's name is set at certificate size and whose results
    are set at footnote size has its emphasis exactly backwards: nobody is
    checking the spelling of the name, they are reading the marks.

    The grading key sits on the same sheet as the rows, above the foot. Filing
    it as an appendix is how a transcript reaches an admissions officer who has
    never seen this institution before as a page of letters to guess at.
    """
    template = filled.template
    measure = field.w
    parts = [
        _lockup(architecture, filled, base=3.0 * scale, mark=""),
        _banner(architecture, filled, scale=scale),
        _runs(architecture, filled, template.title, cls="ttl ttl--rec",
              base=4.8 * scale, inline=architecture.mode == "peer"),
        '<div class="hairspace"></div>',
        _runs(architecture, filled, template.lede, cls="lede",
              base=2.7 * scale),
        _runs(architecture, filled, _peak(template), cls="name name--led",
              base=5.4 * scale),
        _name_rule(measure * 0.46, scheme=scheme, ink=ink),
        _register_band(
            architecture, filled,
            (
                (Wording(en="Programme", ar="البرنامج"),
                 Wording(en="{programme}")),
                (Wording(en="Identity Number", ar="الرقم التعريفي"),
                 Wording(en="{student_id}")),
                (Wording(en="Session", ar="العام الدراسي"),
                 Wording(en="{session}")),
            ),
            scheme=scheme, ink=ink,
        ),
        '<div class="cite cite--rec">'
        + _runs(architecture, filled, template.statement, cls="stmt",
                base=2.6 * scale, lead_only=True)
        + "</div>",
        _table(filled, template, "rows", ink=ink, scheme=scheme),
        # The record is closed the moment it is sealed. Unused space below the
        # last row on a transcript is where a line gets added afterwards, and
        # ruling it out is older than photocopiers: a closing rule and a stated
        # end mean anything below them is visibly an addition. This is why the
        # blank area is left blank rather than filled with ruled lines — ruled
        # lines invite an entry, a closing rule forbids one.
        _end_of_record(architecture, filled, scale=scale),
        '<div class="spacer"></div>',
        '<div class="key">'
        + _runs(architecture, filled,
                Wording(en="Grading scale", ar="سلّم الدرجات"),
                cls="keyhead", base=1.9 * scale, lead_only=True)
        + _runs(architecture, filled, Wording(en="{grading_key}"),
                cls="keybody", base=2.3 * scale)
        + "</div>",
    ]
    foot = (
        '<div class="exec exec--rec">'
        + '<div class="sigrow">'
        + _signature_block(filled, template, scheme=scheme, ink=ink,
                           assets=assets)
        + "</div>"
        + _seal(filled, template, scheme=scheme, ink=ink, radius=10.0,
                device=device)
        + "</div>"
        + '<div class="vrow">'
        + _verification(filled, template, scheme=scheme, ink=ink, width=measure,
                        height=27, paper=paper)
        + "</div>"
    )
    return "".join(parts) + foot


_CSS = """
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #221F1B; }
.wrap { padding: 8mm; }
.tag { font-family: 'Inter', sans-serif; font-size: 3.0mm; letter-spacing: 0.14em;
  text-transform: uppercase; color: #A79E8E; margin: 0 0 3mm 1mm; font-weight: 600; }
.tag b { color: #F2E9D8; }
.sheet { position: relative; overflow: hidden; box-shadow: 0 4mm 12mm rgba(0,0,0,0.45); }
.plate { position: absolute; inset: 0; }
.plate svg { display: block; width: 100%; height: 100%; }
.field { position: absolute; display: flex; flex-direction: column;
  align-items: center; text-align: center; }
.spacer { flex: 1 1 auto; min-height: 0.4mm; }
.spacer--high { flex-grow: 0.62; }
.lockup { display: flex; align-items: center; justify-content: center;
  gap: 4mm; width: 100%; flex: none; }
.lockup--stack { flex-direction: column; gap: 1.4mm; }
.lk { flex: 1 1 0; font-weight: 600; letter-spacing: 0.02em; }
.lockup--stack .lk { flex: none; }
.ttl { font-weight: 600; letter-spacing: 0.03em; flex: none; }
.ttl--arabic { letter-spacing: 0; font-weight: 700; }
.ttl-row { display: flex; gap: 7mm; align-items: baseline; justify-content: center;
  flex: none; }
.sub { font-family: 'Inter', sans-serif; text-transform: uppercase;
  letter-spacing: 0.30em; font-weight: 600; flex: none; margin-top: 1.6mm; }
.lede { font-style: italic; flex: none; margin-top: 1.0mm; }
.lede--arabic { font-style: normal; }
.name { font-weight: 600; letter-spacing: -0.006em; flex: none;
  margin-top: 1.6mm; text-wrap: balance; }
.name.is-sub { margin-top: 0.6mm; }
.name--arabic { letter-spacing: 0; font-weight: 700; }
.namerule { display: block; flex: none; height: 3mm; margin-top: 1.6mm; }
.cite { display: flex; gap: 7mm; justify-content: center; align-items: flex-start;
  width: 100%; flex: none; margin-top: 2.0mm; }
.cite .stmt { flex: 1 1 0; text-align: justify; text-align-last: center; }
.cite--rec { display: block; }
.cite--rec .stmt { text-align: center; }
.award { flex: none; margin-top: 3.4mm; }
.awd { font-family: 'Inter', sans-serif; text-transform: uppercase;
  letter-spacing: 0.20em; font-weight: 600; }
.awd--arabic { text-transform: none; letter-spacing: 0; font-family: 'Amiri', serif; }
.awd-row { display: flex; gap: 6mm; align-items: baseline; justify-content: center; }
.band { display: flex; align-items: stretch; justify-content: space-between;
  width: 100%; flex: none; margin-top: 1.8mm; }
.bcell { flex: 1 1 0; padding: 0 3mm; }
.bdiv { flex: none; width: 0.2mm; align-self: stretch; }
.bhead { display: flex; gap: 2mm; justify-content: center; }
.bk { font-family: 'Inter', sans-serif; font-size: 1.7mm; letter-spacing: 0.16em;
  text-transform: uppercase; font-weight: 600; }
.bk--arabic { text-transform: none; letter-spacing: 0; font-family: 'Amiri', serif;
  font-size: 2.0mm; }
.bval { font-family: 'IBM Plex Mono', monospace; font-size: 2.3mm;
  margin-top: 0.6mm; }
.rows { width: 100%; border-collapse: collapse; flex: none; margin-top: 3mm;
  font-family: 'Source Serif 4', serif; font-size: 2.5mm; }
.rows th { font-family: 'Inter', sans-serif; font-size: 1.8mm; font-weight: 600;
  letter-spacing: 0.16em; text-transform: uppercase; padding: 1.4mm 2mm;
  border-bottom: 0.28mm solid var(--rule); }
.rows td { padding: 1.2mm 2mm; border-bottom: 0.10mm solid var(--rule); }
.exec { display: flex; align-items: flex-end; gap: 5mm; width: 100%; flex: none;
  margin-top: 2.0mm; }
.exec--rec { justify-content: center; }
.sigrow { flex: 1 1 auto; display: flex; align-items: flex-start; gap: 6mm; }
.sig { flex: 1 1 0; text-align: center; }
.sig .ink { display: block; width: 100%; height: 6.6mm; margin-bottom: -1.0mm;
  object-fit: contain; object-position: center bottom; }
.sig .nm { font-size: 3.1mm; height: 5.2mm; display: flex; align-items: flex-end;
  justify-content: center; white-space: nowrap; }
.sig .nm-ar { font-family: 'Amiri', serif; font-size: 3.0mm; margin-bottom: 0.4mm; }
.sig .srule { display: block; width: 100%; height: 1.6mm; }
.sig .of { font-family: 'Inter', sans-serif; text-transform: uppercase;
  font-weight: 600; font-size: 1.9mm; letter-spacing: 0.18em; margin-top: 1.1mm; }
.sig .of-ar { font-family: 'Amiri', serif; font-size: 2.2mm; margin-top: 0.4mm; }
.sealbox { flex: none; width: 22mm; }
.sealbox svg, .nbox svg, .vbox svg { display: block; width: 100%; height: auto; }
.nbox { flex: none; width: 46mm; }
.vrow { width: 100%; flex: none; margin-top: 2.0mm; }
.endrule { flex: none; width: 100%; margin-top: 1.6mm; padding-top: 1.2mm;
  border-top: 0.24mm solid; display: flex; justify-content: center; }
.endr { font-family: 'Inter', sans-serif; text-transform: uppercase;
  font-weight: 600; letter-spacing: 0.26em; }
.endr--arabic { text-transform: none; letter-spacing: 0;
  font-family: 'Amiri', serif; }
.endr-row { display: flex; gap: 4mm; align-items: baseline; }
.numrow { flex: none; margin-top: 2.0mm; display: flex; justify-content: center; }
.hairspace { flex: none; height: 2.4mm; }
/* The permanent banner sits in the flow above the title, where it is read
   before the document is, rather than over it where it reads as decoration. */
.banner { flex: none; margin: 1.6mm 0 0.4mm; padding: 1.0mm 4mm;
  border-top: 0.20mm solid; border-bottom: 0.20mm solid; }
.bnr { font-family: 'Inter', sans-serif; text-transform: uppercase;
  font-weight: 700; letter-spacing: 0.24em; }
.bnr--arabic { text-transform: none; letter-spacing: 0;
  font-family: 'Amiri', serif; }
.bnr-row { display: flex; gap: 5mm; align-items: baseline; justify-content: center; }
/* Over the ground, under nothing. A copy notice that content can obscure is a
   copy notice a forger can obscure. */
.overprint { position: absolute; inset: 0; pointer-events: none; z-index: 3; }
.overprint svg { display: block; width: 100%; height: 100%; }
.field { z-index: 2; }
.name--led { font-weight: 600; }
.key { flex: none; width: 100%; margin-top: 2.0mm; padding-top: 1.4mm;
  border-top: 0.16mm solid; text-align: center; }
.keyhead { font-family: 'Inter', sans-serif; text-transform: uppercase;
  font-weight: 600; letter-spacing: 0.20em; }
.keybody { margin-top: 0.8mm; }
"""


def _palette(ink: str, scheme, accent: str) -> str:
    return f"""
.lk {{ color: {accent}; }}
.ttl {{ color: {ink}; }}
.sub {{ color: {geo.tint(accent, 0.95)}; }}
.lede {{ color: {geo.tint(ink, 0.62)}; }}
.name {{ color: {ink}; }}
.name.is-sub {{ color: {geo.tint(ink, 0.86)}; }}
.stmt {{ color: {geo.tint(ink, 0.80)}; }}
.awd {{ color: {scheme.role("engraved").shadow}; }}
.bk {{ color: {geo.tint(ink, 0.52)}; }}
.bval, .sig .nm, .sig .nm-ar, .rows td {{ color: {ink}; }}
.sig .of, .rows th {{ color: {geo.tint(accent, 0.92)}; }}
.sig .of-ar {{ color: {geo.tint(ink, 0.58)}; }}
/* Oxblood is reserved for exactly two things and appears nowhere else in the
   library: a permanent banner that says this document is not what it might be
   taken for, and a reissuance overprint. Spending it anywhere else would make
   it stop meaning anything here. */
.banner {{ border-color: #6E1F2B; }}
.bnr {{ color: #6E1F2B; }}
.endrule {{ border-color: {geo.tint(ink, 0.40)}; }}
.endr {{ color: {geo.tint(ink, 0.56)}; }}
.key {{ border-color: {geo.tint(ink, 0.30)}; }}
.keyhead {{ color: {geo.tint(accent, 0.92)}; }}
.keybody {{ color: {geo.tint(ink, 0.78)}; }}
"""


def sheet_for_template(filled: Filled, *, sheet: str | None = None,
                       device: str = "",
                       signature_assets: dict[str, str] | None = None,
                       paper: str = "#F4ECDC",
                       ink: str = "#221A10") -> Rendered:
    """Render one filled template onto one sheet size.

    `sheet` defaults to the template's own, which is the size the document was
    designed at. Any other size in `design.sheets` is re-solved rather than
    scaled: the border is re-cut from its proportions, the optical sizes move
    with the field on a square-root curve, and the fixed instruments do not move
    at all. If what remains cannot carry the composition, this raises rather
    than printing a document whose verification panel has been shrunk out of
    usefulness.
    """
    template = filled.template
    chosen = sheet_for(sheet or template.sheet)
    fit = fits(family=template.family, sheet=chosen,
               border_weight=template.border_weight)
    measured = MEASURED_OVERFLOWS.get((template.key, chosen.key))
    if measured:
        raise SheetTooSmall(
            f"{template.name} cannot be issued on {chosen.name}: {measured}. "
            "The arithmetic accepts this size and the press proof does not; "
            "the proof wins. Sheets this document does fit: "
            + ", ".join(template.sheets()) + "."
        )
    if not fit.ok:
        raise SheetTooSmall(
            f"{template.name} cannot be issued on {chosen.name}. "
            + " ".join(fit.reasons)
            + " Sheets this document does fit: "
            + ", ".join(template.sheets()) + "."
        )

    width, height = chosen.width, chosen.height
    scale = fit.type_scale
    scheme = scheme_for(template.scheme)
    architecture = architecture_for(template.language)
    budget = budget_for(template.level)

    ground = heritage_ground(
        width=width, height=height, scheme=scheme,
        rail_text=" · ".join(p for p in (
            (filled.value("institution") or "").upper(),
            filled.value("serial"),
        ) if p),
        seed=filled.value("serial") or template.key,
        paper=paper, ink=scheme.role("engraved").core,
        border_weight=template.border_weight,
        # Fibres are a count over an area, so a fixed number thins out on A3
        # and clumps on B5. Scaled by area against the A4 landscape the count
        # was chosen on.
        fibre_count=round((150 if "fibres" in budget.permits else 90)
                          * (chosen.area_cm2 / 623.7)),
        show_watermark=template.family not in ("record", "ledger"),
    )
    field = ground.field

    shared = {
        "architecture": architecture, "scheme": scheme, "ink": ink,
        "paper": paper, "field": field, "device": device,
        "assets": signature_assets or {}, "scale": scale,
    }
    if template.family in ("stage", "college"):
        body = _ceremonial(filled, width=width,
                           award=template.family == "college", **shared)
    elif template.family == "award":
        body = _ceremonial(filled, width=width, award=True, **shared)
    elif template.family == "ledger":
        body = _ledger(filled, **shared)
    else:
        body = _administrative(filled, **shared)

    html = (
        f'<div class="sheet" style="width:{width:g}mm;height:{height:g}mm;'
        f'background:{paper}">'
        f'<div class="plate">{ground.svg}</div>'
        + _overprint(filled, width=width, height=height, scheme=scheme)
        + f'<div class="field" style="left:{field.x:.2f}mm;top:{field.y:.2f}mm;'
        f'width:{field.w:.2f}mm;height:{field.h:.2f}mm">{body}</div>'
        "</div>"
    )
    return Rendered(html=html, width=width, height=height, field=field,
                    template=template, sheet=chosen, fit=fit)


def render(filled: Filled, *, sheet: str | None = None, device: str = "",
           signature_assets: dict[str, str] | None = None,
           paper: str = "#F4ECDC", ink: str = "#221A10",
           embed_fonts: bool = True, caption: bool = True) -> str:
    """A complete HTML page for one sheet, ready to print or rasterise."""
    built = sheet_for_template(filled, sheet=sheet, device=device,
                               signature_assets=signature_assets,
                               paper=paper, ink=ink)
    template = filled.template
    scheme = scheme_for(template.scheme)
    tag = (
        f'<p class="tag"><b>{_escape(template.key)} · {_escape(template.name)}'
        f"</b> — {_escape(template.family)} family · {_escape(template.code)} · "
        f"class {_escape(template.security_class)} · Level {template.level} · "
        f"{_escape(built.sheet.name)} · type ×{built.type_scale:g}</p>"
    ) if caption else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{_escape(template.name)}</title><style>"
        f"@page {{ size: {built.width:g}mm {built.height:g}mm; margin: 0; }}"
        + font_face_css(embed=embed_fonts) + _CSS
        + _palette(ink, scheme, scheme.role("primary").core)
        + "</style></head><body><div class=\"wrap\">"
        + tag + built.html + "</div></body></html>"
    )
