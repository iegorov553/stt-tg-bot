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
        # Основная модель для суммаризации (дёшево/быстро, отлично для транскрибатов)
        self.model = "gpt-5-nano"
        # Альтернативы при необходимости:
        # self.model = "gpt-5-mini"
        # self.model = "gpt-4.1-mini"  # до 1M токенов контекста

        self.timeout = 60.0  # чуть выше на длинных входах

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

        # Выбор разумного лимита токенов под длину текста
        # ~ 1k слов ~ 750–900 токенов. Оценим по словам грубо.
        word_count = len(transcription.split())
        if word_count < 1200:  # ~ до 10 минут речи
            max_tokens = 500
        elif word_count < 6000:  # ~ 10–60 минут
            max_tokens = 1000
        else:  # ~ 60–120+ минут
            max_tokens = 1500

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
                                    "Ты аналитик и редактор, который делает точные, краткие и полезные "
                                    "саммари русскоязычных транскрибатов аудио/видео. "
                                    "Всегда пиши ТОЛЬКО на русском. "
                                    "Не придумывай факты; если данных нет, явно укажи «нет данных». "
                                    "Сохраняй имена, даты, цифры и формулировки решений."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        # Параметры под суммаризацию
                        "temperature": 0.2,
                        "top_p": 1.0,
                        "presence_penalty": 0.0,
                        "frequency_penalty": 0.2,
                        "max_tokens": max_tokens,
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
Суммируй транскрибированный текст аудио/видео.
Адаптируй объём и детализацию под длину текста: короткий (до 10 мин), средний (10–60 мин), длинный (60–120+ мин).

ТРЕБОВАНИЯ:
— Язык: русский.
— Тон: нейтральный, деловой, без эмодзи.
— Структура (если применимо):
  1) TL;DR (1–3 предложения).
  2) Основные темы и тезисы (буллеты).
  3) Принятые решения и договорённости (если была встреча/созвон).
  4) Action items: кто → что → срок (если указано/подразумевается).
  5) Цифры/метрики/сроки/имена (сохранить точные значения).
  6) Риски/неопределённости/вопросы без ответа.
  7) Если в тексте есть таймкоды — «Хайлайты по времени» (список кратких моментов с таймкодами). Если таймкодов нет — пропусти этот раздел.
— Краткость важнее дословных пересказов. Убирай повторы и «водные» вставки.
— Ничего не выдумывай. Если чего-то нет в тексте — пиши «нет данных».

Текст:
<<<TRANSCRIPT_START
{transcription}
TRANSCRIPT_END>>>
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
