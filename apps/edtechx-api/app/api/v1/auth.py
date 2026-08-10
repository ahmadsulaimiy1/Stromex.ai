"""Authentication routes.

Public by necessity, and therefore the most exposed surface in the product.
Every route here is rate-limit-bearing (Phase 2 follow-up), tenant-scoped by
the host, and deliberately uniform in what it reveals.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field

from app.api.deps import (
    CurrentPrincipal,
    DbSession,
    RateLimit,
    TenantContext,
    limit_by_account,
)
from app.core import errors, rate_limit
from app.modules.identity import service as identity_service

router = APIRouter(prefix="/auth", tags=["auth"])


class SignInRequest(BaseModel):
    # Deliberately a bounded string rather than `EmailStr`. At sign-in the
    # address is a lookup key, not a new registration: rejecting a malformed
    # one with 422 would distinguish "malformed" from "wrong", which is the
    # enumeration leak the uniform 401 exists to close. Strict deliverability
    # validation belongs on registration and invitation, where it helps.
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=512)


class SignOutRequest(BaseModel):
    everywhere: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"  # noqa: S105 - a scheme name, not a secret
    expires_in: int


def _require_tenant(tenant: TenantContext):
    """Authentication is always *at a school*, never at the platform."""
    if tenant is None:
        raise errors.TenantNotResolved()
    return tenant


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post(
    "/sign-in",
    response_model=TokenResponse,
    summary="Sign in at this school",
    responses={
        401: {"description": "Credentials not recognised"},
        429: {"description": "Too many attempts"},
    },
    dependencies=[
        Depends(RateLimit(rate_limit.SIGN_IN_PER_IP, by="ip")),
        Depends(RateLimit(rate_limit.SIGN_IN_PER_TENANT, by="tenant")),
    ],
)
def sign_in(
    payload: SignInRequest, request: Request, tenant: TenantContext, db: DbSession
) -> TokenResponse:
    school = _require_tenant(tenant)
    # Keyed on the submitted address, whether or not it names a real account:
    # limiting only real accounts would turn the 429 into an existence oracle.
    limit_by_account(request, tenant, payload.email)
    tokens = identity_service.authenticate(
        db,
        tenant_id=school.id,
        email=payload.email,
        password=payload.password,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new pair",
    responses={429: {"description": "Too many attempts"}},
    dependencies=[Depends(RateLimit(rate_limit.REFRESH_PER_IP, by="ip"))],
)
def refresh(
    payload: RefreshRequest, request: Request, tenant: TenantContext, db: DbSession
) -> TokenResponse:
    school = _require_tenant(tenant)
    tokens = identity_service.refresh_session(
        db,
        tenant_id=school.id,
        refresh_token=payload.refresh_token,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/sign-out",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out of this session, or of every session",
)
def sign_out(
    payload: SignOutRequest, principal: CurrentPrincipal, db: DbSession
) -> Response:
    identity_service.sign_out(
        db, session_id=principal.session_id, everywhere=payload.everywhere
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
