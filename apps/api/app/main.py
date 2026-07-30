import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.llm.base import ProviderError

logger = structlog.get_logger(__name__)

settings = get_settings()

app = FastAPI(
    title="StromeX API",
    description="English-Arabic AI Operating System — backend API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
    logger.error("unhandled_provider_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "No AI model provider is currently available."},
    )


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
