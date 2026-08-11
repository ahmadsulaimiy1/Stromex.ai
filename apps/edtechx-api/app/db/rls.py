"""Row-level security: the layer that actually enforces tenant isolation.

Layers 1 (request context) and 3 (ORM guard) exist to fail fast and to keep
application code honest. This module is the guarantee. If every line of
application code forgot its `WHERE tenant_id = ...`, PostgreSQL would still
return zero rows.

Two details matter more than they look:

  * FORCE ROW LEVEL SECURITY — without it the table *owner* bypasses the
    policy, so a deployment that accidentally connected as the owner would
    silently lose isolation while every test still passed.

  * NULLIF(current_setting(...), '') — an unset or blank setting must yield
    SQL NULL, so the predicate is false and no rows are visible. Casting ''
    directly to uuid raises, which would turn a missing context into a 500
    rather than into an empty result; both are safe, but the NULL form lets
    genuinely tenant-less queries (platform tables) behave predictably.
"""

from __future__ import annotations

from sqlalchemy import Connection, text

from app.db.base import TENANT_OWNED_MODELS

TENANT_SETTING = "app.tenant_id"
POLICY_NAME = "tenant_isolation"

_TENANT_PREDICATE = (
    f"tenant_id = NULLIF(current_setting('{TENANT_SETTING}', true), '')::uuid"
)

# Written once, never rewritten. The application role gets INSERT and SELECT and
# nothing else, so "append-only" is a property of the grant rather than of the
# code that happens to be calling.
APPEND_ONLY_TABLES: tuple[str, ...] = (
    "audit_events",
    "security_events",
    "enrolment_events",
    "attendance_amendments",
    "approval_records",
    "result_amendments",
)

# Rows that may be corrected but never erased. A published result joins the
# list for the same reason an enrolment does: it happened, it was relied on, and
# a system able to make it disappear cannot be trusted with the ones that remain.
# An issued document is the same argument with a signature on it: it is withdrawn
# by being voided and replaced by being superseded, and both survive.
UNDELETABLE_TABLES: tuple[str, ...] = (
    "enrolments",
    "published_results",
    "documents",
)


def tenant_owned_table_names() -> list[str]:
    return [m.__tablename__ for m in TENANT_OWNED_MODELS]


def policy_statements(table: str) -> list[str]:
    return [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
        f"DROP POLICY IF EXISTS {POLICY_NAME} ON {table}",
        (
            f"CREATE POLICY {POLICY_NAME} ON {table} "
            f"USING ({_TENANT_PREDICATE}) "
            f"WITH CHECK ({_TENANT_PREDICATE})"
        ),
    ]


def existing_tables(connection: Connection) -> set[str]:
    return set(
        connection.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        .scalars()
        .all()
    )


def apply_rls(connection: Connection, tables: list[str] | None = None) -> list[str]:
    """Enable and (re)create the isolation policy on every tenant-owned table.

    Scoped to tables that *exist*, not to every model in the registry. A
    migration runs against the schema as it stands at that revision: the
    baseline cannot protect a table a later migration has not created yet.
    Ignoring that produced a baseline that failed the moment a new model was
    added — which is the right failure, caught in the wrong place.

    Tables that exist but are unprotected are still the caller's problem, and
    `verify_rls` reports them.

    Idempotent: safe to run on every migration and every test-database build.
    """
    present = existing_tables(connection)
    targets = [
        table
        for table in (tables if tables is not None else tenant_owned_table_names())
        if table in present
    ]
    for table in targets:
        for statement in policy_statements(table):
            connection.execute(text(statement))
    return targets


def grant_app_role(connection: Connection, role: str) -> None:
    """Grant the request-path role exactly what it needs, and nothing more.

    Notably absent: UPDATE and DELETE on `audit_events`. The audit log is an
    append-only compliance artefact (EDTECHX_SECURITY.md §9); the application
    must be structurally incapable of rewriting it.

    `enrolment_events` is held to the same standard, for the same reason. A
    student's academic history is the record an institution is asked to produce
    years later, and a correction to it must be a new event rather than an
    edit. `enrolments` keeps UPDATE — a placement has to be closable — but not
    DELETE: a placement that happened cannot be made not to have happened.
    """
    connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {role}"))
    connection.execute(
        text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role}")
    )
    connection.execute(
        text(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {role}")
    )
    # Existence-aware, because this runs inside migrations too: at the baseline
    # revision the later tables do not exist yet, and a REVOKE on a missing
    # table aborts the transaction.
    present = existing_tables(connection)
    for table in APPEND_ONLY_TABLES:
        if table in present:
            connection.execute(text(f"REVOKE UPDATE, DELETE ON {table} FROM {role}"))
    for table in UNDELETABLE_TABLES:
        if table in present:
            connection.execute(text(f"REVOKE DELETE ON {table} FROM {role}"))


def verify_rls(connection: Connection) -> list[str]:
    """Return tenant-owned tables that are not correctly protected.

    Called by a test and by the migration gate. An empty list is the only
    acceptable result; anything else blocks the release.
    """
    rows = connection.execute(
        text(
            """
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
                   (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid) AS policies
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
            """
        )
    ).all()
    state = {r[0]: (r[1], r[2], r[3]) for r in rows}

    unprotected: list[str] = []
    for table in tenant_owned_table_names():
        if table not in state:
            # Not yet created at this revision. Whether a model's table is
            # missing entirely is a schema-drift question, answered by
            # `missing_tables` and by the migration drift test — not by the
            # isolation check, which would otherwise fail every migration that
            # runs before the last one.
            continue
        enabled, forced, policies = state[table]
        if not (enabled and forced and policies > 0):
            unprotected.append(table)
    return unprotected


def missing_tables(connection: Connection) -> list[str]:
    """Tenant-owned models with no table. Used by the production readiness check."""
    present = existing_tables(connection)
    return [t for t in tenant_owned_table_names() if t not in present]
