"""Multi-factor enrolment and verification.

Enrolment is two steps on purpose. A single "turn on MFA" call that trusts the
secret was stored correctly locks people out of their own school when the
authenticator did not actually scan it. Confirming a code before enabling means
the factor is proven to work before it becomes required.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from sqlalchemy.orm import Session

from app.core import crypto
from app.core.errors import ConflictingState, InvalidCredentials, ValidationFailed
from app.core.security import hash_password, verify_password
from app.db.session import bind_tenant, get_session_factory
from app.modules.audit.service import AuditAction, SecurityEventKind, Severity, record_security
from app.modules.audit.service import record as audit_record
from app.modules.identity import totp
from app.modules.identity.models import User

logger = structlog.get_logger(__name__)

ISSUER = "EdirasX"


@dataclass(frozen=True, slots=True)
class Enrolment:
    secret: str
    uri: str
    recovery_codes: list[str]


def _load(user_id: uuid.UUID) -> tuple[Session, User]:
    session = get_session_factory()()
    bind_tenant(session, None)
    user = session.get(User, user_id)
    if user is None:
        session.close()
        raise ConflictingState("No such account.")
    return session, user


def begin_enrolment(user_id: uuid.UUID, *, account_label: str) -> Enrolment:
    """Generate a secret and recovery codes, and stage them un-activated.

    The plaintext secret and codes are returned exactly once. They are stored
    encrypted and hashed respectively, so this is the only moment they can be
    shown — which is why the response is the only copy the user gets.
    """
    session, user = _load(user_id)
    try:
        if user.mfa_enabled_at is not None:
            raise ConflictingState(
                "This account already uses an authenticator app. Remove it first."
            )
        secret = totp.generate_secret()
        codes = totp.generate_recovery_codes()

        user.mfa_secret_encrypted = crypto.encrypt(secret, purpose=crypto.MFA_SECRET)
        user.mfa_recovery_hashes = [hash_password(code) for code in codes]
        user.mfa_last_counter = None
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return Enrolment(
        secret=secret,
        uri=totp.provisioning_uri(secret, account=account_label, issuer=ISSUER),
        recovery_codes=codes,
    )


def activate(db: Session, user_id: uuid.UUID, code: str, *, tenant_id: uuid.UUID) -> None:
    """Enable MFA once a code from the new secret verifies."""
    session, user = _load(user_id)
    try:
        if user.mfa_secret_encrypted is None:
            raise ConflictingState("Start enrolment before confirming a code.")
        if user.mfa_enabled_at is not None:
            raise ConflictingState("This account already uses an authenticator app.")

        secret = crypto.decrypt(user.mfa_secret_encrypted, purpose=crypto.MFA_SECRET)
        result = totp.verify(secret, code, last_used_counter=user.mfa_last_counter)
        if not result:
            raise ValidationFailed({"code": "That code was not correct. Try the next one."})

        user.mfa_enabled_at = datetime.now(UTC)
        user.mfa_last_counter = result.counter
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    audit_record(
        db,
        action=AuditAction.configure,
        resource_type="user_mfa",
        resource_id=user_id,
        after={"mfa": "enabled"},
        reason="Authenticator app enrolled",
        actor_user_id=user_id,
    )


def verify_code(user_id: uuid.UUID, code: str, *, tenant_id: uuid.UUID, ip: str | None) -> None:
    """Check a TOTP code or a recovery code, rejecting replays.

    Both paths consume what they use: a TOTP counter is recorded so the same
    code cannot be presented twice, and a recovery code is removed once spent.
    A recovery code that survived its use would be a permanent bypass of the
    second factor.
    """
    session, user = _load(user_id)
    try:
        if user.mfa_enabled_at is None or user.mfa_secret_encrypted is None:
            raise ConflictingState("This account does not use an authenticator app.")

        secret = crypto.decrypt(user.mfa_secret_encrypted, purpose=crypto.MFA_SECRET)
        result = totp.verify(secret, code, last_used_counter=user.mfa_last_counter)
        if result:
            user.mfa_last_counter = result.counter
            session.commit()
            return

        remaining = list(user.mfa_recovery_hashes or [])
        for index, stored in enumerate(remaining):
            if verify_password(code.strip().upper(), stored):
                remaining.pop(index)
                user.mfa_recovery_hashes = remaining
                session.commit()
                record_security(
                    SecurityEventKind.login_failed,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    severity=Severity.warning,
                    ip=ip,
                    reason="recovery_code_used",
                    remaining=len(remaining),
                )
                return

        record_security(
            SecurityEventKind.login_failed,
            tenant_id=tenant_id,
            user_id=user_id,
            ip=ip,
            reason="mfa_code_rejected",
        )
        raise InvalidCredentials()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def disable(db: Session, user_id: uuid.UUID) -> None:
    """Remove the second factor entirely, including unspent recovery codes."""
    session, user = _load(user_id)
    try:
        user.mfa_secret_encrypted = None
        user.mfa_enabled_at = None
        user.mfa_last_counter = None
        user.mfa_recovery_hashes = None
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    audit_record(
        db,
        action=AuditAction.configure,
        resource_type="user_mfa",
        resource_id=user_id,
        before={"mfa": "enabled"},
        after={"mfa": "disabled"},
        reason="Authenticator app removed",
        actor_user_id=user_id,
    )


def is_enabled(user_id: uuid.UUID) -> bool:
    session, user = _load(user_id)
    try:
        return user.mfa_enabled_at is not None
    finally:
        session.close()
