"""OpenAI API client for generating transcription summaries."""

import logging
import random
from typing import Optional, Tuple

import httpx

from stt_tg_bot.config.settings import get_settings

logger = logging.getLogger(__name__)


RETRY_STATUS = {500, 502, 503, 504}
FALLBACK_MODELS = ["gpt-5-mini", "gpt-4.1-mini"]  # порядок фолбэка


class OpenAIClient:
    """Client for interacting with OpenAI API."""

    def __init__(self) -> None:
        """Initialize OpenAI client with API key from settings."""
        self.settings = get_settings()
        self.api_key = self.settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        # Базовая модель (быстро/дёшево). При 500 будет авто-фолбэк.
        self.model = "gpt-5-nano"
        self.timeout = 60.0  # немного выше на длинных входах

    async def generate_summary(self, transcription: str) -> Optional[str]:
        """
        Generate a summary of the transcription using OpenAI API.
        """
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            return None

        if not transcription.strip():
            logger.warning("Empty transcription provided for summary")
            return None

        # Грубая оценка слов → выбор лимита токенов для ответа
        wc = len(transcription.split())
        if wc < 1200:  # ~до 10 мин речи
            max_tokens = 500
        elif wc < 6000:  # ~10–60 мин
            max_tokens = 1000
        else:  # ~60–120+ мин
            max_tokens = 1500

        prompt = self._create_summary_prompt(transcription)

        # 1) пытаемся Chat Completions с основной моделью + ретраи
        summary, err = await self._post_chat(prompt, self.model, max_tokens)
        if summary is not None:
            return summary

        # 2) быстрая смена модели в Chat Completions
        for fb in FALLBACK_MODELS:
            logger.warning(f"ChatCompletions fallback to model={fb} after: {err}")
            summary, err = await self._post_chat(prompt, fb, max_tokens)
            if summary is not None:
                return summary

        # 3) Responses API как устойчивый фолбэк
        logger.warning(f"Falling back to Responses API after: {err}")
        return await self._post_responses(prompt, FALLBACK_MODELS[0], max_tokens)

    async def _post_chat(
        self, prompt: str, model: str, max_tokens: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """POST /chat/completions with retries and jitter."""
        payload = {
            "model": model,
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
            "temperature": 0.2,
            "top_p": 1.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.2,
            "max_tokens": max_tokens,
        }
        return await self._post_with_retries(
            f"{self.base_url}/chat/completions", payload
        )

    async def _post_responses(
        self, prompt: str, model: str, max_tokens: int
    ) -> Optional[str]:
        """POST /responses as a fallback."""
        payload = {
            "model": model,
            "input": [
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
            "max_output_tokens": max_tokens,
            "temperature": 0.2,
            # (опционально) минимальное «мышление» у reasoning-моделей для скорости:
            "reasoning": {"effort": "minimal"},
        }
        summary, _err = await self._post_with_retries(
            f"{self.base_url}/responses", payload, responses_api=True
        )
        return summary

    async def _post_with_retries(
        self, url: str, payload: dict, responses_api: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        backoff_base = 0.25
        attempts = 0
        last_err = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while attempts < 5:
                attempts += 1
                try:
                    resp = await client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    req_id = resp.headers.get("x-request-id")
                    if resp.status_code == 200:
                        data = resp.json()
                        if responses_api:
                            # Responses API
                            # формат: {"output":[{"content":[{"text":"..."}]}], ...}
                            try:
                                text = data["output"][0]["content"][0]["text"].strip()
                            except Exception:
                                text = None
                        else:
                            # Chat Completions
                            try:
                                text = data["choices"][0]["message"]["content"].strip()
                            except Exception:
                                text = None

                        if text:
                            logger.info(
                                f"Generated summary ({len(text)} chars). req_id={req_id}"
                            )
                            return text, None
                        logger.warning(f"Empty content from API. req_id={req_id}")
                        return None, "empty_content"

                    # Неретрайные 4xx — сразу выходим (кроме 429)
                    if 400 <= resp.status_code < 500 and resp.status_code != 429:
                        logger.error(
                            f"OpenAI API {resp.status_code}: {resp.text} req_id={req_id}"
                        )
                        return None, f"{resp.status_code}"

                    # Ретраим 429 и 5xx
                    if resp.status_code in RETRY_STATUS or resp.status_code == 429:
                        delay = (
                            backoff_base * (2 ** (attempts - 1)) + random.random() * 0.1  # nosec B311
                        )
                        logger.warning(
                            f"API {resp.status_code}, attempt {attempts}/5, sleep {delay:.2f}s, req_id={req_id}"
                        )
                        await self._sleep(delay)
                        continue

                    # неожиданный код
                    logger.error(
                        f"Unexpected API status: {resp.status_code} {resp.text} req_id={req_id}"
                    )
                    return None, f"{resp.status_code}"

                except httpx.TimeoutException:
                    last_err = "timeout"
                    delay = backoff_base * (2 ** (attempts - 1)) + random.random() * 0.1  # nosec B311
                    logger.warning(f"Timeout, attempt {attempts}/5, sleep {delay:.2f}s")
                    await self._sleep(delay)
                except httpx.RequestError as e:
                    last_err = f"request_error: {e}"
                    delay = backoff_base * (2 ** (attempts - 1)) + random.random() * 0.1  # nosec B311
                    logger.warning(
                        f"Request error, attempt {attempts}/5, sleep {delay:.2f}s"
                    )
                    await self._sleep(delay)
                except Exception as e:
                    last_err = f"unexpected: {e}"
                    logger.error(f"Unexpected error: {e}")
                    break

        return None, last_err or "failed"

    async def _sleep(self, seconds: float) -> None:
        # Отдельный метод — удобно мокать в тестах
        import asyncio

        await asyncio.sleep(seconds)

    def _create_summary_prompt(self, transcription: str) -> str:
        """
        Create a prompt for summarizing the transcription.
        """
        return f"""
Суммируй транскрибированный текст аудио/видео.
Адаптируй объём и детализацию под длину текста: короткий (до 10 мин), средний (10–60 мин), длинный (60–120+ мин).

ТРЕБОВАНИЯ:
— Язык: русский. Тон: нейтральный, деловой, без эмодзи.
— Структура (если применимо):
  1) TL;DR (1–3 предложения).
  2) Основные темы и тезисы (буллеты).
  3) Принятые решения и договорённости (если встреча/созвон).
  4) Action items: кто → что → срок (если есть).
  5) Цифры/метрики/сроки/имена (точные значения).
  6) Риски/неопределённости/вопросы без ответа.
  7) Хайлайты по времени — только если явно есть таймкоды.

— Убирай повторы и «воду». Ничего не выдумывай: если данных нет, пиши «нет данных».

Текст:
<<<TRANSCRIPT_START
{transcription}
TRANSCRIPT_END>>>
""".strip()


# Глобальный экземпляр клиента
openai_client = OpenAIClient()


async def generate_transcription_summary(transcription: str) -> Optional[str]:
    return await openai_client.generate_summary(transcription)
