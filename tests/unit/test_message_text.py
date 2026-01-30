"""Tests for message text extraction utility."""

from dataclasses import dataclass

from stt_tg_bot.utils.message_text import get_message_text


@dataclass
class _DummyMessage:
    text: str | None = None
    caption: str | None = None


def test_get_message_text_prefers_text() -> None:
    """Text has priority over caption."""
    message = _DummyMessage(text="text", caption="caption")

    assert get_message_text(message) == "text"


def test_get_message_text_falls_back_to_caption() -> None:
    """Caption is used when text is missing."""
    message = _DummyMessage(text=None, caption="caption")

    assert get_message_text(message) == "caption"


def test_get_message_text_empty_when_missing() -> None:
    """Empty string when neither text nor caption is available."""
    message = _DummyMessage(text=None, caption=None)

    assert get_message_text(message) == ""
