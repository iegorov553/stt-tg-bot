"""OpenAI API client for generating transcription summaries."""

import logging
from typing import Optional

import httpx

from stt_tg_bot.config.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API."""

    def __init__(self) -> None:
        """Initialize OpenAI client with API key from settings."""
        self.settings = get_settings()
        self.api_key = self.settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"  # Using the most cost-effective model
        self.timeout = 30.0

    async def generate_summary(self, transcription: str) -> Optional[str]:
        """
        Generate a summary of the transcription using OpenAI API.

        Args:
            transcription: The full transcription text to summarize

        Returns:
            Summary text or None if generation failed
        """
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            return None

        if not transcription.strip():
            logger.warning("Empty transcription provided for summary")
            return None

        prompt = self._create_summary_prompt(transcription)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Ты помощник, который создает краткие и информативные "
                                    "саммари текстов на русском языке. Отвечай только на русском языке."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 300,  # Ограничиваем размер ответа
                        "temperature": 0.3,  # Менее креативный, более фактический
                        "presence_penalty": 0.0,
                        "frequency_penalty": 0.1,
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"OpenAI API error: {response.status_code} - {response.text}"
                    )
                    return None

                data = response.json()

                if "choices" not in data or not data["choices"]:
                    logger.error("OpenAI API returned no choices")
                    return None

                summary = data["choices"][0]["message"]["content"].strip()

                if not summary:
                    logger.warning("OpenAI API returned empty summary")
                    return None

                logger.info(f"Generated summary: {len(summary)} characters")
                return summary

        except httpx.TimeoutException:
            logger.error("OpenAI API request timed out")
            return None
        except httpx.RequestError as e:
            logger.error(f"OpenAI API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI API call: {e}")
            return None

    def _create_summary_prompt(self, transcription: str) -> str:
        """
        Create a prompt for summarizing the transcription.

        Args:
            transcription: The transcription text

        Returns:
            Formatted prompt for OpenAI
        """
        return f"""
Создай краткое и информативное саммари следующей аудиозаписи.
Выдели основные темы, ключевые моменты и важные выводы.

Текст для анализа:
{transcription}

Требования к саммари:
- На русском языке
- Структурированно (если есть несколько тем)
- Кратко, но информативно
- Выдели самое важное
- Если это встреча/диалог - укажи основные решения
- Если это лекция/презентация - основные тезисы
- Если это разговор - ключевые темы обсуждения
""".strip()


# Глобальный экземпляр клиента
openai_client = OpenAIClient()


async def generate_transcription_summary(transcription: str) -> Optional[str]:
    """
    Generate summary for transcription using OpenAI.

    This is a convenience function that uses the global OpenAI client.

    Args:
        transcription: The transcription text to summarize

    Returns:
        Summary text or None if generation failed
    """
    return await openai_client.generate_summary(transcription)
