"""The migration path must produce exactly the schema the models describe.

Two failure modes this guards against, both of which are silent:

  * a model changes and nobody writes the migration, so development works from
    `build_schema()` and production drifts;
  * a migration creates tables without enabling row-level security, which looks
    entirely successful and removes the product's central guarantee.

Runs against its own scratch database so it cannot disturb the suite's.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text

from app.db.registry import Base
from app.db.rls import tenant_owned_table_names, verify_rls
from app.tests.conftest import requires_db

pytestmark = requires_db

API_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRATCH_DB = "edtechx_mig"
MIGRATION_URL = (
    f"postgresql+psycopg://edtechx_migrator:edtechx_migrator@localhost:5432/{SCRATCH_DB}"
)
# No CREATE DATABASE here on purpose: the migrator role deliberately lacks
# CREATEDB, which is the right posture for a role whose only job is DDL on one
# database. Resetting the schema achieves the same clean slate within the
# privileges the role actually has in production.


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=API_ROOT,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": "/root",
            "EDTECHX_ENVIRONMENT": "test",
            "EDTECHX_SECRET_KEY": "test-secret-key-that-is-long-enough-32",
            "EDTECHX_MIGRATION_DATABASE_URL": MIGRATION_URL,
            "EDTECHX_DATABASE_URL": MIGRATION_URL.replace(
                "edtechx_migrator:edtechx_migrator", "edtechx_app:edtechx_app"
            ),
        },
        timeout=180,
    )


def _scratch_available() -> bool:
    engine = create_engine(MIGRATION_URL, future=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


@pytest.fixture(scope="module")
def migrated() -> str:
    """A scratch database built entirely by `alembic upgrade head`."""
    if not _scratch_available():
        pytest.skip(
            f"Scratch database {SCRATCH_DB!r} is absent. Create it once with "
            f"`CREATE DATABASE {SCRATCH_DB} OWNER edtechx_migrator;` — see the "
            "API README. The migrator role deliberately cannot create it itself."
        )
    engine = create_engine(MIGRATION_URL, future=True)
    try:
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
            connection.execute(text("GRANT USAGE ON SCHEMA public TO edtechx_app"))
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    finally:
        engine.dispose()

    result = _alembic("upgrade", "head")
    assert result.returncode == 0, f"alembic upgrade failed:\n{result.stderr}"
    return MIGRATION_URL


def test_upgrade_creates_every_table(migrated: str) -> None:
    engine = create_engine(migrated, future=True)
    try:
        with engine.connect() as connection:
            present = set(
                connection.execute(
                    text(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                    )
                )
                .scalars()
                .all()
            )
    finally:
        engine.dispose()

    expected = set(Base.metadata.tables) | {"alembic_version"}
    missing = expected - present
    assert not missing, f"The migration did not create: {sorted(missing)}"


def test_migrated_schema_has_row_level_security(migrated: str) -> None:
    """The gate that makes this migration worth having.

    A schema built by migration must be as protected as one built by
    `build_schema()`. If these two paths can diverge, production and development
    disagree about the one guarantee that must never be wrong.
    """
    engine = create_engine(migrated, future=True)
    try:
        with engine.connect() as connection:
            unprotected = verify_rls(connection)
    finally:
        engine.dispose()
    assert unprotected == [], (
        f"Migrated schema leaves these tenant-owned tables unprotected: {unprotected}"
    )


def test_every_tenant_owned_table_is_actually_covered(migrated: str) -> None:
    """Guards the guard: `verify_rls` must be checking a non-empty set."""
    assert len(tenant_owned_table_names()) >= 6


def test_migration_matches_the_models(migrated: str) -> None:
    """Autogenerate against the migrated database must find nothing to do.

    This is the drift check: if a model has changed without a migration, the
    comparison produces operations and this fails, naming what is missing.
    """
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    engine = create_engine(migrated, future=True)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection, opts={"compare_type": True}
            )
            diff = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()

    # Alembic reports the RLS-only artefacts it cannot model; nothing else is
    # acceptable.
    material = [d for d in diff if not _is_ignorable(d)]
    assert not material, (
        "The models and the migrations have drifted. Missing migration for:\n"
        + "\n".join(repr(d) for d in material)
    )


def _is_ignorable(diff_item: object) -> bool:
    text_form = repr(diff_item)
    return "alembic_version" in text_form


def test_downgrade_is_defined(migrated: str) -> None:
    """A baseline with no down path cannot be rolled back in an incident."""
    result = _alembic("downgrade", "base")
    assert result.returncode == 0, f"downgrade failed:\n{result.stderr}"

    engine = create_engine(migrated, future=True)
    try:
        with engine.connect() as connection:
            remaining = set(
                connection.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
                .scalars()
                .all()
            )
    finally:
        engine.dispose()
    assert remaining <= {"alembic_version"}, f"downgrade left tables behind: {remaining}"

    # Leave the scratch database at head so ordering between tests cannot
    # matter to anything that runs later.
    assert _alembic("upgrade", "head").returncode == 0
