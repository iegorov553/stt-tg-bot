# Single-stage build с Poetry
FROM python:3.11-slim as production

# Создаём пользователя для запуска приложения
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Устанавливаем системные зависимости и Poetry
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && pip install poetry==2.1.4

# Настраиваем Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_CREATE=0 \
    POETRY_CACHE_DIR=/opt/poetry-cache

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Устанавливаем только production зависимости
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR \
    && pip uninstall -y poetry

# Создаём рабочую директорию
WORKDIR /app

# Копируем код приложения
COPY stt_tg_bot/ ./stt_tg_bot/

# Меняем владельца файлов на appuser
RUN chown -R appuser:appuser /app

# Переключаемся на пользователя appuser
USER appuser

# Проверяем установку
RUN python -c "import stt_tg_bot; print('Application imported successfully')"

# Настраиваем переменные окружения для production
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Expose порт
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Запуск приложения
CMD ["python", "-m", "stt_tg_bot.main"]
