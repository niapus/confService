from unittest.mock import ANY, MagicMock, patch

from app.exceptions.conversion_exception import EmptyRequiredFieldException
from app.exceptions.conflict_exception import (
    ApplicationAfterDeadlineException, ThesisAfterDeadlineException,
    ApplicationAlreadyExists, ConferenceAlreadyEndedException,
)
from app.exceptions.file_exception import FileSizeException, FileExtensionException
from app.exceptions.not_found_exception import ConferenceNotFoundException, ApplicationNotFoundException
from app.exceptions.validation_exception import ValidationException
from tests.factories import make_conference, make_application, make_thesis


class TestShowConference:

    def test_returns_200(self, client, mock_services):
        mock_services["conference"].get_conference_by_id.return_value = make_conference()
        mock_services["schedule"].get_schedule.return_value = []
        resp = client.get("/conference/1")
        assert resp.status_code == 200

    def test_calls_services(self, client, mock_services):
        mock_services["conference"].get_conference_by_id.return_value = make_conference()
        mock_services["schedule"].get_schedule.return_value = []
        client.get("/conference/1")
        mock_services["conference"].get_conference_by_id.assert_called_once_with(1, ANY)
        mock_services["schedule"].get_schedule.assert_called_once_with(1, ANY)

    def test_not_found(self, client, mock_services):
        mock_services["conference"].get_conference_by_id.side_effect = ConferenceNotFoundException(1)
        mock_services["schedule"].get_schedule.return_value = []
        resp = client.get("/conference/999")
        assert resp.status_code == 404


class TestShowApplication:

    def test_returns_200(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        resp = client.get("/conference/1/application")
        assert resp.status_code == 200

    def test_conference_not_found_returns_404(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.side_effect = ConferenceNotFoundException(1)
        resp = client.get("/conference/1/application")
        assert resp.status_code == 404

    def test_conference_already_ended_returns_409(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.side_effect = ConferenceAlreadyEndedException(1)
        resp = client.get("/conference/1/application")
        assert resp.status_code == 409


class TestShowUploadThesis:

    def test_returns_200(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        resp = client.get("/conference/1/thesis")
        assert resp.status_code == 200

    def test_conference_not_found_returns_404(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.side_effect = ConferenceNotFoundException(1)
        resp = client.get("/conference/1/thesis")
        assert resp.status_code == 404

    def test_conference_already_ended_returns_409(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.side_effect = ConferenceAlreadyEndedException(1)
        resp = client.get("/conference/1/thesis")
        assert resp.status_code == 409


class TestCreateApplication:

    def test_success_without_verification(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["application"].create_application.return_value = make_application()
        mock_services["notification"].verification_enabled = False

        resp = client.post("/conference/1/application", data={
            "surname": "Ivanov",
            "name": "Ivan",
            "patronymic": "Ivanovich",
            "gender": "male",
            "birth_date": "2000-01-15",
            "degree": "none",
            "status": ["student"],
            "study_name": "Test Uni",
            "study_place": "Test City",
            "study_level": "education_mag",
            "participation_format": "offline",
            "email": "ivan@test.com",
        })
        assert resp.status_code == 302
        assert "/conference/1" in resp.headers["Location"]

    def test_success_with_verification(self, client, mock_services):
        conf = make_conference()
        app_obj = make_application()
        mock_services["conference"].get_upcoming_conference.return_value = conf
        mock_services["application"].create_application.return_value = app_obj
        mock_services["notification"].verification_enabled = True
        mock_services["verification"].generate_verification_token.return_value = "token123"
        mock_services["notification"].send_verification_email.return_value = None

        resp = client.post("/conference/1/application", data={
            "surname": "Ivanov",
            "name": "Ivan",
            "patronymic": "Ivanovich",
            "gender": "male",
            "birth_date": "2000-01-15",
            "degree": "none",
            "status": ["student"],
            "study_name": "Test Uni",
            "study_place": "Test City",
            "study_level": "education_mag",
            "participation_format": "offline",
            "email": "ivan@test.com",
        })
        assert resp.status_code == 302
        assert "/conference/1/application/verify" in resp.headers["Location"]

    def test_after_deadline(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["application"].create_application.side_effect = ApplicationAfterDeadlineException("2025-01-01")
        resp = client.post("/conference/1/application", data={
            "surname": "Ivanov",
            "name": "Ivan",
            "patronymic": "Ivanovich",
            "gender": "male",
            "birth_date": "2000-01-15",
            "degree": "none",
            "status": ["student"],
            "study_name": "Test Uni",
            "study_place": "Test City",
            "study_level": "education_mag",
            "participation_format": "offline",
            "email": "ivan@test.com",
        })
        # ConflictException -> AppException handler -> 409
        assert resp.status_code == 409

    def test_duplicate_email_returns_409(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["application"].create_application.side_effect = ApplicationAlreadyExists("ivan@test.com")
        resp = client.post("/conference/1/application", data={
            "surname": "Ivanov",
            "name": "Ivan",
            "patronymic": "Ivanovich",
            "gender": "male",
            "birth_date": "2000-01-15",
            "degree": "none",
            "status": ["student"],
            "study_name": "Test Uni",
            "study_place": "Test City",
            "study_level": "education_mag",
            "participation_format": "offline",
            "email": "ivan@test.com",
        })
        assert resp.status_code == 409

    def test_validation_error_renders_form(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["application"].create_application.side_effect = EmptyRequiredFieldException("surname")

        resp = client.post("/conference/1/application", data={
            "surname": "",
            "name": "Ivan",
            "email": "ivan@test.com",
        })
        # handle_form_errors catches ConversionException -> renders template with error
        assert resp.status_code == 200


class TestUploadThesis:

    def test_success(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["thesis"].create_thesis.return_value = make_thesis()

        resp = client.post("/conference/1/thesis", data={
            "authors": "Ivanov I.I.",
            "title": "Test Thesis",
            "email": "ivan@test.com",
        })
        assert resp.status_code == 302
        assert "/conference/1" in resp.headers["Location"]

    def test_after_deadline(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["thesis"].create_thesis.side_effect = ThesisAfterDeadlineException("2025-01-01")
        resp = client.post("/conference/1/thesis", data={
            "authors": "Ivanov I.I.",
            "title": "Test Thesis",
            "email": "ivan@test.com",
        })
        assert resp.status_code == 409

    def test_file_size_error(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["thesis"].create_thesis.side_effect = FileSizeException(16)

        resp = client.post("/conference/1/thesis", data={
            "authors": "Ivanov I.I.",
            "title": "Test Thesis",
            "email": "ivan@test.com",
        })
        # handle_form_errors catches FileException -> renders template
        assert resp.status_code == 200

    def test_file_extension_error(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["thesis"].create_thesis.side_effect = FileExtensionException(".exe")

        resp = client.post("/conference/1/thesis", data={
            "authors": "Ivanov I.I.",
            "title": "Test Thesis",
            "email": "ivan@test.com",
        })
        assert resp.status_code == 200

    def test_empty_authors_renders_form(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["thesis"].create_thesis.side_effect = EmptyRequiredFieldException("authors")

        resp = client.post("/conference/1/thesis", data={
            "authors": "",
            "title": "Test",
            "email": "ivan@test.com",
        })
        assert resp.status_code == 200

    def test_application_not_found_returns_404(self, client, mock_services):
        mock_services["conference"].get_upcoming_conference.return_value = make_conference()
        mock_services["thesis"].create_thesis.side_effect = ApplicationNotFoundException("unknown@test.com")

        resp = client.post("/conference/1/thesis", data={
            "authors": "Ivanov I.I.",
            "title": "Test Thesis",
            "email": "unknown@test.com",
        })
        assert resp.status_code == 404


class TestVerifyEmailPage:

    def test_returns_200(self, client, mock_services):
        resp = client.get("/conference/1/application/verify")
        assert resp.status_code == 200
