"""Tests for Telegram text chunk helpers."""

import pytest

from stt_tg_bot.utils.text_chunks import TELEGRAM_MAX_MESSAGE_LENGTH, split_text


def test_split_text_empty_without_prefix():
    assert split_text("") == []


def test_split_text_empty_with_prefix():
    assert split_text("", prefix="Header") == ["Header"]


def test_split_text_prefix_respected():
    chunks = split_text("abcdef", max_len=4, prefix=">>")
    assert chunks == [">>ab", "cdef"]


def test_split_text_chunks_at_limit():
    text = "a" * (TELEGRAM_MAX_MESSAGE_LENGTH + 10)
    chunks = split_text(text)
    assert len(chunks) == 2
    assert len(chunks[0]) == TELEGRAM_MAX_MESSAGE_LENGTH
    assert len(chunks[1]) == 10


def test_split_text_raises_when_prefix_too_long():
    with pytest.raises(ValueError):
        split_text("data", max_len=5, prefix="x" * 6)
