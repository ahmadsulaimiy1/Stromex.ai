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


def apply_rls(connection: Connection, tables: list[str] | None = None) -> list[str]:
    """Enable and (re)create the isolation policy on every tenant-owned table.

    Idempotent: safe to run on every migration and on every test-database
    build. Returns the tables it touched.
    """
    targets = tables if tables is not None else tenant_owned_table_names()
    for table in targets:
        for statement in policy_statements(table):
            connection.execute(text(statement))
    return targets


def grant_app_role(connection: Connection, role: str) -> None:
    """Grant the request-path role exactly what it needs, and nothing more.

    Notably absent: UPDATE and DELETE on `audit_events`. The audit log is an
    append-only compliance artefact (EDTECHX_SECURITY.md §9); the application
    must be structurally incapable of rewriting it.
    """
    connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {role}"))
    connection.execute(
        text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role}")
    )
    connection.execute(
        text(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {role}")
    )
    connection.execute(text(f"REVOKE UPDATE, DELETE ON audit_events FROM {role}"))
    connection.execute(text(f"REVOKE UPDATE, DELETE ON security_events FROM {role}"))


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
        enabled, forced, policies = state.get(table, (False, False, 0))
        if not (enabled and forced and policies > 0):
            unprotected.append(table)
    return unprotected
