from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit_by_field, rate_limit_by_ip
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
from app.db.models.user import User
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
    return user


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(_login_ip_limit), Depends(_login_email_limit)],
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenPair:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        decoded = decode_token_full(payload.refresh_token, TokenType.REFRESH)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.get(User, decoded.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Rotate: the presented refresh token is single-use from here on. If it
    # is ever replayed — by an attacker who intercepted it, or by a client
    # bug that retries — the replay is a revoked-token error, not a silent
    # second valid session.
    remaining = (decoded.expires_at - datetime.now(timezone.utc)).total_seconds()
    revoke(decoded.jti, ttl_seconds=int(remaining))

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
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
    remaining = (decoded.expires_at - datetime.now(timezone.utc)).total_seconds()
    revoke(decoded.jti, ttl_seconds=int(remaining))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
