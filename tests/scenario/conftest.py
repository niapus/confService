"""
Инфраструктура сценарных тестов.

В отличие от интеграционных, здесь не отключаем @before_request — маршруты идут
через полный стек: open Session - view-функция - teardown_request - commit/rollback.
Цель: проверить ключевые сценарии работы системы end-to-end.
"""
import os

import pytest

from app.config import Config


@pytest.fixture
def app(tmp_path):
    """Полностью настроенный Flask-app: реальная SQLite, реальные сервисы."""
    db_path = tmp_path / "acc.db"
    Config.SECRET_KEY = "scenario-test-secret-key-32-chars-minimum!"
    Config.ADMIN_DATA = "admin:password1234"
    Config.MAIL_ENABLED = False
    Config.EMAIL_VERIFICATION_ENABLED = False
    Config.SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    Config.LOGS_FOLDER = str(tmp_path / "logs")
    Config.UPLOAD_FOLDER = str(tmp_path / "uploads")
    Config.THEMES_FOLDER = Config.BASE_DIR / "themes"
    Config.TESTING = True

    os.environ["SECRET_KEY"] = Config.SECRET_KEY
    os.environ["ADMIN_DATA"] = Config.ADMIN_DATA
    os.environ["MAIL_ENABLED"] = "false"
    os.environ["EMAIL_VERIFICATION_ENABLED"] = "false"

    from app import create_app

    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False

    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    """test_client с активной admin-сессией. Логинимся через POST /auth/login."""
    resp = client.post("/auth/login", data={"login": "admin", "password": "password1234"})
    assert resp.status_code == 302, f"login failed: {resp.status_code} {resp.data!r}"
    return client


# Минимальный PDF, проходящий filetype.guess()
PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"\x00" * 1024


@pytest.fixture
def pdf_bytes():
    return PDF_BYTES
