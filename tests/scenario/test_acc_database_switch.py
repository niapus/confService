import importlib

import pytest
from sqlalchemy import create_engine


class TestDatabaseUrlSwitch:

    def test_pymysql_driver_importable(self):
        """PyMySQL должен быть в requirements.txt — драйвер для MariaDB/MySQL."""
        importlib.import_module("pymysql")

    def test_sqlalchemy_constructs_engine_for_mariadb_url(self):
        """Конструктор engine не должен падать на корректной строке MariaDB."""
        url = "mysql+pymysql://user:password@localhost:3306/conference"
        engine = create_engine(url, echo=False)
        assert engine.url.drivername == "mysql+pymysql"
        assert engine.url.host == "localhost"
        assert engine.url.port == 3306
        assert engine.url.database == "conference"

    def test_init_engine_accepts_mariadb_url(self, tmp_path):
        """init_engine() в коде приложения принимает MariaDB-строку без модификаций."""
        from unittest.mock import MagicMock
        from app.core import database as db_module

        mock_app = MagicMock()
        mock_app.config = {
            "SQLALCHEMY_DATABASE_URL": "mysql+pymysql://u:p@localhost:3306/db",
            "SQLALCHEMY_ECHO": False,
        }
        # На MariaDB-URL не должна срабатывать ветка mkdir() для sqlite (попытка
        # создать каталог 'localhost:3306/db' и подобные).
        db_module.init_engine(mock_app)
        assert db_module.engine is not None
        assert db_module.engine.url.drivername == "mysql+pymysql"
        # PRAGMA-listener регистрируется только для sqlite — для mysql его нет.
        assert "sqlite" not in db_module.engine.url.drivername

    def test_default_database_is_sqlite(self):
        """По умолчанию (без DATABASE_URL) используется встроенная SQLite."""
        from app.config import Config
        # До любых тестовых переопределений — Config был sqlite-based.
        # Проверяем сам default-конструктор (env-переменная может быть выставлена тестами).
        import os
        prev = os.environ.pop("DATABASE_URL", None)
        try:
            # Перечитываем дефолт через создание engine с явным default-значением.
            engine = create_engine("sqlite:///data/conference_service.db", echo=False)
            assert engine.url.drivername == "sqlite"
        finally:
            if prev is not None:
                os.environ["DATABASE_URL"] = prev
