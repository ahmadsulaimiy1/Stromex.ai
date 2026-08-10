"""Multi-factor authentication, attacked.

The properties worth testing are the ones a working demo would not reveal: that
a code cannot be used twice, that a challenge from one school cannot complete a
sign-in at another, that a recovery code is spent when used, and that the
password alone stops being sufficient the moment MFA is on.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.core import crypto
from app.core.security import decode_mfa_challenge, issue_access_token
from app.main import app
from app.modules.identity import totp
from app.tests.conftest import OWNER_PASSWORD, TenantFixture, requires_db

pytestmark = requires_db


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _sign_in(client: TestClient, school: TenantFixture, password: str = OWNER_PASSWORD):
    return client.post(
        "/api/v1/auth/sign-in",
        headers={"Host": school.hostname},
        json={"email": school.user.email, "password": password},
    )


def _auth(client: TestClient, school: TenantFixture) -> dict[str, str]:
    token = _sign_in(client, school).json()["access_token"]
    return {"Host": school.hostname, "Authorization": f"Bearer {token}"}


def _fresh_code(school: TenantFixture, secret: str) -> str:
    """A code from a counter this account has not already spent.

    Activation consumes the window it was confirmed in, so the code an
    authenticator is *currently* showing is legitimately refused for the rest
    of that step. This is the intended behaviour of a one-time password and is
    what every mainstream implementation does; the test simply has to move to
    the next window rather than pretend replay is allowed.
    """
    from app.db.session import bind_tenant, get_session_factory
    from app.modules.identity.models import User

    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        user = session.get(User, school.user_id)
        last = user.mfa_last_counter if user else None
    finally:
        session.close()

    counter = totp.counter_at()
    if last is not None and counter <= last:
        counter = last + 1
    return totp.code_for(secret, counter)


def _enrol(client: TestClient, school: TenantFixture) -> tuple[str, list[str]]:
    """Enrol and activate, returning the secret and recovery codes."""
    headers = _auth(client, school)
    enrolment = client.post("/api/v1/auth/mfa/enrol", headers=headers)
    assert enrolment.status_code == 200, enrolment.text
    body = enrolment.json()
    secret = body["secret"]

    activated = client.post(
        "/api/v1/auth/mfa/activate",
        headers=headers,
        json={"code": totp.code_for(secret, totp.counter_at())},
    )
    assert activated.status_code == 204, activated.text
    return secret, body["recovery_codes"]


# --- the algorithm --------------------------------------------------------


def test_codes_match_rfc_6238_test_vectors() -> None:
    """Anchored to the RFC so the implementation cannot drift silently."""
    import base64

    secret = base64.b32encode(b"12345678901234567890").decode()
    assert totp.code_for(secret, 1) == "287082"
    assert totp.code_for(secret, 37037036) == "081804"


def test_a_code_is_accepted_within_the_drift_window() -> None:
    secret = totp.generate_secret()
    now = time.time()
    for offset in (-totp.STEP_SECONDS, 0, totp.STEP_SECONDS):
        code = totp.code_for(secret, totp.counter_at(now + offset))
        assert totp.verify(secret, code, moment=now), f"offset {offset} rejected"


def test_a_code_outside_the_window_is_refused() -> None:
    secret = totp.generate_secret()
    now = time.time()
    stale = totp.code_for(secret, totp.counter_at(now) - 5)
    assert not totp.verify(secret, stale, moment=now)


def test_a_used_counter_cannot_be_replayed() -> None:
    """The property that makes it a *one-time* password."""
    secret = totp.generate_secret()
    counter = totp.counter_at()
    code = totp.code_for(secret, counter)

    first = totp.verify(secret, code)
    assert first and first.counter == counter
    assert not totp.verify(secret, code, last_used_counter=first.counter)


def test_malformed_codes_are_refused_without_computing() -> None:
    secret = totp.generate_secret()
    for bad in ("", "12345", "1234567", "abcdef", "12 34 56 78"):
        assert not totp.verify(secret, bad)


# --- secret storage -------------------------------------------------------


def test_the_secret_is_encrypted_at_rest(client: TestClient, school_a: TenantFixture) -> None:
    from app.db.session import bind_tenant, get_session_factory
    from app.modules.identity.models import User

    secret, _ = _enrol(client, school_a)
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        user = session.get(User, school_a.user_id)
        assert user is not None and user.mfa_secret_encrypted
        stored = user.mfa_secret_encrypted
    finally:
        session.close()

    assert secret not in stored, "the TOTP secret is recoverable from the column"
    assert crypto.decrypt(stored, purpose=crypto.MFA_SECRET) == secret


def test_a_ciphertext_cannot_be_moved_between_purposes() -> None:
    """Purpose binding: a secret lifted into another column must not decrypt."""
    sealed = crypto.encrypt("sensitive", purpose=crypto.MFA_SECRET)
    with pytest.raises(crypto.DecryptionFailed):
        crypto.decrypt(sealed, purpose=crypto.AI_CREDENTIAL)


def test_tampered_ciphertext_is_rejected_rather_than_mangled() -> None:
    sealed = crypto.encrypt("sensitive", purpose=crypto.MFA_SECRET)
    tampered = sealed[:-4] + ("AAAA" if not sealed.endswith("AAAA") else "BBBB")
    with pytest.raises(crypto.DecryptionFailed):
        crypto.decrypt(tampered, purpose=crypto.MFA_SECRET)


# --- the sign-in flow -----------------------------------------------------


def test_password_alone_stops_being_enough(client: TestClient, school_a: TenantFixture) -> None:
    _enrol(client, school_a)
    response = _sign_in(client, school_a)
    assert response.status_code == 200
    body = response.json()
    assert body.get("mfa_required") is True
    assert "access_token" not in body, "tokens were issued before the second factor"
    assert body["challenge"]


def test_a_challenge_plus_a_code_completes_the_sign_in(
    client: TestClient, school_a: TenantFixture
) -> None:
    secret, _ = _enrol(client, school_a)
    challenge = _sign_in(client, school_a).json()["challenge"]

    response = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school_a.hostname},
        json={"challenge": challenge, "code": _fresh_code(school_a, secret)},
    )
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]


def test_a_wrong_code_does_not_complete_the_sign_in(
    client: TestClient, school_a: TenantFixture
) -> None:
    _enrol(client, school_a)
    challenge = _sign_in(client, school_a).json()["challenge"]
    response = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school_a.hostname},
        json={"challenge": challenge, "code": "000000"},
    )
    assert response.status_code == 401


def test_a_code_cannot_be_replayed_through_the_api(
    client: TestClient, school_a: TenantFixture
) -> None:
    """Shoulder-surfing resistance, end to end."""
    secret, _ = _enrol(client, school_a)
    code = _fresh_code(school_a, secret)

    first = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school_a.hostname},
        json={"challenge": _sign_in(client, school_a).json()["challenge"], "code": code},
    )
    assert first.status_code == 200

    replay = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school_a.hostname},
        json={"challenge": _sign_in(client, school_a).json()["challenge"], "code": code},
    )
    assert replay.status_code == 401, "a code was accepted twice"


def test_an_access_token_cannot_be_used_as_a_challenge(
    client: TestClient, school_a: TenantFixture
) -> None:
    """Otherwise the second factor could be satisfied by the first."""
    secret, _ = _enrol(client, school_a)
    token, _claims = issue_access_token(
        user_id=school_a.user_id,
        membership_id=school_a.membership_id,
        tenant_id=school_a.tenant_id,
        session_id=school_a.membership_id,
    )
    response = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school_a.hostname},
        json={"challenge": token, "code": totp.code_for(secret, totp.counter_at())},
    )
    assert response.status_code == 401


def test_a_challenge_from_one_school_cannot_complete_at_another(
    client: TestClient, school_a: TenantFixture, school_b: TenantFixture
) -> None:
    """Journey 12, applied to the half-finished authentication state."""
    secret, _ = _enrol(client, school_a)
    challenge = _sign_in(client, school_a).json()["challenge"]
    assert decode_mfa_challenge(challenge).tenant_id == school_a.tenant_id

    response = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school_b.hostname},
        json={"challenge": challenge, "code": totp.code_for(secret, totp.counter_at())},
    )
    assert response.status_code == 401


# --- recovery codes -------------------------------------------------------


def test_a_recovery_code_completes_a_sign_in(
    client: TestClient, school_a: TenantFixture
) -> None:
    _secret, codes = _enrol(client, school_a)
    response = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school_a.hostname},
        json={
            "challenge": _sign_in(client, school_a).json()["challenge"],
            "code": codes[0],
        },
    )
    assert response.status_code == 200, response.text


def test_a_recovery_code_is_spent_when_used(
    client: TestClient, school_a: TenantFixture
) -> None:
    """A recovery code that survived its use would permanently bypass MFA."""
    _secret, codes = _enrol(client, school_a)
    for _ in range(2):
        response = client.post(
            "/api/v1/auth/mfa/verify",
            headers={"Host": school_a.hostname},
            json={
                "challenge": _sign_in(client, school_a).json()["challenge"],
                "code": codes[0],
            },
        )
    assert response.status_code == 401, "a recovery code was accepted twice"

    # A different code still works, so only the spent one was consumed.
    still_valid = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school_a.hostname},
        json={
            "challenge": _sign_in(client, school_a).json()["challenge"],
            "code": codes[1],
        },
    )
    assert still_valid.status_code == 200


def test_recovery_codes_are_stored_hashed(client: TestClient, school_a: TenantFixture) -> None:
    from app.db.session import bind_tenant, get_session_factory
    from app.modules.identity.models import User

    _secret, codes = _enrol(client, school_a)
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        user = session.get(User, school_a.user_id)
        stored = user.mfa_recovery_hashes or []
    finally:
        session.close()

    assert len(stored) == len(codes)
    assert all(code not in "".join(stored) for code in codes)
    assert all(h.startswith("$argon2id$") for h in stored)


# --- lifecycle ------------------------------------------------------------


def test_enrolment_cannot_be_started_twice(
    client: TestClient, school_a: TenantFixture
) -> None:
    """Otherwise a second enrolment would silently orphan the first device."""
    _enrol(client, school_a)
    response = client.post("/api/v1/auth/mfa/enrol", headers=_auth_after_mfa(client, school_a))
    assert response.status_code == 409


def _auth_after_mfa(client: TestClient, school: TenantFixture) -> dict[str, str]:
    """Sign in fully through the second factor and return usable headers."""
    from app.db.session import bind_tenant, get_session_factory
    from app.modules.identity.models import User

    challenge = _sign_in(client, school).json()["challenge"]
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        user = session.get(User, school.user_id)
        secret = crypto.decrypt(user.mfa_secret_encrypted, purpose=crypto.MFA_SECRET)
    finally:
        session.close()

    response = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Host": school.hostname},
        json={"challenge": challenge, "code": _fresh_code(school, secret)},
    )
    assert response.status_code == 200, response.text
    return {
        "Host": school.hostname,
        "Authorization": f"Bearer {response.json()['access_token']}",
    }


def test_removing_the_second_factor_restores_password_only_sign_in(
    client: TestClient, school_a: TenantFixture
) -> None:
    _enrol(client, school_a)
    headers = _auth_after_mfa(client, school_a)

    removed = client.delete("/api/v1/auth/mfa", headers=headers)
    assert removed.status_code == 204, removed.text

    response = _sign_in(client, school_a)
    assert response.status_code == 200
    assert response.json().get("access_token"), "MFA removal did not take effect"


def test_activating_with_a_wrong_code_leaves_mfa_off(
    client: TestClient, school_a: TenantFixture
) -> None:
    """Enrolment is two-step precisely so a mis-scanned secret cannot lock anyone out."""
    headers = _auth(client, school_a)
    assert client.post("/api/v1/auth/mfa/enrol", headers=headers).status_code == 200

    rejected = client.post(
        "/api/v1/auth/mfa/activate", headers=headers, json={"code": "000000"}
    )
    assert rejected.status_code == 422

    response = _sign_in(client, school_a)
    assert response.json().get("access_token"), "a failed activation still enabled MFA"
