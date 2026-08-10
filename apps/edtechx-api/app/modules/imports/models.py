"""The record of an import, kept because an import is a change to the record.

A school's data arrives in bulk exactly once — at the start — and that is the
moment its records are most fragile and least reviewed. Six months later,
somebody will ask why a child's date of birth is wrong, and the answer needs to
be "row 412 of `year7-september.xlsx`, uploaded by the registrar on the 2nd,
which said `04/03/2011`", not a shrug.

So every import keeps its file's shape, its mapping, its options, and every row
it read, with the outcome of each. Two tables:

  `import_batches` — one per upload: what kind, from what file, mapped how,
  with what options, ending in what state.

  `import_rows` — one per line of the file, holding the raw values exactly as
  read, the interpreted values, and the outcome. This is what makes the error
  report per-row rather than per-file, and what makes a reversal possible.

The batch is a workflow, not a log entry. It moves `draft → validated → applied`
and stops at `failed` when the file cannot be applied at all. There is no state
in which some rows have landed and others have not: applying is one database
transaction, and a batch that fails leaves nothing behind.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantOwned, Timestamped, UUIDPrimaryKey


class BatchStatus(str, enum.Enum):
    """Where an import has got to.

    `validated` is a real state rather than a step: a file may be validated on
    Monday, discussed, corrected and applied on Wednesday, and the preview the
    registrar approved must still be there.
    """

    draft = "draft"           # read, not yet checked
    validated = "validated"   # checked; the preview is meaningful
    failed = "failed"         # cannot be applied — nothing was written
    applied = "applied"
    reversed = "reversed"


class RowStatus(str, enum.Enum):
    pending = "pending"
    valid = "valid"
    invalid = "invalid"
    duplicate = "duplicate"   # matches something already here
    skipped = "skipped"       # a duplicate the options said to leave alone
    applied = "applied"
    reversed = "reversed"


class ImportBatch(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One upload, from the file landing to whatever became of it."""

    __tablename__ = "import_batches"
    __table_args__ = (
        Index("ix_import_batches_tenant_created", "tenant_id", "created_at"),
    )

    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # SHA-256 of the uploaded bytes. Not for integrity — for recognising that
    # somebody is uploading the same file a second time, which is the single
    # most common way a school ends up with every student twice.
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="import_batch_status"),
        nullable=False,
        default=BatchStatus.draft,
    )

    # The file's own shape, kept so a preview can be rebuilt without the file.
    columns: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # {field_key: column_name} — the person's decision, not our guess.
    mapping: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    options: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    uploaded_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )
    applied_by_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Why an application failed, in the words the person will be shown.
    failure_reason: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    @property
    def can_apply(self) -> bool:
        return self.status is BatchStatus.validated and self.invalid_count == 0


class ImportRow(UUIDPrimaryKey, Timestamped, TenantOwned, Base):
    """One line of the file, its interpretation, and what became of it."""

    __tablename__ = "import_rows"
    __table_args__ = (
        Index("ix_import_rows_tenant_batch", "tenant_id", "batch_id", "line_number"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    # The file's line number, not the row's index. An error report that does not
    # match what the person sees in their spreadsheet is worse than none.
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # Exactly as read, before mapping or interpretation. This is the evidence.
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # After mapping and parsing — dates as ISO strings, so the row is a faithful
    # record on its own without needing the spec that produced it.
    values: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[RowStatus] = mapped_column(
        Enum(RowStatus, name="import_row_status"),
        nullable=False,
        default=RowStatus.pending,
    )
    # Messages, plural, and per field where it makes sense. One error at a time
    # turns a ten-minute job into a morning.
    errors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # What this row matched, and how confidently, when it matched something.
    matched_by: Mapped[str | None] = mapped_column(String(120))
    # What the row created, so a reversal knows what to look at.
    created: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    @property
    def is_blocking(self) -> bool:
        return self.status is RowStatus.invalid


__all__ = ["BatchStatus", "ImportBatch", "ImportRow", "RowStatus"]
