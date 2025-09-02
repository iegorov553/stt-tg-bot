"""Tests for Groq client."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from groq import BadRequestError, InternalServerError

from stt_tg_bot.services.groq_client import (
    GroqServiceUnavailableError,
    GroqTranscriptionError,
    GroqUnsupportedFormatError,
    GroqWhisperClient,
    transcribe_with_fallback,
)


class TestGroqWhisperClient:
    """Tests for GroqWhisperClient class."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.client = GroqWhisperClient()
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        self.temp_path = Path(self.temp_file.name)
        self.temp_file.close()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        if self.temp_path.exists():
            self.temp_path.unlink()

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.aiofiles.open")
    async def test_transcribe_audio_success(
        self, mock_aiofiles_open: MagicMock
    ) -> None:
        """Test successful audio transcription."""
        # Mock aiofiles.open
        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        # Mock Groq client response
        self.client.client.audio.transcriptions.create = AsyncMock(
            return_value="Это тестовая транскрипция."
        )

        result = await self.client.transcribe_audio(self.temp_path)

        assert result == "Это тестовая транскрипция."
        self.client.client.audio.transcriptions.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.aiofiles.open")
    async def test_transcribe_audio_empty_result(
        self, mock_aiofiles_open: MagicMock
    ) -> None:
        """Test transcription with empty result."""
        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        self.client.client.audio.transcriptions.create = AsyncMock(return_value="   ")

        result = await self.client.transcribe_audio(self.temp_path)

        assert result == ""

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.aiofiles.open")
    async def test_transcribe_audio_bad_request_unsupported_format(
        self, mock_aiofiles_open: MagicMock
    ) -> None:
        """Test transcription with unsupported format error."""
        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        # Create a proper BadRequestError with required arguments
        from httpx import Request, Response

        mock_request = Request("POST", "https://api.groq.com")
        mock_response = Response(400, request=mock_request)
        error = BadRequestError(
            "Unsupported file format", response=mock_response, body=None
        )
        self.client.client.audio.transcriptions.create = AsyncMock(side_effect=error)

        with pytest.raises(GroqUnsupportedFormatError):
            await self.client.transcribe_audio(self.temp_path)

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.aiofiles.open")
    async def test_transcribe_audio_internal_server_error(
        self, mock_aiofiles_open: MagicMock
    ) -> None:
        """Test transcription with internal server error."""
        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        # Create a proper InternalServerError with required arguments
        from httpx import Request, Response

        mock_request = Request("POST", "https://api.groq.com")
        mock_response = Response(500, request=mock_request)
        error = InternalServerError("Server error", response=mock_response, body=None)
        self.client.client.audio.transcriptions.create = AsyncMock(side_effect=error)

        with pytest.raises(GroqServiceUnavailableError):
            await self.client.transcribe_audio(self.temp_path)

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.aiofiles.open")
    async def test_transcribe_audio_generic_exception(
        self, mock_aiofiles_open: MagicMock
    ) -> None:
        """Test transcription with generic exception."""
        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        self.client.client.audio.transcriptions.create = AsyncMock(
            side_effect=Exception("Generic error")
        )

        with pytest.raises(GroqTranscriptionError):
            await self.client.transcribe_audio(self.temp_path)

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.settings")
    @patch("stt_tg_bot.services.groq_client.aiofiles.open")
    async def test_transcribe_audio_with_fallback_model(
        self, mock_aiofiles_open: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test transcription with fallback model."""
        mock_settings.groq_model_fallback = "whisper-large-v3"
        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        self.client.client.audio.transcriptions.create = AsyncMock(
            return_value="Fallback transcription"
        )

        result = await self.client.transcribe_audio(self.temp_path, use_fallback=True)

        assert result == "Fallback transcription"


class TestTranscribeWithFallback:
    """Tests for transcribe_with_fallback function."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        self.temp_path = Path(self.temp_file.name)
        self.temp_file.close()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        if self.temp_path.exists():
            self.temp_path.unlink()

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.GroqWhisperClient")
    async def test_transcribe_with_fallback_success_primary(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test successful transcription with primary model."""
        mock_client = AsyncMock()
        mock_client.transcribe_audio.return_value = "Primary model result"
        mock_client_class.return_value = mock_client

        result = await transcribe_with_fallback(self.temp_path)

        assert result == "Primary model result"
        mock_client.transcribe_audio.assert_called_once_with(
            self.temp_path, use_fallback=False
        )

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.GroqWhisperClient")
    async def test_transcribe_with_fallback_success_fallback(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test successful transcription with fallback model."""
        mock_client = AsyncMock()
        mock_client.transcribe_audio.side_effect = [
            GroqServiceUnavailableError("Primary failed"),
            "Fallback model result",
        ]
        mock_client_class.return_value = mock_client

        result = await transcribe_with_fallback(self.temp_path)

        assert result == "Fallback model result"
        assert mock_client.transcribe_audio.call_count == 2

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.GroqWhisperClient")
    async def test_transcribe_with_fallback_unsupported_format(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test transcription with unsupported format (no fallback attempt)."""
        mock_client = AsyncMock()
        mock_client.transcribe_audio.side_effect = GroqUnsupportedFormatError(
            "Unsupported format"
        )
        mock_client_class.return_value = mock_client

        with pytest.raises(GroqUnsupportedFormatError):
            await transcribe_with_fallback(self.temp_path)

        # Should not attempt fallback for unsupported format
        mock_client.transcribe_audio.assert_called_once()

    @pytest.mark.asyncio
    @patch("stt_tg_bot.services.groq_client.GroqWhisperClient")
    async def test_transcribe_with_fallback_both_fail(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test transcription when both primary and fallback fail."""
        mock_client = AsyncMock()
        mock_client.transcribe_audio.side_effect = [
            GroqServiceUnavailableError("Primary failed"),
            GroqServiceUnavailableError("Fallback failed"),
        ]
        mock_client_class.return_value = mock_client

        with pytest.raises(GroqServiceUnavailableError):
            await transcribe_with_fallback(self.temp_path)

        assert mock_client.transcribe_audio.call_count == 2
