"""Application errors and their HTTP mapping.

The status codes here encode two decisions from the permission model:

  * a missing *permission* is 403 — the capability is not secret;
  * a missing *scope* over a named resource is 404 — its existence is
    (ADR-004).

Error bodies never carry internals. `detail` is written for the person reading
it on screen; anything an engineer needs goes to the structured log.
"""

from __future__ import annotations

from typing import Any


class EdTechXError(Exception):
    status_code: int = 500
    code: str = "internal_error"
    detail: str = "Something went wrong. Please try again."

    def __init__(self, detail: str | None = None, **context: Any) -> None:
        self.detail = detail or self.detail
        self.context = context
        super().__init__(self.detail)

    def to_body(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "detail": self.detail}}


class NotAuthenticated(EdTechXError):
    status_code = 401
    code = "not_authenticated"
    detail = "Please sign in to continue."


class InvalidCredentials(EdTechXError):
    status_code = 401
    code = "invalid_credentials"
    # Identical whether the account exists or not — see EDTECHX_SECURITY.md §2.
    detail = "Those sign-in details were not recognised."


class AccountLocked(EdTechXError):
    status_code = 423
    code = "account_locked"
    detail = "This account is temporarily locked. Please try again shortly."


class PermissionDenied(EdTechXError):
    status_code = 403
    code = "permission_denied"
    detail = "You do not have permission to do that."


class ResourceNotFound(EdTechXError):
    status_code = 404
    code = "not_found"
    detail = "That item could not be found."


class EntitlementRequired(EdTechXError):
    """The plan does not include this capability — an upgrade path, not a wall."""

    status_code = 402
    code = "entitlement_required"
    detail = "This feature is not included in your current plan."

    def __init__(self, feature: str, detail: str | None = None) -> None:
        super().__init__(detail, feature=feature)
        self.feature = feature

    def to_body(self) -> dict[str, Any]:
        body = super().to_body()
        body["error"]["feature"] = self.feature
        return body


class RateLimited(EdTechXError):
    """Too many requests. Carries Retry-After so a client can behave well."""

    status_code = 429
    code = "rate_limited"
    detail = "Too many attempts. Please wait a moment and try again."

    def __init__(self, retry_after: int, policy: str = "") -> None:
        super().__init__(None, retry_after=retry_after, policy=policy)
        self.retry_after = retry_after
        self.policy = policy


class QuotaExceeded(EdTechXError):
    status_code = 429
    code = "quota_exceeded"
    detail = "You have reached your allowance for this period."


class ValidationFailed(EdTechXError):
    status_code = 422
    code = "validation_failed"
    detail = "Some of the information provided was not valid."

    def __init__(self, fields: dict[str, str], detail: str | None = None) -> None:
        super().__init__(detail, fields=fields)
        self.fields = fields

    def to_body(self) -> dict[str, Any]:
        body = super().to_body()
        body["error"]["fields"] = self.fields
        return body


class ConflictingState(EdTechXError):
    status_code = 409
    code = "conflict"
    detail = "That action conflicts with the current state of this record."


class TenantNotResolved(EdTechXError):
    status_code = 404
    code = "unknown_school"
    detail = "No school is configured for this address."


class TenantSuspended(EdTechXError):
    status_code = 403
    code = "school_unavailable"
    detail = "This school's account is not currently active."


class TenantContextMismatch(EdTechXError):
    """A token minted for one school, presented on another's hostname."""

    status_code = 403
    code = "tenant_mismatch"
    detail = "Please sign in again."


class ElevationRequired(EdTechXError):
    status_code = 403
    code = "elevation_required"
    detail = "Please confirm your password to continue."
