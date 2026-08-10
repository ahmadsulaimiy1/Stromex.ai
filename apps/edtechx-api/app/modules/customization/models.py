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

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
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
