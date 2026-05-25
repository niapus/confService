"""
Интеграционные тесты конвейера инициализации приложения.

Покрывают то, что обычные unit-тесты не покрывают: реальную работу init_app() на
свежем приложении, ветки валидации ADMIN_DATA / SECRET_KEY / MAIL, создание
служебных директорий, создание администраторов в БД через AdminService.
"""
import os
from unittest.mock import MagicMock

import pytest

from app.core import startup
from app.exceptions.startup_exception import EnvironmentValidationException
from app.models.admin import Admin


_validate_admin_format = startup.__dict__["__validate_admin_data_format"]
_validate_environment = startup.__dict__["__validate_environment"]
_create_directories = startup.__dict__["__create_directories"]


class TestValidateAdminDataFormat:

    def test_valid_single_admin_returns_no_errors(self):
        assert _validate_admin_format("admin:password1234") == []

    def test_valid_multiple_admins(self):
        assert _validate_admin_format("alice:password1,boris:password2") == []

    def test_missing_colon_reported(self):
        errors = _validate_admin_format("just_login_no_colon")
        assert len(errors) == 1
        assert "неверный формат" in errors[0]

    def test_empty_login_reported(self):
        errors = _validate_admin_format(":password1234")
        assert any("пустой логин" in e for e in errors)

    def test_short_login_reported(self):
        errors = _validate_admin_format("abc:password1234")
        assert any("слишком короткий" in e and "abc" in e for e in errors)

    def test_duplicate_login_reported(self):
        errors = _validate_admin_format("alice:pass12345,alice:pass54321")
        assert any("повторяющийся логин" in e for e in errors)

    def test_empty_password_reported(self):
        errors = _validate_admin_format("alice:")
        assert any("пустой пароль" in e for e in errors)

    def test_short_password_reported(self):
        errors = _validate_admin_format("alice:short")
        assert any("слишком короткий" in e and "alice" in e for e in errors)

    def test_password_with_colon_is_valid(self):
        # split(':', 1) — пароль может содержать ':'
        assert _validate_admin_format("alice:pass:word:with:colons") == []

    def test_multiple_errors_accumulated(self):
        # "a" — короткий логин; "p" — короткий пароль; ":nopass" — пустой логин
        errors = _validate_admin_format("a:p,bob:short,:nopass")
        assert len(errors) >= 3

def _mock_app(config: dict):
    app = MagicMock()
    app.config = config
    return app


class TestValidateEnvironment:

    BASE = {
        "SECRET_KEY": "a" * 32,
        "ADMIN_DATA": "admin:password1234",
        "MAIL_ENABLED": False,
        "EMAIL_VERIFICATION_ENABLED": False,
    }

    def test_happy_path_passes(self):
        _validate_environment(_mock_app(dict(self.BASE)))  # без исключения

    def test_missing_secret_key_raises(self):
        cfg = dict(self.BASE, SECRET_KEY=None)
        with pytest.raises(EnvironmentValidationException) as ei:
            _validate_environment(_mock_app(cfg))
        assert "SECRET_KEY" in ei.value.message

    def test_short_secret_key_raises(self):
        cfg = dict(self.BASE, SECRET_KEY="short")
        with pytest.raises(EnvironmentValidationException) as ei:
            _validate_environment(_mock_app(cfg))
        assert "SECRET_KEY" in ei.value.message
        assert "слишком короткий" in ei.value.message

    def test_missing_admin_data_is_allowed(self):
        cfg = dict(self.BASE, ADMIN_DATA=None)
        _validate_environment(_mock_app(cfg))  # без исключения

    def test_invalid_admin_data_format_raises(self):
        cfg = dict(self.BASE, ADMIN_DATA="bad_no_colon")
        with pytest.raises(EnvironmentValidationException) as ei:
            _validate_environment(_mock_app(cfg))
        assert "ADMIN_DATA" in ei.value.message

    def test_verification_without_mail_raises(self):
        cfg = dict(self.BASE, MAIL_ENABLED=False, EMAIL_VERIFICATION_ENABLED=True)
        with pytest.raises(EnvironmentValidationException) as ei:
            _validate_environment(_mock_app(cfg))
        assert "MAIL_ENABLED" in ei.value.message

    def test_mail_enabled_without_smtp_settings_raises(self):
        cfg = dict(self.BASE, MAIL_ENABLED=True)
        with pytest.raises(EnvironmentValidationException) as ei:
            _validate_environment(_mock_app(cfg))
        msg = ei.value.message
        for required in ("MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME", "MAIL_PASSWORD"):
            assert required in msg

    def test_mail_enabled_with_full_settings_passes(self):
        cfg = dict(
            self.BASE,
            MAIL_ENABLED=True,
            MAIL_SERVER="smtp.test.com",
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
            MAIL_USERNAME="u",
            MAIL_PASSWORD="p",
            MAIL_DEFAULT_SENDER="s@test.com",
        )
        _validate_environment(_mock_app(cfg))

class TestCreateDirectories:

    def test_creates_all_three_dirs(self, tmp_path):
        cfg = {
            "LOGS_FOLDER": str(tmp_path / "logs"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
            "THEMES_FOLDER": str(tmp_path / "themes"),
        }
        _create_directories(_mock_app(cfg))

        assert (tmp_path / "logs").is_dir()
        assert (tmp_path / "uploads").is_dir()
        assert (tmp_path / "themes").is_dir()

    def test_idempotent(self, tmp_path):
        cfg = {
            "LOGS_FOLDER": str(tmp_path / "logs"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
            "THEMES_FOLDER": str(tmp_path / "themes"),
        }
        _create_directories(_mock_app(cfg))
        _create_directories(_mock_app(cfg))
        assert (tmp_path / "logs").is_dir()

class TestInitAppHappyPath:
    """Проверяет, что свежий create_app действительно создал админа и каталоги."""

    def test_admin_table_has_default_admin(self, app, session):
        admin = session.query(Admin).filter_by(login="admin").first()
        assert admin is not None
        assert admin.password_hash
        assert admin.password_hash != "password1234"

    def test_admin_password_hashed_with_pbkdf2(self, app, session):
        admin = session.query(Admin).filter_by(login="admin").first()
        assert admin.password_hash.startswith("pbkdf2:") or admin.password_hash.startswith("scrypt:")

    def test_directories_exist(self, app):
        assert os.path.isdir(app.config["LOGS_FOLDER"])
        assert os.path.isdir(app.config["UPLOAD_FOLDER"])

    def test_app_extensions_contain_services(self, app):
        assert "services" in app.extensions
        assert "theme_loader" in app.extensions
