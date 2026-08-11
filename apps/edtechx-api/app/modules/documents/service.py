"""Issuing, reissuing, verifying and reading back an institution's documents.

Four rules hold this module's shape, and each of them is a thing an academic
registrar will eventually be asked about under pressure.

**Issue composes; reprint does not.** `issue` builds the content once and stores
it. Every later reading of that document — a reprint, an export, a verification
— reads the stored payload. There is no code path that recomposes an issued
document, which is why a transcript reprinted in 2031 says what the 2026 copy
said even though the grading scale, the course names and the school's own
vocabulary have all moved on since.

**A document may not quote a result the institution has not published.** The
default, and the setting to think hardest about before changing: an unpublished
mark on a printed report card is a mark nobody approved, in a parent's hands.

**Nothing is deleted.** A document issued in error is voided with a reason. A
document overtaken by a correction is superseded by its replacement, and both
survive with a link between them.

**Verification discloses that a document is genuine, not what it says.** A code
handed to an employer answers "did you issue this, to this person, on this
date?" and nothing else. A verification endpoint that returned the grades would
be a public results database with an unguessable-ish URL.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.service import AuditAction, record
from app.modules.customization import branding as branding_module
from app.modules.documents import integrity
from app.modules.documents import sections as catalogue
from app.modules.documents.compose import ComposeError, Composition, compose
from app.modules.documents.models import (
    Document,
    DocumentSequence,
    DocumentStatus,
    DocumentTemplate,
    TemplateStatus,
)

__all__ = [
    "ComposeError",
    "DocumentError",
    "NotAuthorisedToIssue",
    "Verification",
    "amendable_sources",
    "content_of",
    "define_template",
    "documents_for",
    "issue",
    "outdated",
    "permission_for",
    "preview",
    "publish_template",
    "published_template",
    "reissue",
    "render",
    "templates",
    "verify",
    "void",
]


class DocumentError(ValueError):
    """A document that should not be produced, or a template that cannot be."""


class NotAuthorisedToIssue(DocumentError):
    """The right document, by the wrong person."""


# --- templates --------------------------------------------------------------

# Only these substitutions are allowed in a number format. A format string is
# administrator-supplied, and validating it here means a nonsense format fails
# when somebody saves the template rather than at the moment a registrar tries
# to print a leaving certificate for a student who is standing in front of them.
NUMBER_FIELDS = frozenset({"prefix", "year", "sequence", "code"})

# Two scopes, not three. An earlier version also had `template`, which gave each
# template its own counter — and two templates numbering `RC/…` then both issued
# `RC/2026/0001`, which the institution-wide uniqueness constraint refused at the
# worst possible moment. A document number belongs to a *series*, and a series is
# identified by its prefix rather than by which template happens to draw on it.
# An institution wanting two separate series gives them two prefixes.
NUMBER_SCOPES = frozenset({"year", "institution"})

DEFAULT_NUMBERING = {
    "format": "{prefix}/{year}/{sequence:04d}",
    "prefix": "DOC",
    "scope": "year",
}

# Base32 without the characters people misread aloud. A verification code is
# read down a telephone by somebody checking a certificate.
_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "OIL01")


def _validate_numbering(numbering: dict) -> dict:
    merged = {**DEFAULT_NUMBERING, **(numbering or {})}
    scope = str(merged.get("scope"))
    if scope not in NUMBER_SCOPES:
        raise DocumentError(
            f"{scope!r} is not a numbering scope. One of: "
            + ", ".join(sorted(NUMBER_SCOPES))
        )
    fmt = str(merged.get("format") or "")
    try:
        rendered = fmt.format(prefix="X", year="2026", sequence=1, code="X")
    except (KeyError, IndexError, ValueError) as exc:
        raise DocumentError(
            f"That document-number format cannot be filled in: {exc}. Available "
            "fields: " + ", ".join(sorted(NUMBER_FIELDS))
        ) from exc
    if not rendered.strip():
        raise DocumentError("A document-number format that produces nothing is not one.")
    if "{sequence" not in fmt:
        raise DocumentError(
            "A document-number format must contain {sequence}. Without it every "
            "document in the series would be given the same number."
        )
    if not str(merged.get("prefix") or "").strip():
        raise DocumentError(
            "A document-number series needs a prefix. It is what distinguishes "
            "one series from another, and two series sharing one would collide."
        )
    return merged


def define_template(
    db: Session,
    *,
    code: str,
    name: str,
    purpose_label: str,
    sections: list[dict],
    purpose: str = "document",
    numbering: dict | None = None,
    page: dict | None = None,
    freeze_branding: bool = False,
    published_results_only: bool = True,
    is_default: bool = False,
    custom: dict | None = None,
) -> DocumentTemplate:
    """Save a new draft version of one institution's design for one document.

    Everything is validated here — sections against the catalogue, options
    against what each section understands, the number format against what can
    actually be substituted — so that a template that saves is a template that
    prints.
    """
    if purpose not in catalogue.PURPOSES:
        raise DocumentError(
            f"{purpose!r} is not a document purpose. One of: "
            + ", ".join(sorted(catalogue.PURPOSES))
        )
    normalised = catalogue.validate_sections(sections)
    numbers = _validate_numbering(numbering or {})

    current = db.execute(
        select(DocumentTemplate)
        .where(DocumentTemplate.code == code)
        .order_by(DocumentTemplate.version.desc())
    ).scalars().first()

    draft = DocumentTemplate(
        code=code,
        name=name,
        purpose_label=purpose_label,
        purpose=purpose,
        status=TemplateStatus.draft,
        version=(current.version + 1) if current else 1,
        parent_version_id=current.id if current else None,
        sections=normalised,
        numbering=numbers,
        page={"size": "A4", "orientation": "portrait", "margin_mm": 18, **(page or {})},
        freeze_branding=freeze_branding,
        published_results_only=published_results_only,
        is_default=is_default,
        custom=custom or {},
    )
    db.add(draft)
    db.flush()
    return draft


def publish_template(
    db: Session, draft: DocumentTemplate, *, membership_id: uuid.UUID | None = None
) -> DocumentTemplate:
    """Make a draft the one that issues, archiving the version it replaces.

    The old version is archived rather than deleted because every document it
    produced still points at it, and "which design was this report card?" has to
    remain answerable.
    """
    if draft.status is TemplateStatus.published:
        return draft
    if draft.status is TemplateStatus.archived:
        raise DocumentError(
            "That template version is archived. Publish a newer draft instead of "
            "reviving an old one — a document has to be able to name the design "
            "that produced it."
        )
    _refuse_conflicting_series(db, draft)

    previous = db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.code == draft.code,
            DocumentTemplate.status == TemplateStatus.published,
        )
    ).scalars().all()
    for row in previous:
        row.status = TemplateStatus.archived
    draft.status = TemplateStatus.published
    draft.published_at = datetime.now(UTC)
    draft.published_by_membership_id = membership_id
    db.flush()
    record(
        db,
        action=AuditAction.publish,
        resource_type="document_template",
        resource_id=draft.id,
        after={"code": draft.code, "version": str(draft.version)},
        actor_membership_id=membership_id,
    )
    return draft


def _refuse_conflicting_series(db: Session, draft: DocumentTemplate) -> None:
    """Two templates may share a number series, but not disagree about it.

    Sharing is legitimate — a school with a long report card and a short one may
    well want both numbered `RC/2026/…` in a single sequence. What is not
    legitimate is two templates drawing on the same series with different
    formats or different reset points, because then one counter produces two
    shapes of number and the institution cannot say what `RC/2026/0007` is.

    Checked at publication rather than at issue, so it fails while somebody is
    configuring rather than while somebody is waiting for a certificate.
    """
    prefix = str(draft.numbering.get("prefix") or "")
    others = db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.status == TemplateStatus.published,
            DocumentTemplate.code != draft.code,
        )
    ).scalars().all()
    for other in others:
        if str(other.numbering.get("prefix") or "") != prefix:
            continue
        for field in ("format", "scope"):
            if other.numbering.get(field) != draft.numbering.get(field):
                raise DocumentError(
                    f"The {prefix!r} number series is already used by the "
                    f"{other.code!r} template with a different {field}. Two "
                    "templates may share a series, but not disagree about it — "
                    "give this one its own prefix, or match the series it joins."
                )


def published_template(db: Session, code: str) -> DocumentTemplate | None:
    """The published version of one template, which is the one that issues."""
    return db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.code == code,
            DocumentTemplate.status == TemplateStatus.published,
        )
    ).scalars().first()


def templates(db: Session, *, purpose: str | None = None) -> list[DocumentTemplate]:
    statement = select(DocumentTemplate).where(
        DocumentTemplate.status == TemplateStatus.published
    )
    if purpose is not None:
        statement = statement.where(DocumentTemplate.purpose == purpose)
    return list(
        db.execute(statement.order_by(DocumentTemplate.name)).scalars().all()
    )


def permission_for(row, action: str) -> str:
    """The permission governing this template or document.

    Three resources rather than one, so that a school which lets a form tutor
    print report cards has not thereby let them print transcripts.
    """
    return f"reporting.{row.purpose}.{action}"


# --- numbering --------------------------------------------------------------


def _scope_key(row: DocumentTemplate, *, when: date) -> str:
    """Which counter this document draws on.

    The prefix, because that is what a series *is*. Two templates that both
    number `RC/…` are deliberately sharing a series and must share a counter;
    `publish_template` refuses to let them disagree about the format or the
    scope, so a shared counter cannot produce two shapes of number.
    """
    prefix = str(row.numbering.get("prefix") or "DOC")
    if str(row.numbering.get("scope", "year")) == "year":
        return f"{prefix}:{when.year}"
    return prefix


def _next_number(db: Session, row: DocumentTemplate, *, when: date) -> tuple[str, int]:
    """Allocate the next number in this template's sequence, under a row lock.

    `max(number) + 1` would be smaller and would hand two registrars pressing
    Issue at the same moment the same transcript number. The lock is held for
    the length of the surrounding transaction, which is the length of one
    issue.
    """
    key = _scope_key(row, when=when)
    counter = db.execute(
        select(DocumentSequence)
        .where(DocumentSequence.scope_key == key)
        .with_for_update()
    ).scalars().first()
    if counter is None:
        counter = DocumentSequence(scope_key=key, next_value=1)
        db.add(counter)
        db.flush()
        counter = db.execute(
            select(DocumentSequence)
            .where(DocumentSequence.scope_key == key)
            .with_for_update()
        ).scalars().one()

    sequence = counter.next_value
    counter.next_value = sequence + 1
    db.flush()

    number = str(row.numbering.get("format") or DEFAULT_NUMBERING["format"]).format(
        prefix=row.numbering.get("prefix") or "DOC",
        year=when.year,
        sequence=sequence,
        code=row.code,
    )
    return (number, sequence)


def _verification_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(16))


def _signed_fields(document_number: str, code: str, payload: dict) -> dict:
    """The canonical field set a document is signed over.

    Deliberately the *identifying* facts plus a digest of the content, rather
    than the whole payload: a signature has to be recomputable years later from
    a database row, and a field set that includes every nested section is one
    refactor away from reporting every genuine document as tampered.
    """
    subject = payload.get("subject") or {}
    return {
        "number": document_number,
        "code": code,
        "title": payload.get("title"),
        "subject": subject.get("student_relationship_id"),
        "name": subject.get("full_name"),
        "content": hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       default=str).encode()
        ).hexdigest(),
    }


# --- composing without issuing ---------------------------------------------


def preview(db: Session, *, template: DocumentTemplate, student, **options) -> Composition:
    """What the document would say, without a number and without a record.

    Deliberately allocates nothing. Somebody designing a report card will look at
    it forty times, and forty gaps in an institution's transcript numbering is a
    question an auditor will ask about.
    """
    return compose(db, template=template, student=student, **options)


# --- issuing ----------------------------------------------------------------


def issue(
    db: Session,
    *,
    template: DocumentTemplate,
    student,
    membership_id: uuid.UUID | None = None,
    permissions: frozenset[str] = frozenset(),
    issued_on: date | None = None,
    supersedes: Document | None = None,
    **options,
) -> Document:
    """Produce a document, number it, and freeze what it says.

    The entitlement check and the permission check are separate calls to
    separate systems on purpose (ADR-030): the first asks whether this
    institution has document production at all, the second whether this person
    may produce this kind of document. Neither answer substitutes for the other.
    """
    from app.modules.authz import permissions as perms
    from app.modules.billing import service as billing

    required = permission_for(template, "create")
    if not perms.has(permissions, required):
        raise NotAuthorisedToIssue(f"Issuing this document needs {required}.")
    if template.status is not TemplateStatus.published:
        raise DocumentError(
            "That template is not published. A draft is for designing with, not "
            "for issuing from."
        )

    billing.require(db, "core.report_cards")

    when = issued_on or date.today()
    identity = branding_module.resolve(db)
    code = _verification_code()
    number, sequence = _next_number(db, template, when=when)

    composition = compose(
        db,
        template=template,
        student=student,
        issued_on=when,
        number=number,
        verification_code=code,
        verification_url=identity.verification_url(code),
        **options,
    )

    if template.published_results_only:
        _refuse_unpublished(composition)

    payload = composition.as_payload()
    signature = integrity.compute(_signed_fields(number, code, payload))
    now = datetime.now(UTC)
    periods = composition.context.get("periods") or []
    year_id = composition.context.get("academic_year_id")

    document = Document(
        template_id=template.id,
        template_code=template.code,
        template_version=template.version,
        purpose=template.purpose,
        purpose_label=template.purpose_label,
        title=composition.title,
        student_relationship_id=student.id,
        academic_year_id=uuid.UUID(year_id) if year_id else None,
        academic_period_id=(
            uuid.UUID(periods[0]["id"]) if len(periods) == 1 else None
        ),
        number=number,
        sequence=sequence,
        version=(supersedes.version + 1) if supersedes else 1,
        supersedes_id=supersedes.id if supersedes else None,
        status=DocumentStatus.issued,
        issued_on=when,
        issued_at=now,
        issued_by_membership_id=membership_id,
        payload=payload,
        sources=composition.sources,
        checksum=signature.digest,
        hash_key_version=signature.key_version,
        verification_code=code,
    )
    db.add(document)
    if supersedes is not None:
        supersedes.status = DocumentStatus.superseded
    db.flush()

    billing.record_usage(db, "documents.rendered", 1, membership_id=membership_id)
    record(
        db,
        action=AuditAction.create,
        resource_type="document",
        resource_id=document.id,
        after={
            "number": number,
            "template": template.code,
            "student_relationship_id": str(student.id),
        },
        actor_membership_id=membership_id,
    )
    return document


def _refuse_unpublished(composition: Composition) -> None:
    """Nothing composed may come from outside the published record.

    Currently structural rather than defensive — the composer reads
    `published_results` and has no access to working scores — and asserted here
    anyway, because the day somebody adds a section that reads a draft mark is
    the day this needs to already exist.
    """
    for block in composition.blocks:
        content = block.get("content") or {}
        for row in content.get("rows", []) or []:
            for entry in row.get("entries", []) or []:
                if entry.get("provisional"):
                    raise DocumentError(
                        "This template may only quote published results, and "
                        f"{block['key']!r} contains a provisional mark."
                    )


def reissue(
    db: Session,
    document: Document,
    *,
    membership_id: uuid.UUID | None = None,
    permissions: frozenset[str] = frozenset(),
    reason: str,
    **options,
) -> Document:
    """Issue a replacement, superseding the old one and keeping it.

    The replacement is composed fresh, which is the whole point: a document is
    reissued because something behind it changed, most often a published result
    that has since been amended. Both survive, and the new one points at the old.
    """
    if not (reason or "").strip():
        raise DocumentError(
            "Reissuing needs a reason. A second transcript with a different total "
            "and no explanation is the thing an appeal is about."
        )
    if document.status is DocumentStatus.void:
        raise DocumentError(
            "That document was voided. Issue a new one rather than replacing "
            "something the institution has withdrawn."
        )

    design = db.get(DocumentTemplate, document.template_id)
    if design is None:  # pragma: no cover - RESTRICT makes this unreachable
        raise DocumentError("The template that produced that document is gone.")
    if design.status is not TemplateStatus.published:
        current = published_template(db, design.code)
        if current is None:
            raise DocumentError(
                f"No published version of the {design.code!r} template. Publish one "
                "before reissuing documents that were produced from it."
            )
        design = current

    from app.modules.people import service as people

    student = people.student(db, document.student_relationship_id)
    if student is None:  # pragma: no cover - RESTRICT makes this unreachable
        raise DocumentError("The student that document is about no longer exists.")

    replacement = issue(
        db,
        template=design,
        student=student,
        membership_id=membership_id,
        permissions=permissions,
        supersedes=document,
        **options,
    )
    record(
        db,
        action=AuditAction.update,
        resource_type="document",
        resource_id=document.id,
        before={"status": DocumentStatus.issued.value, "number": document.number},
        after={"status": DocumentStatus.superseded.value, "number": replacement.number},
        reason=reason.strip(),
        actor_membership_id=membership_id,
    )
    return replacement


def void(
    db: Session,
    document: Document,
    *,
    reason: str,
    membership_id: uuid.UUID | None = None,
    permissions: frozenset[str] = frozenset(),
) -> Document:
    """Withdraw a document without erasing it.

    The row stays, the number stays allocated, and the payload stays readable.
    An institution that can make an issued transcript disappear cannot be
    trusted with the ones that remain.
    """
    from app.modules.authz import permissions as perms

    required = permission_for(document, "create")
    if not perms.has(permissions, required):
        raise NotAuthorisedToIssue(f"Voiding this document needs {required}.")
    if not (reason or "").strip():
        raise DocumentError("Voiding a document needs a reason.")

    before = document.status.value
    document.status = DocumentStatus.void
    document.void_reason = reason.strip()
    db.flush()
    record(
        db,
        action=AuditAction.update,
        resource_type="document",
        resource_id=document.id,
        before={"status": before},
        after={"status": DocumentStatus.void.value},
        reason=reason.strip(),
        actor_membership_id=membership_id,
    )
    return document


# --- reading back -----------------------------------------------------------


def documents_for(
    db: Session,
    student_relationship_id: uuid.UUID,
    *,
    include_superseded: bool = False,
) -> list[Document]:
    statement = select(Document).where(
        Document.student_relationship_id == student_relationship_id
    )
    if not include_superseded:
        statement = statement.where(Document.status == DocumentStatus.issued)
    return list(
        db.execute(statement.order_by(Document.issued_at)).scalars().all()
    )


def amendable_sources(document: Document) -> dict[uuid.UUID, int]:
    """The published results this document quoted, and how corrected they were."""
    raw = (document.sources or {}).get("published_results") or {}
    return {uuid.UUID(key): int(value) for key, value in raw.items()}


def outdated(db: Session, document: Document) -> list[str]:
    """Whether anything behind this document has changed since it was issued.

    Returns descriptions rather than a boolean, because "this transcript
    predates two corrections" is what a registrar needs to decide whether to
    reissue, and `True` is not.

    Note what this deliberately does *not* do: it does not alter the document.
    An issued document that has been overtaken is still exactly what the
    institution said on the day it said it, and the remedy is a reissue that
    supersedes it — never a silent update.
    """
    from app.modules.assessment import service as assessment

    quoted = amendable_sources(document)
    if not quoted:
        return []
    now = assessment.amendment_counts(db, list(quoted))
    notes: list[str] = []
    for result_id, was in sorted(quoted.items(), key=lambda kv: str(kv[0])):
        since = now.get(result_id, 0) - was
        if since > 0:
            notes.append(
                f"A result quoted here has been corrected {since} time"
                f"{'s' if since > 1 else ''} since this was issued."
            )
    return notes


# --- verification -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Verification:
    """What a third party holding a document is told.

    The document number, who it is about, when it was issued, and whether it is
    still the institution's current word. Not the grades: a verification
    endpoint that returned those would be a public results database with an
    unguessable-ish URL.
    """

    number: str
    title: str
    subject_name: str
    issued_on: date
    status: str
    checksum: str
    superseded_by: str | None = None
    #: Whether the record still matches the signature it was issued with.
    content_verified: bool = True
    #: Set when this environment holds no key for the document's era. A
    #: deployment gap is not tampering, and reporting them alike would publicly
    #: accuse a genuine document over an unset environment variable.
    integrity_unknown: bool = False
    # A revocation *note* is deliberately absent. The reference architecture
    # this was modelled on returns one, and on reflection it should not: the
    # note is written by a registrar and may say "withdrawn following an
    # academic misconduct finding". Anybody holding a verification code would
    # then learn something about a person that the institution never decided to
    # publish. The status alone answers the question a verifier actually has.

    @property
    def is_current(self) -> bool:
        return self.status == DocumentStatus.issued.value


def verify(db: Session, code: str) -> Verification | None:
    """Confirm a document is genuine. Returns `None` for anything else.

    One answer for "no such code", "wrong code" and "code from another
    institution", for the same reason a sign-in gives one answer to a wrong
    password and an unknown address (ADR-004).
    """
    if not code or not code.strip():
        return None
    document = db.execute(
        select(Document).where(Document.verification_code == code.strip().upper())
    ).scalars().first()
    if document is None:
        return None

    replacement = db.execute(
        select(Document.number).where(Document.supersedes_id == document.id)
    ).scalars().first()

    # Recomputed under the key that *signed* this document rather than the
    # current one. A secret rotation must not report every certificate ever
    # issued as tampered.
    check = integrity.verify(
        _signed_fields(document.number, document.verification_code, document.payload or {}),
        document.checksum,
        key_version=document.hash_key_version or 1,
    )

    return Verification(
        number=document.number,
        title=document.title,
        subject_name=(document.payload.get("subject") or {}).get("full_name", ""),
        issued_on=document.issued_on,
        status=document.status.value,
        checksum=document.checksum,
        superseded_by=replacement,
        # `key_unavailable` is deliberately *not* a failure here. The document
        # is reported as unverified-in-this-environment rather than as altered.
        content_verified=check.ok or check.is_deployment_gap,
        integrity_unknown=check.is_deployment_gap,
    )


def content_of(document: Document) -> dict:
    """The stored payload. What the document says, and the only source for it.

    A function rather than an attribute read, so that every caller reaching for
    a document's content goes through a name that says where it comes from.
    Recomposing here would defeat the entire design (ADR-034).
    """
    return document.payload


def render(
    db: Session, document: Document, *, fmt: str = "html", watermark: str | None = None
) -> str:
    """Reprint an issued document. Reads the payload; never recomposes it.

    This is where the one policy decision about branding is made, in one place:
    a template that froze the institution's identity at issue prints under that
    identity, and everything else prints under the identity the institution has
    today. Both are defensible and institutions want different ones, which is
    why it is a setting rather than a judgement we made for all of them
    (ADR-034).

    A voided document still prints — with VOID across it. Refusing would leave
    whoever is holding a copy unable to find out that it was withdrawn.
    """
    from app.modules.documents.render import render_html, render_text

    payload = document.payload or {}
    frozen = branding_module.from_snapshot(payload.get("branding"))
    identity = frozen or branding_module.resolve(db)

    if fmt == "text":
        return render_text(payload)

    design = db.get(DocumentTemplate, document.template_id)
    stamp = watermark
    if stamp is None:
        stamp = "VOID" if document.status is DocumentStatus.void else ""
    return render_html(
        payload,
        branding=identity,
        page=(design.page if design else {}),
        watermark=stamp,
    )
