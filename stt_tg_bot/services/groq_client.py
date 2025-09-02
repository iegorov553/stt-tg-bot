"""Groq Whisper API client for speech transcription."""

import logging
from pathlib import Path

import aiofiles
from groq import AsyncGroq, BadRequestError, InternalServerError, RateLimitError

from stt_tg_bot.config.settings import settings

logger = logging.getLogger(__name__)


class GroqTranscriptionError(Exception):
    """Базовая ошибка транскрипции Groq."""

    pass


class GroqUnsupportedFormatError(GroqTranscriptionError):
    """Ошибка неподдерживаемого формата файла."""

    pass


class GroqServiceUnavailableError(GroqTranscriptionError):
    """Ошибка недоступности сервиса Groq."""

    pass


class GroqTimeout(GroqTranscriptionError):
    """Ошибка таймаута при обращении к Groq."""

    pass


class GroqWhisperClient:
    """Клиент для работы с Groq Whisper API."""

    def __init__(self) -> None:
        """Инициализация клиента Groq."""
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def transcribe_audio(
        self, audio_file_path: Path, use_fallback: bool = False
    ) -> str:
        """
        Транскрибирует аудиофайл с помощью Groq Whisper.

        Args:
            audio_file_path: Путь к аудиофайлу
            use_fallback: Использовать fallback модель

        Returns:
            Текст транскрипции

        Raises:
            GroqUnsupportedFormatError: Неподдерживаемый формат файла
            GroqServiceUnavailableError: Сервис недоступен
            GroqTimeout: Таймаут при обработке
        """
        model = (
            settings.groq_model_fallback
            if use_fallback
            else settings.groq_model_primary
        )

        try:
            async with aiofiles.open(audio_file_path, "rb") as audio_file:
                logger.info(f"Transcribing with model: {model}")

                # Читаем содержимое файла для передачи в Groq API
                file_content = await audio_file.read()

                transcription = await self.client.audio.transcriptions.create(
                    file=(audio_file_path.name, file_content),
                    model=model,
                    language="ru",
                    response_format="text",
                )

                transcription_text = str(transcription)
                if not transcription_text or not transcription_text.strip():
                    logger.warning("Получена пустая транскрипция")
                    return ""

                logger.info("Транскрипция успешно выполнена")
                return transcription_text.strip()

        except BadRequestError as e:
            logger.error(f"Ошибка формата файла: {e}")
            if "unsupported" in str(e).lower() or "format" in str(e).lower():
                raise GroqUnsupportedFormatError("Неподдерживаемый формат аудиофайла")
            raise GroqTranscriptionError(f"Ошибка запроса: {e}")

        except (InternalServerError, RateLimitError) as e:
            logger.error(f"Ошибка сервиса Groq: {e}")
            raise GroqServiceUnavailableError("Сервис временно недоступен")

        except Exception as e:
            logger.error(f"Неизвестная ошибка при транскрипции: {e}")
            raise GroqTranscriptionError(f"Ошибка транскрипции: {e}")


async def transcribe_with_fallback(audio_file_path: Path) -> str:
    """
    Транскрибирует аудио с автоматическим fallback на резервную модель.

    Args:
        audio_file_path: Путь к аудиофайлу

    Returns:
        Текст транскрипции

    Raises:
        GroqUnsupportedFormatError: Неподдерживаемый формат файла
        GroqServiceUnavailableError: Оба сервиса недоступны
        GroqTimeout: Таймаут при обработке
    """
    client = GroqWhisperClient()

    try:
        # Пытаемся с основной моделью
        return await client.transcribe_audio(audio_file_path, use_fallback=False)

    except (GroqServiceUnavailableError, GroqTranscriptionError) as primary_error:
        logger.warning(f"Основная модель недоступна: {primary_error}")

        # Если основная модель недоступна, пробуем fallback
        try:
            logger.info("Пытаемся с fallback моделью")
            return await client.transcribe_audio(audio_file_path, use_fallback=True)

        except GroqUnsupportedFormatError:
            # Если формат неподдерживается, нет смысла пытаться с другой моделью
            raise

        except Exception as fallback_error:
            logger.error(f"Fallback модель тоже недоступна: {fallback_error}")
            raise GroqServiceUnavailableError("Все модели недоступны")
