"""Sign-in, refresh rotation, reuse detection, lockout, and provisioning.

The interesting assertions here are the negative ones. Anyone can verify that a
correct password signs a person in; what matters is that a wrong one, a
non-existent account, a suspended account, and an account belonging to a
*different school* are indistinguishable from outside.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.errors import ValidationFailed
from app.main import app
from app.modules.authz.models import Role
from app.modules.identity.models import User, UserSession
from app.modules.tenancy.models import Tenant
from app.modules.tenancy.service import (
    RESERVED_SLUGS,
    provision_school,
    suspend,
    validate_slug,
)
from app.tests.conftest import OWNER_PASSWORD, TenantFixture, requires_db

pytestmark = requires_db


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _sign_in(client: TestClient, school: TenantFixture, password: str, email: str | None = None):
    return client.post(
        "/api/v1/auth/sign-in",
        headers={"Host": school.hostname},
        json={"email": email or school.user.email, "password": password},
    )


# --- provisioning ---------------------------------------------------------


def test_provisioning_creates_a_complete_school(school_a: TenantFixture) -> None:
    session = school_a.session()
    try:
        roles = session.execute(select(Role)).scalars().all()
        assert {r.key for r in roles} >= {"owner", "teacher", "guardian", "student"}
        assert all(r.is_system for r in roles)
    finally:
        session.close()


def test_provisioned_school_is_active_and_resolvable(
    client: TestClient, school_a: TenantFixture
) -> None:
    response = client.get("/api/v1/context", headers={"Host": school_a.hostname})
    assert response.status_code == 200
    assert response.json()["school"]["id"] == str(school_a.tenant_id)


def test_slug_validation_rejects_the_obvious_mistakes() -> None:
    for bad in ("", "a", "Has Capitals", "-leading", "trailing-", "under_score", "a" * 70):
        with pytest.raises(ValidationFailed):
            validate_slug(bad)
    assert validate_slug("  St-Bede  ") == "st-bede"


def test_reserved_slugs_are_refused() -> None:
    """A school at `admin.edirasx.com` would read as though we ran it."""
    for reserved in sorted(RESERVED_SLUGS)[:5]:
        with pytest.raises(ValidationFailed):
            validate_slug(reserved)


def test_a_duplicate_address_is_refused(school_a: TenantFixture) -> None:
    from app.core.errors import ConflictingState

    with pytest.raises(ConflictingState):
        provision_school(
            slug=school_a.tenant.slug,
            name="Impostor",
            owner_email="someone@example.test",
            owner_name="Someone",
            base_domain="edtechx.localhost",
        )


def test_provisioning_reuses_an_existing_account_without_touching_its_password(
    school_a: TenantFixture,
) -> None:
    """A teacher at two schools is one person, not two accounts."""
    second = provision_school(
        slug=f"second-{uuid.uuid4().hex[:8]}",
        name="Second School",
        owner_email=school_a.user.email,
        owner_name="Same Person",
        base_domain="edtechx.localhost",
        owner_password="a-different-passphrase-entirely",
    )
    assert second.owner_user_id == school_a.user_id

    from app.db.session import bind_tenant, get_session_factory

    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        user = session.get(User, school_a.user_id)
        assert user is not None
        # The original password still works; the second school could not
        # overwrite it.
        from app.core.security import verify_password

        assert verify_password(OWNER_PASSWORD, user.password_hash)
    finally:
        session.close()


def test_a_failed_provisioning_leaves_no_resolvable_school() -> None:
    """A school without roles or an owner must never answer traffic."""
    from app.db.session import bind_tenant, get_session_factory

    slug = f"broken-{uuid.uuid4().hex[:8]}"
    with pytest.raises(ValidationFailed):
        provision_school(
            slug=slug,
            name="",  # rejected before anything is written
            owner_email="x@example.test",
            owner_name="X",
            base_domain="edtechx.localhost",
        )
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        assert (
            session.execute(select(Tenant).where(Tenant.slug == slug)).scalar_one_or_none()
            is None
        )
    finally:
        session.close()


# --- sign-in --------------------------------------------------------------


def test_correct_credentials_sign_in(client: TestClient, school_a: TenantFixture) -> None:
    response = _sign_in(client, school_a, OWNER_PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "Bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["expires_in"] > 0


def test_the_issued_token_works(client: TestClient, school_a: TenantFixture) -> None:
    token = _sign_in(client, school_a, OWNER_PASSWORD).json()["access_token"]
    response = client.get(
        "/api/v1/me",
        headers={"Host": school_a.hostname, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["tenant_id"] == str(school_a.tenant_id)


def test_wrong_password_and_unknown_account_are_indistinguishable(
    client: TestClient, school_a: TenantFixture
) -> None:
    """The central anti-enumeration property."""
    wrong = _sign_in(client, school_a, "not-the-right-passphrase")
    unknown = _sign_in(
        client, school_a, OWNER_PASSWORD, email="nobody@nowhere.test"
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_a_token_issued_here_does_not_work_at_another_school(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    token = _sign_in(client, school_a, OWNER_PASSWORD).json()["access_token"]
    response = client.get(
        "/api/v1/me",
        headers={"Host": school_b.hostname, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "tenant_mismatch"


def test_a_member_of_one_school_cannot_sign_in_at_another(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """Correct credentials, wrong school — refused, and indistinguishably so.

    School B must not be able to discover that this person exists at School A.
    """
    response = client.post(
        "/api/v1/auth/sign-in",
        headers={"Host": school_b.hostname},
        json={"email": school_a.user.email, "password": OWNER_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json() == _sign_in(client, school_b, "wrong-passphrase-here").json()


def test_sign_in_is_refused_at_a_suspended_school(
    client: TestClient, school_a: TenantFixture
) -> None:
    suspend(school_a.tenant_id, reason="test")
    response = _sign_in(client, school_a, OWNER_PASSWORD)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "school_unavailable"


def test_repeated_failures_lock_the_account(
    client: TestClient, school_a: TenantFixture
) -> None:
    from app.core.config import get_settings

    threshold = get_settings().login_hard_fail_threshold
    for _ in range(threshold):
        assert _sign_in(client, school_a, "wrong-passphrase-here").status_code == 401

    # Locked — and now even the correct password is refused.
    response = _sign_in(client, school_a, OWNER_PASSWORD)
    assert response.status_code == 423
    assert response.json()["error"]["code"] == "account_locked"


# --- refresh rotation -----------------------------------------------------


def test_refresh_returns_a_new_pair(client: TestClient, school_a: TenantFixture) -> None:
    first = _sign_in(client, school_a, OWNER_PASSWORD).json()
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_a.hostname},
        json={"refresh_token": first["refresh_token"]},
    )
    assert response.status_code == 200
    second = response.json()
    assert second["refresh_token"] != first["refresh_token"]


def test_a_refresh_token_works_exactly_once(
    client: TestClient, school_a: TenantFixture
) -> None:
    first = _sign_in(client, school_a, OWNER_PASSWORD).json()
    assert (
        client.post(
            "/api/v1/auth/refresh",
            headers={"Host": school_a.hostname},
            json={"refresh_token": first["refresh_token"]},
        ).status_code
        == 200
    )
    replay = client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_a.hostname},
        json={"refresh_token": first["refresh_token"]},
    )
    assert replay.status_code == 401


def test_reuse_of_a_rotated_token_burns_the_whole_family(
    client: TestClient, school_a: TenantFixture
) -> None:
    """Theft detection.

    A replayed token means somebody holds a copy they should not. Revoking the
    entire family signs the legitimate holder out too — the correct trade when
    the alternative is leaving an attacker signed in.
    """
    first = _sign_in(client, school_a, OWNER_PASSWORD).json()
    second = client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_a.hostname},
        json={"refresh_token": first["refresh_token"]},
    ).json()

    # The attacker replays the original.
    replay = client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_a.hostname},
        json={"refresh_token": first["refresh_token"]},
    )
    assert replay.status_code == 401

    # The legitimate holder's newer token is now dead too.
    after = client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_a.hostname},
        json={"refresh_token": second["refresh_token"]},
    )
    assert after.status_code == 401


def test_a_refresh_token_is_not_usable_at_another_school(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    first = _sign_in(client, school_a, OWNER_PASSWORD).json()
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_b.hostname},
        json={"refresh_token": first["refresh_token"]},
    )
    assert response.status_code == 401


def test_refresh_tokens_are_stored_only_as_hashes(school_a: TenantFixture) -> None:
    session = school_a.session()
    try:
        stored = session.execute(select(UserSession.refresh_token_hash)).scalars().all()
        assert all(len(h) == 64 for h in stored) or not stored
    finally:
        session.close()


# --- sign-out -------------------------------------------------------------


def test_sign_out_revokes_the_session(client: TestClient, school_a: TenantFixture) -> None:
    tokens = _sign_in(client, school_a, OWNER_PASSWORD).json()
    headers = {
        "Host": school_a.hostname,
        "Authorization": f"Bearer {tokens['access_token']}",
    }
    assert client.post("/api/v1/auth/sign-out", headers=headers, json={}).status_code == 204

    # The refresh token no longer works.
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_a.hostname},
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert response.status_code == 401


def test_sign_out_everywhere_revokes_every_session(
    client: TestClient, school_a: TenantFixture
) -> None:
    first = _sign_in(client, school_a, OWNER_PASSWORD).json()
    second = _sign_in(client, school_a, OWNER_PASSWORD).json()

    headers = {
        "Host": school_a.hostname,
        "Authorization": f"Bearer {second['access_token']}",
    }
    assert (
        client.post(
            "/api/v1/auth/sign-out", headers=headers, json={"everywhere": True}
        ).status_code
        == 204
    )

    for tokens in (first, second):
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Host": school_a.hostname},
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 401


def test_sign_out_requires_authentication(
    client: TestClient, school_a: TenantFixture
) -> None:
    response = client.post(
        "/api/v1/auth/sign-out", headers={"Host": school_a.hostname}, json={}
    )
    assert response.status_code == 401


# --- audit ----------------------------------------------------------------


def test_a_sign_in_is_audited(client: TestClient, school_a: TenantFixture) -> None:
    from app.modules.audit.models import AuditAction, AuditEvent

    _sign_in(client, school_a, OWNER_PASSWORD)
    session = school_a.session()
    try:
        logins = (
            session.execute(
                select(AuditEvent).where(AuditEvent.action == AuditAction.login)
            )
            .scalars()
            .all()
        )
        assert logins, "A successful sign-in left no audit trail"
        assert all(e.tenant_id == school_a.tenant_id for e in logins)
    finally:
        session.close()


def test_a_failed_sign_in_is_recorded_as_a_security_event(
    client: TestClient, school_a: TenantFixture
) -> None:
    from app.db.session import bind_tenant, get_session_factory
    from app.modules.audit.models import SecurityEvent, SecurityEventKind

    _sign_in(client, school_a, "wrong-passphrase-here")
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        events = (
            session.execute(
                select(SecurityEvent).where(
                    SecurityEvent.tenant_id == school_a.tenant_id,
                    SecurityEvent.kind == SecurityEventKind.login_failed,
                )
            )
            .scalars()
            .all()
        )
        assert events
    finally:
        session.close()


# --- session liveness -----------------------------------------------------


def test_sign_out_invalidates_the_access_token_immediately(
    client: TestClient, school_a: TenantFixture
) -> None:
    """Signing out must sign you out *now*, not when the token expires.

    A revoked refresh family with a still-valid access token means "sign out"
    is a promise kept up to fifteen minutes late — which on a shared classroom
    machine is exactly the window that matters.
    """
    tokens = _sign_in(client, school_a, OWNER_PASSWORD).json()
    headers = {
        "Host": school_a.hostname,
        "Authorization": f"Bearer {tokens['access_token']}",
    }
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/sign-out", headers=headers, json={}).status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_sign_out_everywhere_invalidates_every_access_token(
    client: TestClient, school_a: TenantFixture
) -> None:
    first = _sign_in(client, school_a, OWNER_PASSWORD).json()
    second = _sign_in(client, school_a, OWNER_PASSWORD).json()

    def me(tokens: dict) -> int:
        return client.get(
            "/api/v1/me",
            headers={
                "Host": school_a.hostname,
                "Authorization": f"Bearer {tokens['access_token']}",
            },
        ).status_code

    assert me(first) == me(second) == 200
    client.post(
        "/api/v1/auth/sign-out",
        headers={
            "Host": school_a.hostname,
            "Authorization": f"Bearer {second['access_token']}",
        },
        json={"everywhere": True},
    )
    assert me(first) == 401, "another device kept a working access token"
    assert me(second) == 401


def test_a_rotated_session_invalidates_its_predecessors_access_token(
    client: TestClient, school_a: TenantFixture
) -> None:
    """Rotation marks the old session revoked, so its access token must die too."""
    first = _sign_in(client, school_a, OWNER_PASSWORD).json()
    old_headers = {
        "Host": school_a.hostname,
        "Authorization": f"Bearer {first['access_token']}",
    }
    assert client.get("/api/v1/me", headers=old_headers).status_code == 200
    client.post(
        "/api/v1/auth/refresh",
        headers={"Host": school_a.hostname},
        json={"refresh_token": first["refresh_token"]},
    )
    assert client.get("/api/v1/me", headers=old_headers).status_code == 401
