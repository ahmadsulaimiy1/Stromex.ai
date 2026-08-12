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
from app.modules.design.signature import motif_for
from app.modules.design.typeface import font_face_css
from app.modules.documents.library import Filled, Template, Wording

__all__ = ["Sheet", "credential_for", "render", "sheet_for"]

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

_SHEETS = {
    "a4-landscape": (297.0, 210.0),
    "a4-portrait": (210.0, 297.0),
    "a3-landscape": (420.0, 297.0),
    "letter-landscape": (279.4, 215.9),
    "letter-portrait": (215.9, 279.4),
}


def _escape(value: str) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


@dataclass(frozen=True, slots=True)
class Sheet:
    """A rendered sheet and the facts a caller needs about it."""

    html: str
    width: float
    height: float
    field: geo.Rect
    template: Template


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
                assets: dict[str, str], award: bool) -> str:
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
        _lockup(architecture, filled, base=3.3, mark=mark),
        '<div class="spacer"></div>',
        _runs(architecture, filled, template.title, cls="ttl", base=5.8,
              inline=architecture.mode == "peer"),
        # The subtitle is the stage gloss on a stage sheet. A college sheet's
        # award is set once, in the conferred-award register below, and setting
        # it here as well cost 7.8mm of a 132mm field to say the same words
        # twice at two sizes.
        "" if award else _runs(architecture, filled, template.subtitle,
                              cls="sub", base=2.7),
        '<div class="spacer"></div>',
        _runs(architecture, filled, template.lede, cls="lede", base=2.9),
        _runs(architecture, filled, _peak(template), cls="name", base=7.2),
        _name_rule(measure * 0.62, scheme=scheme, ink=ink),
        '<div class="spacer"></div>',
        '<div class="cite">'
        + _runs(architecture, filled, template.statement, cls="stmt", base=2.75)
        + "</div>",
    ]
    if award:
        parts.append(
            '<div class="award">'
            + _runs(architecture, filled, template.award, cls="awd", base=2.9,
                    inline=True)
            + "</div>"
        )
    parts.append('<div class="spacer"></div>')
    parts.append(_register_band(
        architecture, filled,
        (
            (template.registers[-3] if len(template.registers) >= 3
             else Wording(en="Student ID", ar="الرقم التعريفي للطالب"),
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
    foot = (
        '<div class="exec">'
        + _number(filled, template, scheme=scheme, ink=ink, width=46, height=14,
                  paper=paper)
        + '<div class="sigrow">'
        + _signature_block(filled, template, scheme=scheme, ink=ink,
                           assets=assets)
        + "</div>"
        + _seal(filled, template, scheme=scheme, ink=ink, radius=9.2,
                device=device)
        + "</div>"
        + '<div class="vrow">'
        + _verification(filled, template, scheme=scheme, ink=ink, width=measure,
                        height=27, paper=paper)
        + "</div>"
    )
    return "".join(parts) + foot


def _administrative(filled: Filled, *, architecture: Architecture, scheme,
                    ink: str, paper: str, field: geo.Rect, device: str,
                    assets: dict[str, str]) -> str:
    """The portrait record: masthead, statement, body or table, pinned foot."""
    template = filled.template
    measure = field.w
    body_key = next(
        (slot.key for slot in template.slots if slot.kind == "table"), ""
    )
    parts = [
        _lockup(architecture, filled, base=3.2, mark=""),
        _runs(architecture, filled, template.title, cls="ttl ttl--rec", base=5.2,
              inline=architecture.mode == "peer"),
        # Uneven on purpose. Two equal spacers put the block on the sheet's
        # geometric centre, which the eye reads as low — the same reason a
        # picture hung at true centre looks like it has slipped. 0.62 above and
        # 1 below lands it on the optical centre.
        '<div class="spacer spacer--high"></div>',
        _runs(architecture, filled, template.lede, cls="lede", base=2.9),
        _runs(architecture, filled, _peak(template), cls="name name--rec",
              base=6.6),
        _name_rule(measure * 0.52, scheme=scheme, ink=ink),
        '<div class="cite cite--rec">'
        + _runs(architecture, filled, template.statement, cls="stmt",
                base=2.85, lead_only=bool(body_key))
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
"""


def sheet_for(filled: Filled, *, device: str = "",
              signature_assets: dict[str, str] | None = None,
              paper: str = "#F4ECDC", ink: str = "#221A10") -> Sheet:
    """Render one filled template to a complete, self-contained sheet."""
    template = filled.template
    width, height = _SHEETS[template.sheet]
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
        fibre_count=150 if "fibres" in budget.permits else 90,
        show_watermark=template.family != "record",
    )
    field = ground.field

    body = (
        _ceremonial(filled, architecture=architecture, scheme=scheme, ink=ink,
                    paper=paper, width=width, field=field, device=device,
                    assets=signature_assets or {},
                    award=template.family == "college")
        if template.family in ("stage", "college")
        else _administrative(filled, architecture=architecture, scheme=scheme,
                             ink=ink, paper=paper, field=field, device=device,
                             assets=signature_assets or {})
    )

    html = (
        f'<div class="sheet" style="width:{width:g}mm;height:{height:g}mm;'
        f'background:{paper}">'
        f'<div class="plate">{ground.svg}</div>'
        f'<div class="field" style="left:{field.x:.2f}mm;top:{field.y:.2f}mm;'
        f'width:{field.w:.2f}mm;height:{field.h:.2f}mm">{body}</div>'
        "</div>"
    )
    return Sheet(html=html, width=width, height=height, field=field,
                 template=template)


def render(filled: Filled, *, device: str = "",
           signature_assets: dict[str, str] | None = None,
           paper: str = "#F4ECDC", ink: str = "#221A10",
           embed_fonts: bool = True, caption: bool = True) -> str:
    """A complete HTML page for one sheet, ready to print or rasterise."""
    built = sheet_for(filled, device=device, signature_assets=signature_assets,
                      paper=paper, ink=ink)
    template = filled.template
    scheme = scheme_for(template.scheme)
    tag = (
        f'<p class="tag"><b>{_escape(template.key)} · {_escape(template.name)}'
        f"</b> — {_escape(template.family)} family · Level {template.level} · "
        f"{_escape(template.sheet)}</p>"
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
