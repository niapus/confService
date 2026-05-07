from datetime import date, timedelta

import pytest

from app.exceptions.conflict_exception import ApplicationAfterDeadlineException, ApplicationAlreadyExists
from app.exceptions.not_found_exception import ApplicationNotFoundException
from app.exceptions.validation_exception import ValidationException
from app.models.application import ApplicationStatus
from app.service.application_service import ApplicationService
from tests.factories import make_conference, make_application, make_application_dto


@pytest.fixture
def application_service(mock_conference_service, mock_application_repository, mock_application_mapper):
    return ApplicationService(
        conference_service=mock_conference_service,
        application_repository=mock_application_repository,
        application_mapper=mock_application_mapper,
        verification_enabled=False
    )


@pytest.fixture
def application_service_verified(mock_conference_service, mock_application_repository, mock_application_mapper):
    return ApplicationService(
        conference_service=mock_conference_service,
        application_repository=mock_application_repository,
        application_mapper=mock_application_mapper,
        verification_enabled=True
    )


class TestCreateApplication:

    def test_create_application_success(self, application_service, mock_conference_service,
                                        mock_application_repository, mock_session, application_dto):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_application_repository.find_confirmed_application_by_conf_email.return_value = None
        mock_application_repository.save.side_effect = lambda app, s: app

        result = application_service.create_application(1, application_dto, mock_session)

        assert result.surname == "Ivanov"
        assert result.email == "ivan@test.com"
        assert result.status == ApplicationStatus.CONFIRMED
        mock_application_repository.save.assert_called_once()

    def test_create_application_after_deadline(self, application_service, mock_conference_service,
                                               mock_session, application_dto):
        conf = make_conference(registration_deadline=date.today() - timedelta(days=1))
        mock_conference_service.get_conference_by_id.return_value = conf

        with pytest.raises(ApplicationAfterDeadlineException):
            application_service.create_application(1, application_dto, mock_session)

    def test_create_application_birth_date_in_future(self, application_service, mock_conference_service,
                                                     mock_session):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        dto = make_application_dto(birth_date=date.today() + timedelta(days=1))

        with pytest.raises(ValidationException):
            application_service.create_application(1, dto, mock_session)

    def test_create_application_already_exists(self, application_service, mock_conference_service,
                                               mock_application_repository, mock_session, application_dto):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        existing = make_application()
        mock_application_repository.find_confirmed_application_by_conf_email.return_value = existing

        with pytest.raises(ApplicationAlreadyExists):
            application_service.create_application(1, application_dto, mock_session)

    def test_create_application_verification_enabled(self, application_service_verified,
                                                     mock_conference_service, mock_application_repository,
                                                     mock_session, application_dto):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_application_repository.find_confirmed_application_by_conf_email.return_value = None
        mock_application_repository.save.side_effect = lambda app, s: app

        result = application_service_verified.create_application(1, application_dto, mock_session)
        assert result.status == ApplicationStatus.UNCONFIRMED

    def test_create_application_fills_all_fields(self, application_service, mock_conference_service,
                                                  mock_application_repository, mock_session, application_dto):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_application_repository.find_confirmed_application_by_conf_email.return_value = None
        mock_application_repository.save.side_effect = lambda app, s: app

        result = application_service.create_application(1, application_dto, mock_session)

        assert result.surname == application_dto.surname
        assert result.name == application_dto.name
        assert result.patronymic == application_dto.patronymic
        assert result.gender == application_dto.gender
        assert result.birth_date == application_dto.birth_date
        assert result.degree == application_dto.degree
        assert result.is_worker == application_dto.is_worker
        assert result.is_student == application_dto.is_student
        assert result.work_name == application_dto.work_name
        assert result.work_place == application_dto.work_place
        assert result.work_position == application_dto.work_position
        assert result.study_name == application_dto.study_name
        assert result.study_place == application_dto.study_place
        assert result.study_level == application_dto.study_level
        assert result.participation_format == application_dto.participation_format
        assert result.email == application_dto.email
        assert result.conference_id == 1


class TestGetConfirmedApplicationByConfEmail:

    def test_returns_application(self, application_service, mock_application_repository, mock_session):
        app = make_application()
        mock_application_repository.find_confirmed_application_by_conf_email.return_value = app

        result = application_service.get_confirmed_application_by_conf_email(1, "ivan@test.com", mock_session)
        assert result == app

    def test_returns_none_when_not_found(self, application_service, mock_application_repository, mock_session):
        mock_application_repository.find_confirmed_application_by_conf_email.return_value = None

        result = application_service.get_confirmed_application_by_conf_email(1, "noone@test.com", mock_session)
        assert result is None


class TestGetFullApplicationsForConference:

    def test_returns_mapped_dtos(self, application_service, mock_application_repository,
                                  mock_application_mapper, mock_session):
        apps = [make_application()]
        mock_application_repository.get_full_applications_for_conference.return_value = apps
        mock_application_mapper.applications_to_full_applications_dto.return_value = [{"id": 1}]

        result = application_service.get_full_applications_for_conference(1, mock_session)
        assert result == [{"id": 1}]
        mock_application_mapper.applications_to_full_applications_dto.assert_called_once_with(apps)


class TestGetApplicationFromSchedule:

    def test_returns_applications(self, application_service, mock_conference_service,
                                   mock_application_repository, mock_session):
        mock_conference_service.exists.return_value = True
        mock_application_repository.get_applications_from_schedule.return_value = ["app1"]

        result = application_service.get_application_from_schedule(1, mock_session)
        assert result == ["app1"]

    def test_raises_when_conference_not_found(self, application_service, mock_conference_service, mock_session):
        from app.exceptions.not_found_exception import ConferenceNotFoundException
        mock_conference_service.exists.side_effect = ConferenceNotFoundException(1)

        with pytest.raises(ConferenceNotFoundException):
            application_service.get_application_from_schedule(1, mock_session)


class TestGetAllApplications:

    def test_returns_all(self, application_service, mock_application_repository, mock_session):
        mock_application_repository.get_all.return_value = ["app1", "app2"]

        result = application_service.get_all_applications(mock_session)
        assert result == ["app1", "app2"]


class TestGetById:

    def test_returns_application(self, application_service, mock_application_repository, mock_session):
        app = make_application()
        mock_application_repository.get_by_id.return_value = app

        result = application_service.get_by_id(1, mock_session)
        assert result == app

    def test_raises_not_found(self, application_service, mock_application_repository, mock_session):
        mock_application_repository.get_by_id.return_value = None

        with pytest.raises(ApplicationNotFoundException):
            application_service.get_by_id(999, mock_session)


class TestSetStatus:

    def test_sets_status(self, application_service, mock_application_repository, mock_session):
        app = make_application()

        application_service.set_status(app, ApplicationStatus.CONFIRMED, mock_session)

        assert app.status == ApplicationStatus.CONFIRMED
        mock_application_repository.save.assert_called_once_with(app, mock_session)
