"""Pytest configuration and fixtures."""

from unittest.mock import MagicMock

import pytest
from aiogram.types import User


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
