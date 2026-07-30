"""Single-use, expiring tokens for password-reset and email-verify links.

Same "store the hash, not the secret" shape as refresh-token revocation
(`app/core/token_denylist.py`): the raw token is only ever held in memory
long enough to email it (or, in dev, log it) — the database and anyone with
read access to it only ever see a SHA-256 hash, which can't be turned back
into a usable link.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models.user import AuthToken, AuthTokenPurpose

PASSWORD_RESET_TTL = timedelta(hours=1)
EMAIL_VERIFY_TTL = timedelta(hours=24)


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def issue_token(db: Session, user_id, purpose: AuthTokenPurpose, ttl: timedelta) -> str:
    raw_token = secrets.token_urlsafe(32)
    db.add(
        AuthToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=_hash(raw_token),
            expires_at=datetime.now(timezone.utc) + ttl,
        )
    )
    db.commit()
    return raw_token


def consume_token(db: Session, raw_token: str, purpose: AuthTokenPurpose) -> AuthToken | None:
    """Looks up and marks a token used in one step. Returns None for a
    missing/wrong-purpose/expired/already-used token — callers only need to
    distinguish "valid" from "not", not which specific reason it failed,
    since telling those apart to the caller would leak whether a token
    existed at all."""
    record = db.query(AuthToken).filter(AuthToken.token_hash == _hash(raw_token)).first()
    if record is None or record.purpose != purpose or record.used_at is not None:
        return None
    if record.expires_at < datetime.now(timezone.utc):
        return None

    record.used_at = datetime.now(timezone.utc)
    db.commit()
    return record
