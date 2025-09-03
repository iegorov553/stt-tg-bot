"""Telegram bot handlers for commands and audio processing."""

import logging
import tempfile
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from stt_tg_bot.services.groq_client import (
    GroqServiceUnavailableError,
    GroqTimeout,
    GroqUnsupportedFormatError,
    transcribe_with_fallback,
)
from stt_tg_bot.utils.access_control import (
    check_message_access,
    send_access_denied_message,
)
from stt_tg_bot.utils.messages import MESSAGES

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))  # type: ignore[misc]
async def start_command(message: Message) -> None:
    """
    Обработчик команды /start.

    Args:
        message: Сообщение пользователя
    """
    if not check_message_access(message):
        await send_access_denied_message(message)
        return

    await message.reply(MESSAGES["start"])


@router.message(Command("help"))  # type: ignore[misc]
async def help_command(message: Message) -> None:
    """
    Обработчик команды /help.

    Args:
        message: Сообщение пользователя
    """
    if not check_message_access(message):
        await send_access_denied_message(message)
        return

    await message.reply(MESSAGES["help"])


@router.message(F.voice | F.audio | F.document)  # type: ignore[misc]
async def handle_audio(message: Message, bot: Bot) -> None:
    """
    Обработчик аудио сообщений (голосовые, аудио, документы).

    Args:
        message: Сообщение с аудио
        bot: Экземпляр бота
    """
    if not check_message_access(message):
        await send_access_denied_message(message)
        return

    # Отправляем сообщение о начале обработки
    processing_message = await message.reply(MESSAGES["processing"])

    # Включаем typing индикатор
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Определяем тип файла и получаем file_id
        if message.voice:
            file_id = message.voice.file_id
            logger.info(f"Обрабатываем voice сообщение: {file_id}")
        elif message.audio:
            file_id = message.audio.file_id
            logger.info(f"Обрабатываем audio файл: {file_id}")
        elif message.document:
            file_id = message.document.file_id
            logger.info(f"Обрабатываем document: {file_id}")
        else:
            logger.warning("Получен неподдерживаемый тип сообщения")
            await processing_message.edit_text(MESSAGES["unsupported_format"])
            return

        # Получаем информацию о файле
        try:
            file_info = await bot.get_file(file_id)
            logger.info(f"Информация о файле: {file_info.file_path}")
        except Exception as e:
            logger.error(f"Не удалось получить информацию о файле: {e}")
            await processing_message.edit_text(MESSAGES["download_error"])
            return

        if not file_info.file_path:
            logger.error("Путь к файлу отсутствует")
            await processing_message.edit_text(MESSAGES["download_error"])
            return

        # Определяем правильное расширение файла
        file_extension = ".ogg"  # По умолчанию для голосовых сообщений
        if message.audio and message.audio.file_name:
            # Для аудиофайлов берём оригинальное расширение
            original_name = Path(message.audio.file_name)
            file_extension = original_name.suffix or ".mp3"
        elif message.document and message.document.file_name:
            # Для документов тоже берём оригинальное расширение
            original_name = Path(message.document.file_name)
            file_extension = original_name.suffix or ".mp3"

        # Скачиваем файл во временную директорию с правильным расширением
        with tempfile.NamedTemporaryFile(
            suffix=file_extension, delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            await bot.download_file(file_info.file_path, temp_path)
            logger.info(f"Файл скачан: {temp_path}")

            # Транскрибируем аудио с fallback
            transcription = await transcribe_with_fallback(temp_path)

            if not transcription:
                await processing_message.edit_text(MESSAGES["empty_transcription"])
                return

            # Отправляем результат
            # Если транскрипция очень длинная, разбиваем на части
            max_length = 4000  # Оставляем запас от лимита в 4096 символов

            if len(transcription) <= max_length:
                await processing_message.edit_text(transcription)
            else:
                # Удаляем служебное сообщение
                await processing_message.delete()

                # Отправляем по частям
                parts = []
                for i in range(0, len(transcription), max_length):
                    part = transcription[i : i + max_length]
                    parts.append(part)

                for i, part in enumerate(parts):
                    if i == 0:
                        await message.reply(f"📝 Часть {i+1}/{len(parts)}:\n\n{part}")
                    else:
                        await message.answer(f"📝 Часть {i+1}/{len(parts)}:\n\n{part}")

        except GroqUnsupportedFormatError:
            logger.warning("Неподдерживаемый формат файла")
            await processing_message.edit_text(MESSAGES["unsupported_format"])

        except GroqServiceUnavailableError:
            logger.error("Сервис Groq недоступен")
            await processing_message.edit_text(MESSAGES["service_unavailable"])

        except GroqTimeout:
            logger.error("Таймаут при обращении к Groq")
            await processing_message.edit_text(MESSAGES["timeout_error"])

        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке аудио: {e}")
            await processing_message.edit_text(MESSAGES["general_error"])

        finally:
            # Удаляем временный файл
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f"Удален временный файл: {temp_path}")

    except Exception as e:
        logger.error(f"Критическая ошибка в обработчике аудио: {e}")
        try:
            await processing_message.edit_text(MESSAGES["general_error"])
        except Exception:  # nosec B110 - игнорируем ошибки UI для стабильности
            pass  # Игнорируем ошибки при редактировании сообщения


@router.message()  # type: ignore[misc]
async def handle_other_messages(message: Message) -> None:
    """
    Обработчик всех остальных сообщений.

    Args:
        message: Сообщение пользователя
    """
    if not check_message_access(message):
        await send_access_denied_message(message)
        return

    # Игнорируем все остальные типы сообщений
    # (согласно ТЗ, никаких дополнительных ответов не нужно)
    pass


def setup_handlers(dp: Dispatcher) -> None:
    """
    Регистрирует все хендлеры в диспетчере.

    Args:
        dp: Диспетчер aiogram
    """
    dp.include_router(router)
