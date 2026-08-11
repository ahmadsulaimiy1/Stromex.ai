"""Resolving how an institution presents itself.

The shape mirrors `terminology`: a published row, merged over defaults, exposed
as a frozen value object that the rest of the product reads and never writes.

The one thing worth saying twice, because a document engine depends on it: a
branding profile is **current presentation metadata**. It is deliberately *not*
snapshotted into a document unless the institution asks for that, and the
distinction is the subject of ADR-034.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customization.models import BrandingProfile, ConfigStatus

__all__ = ["Branding", "from_snapshot", "publish", "resolve"]


@dataclass(frozen=True, slots=True)
class Branding:
    """One institution's visual identity, ready to render.

    Every field but `display_name` may be empty, and an institution that has
    filled in nothing must still produce a document that looks deliberate. The
    renderer therefore treats absence as a layout decision rather than as a gap
    to apologise for: no crest means no crest block, not an empty box.
    """

    display_name: str
    legal_name: str = ""
    motto: str = ""
    address: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    website: str = ""
    logo_url: str = ""
    crest_url: str = ""
    signature_image_url: str = ""
    watermark_url: str = ""
    primary_colour: str = "#1F3A5F"
    accent_colour: str = "#B08D57"
    ink_colour: str = "#12161C"
    heading_font: str = ""
    body_font: str = ""
    letterhead_note: str = ""
    footer_note: str = ""
    verification_url_template: str = ""

    @property
    def formal_name(self) -> str:
        """What goes on a certificate: the legal name where there is one."""
        return self.legal_name or self.display_name

    def verification_url(self, code: str) -> str:
        template = self.verification_url_template
        if not template or "{code}" not in template:
            return ""
        return template.replace("{code}", code)

    def as_dict(self) -> dict:
        return asdict(self)


def _fallback_name(db: Session) -> str:
    """The institution's own name, when it has not set a branding profile.

    Read through `tenancy.service` rather than by reaching into its table: the
    tenant row is another module's, and a placeholder like "Your institution"
    printed on a report card would be worse than one round trip.
    """
    from app.modules.tenancy import service as tenancy

    identity = tenancy.identity_of(db)
    return identity.name if identity else ""


def resolve(db: Session) -> Branding:
    """The published profile, or a usable default built from the tenant's name."""
    row = db.execute(
        select(BrandingProfile)
        .where(BrandingProfile.status == ConfigStatus.published)
        .order_by(BrandingProfile.version.desc())
    ).scalars().first()

    if row is None:
        return Branding(display_name=_fallback_name(db))

    def text(value: str | None, default: str = "") -> str:
        return value if value else default

    return Branding(
        display_name=row.display_name or _fallback_name(db),
        legal_name=text(row.legal_name),
        motto=text(row.motto),
        address=text(row.address),
        contact_email=text(row.contact_email),
        contact_phone=text(row.contact_phone),
        website=text(row.website),
        logo_url=text(row.logo_url),
        crest_url=text(row.crest_url),
        signature_image_url=text(row.signature_image_url),
        watermark_url=text(row.watermark_url),
        primary_colour=text(row.primary_colour, Branding.primary_colour),
        accent_colour=text(row.accent_colour, Branding.accent_colour),
        ink_colour=text(row.ink_colour, Branding.ink_colour),
        heading_font=text(row.heading_font),
        body_font=text(row.body_font),
        letterhead_note=text(row.letterhead_note),
        footer_note=text(row.footer_note),
        verification_url_template=text(row.verification_url_template),
    )


def from_snapshot(snapshot: dict | None) -> Branding | None:
    """Rebuild a branding a document froze at issue.

    Tolerant of missing and unknown keys on purpose: a document issued under an
    older release must keep rendering after this dataclass gains a field, and a
    field it has never heard of is not a reason to refuse to print somebody's
    transcript.
    """
    if not snapshot:
        return None
    fields = set(Branding.__dataclass_fields__)
    known = {k: v for k, v in snapshot.items() if k in fields and v is not None}
    if not known.get("display_name"):
        return None
    return Branding(**known)


def publish(
    db: Session,
    *,
    display_name: str,
    membership_id: uuid.UUID | None = None,
    **fields: object,
) -> BrandingProfile:
    """Publish a new version, superseding rather than mutating the previous one."""
    if not (display_name or "").strip():
        raise ValueError("A branding profile needs a name to present.")

    current = db.execute(
        select(BrandingProfile).order_by(BrandingProfile.version.desc())
    ).scalars().first()

    unknown = set(fields) - set(BrandingProfile.__mapper__.columns.keys())
    if unknown:
        raise ValueError(f"Not branding fields: {sorted(unknown)}")

    if current is not None and current.status is ConfigStatus.published:
        current.status = ConfigStatus.archived

    profile = BrandingProfile(
        display_name=display_name.strip(),
        status=ConfigStatus.published,
        version=(current.version + 1) if current else 1,
        parent_version_id=current.id if current else None,
        published_at=datetime.now(UTC),
        published_by_membership_id=membership_id,
        **fields,
    )
    db.add(profile)
    db.flush()
    return profile
