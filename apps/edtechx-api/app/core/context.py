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
class Principal:
    """The authenticated actor, already bound to one tenant."""

    user_id: UUID
    membership_id: UUID
    tenant_id: UUID
    permissions: frozenset[str]
    scopes: tuple[str, ...]
    session_id: UUID
    authenticated_at: float
    is_platform_operator: bool = False


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
