"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from stt_tg_bot.config.settings import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_valid_settings(self) -> None:
        """Test valid settings creation."""
        settings = Settings(
            telegram_bot_token="123456:ABC-DEF1234ghIkl",
            groq_api_key="gsk_test_key",
            public_base_url="https://example.com",
            webhook_secret="secret123",
            allowlist="123456789,@testuser",
        )

        assert settings.telegram_bot_token == "123456:ABC-DEF1234ghIkl"
        assert settings.groq_api_key == "gsk_test_key"
        assert settings.public_base_url == "https://example.com"
        assert settings.webhook_secret == "secret123"
        assert settings.allowlist == "123456789,@testuser"

    def test_missing_required_field(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Settings(
                telegram_bot_token="123456:ABC-DEF1234ghIkl",
                groq_api_key="gsk_test_key",
                public_base_url="https://example.com",
                webhook_secret="secret123",
                # allowlist отсутствует
            )

    def test_default_values(self) -> None:
        """Test default values for optional settings."""
        settings = Settings(
            telegram_bot_token="123456:ABC-DEF1234ghIkl",
            groq_api_key="gsk_test_key",
            public_base_url="https://example.com",
            webhook_secret="secret123",
            allowlist="123456789",
        )

        assert settings.use_webhook is True
        assert settings.port == 8080
        assert settings.read_timeout_sec == 120
        assert settings.groq_model_primary == "whisper-large-v3-turbo"
        assert settings.groq_model_fallback == "whisper-large-v3"

    def test_parsed_allowlist(self) -> None:
        """Test parsed_allowlist property."""
        settings = Settings(
            telegram_bot_token="123456:ABC-DEF1234ghIkl",
            groq_api_key="gsk_test_key",
            public_base_url="https://example.com",
            webhook_secret="secret123",
            allowlist="123456789, @testuser ,  987654321  , @another_user",
        )

        expected = {"123456789", "@testuser", "987654321", "@another_user"}
        assert settings.parsed_allowlist == expected

    def test_parsed_allowlist_empty_items(self) -> None:
        """Test that empty items in allowlist are ignored."""
        settings = Settings(
            telegram_bot_token="123456:ABC-DEF1234ghIkl",
            groq_api_key="gsk_test_key",
            public_base_url="https://example.com",
            webhook_secret="secret123",
            allowlist="123456789,,@testuser,  ,987654321",
        )

        expected = {"123456789", "@testuser", "987654321"}
        assert settings.parsed_allowlist == expected

    def test_webhook_url(self) -> None:
        """Test webhook_url property."""
        settings = Settings(
            telegram_bot_token="123456:ABC-DEF1234ghIkl",
            groq_api_key="gsk_test_key",
            public_base_url="https://mybot.herokuapp.com",
            webhook_secret="mysecret",
            allowlist="123456789",
        )

        expected = "https://mybot.herokuapp.com/tg/mysecret"
        assert settings.webhook_url == expected
