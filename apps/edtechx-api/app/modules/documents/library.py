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

import re
from dataclasses import dataclass, field
from typing import Final

__all__ = [
    "FAMILIES",
    "TEMPLATES",
    "Filled",
    "SignatorySlot",
    "Slot",
    "Template",
    "TemplateError",
    "Verification",
    "Wording",
    "family",
    "fill",
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
# The shared slot vocabulary
# ---------------------------------------------------------------------------
#
# Written once and reused, so that "Institution" means the same field on all
# fifteen templates and a tenant configures it once rather than fifteen times.


def _institution() -> tuple[Slot, ...]:
    return (
        Slot("institution", "Institution", "المؤسسة", "text",
             default="Institution Name",
             note="The awarding body's registered name, as it appears on its "
                  "instrument of establishment."),
        Slot("institution_ar", "Institution (Arabic)", "المؤسسة بالعربية",
             "text_ar", required=False, default="اسم المؤسسة",
             note="Leave blank on a monolingual sheet — an empty Arabic run is "
                  "resolved away, not printed as a gap."),
        Slot("school", "School or faculty", "المدرسة", "text",
             required=False, default="School Name"),
        Slot("school_ar", "School or faculty (Arabic)", "المدرسة بالعربية",
             "text_ar", required=False, default=""),
        Slot("authority", "Supervising authority", "الجهة المشرفة", "text",
             required=False, default="",
             note="A ministry or board line, where the award is made under "
                  "one. Left empty it is not printed, and no authority is "
                  "implied that has not been named."),
        Slot("authority_ar", "Supervising authority (Arabic)",
             "الجهة المشرفة بالعربية", "text_ar", required=False, default=""),
    )


def _recipient() -> tuple[Slot, ...]:
    return (
        Slot("recipient", "Recipient name", "اسم الحامل", "name",
             default="Recipient Full Name",
             note="The visual peak of the sheet. Set to the name the holder "
                  "will be known by for life, not an abbreviated file name."),
        Slot("recipient_ar", "Recipient name (Arabic)", "الاسم بالعربية",
             "name_ar", required=False, default="",
             note="Never transliterated automatically. A person's name in "
                  "another script is theirs to give."),
        Slot("student_id", "Student identity number", "الرقم التعريفي للطالب",
             "identifier", default="000-0000-0000"),
    )


def _particulars() -> tuple[Slot, ...]:
    return (
        Slot("session", "Academic session", "العام الدراسي", "text",
             default="2025 – 2026"),
        Slot("issued_on", "Date of issue", "تاريخ الإصدار", "date",
             default="1 January 2026"),
        Slot("issued_on_hijri", "Date of issue (Hijri)", "التاريخ الهجري",
             "date_hijri", required=False, default=""),
        Slot("place", "Place of issue", "مكان الإصدار", "text",
             default="City, State, Country"),
        Slot("place_ar", "Place of issue (Arabic)", "مكان الإصدار بالعربية",
             "text_ar", required=False, default=""),
    )


def _credential() -> tuple[Slot, ...]:
    return (
        Slot("serial", "Serial number", "الرقم التسلسلي", "identifier",
             default="XXX/0000/000000",
             note="Minted by the issuing register, never typed. It is what "
                  "the border rail and the covert layers carry."),
        Slot("document_id", "Document number", "رقم الوثيقة", "identifier",
             default="DID-2026-XXX-0000000"),
        Slot("verification_code", "Verification code", "رمز التحقق",
             "identifier", default="0000-0000-0000"),
        Slot("archive_reference", "Archive reference", "المرجع الأرشيفي",
             "identifier", default="ARCH/XXX/2026/000000"),
        Slot("verify_url", "Verification address", "عنوان التحقق", "text",
             default="verify.example.edu",
             note="Printed on the face so the sheet is verifiable without the "
                  "QR — a code with nowhere to take it is not verification."),
        Slot("original_reference", "Original reference number",
             "رقم الوثيقة الأصلية", "identifier", required=False, default="",
             note="Filled only on a duplicate, and required there. It is what "
                  "makes a reissued sheet trace back to the one it replaces "
                  "instead of standing beside it as a second original."),
    )


def _signature_slots(*offices: tuple[str, str, str]) -> tuple[Slot, ...]:
    out: list[Slot] = []
    for key, label_en, label_ar in offices:
        out.append(Slot(f"{key}_name", f"{label_en} — name", label_ar, "text",
                        default=f"{label_en} Name"))
        out.append(Slot(f"{key}_name_ar", f"{label_en} — name (Arabic)",
                        f"{label_ar} (بالعربية)", "text_ar",
                        required=False, default=""))
        out.append(Slot(f"{key}_ink", f"{label_en} — signature", "التوقيع",
                        "signature", required=False, default="",
                        note="A prepared transparent signature. Uploads are "
                             "assessed and their paper removed before mounting."))
    return tuple(out)


_SEAL_SLOT = Slot(
    "seal", "Institutional seal", "الختم الرسمي", "seal", required=False,
    default="",
    note="An uploaded device is fitted inside the seal architecture — its own "
         "ring, legend and relief — rather than pasted on top of it.",
)

_STANDARD_SECURITY: Final[tuple[str, ...]] = (
    "constructed guilloché ground",
    "anti-copy line screens at 8° and 53°",
    "embossed khatam watermark",
    "serial-bearing fine-text rails",
    "engraved number cartouche",
    "Code 128 archive symbol",
    "QR verification bay",
    "void notice",
)


# ---------------------------------------------------------------------------
# Family 1 — the stage certificates
# ---------------------------------------------------------------------------
#
# Four sheets that differ only in the stage they name. They are declared from a
# table rather than written out four times, because four hand-written copies of
# one layout is how the third one ends up 1.4mm out and nobody notices for a
# year. What varies is transcribed; what does not vary is shared.

_STAGES: Final[tuple[tuple[str, str, str, str, str], ...]] = (
    # key, term, gloss, Arabic stage (definite), Arabic body form
    ("preparatory", "Tamhīdiyyah", "Preparatory Stage Completion",
     "المرحلة التمهيدية", "المرحلة التمهيدية"),
    ("primary", "Ibtidāʼiyyah", "Primary Stage Completion",
     "المرحلة الابتدائية", "المرحلة الابتدائية"),
    ("intermediate", "Iʻdādiyyah", "Intermediate Stage Completion",
     "المرحلة الإعدادية", "المرحلة الإعدادية"),
    ("secondary", "Thānawiyyah", "Secondary Stage Completion",
     "المرحلة الثانوية", "المرحلة الثانوية"),
)


def _stage_template(key: str, term: str, gloss: str, stage_ar: str,
                    body_ar: str) -> Template:
    return Template(
        key=f"stage-{key}",
        name=f"Certificate of {term}",
        name_ar=f"شهادة إتمام {stage_ar}",
        family="stage",
        sheet="a4-landscape",
        level=3,
        # Peer: neither script is the special case, and the citation runs in
        # two columns so a reader of either language meets the sentence at the
        # same height on the sheet.
        language="peer",
        scheme="imperial",
        title=Wording(en=f"Certificate of {term}",
                      ar=f"شهادة إتمام {stage_ar}"),
        subtitle=Wording(en=gloss),
        lede=Wording(en="This is to certify that",
                     ar="تشهد إدارة {institution_ar} بأن"),
        statement=Wording(
            en="has successfully completed the " + term + " stage in the "
               "{session} academic session, in accordance with the approved "
               "curriculum and academic standards of the School.",
            ar="قد أتمّ بنجاحٍ متطلبات " + body_ar + " في العام الدراسي "
               "{session}، وفقًا للمناهج المعتمدة والمعايير الأكاديمية "
               "المعمول بها في المدرسة.",
        ),
        registers=(
            Wording(en="Student ID", ar="الرقم التعريفي للطالب"),
            Wording(en="Date of Issue", ar="تاريخ الإصدار"),
            Wording(en="Place of Issue", ar="مكان الإصدار"),
        ),
        slots=(
            *_institution(), *_recipient(), *_particulars(), *_credential(),
            *_signature_slots(
                ("principal", "Principal and Head of School", "رئيس المدرسة"),
                ("chairman", "Chairman, Board of Governors", "رئيس مجلس الإدارة"),
            ),
            _SEAL_SLOT,
        ),
        signatories=(
            SignatorySlot("principal", "Principal and Head of School",
                          "رئيس المدرسة", "principal_name", "principal_ink",
                          seal=True),
            SignatorySlot("chairman", "Chairman, Board of Governors",
                          "رئيس مجلس الإدارة", "chairman_name", "chairman_ink"),
        ),
        verification=Verification(),
        security=_STANDARD_SECURITY,
        # The full border spends 36.3mm a side, which leaves a 132mm field on a
        # landscape sheet for a composition that measures 141. Narrowing the
        # whole border together keeps every proportion between its bands and is
        # what `border_weight` is for; deleting two of the bands would not be.
        border_weight=0.88,
        provenance=(
            "Imported from the benchmark press's stage certificate. The stage "
            "wording, the citation sentence and the three-register "
            "particulars band are transcribed; the ground is re-cut as "
            "constructed geometry; every name is a slot."
        ),
        notes=(
            "The citation is set to three lines at this measure on purpose. "
            "The wording it replaced ran to four lines for the longer stage "
            "names, and the fourth line crossed the particulars band's rule — "
            "on every sheet of a printed batch. Re-measure before lengthening "
            "this sentence or adding a fifth stage."
        ),
    )


# ---------------------------------------------------------------------------
# Family 2 — the college awards
# ---------------------------------------------------------------------------


def _college_template(*, key: str, name: str, name_ar: str, award_en: str,
                      award_ar: str, stage_en: str, stage_ar: str,
                      progresses_en: str, progresses_ar: str,
                      title_en: str, title_ar: str, scheme: str,
                      notes: str, level: int = 3, code: str = "CERT",
                      extra: tuple[Slot, ...] = ()) -> Template:
    return Template(
        key=f"college-{key}",
        name=name,
        name_ar=name_ar,
        family="college",
        sheet="a4-landscape",
        level=level,
        language="peer",
        scheme=scheme,
        title=Wording(en=title_en, ar=title_ar),
        subtitle=Wording(en=award_en, ar=award_ar),
        lede=Wording(en="This is to certify that",
                     ar="تشهد إدارة {institution_ar} بأن"),
        statement=Wording(
            en="has satisfactorily completed " + stage_en + " at {school} for "
               "the academic session {session}, has met in full the academic "
               "and conduct requirements of the institution, and is hereby "
               "graduated and admitted to " + progresses_en + ".",
            ar="قد أتمّ بنجاحٍ " + stage_ar + " في العام الدراسي {session}، "
               "وفقًا للمناهج المعتمدة والمعايير الأكاديمية المعمول بها في "
               "الكلية، " + progresses_ar + ".",
        ),
        award=Wording(en=award_en, ar=award_ar),
        registers=(
            Wording(en="Award Conferred", ar="الشهادة الممنوحة"),
            Wording(en="Student Identity Number", ar="الرقم التعريفي للطالب"),
            Wording(en="Date of Issue", ar="تاريخ الإصدار"),
            Wording(en="Place of Issue", ar="مكان الإصدار"),
        ),
        slots=(
            *_institution(), *_recipient(), *_particulars(), *_credential(),
            *extra,
            *_signature_slots(
                ("head", "Head of the awarding school", "مدير الكلية"),
                ("chairman", "Chairman, Board of Governors", "رئيس مجلس الإدارة"),
            ),
            _SEAL_SLOT,
        ),
        signatories=(
            SignatorySlot("head", "Head of the awarding school", "مدير الكلية",
                          "head_name", "head_ink", seal=True),
            SignatorySlot("chairman", "Chairman, Board of Governors",
                          "رئيس مجلس الإدارة", "chairman_name", "chairman_ink"),
        ),
        verification=Verification(),
        security=_STANDARD_SECURITY,
        code=code,
        security_class="A",
        border_weight=0.82,
        provenance=(
            "Imported from the benchmark press's college award. The citation "
            "runs in two columns rather than two stacked paragraphs — stacked "
            "it costs 26mm of a 138mm field and makes a reader of one language "
            "wait for the other."
        ),
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Family 3 — the records, and the register
# ---------------------------------------------------------------------------


def _record_template(*, key: str, name: str, name_ar: str, level: int,
                     eyebrow_en: str, eyebrow_ar: str, body_en: str,
                     body_ar: str, extra: tuple[Slot, ...] = (),
                     signatory: tuple[str, str, str],
                     notes: str = "", sheet: str = "a4-portrait",
                     registers: tuple[Wording, ...] = (),
                     about_a_person: bool = True,
                     peak: tuple[str, str] = ("recipient", "recipient_ar"),
                     code: str = "CERT", security_class: str = "B",
                     banner: Wording | None = None,
                     ) -> Template:
    office_key, office_en, office_ar = signatory
    return Template(
        key=f"record-{key}",
        name=name,
        name_ar=name_ar,
        family="record",
        sheet=sheet,
        level=level,
        # Latin-primary rather than peer: these are administrative records
        # whose Arabic is a full parallel text, not a ceremonial counterpart of
        # equal typographic weight. Calling it "peer" on a sheet that does not
        # compose that way would be a label, not an architecture.
        language="latin-primary",
        scheme="signature",
        title=Wording(en=name, ar=name_ar),
        lede=Wording(en=eyebrow_en, ar=eyebrow_ar),
        statement=Wording(en=body_en, ar=body_ar),
        registers=registers,
        slots=(
            *_institution(),
            # A register has no holder, so it carries no holder's fields. The
            # alternative — leaving `recipient` on it as an unused slot — is how
            # a registrar ends up filling in a name that is never printed and
            # concluding the system lost it.
            *(_recipient() if about_a_person else ()),
            *_particulars(), *_credential(),
            *extra,
            *_signature_slots((office_key, office_en, office_ar)),
            _SEAL_SLOT,
        ),
        peak_slot=peak[0], peak_slot_ar=peak[1],
        signatories=(
            SignatorySlot(office_key, office_en, office_ar,
                          f"{office_key}_name", f"{office_key}_ink", seal=True),
        ),
        verification=Verification(
            identifiers=("document_id", "verification_code", "serial"),
        ),
        security=(
            "constructed guilloché ground",
            "anti-copy line screens at 8° and 53°",
            "serial-bearing fine-text rails",
            "QR verification bay",
            "void notice",
        ),
        provenance=(
            "Imported from the benchmark press's document shell — the portrait "
            "register that carries its administrative records."
        ),
        notes=notes,
        border_weight=0.78,
        code=code,
        security_class=security_class,
        banner=banner or Wording(),
    )


# ---------------------------------------------------------------------------
# Family 4 — the ledgers: transcript, supplement, statement of results
# ---------------------------------------------------------------------------
#
# A ledger is not a certificate with a table on it. A certificate has one
# statement and one peak; a ledger has a holder block, a body of rows that may
# run to more than one page, and a key that tells a reader what the rows mean.
# The peak is smaller because the rows are the document, and the grading key is
# not an appendix — a transcript sent abroad without one is a page of letters
# an admissions officer has to guess at.


def _ledger_template(*, key: str, name: str, name_ar: str, code: str,
                     lede_en: str, lede_ar: str, body_en: str, body_ar: str,
                     columns: tuple[Wording, ...], rows_note: str,
                     rows_default: str = "",
                     extra: tuple[Slot, ...] = (), level: int = 3,
                     banner: Wording | None = None,
                     signatory: tuple[str, str, str] = (
                         "registrar", "Registrar", "المسجّل"),
                     notes: str = "") -> Template:
    office_key, office_en, office_ar = signatory
    return Template(
        key=f"ledger-{key}",
        name=name,
        name_ar=name_ar,
        family="ledger",
        sheet="a4-portrait",
        level=level,
        language="latin-primary",
        scheme="signature",
        title=Wording(en=name, ar=name_ar),
        lede=Wording(en=lede_en, ar=lede_ar),
        statement=Wording(en=body_en, ar=body_ar),
        banner=banner or Wording(),
        registers=columns,
        slots=(
            *_institution(), *_recipient(), *_particulars(), *_credential(),
            Slot("programme", "Programme of study", "البرنامج الدراسي", "text",
                 default="Programme Name"),
            Slot("rows", "Rows", "الصفوف", "table", default=rows_default,
                 note=rows_note),
            Slot("grading_key", "Grading scale", "سلّم الدرجات", "paragraph",
                 default="A 80–100 Distinction · B 70–79 Very Good · "
                         "C 60–69 Good · D 50–59 Pass · F below 50 Fail",
                 note="Printed on every sheet, not filed as an appendix. A "
                      "transcript read by somebody who has never seen this "
                      "institution's grading conventions is a page of letters "
                      "they have to guess at."),
            *extra,
            *_signature_slots((office_key, office_en, office_ar)),
            _SEAL_SLOT,
        ),
        signatories=(
            SignatorySlot(office_key, office_en, office_ar,
                          f"{office_key}_name", f"{office_key}_ink", seal=True),
        ),
        verification=Verification(),
        security=_STANDARD_SECURITY,
        code=code,
        security_class="A",
        provenance=(
            "Specified in the benchmark's own master document specification "
            "and never built there. Composed here as a ledger: a holder block, "
            "a body of rows, and a grading key on the same sheet."
        ),
        notes=notes,
        border_weight=0.74,
    )


# ---------------------------------------------------------------------------
# Family 5 — the awards
# ---------------------------------------------------------------------------
#
# One template family parameterised by awarding authority and citation, not six
# that drift apart. An award is the one document in the library whose *citation*
# is the substance: a certificate says what was completed, an award says what
# was done and who says so. So the citation is a slot, the authority line is a
# slot, and there is no academic session on it at all — an award for a piece of
# work is not an award for a year.


def _award_template(*, key: str, name: str, name_ar: str, code: str,
                    title_en: str, title_ar: str, authority_en: str,
                    authority_ar: str, extra: tuple[Slot, ...] = (),
                    signatory: tuple[str, str, str], level: int = 3,
                    scheme: str = "imperial", notes: str = "") -> Template:
    office_key, office_en, office_ar = signatory
    return Template(
        key=f"award-{key}",
        name=name,
        name_ar=name_ar,
        family="award",
        sheet="a4-landscape",
        level=level,
        language="peer",
        scheme=scheme,
        title=Wording(en=title_en, ar=title_ar),
        subtitle=Wording(en=authority_en, ar=authority_ar),
        lede=Wording(en="This award is made to",
                     ar="تُمنح هذه الجائزة إلى"),
        statement=Wording(en="{citation}", ar="{citation_ar}"),
        award=Wording(en="{award_title}", ar="{award_title_ar}"),
        registers=(
            Wording(en="Award", ar="الجائزة"),
            Wording(en="Conferred on", ar="تاريخ المنح"),
            Wording(en="Place", ar="المكان"),
        ),
        slots=(
            *_institution(), *_recipient(), *_particulars(), *_credential(),
            Slot("award_title", "Award", "الجائزة", "text",
                 default="Award Title"),
            Slot("award_title_ar", "Award (Arabic)", "الجائزة بالعربية",
                 "text_ar", required=False, default=""),
            Slot("citation", "Citation", "نص الجائزة", "paragraph",
                 default="",
                 note="What was actually done, in the institution's own words. "
                      "An award with a generic citation is a certificate of "
                      "attendance with a ribbon on it."),
            Slot("citation_ar", "Citation (Arabic)", "نص الجائزة بالعربية",
                 "paragraph_ar", required=False, default=""),
            *extra,
            *_signature_slots((office_key, office_en, office_ar)),
            _SEAL_SLOT,
        ),
        signatories=(
            SignatorySlot(office_key, office_en, office_ar,
                          f"{office_key}_name", f"{office_key}_ink", seal=True),
        ),
        verification=Verification(
            identifiers=("document_id", "verification_code", "serial"),
        ),
        security=(
            "constructed guilloché ground",
            "anti-copy line screens at 8° and 53°",
            "embossed khatam watermark",
            "serial-bearing fine-text rails",
            "engraved number cartouche",
            "QR verification bay",
            "void notice",
        ),
        code=code,
        security_class="B",
        provenance=(
            "Specified in the benchmark's own master document specification as "
            "one shared template parameterised by awarding authority and "
            "citation — one family, not six independently drifting ones."
        ),
        notes=notes,
        border_weight=0.86,
    )


def _build() -> dict[str, Template]:
    out: dict[str, Template] = {}

    for key, term, gloss, stage_ar, body_ar in _STAGES:
        template = _stage_template(key, term, gloss, stage_ar, body_ar)
        out[template.key] = template

    college = (
        _college_template(
            key="junior-secondary",
            name="Junior Secondary Graduation Certificate",
            name_ar="شهادة تخرج المرحلة الإعدادية",
            title_en="Certificate of Graduation", title_ar="شهادة تخرج",
            award_en="Junior Secondary School Graduation Certificate",
            award_ar="شهادة تخرج المرحلة الإعدادية",
            stage_en="the three-year Junior Secondary School programme",
            stage_ar="متطلبات المرحلة الإعدادية",
            progresses_en="the Senior Secondary School",
            progresses_ar="وأُجيزَ له الانتقال إلى المرحلة الثانوية",
            scheme="imperial",
            notes=(
                "The award line is deliberately NOT a national certificate's "
                "name. A national award is made by a state examination board "
                "on its own examination; a school certificate borrowing that "
                "name claims an authority the institution does not hold. This "
                "sheet certifies what a school can certify — completion of its "
                "own programme — and the wording must not be 'improved' into "
                "the national one."
            ),
        ),
        _college_template(
            key="senior-secondary",
            name="Senior Secondary Graduation Certificate",
            name_ar="شهادة تخرج المرحلة الثانوية",
            title_en="Certificate of Graduation", title_ar="شهادة تخرج",
            award_en="Senior Secondary School Graduation Certificate",
            award_ar="شهادة تخرج المرحلة الثانوية",
            stage_en="the three-year Senior Secondary School programme",
            stage_ar="متطلبات المرحلة الثانوية",
            progresses_en="tertiary study",
            progresses_ar="وأُجيزَ له التقدّم للدراسة الجامعية",
            scheme="imperial",
            notes=(
                "Same rule as the junior sheet, and it matters more here: the "
                "senior award is the one most often mistaken for a national "
                "school certificate. It is not one, and it does not say it is."
            ),
        ),
        _college_template(
            key="primary",
            name="Primary School Graduation Certificate",
            name_ar="شهادة تخرج المرحلة الابتدائية",
            title_en="Certificate of Graduation", title_ar="شهادة تخرج",
            award_en="Primary School Graduation Certificate",
            award_ar="شهادة تخرج المرحلة الابتدائية",
            stage_en="the Primary School programme",
            stage_ar="متطلبات المرحلة الابتدائية",
            progresses_en="the Junior Secondary School",
            progresses_ar="وأُجيزَ له الانتقال إلى المرحلة الإعدادية",
            scheme="crimson",
            level=2,
            notes=(
                "No year count in the citation. The benchmark's own prospectus "
                "states an age range and never a number of primary years, so "
                "'the six-year programme' would be invented — and an invented "
                "number on a permanent record is the error this whole library "
                "exists to avoid. Add the count when an institution confirms "
                "its own. The warm metal is deliberate: a parent holding this "
                "and a stage certificate must never have to work out which "
                "school issued which."
            ),
        ),
        _college_template(
            key="memorisation-complete",
            name="Certificate of Completion — Memorisation",
            name_ar="شهادة إتمام حفظ القرآن الكريم",
            title_en="Certificate of Completion",
            title_ar="شهادة إتمام حفظ القرآن الكريم",
            award_en="Completion of the Memorisation of the Glorious Qurʼan "
                     "(Thirty Juzʼ)",
            award_ar="إتمام حفظ القرآن الكريم كاملًا — ثلاثون جزءًا",
            stage_en="the memorisation of the entire Glorious Qurʼan, thirty juzʼ,",
            stage_ar="حفظ القرآن الكريم كاملًا — ثلاثين جزءًا —",
            progresses_en="the Ijazah examination of the College",
            progresses_ar="وأُجيزَ له التقدّم لامتحان الإجازة بالكلية",
            scheme="palace",
            level=4,
            notes=(
                "Admission to the Ijazah examination is what follows from "
                "completing the memorisation; the Ijazah itself is a separate "
                "award made after examination by named scholars. The citation "
                "says the first and must never be shortened into the second."
            ),
        ),
        _college_template(
            key="memorisation-ten",
            name="Certificate of Achievement — Ten Juzʼ",
            name_ar="شهادة حفظ عشرة أجزاء",
            title_en="Certificate of Achievement",
            title_ar="شهادة حفظ عشرة أجزاء",
            award_en="Memorisation of Ten Juzʼ of the Glorious Qurʼan",
            award_ar="حفظ عشرة أجزاء من القرآن الكريم",
            stage_en="the memorisation of ten juzʼ of the Glorious Qurʼan",
            stage_ar="حفظ عشرة أجزاء من القرآن الكريم",
            progresses_en="the continuing memorisation programme of the College",
            progresses_ar="ويواصل برنامج الحفظ بالكلية",
            scheme="palace",
            level=3,
            notes=(
                "A separate template rather than a variant of the completion "
                "sheet, and separate on purpose. The two are different "
                "achievements: a completion sheet printed over a child who has "
                "memorised ten juzʼ overstates it, and an achievement sheet "
                "printed over one who has completed the whole robs her of it. "
                "Neither may be reachable from the other by a default."
            ),
        ),
    )
    college = (*college, _college_template(
        key="islamiyyah",
        code="ISL",
        name="Islamiyyah Certificate",
        name_ar="شهادة الدراسات الإسلامية",
        title_en="Certificate of Islamic Studies",
        title_ar="شهادة الدراسات الإسلامية",
        award_en="Islamiyyah — {islamiyyah_level}",
        award_ar="المستوى: {islamiyyah_level_ar}",
        stage_en="the Islamiyyah programme at the level of {islamiyyah_level}",
        stage_ar="متطلبات برنامج الدراسات الإسلامية في مستوى "
                 "{islamiyyah_level_ar}",
        progresses_en="the next level of the programme",
        progresses_ar="ويواصل المستوى التالي من البرنامج",
        scheme="palace",
        level=3,
        extra=(
            Slot("islamiyyah_level", "Islamiyyah level", "المستوى", "text",
                 default="Level Name"),
            Slot("islamiyyah_level_ar", "Islamiyyah level (Arabic)",
                 "المستوى بالعربية", "text_ar", required=False,
                 default="المستوى"),
        ),
        notes=(
            "Specified in the benchmark's master document specification and "
            "never built there. The level is a slot rather than a set of "
            "templates: an institution that runs six Islamiyyah levels needs "
            "one certificate that names the level, not six certificates that "
            "drift apart at the third revision."
        ),
    ))
    for template in college:
        out[template.key] = template

    records = (
        _record_template(
            key="alumni-registration",
            code="ALUM",
            security_class="C",
            name="Alumni Registration Certificate",
            name_ar="شهادة تسجيل الخريجين",
            level=2,
            eyebrow_en="{institution} certifies that",
            eyebrow_ar="تشهد إدارة {institution_ar} بأن",
            body_en="has been formally entered into the Alumni Register "
                    "following graduation from {school} in the {session} "
                    "session, bearing Permanent Graduate ID {graduate_id}.",
            body_ar="قد تم تسجيله رسميًا في سجل الخريجين لدى {school} عقب "
                    "التخرج في دورة {session}، ويحمل الرقم الدائم للخريج "
                    "{graduate_id}.",
            extra=(
                Slot("graduate_id", "Permanent graduate ID",
                     "الرقم الدائم للخريج", "identifier",
                     default="ALM-000000"),
            ),
            signatory=("registrar", "Registrar", "المسجّل"),
        ),
        _record_template(
            key="testimonial",
            code="TEST",
            security_class="B",
            name="Official Testimonial",
            name_ar="شهادة توصية رسمية",
            level=2,
            eyebrow_en="{institution} provides this testimonial regarding",
            eyebrow_ar="تقدم إدارة {institution_ar} هذه الشهادة بخصوص",
            body_en="{testimonial_text}",
            body_ar="",
            extra=(
                Slot("testimonial_text", "Testimonial", "نص الشهادة",
                     "paragraph", default="",
                     note="Written by an officer who knows the holder. It is "
                          "never generated from a data table, and no "
                          "translation is fabricated for the other script — a "
                          "reference nobody wrote is not a reference."),
            ),
            signatory=("principal", "Principal", "رئيس المدرسة"),
            notes=(
                "The only template in the library whose body is free text. "
                "That is what a testimonial is: a named officer's own words "
                "about a person. The Arabic half is left empty rather than "
                "machine-translated, because a translated character reference "
                "is a reference the signatory did not give."
            ),
        ),
        _record_template(
            key="character",
            code="CHAR",
            security_class="B",
            name="Character Certificate",
            name_ar="شهادة حسن سيرة وسلوك",
            level=2,
            eyebrow_en="{institution} certifies that",
            eyebrow_ar="تشهد إدارة {institution_ar} بأن",
            body_en="has been a student of good conduct during their time at "
                    "the institution, {conduct_qualifier}.",
            body_ar="كان طالبًا يتمتع بحسن السيرة والسلوك خلال فترة دراسته "
                    "بالمؤسسة، {conduct_qualifier_ar}.",
            extra=(
                Slot("conduct_qualifier", "Conduct qualifier", "التحفظ",
                     "text",
                     default="without any disciplinary action recorded "
                             "against them",
                     note="Snapshotted at issue from the conduct record and "
                          "never recomputed later. A certificate that changes "
                          "its meaning after it was signed is not a record."),
                Slot("conduct_qualifier_ar", "Conduct qualifier (Arabic)",
                     "التحفظ بالعربية", "text_ar", required=False,
                     default="دون أي إجراء تأديبي مسجل بحقه"),
            ),
            signatory=("principal", "Principal", "رئيس المدرسة"),
            notes=(
                "A fact statement, not a narrative reference — which is why it "
                "is a different template from the Testimonial rather than a "
                "shorter setting of it. The qualifier is the whole document: "
                "it must state a recorded disciplinary action where one exists "
                "rather than omit it, because a certificate of good conduct "
                "that quietly drops the exception is a false one."
            ),
        ),
        _record_template(
            key="clearance",
            code="CLR",
            security_class="B",
            name="Graduation Clearance Certificate",
            name_ar="شهادة إتمام إجراءات التخرج",
            level=1,
            eyebrow_en="{institution} certifies that",
            eyebrow_ar="تشهد إدارة {institution_ar} بأن",
            body_en="has completed every clearance stage required for "
                    "graduation in the {session} session, as recorded below.",
            body_ar="قد أتمّ جميع مراحل إخلاء الطرف المطلوبة للتخرج في دورة "
                    "{session}، وفقًا لما هو مثبت أدناه.",
            extra=(
                Slot("clearance_rows", "Clearance stages", "مراحل إخلاء الطرف",
                     "table", default="",
                     note="One row per stage: the stage, who cleared it, and "
                          "when. A stage that is not applicable says so; an "
                          "empty row is not the same statement as 'N/A'."),
            ),
            registers=(
                Wording(en="Stage", ar="المرحلة"),
                Wording(en="Status", ar="الحالة"),
                Wording(en="Cleared by", ar="أخلى الطرف"),
                Wording(en="Date", ar="التاريخ"),
            ),
            signatory=("registrar", "Registrar", "المسجّل"),
        ),
        _record_template(
            key="graduation",
            code="CERT",
            security_class="A",
            name="Graduation Certificate",
            name_ar="شهادة التخرج",
            level=3,
            eyebrow_en="{institution} certifies that",
            eyebrow_ar="تشهد إدارة {institution_ar} بأن",
            body_en="has fulfilled the requirements of the programme of study "
                    "at {school} and was graduated in the {session} session.",
            body_ar="قد استوفى متطلبات البرنامج الدراسي لدى {school} وتخرّج في "
                    "دورة {session}.",
            signatory=("principal", "Principal", "رئيس المدرسة"),
        ),
        _record_template(
            key="graduation-register",
            code="REG",
            security_class="C",
            name="Graduation Register",
            name_ar="سجل التخرج",
            level=1,
            eyebrow_en="{institution} records the following graduands",
            eyebrow_ar="تسجّل إدارة {institution_ar} الخريجين التالية أسماؤهم",
            body_en="The persons named below were graduated from {school} in "
                    "the {session} session. This register is the institutional "
                    "record; a certificate is the holder's copy of one line "
                    "of it.",
            body_ar="تخرّج المذكورون أدناه من {school} في دورة {session}. هذا "
                    "السجل هو السجل المؤسسي؛ والشهادة نسخة الحامل من سطرٍ "
                    "واحد منه.",
            extra=(
                Slot("register_rows", "Register rows", "صفوف السجل", "table",
                     default="",
                     note="One row per graduand. The register is tabular and "
                          "is the one template in the library composed as a "
                          "column of data rather than around a single name."),
            ),
            registers=(
                Wording(en="No.", ar="م"),
                Wording(en="Name", ar="الاسم"),
                Wording(en="Identity Number", ar="الرقم التعريفي"),
                Wording(en="Programme", ar="البرنامج"),
                Wording(en="Class", ar="الصف"),
            ),
            signatory=("registrar", "Registrar", "المسجّل"),
            sheet="a4-portrait",
            about_a_person=False,
            peak=("session", ""),
            notes=(
                "The one template in the library that is not about a person. "
                "Its peak is the SESSION, it carries no recipient slots at "
                "all, and its body is a column of rows rather than a sentence "
                "about a name. The first proof of it set one graduand's name "
                "at full peak size over a list of four — a composition that "
                "reads as that student's certificate with three strangers "
                "appended."
            ),
        ),
    )
    records = (*records, _record_template(
        key="provisional",
        name="Provisional Certificate",
        name_ar="شهادة مؤقتة",
        level=3,
        code="PROV",
        security_class="A",
        banner=Wording(
            en="PROVISIONAL — FINAL CERTIFICATE IN PREPARATION",
            ar="مؤقتة — الشهادة النهائية قيد الإعداد",
        ),
        eyebrow_en="{institution} certifies that",
        eyebrow_ar="تشهد إدارة {institution_ar} بأن",
        body_en="had met every requirement for graduation from {school} as at "
                "{issued_on}. The final Certificate is in preparation and will "
                "be issued under its own reference number; this document "
                "stands in its place until then and does not replace it.",
        body_ar="قد استوفى جميع متطلبات التخرج من {school} حتى تاريخ "
                "{issued_on}. والشهادة النهائية قيد الإعداد وتصدر برقمها "
                "الخاص، وهذه الوثيقة تقوم مقامها إلى حين صدورها ولا تحل "
                "محلها.",
        signatory=("registrar", "Registrar", "المسجّل"),
        notes=(
            "The gap between clearing every stage and the parchment being "
            "printed, sealed and signed is real and at many institutions runs "
            "to weeks. This is what a university or an embassy actually "
            "accepts in that window. It is deliberately NOT the Statement of "
            "Results, which is an academic-progress document and says the "
            "wrong thing; and its banner is permanent rather than an edition, "
            "because a provisional certificate without it reads as the "
            "certificate it is standing in for."
        ),
    ))
    for template in records:
        out[template.key] = template

    ledgers = (
        _ledger_template(
            key="transcript",
            name="Official Academic Transcript",
            name_ar="كشف الدرجات الرسمي",
            code="TRAN",
            lede_en="{institution} certifies the academic record of",
            lede_ar="تشهد إدارة {institution_ar} بالسجل الأكاديمي لـ",
            body_en="The record below is a complete and unaltered statement of "
                    "the results obtained in the programme of {programme} at "
                    "{school}. It is issued under seal and is invalid without "
                    "it.",
            body_ar="السجل أدناه بيان كامل غير معدّل للنتائج المحرزة في "
                    "برنامج {programme} لدى {school}، صادر بختم المؤسسة ولا "
                    "يُعتد به بدونه.",
            columns=(
                Wording(en="Session", ar="العام"),
                Wording(en="Course", ar="المقرر"),
                Wording(en="Credit", ar="الساعات"),
                Wording(en="Mark", ar="الدرجة"),
                Wording(en="Grade", ar="التقدير"),
            ),
            rows_note=(
                "One row per course per term: session, course, credit, mark, "
                "grade. Snapshotted at issue and never recomputed — a "
                "transcript that changes after it was sealed is not a record."
            ),
            notes=(
                "The layout branches by institution in the benchmark's own "
                "specification: a subject-by-subject table for an academic "
                "programme, a stage-progression table for a memorisation one. "
                "Both are this template with different columns and different "
                "rows, which is what the column set being a slot is for."
            ),
        ),
        _ledger_template(
            key="supplement",
            name="Diploma Supplement",
            name_ar="ملحق الشهادة",
            code="SUPP",
            lede_en="This supplement describes the qualification held by",
            lede_ar="يصف هذا الملحق المؤهل الذي يحمله",
            body_en="This supplement explains the nature, level and content of "
                    "the qualification named below, and the grading scale "
                    "against which the accompanying Transcript should be read. "
                    "It carries no statement of value, equivalence or "
                    "recognition, and confers no rights beyond those of the "
                    "qualification it describes.",
            body_ar="يوضح هذا الملحق طبيعة المؤهل المذكور أدناه ومستواه "
                    "ومحتواه، وسلّم الدرجات الذي يُقرأ به كشف الدرجات المرفق. "
                    "ولا يتضمن أي حكم بالقيمة أو المعادلة أو الاعتراف، ولا "
                    "يمنح حقوقًا تتجاوز حقوق المؤهل الذي يصفه.",
            columns=(
                Wording(en="Section", ar="القسم"),
                Wording(en="Information", ar="البيان"),
            ),
            rows_note=(
                "The eight sections the international convention expects: the "
                "holder, the qualification, its level, the programme and "
                "results, its function, additional information, the "
                "certification of the supplement itself, and a factual "
                "description of the institution's own education system."
            ),
            # The eight sections are the document, so they are the default
            # rather than an empty table an institution has to know to fill.
            # A supplement shipped with a course list in it — which is what the
            # first proof rendered, because it inherited the transcript's rows —
            # is a supplement that explains nothing.
            rows_default=(
                "1. The holder|Named above, with the identity number recorded "
                "against this institution's own register.\n"
                "2. The qualification|As named on the accompanying "
                "certificate, awarded by this institution in its own right.\n"
                "3. Level|The stage of study the qualification completes "
                "within this institution's published progression.\n"
                "4. Programme and results|Set out in full on the accompanying "
                "Transcript, which this supplement does not repeat.\n"
                "5. Function|What the qualification entitles the holder to "
                "within this institution: admission to the next stage.\n"
                "6. Additional information|Any distinction, medium of "
                "instruction, or attendance mode the institution records.\n"
                "7. Certification|Signed and sealed below by the office named, "
                "and verifiable at the address printed on this sheet.\n"
                "8. The education system|The institution's own curriculum "
                "structure and the grading scale printed below."
            ),
            level=2,
            notes=(
                "The single highest-leverage document in the library for a "
                "graduate applying abroad. An excellent transcript is still "
                "unreadable to an admissions officer who has never seen this "
                "institution's grading conventions. The disclaimer in the body "
                "is not boilerplate: a supplement that implies equivalence to "
                "a foreign qualification is making a claim only a recognition "
                "authority can make."
            ),
        ),
        _ledger_template(
            key="statement",
            name="Statement of Results",
            name_ar="بيان النتائج",
            code="SOR",
            level=1,
            banner=Wording(en="INTERIM — NOT A COMPLETION DOCUMENT",
                           ar="مؤقت — ليس وثيقة إتمام"),
            lede_en="{institution} states the results obtained by",
            lede_ar="تبيّن إدارة {institution_ar} النتائج المحرزة لـ",
            body_en="The results below are those recorded to date in the "
                    "programme of {programme}. This is a statement of academic "
                    "progress. It is not a statement that the requirements for "
                    "an award have been met, and it must not be read as one.",
            body_ar="النتائج أدناه هي المسجّلة حتى تاريخه في برنامج "
                    "{programme}. وهذا بيان بالتقدّم الأكاديمي، وليس إفادةً "
                    "باستيفاء متطلبات المنح، ولا يجوز قراءته على هذا النحو.",
            columns=(
                Wording(en="Session", ar="العام"),
                Wording(en="Course", ar="المقرر"),
                Wording(en="Mark", ar="الدرجة"),
                Wording(en="Grade", ar="التقدير"),
            ),
            rows_note="One row per course recorded to date.",
            signatory=("examinations", "Examinations and Records",
                       "الامتحانات والسجلات"),
            notes=(
                "Signed by Examinations and Records rather than by the "
                "Registrar or the Principal, and that is the point: the office "
                "that signs a document is a statement about what the document "
                "claims. A principal's signature on an interim results "
                "statement implies a completion the statement does not attest."
            ),
        ),
    )
    for template in ledgers:
        out[template.key] = template

    awards = (
        _award_template(
            key="general",
            name="Award Certificate",
            name_ar="شهادة جائزة",
            code="AWD",
            title_en="Certificate of Award", title_ar="شهادة جائزة",
            authority_en="Awarded by the Institution",
            authority_ar="ممنوحة من المؤسسة",
            signatory=("principal", "Principal", "رئيس المدرسة"),
            notes=(
                "The general award: academic, leadership, sporting or other "
                "honours. The specific honour is the award title slot, so one "
                "template serves four registers rather than four templates "
                "serving one each."
            ),
        ),
        _award_template(
            key="distinction",
            name="Special Distinction Certificate",
            name_ar="شهادة تميّز خاص",
            code="DIST",
            title_en="Special Distinction", title_ar="تميّز خاص",
            authority_en="Conferred by Resolution of the Institution",
            authority_ar="ممنوحة بقرار من المؤسسة",
            signatory=("principal", "Principal", "رئيس المدرسة"),
            level=4,
            scheme="crimson",
            notes=(
                "Level IV and a second metal, because a distinction that looks "
                "like every other award is not a distinction. Exceptional by "
                "construction: if an institution issues these in volume it has "
                "stopped meaning what it says, and no layout can fix that."
            ),
        ),
        _award_template(
            key="board",
            name="Board Award",
            name_ar="جائزة مجلس الإدارة",
            code="BRD",
            title_en="Award of the Board of Governors",
            title_ar="جائزة مجلس الإدارة",
            authority_en="Conferred by Resolution of the Board of Governors",
            authority_ar="ممنوحة بقرار من مجلس الإدارة",
            extra=(
                Slot("resolution", "Authorising resolution", "رقم القرار",
                     "identifier", default="RES-2026-000",
                     note="The resolution that authorised this award. A board "
                          "award with no resolution behind it was not made by "
                          "the board."),
            ),
            signatory=("chairman", "Chairman, Board of Governors",
                       "رئيس مجلس الإدارة"),
            level=4,
            notes=(
                "The only award in the library that must name its authorising "
                "instrument on its face. A board acts by resolution; a "
                "certificate claiming a board award without one is claiming a "
                "decision that was never taken."
            ),
        ),
        _award_template(
            key="head-of-schools",
            name="Head of Schools Award",
            name_ar="جائزة رئيس المدارس",
            code="FCA",
            title_en="Award of the Head of Schools",
            title_ar="جائزة رئيس المدارس",
            authority_en="Conferred by the Head of Schools",
            authority_ar="ممنوحة من رئيس المدارس",
            extra=(
                Slot("honorific", "Honorific line", "سطر اللقب", "text",
                     required=False, default="",
                     note="The awarding office as the institution names it — "
                          "Founder, Head of Schools, Administrator. One "
                          "template with a selectable honorific, because "
                          "inventing parallel award registries for one "
                          "authority is duplication, not rigour."),
            ),
            signatory=("head_of_schools", "Head of Schools",
                       "رئيس المدارس"),
            level=4,
            scheme="palace",
            notes=(
                "Where one person holds the Founder and Head of Schools "
                "offices, this is one template with a selectable honorific "
                "line rather than two award systems that drift apart."
            ),
        ),
    )
    for template in awards:
        out[template.key] = template

    for template in out.values():
        template.check()
    return out


#: The imported library. Fifteen templates in three families.
TEMPLATES: Final[dict[str, Template]] = _build()

#: The three layout families, and what distinguishes them as *compositions*
#: rather than as categories. A family is not a tag: it decides where the peak
#: sits, how the citation runs, and what the foot carries.
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
