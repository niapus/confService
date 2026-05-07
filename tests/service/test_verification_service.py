import pytest

from app.exceptions.email_verification_exception import EmailVerificationException
from app.models.application import ApplicationStatus
from app.service.verification_service import VerificationService
from tests.factories import make_application


@pytest.fixture
def verification_service(mock_application_service, mock_jwt_service):
    return VerificationService(
        application_service=mock_application_service,
        jwt_service=mock_jwt_service
    )


class TestGenerateVerificationToken:

    def test_generates_token(self, verification_service, mock_jwt_service):
        app = make_application()
        mock_jwt_service.generate_verification_token.return_value = "token123"

        result = verification_service.generate_verification_token(app)

        mock_jwt_service.generate_verification_token.assert_called_once_with(app.id, app.email)
        assert result == "token123"


class TestVerifyEmail:

    def test_verify_email_success(self, verification_service, mock_jwt_service,
                                   mock_application_service, mock_session):
        app = make_application(status=ApplicationStatus.UNCONFIRMED)
        mock_jwt_service.verify_token.return_value = {
            'app_id': app.id,
            'email': app.email
        }
        mock_application_service.get_by_id.return_value = app

        result = verification_service.verify_email("valid_token", mock_session)

        assert result == app
        mock_application_service.set_status.assert_called_once_with(
            app, ApplicationStatus.CONFIRMED, mock_session
        )

    def test_verify_email_mismatch_email(self, verification_service, mock_jwt_service,
                                          mock_application_service, mock_session):
        app = make_application(email="ivan@test.com")
        mock_jwt_service.verify_token.return_value = {
            'app_id': app.id,
            'email': 'other@test.com'
        }
        mock_application_service.get_by_id.return_value = app

        with pytest.raises(EmailVerificationException):
            verification_service.verify_email("token", mock_session)

    def test_verify_email_already_confirmed(self, verification_service, mock_jwt_service,
                                             mock_application_service, mock_session):
        app = make_application(status=ApplicationStatus.CONFIRMED)
        mock_jwt_service.verify_token.return_value = {
            'app_id': app.id,
            'email': app.email
        }
        mock_application_service.get_by_id.return_value = app

        with pytest.raises(EmailVerificationException):
            verification_service.verify_email("token", mock_session)
