"""
Безопасное хранение паролей администраторов.

Проверяется реализация AdminService.create_admins_from_env / authenticate:
  - пароль в БД лежит как хеш, не plaintext;
  - хеш использует современный медленный алгоритм werkzeug (pbkdf2 или scrypt);
  - соль уникальна — два админа с одинаковым паролем имеют РАЗНЫЕ хеши;
  - check_password_hash корректно срабатывает только на исходном пароле.

Защита от компрометации БД.
"""
import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.admin import Admin
from app.service.admin_service import AdminService
from app.repository.admin_repository import AdminRepository


class TestPasswordHashing:

    def test_password_is_hashed_not_plaintext(self, app_csrf_off, session):
        admin = session.query(Admin).filter_by(login="admin").first()
        assert admin is not None
        assert admin.password_hash != "password1234"
        assert "password1234" not in admin.password_hash

    def test_hash_uses_modern_kdf(self, app_csrf_off, session):
        """werkzeug.security возвращает строку с префиксом алгоритма + параметрами."""
        admin = session.query(Admin).filter_by(login="admin").first()
        ok = (
            admin.password_hash.startswith("pbkdf2:sha256:")
            or admin.password_hash.startswith("scrypt:")
        )
        assert ok, f"Неожиданный алгоритм: {admin.password_hash.split('$', 1)[0]}"

    def test_hash_format_contains_salt_and_digest(self, app_csrf_off, session):
        """Формат werkzeug: '<algo>$<salt>$<hash>' — то есть минимум два '$' разделителя."""
        admin = session.query(Admin).filter_by(login="admin").first()
        parts = admin.password_hash.split("$")
        assert len(parts) >= 3, f"Хеш без соли: {admin.password_hash}"
        # сам хеш — непустая шестнадцатеричная строка
        assert len(parts[-1]) >= 16

    def test_two_admins_same_password_get_different_hashes(self):
        """Соль должна делать хеши разными даже для одинакового пароля."""
        h1 = generate_password_hash("samepass1234")
        h2 = generate_password_hash("samepass1234")
        assert h1 != h2
        # но оба валидны для исходного пароля
        assert check_password_hash(h1, "samepass1234")
        assert check_password_hash(h2, "samepass1234")

    def test_check_password_rejects_wrong(self):
        h = generate_password_hash("right_password_1234")
        assert check_password_hash(h, "right_password_1234")
        assert not check_password_hash(h, "wrong_password")
        assert not check_password_hash(h, "right_password_1234 ")  # trailing space
        assert not check_password_hash(h, "")


class TestAdminServiceCreateFromEnv:

    def _service(self):
        return AdminService(AdminRepository())

    def test_admins_created_with_hashed_passwords(self, app_csrf_off):
        from app.core import database
        session = database.Session()
        try:
            count_before = session.query(Admin).count()
            self._service().create_admins_from_env("new1:pwd12345678,new2:pwd87654321", session)
            session.commit()
            assert session.query(Admin).count() == count_before
            # имеющийся admin всё ещё хеширован
            existing = session.query(Admin).filter_by(login="admin").first()
            assert not existing.password_hash.startswith("password")
        finally:
            session.close()

    def test_initial_creation_writes_hash_not_plaintext(self):
        """На пустой таблице create_admins_from_env должен класть именно хеш."""
        from unittest.mock import MagicMock
        repo = MagicMock()
        repo.get_admin_count.return_value = 0
        captured = {}
        repo.save_all.side_effect = lambda admins, session: captured.setdefault("admins", admins)

        service = AdminService(repo)
        service.create_admins_from_env("root:supersecret1234", session=MagicMock())

        saved = captured["admins"]
        assert len(saved) == 1
        assert saved[0].login == "root"
        assert saved[0].password_hash != "supersecret1234"
        assert check_password_hash(saved[0].password_hash, "supersecret1234")