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
from stt_tg_bot.utils.access_control import check_message_access, send_access_denied_message
from stt_tg_bot.utils.messages import MESSAGES
from stt_tg_bot.utils.text_chunks import TELEGRAM_MAX_MESSAGE_LENGTH, split_text

logger = logging.getLogger(__name__)

router = Router()

CHUNK_HEADER_TEMPLATE = "📝 Часть {current}/{total}:\n\n"
CHUNK_HEADER_RESERVE = len("📝 Часть 999/999:\n\n")


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
    processing_message_deleted = False

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
            logger.info(
                f"Информация о файле: {file_info.file_path}, размер: {file_info.file_size}"
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Не удалось получить информацию о файле: {error_msg}")

            # Специальная обработка для больших файлов
            if "file is too big" in error_msg.lower():
                # Получаем расширение файла для генерации URL
                from stt_tg_bot.utils.file_helpers import (
                    get_file_extension_from_message,
                    generate_compression_url,
                )

                file_extension = get_file_extension_from_message(message)
                compress_url = generate_compression_url(file_extension)

                # Отправляем сообщение с предложением сжать файл
                large_file_message = MESSAGES["file_too_large"].format(
                    compress_url=compress_url
                )
                await processing_message.edit_text(
                    large_file_message, disable_web_page_preview=True
                )
            else:
                await processing_message.edit_text(MESSAGES["download_error"])
            return

        if not file_info.file_path:
            logger.error("Путь к файлу отсутствует")
            await processing_message.edit_text(MESSAGES["download_error"])
            return

        # Проверяем размер файла (20 МБ = 20 * 1024 * 1024 байт)
        max_file_size = 20 * 1024 * 1024
        if file_info.file_size and file_info.file_size > max_file_size:
            logger.info(f"Файл слишком большой: {file_info.file_size} байт")

            # Получаем расширение файла для генерации URL
            from stt_tg_bot.utils.file_helpers import (
                get_file_extension_from_message,
                generate_compression_url,
            )

            file_extension = get_file_extension_from_message(message)
            compress_url = generate_compression_url(file_extension)

            # Отправляем сообщение с предложением сжать файл
            large_file_message = MESSAGES["file_too_large"].format(
                compress_url=compress_url
            )
            await processing_message.edit_text(
                large_file_message, disable_web_page_preview=True
            )
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

            # Определяем длительность аудио
            from stt_tg_bot.utils.file_helpers import (
                create_transcription_file,
                format_transcription_stats,
                get_audio_duration_from_message,
                should_send_as_file,
            )

            audio_duration = get_audio_duration_from_message(message)

            # Проверяем нужно ли отправить как файл
            if should_send_as_file(transcription, audio_duration):
                # Создаём файл с полной транскрипцией
                file_path = await create_transcription_file(transcription)

                try:
                    # Создаём саммари или превью через OpenAI
                    from stt_tg_bot.utils.file_helpers import create_summary_or_preview

                    preview_content, used_openai = await create_summary_or_preview(
                        transcription
                    )
                    stats = format_transcription_stats(transcription, audio_duration)

                    # Формируем сообщение в зависимости от того, использовался ли OpenAI
                    if used_openai:
                        preview_message = (
                            f"📝 **Расшифровка готова!** ({stats})\n\n"
                            f"📋 **Краткое содержание:**\n{preview_content}"
                        )
                    else:
                        preview_message = (
                            f"📝 **Расшифровка готова!** ({stats})\n\n"
                            f"⚠️ OpenAI API недоступен, показываю превью:\n\n{preview_content}"
                        )

                    # Удаляем служебное сообщение
                    await processing_message.delete()
                    processing_message_deleted = True

                    # Отправляем превью
                    preview_chunks = split_text(
                        preview_message, max_len=TELEGRAM_MAX_MESSAGE_LENGTH
                    )
                    if not preview_chunks:
                        preview_chunks = [preview_message]
                    for idx, chunk in enumerate(preview_chunks):
                        send_method = message.reply if idx == 0 else message.answer
                        await send_method(chunk, parse_mode="Markdown")

                    # Отправляем файл
                    from aiogram.types import FSInputFile

                    document = FSInputFile(file_path, filename=file_path.name)
                    await message.answer_document(
                        document, caption=f"📎 Полная расшифровка ({stats})"
                    )

                finally:
                    # Удаляем временный файл
                    try:
                        file_path.unlink()
                    except Exception:
                        pass  # Игнорируем ошибки удаления

            else:
                # Отправляем обычным сообщением для коротких текстов
                if len(transcription) <= TELEGRAM_MAX_MESSAGE_LENGTH:
                    await processing_message.edit_text(transcription)
                else:
                    # Разбиваем на части (резервный вариант)
                    await processing_message.delete()
                    processing_message_deleted = True

                    chunks = split_text(
                        transcription,
                        max_len=TELEGRAM_MAX_MESSAGE_LENGTH - CHUNK_HEADER_RESERVE,
                    )
                    total_parts = max(1, len(chunks))
                    for index, chunk in enumerate(chunks, start=1):
                        header = CHUNK_HEADER_TEMPLATE.format(
                            current=index, total=total_parts
                        )
                        send_method = message.reply if index == 1 else message.answer
                        await send_method(f"{header}{chunk}")

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
            if not processing_message_deleted:
                await processing_message.edit_text(MESSAGES["general_error"])

        finally:
            # Удаляем временный файл
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f"Удален временный файл: {temp_path}")

    except Exception as e:
        logger.error(f"Критическая ошибка в обработчике аудио: {e}")
        if not processing_message_deleted:
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
