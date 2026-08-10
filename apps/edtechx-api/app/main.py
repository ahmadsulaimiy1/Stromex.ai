"""EdTechX API application."""

from __future__ import annotations

import logging

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import EdTechXError
from app.core.middleware import (
    MaxBodySizeMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from app.db import registry  # noqa: F401  (populates model metadata)
from app.modules.authz.system_roles import validate_catalogue


def configure_logging(json_logs: bool) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer()
            if json_logs
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(json_logs=settings.is_production)

    # Fail the boot, not a request, if a role template drifted from the
    # permission catalogue.
    validate_catalogue()

    app = FastAPI(
        title="EdTechX API",
        description="The education platform that becomes your school's own platform.",
        version="0.1.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    # Outermost first: request identity wraps everything it logs.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MaxBodySizeMiddleware, max_body_bytes=settings.max_body_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["authorization", "content-type", "x-request-id"],
        max_age=600,
    )

    app.include_router(api_router)

    @app.exception_handler(EdTechXError)
    async def handle_app_error(request: Request, exc: EdTechXError) -> JSONResponse:
        structlog.get_logger(__name__).info(
            "handled_error",
            code=exc.code,
            status=exc.status_code,
            path=request.url.path,
            **{k: str(v) for k, v in exc.context.items()},
        )
        headers: dict[str, str] = {}
        retry_after = getattr(exc, "retry_after", None)
        if retry_after is not None:
            # Without this a well-behaved client has no way to back off
            # correctly, and retries in a tight loop against the limiter.
            headers["Retry-After"] = str(retry_after)
        return JSONResponse(
            status_code=exc.status_code, content=exc.to_body(), headers=headers
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Detail deliberately generic: internals belong in the log, not in a
        # response body that may be read by anyone.
        structlog.get_logger(__name__).exception(
            "unhandled_error", path=request.url.path, error=type(exc).__name__
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "detail": "Something went wrong. Please try again.",
                }
            },
        )

    return app


app = create_app()
