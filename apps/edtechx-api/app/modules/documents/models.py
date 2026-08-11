"""Documents an institution issues about a person.

Two tables and a counter. The counter is not an afterthought: a document number
that repeats is a document that cannot be quoted, and a registrar asked "which
transcript is this?" needs an answer that is not "the one from about March".

**A document stores what it said.** `payload` is the composed content — every
grade, every total, every comment, the terminology in force, the periods
covered — frozen at issue. Reprinting reads that payload. There is deliberately
no path that recomposes an issued document from live data, because the whole
value of an academic document is that the copy produced in 2031 says what the
copy produced in 2026 said.

**What is *not* in the payload is the institution's own presentation** — its
crest, its address, its colours. Those are resolved fresh at render, because a
school that has moved should reprint an old transcript with the address that
reaches it today. An institution that wants the opposite sets
`freeze_branding` on the template, and then the identity is copied in too. Which
of the two an institution wants is a real question with two real answers, so it
is a setting rather than a decision we made for everyone (ADR-034).

**Nothing here is deleted.** A document that should not have been issued is
`void`, with a reason; a document overtaken by a correction is `superseded` by
its replacement, and both survive. An institution that can make an issued
transcript disappear cannot be trusted with the ones that remain.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class TemplateStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class DocumentStatus(str, enum.Enum):
    """What an issued document is now.

    `issued` is the ordinary state and the only one that verifies clean. The
    other two are both "no longer the current word", and they are different
    words on purpose: `void` means the institution withdrew it, `superseded`
    means a newer version exists and points at it.
    """

    issued = "issued"
    superseded = "superseded"
    void = "void"

    @property
    def is_current(self) -> bool:
        return self is DocumentStatus.issued


class DocumentTemplate(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One institution's design for one kind of document.

    Versioned like every other configuration document in the product: publishing
    a new version archives the old one and leaves it addressable, because a
    document issued last July was produced by *that* design and has to keep
    saying which.

    `purpose` names the permission resource this template is governed by, and is
    one of `report_card`, `transcript`, `document` — three rather than one,
    because a school that lets a form tutor print report cards has not thereby
    let them print transcripts. `purpose_label` is the institution's own word for
    the document and is never read to make a decision.
    """

    __tablename__ = "document_templates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "code", "version", name="uq_document_templates_code_version"
        ),
        Index("ix_document_templates_tenant_status", "tenant_id", "status"),
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # "Report Card", "Termly Report", "Academic Transcript", "Certificate of
    # Enrolment", "Statement of Completion" — whatever this institution calls it.
    purpose_label: Mapped[str] = mapped_column(String(120), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False, default="document")

    status: Mapped[TemplateStatus] = mapped_column(
        Enum(TemplateStatus, name="document_template_status"),
        nullable=False,
        default=TemplateStatus.draft,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("document_templates.id", ondelete="SET NULL")
    )

    # The ordered list of `{key, title, visible, omit_when_empty, options}`,
    # validated against the section catalogue when the template is saved.
    sections: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # `{format, prefix, scope}` — how this document's number is built.
    numbering: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # `{size, orientation, margin_mm}` — presentation, applied at render.
    page: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Whether the institution's identity is copied into the document at issue
    # rather than resolved fresh at render. False by default; see the module
    # docstring and ADR-034.
    freeze_branding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Whether this document may only quote results the institution has published.
    # True by default, and the one setting an institution should think hardest
    # about before turning off: a draft mark on a printed report card is a mark
    # nobody approved, in a parent's hands.
    published_results_only: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )


class DocumentSequence(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """The counter behind a document number.

    A row per numbering scope, incremented under a row lock. `max(number) + 1`
    would be smaller and would hand two registrars pressing Issue at the same
    moment the same transcript number.
    """

    __tablename__ = "document_sequences"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "scope_key", name="uq_document_sequences_tenant_scope"
        ),
    )

    scope_key: Mapped[str] = mapped_column(String(120), nullable=False)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Document(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One issued document. What it said, when, to whom, and by whose authority."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "number", name="uq_documents_tenant_number"),
        UniqueConstraint(
            "tenant_id", "verification_code", name="uq_documents_tenant_verification"
        ),
        CheckConstraint("version > 0", name="positive_version"),
        Index("ix_documents_tenant_subject", "tenant_id", "student_relationship_id"),
        Index("ix_documents_tenant_template", "tenant_id", "template_id"),
    )

    # The exact template *version* that produced it, not the template family.
    template_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("document_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Denormalised so the document can name its own design after the template
    # row has been archived, renamed, or replaced.
    template_code: Mapped[str] = mapped_column(String(60), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    purpose_label: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)

    student_relationship_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_relationships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="RESTRICT")
    )
    academic_period_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_periods.id", ondelete="RESTRICT")
    )

    number: Mapped[str] = mapped_column(String(80), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="RESTRICT")
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.issued,
    )
    void_reason: Mapped[str | None] = mapped_column(Text)

    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))

    # The composed content. Everything the document says.
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # The rows this document was composed from, and what they looked like then:
    # `{"published_results": {"<id>": <amendment count>}, ...}`. Lets the engine
    # answer "has anything behind this document changed since?" without keeping
    # a second copy of the results.
    sources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # SHA-256 of the canonical payload. A holder comparing two copies of a
    # transcript, or a verifier checking one against our record, compares this.
    # An HMAC over the document's canonical field set, keyed by a secret this
    # deployment holds. It was a plain SHA-256 until studying a real credential
    # architecture made the problem obvious: anybody can recompute a plain
    # digest, so a forger's invented document verifies perfectly. See
    # `documents/integrity.py`.
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    # Which signing key produced it. Recorded per document because a rotated
    # secret must not turn every certificate ever issued into a reported
    # forgery — verification uses the key that *signed* this one.
    hash_key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Unguessable, and the only thing a third party is given. Verification
    # confirms a document is genuine; it does not disclose the grades.
    verification_code: Mapped[str] = mapped_column(String(32), nullable=False)


__all__ = [
    "Document",
    "DocumentSequence",
    "DocumentStatus",
    "DocumentTemplate",
    "TemplateStatus",
]
