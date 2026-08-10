"""System and context routes.

`/context` is the endpoint the web client calls before rendering anything: it
returns the school the current host belongs to, so the interface can present
the school's identity rather than ours from the very first paint.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import (
    CurrentPrincipal,
    OptionalPrincipal,
    TenantContext,
)
from app.core.config import get_settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    environment: str


class SchoolContext(BaseModel):
    id: str
    slug: str
    name: str
    locale: str
    timezone: str


class ContextResponse(BaseModel):
    school: SchoolContext | None
    authenticated: bool


class MeResponse(BaseModel):
    user_id: str
    membership_id: str
    tenant_id: str
    permissions: list[str]
    scopes: list[str]


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health() -> HealthResponse:
    """Public by design: a health check that needed a tenant would be useless."""
    settings = get_settings()
    return HealthResponse(status="ok", environment=settings.environment)


@router.get("/context", response_model=ContextResponse, summary="Resolve the school")
def context(tenant: TenantContext, principal: OptionalPrincipal) -> ContextResponse:
    school = (
        SchoolContext(
            id=str(tenant.id),
            slug=tenant.slug,
            name=tenant.name,
            locale=tenant.locale,
            timezone=tenant.timezone,
        )
        if tenant
        else None
    )
    return ContextResponse(school=school, authenticated=principal is not None)


@router.get("/me", response_model=MeResponse, summary="The current principal")
def me(principal: CurrentPrincipal) -> MeResponse:
    return MeResponse(
        user_id=str(principal.user_id),
        membership_id=str(principal.membership_id),
        tenant_id=str(principal.tenant_id),
        permissions=sorted(principal.permissions),
        scopes=list(principal.scope_kinds),
    )

# The placeholder `/students` route that used to live here has been replaced by
# the real one in `app/api/v1/people.py`, which is scoped. The authorization
# tests in `test_api.py` still point at that path and now exercise the whole
# stack against a route that means something.
