"""Application settings configuration."""

import sys
from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from pydantic_settings import BaseSettings, SettingsConfigDict
else:
    try:
        from pydantic_settings import BaseSettings, SettingsConfigDict
    except (
        ModuleNotFoundError
    ):  # pragma: no cover - executed only when dependency missing
        from pydantic import BaseModel

        class SettingsConfigDict(dict):
            """Fallback stub for SettingsConfigDict when pydantic-settings is absent."""

            pass

        class BaseSettings(BaseModel):
            """Fallback stub that mimics BaseSettings for testing environments."""

            model_config: "SettingsConfigDict" = SettingsConfigDict()


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        case_sensitive=True, extra="ignore", env_file_encoding="utf-8"
    )

    # Обязательные настройки
    telegram_bot_token: str = Field(..., description="Telegram Bot Token")
    groq_api_key: str = Field(..., description="Groq API Key")
    public_base_url: str = Field(..., description="Public URL for webhook")
    webhook_secret: str = Field(..., description="Webhook secret token")
    allowlist: str = Field(
        ..., description="Comma-separated list of user IDs and usernames"
    )

    # Опциональные настройки с дефолтными значениями
    use_webhook: bool = Field(
        default=True, description="Use webhook mode (False for long polling)"
    )
    port: int = Field(default=8080, description="Port for webhook server")
    read_timeout_sec: int = Field(
        default=120, description="HTTP read timeout in seconds"
    )
    groq_model_primary: str = Field(
        default="whisper-large-v3-turbo", description="Primary Groq model"
    )
    groq_model_fallback: str = Field(
        default="whisper-large-v3", description="Fallback Groq model"
    )
    groq_language: str | None = Field(
        default=None, description="Optional language override for Groq transcription"
    )

    # Опциональные настройки для OpenAI
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API Key for summaries and TTS"
    )
    openai_tts_model: str = Field(
        default="gpt-4o-mini-tts", description="OpenAI TTS model"
    )
    openai_tts_voice: str = Field(default="coral", description="OpenAI TTS voice")
    openai_tts_response_format: str = Field(
        default="opus", description="OpenAI TTS response format"
    )
    openai_tts_max_chars: int = Field(
        default=4096, description="Maximum characters for TTS input"
    )
    openai_tts_rate_limit_per_minute: int = Field(
        default=5, description="TTS requests per minute limit"
    )
    openai_tts_rate_limit_window_sec: int = Field(
        default=60, description="TTS rate limit window in seconds"
    )

    @property
    def parsed_allowlist(self) -> set[str]:
        """Parse allowlist string into set of user IDs and usernames."""
        return {item.strip() for item in self.allowlist.split(",") if item.strip()}

    @property
    def webhook_url(self) -> str:
        """Get full webhook URL."""
        return f"{self.public_base_url}/tg/{self.webhook_secret}"


# Глобальная переменная для настроек (ленивая инициализация)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Получить настройки приложения."""
    import os

    global _settings
    if _settings is None:
        try:
            # Создаём Settings с явным указанием переменных окружения
            _settings = Settings(
                telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
                groq_api_key=os.environ["GROQ_API_KEY"],
                public_base_url=os.environ["PUBLIC_BASE_URL"],
                webhook_secret=os.environ["WEBHOOK_SECRET"],
                allowlist=os.environ["ALLOWLIST"],
                # Опциональные с дефолтами
                use_webhook=os.environ.get("USE_WEBHOOK", "true").lower() == "true",
                port=int(os.environ.get("PORT", "8080")),
                read_timeout_sec=int(os.environ.get("READ_TIMEOUT_SEC", "120")),
                groq_model_primary=os.environ.get(
                    "GROQ_MODEL_PRIMARY", "whisper-large-v3-turbo"
                ),
                groq_model_fallback=os.environ.get(
                    "GROQ_MODEL_FALLBACK", "whisper-large-v3"
                ),
                groq_language=os.environ.get("GROQ_LANGUAGE"),
                openai_api_key=os.environ.get("OPENAI_API_KEY"),
                openai_tts_model=os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
                openai_tts_voice=os.environ.get("OPENAI_TTS_VOICE", "coral"),
                openai_tts_response_format=os.environ.get(
                    "OPENAI_TTS_RESPONSE_FORMAT", "opus"
                ),
                openai_tts_max_chars=int(
                    os.environ.get("OPENAI_TTS_MAX_CHARS", "4096")
                ),
                openai_tts_rate_limit_per_minute=int(
                    os.environ.get("OPENAI_TTS_RATE_LIMIT_PER_MINUTE", "5")
                ),
                openai_tts_rate_limit_window_sec=int(
                    os.environ.get("OPENAI_TTS_WINDOW_SEC", "60")
                ),
            )
        except KeyError as e:
            # В тестах могут отсутствовать переменные окружения
            if "test" in sys.modules or "pytest" in sys.modules:
                _settings = Settings(  # nosec B106 - тестовые данные для unit-тестов
                    telegram_bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
                    groq_api_key="test_key",
                    public_base_url="https://test.com",
                    webhook_secret="test_secret",
                    allowlist="123456789",
                )
            else:
                raise e
        except Exception as e:
            raise e
    return _settings


# Для обратной совместимости
try:
    settings = get_settings()
except Exception:
    # В тестах или при отсутствии настроек используем заглушку
    settings = None  # type: ignore
