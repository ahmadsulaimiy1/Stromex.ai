"""Regression tests for the audit finding that nothing stopped
ENVIRONMENT=production from booting with insecure defaults."""

import pytest

from app.core.config import Settings


def _prod_settings(**overrides) -> Settings:
    base = {
        "environment": "production",
        "secret_key": "a" * 40,
        "qdrant_url": "http://qdrant:6333",
        "cors_origins": ["https://stromex.ai"],
    }
    base.update(overrides)
    return Settings(**base)


def test_production_with_safe_config_does_not_raise():
    _prod_settings().validate_for_production()  # should not raise


def test_development_with_insecure_defaults_does_not_raise():
    Settings(environment="development").validate_for_production()


def test_production_rejects_default_secret_key():
    settings = _prod_settings(secret_key=Settings.model_fields["secret_key"].default)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        settings.validate_for_production()


def test_production_rejects_short_secret_key():
    settings = _prod_settings(secret_key="short")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        settings.validate_for_production()


def test_production_rejects_missing_qdrant_url():
    settings = _prod_settings(qdrant_url=None)
    with pytest.raises(RuntimeError, match="QDRANT_URL"):
        settings.validate_for_production()


def test_production_rejects_default_cors_origins():
    settings = _prod_settings(cors_origins=Settings.model_fields["cors_origins"].default)
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        settings.validate_for_production()
