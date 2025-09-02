"""Application settings configuration."""

import sys

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=[".env.test", ".env"], case_sensitive=True, extra="ignore"
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
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            # В тестах могут отсутствовать переменные окружения
            # Возвращаем объект с минимальными настройками для тестирования
            if "test" in sys.modules or "pytest" in sys.modules:
                _settings = Settings(  # nosec B106 - тестовые данные для unit-тестов
                    telegram_bot_token="test_token",
                    groq_api_key="test_key",
                    public_base_url="https://test.com",
                    webhook_secret="test_secret",
                    allowlist="123456789",
                )
            else:
                raise e
    return _settings


# Для обратной совместимости
try:
    settings = get_settings()
except Exception:
    # В тестах или при отсутствии настроек используем заглушку
    settings = None  # type: ignore
