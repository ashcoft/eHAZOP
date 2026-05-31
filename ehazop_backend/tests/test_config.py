"""Tests for configuration module."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_settings_default_values(self):
        """Settings should have correct default values."""
        settings = Settings()
        assert settings.APP_NAME == "EHAZOP Platform"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.DEBUG is False
        assert settings.ALGORITHM == "HS256"

    def test_settings_custom_values(self):
        """Settings should accept custom values."""
        settings = Settings(
            APP_NAME="Custom App",
            DEBUG=True,
            SECRET_KEY="custom-secret-key",
        )
        assert settings.APP_NAME == "Custom App"
        assert settings.DEBUG is True
        assert settings.SECRET_KEY == "custom-secret-key"

    def test_settings_defaults_for_security(self):
        """Security settings should have secure defaults."""
        settings = Settings()
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert settings.ALGORITHM == "HS256"
        assert settings.SECRET_KEY != ""  # Should have a default

    def test_settings_defaults_for_database(self):
        """Database settings should have defaults."""
        settings = Settings()
        assert settings.DATABASE_URL is not None
        assert "postgresql" in settings.DATABASE_URL

    def test_settings_defaults_for_storage(self):
        """Storage settings should have defaults."""
        settings = Settings()
        assert settings.STORAGE_TYPE == "local"
        assert settings.STORAGE_LOCAL_PATH == "./storage"

    def test_settings_defaults_for_llm(self):
        """LLM settings should have defaults."""
        settings = Settings()
        assert settings.LLM_PROVIDER == "gemini"
        assert settings.LLM_MODEL == "gemini-2.0-flash"

    def test_settings_cors_origins_default(self):
        """CORS origins should have default values."""
        settings = Settings()
        assert len(settings.CORS_ORIGINS) == 2
        assert "localhost:3000" in settings.CORS_ORIGINS[0]
        assert "localhost:5173" in settings.CORS_ORIGINS[1]

    def test_settings_rate_limiting_default(self):
        """Rate limiting should be enabled by default."""
        settings = Settings()
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS_PER_MINUTE == 60

    def test_settings_log_level_default(self):
        """Log level should default to INFO."""
        settings = Settings()
        assert settings.LOG_LEVEL == "INFO"

    def test_settings_storage_types(self):
        """Storage type should accept valid types."""
        for storage_type in ["local", "s3", "minio"]:
            settings = Settings(STORAGE_TYPE=storage_type)
            assert settings.STORAGE_TYPE == storage_type

    def test_settings_llm_providers(self):
        """LLM provider should accept valid types."""
        for provider in ["gemini", "openai"]:
            settings = Settings(LLM_PROVIDER=provider)
            assert settings.LLM_PROVIDER == provider

    def test_settings_log_levels(self):
        """Log level should accept valid levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            settings = Settings(LOG_LEVEL=level)
            assert settings.LOG_LEVEL == level

    def test_settings_vector_dimension_default(self):
        """Vector dimension should have a default."""
        settings = Settings()
        assert settings.VECTOR_DIMENSION == 768


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self):
        """get_settings should return a Settings instance."""
        # Clear cache to ensure fresh instance
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self):
        """get_settings should cache the settings."""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_returns_same_instance(self):
        """Multiple calls should return the same instance."""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        # They should be the same cached instance
        assert settings1 is settings2


class TestSettingsValidation:
    """Tests for Settings validation."""

    def test_settings_ignore_extra_fields(self):
        """Settings should ignore extra fields."""
        # This should not raise an error
        settings = Settings(EXTRA_FIELD_THAT_DOES_NOT_EXIST="value")
        assert settings.APP_NAME == "EHAZOP Platform"


class TestSettingsSecrets:
    """Tests for secrets handling."""

    def test_settings_secret_key_default(self):
        """SECRET_KEY should have a default but warn to change it."""
        settings = Settings()
        assert settings.SECRET_KEY != ""
        assert settings.SECRET_KEY == "change-me-in-production"

    def test_settings_gemini_api_key_nullable(self):
        """GEMINI_API_KEY should be optional."""
        settings = Settings()
        assert settings.GEMINI_API_KEY is None

    def test_settings_s3_credentials_nullable(self):
        """S3 credentials should be optional."""
        settings = Settings()
        assert settings.S3_ACCESS_KEY is None
        assert settings.S3_SECRET_KEY is None