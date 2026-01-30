"""Utilities for extracting text from Telegram messages."""

from __future__ import annotations


def get_message_text(message) -> str:
    """Return message text or caption, preferring text."""
    return (
        getattr(message, "text", None) or getattr(message, "caption", None) or ""
    ).strip()
