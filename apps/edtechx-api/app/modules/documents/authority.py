"""Who may sign an institution's documents, and under whose seal.

The thing this module refuses to be is the obvious one: a signature image and a
name on the branding profile. `BrandingProfile` still carries a
`signature_image_url`, and nothing in the issuance path reads it, because a
picture of somebody's handwriting establishes nothing. Authority is a chain, and
each link is a separate row for a separate reason:

    Office ─── the institution's post. "Registrar", "Dean of Science".
       │       Outlives every holder of it, and is what a template requires.
       │
    Appointment ─ a person holds that office, from a date, until a date.
       │       Carries the status and the document categories permitted.
       │
    Asset ──── the mark that appears on the page: an image, or a typeset name.
               Approved separately, replaceable without a new appointment, and
               digested so a document can record *which* one it used.

**Vacancy is a state, not an absence.** If a template requires a Registrar's
signature and no appointment is live on the issue date, issuance is refused —
`SignatoryVacancyError` — and the operator is told which office is missing. The
system does not print an empty rule, borrow the previous officer, silently
substitute a colleague, or draw a signature nobody made. An institution with a
vacant registrarship cannot issue transcripts, and that is the correct
behaviour: the document asserts that an officer of the institution certified it.

**A document that was validly signed stays validly signed.** The signature block
is frozen into the document at issue — office, holder, title, asset digest — and
verification reads *that*, never the current appointment. A registrar who leaves
in 2029 does not invalidate the four thousand transcripts they signed in 2028.
This is the same argument as ADR-034's frozen payload, applied to authority, and
it is why the appointment's `ended_on` closes the appointment rather than
deleting it.

**A seal is a controlled asset, not decoration.** Its states are the states an
institution actually has: drafted, approved, active, superseded, revoked. A
renderer may never reach for a placeholder, an older seal, or another
institution's — if the required seal is not available, issuance fails for the
same reason a vacancy does. And the seal that was in force is recorded on the
document, so reprinting a 2027 certificate reprints the 2027 seal.
"""

from __future__ import annotations

import enum
import hashlib
import uuid
from datetime import date

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
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey

__all__ = [
    "ASSET_USABLE",
    "SEAL_USABLE",
    "AppointmentStatus",
    "AssetKind",
    "AssetStatus",
    "Seal",
    "SealStatus",
    "SignatoryAppointment",
    "SignatoryOffice",
    "SignatureAsset",
    "digest_of",
]


def digest_of(content: str) -> str:
    """A plain SHA-256 of an asset's bytes, and deliberately not an HMAC.

    Unlike a document's signature (ADR-036), this is never compared against
    something an adversary supplies: it identifies *which* image was on the
    page, so a reprint that silently used a different one is detectable. There
    is no secret to protect and adding one would imply a guarantee it does not
    make.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class AppointmentStatus(str, enum.Enum):
    """Where an appointment stands.

    `suspended` is separate from `ended` because they are different facts and
    the institution needs both: an officer on leave has not vacated the post,
    and the post is nonetheless unable to sign today. Both refuse issuance;
    only one of them means the office is vacant.
    """

    pending = "pending"
    active = "active"
    suspended = "suspended"
    revoked = "revoked"
    ended = "ended"


class AssetStatus(str, enum.Enum):
    drafted = "drafted"
    approved = "approved"
    superseded = "superseded"
    revoked = "revoked"


class AssetKind(str, enum.Enum):
    """What actually appears above the rule.

    `typeset` is first-class rather than a fallback. A great many institutions
    sign with a name set in the document's own face beneath a printed rule, and
    that is a real signature block, not a missing image. What is *not* allowed
    is nothing at all — see `SignatoryVacancyError`.
    """

    image = "image"
    typeset = "typeset"


#: The one asset state that may appear on a document being issued today.
ASSET_USABLE: frozenset[AssetStatus] = frozenset({AssetStatus.approved})


class SealStatus(str, enum.Enum):
    drafted = "drafted"
    approved = "approved"
    superseded = "superseded"
    revoked = "revoked"


SEAL_USABLE: frozenset[SealStatus] = frozenset({SealStatus.approved})


class SignatoryOffice(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """A post that signs, named by the institution that has it.

    Not an enum. "Registrar" is a British and Nigerian word, "Recteur" is not,
    and an Islamic institute may sign with a Shaykh al-Ma'had. The platform
    never reads `name` to make a decision; `code` is what a template requires.
    """

    __tablename__ = "signatory_offices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_signatory_offices_tenant_code"),
        Index("ix_signatory_offices_tenant_sequence", "tenant_id", "sequence"),
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    # What is printed beneath the rule, where it differs from the office's own
    # name: "Registrar and Secretary to Senate".
    printed_title: Mapped[str | None] = mapped_column(String(200))
    # Where this signature sits relative to the others on a page.
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Whether the institution considers the office currently in use at all. An
    # office it has retired is not a vacancy; it is simply no longer required,
    # and a template that still names it is the thing to fix.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class SignatureAsset(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """The mark itself, as a controlled asset with its own approval.

    Separate from the appointment because the two change independently: an
    officer who re-signs a cleaner specimen has a new asset and the same
    appointment, and an officer whose signature image leaks needs that asset
    revoked without vacating the post.
    """

    __tablename__ = "signature_assets"
    __table_args__ = (
        Index("ix_signature_assets_tenant_person", "tenant_id", "person_id"),
        CheckConstraint(
            "(kind = 'image') = (content IS NOT NULL)",
            name="image_has_content",
        ),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("people.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[AssetKind] = mapped_column(
        Enum(AssetKind, name="signature_asset_kind"),
        nullable=False,
        default=AssetKind.typeset,
    )
    # A `data:` URI or a storage reference. Held here rather than in object
    # storage because a signature specimen is a few kilobytes and belongs with
    # the authority record it evidences, not in a bucket somebody can rotate
    # independently of the database.
    content: Mapped[str | None] = mapped_column(Text)
    # SHA-256 of `content`, or of the typeset name where there is no image. A
    # document records this so a reprint that used a different specimen is
    # detectable rather than invisible.
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="signature_asset_status"),
        nullable=False,
        default=AssetStatus.drafted,
    )
    approved_on: Mapped[date | None] = mapped_column(Date)
    approved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )
    revoked_on: Mapped[date | None] = mapped_column(Date)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def is_usable(self, *, on: date) -> bool:
        if self.status not in ASSET_USABLE:
            return False
        if self.approved_on is not None and on < self.approved_on:
            return False
        return not (self.revoked_on is not None and on >= self.revoked_on)


class SignatoryAppointment(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """This person holds this office, from this date, for these documents.

    A row with a beginning and an end, for the third time in this codebase and
    the same reason as the first two: the appointment that signed a document in
    2028 has to remain readable in 2038, and a mutable `office.holder_id` erases
    it the moment somebody is replaced.
    """

    __tablename__ = "signatory_appointments"
    __table_args__ = (
        CheckConstraint(
            "ended_on IS NULL OR ended_on >= appointed_on",
            name="ends_after_appointment",
        ),
        # One live appointment per office. Two people simultaneously holding
        # "the Registrar" is not a thing an institution means, and letting it
        # happen would make "which of them signs?" a question the code answers
        # by accident.
        Index(
            "uq_signatory_appointments_live",
            "tenant_id",
            "office_id",
            unique=True,
            postgresql_where=text("ended_on IS NULL AND status <> 'ended'"),
        ),
        Index(
            "ix_signatory_appointments_tenant_office",
            "tenant_id",
            "office_id",
            "appointed_on",
        ),
    )

    office_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("signatory_offices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("people.id", ondelete="RESTRICT"), nullable=False
    )
    # Optional: the staff record, where the institution keeps one. Nullable
    # because an external chair of examiners signs and is not on the payroll.
    staff_relationship_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("staff_relationships.id", ondelete="SET NULL")
    )
    signature_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signature_assets.id", ondelete="RESTRICT")
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="signatory_appointment_status"),
        nullable=False,
        default=AppointmentStatus.pending,
    )
    appointed_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date)
    ended_reason: Mapped[str | None] = mapped_column(String(200))
    # Which document categories this appointment may sign: a subset of
    # `report_card`, `transcript`, `document`. Empty means all three — the
    # ordinary case, and stated as emptiness rather than as three rows so that
    # "the Registrar signs everything" needs no configuration.
    purposes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # What is printed beneath the rule for this holder, where it differs from
    # the office's: "Prof. Idris Kamara, PhD".
    printed_name: Mapped[str | None] = mapped_column(String(200))
    printed_title: Mapped[str | None] = mapped_column(String(200))
    authorised_at: Mapped[date | None] = mapped_column(Date)
    authorised_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def covers(self, purpose: str) -> bool:
        return not self.purposes or purpose in self.purposes

    def is_live(self, *, on: date) -> bool:
        """In force on this date. Says nothing about the signature asset."""
        if self.status is not AppointmentStatus.active:
            return False
        if on < self.appointed_on:
            return False
        return not (self.ended_on is not None and on > self.ended_on)


class Seal(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """The institution's seal or crest, versioned and approved.

    `BrandingProfile.crest_url` is presentation — the mark at the top of a
    screen and of a letterhead, changeable by whoever manages the brand. This
    is authority, and it is deliberately not the same row: a school may
    redesign its website crest on a Tuesday, and the seal on a degree
    certificate is a governance decision with a date attached.
    """

    __tablename__ = "seals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_seals_tenant_code"),
        CheckConstraint(
            "in_force_until IS NULL OR in_force_until >= in_force_from",
            name="in_force_range",
        ),
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    # A `data:` URI or storage reference for the artwork.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[SealStatus] = mapped_column(
        Enum(SealStatus, name="seal_status"), nullable=False, default=SealStatus.drafted
    )
    in_force_from: Mapped[date] = mapped_column(Date, nullable=False)
    in_force_until: Mapped[date | None] = mapped_column(Date)
    # The seal that replaced this one, so a chain of crests is walkable in both
    # directions when somebody asks which mark was in force in 2027.
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("seals.id", ondelete="SET NULL")
    )
    approved_on: Mapped[date | None] = mapped_column(Date)
    approved_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )
    revoked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(Text)
    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def is_usable(self, *, on: date) -> bool:
        if self.status not in SEAL_USABLE:
            return False
        if on < self.in_force_from:
            return False
        return not (self.in_force_until is not None and on > self.in_force_until)
