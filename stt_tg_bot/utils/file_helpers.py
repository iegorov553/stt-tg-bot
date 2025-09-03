"""File handling utilities for transcription results."""

import tempfile
from datetime import datetime
from pathlib import Path

import aiofiles


def should_send_as_file(transcription: str, audio_duration_seconds: float = 0) -> bool:
    """
    Определяет, нужно ли отправлять результат как файл.

    Args:
        transcription: Текст транскрипции
        audio_duration_seconds: Длительность аудио в секундах

    Returns:
        True если нужно отправить как файл + превью
    """
    # Если аудио длиннее 5 минут (300 секунд)
    if audio_duration_seconds > 300:
        return True

    # Если текст длиннее 2000 символов
    if len(transcription) > 2000:
        return True

    return False


def create_preview(transcription: str, max_length: int = 500) -> str:
    """
    Создаёт превью текста для предварительного просмотра.

    Args:
        transcription: Полный текст транскрипции
        max_length: Максимальная длина превью

    Returns:
        Обрезанный текст с многоточием если нужно
    """
    if len(transcription) <= max_length:
        return transcription

    # Обрезаем по словам, а не по символам
    words = transcription[:max_length].split()
    # Убираем последнее слово если оно обрезана
    if len(" ".join(words)) >= max_length:
        words = words[:-1]

    return " ".join(words) + "..."


async def create_transcription_file(transcription: str) -> Path:
    """
    Создаёт временный файл с транскрипцией.

    Args:
        transcription: Текст для сохранения

    Returns:
        Путь к созданному файлу
    """
    # Создаём имя файла с текущей датой и временем
    now = datetime.now()
    filename = f"transcription_{now.strftime('%Y-%m-%d_%H-%M')}.txt"

    # Создаём временный файл
    temp_dir = Path(tempfile.gettempdir())
    file_path = temp_dir / filename

    # Записываем содержимое
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(transcription)

    return file_path


def format_transcription_stats(
    transcription: str, audio_duration_seconds: float = 0
) -> str:
    """
    Форматирует статистику транскрипции для отображения.

    Args:
        transcription: Текст транскрипции
        audio_duration_seconds: Длительность аудио в секундах

    Returns:
        Отформатированная строка со статистикой
    """
    word_count = len(transcription.split())
    char_count = len(transcription)

    stats = f"{word_count} слов"

    if audio_duration_seconds > 0:
        minutes = int(audio_duration_seconds // 60)
        seconds = int(audio_duration_seconds % 60)
        if minutes > 0:
            stats += f", {minutes}:{seconds:02d} мин"
        else:
            stats += f", {seconds} сек"

    if char_count > 1000:
        stats += f", {char_count // 1000}k символов"
    else:
        stats += f", {char_count} символов"

    return stats


def get_audio_duration_from_message(message) -> float:
    """
    Извлекает длительность аудио из сообщения Telegram.

    Args:
        message: Объект сообщения aiogram

    Returns:
        Длительность в секундах или 0 если не определено
    """
    if message.voice and message.voice.duration:
        return float(message.voice.duration)
    elif message.audio and message.audio.duration:
        return float(message.audio.duration)
    elif message.document:
        # Для документов длительность может быть недоступна
        return 0.0

    return 0.0
