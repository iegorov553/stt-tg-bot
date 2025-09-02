# STT Telegram Bot

## Project Overview

Speech-to-Text Telegram bot built with Python using Groq Whisper API for fast audio transcription. The bot processes voice messages and audio files, converting them to text in Russian.

## Quick Navigation

- **Main Entry Point**: `stt_tg_bot/main.py`
- **Configuration**: `stt_tg_bot/config/settings.py`
- **Bot Handlers**: `stt_tg_bot/handlers/bot_handlers.py`
- **Groq Integration**: `stt_tg_bot/services/groq_client.py`
- **Webhook Server**: `stt_tg_bot/services/webhook_server.py`
- **Tests**: `tests/` directory
- **Docker**: `Dockerfile`

## Key Technologies

- **Framework**: aiogram 3.x for Telegram Bot API
- **API**: Groq Whisper for speech-to-text
- **Web Server**: FastAPI for webhook handling
- **Environment**: Poetry for dependency management
- **Deployment**: Docker + Railway
- **Testing**: pytest with coverage
- **Quality**: Ruff, mypy, Bandit, pre-commit

## Development Commands

```bash
# Install dependencies
poetry install

# Run bot (development)
export USE_WEBHOOK=false && poetry run python -m stt_tg_bot.main

# Run tests
poetry run pytest

# Format and lint
poetry run ruff format . && poetry run ruff check . --fix

# Type check
poetry run mypy stt_tg_bot/
```

## Configuration

See `.env.example` for required environment variables. The bot uses Pydantic Settings for configuration management with automatic validation.

## Deployment

The bot is designed for Railway deployment with webhook mode. Health check endpoint available at `/`.

For development guidance, refer to the main README.md file.
