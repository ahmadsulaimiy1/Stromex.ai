"""The imported template library: benchmark documents, made editable.

Twenty-four documents in five composition families. Fifteen were brought across
from the benchmark institution's press, where they existed as rendering code.
The other nine existed only in that institution's own master specification —
named, numbered and given a security class, and never built: the transcript, the
diploma supplement, the statement of results, the provisional certificate, the
Islamiyyah certificate and the four awards. They are here because a document
ecosystem with a certificate and no transcript is not an ecosystem, and because
the specification that named them was right about what an institution needs.

This file is what all twenty-four became. Each one is a `Template`: its sheet, its
ceremonial level, its language architecture, its zone structure, its complete
bilingual wording, the slots an institution fills, the signatures and seals it
carries, and how it verifies. An institution adopts one, edits the slots, and
prints. That is the whole point of the import: nobody should have to
commission a certificate to have one.

**What "imported exactly" means here, precisely.**

*Exact:* the layout family, the sheet and orientation, the band architecture of
the ground, the zone order, the ceremonial register, the sentence structure and
— where the sentence is institutional rather than personal — the wording,
character for character, including the Arabic.

*Not exact, deliberately:* the names. Every personal name, every institution
name, every school, place, signatory and office is a **slot with a generic
default**. A real registrar's name and a real principal's signature belong to
the institution that owns them, and carrying them into a multi-tenant template
library would put a named human being's attestation on documents they never
saw. So the templates carry `{institution}`, `{principal_name}`,
`{chairman_name}` — real fields with placeholder values — and the tenant fills
them. The layout does not change by a millimetre.

*Not carried at all:* the raster artwork. The benchmark's own master background
is 92 DPI over an A4 sheet, which is a quarter of what a press needs. The
ground these templates print on is `design.heritage` — the same band
architecture, redrawn as constructed geometry, and therefore resolution-free.
That is stated here rather than buried, because "including the background" was
the ask and this is the honest answer to it: the background is the same
architecture at a resolution the raster never had.

**The wording rule.** Two kinds of sentence live in a template. An
*institutional* sentence ("has satisfactorily completed … and is hereby
graduated and admitted to …") is transcribed and is not the tenant's to
rewrite casually — its precision is the reason the document means anything. A
*naming* sentence is entirely slots. Where the benchmark deliberately refused a
national award's name — a school certificate may not call itself a Basic
Education Certificate, because that award is made by a state examination board
and not by a school — the refusal is transcribed with it, in `Template.notes`.
Importing the layout and dropping that reasoning would import the sheet and
lose the thing that made it lawful.

**Reference-number families.** Each template belongs to one — CERT, TRAN, SUPP,
SOR, PROV, TEST, CHAR, CLR, ALUM, AWD, DIST, BRD, FCA, ISL, REG — carried from
the benchmark's own numbering standard rather than invented. A transcript
numbered in the certificate series collides with a certificate the first time
two offices issue on the same day, and a collision between two permanent records
is not a bug that can be fixed after the fact.

**Security classes.** A — a legal academic record, fully publicly verifiable,
meant for security stock. B — institutional recognition, standard verification,
premium letterhead. C — registry, minimal public verification, and never
reissued as a certified copy because a register is regenerated from itself
rather than copied. The class is a property of the document, not a setting.

**Reissuance.** `EDITIONS` carries the discipline the specification is most
emphatic about: a reissued document is visibly and permanently a copy, carries
its own new reference number, names the original's where it is a duplicate, and
never alters or withdraws the original. Two unmarked originals of one credential
is the failure this prevents — a holder can lend one and keep one, and a
verifier cannot tell which is which.

**Sheet sizes.** A template names the sheet it was *designed* at and computes
the ones it can honestly be *issued* on (`Template.sheets()`). The computation
is in `design.sheets` and it can say no: a verification panel that has been
squeezed until it fits is a panel that cannot be scanned, so a sheet too small
to carry one is refused with the arithmetic rather than printed.

**Verification.** Every template declares a `Verification` spec, and every spec
resolves against `design.credential.Credential` — five identifiers, a
verification URL, a void notice, a Code 128 archive symbol and a QR bay.
Nothing here invents a second verification scheme; the templates are consumers
of the one EdirasX already has, which is why an imported certificate verifies
by the same route, with the same five states, as one EdirasX designed itself.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from typing import Final

__all__ = [
    "DEFAULT_LIBRARY",
    "EDITIONS",
    "FAMILIES",
    "MEASURED_OVERFLOWS",
    "TEMPLATES",
    "Edition",
    "Filled",
    "SignatorySlot",
    "Slot",
    "Template",
    "TemplateError",
    "Verification",
    "Wording",
    "family",
    "fill",
    "load",
    "template_for",
    "templates_in",
]


class TemplateError(ValueError):
    """A template could not be filled, and says which slot and why."""


_TOKEN = re.compile(r"\{([a-z0-9_]+)\}")


@dataclass(frozen=True, slots=True)
class Slot:
    """One editable field.

    `default` is generic on purpose and is never a real person's name. It is
    written so that an unfilled template still reads as a specimen rather than
    as a broken one — `{recipient}` printed literally on a proof is how a
    placeholder ends up on a real certificate.
    """

    key: str
    label_en: str
    label_ar: str
    kind: str = "text"
    required: bool = True
    default: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValueError(
                f"Slot {self.key!r} has kind {self.kind!r}, which the renderer "
                f"has no treatment for. Known kinds: {', '.join(sorted(_KINDS))}."
            )


#: What a slot *is*, which decides how it is set rather than how it is stored.
#: A name is the visual peak and is fitted per document; an identifier is
#: tabular-figure monospace and never hyphenates; a paragraph flows; a
#: signature is a prepared transparent asset and never a typed name in italics.
_KINDS: Final[frozenset[str]] = frozenset({
    "name", "name_ar", "text", "text_ar", "paragraph", "paragraph_ar",
    "identifier", "date", "date_hijri", "signature", "seal", "table",
})


@dataclass(frozen=True, slots=True)
class Wording:
    """A fixed sentence in both scripts. Braces name slots.

    Either side may be empty — a monolingual template is not a bilingual one
    with a blank half, and `language.Architecture` resolves which runs exist.
    """

    en: str = ""
    ar: str = ""

    @property
    def tokens(self) -> frozenset[str]:
        return frozenset(_TOKEN.findall(self.en)) | frozenset(_TOKEN.findall(self.ar))


@dataclass(frozen=True, slots=True)
class SignatorySlot:
    """One signature block: an office, a name, and prepared ink.

    The office is fixed by the template — a graduation certificate is signed by
    a principal, and which principal is the tenant's business. `ink` names the
    slot that carries the prepared signature asset, not an image: assets go
    through `design.signature_asset.strip_background`, so what lands on the
    sheet is ink on the guilloche rather than a white card pasted over it.
    """

    key: str
    role_en: str
    role_ar: str = ""
    name_slot: str = ""
    ink_slot: str = ""
    seal: bool = False


@dataclass(frozen=True, slots=True)
class Verification:
    """How this document proves it is itself.

    Every field maps onto `design.credential.Credential`. `void_notice` is
    bilingual and is transcribed: a sheet that does not say what invalidates it
    has left the reader to guess.
    """

    #: Which of the five identifiers this document prints on its face.
    identifiers: tuple[str, ...] = ("document_id", "verification_code",
                                    "serial", "archive_reference")
    #: A real Code 128 subset C symbol of the numeric archive reference.
    barcode: bool = True
    qr: bool = True
    #: The rail that carries the live serial through the border.
    serial_rail: bool = True
    void_en: str = "Void if altered or erased"
    void_ar: str = "لاغيةٌ عند أي كشطٍ أو تعديل"


@dataclass(frozen=True, slots=True)
class Template:
    """One imported, editable document."""

    key: str
    name: str
    name_ar: str
    family: str
    sheet: str
    level: int
    language: str
    scheme: str
    title: Wording
    lede: Wording
    statement: Wording
    slots: tuple[Slot, ...]
    signatories: tuple[SignatorySlot, ...]
    verification: Verification
    subtitle: Wording = Wording()
    award: Wording = Wording()
    registers: tuple[Wording, ...] = ()
    security: tuple[str, ...] = ()
    provenance: str = ""
    notes: str = ""
    border_weight: float = 1.0
    #: Which slots supply the sheet's visual peak. Almost always the recipient,
    #: because a certificate is about one person. A register is not: it is about
    #: a cohort, and setting one graduand's name at 7mm over a list of four is
    #: a composition that says the wrong thing about the document. So the peak
    #: is named by the template rather than assumed by the renderer.
    peak_slot: str = "recipient"
    peak_slot_ar: str = "recipient_ar"
    #: The reference-number family this document's numbers belong to — CERT,
    #: TRAN, SUPP, SOR, PROV, TEST, CHAR, CLR, ALUM, AWD, DIST, BRD, FCA, REG.
    #: Carried from the benchmark's own numbering standard, because a transcript
    #: numbered in the certificate series is a transcript that collides with a
    #: certificate the first time two offices issue on the same day.
    code: str = "CERT"
    #: A — legal academic record; B — institutional recognition; C — registry.
    #: The class decides public verification depth and the paper it is meant to
    #: be struck on, and it is a property of the document rather than a setting.
    security_class: str = "A"
    #: A banner this document *always* carries, because the document is not what
    #: an unbannered version of it would be. A Statement of Results without
    #: INTERIM on it reads as a final academic record; a Provisional Certificate
    #: without its banner reads as the certificate it is standing in for.
    banner: Wording = Wording()

    @property
    def slot_keys(self) -> frozenset[str]:
        return frozenset(slot.key for slot in self.slots)

    @property
    def wording(self) -> tuple[Wording, ...]:
        return (self.title, self.subtitle, self.lede, self.statement,
                self.award, self.banner, *self.registers)

    def sheets(self) -> tuple[str, ...]:
        """Every sheet size this template can honestly be issued on.

        Computed rather than listed, from the composition's own floors: see
        `design.sheets.fits`. A template does not get to declare that it fits
        A6 — the arithmetic decides, and the arithmetic includes a verification
        panel that may not be shrunk.
        """
        from app.modules.design.sheets import usable_sheets

        return tuple(
            sheet.key for sheet in
            usable_sheets(self.family, border_weight=self.border_weight)
            if (self.key, sheet.key) not in MEASURED_OVERFLOWS
        )

    def defaults(self) -> dict[str, str]:
        return {slot.key: slot.default for slot in self.slots}

    def check(self) -> None:
        """Every token in every sentence names a slot that exists.

        Run at import time, not at print time. A sentence naming a slot the
        template does not have prints a literal `{recipient}` on a sheet
        somebody keeps for fifty years, and it prints it in the one position
        nobody proofreads because it is the position that is always right.
        """
        known = self.slot_keys
        for phrase in self.wording:
            missing = phrase.tokens - known
            if missing:
                raise TemplateError(
                    f"Template {self.key!r} has wording naming "
                    f"{', '.join(sorted(missing))}, which is not a slot on it. "
                    "Add the slot or correct the sentence — a template may not "
                    "print an unresolved token."
                )
        seen: set[str] = set()
        for slot in self.slots:
            if slot.key in seen:
                raise TemplateError(
                    f"Template {self.key!r} declares slot {slot.key!r} twice."
                )
            seen.add(slot.key)
        for signatory in self.signatories:
            for ref in (signatory.name_slot, signatory.ink_slot):
                if ref and ref not in known:
                    raise TemplateError(
                        f"Template {self.key!r} signatory {signatory.key!r} "
                        f"refers to slot {ref!r}, which does not exist."
                    )


@dataclass(frozen=True, slots=True)
class Edition:
    """Whether a printed sheet is the original, or a reissue of one.

    The benchmark's reissuance discipline, imported whole because it is the part
    institutions get wrong: when a graduate loses a certificate, what they are
    sent must be **visibly and permanently** a copy. It carries its own new
    reference number, it names the original's, and it is logged as a reissuance
    against the original row. The original is never altered, never withdrawn,
    and stays independently verifiable at its own number for its own lifetime.

    Two originals of one credential is the failure this prevents. A holder with
    two unmarked certificates can lend one and keep one, and a verifier has no
    way to tell which is which — so a reissue that is not visibly a reissue is
    not a convenience, it is a second original.
    """

    key: str
    banner_en: str
    banner_ar: str
    #: Whether the sheet must name the original document's reference number.
    names_original: bool = False
    note: str = ""

    @property
    def is_original(self) -> bool:
        return self.key == "original"


EDITIONS: Final[dict[str, Edition]] = {
    "original": Edition("original", "", "", note="The issued document itself."),
    "certified_copy": Edition(
        "certified_copy", "CERTIFIED TRUE COPY", "نسخة طبق الأصل معتمدة",
        note="Issued where a receiving institution requires a certified copy "
             "rather than accepting a photocopy. Carries its own reference "
             "number and is logged against the original.",
    ),
    "duplicate": Edition(
        "duplicate", "DUPLICATE", "نسخة مكررة", names_original=True,
        note="Issued where the original has been lost or destroyed. Must name "
             "the original's reference number on its face: a duplicate that "
             "does not is indistinguishable from a second original.",
    ),
}


@dataclass(frozen=True, slots=True)
class Filled:
    """A template with an institution's values in it, ready to render."""

    template: Template
    values: dict[str, str] = field(default_factory=dict)
    edition: Edition = EDITIONS["original"]

    def text(self, phrase: Wording) -> Wording:
        return Wording(en=self._sub(phrase.en), ar=self._sub(phrase.ar))

    def _sub(self, source: str) -> str:
        if not source:
            return ""
        return _TOKEN.sub(lambda m: self.values.get(m.group(1), ""), source)

    def value(self, key: str) -> str:
        return self.values.get(key, "")

    @property
    def overprint(self) -> Wording:
        """The reissuance banner this sheet carries, if any.

        Composed here rather than in the renderer so that a duplicate cannot be
        printed without its original's number: the sentence is built from the
        value, and `fill` has already refused the edition if the value is
        missing.
        """
        edition = self.edition
        if edition.is_original:
            return Wording()
        if not edition.names_original:
            return Wording(en=edition.banner_en, ar=edition.banner_ar)
        reference = self.value("original_reference")
        return Wording(
            en=f"{edition.banner_en} — ORIGINAL REFERENCE No. {reference}",
            ar=f"{edition.banner_ar} — رقم الوثيقة الأصلية {reference}",
        )


def fill(template: Template, values: dict[str, str] | None = None, *,
         strict: bool = True, edition: str = "original") -> Filled:
    """Put an institution's values into a template.

    `strict` refuses when a required slot is empty. That is the default because
    the alternative is a certificate that prints a blank where a name goes, and
    a blank is the one defect that survives every proof — the eye reads the
    space as the layout rather than as the absence.

    Unknown keys are refused rather than ignored: a caller passing
    `principal_name` to a template whose slot is `head_teacher_name` has just
    silently printed the default over the value they supplied.

    `edition` refuses in two more ways, and both are about not minting a second
    original. A Class C registry document is not reissued as a certified copy —
    it is regenerated from the register, and stamping a copy notice on it
    implies a chain of custody it does not have. And a duplicate with no
    original reference number is refused outright.
    """
    supplied = dict(values or {})
    unknown = set(supplied) - template.slot_keys
    if unknown:
        raise TemplateError(
            f"Template {template.key!r} has no slot named "
            f"{', '.join(sorted(unknown))}. Its slots are: "
            f"{', '.join(sorted(template.slot_keys))}."
        )
    resolved = template.defaults()
    resolved.update({k: v for k, v in supplied.items() if v is not None})

    if strict:
        empty = [
            slot for slot in template.slots
            if slot.required and not str(resolved.get(slot.key, "")).strip()
        ]
        if empty:
            detail = "; ".join(
                f"{slot.key} ({slot.label_en})"
                + (f" — {slot.note}" if slot.note else "")
                for slot in empty
            )
            raise TemplateError(
                f"Template {template.key!r} cannot be printed: {detail}."
            )

    try:
        chosen = EDITIONS[edition]
    except KeyError:
        raise TemplateError(
            f"No edition named {edition!r}. Editions: "
            f"{', '.join(sorted(EDITIONS))}."
        ) from None
    if not chosen.is_original:
        if template.security_class == "C":
            raise TemplateError(
                f"{template.name} is a registry document and is regenerated "
                "from the register rather than reissued as a copy. Stamping a "
                "copy notice on it would imply a chain of custody it does not "
                "have."
            )
        if chosen.names_original and not resolved.get("original_reference", "").strip():
            raise TemplateError(
                "A duplicate must name the original's reference number on its "
                "face. Without it the sheet is indistinguishable from a second "
                "original, which is the failure the duplicate protocol exists "
                "to prevent. Set `original_reference`."
            )
    return Filled(template=template, values=resolved, edition=chosen)


# ---------------------------------------------------------------------------
# Loading the library
# ---------------------------------------------------------------------------
#
# The twenty-four templates are **data**, not product code, and they were moved
# here from a thousand lines of Python literals for a reason a test caught
# rather than a reviewer: the definitions named one education tradition's
# vocabulary — Diploma Supplement, Ibtidāʼiyyah, Junior Secondary — inside the
# product. A German institution issues a Diplom, a French one a licence, an
# Islamic seminary an ijāzah, and none of them should need EdirasX redeployed
# to have their own document set.
#
# So what lives in this file is the *architecture*: what a template is, what a
# slot is, what an edition is, what may be reissued and what may not, and every
# refusal. What lives in the data file is *content*: which twenty-four documents
# a particular institution issues and what its sentences say. A tenant ships its
# own file and gets its own library without a deploy — which is also, exactly,
# what "imported here for their quick edit" asked for.

#: The library that ships with EdirasX. One institution's document set, carried
#: across from its own press, with every name replaced by a slot.
DEFAULT_LIBRARY: Final[str] = "document-templates.toml"


def _wording(source: dict, name: str) -> Wording:
    """A bilingual sentence from `name.en` / `name.ar` keys, or nothing."""
    block = source.get(name)
    if isinstance(block, dict):
        return Wording(en=block.get("en", ""), ar=block.get("ar", ""))
    return Wording()


def load(path: pathlib.Path | None = None) -> dict[str, Template]:
    """Read a template library from a TOML file.

    Every template is checked as it is read, not when it is first printed. A
    sentence naming a slot that does not exist is a defect in the file, and the
    place to find it is at startup rather than on a sheet somebody keeps for
    fifty years.
    """
    import tomllib

    source = path or (
        pathlib.Path(__file__).resolve().parents[2] / "data" / DEFAULT_LIBRARY
    )
    raw = tomllib.loads(source.read_text(encoding="utf-8"))
    out: dict[str, Template] = {}
    for entry in raw.get("template", ()):
        template = Template(
            key=entry["key"],
            name=entry["name"],
            name_ar=entry.get("name_ar", ""),
            family=entry["family"],
            sheet=entry["sheet"],
            level=int(entry["level"]),
            language=entry["language"],
            scheme=entry["scheme"],
            title=_wording(entry, "title"),
            subtitle=_wording(entry, "subtitle"),
            lede=_wording(entry, "lede"),
            statement=_wording(entry, "statement"),
            award=_wording(entry, "award"),
            banner=_wording(entry, "banner"),
            registers=tuple(
                Wording(en=r.get("en", ""), ar=r.get("ar", ""))
                for r in entry.get("registers", ())
            ),
            slots=tuple(
                Slot(key=s["key"], label_en=s["label_en"],
                     label_ar=s.get("label_ar", ""), kind=s.get("kind", "text"),
                     required=bool(s.get("required", True)),
                     default=s.get("default", ""), note=s.get("note", ""))
                for s in entry.get("slots", ())
            ),
            signatories=tuple(
                SignatorySlot(key=g["key"], role_en=g["role_en"],
                              role_ar=g.get("role_ar", ""),
                              name_slot=g.get("name_slot", ""),
                              ink_slot=g.get("ink_slot", ""),
                              seal=bool(g.get("seal", False)))
                for g in entry.get("signatories", ())
            ),
            verification=Verification(
                identifiers=tuple(entry["verification"]["identifiers"]),
                barcode=bool(entry["verification"]["barcode"]),
                qr=bool(entry["verification"]["qr"]),
                serial_rail=bool(entry["verification"]["serial_rail"]),
                void_en=entry["verification"]["void_en"],
                void_ar=entry["verification"]["void_ar"],
            ),
            security=tuple(entry.get("security", ())),
            provenance=entry.get("provenance", ""),
            notes=entry.get("notes", ""),
            border_weight=float(entry.get("border_weight", 1.0)),
            peak_slot=entry.get("peak_slot", "recipient"),
            peak_slot_ar=entry.get("peak_slot_ar", ""),
            code=entry.get("code", "CERT"),
            security_class=entry.get("security_class", "A"),
        )
        template.check()
        if template.family not in FAMILIES:
            raise TemplateError(
                f"Template {template.key!r} declares family "
                f"{template.family!r}, which no composition renders. "
                f"Families: {', '.join(sorted(FAMILIES))}."
            )
        out[template.key] = template
    if not out:
        raise TemplateError(f"{source} declares no templates.")
    return out


#: The three original layout families plus the two the missing documents needed.
#: A family is not a tag: it decides where the peak sits, how the citation runs,
#: and what the foot carries, and each is written out as its own composition in
#: `library_sheet.py`. Adding one means writing a composition, which is why the
#: set lives in the product and the templates do not.
FAMILIES: Final[dict[str, str]] = {
    "stage": "Landscape ceremonial. One name at the optical centre, a "
             "two-column bilingual citation beneath it, a three-register "
             "particulars band across the waist, and the verification plate "
             "and two signatures sharing the foot.",
    "college": "Landscape ceremonial with an award line. Same architecture as "
               "the stage sheet, plus a conferred-award register between the "
               "citation and the foot — the award is a different statement "
               "from the citation and is set as one.",
    "record": "Portrait administrative. A masthead, an eyebrow, the name, a "
              "short body or a table, and a pinned administrative foot. The "
              "border is narrower because the field has to hold rows.",
    "ledger": "Portrait tabular. A holder block, a body of rows that is the "
              "document rather than an illustration of it, and a grading key "
              "on the same sheet — a transcript read without one is a page of "
              "letters somebody has to guess at. The peak is small because the "
              "rows are what is being certified.",
    "award": "Landscape ceremonial without an academic session. The citation "
             "is the substance: a certificate says what was completed, an "
             "award says what was done and who says so. One family "
             "parameterised by awarding authority, not six that drift apart.",
}

#: The library as shipped. Loaded at import so a malformed file is a startup
#: failure rather than a print-time one.
TEMPLATES: Final[dict[str, Template]] = load()


#: Sizes the arithmetic accepts and the press proof rejects, with the measured
#: overflow. Data, not a fudge factor.
#:
#: `design.sheets` predicts a composition's height as a straight line in the
#: type scale, and text does not oblige: a citation that fits on one line at
#: ×1.00 takes two at ×1.02, and the column jumps 7mm for a 2 % change. No
#: linear model catches that, and widening the model until it does would refuse
#: A4 landscape — the size these certificates were designed at.
#:
#: So the model predicts, `tools/design/library.py` renders and measures, and
#: what it catches is written down here rather than absorbed into a constant
#: that would then break something else. Each entry is a real measurement from a
#: real render, and each is re-checked on every audit run.
MEASURED_OVERFLOWS: Final[dict[tuple[str, str], str]] = {
    ("college-primary", "a4-portrait"):
        "0.3mm over — the portrait citation gains a line at ×1.27",
    ("college-memorisation-complete", "letter-landscape"):
        "3.4mm over — the thirty-juzʼ citation, the longest institutional "
        "sentence in the library, gains a line at ×1.015",
    ("record-clearance", "b5-landscape"):
        "10.3mm over — the clearance table's rows are not in the model",
    ("record-graduation-register", "b5-landscape"):
        "5.3mm over — the register's rows are not in the model",
}


def template_for(key: str) -> Template:
    try:
        return TEMPLATES[key]
    except KeyError:
        raise TemplateError(
            f"No imported template named {key!r}. The library holds: "
            f"{', '.join(sorted(TEMPLATES))}."
        ) from None


def templates_in(family_key: str) -> tuple[Template, ...]:
    if family_key not in FAMILIES:
        raise TemplateError(
            f"No family named {family_key!r}. Families: "
            f"{', '.join(sorted(FAMILIES))}."
        )
    return tuple(t for t in TEMPLATES.values() if t.family == family_key)


def family(key: str) -> str:
    return FAMILIES[template_for(key).family]
