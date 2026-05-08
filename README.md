# Система управления конференциями

Лёгковесная веб-система для организации научных конференций: сбор заявок и тезисов, формирование программы, публикация сборников. Работает из коробки через Docker, поддерживает темы оформления в стиле Nikola.

---

## Возможности

- Создание нескольких конференций с независимыми дедлайнами и настройками
- Приём заявок на доклады и тезисов (PDF/DOCX) от участников
- Модерация заявок и тезисов администратором
- Формирование расписания конференции
- Публикация материалов (программы, сборников)
- Уведомления по почте (опционально)
- Система тем оформления с наследованием (Jinja2, аналогично Nikola)
- Поддержка Markdown при описании конференции
- SQLite по умолчанию, MariaDB/MySQL опционально

---

## Быстрый старт (Docker)

### 1. Скачать проект

```bash
git clone <ссылка-на-репозиторий>
cd confService
```

Или загрузить ZIP-архив и распаковать.

### 2. Создать файл конфигурации

**Linux / macOS:**
```bash
cp .env.example .env
```

**Windows:**
```powershell
copy .env.example .env
```

Открыть `.env` в любом текстовом редакторе и заполнить обязательные поля:

```dotenv
# Секретный ключ (случайная строка, минимум 32 символа)
# Сгенерировать: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=замените_на_случайную_строку

# Логин и пароль администратора
ADMIN_DATA=admin:ваш_пароль
```

> Пароль администратора — минимум 8 символов.

### 3. Запустить

```bash
docker compose up -d
```

Сайт будет доступен по адресу: **http://localhost:5000**

Панель администратора: **http://localhost:5000/auth/login**

### Остановить / перезапустить

```bash
docker compose down        # остановить
docker compose up -d       # запустить снова
docker compose restart     # перезапустить
```

Все данные (база данных, загруженные файлы, темы, логи) сохраняются в папках рядом с `docker-compose.yml`:

| Папка | Содержимое |
|-------|-----------|
| `data/` | База данных SQLite |
| `uploads/` | Загруженные тезисы и материалы |
| `themes/` | Пользовательские темы оформления |
| `logs/` | Логи приложения |

---

## Настройка (`.env`)

Все параметры хранятся в файле `.env`. Образец — `.env.example`.

### Обязательные

| Параметр | Описание |
|----------|---------|
| `SECRET_KEY` | Секретный ключ Flask (≥ 32 символов) |
| `ADMIN_DATA` | Логин и пароль администратора: `login:password`. Несколько через запятую: `admin1:pass1,admin2:pass2` |

### База данных

По умолчанию используется SQLite — ничего дополнительно устанавливать не нужно.

```dotenv
# SQLite (по умолчанию)
DATABASE_URL=sqlite:///data/conference_service.db

# MariaDB / MySQL (если нужна полноценная СУБД)
DATABASE_URL=mysql+pymysql://user:password@host:3306/conference_db
```

### Почта (опционально)

Без почты система работает полностью. Письма нужны только для уведомлений участников.

```dotenv
MAIL_ENABLED=true
EMAIL_VERIFICATION_ENABLED=false   # true — требовать подтверждение почты при регистрации

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your@email.com
```

### Темы оформления

```dotenv
ACTIVE_THEME=default   # имя папки из themes/ или "default" для базовой темы
```

### HTTPS (продакшн)

```dotenv
SESSION_COOKIE_SECURE=true   # включить только при работе за HTTPS
```

---

## Темы оформления

Темы хранятся в папке `themes/` (рядом с `docker-compose.yml`). Каждая тема — это папка с файлом `theme.yaml` и поддиректориями `templates/` и `static/`.

### Структура темы

```
themes/
└── my-theme/
    ├── theme.yaml          # метаданные
    ├── templates/          # переопределяемые шаблоны Jinja2
    │   └── base.html
    └── static/             # переопределяемые стили и скрипты
        └── css/
            └── base.css
```

### theme.yaml

```yaml
name: Моя тема
description: Описание темы
parent: default             # родительская тема (необязательно)
```

Производная тема содержит **только** те файлы, которые нужно переопределить. Остальные подтягиваются из родительской темы автоматически.

После добавления темы — указать её имя в `.env`:
```dotenv
ACTIVE_THEME=my-theme
```

И перезапустить контейнер:
```bash
docker compose up -d
```

---

## Обновление

```bash
git pull                    # получить обновления
docker compose up -d --build  # пересобрать и перезапустить
```

Данные при этом не затрагиваются.

---

## Локальный запуск без Docker

Требования: Python 3.11+

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

После копирования `.env` — открыть файл и заполнить `SECRET_KEY` и `ADMIN_DATA`.

---

## Резервное копирование

Для полного резервного копирования достаточно скопировать три папки:

```
data/       — база данных
uploads/    — загруженные файлы
themes/     — пользовательские темы (если есть)
```

Восстановление: скопировать папки обратно и запустить `docker compose up -d`.
