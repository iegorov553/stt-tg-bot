"""Emoji filtering utilities."""

from __future__ import annotations

import re


_EMOJI_RANGES = (
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f700-\U0001f77f"  # alchemical symbols
    "\U0001f780-\U0001f7ff"  # geometric shapes extended
    "\U0001f800-\U0001f8ff"  # supplemental arrows
    "\U0001f900-\U0001f9ff"  # supplemental symbols & pictographs
    "\U0001fa00-\U0001fa6f"  # chess symbols and more
    "\U0001fa70-\U0001faff"  # symbols and pictographs extended
    "\U00002700-\U000027bf"  # dingbats
    "\U00002600-\U000026ff"  # miscellaneous symbols
    "\U000024c2-\U0001f251"  # enclosed characters
    "\U0001f3fb-\U0001f3ff"  # skin tone modifiers
    "\u200d"  # zero width joiner
    "\ufe0f"  # variation selector
)

_EMOJI_PATTERN = re.compile(f"[{_EMOJI_RANGES}]", flags=re.UNICODE)


def replace_emojis_with_space(text: str) -> str:
    """Replace emojis in the text with spaces."""
    return _EMOJI_PATTERN.sub(" ", text)
