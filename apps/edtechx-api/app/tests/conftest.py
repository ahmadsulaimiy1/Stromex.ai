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

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.bootstrap import build_schema
from app.db.registry import (
    Membership,
    MembershipRole,
    Role,
    RolePermission,
    Tenant,
    TenantDomain,
    User,
)
from app.db.session import bind_tenant, get_engine, get_session_factory
from app.modules.authz.system_roles import SYSTEM_ROLES_BY_KEY
from app.modules.identity.models import (
    MembershipStatus,
    UserStatus,
)
from app.modules.tenancy.models import DomainKind, TenantStatus


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


def _provision(slug: str) -> TenantFixture:
    """Create a school the way provisioning will: tenant, domain, roles, owner."""
    factory = get_session_factory()

    # Tenant and domain are platform tables, created without a tenant context.
    platform = factory()
    bind_tenant(platform, None)
    try:
        tenant = Tenant(
            slug=slug,
            name=slug.replace("-", " ").title(),
            status=TenantStatus.active,
            timezone="UTC",
            locale="en",
            currency="GBP",
            activated_at=datetime.now(UTC),
        )
        platform.add(tenant)
        platform.flush()
        platform.add(
            TenantDomain(
                tenant_id=tenant.id,
                hostname=f"{slug}.edtechx.localhost",
                kind=DomainKind.subdomain,
                is_primary=True,
            )
        )
        user = User(
            email=f"owner@{slug}.test",
            full_name=f"{slug} Owner",
            status=UserStatus.active,
            email_verified_at=datetime.now(UTC),
        )
        platform.add(user)
        platform.commit()
        tenant_id = tenant.id
        user_id = user.id
    finally:
        platform.close()

    # Everything else is written inside the tenant's own context, exactly as
    # application code will.
    scoped = session_for(tenant_id)
    try:
        template = SYSTEM_ROLES_BY_KEY["owner"]
        role = Role(
            key=template.key,
            name=template.name,
            description=template.description,
            is_system=True,
        )
        scoped.add(role)
        scoped.flush()
        for permission in sorted(template.permissions):
            scoped.add(RolePermission(role_id=role.id, permission=permission))

        membership = Membership(
            user_id=user_id,
            status=MembershipStatus.active,
            display_name=f"{slug} Owner",
            started_at=datetime.now(UTC),
        )
        scoped.add(membership)
        scoped.flush()
        scoped.add(
            MembershipRole(
                membership_id=membership.id,
                role_id=role.id,
                scope=template.default_scope.to_json(),
                granted_at=datetime.now(UTC),
            )
        )
        scoped.commit()
        scoped.refresh(role)
        scoped.refresh(membership)
        tenant_obj = scoped.get(Tenant, tenant_id)
        user_obj = scoped.get(User, user_id)
        assert tenant_obj is not None and user_obj is not None
        return TenantFixture(tenant_obj, user_obj, membership, role)
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
