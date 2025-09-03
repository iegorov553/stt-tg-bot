"""Main application entry point."""

import asyncio
import logging
import sys

import uvicorn
from aiogram import Bot, Dispatcher

from stt_tg_bot.config.settings import settings
from stt_tg_bot.handlers.bot_handlers import setup_handlers

# Настройка минимального логирования (только ошибки)
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Отключаем подробные логи сторонних библиотек
logging.getLogger("aiogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("uvicorn").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


async def run_polling() -> None:
    """Запускает бота в режиме long polling для локальной разработки."""
    logger.info("Запуск бота в режиме polling")

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    # Настраиваем хендлеры
    setup_handlers(dp)

    try:
        # Удаляем webhook если он был установлен
        await bot.delete_webhook(drop_pending_updates=True)

        # Запускаем polling
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


def run_webhook() -> None:
    """Запускает бота в режиме webhook для продакшена."""
    logger.info("Запуск бота в режиме webhook")

    uvicorn.run(
        "stt_tg_bot.services.webhook_server:app",
        host="0.0.0.0",  # nosec B104 - необходимо для Docker deployment
        port=settings.port,
        log_level="error",  # Минимальный уровень логирования
    )


def main() -> None:
    """Главная функция приложения."""
    if settings is None:
        import os
        from stt_tg_bot.config.settings import Settings

        logger.error("Настройки не инициализированы! Диагностика...")

        # Показываем что переменные есть
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "GROQ_API_KEY",
            "PUBLIC_BASE_URL",
            "WEBHOOK_SECRET",
            "ALLOWLIST",
        ]
        for var in required_vars:
            value = os.environ.get(var, "НЕ НАЙДЕНА")
            logger.error(
                f"{var}: {value[:10]}..."
                if value != "НЕ НАЙДЕНА" and len(value) > 10
                else f"{var}: {value}"
            )

        # Попробуем создать Settings и покажем ошибку
        try:
            logger.error("Пытаемся создать Settings...")
            Settings()
            logger.error("Settings созданы успешно!")
        except Exception as e:
            logger.error(f"Ошибка при создании Settings: {type(e).__name__}: {e}")

        sys.exit(1)

    if settings.use_webhook:
        run_webhook()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
