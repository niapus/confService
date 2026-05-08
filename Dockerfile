# ===== Стадия 1: Сборка зависимостей =====
FROM python:3.11-slim AS builder

WORKDIR /app

# Устанавливаем gcc только для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ===== Стадия 2: Финальный образ =====
FROM python:3.11-slim

WORKDIR /app

# Копируем только установленные пакеты из стадии сборки
COPY --from=builder /root/.local /root/.local

# Копируем приложение
COPY app/ app/
COPY wsgi.py .
COPY gunicorn_config.py .

# Создаём директории
RUN mkdir -p logs uploads data themes

# Добавляем путь к пакетам в PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn_config.py", "wsgi:app"]