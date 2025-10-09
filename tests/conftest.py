"""Pytest configuration and fixtures."""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

try:
    from aiogram.types import User
except ModuleNotFoundError:  # pragma: no cover - executed only when aiogram absent
    @dataclass
    class User:
        """Minimal stub to satisfy tests when aiogram is unavailable."""

        id: int
        is_bot: bool
        first_name: str
        last_name: str | None = None
        username: str | None = None


@pytest.fixture
def mock_user() -> User:
    """Create a mock User object."""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
    )


@pytest.fixture
def mock_user_no_username() -> User:
    """Create a mock User object without username."""
    return User(id=123456789, is_bot=False, first_name="Test", last_name="User")


@pytest.fixture
def mock_message():
    """Create a mock Message object."""
    message = MagicMock()
    message.message_id = 1
    message.date = 1234567890
    message.chat.id = 123456789
    message.chat.type = "private"
    message.from_user = User(id=123456789, is_bot=False, first_name="Test")
    message.text = "/start"
    return message
