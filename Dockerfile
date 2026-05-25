# ===== Стадия 1: Сборка зависимостей =====
FROM python:3.14-slim AS builder

WORKDIR /app

# Устанавливаем gcc только для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-пакеты в изолированный префикс
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ===== Стадия 2: Финальный образ =====
FROM python:3.14-slim

# gosu для безопасного понижения привилегий в entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

# Создаём непривилегированного пользователя
RUN useradd --create-home --uid 1000 --shell /bin/bash appuser

WORKDIR /app

# Копируем установленные пакеты из стадии сборки в системные пути
COPY --from=builder /install /usr/local

# Копируем приложение
COPY app/ app/
COPY wsgi.py .
COPY gunicorn_config.py .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Создаём директории и передаём владение appuser
RUN mkdir -p logs uploads data themes \
    && chown -R appuser:appuser /app \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn_config.py", "wsgi:app"]
