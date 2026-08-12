"""The imported template library: benchmark documents, made editable.

Fifteen documents were brought across from the benchmark institution's press —
four stage certificates, five college awards, five records and one register —
and this file is what they became. Each one is a `Template`: its sheet, its
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

    @property
    def slot_keys(self) -> frozenset[str]:
        return frozenset(slot.key for slot in self.slots)

    @property
    def wording(self) -> tuple[Wording, ...]:
        return (self.title, self.subtitle, self.lede, self.statement,
                self.award, *self.registers)

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
class Filled:
    """A template with an institution's values in it, ready to render."""

    template: Template
    values: dict[str, str] = field(default_factory=dict)

    def text(self, phrase: Wording) -> Wording:
        return Wording(en=self._sub(phrase.en), ar=self._sub(phrase.ar))

    def _sub(self, source: str) -> str:
        if not source:
            return ""
        return _TOKEN.sub(lambda m: self.values.get(m.group(1), ""), source)

    def value(self, key: str) -> str:
        return self.values.get(key, "")


def fill(template: Template, values: dict[str, str] | None = None, *,
         strict: bool = True) -> Filled:
    """Put an institution's values into a template.

    `strict` refuses when a required slot is empty. That is the default because
    the alternative is a certificate that prints a blank where a name goes, and
    a blank is the one defect that survives every proof — the eye reads the
    space as the layout rather than as the absence.

    Unknown keys are refused rather than ignored: a caller passing
    `principal_name` to a template whose slot is `head_teacher_name` has just
    silently printed the default over the value they supplied.
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
    return Filled(template=template, values=resolved)


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
                      notes: str, level: int = 3) -> Template:
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
    for template in college:
        out[template.key] = template

    records = (
        _record_template(
            key="alumni-registration",
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
    for template in records:
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
