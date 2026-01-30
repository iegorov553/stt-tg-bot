"""Tests for emoji filtering utilities."""

from stt_tg_bot.utils.emoji_filter import replace_emojis_with_space


def test_replace_emojis_with_space_removes_emojis() -> None:
    """Ensure emojis are removed and surrounding text is preserved."""
    text = "Привет😀мир"
    result = replace_emojis_with_space(text)

    assert "😀" not in result
    assert result == "Привет мир"


def test_replace_emojis_with_space_handles_multiple_emojis() -> None:
    """Ensure multiple emojis are removed in one pass."""
    text = "Тест 👩‍💻✅ ок"
    result = replace_emojis_with_space(text)

    assert "👩" not in result
    assert "💻" not in result
    assert "✅" not in result
