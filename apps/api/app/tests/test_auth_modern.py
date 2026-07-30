"""Tests for the modern-mobile-auth feature: guest mode, password reset,
email verification, logout-all-devices, account deletion, and the Google
OAuth endpoints' behavior when Google Sign-In isn't (yet) configured."""
from urllib.parse import parse_qs, urlparse

import pytest

from app.core import email as email_module


@pytest.fixture()
def sent_emails(monkeypatch):
    """Captures every outbound email instead of actually sending (or, in
    dev mode, merely logging) it — a test needs the real token embedded in
    the link, not just proof that *an* email happened."""
    messages = []

    def _fake_send(to, subject, body):
        messages.append({"to": to, "subject": subject, "body": body})

    monkeypatch.setattr(email_module, "send_email", _fake_send)
    return messages


def _token_from_link(body: str) -> str:
    for word in body.split():
        if word.startswith("http"):
            return parse_qs(urlparse(word).query)["token"][0]
    raise AssertionError(f"no link found in email body: {body!r}")


def _register(client, email, password="correcthorsebattery", display_name="Test User"):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert resp.status_code == 201
    return resp.json()


def _login(client, email, password="correcthorsebattery"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()


# --- Guest mode ---------------------------------------------------------


def test_guest_account_is_immediately_usable(app_client, in_memory_qdrant):
    resp = app_client.post("/api/v1/auth/guest")
    assert resp.status_code == 201
    tokens = resp.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = app_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    body = me.json()
    assert body["is_guest"] is True
    assert body["is_verified"] is True
    assert body["email"].startswith("guest-")


def test_guest_can_upgrade_to_full_account(app_client, in_memory_qdrant, random_email, sent_emails):
    tokens = app_client.post("/api/v1/auth/guest").json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = app_client.post(
        "/api/v1/auth/guest/upgrade",
        json={"email": random_email, "password": "correcthorsebattery", "display_name": "Upgraded"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_guest"] is False
    assert body["email"] == random_email
    assert body["is_verified"] is False  # a real email now exists and needs verifying
    assert any(m["to"] == random_email for m in sent_emails)

    # The now-upgraded account logs in like any normal account.
    login_resp = app_client.post(
        "/api/v1/auth/login", json={"email": random_email, "password": "correcthorsebattery"}
    )
    assert login_resp.status_code == 200


def test_non_guest_cannot_use_upgrade_endpoint(app_client, random_email, in_memory_qdrant):
    _register(app_client, random_email)
    tokens = _login(app_client, random_email)
    resp = app_client.post(
        "/api/v1/auth/guest/upgrade",
        json={"email": "someone-else@stromex.ai", "password": "correcthorsebattery", "display_name": "X"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 400


# --- Password reset ------------------------------------------------------


def test_password_reset_full_flow(app_client, random_email, in_memory_qdrant, sent_emails):
    _register(app_client, random_email, password="original-password")

    resp = app_client.post("/api/v1/auth/password-reset/request", json={"email": random_email})
    assert resp.status_code == 202
    token = _token_from_link(sent_emails[-1]["body"])

    confirm = app_client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "brand-new-password"},
    )
    assert confirm.status_code == 204

    # Old password no longer works, new one does.
    assert app_client.post(
        "/api/v1/auth/login", json={"email": random_email, "password": "original-password"}
    ).status_code == 401
    assert app_client.post(
        "/api/v1/auth/login", json={"email": random_email, "password": "brand-new-password"}
    ).status_code == 200


def test_password_reset_token_is_single_use(app_client, random_email, in_memory_qdrant, sent_emails):
    _register(app_client, random_email)
    app_client.post("/api/v1/auth/password-reset/request", json={"email": random_email})
    token = _token_from_link(sent_emails[-1]["body"])

    first = app_client.post(
        "/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": "second-password"}
    )
    assert first.status_code == 204

    replay = app_client.post(
        "/api/v1/auth/password-reset/confirm", json={"token": token, "new_password": "third-password"}
    )
    assert replay.status_code == 400


def test_password_reset_request_for_unknown_email_still_returns_202(app_client, in_memory_qdrant):
    # Prevents account enumeration: the response can't reveal whether the
    # address is registered.
    resp = app_client.post(
        "/api/v1/auth/password-reset/request", json={"email": "nobody-at-all@stromex.ai"}
    )
    assert resp.status_code == 202


def test_password_reset_invalidates_existing_sessions(app_client, random_email, in_memory_qdrant, sent_emails):
    tokens = _register_and_login(app_client, random_email)
    access_token = tokens["access_token"]

    app_client.post("/api/v1/auth/password-reset/request", json={"email": random_email})
    reset_token = _token_from_link(sent_emails[-1]["body"])
    app_client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "another-new-password"},
    )

    resp = app_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 401


def _register_and_login(client, email, password="correcthorsebattery"):
    _register(client, email, password)
    return _login(client, email, password)


# --- Email verification ---------------------------------------------------


def test_new_account_is_unverified_until_confirmed(app_client, random_email, in_memory_qdrant, sent_emails):
    _register(app_client, random_email)
    tokens = _login(app_client, random_email)
    me = app_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    ).json()
    assert me["is_verified"] is False

    token = _token_from_link(sent_emails[-1]["body"])
    confirm = app_client.post("/api/v1/auth/email/verify/confirm", json={"token": token})
    assert confirm.status_code == 204

    me_after = app_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    ).json()
    assert me_after["is_verified"] is True


def test_email_verify_token_is_single_use(app_client, random_email, in_memory_qdrant, sent_emails):
    _register(app_client, random_email)
    token = _token_from_link(sent_emails[-1]["body"])

    assert app_client.post("/api/v1/auth/email/verify/confirm", json={"token": token}).status_code == 204
    assert app_client.post("/api/v1/auth/email/verify/confirm", json={"token": token}).status_code == 400


def test_invalid_verify_token_is_rejected(app_client, in_memory_qdrant):
    resp = app_client.post("/api/v1/auth/email/verify/confirm", json={"token": "not-a-real-token"})
    assert resp.status_code == 400


# --- Logout-all-devices ---------------------------------------------------


def test_logout_all_invalidates_existing_access_and_refresh_tokens(
    app_client, random_email, in_memory_qdrant
):
    tokens = _register_and_login(app_client, random_email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = app_client.post("/api/v1/auth/logout-all", headers=headers)
    assert resp.status_code == 204

    # The access token used to issue the logout-all call is itself now stale.
    assert app_client.get("/api/v1/auth/me", headers=headers).status_code == 401
    # The refresh token from the same session is stale too.
    assert app_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    ).status_code == 401

    # A fresh login (issuing tokens under the new version) works normally.
    new_tokens = _login(app_client, random_email)
    assert app_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
    ).status_code == 200


# --- Account deletion ------------------------------------------------------


def test_guest_can_delete_own_account_without_a_password(app_client, in_memory_qdrant):
    tokens = app_client.post("/api/v1/auth/guest").json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = app_client.request("DELETE", "/api/v1/auth/me", json={}, headers=headers)
    assert resp.status_code == 204
    assert app_client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_password_account_deletion_requires_correct_password(app_client, random_email, in_memory_qdrant):
    tokens = _register_and_login(app_client, random_email, password="the-real-password")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    wrong = app_client.request(
        "DELETE", "/api/v1/auth/me", json={"password": "wrong-password"}, headers=headers
    )
    assert wrong.status_code == 401

    missing = app_client.request("DELETE", "/api/v1/auth/me", json={}, headers=headers)
    assert missing.status_code == 401

    correct = app_client.request(
        "DELETE", "/api/v1/auth/me", json={"password": "the-real-password"}, headers=headers
    )
    assert correct.status_code == 204
    assert app_client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_deleted_account_email_can_be_reregistered(app_client, random_email, in_memory_qdrant):
    tokens = _register_and_login(app_client, random_email, password="the-real-password")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    app_client.request("DELETE", "/api/v1/auth/me", json={"password": "the-real-password"}, headers=headers)

    resp = app_client.post(
        "/api/v1/auth/register",
        json={"email": random_email, "password": "a-different-password", "display_name": "Reborn"},
    )
    assert resp.status_code == 201


# --- Google OAuth: behavior with no Client ID configured ------------------


def test_google_authorize_returns_503_when_not_configured(app_client):
    # The test environment (see conftest.py) never sets GOOGLE_CLIENT_ID —
    # this is exactly the "nobody's created Google Cloud credentials yet"
    # state, and it must fail loudly (503) rather than redirect into a
    # client id that doesn't exist.
    resp = app_client.get("/api/v1/auth/google/authorize", follow_redirects=False)
    assert resp.status_code == 503


def test_google_callback_rejects_unknown_state(app_client):
    resp = app_client.get(
        "/api/v1/auth/google/callback",
        params={"code": "irrelevant", "state": "not-a-real-state:web"},
        follow_redirects=False,
    )
    assert resp.status_code == 400
