"""What an institution has declared about the shape of its own world.

Almost everything the interface needs is *derived* — from the rows an
institution has created, the permissions a person holds, and what the plan
includes. This table exists for the two cases derivation cannot cover:

  **A new institution has no rows yet.** A university on its first morning has
  created no programmes, so nothing can be inferred, and showing it a nursery's
  interface while it sets itself up would be exactly the failure this design
  exists to prevent. So an institution may *declare* the layers it intends to
  use, and the interface believes it immediately.

  **An institution wants a layer out of the way.** A school that created three
  cohorts years ago and no longer uses them can suppress the concept without
  deleting the rows — because deleting them would be deleting history.

Declaration is additive to what exists and suppression is subtractive from it,
and the asymmetry is deliberate: an institution can always show a layer it does
not yet use, and can never hide one it is actively using. Data that exists is
reachable. What changes is whether the concept leads the interface.

Note what this is **not**: an institution type. There is no `NURSERY |
SECONDARY | UNIVERSITY` column here and there will not be one — that is ADR-024's
forbidden enum arriving through the back door, and it would answer "what kind of
place is this?" when the only question worth asking is "what does this place
actually use?".
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class InterfaceProfile(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One institution's declaration about its own shape.

    At most one row per institution. Absent is a valid and common state: an
    institution that has simply used the product has told us everything we need
    by doing so.
    """

    __tablename__ = "interface_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_interface_profiles_tenant"),
    )

    # Layer keys (`academics.service.LAYER_TABLES`) this institution intends to
    # use, whether or not it has rows in them yet.
    declared_layers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Layer keys to keep out of the way even though rows exist. Cannot hide a
    # layer from somebody who is looking at its records; only from the
    # navigation.
    suppressed_layers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Capability keys the institution has switched off for itself, independent
    # of the plan. The same distinction `billing.FeatureSetting` draws, at the
    # level of a navigation entry rather than a purchase.
    hidden_capabilities: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Free text the institution uses for itself — "the College", "the Academy",
    # "the Institute". Rendered where the product would otherwise say "school".
    self_description: Mapped[str | None] = mapped_column(String(120))
    setup_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    note: Mapped[str | None] = mapped_column(Text)
    # Reserved for the layout overrides the Design Studio will write. Present
    # now so the shape of the record does not change under a school later.
    layout: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @property
    def is_set_up(self) -> bool:
        return self.setup_completed_at is not None


class UserPreference(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One person's own choices about their experience.

    Tenant-owned rather than global, deliberately. A teacher who works at two
    institutions has two working lives, and carrying the density they chose for
    a nursery register into a university's results screen would be a small,
    daily wrongness. The person is one human (ADR-027); their preferences are
    about a place.
    """

    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "membership_id", name="uq_user_preferences_member"),
    )

    membership_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    locale: Mapped[str | None] = mapped_column(String(16))
    timezone: Mapped[str | None] = mapped_column(String(64))
    # "system" | "light" | "dark" — a preference, not a brand decision.
    colour_scheme: Mapped[str] = mapped_column(String(16), nullable=False, default="system")
    # "comfortable" | "compact". A registrar reading four hundred rows and a
    # parent reading one want different things from the same table.
    density: Mapped[str] = mapped_column(String(16), nullable=False, default="comfortable")
    reduce_motion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Capability keys this person has pinned, in their order.
    pinned: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


__all__ = ["InterfaceProfile", "UserPreference"]
