"""
Интеграционные тесты AdminRepository на реальной SQLite.

Проверяют уникальность login на уровне БД.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.admin import Admin
from app.repository.admin_repository import AdminRepository


@pytest.fixture
def repo():
    return AdminRepository()


@pytest.fixture
def session_fresh(app, session_factory):
    """
    Свежая сессия без админов, созданных startup-конвейером.
    create_app() создаёт админа 'admin' через __create_admin → очищаем таблицу.
    """
    s = session_factory()
    s.query(Admin).delete()
    s.commit()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


class TestGetAdminCount:
    def test_returns_zero_when_empty(self, repo, session_fresh):
        assert repo.get_admin_count(session_fresh) == 0

    def test_counts_rows(self, repo, session_fresh):
        admins = [Admin(login=f"a{i}", password_hash="h") for i in range(3)]
        repo.save_all(admins, session_fresh)
        session_fresh.commit()
        assert repo.get_admin_count(session_fresh) == 3


class TestGetAdminByLogin:
    def test_returns_admin(self, repo, session_fresh):
        repo.save_all([Admin(login="root", password_hash="h")], session_fresh)
        session_fresh.commit()

        found = repo.get_admin_by_login("root", session_fresh)
        assert found is not None
        assert found.login == "root"

    def test_returns_none_when_missing(self, repo, session_fresh):
        assert repo.get_admin_by_login("nope", session_fresh) is None


class TestSaveAll:
    def test_save_all_persists_collection(self, repo, session_fresh):
        admins = [
            Admin(login="alice", password_hash="h1"),
            Admin(login="bob", password_hash="h2"),
        ]
        repo.save_all(admins, session_fresh)
        session_fresh.commit()

        for a in admins:
            assert a.id is not None

    def test_unique_login_constraint(self, repo, session_fresh):
        repo.save_all([Admin(login="dup", password_hash="h")], session_fresh)
        session_fresh.commit()

        with pytest.raises(IntegrityError):
            repo.save_all([Admin(login="dup", password_hash="other")], session_fresh)
            session_fresh.flush()
        session_fresh.rollback()
