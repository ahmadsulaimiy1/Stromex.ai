import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.auth_tokens import EMAIL_VERIFY_TTL, PASSWORD_RESET_TTL, consume_token, issue_token
from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.email import send_email_verification_email, send_password_reset_email
from app.core.google_oauth import (
    GoogleOAuthNotConfigured,
    authorize_url,
    exchange_code,
    verify_id_token,
)
from app.core.rate_limit import rate_limit_by_field, rate_limit_by_ip, rate_limit_by_user
from app.core.redis import get_redis
from app.core.security import (
    TokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token_full,
    hash_password,
    verify_password,
)
from app.core.token_denylist import revoke
from app.db.base import get_db
from app.db.models.user import AuthTokenPurpose, User
from app.schemas.auth import (
    AccountDeleteRequest,
    EmailVerifyConfirm,
    GuestUpgradeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.schemas.user import RefreshRequest, TokenPair, UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

# Brute-force / abuse mitigations (audit finding: these endpoints had no rate
# limiting at all). Register is IP-only — there's no account to key against
# yet. Login is limited two ways: by IP (stop one client hammering many
# accounts) AND by the submitted email (stop credential stuffing against one
# account spread across many IPs) — either alone misses the other pattern.
_register_limit = rate_limit_by_ip(times=5, seconds=3600, bucket="register")
_login_ip_limit = rate_limit_by_ip(times=20, seconds=300, bucket="login-ip")
_login_email_limit = rate_limit_by_field(times=8, seconds=900, bucket="login-email", field="email")
_guest_limit = rate_limit_by_ip(times=20, seconds=3600, bucket="guest")
_reset_request_ip_limit = rate_limit_by_ip(times=10, seconds=3600, bucket="reset-request-ip")
_reset_request_email_limit = rate_limit_by_field(
    times=5, seconds=3600, bucket="reset-request-email", field="email"
)
_verify_request_limit = rate_limit_by_user(times=5, seconds=3600, bucket="verify-request")
_google_callback_limit = rate_limit_by_ip(times=30, seconds=3600, bucket="google-callback")
_account_delete_limit = rate_limit_by_user(times=5, seconds=3600, bucket="account-delete")

_GOOGLE_STATE_PREFIX = "google-oauth-state"
_GOOGLE_STATE_TTL_SECONDS = 600


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_register_limit)],
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = issue_token(db, user.id, AuthTokenPurpose.EMAIL_VERIFY, EMAIL_VERIFY_TTL)
    send_email_verification_email(user.email, token)

    return user


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(_login_ip_limit), Depends(_login_email_limit)],
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenPair:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or user.password_hash is None or not verify_password(
        payload.password, user.password_hash
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return TokenPair(
        access_token=create_access_token(user.id, user.token_version),
        refresh_token=create_refresh_token(user.id, user.token_version),
    )


@router.post(
    "/guest",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_guest_limit)],
)
def create_guest(db: Session = Depends(get_db)) -> TokenPair:
    """Continue as Guest: an immediately usable local account with no email
    or password, so a first-time user can start chatting within seconds.
    Upgrade to a full account later via POST /auth/guest/upgrade without
    losing anything — it's the same user row, not a migration."""
    user = User(
        # Note: ".local" is a reserved TLD that pydantic's EmailStr
        # validator rejects on response serialization (it isn't just an
        # unreachable address to email-validator, it's a name reserved by
        # RFC 6762 and treated as invalid outright) — use a subdomain of a
        # real TLD instead, still guaranteed to never be a real mailbox.
        email=f"guest-{uuid.uuid4()}@guest.stromex.ai",
        password_hash=None,
        display_name="Guest",
        is_guest=True,
        is_verified=True,  # nothing to verify — there's no real email here
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenPair(
        access_token=create_access_token(user.id, user.token_version),
        refresh_token=create_refresh_token(user.id, user.token_version),
    )


@router.post("/guest/upgrade", response_model=UserRead)
def upgrade_guest(
    payload: GuestUpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if not current_user.is_guest:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This account is not a guest account")

    existing = db.query(User).filter(User.email == payload.email, User.id != current_user.id).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    current_user.email = payload.email
    current_user.password_hash = hash_password(payload.password)
    current_user.display_name = payload.display_name
    current_user.is_guest = False
    current_user.is_verified = False
    db.commit()
    db.refresh(current_user)

    token = issue_token(db, current_user.id, AuthTokenPurpose.EMAIL_VERIFY, EMAIL_VERIFY_TTL)
    send_email_verification_email(current_user.email, token)

    return current_user


@router.post(
    "/password-reset/request",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_reset_request_ip_limit), Depends(_reset_request_email_limit)],
)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> None:
    """Always answers 202, whether or not the email exists — confirming
    either way here would let an attacker enumerate registered accounts."""
    user = db.query(User).filter(User.email == payload.email, User.is_guest.is_(False)).first()
    if user is not None:
        token = issue_token(db, user.id, AuthTokenPurpose.PASSWORD_RESET, PASSWORD_RESET_TTL)
        send_password_reset_email(user.email, token)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> None:
    record = consume_token(db, payload.token, AuthTokenPurpose.PASSWORD_RESET)
    if record is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user.password_hash = hash_password(payload.new_password)
    # A password reset is exactly the moment to assume every existing
    # session might be compromised (that's usually why it's happening) —
    # sign out everywhere rather than leaving old sessions valid.
    user.token_version += 1
    db.commit()


@router.post(
    "/email/verify/request",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_verify_request_limit)],
)
def request_email_verification(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    if current_user.is_verified:
        return
    token = issue_token(db, current_user.id, AuthTokenPurpose.EMAIL_VERIFY, EMAIL_VERIFY_TTL)
    send_email_verification_email(current_user.email, token)


@router.post("/email/verify/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_email_verification(payload: EmailVerifyConfirm, db: Session = Depends(get_db)) -> None:
    record = consume_token(db, payload.token, AuthTokenPurpose.EMAIL_VERIFY)
    if record is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user.is_verified = True
    db.commit()


@router.get("/google/authorize")
def google_authorize(platform: str = Query(default="web", pattern="^(web|android)$")) -> RedirectResponse:
    """Opens Google's own consent screen in the system browser (never in the
    app's embedded WebView — Google's terms disallow signing in there; see
    app/core/google_oauth.py). `platform` controls where /google/callback
    sends the user back to once Google redirects here with a code."""
    state = f"{secrets.token_urlsafe(24)}:{platform}"
    get_redis().set(f"{_GOOGLE_STATE_PREFIX}:{state}", "1", ex=_GOOGLE_STATE_TTL_SECONDS)
    try:
        url = authorize_url(state)
    except GoogleOAuthNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return RedirectResponse(url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/google/callback", dependencies=[Depends(_google_callback_limit)])
def google_callback(
    code: str, state: str, db: Session = Depends(get_db)
) -> RedirectResponse:
    redis = get_redis()
    state_key = f"{_GOOGLE_STATE_PREFIX}:{state}"
    if not redis.delete(state_key):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state")
    platform = state.rsplit(":", 1)[-1] if ":" in state else "web"

    try:
        identity = exchange_code(code)
    except GoogleOAuthNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Google sign-in failed"
        ) from exc

    user = db.query(User).filter(User.google_sub == identity.sub).first()
    if user is None:
        # Link to an existing email/password account with a matching,
        # Google-verified email, rather than creating a duplicate account —
        # but only when Google itself vouches the email is verified, so an
        # attacker can't claim someone else's account via an unverified
        # address at some third-party provider.
        if identity.email_verified:
            user = db.query(User).filter(User.email == identity.email).first()
        if user is None:
            user = User(
                email=identity.email,
                password_hash=None,
                display_name=identity.name or identity.email.split("@")[0],
                is_guest=False,
                is_verified=identity.email_verified,
                google_sub=identity.sub,
            )
            db.add(user)
        else:
            user.google_sub = identity.sub
            if identity.email_verified:
                user.is_verified = True
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user.id, user.token_version)
    refresh_token = create_refresh_token(user.id, user.token_version)

    settings = get_settings()
    if platform == "android":
        redirect_url = (
            f"{settings.app_deep_link_scheme}://auth-callback"
            f"?access_token={access_token}&refresh_token={refresh_token}"
        )
    else:
        redirect_url = (
            f"{settings.frontend_base_url}/auth/google-callback"
            f"?access_token={access_token}&refresh_token={refresh_token}"
        )
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        decoded = decode_token_full(payload.refresh_token, TokenType.REFRESH)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.get(User, decoded.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    if decoded.token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated by a sign-out on all devices",
        )

    # Rotate: the presented refresh token is single-use from here on. If it
    # is ever replayed — by an attacker who intercepted it, or by a client
    # bug that retries — the replay is a revoked-token error, not a silent
    # second valid session.
    remaining = (decoded.expires_at - datetime.now(UTC)).total_seconds()
    revoke(decoded.jti, ttl_seconds=int(remaining))

    return TokenPair(
        access_token=create_access_token(user.id, user.token_version),
        refresh_token=create_refresh_token(user.id, user.token_version),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest) -> None:
    """Revokes the given refresh token so it can no longer mint new access
    tokens. Already-issued access tokens remain valid until they naturally
    expire (≤30 minutes) — see `app/core/token_denylist.py` for why that's
    the accepted tradeoff rather than a gap."""
    try:
        decoded = decode_token_full(payload.refresh_token, TokenType.REFRESH)
    except TokenError:
        # Already invalid/expired/revoked — logout's goal is already
        # satisfied, so this isn't an error from the caller's point of view.
        return
    remaining = (decoded.expires_at - datetime.now(UTC)).total_seconds()
    revoke(decoded.jti, ttl_seconds=int(remaining))


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all_devices(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    """Invalidates every access and refresh token issued so far for this
    account in one step, by bumping token_version — see get_current_user
    and /refresh, which both compare a token's embedded version against
    this. No need to enumerate or individually revoke outstanding tokens."""
    current_user.token_version += 1
    db.commit()


@router.delete(
    "/me", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(_account_delete_limit)]
)
def delete_account(
    payload: AccountDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Permanently deletes the account and everything owned by it
    (conversations, memory, Qur'an plans, books — all `cascade="all,
    delete-orphan"` on User). Confirmation requirement depends on how the
    account authenticates: a guest account (nothing irreplaceable, no
    credential to check) needs only a live session; a password account
    must re-confirm its current password; a Google-only account (no
    password set) must re-confirm with a fresh Google ID token for the
    same google_sub — either way, a bare access token alone can't destroy
    the account."""
    if current_user.is_guest:
        pass
    elif current_user.password_hash is not None:
        if not payload.password or not verify_password(payload.password, current_user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    elif current_user.google_sub is not None:
        if not payload.google_id_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Re-authentication with Google is required to delete this account",
            )
        try:
            identity = verify_id_token(payload.google_id_token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Google re-authentication failed"
            ) from exc
        if identity.sub != current_user.google_sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account does not match this account",
            )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot verify account ownership")

    db.delete(current_user)
    db.commit()


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
