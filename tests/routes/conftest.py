import os
from unittest.mock import MagicMock

import pytest

from app import create_app
from app.config import Config


@pytest.fixture(scope="session", autouse=True)
def _patch_config(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("test_app_data")
    Config.SECRET_KEY = "test-secret-key-that-is-at-least-32-chars-long!!"
    Config.ADMIN_DATA = "admin:password1234"
    Config.MAIL_ENABLED = False
    Config.EMAIL_VERIFICATION_ENABLED = False
    Config.SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    Config.LOGS_FOLDER = str(tmp_dir / "logs")
    Config.UPLOAD_FOLDER = str(tmp_dir / "uploads")
    os.environ["SECRET_KEY"] = Config.SECRET_KEY
    os.environ["ADMIN_DATA"] = Config.ADMIN_DATA
    os.environ["MAIL_ENABLED"] = "false"
    os.environ["EMAIL_VERIFICATION_ENABLED"] = "false"


@pytest.fixture(scope="session")
def app():
    # session scope: create_app() вызывается один раз на весь прогон.
    # Это исключает создание нескольких RotatingFileHandler на один файл,
    # что на Windows приводит к PermissionError при ротации лога.
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    before_funcs = app.before_request_funcs.get(None, [])
    app.before_request_funcs[None] = [
        f for f in before_funcs if getattr(f, '__name__', '') != '_before_request'
    ]

    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_services(app):
    services = app.extensions["services"]

    mocks = {
        "conference": MagicMock(),
        "application": MagicMock(),
        "admin": MagicMock(),
        "thesis": MagicMock(),
        "conference_file": MagicMock(),
        "verification": MagicMock(),
        "schedule": MagicMock(),
        "notification": MagicMock(),
        "log": MagicMock(),
    }

    services._services["conference"] = mocks["conference"]
    services._services["application"] = mocks["application"]
    services._services["admin"] = mocks["admin"]
    services._services["thesis"] = mocks["thesis"]
    services._services["conference_file"] = mocks["conference_file"]
    services._services["verification"] = mocks["verification"]
    services._services["schedule"] = mocks["schedule"]
    services._services["notification"] = mocks["notification"]
    services._services["log"] = mocks["log"]

    return mocks


@pytest.fixture
def admin_session(client, mock_services):
    from app.models.admin import Admin
    admin = Admin()
    admin.id = 1
    admin.login = "admin"

    mock_services["admin"].authenticate.return_value = admin

    resp = client.post("/auth/login", data={"login": "admin", "password": "password1234"})
    assert resp.status_code == 302
    return client
