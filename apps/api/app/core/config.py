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


@lru_cache
def get_settings() -> Settings:
    return Settings()
