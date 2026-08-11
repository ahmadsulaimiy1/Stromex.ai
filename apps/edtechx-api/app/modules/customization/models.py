"""Configuration a school owns, stored as versioned documents.

Terminology is the first of these to be built, and it is the one schools notice
most: a school that calls a class a "form" and a student a "pupil" must never
see our defaults leak through. Everything here follows the same shape —
`status`, `version`, `payload` — so draft, preview, publish, and rollback are
one mechanism rather than one per configuration kind
(EDTECHX_CUSTOMIZATION_ENGINE.md §2).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class ConfigStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class TerminologySet(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """The school's words, per locale.

    `terms` maps a canonical key to the school's singular and plural. The
    interface never contains a domain noun as a literal; it asks for the key
    and receives whatever this school calls it.
    """

    __tablename__ = "terminology_sets"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "locale", "version", name="uq_terminology_tenant_locale_version"
        ),
    )

    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    status: Mapped[ConfigStatus] = mapped_column(
        Enum(ConfigStatus, name="config_status"), nullable=False, default=ConfigStatus.draft
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("terminology_sets.id", ondelete="SET NULL")
    )
    terms: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))


class BrandingProfile(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """How an institution presents itself: its name, its marks, its colours.

    Versioned exactly like terminology, and for the same reason — a rebrand is
    a decision somebody makes, previews, and occasionally regrets.

    Everything here is *current* presentation rather than historical fact. A
    school that moves premises reprints an old transcript on today's letterhead
    with today's address, because the address is how somebody reaches the
    institution now and not a claim about where it stood in 2019. Institutions
    that need the opposite — a certificate frozen under the identity that
    awarded it — set `freeze_at_issue` on the document template, and the engine
    copies this row into the document instead of resolving it at render
    (ADR-034).
    """

    __tablename__ = "branding_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "version", name="uq_branding_tenant_version"),
    )

    status: Mapped[ConfigStatus] = mapped_column(
        Enum(ConfigStatus, name="config_status"), nullable=False, default=ConfigStatus.draft
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("branding_profiles.id", ondelete="SET NULL")
    )

    # What the institution calls itself, in two registers. A degree certificate
    # carries the legal name; a dashboard header carries the short one.
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(200))
    motto: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text)
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(40))
    website: Mapped[str | None] = mapped_column(String(255))
    # Held as URLs rather than as bytes. A crest belongs in object storage; a
    # database row that occasionally contains two megabytes of PNG makes every
    # query that touches it slower for no benefit.
    logo_url: Mapped[str | None] = mapped_column(String(500))
    crest_url: Mapped[str | None] = mapped_column(String(500))
    signature_image_url: Mapped[str | None] = mapped_column(String(500))
    watermark_url: Mapped[str | None] = mapped_column(String(500))

    primary_colour: Mapped[str | None] = mapped_column(String(9))
    accent_colour: Mapped[str | None] = mapped_column(String(9))
    ink_colour: Mapped[str | None] = mapped_column(String(9))
    heading_font: Mapped[str | None] = mapped_column(String(120))
    body_font: Mapped[str | None] = mapped_column(String(120))

    letterhead_note: Mapped[str | None] = mapped_column(Text)
    footer_note: Mapped[str | None] = mapped_column(Text)
    # Where a holder of a document goes to check it is genuine. A template, so
    # the code can be substituted: "https://verify.example.edu/{code}".
    verification_url_template: Mapped[str | None] = mapped_column(String(500))

    custom: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
