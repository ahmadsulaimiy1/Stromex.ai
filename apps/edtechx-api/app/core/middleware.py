"""Edge middleware: request identity, response headers, and body limits."""

from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.core.context import set_request_id

logger = structlog.get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request id and emit one structured access log per request.

    The log carries identifiers only — never credentials, tokens, prompt
    content, or personal data (EDTECHX_ARCHITECTURE.md §10).
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        token = set_request_id(request_id)
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                tenant_id=str(getattr(request.state, "tenant_id", "") or ""),
            )
            from app.core.context import _request_id

            _request_id.reset(token)
        response.headers["x-request-id"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Headers that cost nothing and remove whole bug classes.

    The CSP is strict on purpose: tenant themes inject *values* into CSS
    custom properties, never raw stylesheet text, so no relaxation is needed
    to support customization (EDTECHX_SECURITY.md §5).
    """

    CSP = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data: blob:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("content-security-policy", self.CSP)
        headers.setdefault("x-content-type-options", "nosniff")
        headers.setdefault("referrer-policy", "strict-origin-when-cross-origin")
        headers.setdefault("cross-origin-opener-policy", "same-origin")
        headers.setdefault(
            "permissions-policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        )
        if get_settings().is_production:
            headers.setdefault(
                "strict-transport-security", "max-age=31536000; includeSubDomains; preload"
            )
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized bodies at the edge, before anything parses them."""

    def __init__(self, app: ASGIApp, max_body_bytes: int) -> None:
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        declared = request.headers.get("content-length")
        if declared is not None:
            try:
                if int(declared) > self.max_body_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "payload_too_large",
                                "detail": "That upload is larger than the limit.",
                            }
                        },
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "bad_request",
                            "detail": "The request could not be understood.",
                        }
                    },
                )
        return await call_next(request)
