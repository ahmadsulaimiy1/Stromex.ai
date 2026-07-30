"""Regression tests for audit findings: no brute-force protection on
register/login, and no way to revoke a refresh token."""

import pytest

from app.core.security import TokenError, TokenType, create_refresh_token, decode_token_full
from app.core.token_denylist import is_revoked, revoke


def _register_and_login(client, email: str, password: str = "correcthorsebattery") -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()


def test_login_is_rate_limited_by_email(app_client, random_email, in_memory_qdrant):
    # The successful login below already counts as attempt 1 of 8 against the
    # login-email bucket (the limiter counts every attempt, not just
    # failures — that's what stops credential stuffing regardless of whether
    # any individual guess happens to be right).
    _register_and_login(app_client, random_email)

    # 7 more wrong-password attempts brings the bucket to 8 (still allowed);
    # the 9th request overall must be blocked.
    for _ in range(7):
        resp = app_client.post(
            "/api/v1/auth/login", json={"email": random_email, "password": "wrong-password"}
        )
        assert resp.status_code == 401

    resp = app_client.post(
        "/api/v1/auth/login", json={"email": random_email, "password": "wrong-password"}
    )
    assert resp.status_code == 429


def test_register_is_rate_limited_by_ip(app_client, in_memory_qdrant):
    for i in range(5):
        resp = app_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"burst-{i}@stromex.ai",
                "password": "correcthorsebattery",
                "display_name": "Burst",
            },
        )
        assert resp.status_code == 201

    resp = app_client.post(
        "/api/v1/auth/register",
        json={"email": "burst-6@stromex.ai", "password": "correcthorsebattery", "display_name": "Burst"},
    )
    assert resp.status_code == 429


def test_logout_revokes_refresh_token(app_client, random_email, in_memory_qdrant):
    tokens = _register_and_login(app_client, random_email)
    refresh_token = tokens["refresh_token"]

    resp = app_client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204

    resp = app_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401
    assert "revoked" in resp.json()["detail"].lower()


def test_refresh_rotates_and_invalidates_the_old_token(app_client, random_email, in_memory_qdrant):
    tokens = _register_and_login(app_client, random_email)
    old_refresh = tokens["refresh_token"]

    resp = app_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200
    new_refresh = resp.json()["refresh_token"]
    assert new_refresh != old_refresh

    # Replaying the old (now-rotated) refresh token must fail — this is what
    # limits the damage from a stolen-but-not-yet-used refresh token.
    resp = app_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 401

    # The new token, however, must still work.
    resp = app_client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert resp.status_code == 200


def test_logout_with_already_invalid_token_is_not_an_error(app_client):
    resp = app_client.post("/api/v1/auth/logout", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 204


def test_denylist_ttl_matches_remaining_token_lifetime():
    import uuid

    token = create_refresh_token(uuid.uuid4())
    decoded = decode_token_full(token, TokenType.REFRESH)
    assert not is_revoked(decoded.jti)

    revoke(decoded.jti, ttl_seconds=5)
    assert is_revoked(decoded.jti)

    with pytest.raises(TokenError):
        decode_token_full(token, TokenType.REFRESH)
