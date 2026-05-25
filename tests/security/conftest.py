"""
Инфраструктура тестов безопасности.

Защита от типовых веб-уязвимостей (CSRF, XSS, SQL-injection) и сопутствующие
проверки безопасной аутентификации, хранения паролей, валидации
загружаемых файлов и подписи JWT-токенов.

В отличие от scenario-фикстур, здесь CSRF-защита SeaSurf включена реальным
образом — Flask.TESTING=False, иначе SeaSurf автоматически отключает проверку
токенов и тесты CSRF теряют смысл. Конкретный TESTING-режим для test_client
включается локально через `app_csrf_off`, где это нужно (например, для проверки
других уязвимостей, не связанных с CSRF).
"""
import os

import pytest

from app.config import Config


def _reset_config(tmp_path, *, testing: bool, mail_enabled: bool = False):
    db_path = tmp_path / "security.db"
    Config.SECRET_KEY = "security-test-secret-key-32-chars-min!"
    Config.ADMIN_DATA = "admin:password1234"
    Config.MAIL_ENABLED = mail_enabled
    Config.EMAIL_VERIFICATION_ENABLED = False
    Config.SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    Config.LOGS_FOLDER = str(tmp_path / "logs")
    Config.UPLOAD_FOLDER = str(tmp_path / "uploads")
    Config.THEMES_FOLDER = Config.BASE_DIR / "themes"
    Config.TESTING = testing
    if mail_enabled:
        Config.MAIL_SERVER = "localhost"
        Config.MAIL_PORT = 25
        Config.MAIL_USE_TLS = True
        Config.MAIL_USERNAME = "test"
        Config.MAIL_PASSWORD = "test"
        Config.MAIL_DEFAULT_SENDER = "test@test.com"

    os.environ["SECRET_KEY"] = Config.SECRET_KEY
    os.environ["ADMIN_DATA"] = Config.ADMIN_DATA
    os.environ["MAIL_ENABLED"] = "true" if mail_enabled else "false"
    os.environ["EMAIL_VERIFICATION_ENABLED"] = "false"


@pytest.fixture
def app_csrf_on(tmp_path):
    """Flask-app с включённой реальной CSRF-защитой SeaSurf.

    SeaSurf проверяет токен только когда app.testing == False — поэтому здесь
    TESTING сознательно выключен, при этом WTF_CSRF тоже включён для полноты.
    """
    _reset_config(tmp_path, testing=False)
    from app import create_app

    application = create_app()
    application.config["TESTING"] = False
    application.config["WTF_CSRF_ENABLED"] = True
    yield application


@pytest.fixture
def app_csrf_off(tmp_path):
    """Flask-app с выключенной CSRF (для тестов XSS/SQLi/file-upload — там CSRF мешает)."""
    _reset_config(tmp_path, testing=True)
    from app import create_app

    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    yield application


@pytest.fixture
def client_csrf_on(app_csrf_on):
    return app_csrf_on.test_client()


@pytest.fixture
def client(app_csrf_off):
    return app_csrf_off.test_client()


@pytest.fixture
def admin_client(client):
    """Залогиненный admin (для тестов, где CSRF не интересна — только проверка авторизации)."""
    resp = client.post("/auth/login", data={"login": "admin", "password": "password1234"})
    assert resp.status_code == 302, f"login failed: {resp.status_code} {resp.data!r}"
    return client


@pytest.fixture
def session(app_csrf_off):
    """Прямая БД-сессия для setUp-данных, привязанная к тому же приложению, что и client."""
    from app.core import database
    s = database.Session()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


# Минимальный валидный PDF — магические байты для filetype.guess()
PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"\x00" * 1024


@pytest.fixture
def pdf_bytes():
    return PDF_BYTES
