"""Tests for TTS text preparation utilities."""

from stt_tg_bot.utils.tts_text import TtsTextError, clean_tts_text, prepare_tts_text


def test_clean_tts_text_removes_emojis_and_normalizes_spaces() -> None:
    """Ensure emoji removal and whitespace normalization."""
    raw = "  Привет😀   мир  "
    assert clean_tts_text(raw) == "Привет мир"


def test_prepare_tts_text_returns_empty_error() -> None:
    """Ensure empty result after cleaning triggers EMPTY error."""
    result = prepare_tts_text("😀😀", max_chars=10)

    assert result.text is None
    assert result.error == TtsTextError.EMPTY


def test_prepare_tts_text_returns_too_long_error() -> None:
    """Ensure too-long text triggers TOO_LONG error."""
    result = prepare_tts_text("a" * 11, max_chars=10)

    assert result.text is None
    assert result.error == TtsTextError.TOO_LONG


def test_prepare_tts_text_success() -> None:
    """Ensure valid text passes through."""
    result = prepare_tts_text("Привет, мир", max_chars=50)

    assert result.text == "Привет, мир"
    assert result.error is None
