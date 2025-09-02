"""Access control utilities for allowlist management."""

from aiogram.types import Message, User

from stt_tg_bot.config.settings import settings


def is_user_allowed(user: User) -> bool:
    """
    Проверяет, разрешён ли доступ пользователю.

    Проверяет по user ID и username в allowlist из настроек.

    Args:
        user: Пользователь Telegram

    Returns:
        True если пользователь в allowlist, False иначе
    """
    allowlist = settings.parsed_allowlist

    # Проверяем по ID пользователя
    if str(user.id) in allowlist:
        return True

    # Проверяем по username (с @ и без)
    if user.username:
        if f"@{user.username}" in allowlist or user.username in allowlist:
            return True

    return False


def check_message_access(message: Message) -> bool:
    """
    Проверяет доступ для сообщения.

    Args:
        message: Сообщение Telegram

    Returns:
        True если доступ разрешён, False иначе
    """
    if not message.from_user:
        return False

    return is_user_allowed(message.from_user)


async def send_access_denied_message(message: Message) -> None:
    """
    Отправляет сообщение об ограниченном доступе.

    Args:
        message: Исходное сообщение пользователя
    """
    ACCESS_DENIED_MESSAGE = "Доступ ограничен. Обратитесь к владельцу бота."
    await message.reply(ACCESS_DENIED_MESSAGE)
