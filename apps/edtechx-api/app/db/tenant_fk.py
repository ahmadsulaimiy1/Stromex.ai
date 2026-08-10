"""Making foreign keys respect the tenant boundary.

Row-level security governs `SELECT`, `INSERT`, `UPDATE` and `DELETE`. It does
**not** govern referential integrity: PostgreSQL runs a foreign-key check with
the privileges of the referenced table's owner and without applying its
policies, which is documented behaviour and is the right default for a database
where every row belongs to everybody.

For a multi-tenant schema it is a hole. A plain `enrolments.student_relationship_id
REFERENCES student_relationships(id)` lets one institution insert a row pointing
at another institution's student. Three consequences, in ascending order of
seriousness:

  1. The row is corrupt: it names a parent its own tenant cannot read.
  2. `ON DELETE RESTRICT` then lets one tenant block another's deletion — a
     cross-tenant denial of service with no visible cause.
  3. Worst, the insert *succeeds only if the id exists somewhere in the
     system*, which turns every foreign key into an existence oracle for other
     tenants' records. That is precisely the disclosure `ADR-004` exists to
     prevent, arriving through the one door row-level security does not watch.

The fix is standard and structural: reference the parent by `(tenant_id, id)`
rather than by `id`. The child's `tenant_id` is stamped from the request
context, so a reference into another tenant simply has no matching parent row —
enforced by the database, on every path, including raw SQL.

This module applies that transformation to the whole metadata rather than
asking each model to remember it, on the same principle as `TenantOwned`: a new
tenant-owned model gets a tenant-scoped foreign key by existing.

`ON DELETE SET NULL` needs care. Nulling the whole referencing key would null
`tenant_id`, which is `NOT NULL` — so the clause becomes `SET NULL (column)`,
naming only the nullable half. That form requires PostgreSQL 15 or later, which
`EDTECHX_ARCHITECTURE.md` §2 already assumes.
"""

from __future__ import annotations

from sqlalchemy import ForeignKeyConstraint, MetaData, UniqueConstraint

from app.db.base import TENANT_OWNED_MODELS

TENANT_COLUMN = "tenant_id"


def tenant_owned_tables() -> set[str]:
    return {model.__tablename__ for model in TENANT_OWNED_MODELS}


def _target_table(constraint: ForeignKeyConstraint) -> str:
    return next(iter(constraint.elements)).column.table.name


def _rewrite_ondelete(ondelete: str | None, column: str) -> str | None:
    """Keep `SET NULL` from nulling `tenant_id` along with the reference."""
    if ondelete and ondelete.strip().upper() == "SET NULL":
        return f"SET NULL ({column})"
    if ondelete and ondelete.strip().upper() == "SET DEFAULT":
        return f"SET DEFAULT ({column})"
    return ondelete


def crossing_constraints(
    metadata: MetaData,
) -> list[tuple[str, str, ForeignKeyConstraint]]:
    """Every single-column foreign key from one tenant-owned table to another.

    Excludes the `tenant_id` key itself, which points at `tenants` — a table
    that is not tenant-owned and is the anchor of the whole scheme.
    """
    owned = tenant_owned_tables()
    found: list[tuple[str, str, ForeignKeyConstraint]] = []
    for table_name in sorted(owned):
        table = metadata.tables.get(table_name)
        if table is None:
            continue
        for constraint in sorted(
            table.foreign_key_constraints, key=lambda c: sorted(c.columns.keys())
        ):
            columns = list(constraint.columns.keys())
            if len(columns) != 1 or columns[0] == TENANT_COLUMN:
                continue
            if _target_table(constraint) in owned:
                found.append((table_name, columns[0], constraint))
    return found


def bind_foreign_keys_to_tenant(metadata: MetaData) -> list[str]:
    """Rewrite every cross-table tenant-owned foreign key as `(tenant_id, id)`.

    Idempotent, and safe to call once at import time. Returns the constraint
    names it created, so a caller can report what it did rather than trusting
    that it did anything.
    """
    owned = tenant_owned_tables()

    # A composite foreign key needs a matching unique key on the parent. `id` is
    # already the primary key; this adds the pair the child will reference.
    for table_name in sorted(owned):
        table = metadata.tables.get(table_name)
        if table is None:
            continue
        name = f"uq_{table_name}_tenant_id_id"
        if any(getattr(c, "name", None) == name for c in table.constraints):
            continue
        table.append_constraint(
            UniqueConstraint(TENANT_COLUMN, "id", name=name)
        )

    created: list[str] = []
    for table_name, column_name, constraint in crossing_constraints(metadata):
        table = metadata.tables[table_name]
        target = _target_table(constraint)
        ondelete = _rewrite_ondelete(constraint.ondelete, column_name)
        onupdate = constraint.onupdate

        # Detach the single-column key: from the table's constraint set, from
        # the column, and from the table's foreign-key index. All three are
        # consulted — by DDL emission, by dependency sorting, and by reflection
        # comparison respectively — and leaving any of them behind produces a
        # schema with both keys, which would defeat the point.
        table.constraints.discard(constraint)
        for element in list(constraint.elements):
            table.c[column_name].foreign_keys.discard(element)
            table.foreign_keys.discard(element)

        name = f"fk_{table_name}_{column_name}_tenant"
        table.append_constraint(
            ForeignKeyConstraint(
                [TENANT_COLUMN, column_name],
                [f"{target}.{TENANT_COLUMN}", f"{target}.id"],
                name=name,
                ondelete=ondelete,
                onupdate=onupdate,
            )
        )
        created.append(name)
    return created


def unscoped_foreign_keys(metadata: MetaData) -> list[str]:
    """Tenant-owned foreign keys that still reference a parent by id alone.

    The check behind the test. An empty list is the only acceptable result:
    anything here is a row one tenant can point at from another.
    """
    return [
        f"{table}.{column} -> {_target_table(constraint)}"
        for table, column, constraint in crossing_constraints(metadata)
    ]
