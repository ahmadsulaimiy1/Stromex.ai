"""Password hashing, token issuance, and the production configuration guard."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security
from app.core.config import INSECURE_SECRET, Settings, get_settings

# --- passwords ------------------------------------------------------------


def test_hash_is_argon2id_and_verifies() -> None:
    hashed = security.hash_password("a-perfectly-fine-passphrase")
    assert hashed.startswith("$argon2id$")
    assert security.verify_password("a-perfectly-fine-passphrase", hashed)


def test_hashes_are_salted_and_therefore_unequal() -> None:
    a = security.hash_password("a-perfectly-fine-passphrase")
    b = security.hash_password("a-perfectly-fine-passphrase")
    assert a != b


def test_wrong_password_is_rejected() -> None:
    hashed = security.hash_password("a-perfectly-fine-passphrase")
    assert not security.verify_password("a-perfectly-wrong-passphrase", hashed)


def test_short_password_is_refused() -> None:
    with pytest.raises(security.WeakPassword):
        security.hash_password("short")


def test_absurdly_long_password_is_refused() -> None:
    """Unbounded input to a memory-hard hash is a denial-of-service lever."""
    with pytest.raises(security.WeakPassword):
        security.hash_password("x" * 2000)


def test_verification_against_a_missing_hash_returns_false() -> None:
    """A user without a password must not authenticate, and must not error.

    Erroring here would leak account existence through the response shape.
    """
    assert security.verify_password("any-password-at-all", None) is False
    assert security.verify_password("any-password-at-all", "") is False


def test_bcrypt_hashes_are_flagged_for_upgrade() -> None:
    legacy = "$2b$12$abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQR"
    assert security.needs_rehash(legacy) is True


# --- access tokens --------------------------------------------------------


def _issue() -> tuple[str, security.AccessTokenClaims]:
    return security.issue_access_token(
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
    )


def test_access_token_round_trips() -> None:
    token, claims = _issue()
    decoded = security.decode_access_token(token)
    assert decoded.user_id == claims.user_id
    assert decoded.tenant_id == claims.tenant_id
    assert decoded.membership_id == claims.membership_id
    assert decoded.jti == claims.jti


def test_token_carries_the_tenant_claim() -> None:
    """Without `tid`, the host/token agreement check has nothing to compare."""
    token, claims = _issue()
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["tid"] == str(claims.tenant_id)
    assert payload["mid"] == str(claims.membership_id)


def test_tampered_token_is_rejected() -> None:
    token, _ = _issue()
    head, body, signature = token.split(".")
    tampered = f"{head}.{body}.{signature[:-4]}AAAA"
    with pytest.raises(security.InvalidToken):
        security.decode_access_token(tampered)


def test_unsigned_token_is_rejected() -> None:
    """The `alg: none` confusion attack must not work."""
    forged = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "mid": str(uuid.uuid4()),
            "tid": str(uuid.uuid4()),
            "sid": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "typ": "access",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        key="",
        algorithm="none",
    )
    with pytest.raises(security.InvalidToken):
        security.decode_access_token(forged)


def test_expired_token_is_rejected() -> None:
    settings = get_settings()
    past = datetime.now(UTC) - timedelta(hours=2)
    expired = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "mid": str(uuid.uuid4()),
            "tid": str(uuid.uuid4()),
            "sid": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "typ": "access",
            "iat": int(past.timestamp()),
            "exp": int((past + timedelta(minutes=15)).timestamp()),
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(security.InvalidToken):
        security.decode_access_token(expired)


def test_a_refresh_token_cannot_be_used_as_an_access_token() -> None:
    settings = get_settings()
    now = datetime.now(UTC)
    refresh_shaped = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "mid": str(uuid.uuid4()),
            "tid": str(uuid.uuid4()),
            "sid": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "typ": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp()),
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(security.InvalidToken, match="not an access token"):
        security.decode_access_token(refresh_shaped)


# --- refresh tokens -------------------------------------------------------


def test_refresh_tokens_are_unpredictable() -> None:
    tokens = {security.generate_refresh_token() for _ in range(200)}
    assert len(tokens) == 200
    assert all(len(t) >= 43 for t in tokens)


def test_refresh_token_is_stored_only_as_a_keyed_hash() -> None:
    token = security.generate_refresh_token()
    stored = security.hash_refresh_token(token)
    assert token not in stored
    assert security.refresh_token_matches(token, stored)
    assert not security.refresh_token_matches(security.generate_refresh_token(), stored)


# --- elevation ------------------------------------------------------------


def test_recent_authentication_counts_as_elevated() -> None:
    assert security.is_elevated(datetime.now(UTC))


def test_stale_authentication_is_not_elevated() -> None:
    """High-risk actions must not ride on a session authenticated hours ago."""
    stale = datetime.now(UTC) - timedelta(hours=3)
    assert not security.is_elevated(stale)


# --- production configuration guard ---------------------------------------


def _prod(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "environment": "production",
        "secret_key": "a" * 48,
        "debug": False,
        "database_url": "postgresql+psycopg://app:pw@db.internal:5432/edtechx",
        "migration_database_url": "postgresql+psycopg://mig:pw@db.internal:5432/edtechx",
        "cors_origins": ["https://portal.example.edu"],
    }
    base.update(overrides)
    return base


def test_production_accepts_a_sound_configuration() -> None:
    assert Settings(**_prod()).is_production


def test_production_refuses_the_default_secret() -> None:
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings(**_prod(secret_key=INSECURE_SECRET))


def test_production_refuses_debug_mode() -> None:
    with pytest.raises(RuntimeError, match="DEBUG"):
        Settings(**_prod(debug=True))


def test_production_refuses_a_shared_migration_role() -> None:
    """If the request path runs as the schema owner, FORCE RLS is bypassed.

    This is the single misconfiguration that would silently void tenant
    isolation while every test still passed, so it is refused at boot.
    """
    shared = "postgresql+psycopg://mig:pw@db.internal:5432/edtechx"
    with pytest.raises(RuntimeError, match="must not run as the schema owner"):
        Settings(**_prod(database_url=shared, migration_database_url=shared))


def test_production_refuses_plaintext_cors_origins() -> None:
    with pytest.raises(RuntimeError, match="https"):
        Settings(**_prod(cors_origins=["http://portal.example.edu"]))
