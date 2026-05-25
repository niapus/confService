"""
Инфраструктура интеграционных тестов.

Тесты используют РЕАЛЬНУЮ in-memory SQLite БД и реальные репозитории/сервисы.
Замокан только SMTP (через MAIL_ENABLED=false по умолчанию).

Каждый тест получает свежий Flask-app со своей изолированной БД через `app` /
`session` / `client` фикстуры. Поскольку модули app.core.database держат
engine/Session как глобалы, фикстура `app` пересоздаёт их через init_engine.
"""

import os
import pytest

from app.config import Config


def _build_app(tmp_path, mail_enabled: bool, monkeypatch=None):
    db_path = tmp_path / "test.db"
    Config.SECRET_KEY = "integration-test-secret-key-32-chars-minimum!"
    Config.ADMIN_DATA = "admin:password1234"
    Config.MAIL_ENABLED = mail_enabled
    Config.EMAIL_VERIFICATION_ENABLED = False
    Config.SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    Config.LOGS_FOLDER = str(tmp_path / "logs")
    Config.UPLOAD_FOLDER = str(tmp_path / "uploads")
    Config.THEMES_FOLDER = Config.BASE_DIR / "themes"

    # При MAIL_ENABLED=true __validate_environment требует SMTP-настройки.
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

    if mail_enabled and monkeypatch is not None:
        # фоновый планировщик внутри теста не нужен — иначе job'ы стартуют в треде.
        import app as app_pkg
        monkeypatch.setattr(app_pkg, "_try_start_scheduler", lambda app, worker_id: None)

    from app import create_app

    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False

    before_funcs = application.before_request_funcs.get(None, [])
    application.before_request_funcs[None] = [
        f for f in before_funcs if getattr(f, "__name__", "") != "before_request"
    ]

    return application


@pytest.fixture
def app(tmp_path):
    """Свежий Flask-app со своей in-memory SQLite на каждый тест (MAIL_ENABLED=false)."""
    yield _build_app(tmp_path, mail_enabled=False)


@pytest.fixture
def app_with_mail(tmp_path, monkeypatch):
    """Flask-app с MAIL_ENABLED=true — NotificationService реально кладёт в очередь.

    Фоновый планировщик отключён через monkeypatch.
    """
    yield _build_app(tmp_path, mail_enabled=True, monkeypatch=monkeypatch)


@pytest.fixture
def services(app):
    return app.extensions["services"]


@pytest.fixture
def session_factory(app):
    """sessionmaker, инициализированный create_app через init_engine."""
    from app.core import database
    return database.Session


@pytest.fixture
def session(session_factory):
    """Сессия с автоматическим закрытием. Изоляция — за счёт свежего app/БД."""
    s = session_factory()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_session(client, services, session_factory):
    """Клиент с активной сессией администратора (вход через реальный AdminService)."""
    resp = client.post(
        "/auth/login",
        data={"login": "admin", "password": "password1234"},
    )
    assert resp.status_code == 302, f"login failed: {resp.status_code}, {resp.data!r}"
    return client


@pytest.fixture
def persisted_conference(session):
    """Сохранённая в БД конференция со стандартными датами в будущем."""
    from datetime import date, timedelta
    from app.models.conference import Conference

    today = date.today()
    c = Conference(
        title="Test Conf",
        description_md="# x",
        description_html="<h1>x</h1>",
        tagline="t",
        registration_deadline=today + timedelta(days=30),
        submission_deadline=today + timedelta(days=45),
        start_date=today + timedelta(days=60),
        end_date=today + timedelta(days=62),
        performance_time=15,
    )
    session.add(c)
    session.commit()
    return c


@pytest.fixture
def persisted_application(session, persisted_conference):
    """Подтверждённая заявка в persisted_conference."""
    from datetime import date
    from app.models.application import (
        Application, ApplicationStatus, GenderEnum, DegreeEnum,
        EducationEnum, ParticipationFormatEnum,
    )

    a = Application(
        conference_id=persisted_conference.id,
        surname="Иванов",
        name="Иван",
        patronymic="Иванович",
        gender=GenderEnum.MALE,
        birth_date=date(2000, 1, 1),
        degree=DegreeEnum.NONE,
        is_worker=False,
        is_student=True,
        study_name="UrFU",
        study_place="Екатеринбург",
        study_level=EducationEnum.MASTER,
        participation_format=ParticipationFormatEnum.OFFLINE,
        email="ivan@test.com",
        status=ApplicationStatus.CONFIRMED,
    )
    session.add(a)
    session.commit()
    return a
