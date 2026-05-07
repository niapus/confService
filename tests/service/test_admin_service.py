from unittest.mock import MagicMock

import pytest

from app.exceptions.auth_exception import InvalidCredentialsException
from app.service.admin_service import AdminService


@pytest.fixture
def admin_service(mock_admin_repository):
    return AdminService(mock_admin_repository)


class TestAdminServiceCreateAdminsFromEnv:

    def test_skips_if_admins_exist(self, admin_service, mock_admin_repository, mock_session):
        mock_admin_repository.get_admin_count.return_value = 1
        admin_service.create_admins_from_env("admin:pass123", mock_session)
        mock_admin_repository.save_all.assert_not_called()

    def test_creates_admins_from_env_data(self, admin_service, mock_admin_repository, mock_session):
        mock_admin_repository.get_admin_count.return_value = 0
        admin_service.create_admins_from_env("admin1:pass1,admin2:pass2", mock_session)
        mock_admin_repository.save_all.assert_called_once()
        admins = mock_admin_repository.save_all.call_args[0][0]
        assert len(admins) == 2
        assert admins[0].login == "admin1"
        assert admins[1].login == "admin2"

    def test_creates_single_admin(self, admin_service, mock_admin_repository, mock_session):
        mock_admin_repository.get_admin_count.return_value = 0
        admin_service.create_admins_from_env("admin:secret", mock_session)
        mock_admin_repository.save_all.assert_called_once()
        admins = mock_admin_repository.save_all.call_args[0][0]
        assert len(admins) == 1
        assert admins[0].login == "admin"

    def test_password_is_hashed(self, admin_service, mock_admin_repository, mock_session):
        mock_admin_repository.get_admin_count.return_value = 0
        admin_service.create_admins_from_env("admin:secret", mock_session)
        admins = mock_admin_repository.save_all.call_args[0][0]
        assert admins[0].password_hash != "secret"

    def test_password_with_colon(self, admin_service, mock_admin_repository, mock_session):
        mock_admin_repository.get_admin_count.return_value = 0
        admin_service.create_admins_from_env("admin:pass:with:colons", mock_session)
        admins = mock_admin_repository.save_all.call_args[0][0]
        assert admins[0].login == "admin"


class TestAdminServiceAuthenticate:

    def test_authenticate_success(self, admin_service, mock_admin_repository, mock_session):
        from werkzeug.security import generate_password_hash
        admin = MagicMock()
        admin.password_hash = generate_password_hash("password123")
        mock_admin_repository.get_admin_by_login.return_value = admin

        result = admin_service.authenticate("admin", "password123", mock_session)
        assert result == admin

    def test_authenticate_wrong_login(self, admin_service, mock_admin_repository, mock_session):
        mock_admin_repository.get_admin_by_login.return_value = None

        with pytest.raises(InvalidCredentialsException):
            admin_service.authenticate("unknown", "password", mock_session)

    def test_authenticate_wrong_password(self, admin_service, mock_admin_repository, mock_session):
        from werkzeug.security import generate_password_hash
        admin = MagicMock()
        admin.password_hash = generate_password_hash("correct_password")
        mock_admin_repository.get_admin_by_login.return_value = admin

        with pytest.raises(InvalidCredentialsException):
            admin_service.authenticate("admin", "wrong_password", mock_session)
