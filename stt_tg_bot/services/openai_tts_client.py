"""OpenAI TTS client for text-to-speech generation."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from stt_tg_bot.config.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAITtsError(Exception):
    """Base error for OpenAI TTS."""


class OpenAITtsConfigError(OpenAITtsError):
    """Configuration error for OpenAI TTS."""


class OpenAITtsRequestError(OpenAITtsError):
    """Client request error for OpenAI TTS."""


class OpenAITtsServiceError(OpenAITtsError):
    """Service-side error for OpenAI TTS."""


class OpenAITtsClient:
    """Client for OpenAI Text-to-Speech API."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.model = self.settings.openai_tts_model
        self.voice = self.settings.openai_tts_voice
        self.response_format = self.settings.openai_tts_response_format
        self.timeout = float(self.settings.read_timeout_sec)

    async def synthesize(
        self,
        text: str,
        model: str | None = None,
        voice: str | None = None,
    ) -> bytes:
        """Synthesize text into audio bytes."""
        if not self.api_key:
            raise OpenAITtsConfigError("OpenAI API key is missing")

        payload = self._build_payload(text=text, model=model, voice=voice)
        response = await self._post_audio_speech(payload)

        if response.status_code == 200:
            if not response.content:
                raise OpenAITtsServiceError("Empty audio content received")
            return response.content

        if response.status_code in {429, 500, 502, 503, 504}:
            logger.warning(
                "OpenAI TTS service error: %s %s",
                response.status_code,
                response.text,
            )
            raise OpenAITtsServiceError("OpenAI TTS service error")

        if 400 <= response.status_code < 500:
            logger.error(
                "OpenAI TTS request error: %s %s",
                response.status_code,
                response.text,
            )
            raise OpenAITtsRequestError("OpenAI TTS request error")

        logger.error(
            "Unexpected OpenAI TTS response: %s %s",
            response.status_code,
            response.text,
        )
        raise OpenAITtsServiceError("Unexpected OpenAI TTS response")

    def _build_payload(
        self, text: str, model: str | None = None, voice: str | None = None
    ) -> dict[str, Any]:
        return {
            "model": model or self.model,
            "input": text,
            "voice": voice or self.voice,
            "response_format": self.response_format,
        }

    async def _post_audio_speech(self, payload: dict[str, Any]) -> httpx.Response:
        url = f"{self.base_url}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(url, headers=headers, json=payload)
