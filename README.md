# STT Telegram Bot

A Speech-to-Text Telegram bot using Groq Whisper API for audio transcription, with optional Text-to-Speech via OpenAI.

## Features

- 🎤 **Audio Transcription**: Supports voice messages, audio files, and documents
- 🔊 **Text-to-Speech**: Forward text posts and receive voice messages (OpenAI TTS)
- 🌐 **Multiple Formats**: OGG, OPUS, MP3, WAV, M4A and more
- 🌍 **Automatic Language Detection**: Recognizes any language supported by Groq Whisper
- 🚀 **Fast Processing**: Groq Whisper Large V3 Turbo with fallback support
- 🔒 **Access Control**: User allowlist with ID and username support
- 📱 **Webhook Support**: Production-ready deployment on Railway
- 🐳 **Docker Support**: Containerized deployment
- 🧪 **Full Test Coverage**: Comprehensive unit and integration tests

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token
- Groq API Key
- OpenAI API Key (required for TTS)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stt-tg-bot
```

2. Install dependencies with Poetry:
```bash
poetry install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the bot:
```bash
# Development mode (polling)
export USE_WEBHOOK=false
poetry run python -m stt_tg_bot.main

# Production mode (webhook)
export USE_WEBHOOK=true
poetry run python -m stt_tg_bot.main
```

## Configuration

### Required Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `GROQ_API_KEY`: Your Groq API key
- `PUBLIC_BASE_URL`: Public URL for webhook (Railway domain)
- `WEBHOOK_SECRET`: Secret token for webhook security
- `ALLOWLIST`: Comma-separated user IDs and usernames (e.g., `123456789,@username`)

### Optional Environment Variables

- `USE_WEBHOOK`: Use webhook mode (default: `true`)
- `PORT`: Server port (default: `8080`)
- `READ_TIMEOUT_SEC`: HTTP timeout (default: `120`)
- `GROQ_MODEL_PRIMARY`: Primary model (default: `whisper-large-v3-turbo`)
- `GROQ_MODEL_FALLBACK`: Fallback model (default: `whisper-large-v3`)
- `GROQ_LANGUAGE`: Optional language override for transcription (default: auto-detect)
- `OPENAI_API_KEY`: OpenAI API key for summaries and TTS (optional but required for TTS)
- `OPENAI_TTS_MODEL`: OpenAI TTS model (default: `gpt-4o-mini-tts`)
- `OPENAI_TTS_VOICE`: OpenAI TTS voice (default: `coral`)
- `OPENAI_TTS_RESPONSE_FORMAT`: OpenAI TTS audio format (default: `opus`)
- `OPENAI_TTS_MAX_CHARS`: Max characters per TTS request (default: `4096`)
- `OPENAI_TTS_RATE_LIMIT_PER_MINUTE`: TTS requests per minute (default: `5`)
- `OPENAI_TTS_WINDOW_SEC`: Rate limit window in seconds (default: `60`)

## Commands

- `/start` - Start the bot and get welcome message
- `/help` - Get help information

## Text-to-Speech Usage

- Forward a text message from any channel/chat to the bot
- The bot will reply with a voice message (OGG/Opus)
- Emoji are removed before synthesis
- Limits: 4096 characters and 5 requests per minute by default

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=stt_tg_bot --cov-report=term-missing
```

> **Tip:** The unit test suite now ships with light-weight fallbacks for optional packages (for example, `aiogram` or `pydantic-settings`). Install the real dependencies from `requirements.txt` to exercise the exact production wiring.

### Code Quality

```bash
# Format code
poetry run ruff format .

# Lint code
poetry run ruff check . --fix

# Type checking
poetry run mypy stt_tg_bot/

# Security check
poetry run bandit -r stt_tg_bot/

# Dependency audit (known aiohttp CVEs are ignored; see SECURITY.md)
poetry run pip-audit \
  --ignore-vuln CVE-2025-69223 \
  --ignore-vuln CVE-2025-69224 \
  --ignore-vuln CVE-2025-69225 \
  --ignore-vuln CVE-2025-69226 \
  --ignore-vuln CVE-2025-69227 \
  --ignore-vuln CVE-2025-69228 \
  --ignore-vuln CVE-2025-69229 \
  --ignore-vuln CVE-2025-69230

# Run all quality checks
poetry run pre-commit run --all-files
```

## Docker Deployment

### Build Docker Image

```bash
docker build -t stt-tg-bot .
```

### Run Container

```bash
docker run -d \
  --name stt-tg-bot \
  -p 8080:8080 \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e GROQ_API_KEY=your_key \
  -e PUBLIC_BASE_URL=https://your-domain.com \
  -e WEBHOOK_SECRET=your_secret \
  -e ALLOWLIST=123456789,@username \
  stt-tg-bot
```

## Railway Deployment

1. Connect your repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically from `main` branch

### Railway Configuration

- **Start Command**: `python -m stt_tg_bot.main`
- **Port**: `8080`
- **Health Check**: `GET /`

## Architecture

### Project Structure

```
stt_tg_bot/
├── config/          # Configuration management
├── handlers/        # Telegram bot handlers
├── services/        # External services (Groq, Webhook)
├── utils/          # Utilities (access control, messages)
├── models/         # Data models (if needed)
└── main.py         # Application entry point
```

### Key Components

- **Settings**: Pydantic-based configuration management
- **Access Control**: User allowlist with ID/username support
- **Groq Client**: Async Whisper API client with fallback
- **Handlers**: Telegram command and message handlers
- **Webhook Server**: FastAPI server for production deployment

## Error Handling

The bot provides user-friendly error messages for common scenarios:

- Access denied for unauthorized users
- Unsupported file formats
- Service unavailability
- Network timeouts
- Processing errors

## Security

- User access control via allowlist
- Webhook secret token validation
- No data persistence or logging of user content
- Temporary file cleanup after processing
- Docker security best practices

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

[Your License]

## Support

For issues and questions, please use the GitHub issue tracker.
