"""Request-scoped context.

The tenant is resolved once, at the edge, from the host and from the
authenticated principal — never from a query parameter, a body field, or a
client-supplied header. Everything downstream reads it from here.

Holding it in a ContextVar rather than passing it as an argument is a
deliberate trade: it means a service method physically cannot be called
without a tenant established, and a background job that forgets to establish
one fails loudly instead of quietly operating on nothing (or, worse, on
everything).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from uuid import UUID


class TenantContextMissing(RuntimeError):
    """Raised when tenant-scoped work is attempted outside a tenant context."""


@dataclass(frozen=True, slots=True)
class Grant:
    """One role grant: what it lets the holder do, and over which records.

    The pairing is the point. A principal's scopes are meaningless as a flat
    list, because the scope that came with "read announcements across the
    school" must not widen "read student records". Keeping the permissions and
    the scope together, per grant, is what makes `scopes_for(permission)`
    answerable — and a lossy union is what made it unanswerable before.

    Held in `core` as a plain record rather than in `authz`, for the same reason
    `permissions` is: `core` may not import a module, and the request context
    has to carry this from the edge to the query.
    """

    permissions: frozenset[str]
    scope_kind: str
    scope_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class Principal:
    """The authenticated actor, already bound to one tenant."""

    user_id: UUID
    membership_id: UUID
    tenant_id: UUID
    # The union of every grant's permissions, expanded. Correct for the yes/no
    # question "may this person do X at all" and for nothing else.
    permissions: frozenset[str]
    # The grants themselves, unmerged. Which records X applies to is answered
    # from here, per permission, never from the union above.
    grants: tuple[Grant, ...]
    session_id: UUID
    authenticated_at: float
    is_platform_operator: bool = False

    @property
    def scope_kinds(self) -> tuple[str, ...]:
        """The distinct scope kinds held, for display. Never for enforcement."""
        seen: list[str] = []
        for grant in self.grants:
            if grant.scope_kind not in seen:
                seen.append(grant.scope_kind)
        return tuple(seen)


_tenant_id: ContextVar[UUID | None] = ContextVar("edtechx_tenant_id", default=None)
_principal: ContextVar[Principal | None] = ContextVar("edtechx_principal", default=None)
_request_id: ContextVar[str | None] = ContextVar("edtechx_request_id", default=None)


# --- tenant ---------------------------------------------------------------

def set_tenant(tenant_id: UUID | None) -> Token:
    return _tenant_id.set(tenant_id)


def get_tenant() -> UUID | None:
    return _tenant_id.get()


def require_tenant() -> UUID:
    tenant_id = _tenant_id.get()
    if tenant_id is None:
        raise TenantContextMissing(
            "No tenant in context. Tenant-scoped work must run inside "
            "tenant_context(); a background job must set it from the job envelope."
        )
    return tenant_id


def reset_tenant(token: Token) -> None:
    _tenant_id.reset(token)


@contextmanager
def tenant_context(tenant_id: UUID | None) -> Iterator[None]:
    token = set_tenant(tenant_id)
    try:
        yield
    finally:
        reset_tenant(token)


# --- principal ------------------------------------------------------------

def set_principal(principal: Principal | None) -> Token:
    return _principal.set(principal)


def get_principal() -> Principal | None:
    return _principal.get()


def require_principal() -> Principal:
    principal = _principal.get()
    if principal is None:
        raise TenantContextMissing("No authenticated principal in context.")
    return principal


@contextmanager
def principal_context(principal: Principal | None) -> Iterator[None]:
    token = set_principal(principal)
    try:
        yield
    finally:
        _principal.reset(token)


# --- request id -----------------------------------------------------------

def set_request_id(request_id: str | None) -> Token:
    return _request_id.set(request_id)


def get_request_id() -> str | None:
    return _request_id.get()
