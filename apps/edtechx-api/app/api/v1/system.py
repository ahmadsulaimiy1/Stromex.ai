"""System and context routes.

`/context` is the endpoint the web client calls before rendering anything: it
returns the school the current host belongs to, so the interface can present
the school's identity rather than ours from the very first paint.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import (
    CurrentPrincipal,
    OptionalPrincipal,
    RequirePermission,
    TenantContext,
)
from app.core.config import get_settings
from app.core.context import Principal

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
        scopes=list(principal.scopes),
    )


@router.get(
    "/students",
    summary="Placeholder guarded route used to prove enforcement end to end",
)
def list_students(
    principal: Annotated[Principal, Depends(RequirePermission("people.student.read"))],
) -> dict[str, list[str]]:
    """A real students endpoint arrives in Phase 2.

    This route exists now so that the authorization and tenant-isolation tests
    exercise the whole stack — router, dependency, session, policy — rather
    than only the units beneath it.
    """
    return {"students": []}
