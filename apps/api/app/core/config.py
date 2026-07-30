from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"

    # --- Security ---
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_A_LONG_RANDOM_VALUE"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    jwt_algorithm: str = "HS256"

    # --- Database ---
    database_url: str = "postgresql+psycopg://stromex:stromex@localhost:5432/stromex"
    # SQLAlchemy's own defaults (pool_size=5, max_overflow=10) are fine for a
    # single dev process but are a real bottleneck under concurrent load —
    # sized here so scaling the pool is a config change, not a code change.
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Qdrant ---
    qdrant_url: str | None = None
    qdrant_local_path: str | None = "./.qdrant-local"
    qdrant_api_key: str | None = None

    # --- LLM providers (all optional; router degrades gracefully if unset) ---
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    deepseek_api_key: str | None = None
    perplexity_api_key: str | None = None

    default_chat_model: str = "claude"

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:3000"]

    # --- Admin bootstrap ---
    admin_bootstrap_email: str | None = None

    def validate_for_production(self) -> None:
        """Audit finding: nothing stopped `ENVIRONMENT=production` from
        booting with the placeholder secret key, a local-file Qdrant store
        that silently fragments across multiple workers/replicas, or a CORS
        allow-list still pointed at localhost. Each of those is a "works in
        the demo, breaks or leaks in production" failure mode — better to
        refuse to start than to start wrong. Called once from `main.py` at
        import time, not from `get_settings()`, so tests and local dev are
        never affected by it."""
        if self.environment != "production":
            return

        problems = []
        if self.secret_key == Settings.model_fields["secret_key"].default:
            problems.append("SECRET_KEY is still the insecure development placeholder")
        if len(self.secret_key) < 32:
            problems.append("SECRET_KEY is too short (want at least 32 random characters)")
        if not self.qdrant_url:
            problems.append(
                "QDRANT_URL is unset — embedded local-file Qdrant mode is not safe "
                "across multiple workers or replicas and must not be used in production"
            )
        if self.cors_origins == Settings.model_fields["cors_origins"].default:
            problems.append("CORS_ORIGINS is still the localhost-only development default")

        if problems:
            raise RuntimeError(
                "Refusing to start with ENVIRONMENT=production: " + "; ".join(problems)
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
