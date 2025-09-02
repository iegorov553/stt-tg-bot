"""Tests for access control utilities."""

from unittest.mock import MagicMock, patch

import pytest
from aiogram.types import Message, User

from stt_tg_bot.utils.access_control import (
    check_message_access,
    is_user_allowed,
    send_access_denied_message,
)


class TestAccessControl:
    """Tests for access control functions."""

    @patch("stt_tg_bot.utils.access_control.settings")
    def test_is_user_allowed_by_id(self, mock_settings: MagicMock) -> None:
        """Test user allowed by ID."""
        mock_settings.parsed_allowlist = {"123456789", "@testuser"}

        user = User(id=123456789, is_bot=False, first_name="Test")
        assert is_user_allowed(user) is True

    @patch("stt_tg_bot.utils.access_control.settings")
    def test_is_user_allowed_by_username_with_at(
        self, mock_settings: MagicMock
    ) -> None:
        """Test user allowed by username with @."""
        mock_settings.parsed_allowlist = {"123456789", "@testuser"}

        user = User(id=987654321, is_bot=False, first_name="Test", username="testuser")
        assert is_user_allowed(user) is True

    @patch("stt_tg_bot.utils.access_control.settings")
    def test_is_user_allowed_by_username_without_at(
        self, mock_settings: MagicMock
    ) -> None:
        """Test user allowed by username without @."""
        mock_settings.parsed_allowlist = {"123456789", "testuser"}

        user = User(id=987654321, is_bot=False, first_name="Test", username="testuser")
        assert is_user_allowed(user) is True

    @patch("stt_tg_bot.utils.access_control.settings")
    def test_is_user_not_allowed(self, mock_settings: MagicMock) -> None:
        """Test user not in allowlist."""
        mock_settings.parsed_allowlist = {"123456789", "@testuser"}

        user = User(
            id=987654321, is_bot=False, first_name="Test", username="anotheruser"
        )
        assert is_user_allowed(user) is False

    @patch("stt_tg_bot.utils.access_control.settings")
    def test_is_user_allowed_no_username(self, mock_settings: MagicMock) -> None:
        """Test user with no username."""
        mock_settings.parsed_allowlist = {"123456789", "@testuser"}

        user = User(id=123456789, is_bot=False, first_name="Test")
        assert is_user_allowed(user) is True

        user_not_allowed = User(id=987654321, is_bot=False, first_name="Test")
        assert is_user_allowed(user_not_allowed) is False

    def test_check_message_access_no_user(self) -> None:
        """Test check_message_access with no user."""
        message = MagicMock(spec=Message)
        message.from_user = None

        assert check_message_access(message) is False

    @patch("stt_tg_bot.utils.access_control.is_user_allowed")
    def test_check_message_access_allowed(
        self, mock_is_user_allowed: MagicMock
    ) -> None:
        """Test check_message_access with allowed user."""
        mock_is_user_allowed.return_value = True

        message = MagicMock(spec=Message)
        message.from_user = User(id=123456789, is_bot=False, first_name="Test")

        assert check_message_access(message) is True
        mock_is_user_allowed.assert_called_once_with(message.from_user)

    @patch("stt_tg_bot.utils.access_control.is_user_allowed")
    def test_check_message_access_not_allowed(
        self, mock_is_user_allowed: MagicMock
    ) -> None:
        """Test check_message_access with not allowed user."""
        mock_is_user_allowed.return_value = False

        message = MagicMock(spec=Message)
        message.from_user = User(id=123456789, is_bot=False, first_name="Test")

        assert check_message_access(message) is False

    @pytest.mark.asyncio
    async def test_send_access_denied_message(self) -> None:
        """Test send_access_denied_message."""
        message = MagicMock(spec=Message)
        message.reply = MagicMock(return_value=None)

        await send_access_denied_message(message)

        message.reply.assert_called_once_with(
            "Доступ ограничен. Обратитесь к владельцу бота."
        )
