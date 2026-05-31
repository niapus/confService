from unittest.mock import ANY

from app.exceptions.auth_exception import InvalidCredentialsException
from app.exceptions.email_verification_exception import EmailVerificationException
from app.models.admin import Admin
from tests.factories import make_application


class TestViewAdminLogin:

    def test_returns_200(self, client, mock_services):
        resp = client.get("/auth/login")
        assert resp.status_code == 200


class TestAdminLogin:

    def test_success_redirects_to_admin(self, client, mock_services):
        admin = Admin()
        admin.id = 1
        admin.login = "admin"
        mock_services["admin"].authenticate.return_value = admin

        resp = client.post("/auth/login", data={"login": "admin", "password": "password1234"})
        assert resp.status_code == 302
        assert "/admin" in resp.headers["Location"]

    def test_sets_session_vars(self, client, mock_services):
        admin = Admin()
        admin.id = 5
        admin.login = "superadmin"
        mock_services["admin"].authenticate.return_value = admin
        resp = client.post("/auth/login", data={"login": "superadmin", "password": "pass"})
        assert resp.status_code == 302

        with client.session_transaction() as sess:
            assert sess["admin_id"] == 5
            assert sess["admin_login"] == "superadmin"

    def test_invalid_credentials_renders_error(self, client, mock_services):
        mock_services["admin"].authenticate.side_effect = InvalidCredentialsException()

        resp = client.post("/auth/login", data={"login": "bad", "password": "bad"})
        assert resp.status_code == 401

    def test_missing_login_field(self, client, mock_services):
        mock_services["admin"].authenticate.side_effect = InvalidCredentialsException()
        resp = client.post("/auth/login", data={"password": "pass"})
        assert resp.status_code == 401

    def test_missing_password_field(self, client, mock_services):
        mock_services["admin"].authenticate.side_effect = InvalidCredentialsException()
        resp = client.post("/auth/login", data={"login": "admin"})
        assert resp.status_code == 401


class TestVerifyEmail:

    def test_success_returns_200(self, client, mock_services):
        app_obj = make_application()
        mock_services["verification"].verify_email.return_value = app_obj
        mock_services["notification"].send_registration_confirmed.return_value = None

        resp = client.get("/auth/verify/sometoken")
        assert resp.status_code == 200
        mock_services["verification"].verify_email.assert_called_once_with("sometoken", ANY)
        mock_services["notification"].send_registration_confirmed.assert_called_once_with(app_obj, ANY)

    def test_invalid_token_renders_error(self, client, mock_services):
        mock_services["verification"].verify_email.side_effect = EmailVerificationException("Неверный токен")

        resp = client.get("/auth/verify/badtoken")
        assert resp.status_code == 400
