"""End-to-end request lifecycle: host resolution, auth, tenant agreement, authz.

These exercise the whole stack rather than the units beneath it, because the
interesting failures live in the seams — a dependency that resolves the tenant
but a handler that queries without it, or a token accepted on the wrong host.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import issue_access_token
from app.main import app
from app.tests.conftest import TenantFixture, requires_db

pytestmark = requires_db


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _auth(school: TenantFixture) -> dict[str, str]:
    """Sign in for real rather than hand-minting a token.

    A fabricated session id no longer authenticates — the session must exist
    and be live — so these tests now exercise the same path a client does.
    """
    from app.tests.conftest import OWNER_PASSWORD

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/sign-in",
            headers={"Host": school.hostname},
            json={"email": school.user.email, "password": OWNER_PASSWORD},
        )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "Host": school.hostname}


# --- public surface -------------------------------------------------------


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_security_headers_are_present(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["x-request-id"]


def test_unknown_host_is_refused(client: TestClient) -> None:
    response = client.get("/api/v1/context", headers={"Host": "nobody.edtechx.localhost"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_school"


def test_context_returns_the_school_for_its_host(
    client: TestClient, school_a: TenantFixture
) -> None:
    response = client.get("/api/v1/context", headers={"Host": school_a.hostname})
    assert response.status_code == 200
    body = response.json()
    assert body["school"]["id"] == str(school_a.tenant_id)
    assert body["school"]["slug"] == school_a.tenant.slug
    assert body["authenticated"] is False


# --- authentication -------------------------------------------------------


def test_me_requires_authentication(client: TestClient, school_a: TenantFixture) -> None:
    response = client.get("/api/v1/me", headers={"Host": school_a.hostname})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_me_returns_the_principal(client: TestClient, school_a: TenantFixture) -> None:
    response = client.get("/api/v1/me", headers=_auth(school_a))
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == str(school_a.tenant_id)
    assert body["membership_id"] == str(school_a.membership_id)
    assert "people.student.read" in body["permissions"]


def test_garbage_token_is_refused(client: TestClient, school_a: TenantFixture) -> None:
    response = client.get(
        "/api/v1/me",
        headers={"Host": school_a.hostname, "Authorization": "Bearer not-a-token"},
    )
    assert response.status_code == 401


def test_non_bearer_authorization_is_ignored(
    client: TestClient, school_a: TenantFixture
) -> None:
    response = client.get(
        "/api/v1/me",
        headers={"Host": school_a.hostname, "Authorization": "Basic dXNlcjpwdw=="},
    )
    assert response.status_code == 401


# --- the tenant agreement check ------------------------------------------


def test_a_token_from_another_school_is_refused_on_this_host(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """Critical journey 12, at the HTTP boundary.

    School A's token is genuinely valid. Presented against School B's hostname
    it must be refused, because a token is authority within one school only.
    """
    token, _ = issue_access_token(
        user_id=school_a.user_id,
        membership_id=school_a.membership_id,
        tenant_id=school_a.tenant_id,
        session_id=uuid.uuid4(),
    )
    response = client.get(
        "/api/v1/me",
        headers={"Host": school_b.hostname, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "tenant_mismatch"


def test_a_membership_from_another_school_is_not_loadable(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """A token naming B's host and B's tenant, but A's membership id.

    The membership lookup runs inside B's tenant context, so A's membership is
    invisible and the request fails closed.
    """
    token, _ = issue_access_token(
        user_id=school_a.user_id,
        membership_id=school_a.membership_id,
        tenant_id=school_b.tenant_id,
        session_id=uuid.uuid4(),
    )
    response = client.get(
        "/api/v1/me",
        headers={"Host": school_b.hostname, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_tenant_cannot_be_overridden_by_a_header_or_query_parameter(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """Client-supplied tenant hints must be inert."""
    headers = _auth(school_a) | {
        "X-Tenant-Id": str(school_b.tenant_id),
        "X-Tenant": school_b.tenant.slug,
    }
    response = client.get(f"/api/v1/me?tenant_id={school_b.tenant_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["tenant_id"] == str(school_a.tenant_id)


# --- authorization --------------------------------------------------------


def test_guarded_route_allows_a_principal_holding_the_permission(
    client: TestClient, school_a: TenantFixture
) -> None:
    response = client.get("/api/v1/students", headers=_auth(school_a))
    assert response.status_code == 200


def test_guarded_route_refuses_an_anonymous_request(
    client: TestClient, school_a: TenantFixture
) -> None:
    response = client.get("/api/v1/students", headers={"Host": school_a.hostname})
    assert response.status_code == 401


def test_guarded_route_refuses_a_principal_without_the_permission(
    client: TestClient, school_a: TenantFixture, db
) -> None:
    """Stripping the grant must close the route immediately."""
    from app.modules.authz.models import MembershipRole
    from app.tests.conftest import session_for

    session = session_for(school_a.tenant_id)
    try:
        grant = (
            session.query(MembershipRole)
            .filter(MembershipRole.membership_id == school_a.membership_id)
            .one()
        )
        session.delete(grant)
        session.commit()
    finally:
        session.close()

    response = client.get("/api/v1/students", headers=_auth(school_a))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


# --- error hygiene --------------------------------------------------------


def test_errors_do_not_leak_internals(client: TestClient) -> None:
    response = client.get("/api/v1/context", headers={"Host": "nobody.edtechx.localhost"})
    body = response.text.lower()
    for leak in ("traceback", "sqlalchemy", "psycopg", "select ", "tenant_id ="):
        assert leak not in body


def test_oversized_body_is_rejected_at_the_edge(
    client: TestClient, school_a: TenantFixture
) -> None:
    response = client.post(
        "/api/v1/me",
        headers=_auth(school_a) | {"Content-Length": str(50 * 1024 * 1024)},
        content=b"x" * 1024,
    )
    assert response.status_code == 413


# --- forged session ids ---------------------------------------------------


def test_a_token_naming_a_session_that_does_not_exist_is_refused(
    client: TestClient, school_a: TenantFixture
) -> None:
    """A correctly-signed token is not enough; its session must exist.

    Without this, anyone able to mint a token — a leaked signing key, a
    developer script — could authenticate indefinitely against a session the
    product has no record of, and no sign-out could reach it.
    """
    token, _ = issue_access_token(
        user_id=school_a.user_id,
        membership_id=school_a.membership_id,
        tenant_id=school_a.tenant_id,
        session_id=uuid.uuid4(),
    )
    response = client.get(
        "/api/v1/me",
        headers={"Host": school_a.hostname, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
