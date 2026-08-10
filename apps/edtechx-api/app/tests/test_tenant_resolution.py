"""Host-to-tenant resolution, and the token/host agreement check."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.db.registry import Tenant, TenantDomain
from app.db.session import bind_tenant, get_session_factory
from app.modules.tenancy.models import DomainKind, TenantStatus
from app.modules.tenancy.resolver import (
    TenantMismatch,
    TenantUnavailable,
    UnknownHost,
    assert_token_matches_host,
    is_platform_host,
    normalize_host,
    resolve_from_host,
    subdomain_slug,
)
from app.tests.conftest import TenantFixture, requires_db

# --- host normalization (no database needed) ------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("St-Bede.EdTechX.localhost", "st-bede.edtechx.localhost"),
        ("st-bede.edtechx.localhost:8000", "st-bede.edtechx.localhost"),
        ("st-bede.edtechx.localhost.", "st-bede.edtechx.localhost"),
        ("  st-bede.edtechx.localhost  ", "st-bede.edtechx.localhost"),
        ("[::1]:8000", "[::1]"),
        (None, ""),
        ("", ""),
    ],
)
def test_host_normalization(raw: str | None, expected: str) -> None:
    assert normalize_host(raw) == expected


def test_platform_hosts_carry_no_tenant() -> None:
    assert is_platform_host("localhost")
    assert not is_platform_host("st-bede.edtechx.localhost")


def test_subdomain_extraction() -> None:
    assert subdomain_slug("st-bede.edtechx.localhost") == "st-bede"
    assert subdomain_slug("edtechx.localhost") is None
    assert subdomain_slug("example.com") is None


def test_nested_subdomains_are_not_tenant_hosts() -> None:
    """`anything.st-bede.edtechx.localhost` must not resolve.

    Accepting a multi-label prefix would let anyone construct a plausible
    hostname and probe for tenants.
    """
    assert subdomain_slug("evil.st-bede.edtechx.localhost") is None


# --- token / host agreement (no database needed) --------------------------


def test_matching_token_and_host_are_accepted() -> None:
    tenant = uuid.uuid4()
    assert assert_token_matches_host(tenant, tenant) == tenant


def test_a_token_from_another_school_is_refused() -> None:
    """The realistic attack: a valid token replayed on a different school's host."""
    with pytest.raises(TenantMismatch):
        assert_token_matches_host(uuid.uuid4(), uuid.uuid4())


def test_anonymous_request_on_a_tenant_host_keeps_the_host_tenant() -> None:
    host_tenant = uuid.uuid4()
    assert assert_token_matches_host(host_tenant, None) == host_tenant


# --- database-backed resolution -------------------------------------------

pytestmark_db = requires_db


@requires_db
def test_resolves_a_school_from_its_hostname(school_a: TenantFixture) -> None:
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        resolved = resolve_from_host(session, school_a.hostname)
        assert resolved is not None
        assert resolved.id == school_a.tenant_id
        assert resolved.slug == school_a.tenant.slug
    finally:
        session.close()


@requires_db
def test_resolution_ignores_port_and_case(school_a: TenantFixture) -> None:
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        resolved = resolve_from_host(session, f"{school_a.hostname.upper()}:8443")
        assert resolved is not None and resolved.id == school_a.tenant_id
    finally:
        session.close()


@requires_db
def test_platform_host_resolves_to_no_tenant() -> None:
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        assert resolve_from_host(session, "localhost:8000") is None
    finally:
        session.close()


@requires_db
def test_unknown_host_is_refused() -> None:
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        with pytest.raises(UnknownHost):
            resolve_from_host(session, "not-a-school.example.com")
        with pytest.raises(UnknownHost):
            resolve_from_host(session, "ghost.edtechx.localhost")
    finally:
        session.close()


@requires_db
def test_suspended_school_does_not_resolve(school_a: TenantFixture) -> None:
    """A suspended school is unavailable, not silently served."""
    admin = get_session_factory()()
    bind_tenant(admin, None)
    try:
        tenant = admin.get(Tenant, school_a.tenant_id)
        assert tenant is not None
        tenant.status = TenantStatus.suspended
        admin.commit()

        with pytest.raises(TenantUnavailable) as exc:
            resolve_from_host(admin, school_a.hostname)
        assert exc.value.status is TenantStatus.suspended
    finally:
        admin.rollback()
        admin.close()


@requires_db
def test_unverified_custom_domain_does_not_resolve(school_a: TenantFixture) -> None:
    """A custom domain must prove control before it can carry a school's identity.

    Otherwise any tenant could claim any hostname and receive traffic meant for
    it the moment DNS happened to point their way.
    """
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        session.add(
            TenantDomain(
                tenant_id=school_a.tenant_id,
                hostname="portal.unverified-example.test",
                kind=DomainKind.custom,
                is_primary=False,
                verified_at=None,
            )
        )
        session.commit()

        with pytest.raises(UnknownHost, match="not verified"):
            resolve_from_host(session, "portal.unverified-example.test")
    finally:
        session.rollback()
        session.close()


@requires_db
def test_verified_custom_domain_resolves(school_a: TenantFixture) -> None:
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        session.add(
            TenantDomain(
                tenant_id=school_a.tenant_id,
                hostname="portal.verified-example.test",
                kind=DomainKind.custom,
                is_primary=False,
                verified_at=datetime.now(UTC),
            )
        )
        session.commit()

        resolved = resolve_from_host(session, "portal.verified-example.test")
        assert resolved is not None and resolved.id == school_a.tenant_id
    finally:
        session.rollback()
        session.close()


@requires_db
def test_a_schools_hostname_never_resolves_to_another_school(
    school_a: TenantFixture, school_b: TenantFixture
) -> None:
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        assert resolve_from_host(session, school_a.hostname).id == school_a.tenant_id
        assert resolve_from_host(session, school_b.hostname).id == school_b.tenant_id
    finally:
        session.close()
