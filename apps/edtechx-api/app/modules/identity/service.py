"""Authentication: sign in, refresh, sign out.

Three properties this module exists to guarantee, each of which is easy to get
subtly wrong:

  * A failed sign-in reveals nothing — not whether the account exists, not
    whether it belongs to this school, not whether it is locked.
  * A refresh token is usable exactly once. Presenting a rotated one is treated
    as theft and burns the whole family.
  * Every session belongs to one school. Signing in at one school grants
    nothing at another.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AccountLocked, InvalidCredentials, NotAuthenticated
from app.core.security import (
    InvalidToken,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    issue_access_token,
    issue_mfa_challenge,
    needs_rehash,
    verify_password,
)
from app.db.session import bind_tenant, get_session_factory
from app.modules.audit.service import (
    AuditAction,
    SecurityEventKind,
    Severity,
    record_security,
)
from app.modules.audit.service import record as audit_record
from app.modules.identity.models import (
    Membership,
    MembershipStatus,
    User,
    UserSession,
    UserStatus,
)

logger = structlog.get_logger(__name__)


class MfaRequired(Exception):
    """The password was correct; a second factor is still owed.

    Raised rather than returned so that no caller can mistake a half-finished
    authentication for a finished one — the type system makes the tokens
    unavailable rather than merely absent.
    """

    def __init__(self, challenge: str) -> None:
        super().__init__("Multi-factor authentication required")
        self.challenge = challenge


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    membership_id: uuid.UUID
    user_id: uuid.UUID
    session_id: uuid.UUID


def _record_security(
    tenant_id: uuid.UUID | None,
    kind: SecurityEventKind,
    *,
    user_id: uuid.UUID | None = None,
    severity: Severity = Severity.warning,
    ip: str | None = None,
    **detail: object,
) -> None:
    record_security(
        kind, tenant_id=tenant_id, user_id=user_id, severity=severity, ip=ip, **detail
    )


def _is_locked(user: User, now: datetime) -> bool:
    return user.locked_until is not None and user.locked_until > now


def _register_failure(user: User | None, tenant_id: uuid.UUID | None, ip: str | None) -> None:
    """Count a failure against the account and lock it past the threshold.

    Counted on the user row rather than only in a cache: a cache flush must not
    hand an attacker a fresh budget.
    """
    if user is None:
        return
    settings = get_settings()
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        fresh = session.get(User, user.id)
        if fresh is None:
            return
        fresh.failed_login_count += 1
        if fresh.failed_login_count >= settings.login_hard_fail_threshold:
            fresh.locked_until = datetime.now(UTC) + timedelta(
                minutes=settings.login_lockout_minutes
            )
            _record_security(
                tenant_id,
                SecurityEventKind.account_locked,
                user_id=fresh.id,
                severity=Severity.critical,
                failures=fresh.failed_login_count,
                ip=ip,
            )
        session.commit()
    finally:
        session.close()


def authenticate(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    email: str,
    password: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> IssuedTokens:
    """Sign a person in at one school.

    Every failure path raises the same `InvalidCredentials` with the same
    message, and every path performs a password verification — including the
    ones where no password could possibly match — so neither the response nor
    its timing distinguishes "no such account" from "wrong password" from
    "not a member of this school".
    """
    now = datetime.now(UTC)
    normalised = email.strip().lower()

    platform = get_session_factory()()
    bind_tenant(platform, None)
    try:
        user = platform.execute(
            select(User).where(User.email == normalised)
        ).scalar_one_or_none()

        # Always verify against *something*: an equalising hash when the account
        # does not exist, so timing does not leak existence.
        password_ok = verify_password(password, user.password_hash if user else None)

        if user is None:
            _record_security(
                tenant_id, SecurityEventKind.login_failed, ip=ip, reason="unknown_account"
            )
            raise InvalidCredentials()

        if _is_locked(user, now):
            _record_security(
                tenant_id, SecurityEventKind.login_failed, user_id=user.id, ip=ip,
                reason="locked",
            )
            raise AccountLocked()

        if not password_ok or user.status is not UserStatus.active:
            _register_failure(user, tenant_id, ip)
            _record_security(
                tenant_id, SecurityEventKind.login_failed, user_id=user.id, ip=ip,
                reason="bad_password" if not password_ok else "inactive_account",
            )
            raise InvalidCredentials()

        user_id = user.id
        rehash = password_ok and needs_rehash(user.password_hash or "")
        mfa_enabled = user.mfa_enabled_at is not None
    finally:
        platform.close()

    # Membership is read inside the tenant's own context, so a user who belongs
    # to a different school simply has no membership here — the same outcome as
    # a wrong password, and indistinguishable from outside.
    membership = db.execute(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalar_one_or_none()
    if membership is None:
        _record_security(
            tenant_id, SecurityEventKind.login_failed, user_id=user_id, ip=ip,
            reason="no_membership_in_tenant",
        )
        raise InvalidCredentials()

    _clear_failures(user_id, rehash_password=password if rehash else None)

    if mfa_enabled:
        # Stop here. No session row, no tokens — only a short-lived challenge
        # that authorises the second factor and nothing else.
        raise MfaRequired(
            issue_mfa_challenge(
                user_id=user_id, membership_id=membership.id, tenant_id=tenant_id
            )
        )

    tokens = _issue_session(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        membership_id=membership.id,
        ip=ip,
        user_agent=user_agent,
    )
    audit_record(
        db,
        action=AuditAction.login,
        resource_type="session",
        resource_id=tokens.session_id,
        actor_user_id=user_id,
        actor_membership_id=membership.id,
        ip=ip,
        user_agent=user_agent,
    )
    return tokens


def _clear_failures(user_id: uuid.UUID, rehash_password: str | None) -> None:
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        user = session.get(User, user_id)
        if user is None:
            return
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        if rehash_password is not None:
            # A password imported as bcrypt is upgraded to Argon2id the first
            # time its owner proves they know it — the only moment it is
            # available in plaintext.
            user.password_hash = hash_password(rehash_password)
        session.commit()
    finally:
        session.close()


def _issue_session(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    membership_id: uuid.UUID,
    ip: str | None,
    user_agent: str | None,
    rotated_from: uuid.UUID | None = None,
) -> IssuedTokens:
    settings = get_settings()
    now = datetime.now(UTC)
    refresh = generate_refresh_token()
    record = UserSession(
        user_id=user_id,
        membership_id=membership_id,
        refresh_token_hash=hash_refresh_token(refresh),
        issued_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_ttl_days),
        rotated_from_id=rotated_from,
        ip=ip,
        user_agent=(user_agent or "")[:512] or None,
    )
    db.add(record)
    db.flush()

    access, _claims = issue_access_token(
        user_id=user_id,
        membership_id=membership_id,
        tenant_id=tenant_id,
        session_id=record.id,
    )
    return IssuedTokens(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_ttl_minutes * 60,
        membership_id=membership_id,
        user_id=user_id,
        session_id=record.id,
    )


def refresh_session(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    refresh_token: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> IssuedTokens:
    """Exchange a refresh token for a new pair, once.

    Reuse detection: a token that has already been rotated is evidence that
    somebody holds a copy they should not. The response is to revoke the entire
    family — the legitimate holder is signed out too, which is the correct
    trade when the alternative is leaving an attacker signed in.
    """
    now = datetime.now(UTC)
    token_hash = hash_refresh_token(refresh_token)

    record = db.execute(
        select(UserSession).where(UserSession.refresh_token_hash == token_hash)
    ).scalar_one_or_none()
    if record is None:
        _record_security(tenant_id, SecurityEventKind.login_failed, ip=ip, reason="unknown_refresh")
        raise NotAuthenticated()

    if record.revoked_at is not None:
        # Revoked on its own session, which commits before this request is
        # rejected. Doing it on the request's session would be undone by the
        # rollback that accompanies the 401 — the detection would fire, log,
        # and then quietly change nothing.
        _revoke_family_committed(tenant_id, record.id, reason="reuse_detected")
        _record_security(
            tenant_id,
            SecurityEventKind.refresh_reuse,
            user_id=record.user_id,
            severity=Severity.critical,
            ip=ip,
            session_id=record.id,
        )
        raise NotAuthenticated()

    if record.expires_at <= now:
        raise NotAuthenticated()

    membership = db.get(Membership, record.membership_id)
    if membership is None or membership.status is not MembershipStatus.active:
        raise NotAuthenticated()

    record.revoked_at = now
    record.revoked_reason = "rotated"
    return _issue_session(
        db,
        tenant_id=tenant_id,
        user_id=record.user_id,
        membership_id=record.membership_id,
        ip=ip,
        user_agent=user_agent,
        rotated_from=record.id,
    )


def _revoke_family_committed(
    tenant_id: uuid.UUID, session_id: uuid.UUID, reason: str
) -> None:
    """Revoke a token family on a session of its own, and commit it.

    Separate from the request's transaction on purpose: the request that
    triggers this is about to be rejected, and a rollback must not undo the
    revocation it triggered.
    """
    own = get_session_factory()()
    bind_tenant(own, tenant_id)
    try:
        record = own.get(UserSession, session_id)
        if record is not None:
            _revoke_family(own, record, reason)
        own.commit()
    except Exception:  # pragma: no cover
        own.rollback()
        logger.error("revoke_family_failed", session_id=str(session_id))
        raise
    finally:
        own.close()


def _revoke_family(db: Session, record: UserSession, reason: str) -> None:
    """Revoke every session descended from, or ancestral to, this one."""
    now = datetime.now(UTC)
    root = record
    seen: set[uuid.UUID] = set()
    while root.rotated_from_id is not None and root.rotated_from_id not in seen:
        seen.add(root.id)
        parent = db.get(UserSession, root.rotated_from_id)
        if parent is None:
            break
        root = parent

    frontier = [root.id]
    while frontier:
        current = frontier.pop()
        session_record = db.get(UserSession, current)
        if session_record is None:
            continue
        if session_record.revoked_reason != reason:
            session_record.revoked_at = now
            session_record.revoked_reason = reason
        children = db.execute(
            select(UserSession.id).where(UserSession.rotated_from_id == current)
        ).scalars().all()
        frontier.extend(children)


def sign_out(db: Session, *, session_id: uuid.UUID, everywhere: bool = False) -> int:
    """Revoke this session, or every session this person holds at this school."""
    now = datetime.now(UTC)
    record = db.get(UserSession, session_id)
    if record is None:
        return 0

    if not everywhere:
        if record.revoked_at is None:
            record.revoked_at = now
            record.revoked_reason = "signed_out"
        return 1

    records = db.execute(
        select(UserSession).where(
            UserSession.user_id == record.user_id,
            UserSession.revoked_at.is_(None),
        )
    ).scalars().all()
    for item in records:
        item.revoked_at = now
        item.revoked_reason = "signed_out_everywhere"
    audit_record(
        db,
        action=AuditAction.logout,
        resource_type="session",
        resource_id=record.id,
        actor_user_id=record.user_id,
        actor_membership_id=record.membership_id,
        reason="Signed out everywhere",
    )
    return len(records)


def session_is_live(db: Session, session_id: uuid.UUID) -> bool:
    record = db.get(UserSession, session_id)
    return (
        record is not None
        and record.revoked_at is None
        and record.expires_at > datetime.now(UTC)
    )


# --- account and membership creation -------------------------------------


def upsert_user(
    *, email: str, full_name: str, password: str | None = None
) -> uuid.UUID:
    """Find or create a global account.

    One human, one credential, many schools — so an existing account is reused
    and its password is never touched by a school provisioning a membership
    for it.
    """
    normalised = email.strip().lower()
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        user = session.execute(
            select(User).where(User.email == normalised)
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=normalised,
                full_name=full_name.strip(),
                status=UserStatus.active if password else UserStatus.invited,
                password_hash=hash_password(password) if password else None,
            )
            session.add(user)
            session.flush()
        user_id = user.id
        session.commit()
        return user_id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_membership(
    db: Session, *, user_id: uuid.UUID, display_name: str
) -> Membership:
    membership = Membership(
        user_id=user_id,
        status=MembershipStatus.active,
        display_name=display_name.strip(),
        started_at=datetime.now(UTC),
    )
    db.add(membership)
    db.flush()
    return membership


def complete_mfa(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    challenge: str,
    code: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> IssuedTokens:
    """Finish a sign-in that was suspended pending a second factor."""
    from app.core.security import decode_mfa_challenge
    from app.modules.identity import mfa

    try:
        claims = decode_mfa_challenge(challenge)
    except InvalidToken as exc:
        raise NotAuthenticated() from exc

    # A challenge minted for one school must not complete a sign-in at another.
    if claims.tenant_id != tenant_id:
        _record_security(
            tenant_id,
            SecurityEventKind.tenant_mismatch,
            user_id=claims.user_id,
            severity=Severity.critical,
            ip=ip,
            reason="mfa_challenge_wrong_tenant",
        )
        raise NotAuthenticated()

    membership = db.get(Membership, claims.membership_id)
    if membership is None or membership.status is not MembershipStatus.active:
        raise NotAuthenticated()

    mfa.verify_code(claims.user_id, code, tenant_id=tenant_id, ip=ip)

    tokens = _issue_session(
        db,
        tenant_id=tenant_id,
        user_id=claims.user_id,
        membership_id=claims.membership_id,
        ip=ip,
        user_agent=user_agent,
    )
    audit_record(
        db,
        action=AuditAction.login,
        resource_type="session",
        resource_id=tokens.session_id,
        actor_user_id=claims.user_id,
        actor_membership_id=claims.membership_id,
        reason="Completed with second factor",
        ip=ip,
        user_agent=user_agent,
    )
    return tokens
