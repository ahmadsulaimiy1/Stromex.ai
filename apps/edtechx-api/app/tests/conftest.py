"""Test fixtures.

Real PostgreSQL, deliberately (ADR-016). The isolation guarantee this suite
exists to prove is a PostgreSQL feature; a SQLite test suite would be green and
meaningless.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest

os.environ.setdefault("EDTECHX_ENVIRONMENT", "test")
os.environ.setdefault(
    "EDTECHX_DATABASE_URL",
    "postgresql+psycopg://edtechx_app:edtechx_app@localhost:5432/edtechx_test",
)
os.environ.setdefault(
    "EDTECHX_MIGRATION_DATABASE_URL",
    "postgresql+psycopg://edtechx_migrator:edtechx_migrator@localhost:5432/edtechx_test",
)
os.environ.setdefault("EDTECHX_SECRET_KEY", "test-secret-key-that-is-long-enough-32")

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.bootstrap import build_schema
from app.db.registry import (
    Membership,
    Role,
    Tenant,
    User,
)
from app.db.session import bind_tenant, get_engine, get_session_factory


def _database_available() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


DB_AVAILABLE = _database_available()
requires_db = pytest.mark.skipif(
    not DB_AVAILABLE, reason="PostgreSQL is not available on localhost:5432"
)


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Iterator[None]:
    if not DB_AVAILABLE:
        yield
        return
    build_schema(drop_first=True)
    yield


@pytest.fixture
def db() -> Iterator[Session]:
    """A session with no tenant bound — used for platform-level fixtures."""
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def session_for(tenant_id: uuid.UUID) -> Session:
    session = get_session_factory()()
    bind_tenant(session, tenant_id)
    return session


class TenantFixture:
    """A provisioned school with one owner, ready to be worked against."""

    def __init__(self, tenant: Tenant, user: User, membership: Membership, role: Role):
        self.tenant = tenant
        self.tenant_id = tenant.id
        self.user = user
        self.user_id = user.id
        self.membership = membership
        self.membership_id = membership.id
        self.role = role
        self.hostname = f"{tenant.slug}.edtechx.localhost"

    def session(self) -> Session:
        return session_for(self.tenant_id)


OWNER_PASSWORD = "a-perfectly-fine-passphrase"


def _provision(slug: str) -> TenantFixture:
    """Create a school through the real provisioning service.

    Deliberately not hand-rolled here any more: a fixture that builds tenants
    differently from production is a fixture that tests something production
    never does.
    """
    from app.modules.tenancy.service import provision_school

    result = provision_school(
        slug=slug,
        name=slug.replace("-", " ").title(),
        owner_email=f"owner@{slug}.test",
        owner_name=f"{slug} Owner",
        owner_password=OWNER_PASSWORD,
        base_domain="edtechx.localhost",
        currency="GBP",
    )

    scoped = session_for(result.tenant_id)
    try:
        tenant = scoped.get(Tenant, result.tenant_id)
        user = scoped.get(User, result.owner_user_id)
        membership = scoped.get(Membership, result.owner_membership_id)
        role = scoped.execute(select(Role).where(Role.key == "owner")).scalar_one()
        assert tenant and user and membership
        return TenantFixture(tenant, user, membership, role)
    finally:
        scoped.close()


@pytest.fixture
def school_a() -> TenantFixture:
    return _provision(f"school-a-{uuid.uuid4().hex[:8]}")


@pytest.fixture
def school_b() -> TenantFixture:
    return _provision(f"school-b-{uuid.uuid4().hex[:8]}")


@pytest.fixture
def future() -> datetime:
    return datetime.now(UTC) + timedelta(days=1)
