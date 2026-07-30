"""Regression tests for security headers and the request body size cap."""


def test_security_headers_present(app_client):
    resp = app_client.get("/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" in resp.headers


def test_oversized_body_is_rejected(app_client):
    huge_password = "x" * (3 * 1024 * 1024)  # 3MB, over the 2MB cap
    resp = app_client.post(
        "/api/v1/auth/register",
        json={"email": "big@stromex.ai", "password": huge_password, "display_name": "Big"},
    )
    assert resp.status_code == 413


def test_normal_sized_body_is_not_rejected(app_client, random_email, in_memory_qdrant):
    resp = app_client.post(
        "/api/v1/auth/register",
        json={"email": random_email, "password": "correcthorsebattery", "display_name": "Normal"},
    )
    assert resp.status_code == 201
