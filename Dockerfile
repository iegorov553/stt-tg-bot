FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаём пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Создаём рабочую директорию
WORKDIR /app

# Копируем код приложения
COPY stt_tg_bot/ ./stt_tg_bot/

# Меняем владельца файлов
RUN chown -R appuser:appuser /app

# Переключаемся на пользователя
USER appuser

# Настраиваем переменные окружения
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
