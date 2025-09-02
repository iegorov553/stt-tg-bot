"""FastAPI webhook server for Telegram bot."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request

from stt_tg_bot.config.settings import settings
from stt_tg_bot.handlers.bot_handlers import setup_handlers

logger = logging.getLogger(__name__)


class WebhookApp:
    """Класс для управления webhook приложением."""

    def __init__(self) -> None:
        """Инициализация приложения."""
        self.bot = Bot(token=settings.telegram_bot_token)
        self.dispatcher = Dispatcher()

        # Настраиваем хендлеры
        setup_handlers(self.dispatcher)

        # Создаём FastAPI приложение
        self.app = FastAPI(
            title="STT Telegram Bot",
            description="Speech-to-Text Telegram Bot using Groq Whisper API",
            version="0.1.0",
            lifespan=self.lifespan,
        )

        # Настраиваем маршруты
        self._setup_routes()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncIterator[None]:
        """Управление жизненным циклом приложения."""
        # Startup
        if settings.use_webhook:
            await self._setup_webhook()
        yield
        # Shutdown
        await self.bot.session.close()

    async def _setup_webhook(self) -> None:
        """Настраивает webhook для бота."""
        try:
            await self.bot.set_webhook(
                url=settings.webhook_url,
                drop_pending_updates=True,
                secret_token=settings.webhook_secret,
            )
            logger.info(f"Webhook установлен: {settings.webhook_url}")
        except Exception as e:
            logger.error(f"Не удалось установить webhook: {e}")
            raise

    def _setup_routes(self) -> None:
        """Настраивает маршруты FastAPI."""

        @self.app.get("/")  # type: ignore[misc]
        async def health_check() -> dict[str, str]:
            """Health check endpoint."""
            return {"status": "ok", "message": "STT Telegram Bot is running"}

        @self.app.post(f"/tg/{settings.webhook_secret}")  # type: ignore[misc]
        async def webhook_handler(
            request: Request, x_telegram_bot_api_secret_token: str = Header(None)
        ) -> dict[str, str]:
            """
            Webhook endpoint для обработки обновлений от Telegram.

            Args:
                request: HTTP запрос
                x_telegram_bot_api_secret_token: Секретный токен от Telegram

            Returns:
                Статус обработки

            Raises:
                HTTPException: При неверном секретном токене
            """
            # Проверяем секретный токен
            if x_telegram_bot_api_secret_token != settings.webhook_secret:
                logger.warning(
                    f"Неверный секретный токен: {x_telegram_bot_api_secret_token}"
                )
                raise HTTPException(status_code=403, detail="Invalid secret token")

            try:
                # Получаем JSON данные
                json_data = await request.json()

                # Создаём Update объект
                update = Update.model_validate(json_data)

                # Передаём обновление диспетчеру
                await self.dispatcher.feed_update(self.bot, update)

                return {"status": "ok"}

            except Exception as e:
                logger.error(f"Ошибка при обработке webhook: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

    def get_app(self) -> FastAPI:
        """Возвращает FastAPI приложение."""
        return self.app


# Создаём глобальный экземпляр приложения
webhook_app = WebhookApp()
app = webhook_app.get_app()
