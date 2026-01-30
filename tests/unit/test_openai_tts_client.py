"""Unit tests for the OpenAI TTS client."""

import pytest

from stt_tg_bot.services.openai_tts_client import (
    OpenAITtsClient,
    OpenAITtsConfigError,
    OpenAITtsRequestError,
    OpenAITtsServiceError,
)


class _FakeResponse:
    def __init__(self, status_code: int, content: bytes = b"", text: str = "") -> None:
        self.status_code = status_code
        self.content = content
        self.text = text


@pytest.mark.asyncio
async def test_synthesize_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure successful synthesis returns audio bytes."""
    client = OpenAITtsClient()
    client.api_key = "test-key"

    async def fake_post(_payload: dict) -> _FakeResponse:
        return _FakeResponse(status_code=200, content=b"audio-bytes")

    monkeypatch.setattr(client, "_post_audio_speech", fake_post)

    result = await client.synthesize("Привет")

    assert result == b"audio-bytes"


@pytest.mark.asyncio
async def test_synthesize_missing_api_key() -> None:
    """Ensure missing API key raises config error."""
    client = OpenAITtsClient()
    client.api_key = None

    with pytest.raises(OpenAITtsConfigError):
        await client.synthesize("Привет")


@pytest.mark.asyncio
async def test_synthesize_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure 4xx responses raise request errors."""
    client = OpenAITtsClient()
    client.api_key = "test-key"

    async def fake_post(_payload: dict) -> _FakeResponse:
        return _FakeResponse(status_code=400, text="bad request")

    monkeypatch.setattr(client, "_post_audio_speech", fake_post)

    with pytest.raises(OpenAITtsRequestError):
        await client.synthesize("Привет")


@pytest.mark.asyncio
async def test_synthesize_service_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure 5xx/429 responses raise service errors."""
    client = OpenAITtsClient()
    client.api_key = "test-key"

    async def fake_post(_payload: dict) -> _FakeResponse:
        return _FakeResponse(status_code=503, text="unavailable")

    monkeypatch.setattr(client, "_post_audio_speech", fake_post)

    with pytest.raises(OpenAITtsServiceError):
        await client.synthesize("Привет")
