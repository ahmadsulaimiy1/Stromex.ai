"""Build a schema with isolation already switched on.

Used by the test suite and by local development. Production schema changes go
through Alembic, but they call the same `apply_rls` and `grant_app_role`
helpers, so there is exactly one definition of what "protected" means.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.db.registry import Base
from app.db.rls import apply_rls, grant_app_role, missing_tables, verify_rls


def build_schema(app_role: str = "edtechx_app", drop_first: bool = False) -> list[str]:
    """Create the schema, enable RLS, and grant the request-path role.

    Returns the tables that received an isolation policy. Raises if any
    tenant-owned table ends up unprotected — a half-applied policy set is more
    dangerous than none, because it looks fine.
    """
    settings = get_settings()
    engine = create_engine(settings.migration_database_url, future=True)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
            if drop_first:
                Base.metadata.drop_all(connection)
            Base.metadata.create_all(connection)
            protected = apply_rls(connection)
            grant_app_role(connection, app_role)

        with engine.connect() as connection:
            unprotected = verify_rls(connection)
            absent = missing_tables(connection)
        if unprotected:
            raise RuntimeError(
                "Tenant-owned tables without row-level security: "
                + ", ".join(sorted(unprotected))
            )
        if absent:
            # `verify_rls` tolerates a missing table because a migration mid-
            # chain legitimately has not created it yet. A freshly built schema
            # has no such excuse.
            raise RuntimeError(
                "Tenant-owned models with no table: " + ", ".join(sorted(absent))
            )
        return protected
    finally:
        engine.dispose()
