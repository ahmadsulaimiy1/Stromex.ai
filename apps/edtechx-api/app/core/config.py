"""Application configuration.

Two database URLs, deliberately. The request path connects as a role that is
subject to row-level security and cannot bypass it; migrations connect as the
schema owner. Collapsing these into one URL would silently destroy the
isolation guarantee described in EDTECHX_ARCHITECTURE.md §4.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]

INSECURE_SECRET = "CHANGE_ME_A_LONG_RANDOM_VALUE_AT_LEAST_32_CHARS"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_prefix="EDTECHX_"
    )

    environment: Environment = "development"
    debug: bool = False

    # --- Security ---
    secret_key: str = INSECURE_SECRET
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    # Actions flagged high-risk require a re-authentication no older than this
    # (EDTECHX_PERMISSION_MODEL.md §8).
    elevation_ttl_minutes: int = 10

    # --- Database ---
    # The request path. MUST be a role without BYPASSRLS that does not own the
    # tables, or row-level security is decorative.
    database_url: str = (
        "postgresql+psycopg://edtechx_app:edtechx_app@localhost:5432/edtechx"
    )
    # DDL only. Never used to serve a request.
    migration_database_url: str = (
        "postgresql+psycopg://edtechx_migrator:edtechx_migrator@localhost:5432/edtechx"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # --- Redis ---
    redis_url: str | None = None

    # --- HTTP ---
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    max_body_bytes: int = 4 * 1024 * 1024

    # --- Tenancy ---
    # Hosts under this suffix resolve a tenant by its leftmost label:
    # `st-bede.edtechx.localhost` -> tenant slug `st-bede`.
    tenant_base_domain: str = "edtechx.localhost"
    # Hosts that carry no tenant at all (platform console, health checks).
    platform_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )

    # --- Passwords ---
    password_min_length: int = 12
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536  # KiB
    argon2_parallelism: int = 4

    # --- Login protection (EDTECHX_SECURITY.md §2) ---
    login_soft_fail_threshold: int = 5
    login_hard_fail_threshold: int = 10
    login_lockout_minutes: int = 15

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _guard_production(self) -> "Settings":
        """Refuse to boot production with development defaults.

        A misconfigured production deployment is a security incident, not a
        warning, so this raises rather than logs.
        """
        if not self.is_production:
            return self

        problems: list[str] = []
        if self.secret_key == INSECURE_SECRET or len(self.secret_key) < 32:
            problems.append("EDTECHX_SECRET_KEY must be set to a value of 32+ characters")
        if self.debug:
            problems.append("EDTECHX_DEBUG must be false in production")
        if "localhost" in self.database_url:
            problems.append("EDTECHX_DATABASE_URL still points at localhost")
        if self.database_url == self.migration_database_url:
            problems.append(
                "EDTECHX_DATABASE_URL and EDTECHX_MIGRATION_DATABASE_URL must differ: "
                "the request path must not run as the schema owner"
            )
        if any(o.startswith("http://") for o in self.cors_origins):
            problems.append("CORS origins must be https in production")

        if problems:
            raise RuntimeError(
                "Refusing to start in production:\n  - " + "\n  - ".join(problems)
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
