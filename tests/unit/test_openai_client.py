"""Unit tests for the OpenAI client."""

import pytest

from stt_tg_bot.services.openai_client import OpenAIClient


@pytest.mark.asyncio
async def test_post_chat_uses_max_completion_tokens(monkeypatch):
    """Ensure Chat Completions payload uses the new max_completion_tokens field."""
    client = OpenAIClient()
    captured_payload: dict[str, object] = {}

    async def fake_post(url: str, payload: dict, responses_api: bool = False):
        captured_payload.update(payload)
        return "ok", None

    monkeypatch.setattr(client, "_post_with_retries", fake_post)

    summary, err = await client._post_chat("prompt", "test-model", 256)

    assert summary == "ok"
    assert err is None
    assert captured_payload["max_completion_tokens"] == 256
    assert "max_tokens" not in captured_payload


@pytest.mark.asyncio
async def test_post_responses_uses_max_output_tokens(monkeypatch):
    """Ensure Responses API payload retains max_output_tokens."""
    client = OpenAIClient()
    captured_payload: dict[str, object] = {}

    async def fake_post(url: str, payload: dict, responses_api: bool = False):
        captured_payload.update(payload)
        return "ok", None

    monkeypatch.setattr(client, "_post_with_retries", fake_post)

    summary = await client._post_responses("prompt", "test-model", 512)

    assert summary == "ok"
    assert captured_payload["max_output_tokens"] == 512
