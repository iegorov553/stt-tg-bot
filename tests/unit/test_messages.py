"""Tests for messages module."""

from stt_tg_bot.utils.messages import MESSAGES


class TestMessages:
    """Tests for message constants."""

    def test_all_messages_exist(self) -> None:
        """Test that all expected messages exist."""
        expected_keys = {
            "start",
            "help",
            "processing",
            "access_denied",
            "unsupported_format",
            "service_unavailable",
            "timeout_error",
            "download_error",
            "general_error",
            "empty_transcription",
        }

        assert set(MESSAGES.keys()) == expected_keys

    def test_messages_are_strings(self) -> None:
        """Test that all messages are non-empty strings."""
        for key, message in MESSAGES.items():
            assert isinstance(message, str), f"Message '{key}' is not a string"
            assert len(message) > 0, f"Message '{key}' is empty"

    def test_specific_messages_content(self) -> None:
        """Test specific message content."""
        assert "Привет" in MESSAGES["start"]
        assert "расшифровки" in MESSAGES["start"]

        assert "команды" in MESSAGES["help"]
        assert "/start" in MESSAGES["help"]
        assert "/help" in MESSAGES["help"]

        assert "Обрабатываю" in MESSAGES["processing"]

        assert "Доступ ограничен" in MESSAGES["access_denied"]

        assert "файл" in MESSAGES["unsupported_format"]
        assert "недоступен" in MESSAGES["service_unavailable"]
        assert "ожидание" in MESSAGES["timeout_error"]
