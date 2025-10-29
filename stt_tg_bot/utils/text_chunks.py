"""Helpers for splitting long messages into Telegram-safe chunks."""

from __future__ import annotations

from typing import Any, AsyncIterator, Awaitable, Callable


TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def split_text(
    text: str, max_len: int = TELEGRAM_MAX_MESSAGE_LENGTH, prefix: str = ""
) -> list[str]:
    """
    Split the given text into chunks that fit Telegram message limits.

    Args:
        text: исходный текст для отправки.
        max_len: максимальная длина одного сообщения Telegram.
        prefix: (опционально) префикс, который будет добавлен к первой части.

    Returns:
        Список частей в правильном порядке.
    """
    if not text:
        return [prefix] if prefix else []

    first_chunk_budget = max_len - len(prefix)
    if first_chunk_budget <= 0:
        raise ValueError("Prefix length exceeds maximum Telegram message length")

    chunks: list[str] = []
    start_idx = 0
    current_budget = first_chunk_budget

    while start_idx < len(text):
        end_idx = min(start_idx + current_budget, len(text))
        chunk = text[start_idx:end_idx]
        chunks.append(chunk)
        start_idx = end_idx
        current_budget = max_len

    if chunks:
        chunks[0] = f"{prefix}{chunks[0]}"
    elif prefix:
        chunks.append(prefix)

    return chunks


async def send_chunked_messages(
    send_fn: Callable[[str], Awaitable[Any]],
    text: str,
    prefix: str = "",
    max_len: int = TELEGRAM_MAX_MESSAGE_LENGTH,
) -> AsyncIterator[Any]:
    """
    Send text split into Telegram-friendly chunks using provided async function.

    Args:
        send_fn: асинхронная функция отправки (например, message.reply или message.answer).
        text: текст для отправки.
        prefix: произвольный префикс для первой части (например, «📝 Часть 1/3:\n\n»).
        max_len: максимальная длина одного сообщения.

    Yields:
        Результаты вызова send_fn для каждой части.
    """
    chunks = split_text(text, max_len=max_len, prefix=prefix)
    for chunk in chunks:
        yield await send_fn(chunk)
