"""Utilities for preparing text for TTS."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from stt_tg_bot.utils.emoji_filter import replace_emojis_with_space


class TtsTextError(Enum):
    """Validation errors for TTS input text."""

    EMPTY = "empty"
    TOO_LONG = "too_long"


@dataclass(frozen=True)
class TtsTextResult:
    """Result of preparing TTS text."""

    text: str | None
    error: TtsTextError | None


def clean_tts_text(text: str) -> str:
    """Remove emojis and normalize whitespace for TTS."""
    no_emojis = replace_emojis_with_space(text)
    normalized = re.sub(r"\s+", " ", no_emojis, flags=re.UNICODE).strip()
    return normalized


def prepare_tts_text(raw_text: str, max_chars: int) -> TtsTextResult:
    """Prepare raw text for TTS with validation."""
    cleaned = clean_tts_text(raw_text or "")

    if not cleaned:
        return TtsTextResult(text=None, error=TtsTextError.EMPTY)

    if len(cleaned) > max_chars:
        return TtsTextResult(text=None, error=TtsTextError.TOO_LONG)

    return TtsTextResult(text=cleaned, error=None)
