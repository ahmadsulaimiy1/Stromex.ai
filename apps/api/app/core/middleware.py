"""HTTP hardening middleware.

Audit findings addressed here:
- No security response headers were set anywhere (X-Content-Type-Options,
  X-Frame-Options, Referrer-Policy, HSTS) — cheap, standard defense-in-depth
  that was simply missing.
- No request body size limit existed at any layer — a client could stream an
  arbitrarily large payload at any endpoint (e.g. a chapter's markdown) and
  the app would happily buffer all of it.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # HSTS is meaningful only once TLS terminates in front of this
        # process (Cloudflare/VPS reverse proxy — see infra/DEPLOYMENT.md);
        # harmless to send over plain HTTP in dev, browsers ignore it there.
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Rejects requests whose declared `Content-Length` exceeds the limit.

    This is a real but partial mitigation: a client that omits Content-Length
    and streams via chunked transfer-encoding bypasses this check entirely.
    The complete fix is enforcing a body-size cap at the reverse proxy
    (nginx `client_max_body_size`, Cloudflare's own request-size limit) in
    front of this process — documented in infra/DEPLOYMENT.md — this
    middleware is the defense-in-depth layer for direct-to-app traffic
    (local dev, health checks bypassing the proxy, etc.), not the only layer.
    """

    def __init__(self, app, max_body_bytes: int) -> None:
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_body_bytes:
                    return Response(
                        content='{"detail":"Request body too large"}',
                        status_code=413,
                        media_type="application/json",
                    )
            except ValueError:
                pass
        return await call_next(request)
