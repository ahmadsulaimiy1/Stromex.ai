"""Critical journey 12: Tenant A must never reach Tenant B.

These tests are generated from the model registry rather than written by hand.
A new tenant-owned model is covered the moment it exists, which is the only way
this guarantee survives a codebase that will grow to hundreds of tables.

The suite deliberately attacks the database directly, bypassing every service,
router, and ORM convenience — because that is what a bug in application code
would effectively do.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import ProgrammingError

from app.db.base import TENANT_OWNED_MODELS
from app.db.registry import Membership, Role, Tenant
from app.db.rls import verify_rls
from app.db.session import bind_tenant, get_engine, get_session_factory
from app.tests.conftest import TenantFixture, requires_db, session_for

pytestmark = requires_db

TENANT_OWNED = sorted(TENANT_OWNED_MODELS, key=lambda m: m.__tablename__)
TABLE_IDS = [m.__tablename__ for m in TENANT_OWNED]


# --- structural guarantees ------------------------------------------------


def test_every_tenant_owned_table_has_a_forced_policy() -> None:
    """No tenant-owned table may exist without FORCE RLS and a policy."""
    with get_engine().connect() as connection:
        unprotected = verify_rls(connection)
    assert unprotected == [], (
        "These tenant-owned tables are not protected by row-level security: "
        f"{unprotected}. Every model carrying TenantOwned must have a forced "
        "policy — see EDTECHX_DATABASE.md §2."
    )


def test_application_role_cannot_bypass_rls() -> None:
    """The request-path role must not hold BYPASSRLS, and must not own tables.

    Either would make every other test in this file meaningless.
    """
    with get_engine().connect() as connection:
        bypasses = connection.execute(
            text("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = current_user")
        ).one()
        assert bypasses[0] is False, "Application role holds BYPASSRLS"
        assert bypasses[1] is False, "Application role is a superuser"

        owned = connection.execute(
            text(
                """
                SELECT count(*) FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relkind = 'r'
                  AND pg_get_userbyid(c.relowner) = current_user
                """
            )
        ).scalar_one()
        assert owned == 0, "Application role owns tables; FORCE RLS would be bypassed"


def test_audit_log_is_append_only_for_the_application_role() -> None:
    """The application must be structurally unable to rewrite history."""
    session = get_session_factory()()
    bind_tenant(session, uuid.uuid4())
    try:
        with pytest.raises(ProgrammingError):
            session.execute(text("UPDATE audit_events SET reason = 'tampered'"))
        session.rollback()
        with pytest.raises(ProgrammingError):
            session.execute(text("DELETE FROM audit_events"))
        session.rollback()
    finally:
        session.close()


# --- read isolation, generated over every model ---------------------------


@pytest.mark.parametrize("model", TENANT_OWNED, ids=TABLE_IDS)
def test_foreign_tenant_sees_no_rows(
    model: type, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """Raw SQL from B's context must not see A's rows, for every table."""
    table = model.__tablename__
    session = school_b.session()
    try:
        leaked = session.execute(
            text(f"SELECT count(*) FROM {table} WHERE tenant_id = :other"),
            {"other": str(school_a.tenant_id)},
        ).scalar_one()
        assert leaked == 0, (
            f"{table}: school B's session can see {leaked} of school A's rows. "
            "Row-level security is not enforcing on this table."
        )
    finally:
        session.close()


@pytest.mark.parametrize("model", TENANT_OWNED, ids=TABLE_IDS)
def test_unbound_session_sees_nothing(model: type, school_a: TenantFixture) -> None:
    """A session with no tenant context is blind, not omniscient.

    This is the failure mode that matters most: a background job, a script, or
    a forgotten code path that never established a tenant. It must see nothing,
    not everything.
    """
    table = model.__tablename__
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        visible = session.execute(
            text(f"SELECT count(*) FROM {table}")
        ).scalar_one()
        assert visible == 0, (
            f"{table}: a session with no tenant context sees {visible} rows. "
            "An unbound context must resolve to no access, never to all access."
        )
    finally:
        session.close()


# --- write isolation ------------------------------------------------------


def test_cannot_insert_a_row_for_another_tenant(
    school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """The WITH CHECK clause must refuse a foreign tenant_id on insert."""
    session = school_b.session()
    try:
        with pytest.raises(ProgrammingError) as exc:
            session.execute(
                text(
                    "INSERT INTO roles (id, tenant_id, key, name, is_system,"
                    " created_at, updated_at)"
                    " VALUES (gen_random_uuid(), :other, 'smuggled', 'Smuggled',"
                    " false, now(), now())"
                ),
                {"other": str(school_a.tenant_id)},
            )
        assert "row-level security" in str(exc.value).lower()
        session.rollback()
    finally:
        session.close()


def test_orm_guard_refuses_a_foreign_tenant_before_the_database_does(
    school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """Layer 3 fails fast with a useful message; layer 2 is the real stop."""
    session = school_b.session()
    try:
        session.add(Role(tenant_id=school_a.tenant_id, key="smuggled", name="Smuggled"))
        with pytest.raises(PermissionError, match="Refusing to write"):
            session.flush()
        session.rollback()
    finally:
        session.close()


def test_cannot_update_another_tenants_row(
    school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """An UPDATE naming another tenant's row must affect nothing."""
    session = school_b.session()
    try:
        result = session.execute(
            text("UPDATE roles SET name = 'hijacked' WHERE tenant_id = :other"),
            {"other": str(school_a.tenant_id)},
        )
        assert result.rowcount == 0
        session.commit()
    finally:
        session.close()

    verify = school_a.session()
    try:
        names = verify.execute(select(Role.name)).scalars().all()
        assert "hijacked" not in names
    finally:
        verify.close()


def test_cannot_delete_another_tenants_row(
    school_a: TenantFixture, school_b: TenantFixture
) -> None:
    session = school_b.session()
    try:
        result = session.execute(
            text("DELETE FROM roles WHERE tenant_id = :other"),
            {"other": str(school_a.tenant_id)},
        )
        assert result.rowcount == 0
        session.commit()
    finally:
        session.close()

    verify = school_a.session()
    try:
        remaining = verify.execute(select(func.count(Role.id))).scalar_one()
        assert remaining > 0, "School A's roles were deleted from school B's session"
    finally:
        verify.close()


# --- identity boundaries --------------------------------------------------


def test_membership_lookup_by_id_fails_across_tenants(
    school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """Knowing a valid id from another school must not be enough — the IDOR case."""
    session = school_b.session()
    try:
        assert session.get(Membership, school_a.membership_id) is None
    finally:
        session.close()


def test_each_school_sees_exactly_its_own_roles(
    school_a: TenantFixture, school_b: TenantFixture
) -> None:
    a_session = school_a.session()
    b_session = school_b.session()
    try:
        a_ids = set(a_session.execute(select(Role.id)).scalars().all())
        b_ids = set(b_session.execute(select(Role.id)).scalars().all())
        assert a_ids and b_ids
        assert a_ids.isdisjoint(b_ids)
        assert school_a.role.id in a_ids
        assert school_a.role.id not in b_ids
    finally:
        a_session.close()
        b_session.close()


def test_tenant_table_itself_is_not_tenant_owned() -> None:
    """`tenants` defines tenants; a policy on it would break host resolution."""
    assert Tenant not in TENANT_OWNED_MODELS


def test_orm_query_is_filtered_even_without_an_explicit_where(
    school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """The developer-facing case: a query that simply forgot to scope itself."""
    session = session_for(school_b.tenant_id)
    try:
        roles = session.execute(select(Role)).scalars().all()
        assert all(r.tenant_id == school_b.tenant_id for r in roles)
    finally:
        session.close()
