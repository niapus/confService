from datetime import date, timedelta

import pytest

from app.exceptions.conflict_exception import ApplicationAfterDeadlineException
from app.exceptions.not_found_exception import ConferenceNotFoundException
from app.exceptions.validation_exception import ValidationException
from app.service.conference_service import ConferenceService
from tests.factories import make_conference, make_conference_dto


@pytest.fixture
def conference_service(mock_conference_repository, mock_markdown_service, mock_notification_service):
    return ConferenceService(
        conference_repository=mock_conference_repository,
        markdown_service=mock_markdown_service,
        notification=mock_notification_service
    )


class TestGetConferenceById:

    def test_returns_conference(self, conference_service, mock_conference_repository, mock_session):
        conf = make_conference()
        mock_conference_repository.get_by_id.return_value = conf

        result = conference_service.get_conference_by_id(1, mock_session)
        assert result == conf

    def test_raises_not_found(self, conference_service, mock_conference_repository, mock_session):
        mock_conference_repository.get_by_id.return_value = None

        with pytest.raises(ConferenceNotFoundException):
            conference_service.get_conference_by_id(999, mock_session)


class TestExists:

    def test_returns_true_when_exists(self, conference_service, mock_conference_repository, mock_session):
        mock_conference_repository.exists.return_value = True

        result = conference_service.exists(1, mock_session)
        assert result is True

    def test_raises_not_found_when_not_exists(self, conference_service, mock_conference_repository, mock_session):
        mock_conference_repository.exists.return_value = False

        with pytest.raises(ConferenceNotFoundException):
            conference_service.exists(999, mock_session)


class TestCheckRegistrationOpen:

    def test_does_not_raise_when_deadline_not_passed(self, conference_service, mock_conference_repository, mock_session):
        conf = make_conference(registration_deadline=date.today() + timedelta(days=5))
        mock_conference_repository.get_by_id.return_value = conf

        conference_service.check_registration_open(1, mock_session)

    def test_raises_when_deadline_passed(self, conference_service, mock_conference_repository, mock_session):
        conf = make_conference(registration_deadline=date.today() - timedelta(days=1))
        mock_conference_repository.get_by_id.return_value = conf

        with pytest.raises(ApplicationAfterDeadlineException):
            conference_service.check_registration_open(1, mock_session)


class TestCreateConference:

    def test_create_conference_success(self, conference_service, mock_conference_repository,
                                        mock_markdown_service, mock_session):
        dto = make_conference_dto()
        mock_markdown_service.to_html.return_value = "<h1>Desc</h1>"
        mock_conference_repository.save.side_effect = lambda c, s: c

        result = conference_service.create_conference(dto, mock_session)

        assert result.title == "New Conference"
        assert result.description_html == "<h1>Desc</h1>"
        mock_conference_repository.save.assert_called_once()

    def test_create_conference_converts_md_to_html(self, conference_service, mock_conference_repository,
                                                     mock_markdown_service, mock_session):
        dto = make_conference_dto(description_md="# New")
        mock_markdown_service.to_html.return_value = "<h1>New</h1>"
        mock_conference_repository.save.side_effect = lambda c, s: c

        result = conference_service.create_conference(dto, mock_session)
        mock_markdown_service.to_html.assert_called_once_with("# New")
        assert result.description_html == "<h1>New</h1>"

    def test_create_conference_start_in_past(self, conference_service, mock_session):
        dto = make_conference_dto(start_date=date.today() - timedelta(days=1))

        with pytest.raises(ValidationException):
            conference_service.create_conference(dto, mock_session)

    def test_create_conference_end_before_start(self, conference_service, mock_session):
        today = date.today()
        dto = make_conference_dto(
            start_date=today + timedelta(days=62),
            end_date=today + timedelta(days=60)
        )

        with pytest.raises(ValidationException):
            conference_service.create_conference(dto, mock_session)

    def test_create_conference_reg_deadline_after_start(self, conference_service, mock_session):
        today = date.today()
        dto = make_conference_dto(
            start_date=today + timedelta(days=60),
            registration_deadline=today + timedelta(days=61)
        )

        with pytest.raises(ValidationException):
            conference_service.create_conference(dto, mock_session)

    def test_create_conference_submission_deadline_after_start(self, conference_service, mock_session):
        today = date.today()
        dto = make_conference_dto(
            start_date=today + timedelta(days=60),
            submission_deadline=today + timedelta(days=61)
        )

        with pytest.raises(ValidationException):
            conference_service.create_conference(dto, mock_session)


class TestUpdateConference:

    def test_update_conference_success(self, conference_service, mock_conference_repository,
                                        mock_markdown_service, mock_notification_service, mock_session):
        conf = make_conference()
        mock_conference_repository.get_by_id.return_value = conf
        mock_markdown_service.to_html.return_value = "<h1>Updated</h1>"
        mock_notification_service.mail_enabled = False

        dto = make_conference_dto(title="Updated Conference")
        result = conference_service.update_conference(1, dto, mock_session)

        assert result.title == "Updated Conference"

    def test_update_conference_sends_notification_when_changed(self, conference_service,
                                                                mock_conference_repository,
                                                                mock_markdown_service,
                                                                mock_notification_service, mock_session):
        conf = make_conference()
        mock_conference_repository.get_by_id.return_value = conf
        mock_markdown_service.to_html.return_value = "<h1>Updated</h1>"
        mock_notification_service.mail_enabled = True

        dto = make_conference_dto(title="Changed Title")
        conference_service.update_conference(1, dto, mock_session)

        mock_notification_service.send_conference_updated.assert_called_once()

    def test_update_conference_no_notification_when_not_changed(self, conference_service,
                                                                 mock_conference_repository,
                                                                 mock_markdown_service,
                                                                 mock_notification_service, mock_session):
        conf = make_conference()
        mock_conference_repository.get_by_id.return_value = conf
        mock_notification_service.mail_enabled = True

        dto = make_conference_dto(
            title=conf.title,
            description_md=conf.description_md,
            start_date=conf.start_date,
            end_date=conf.end_date,
            registration_deadline=conf.registration_deadline,
            submission_deadline=conf.submission_deadline,
        )
        conference_service.update_conference(1, dto, mock_session)

        mock_notification_service.send_conference_updated.assert_not_called()

    def test_update_conference_validates_dates(self, conference_service, mock_conference_repository, mock_session):
        conf = make_conference()
        mock_conference_repository.get_by_id.return_value = conf

        dto = make_conference_dto(start_date=date.today() - timedelta(days=1))

        with pytest.raises(ValidationException):
            conference_service.update_conference(1, dto, mock_session)

    def test_update_md_html_not_reconverted_when_same(self, conference_service,
                                                       mock_conference_repository,
                                                       mock_markdown_service,
                                                       mock_notification_service, mock_session):
        conf = make_conference()
        conf.description_html = "<h1>Hello</h1>"
        mock_conference_repository.get_by_id.return_value = conf
        mock_notification_service.mail_enabled = False

        dto = make_conference_dto(description_md=conf.description_md)
        conference_service.update_conference(1, dto, mock_session)

        mock_markdown_service.to_html.assert_not_called()

    def test_update_md_html_reconverted_when_changed(self, conference_service,
                                                      mock_conference_repository,
                                                      mock_markdown_service,
                                                      mock_notification_service, mock_session):
        conf = make_conference()
        conf.description_html = "<h1>Hello</h1>"
        mock_conference_repository.get_by_id.return_value = conf
        mock_markdown_service.to_html.return_value = "<h1>New</h1>"
        mock_notification_service.mail_enabled = False

        dto = make_conference_dto(description_md="# New")
        conference_service.update_conference(1, dto, mock_session)

        mock_markdown_service.to_html.assert_called_once_with("# New")

    def test_update_md_html_reconverted_when_html_is_none(self, conference_service,
                                                           mock_conference_repository,
                                                           mock_markdown_service,
                                                           mock_notification_service, mock_session):
        conf = make_conference()
        conf.description_html = None
        mock_conference_repository.get_by_id.return_value = conf
        mock_markdown_service.to_html.return_value = "<h1>Hello</h1>"
        mock_notification_service.mail_enabled = False

        dto = make_conference_dto(description_md=conf.description_md)
        conference_service.update_conference(1, dto, mock_session)

        mock_markdown_service.to_html.assert_called_once()


class TestGetStartingInDays:

    def test_returns_conferences(self, conference_service, mock_conference_repository, mock_session):
        mock_conference_repository.get_starting_in_days.return_value = ["conf1"]

        result = conference_service.get_starting_in_days(mock_session, 3)
        assert result == ["conf1"]


class TestGetAllConferences:

    def test_returns_all(self, conference_service, mock_conference_repository, mock_session):
        mock_conference_repository.get_all.return_value = ["conf1", "conf2"]

        result = conference_service.get_all_conferences(mock_session)
        assert result == ["conf1", "conf2"]


class TestDeleteConference:

    def test_delete_conference(self, conference_service, mock_conference_repository, mock_session):
        conf = make_conference()

        conference_service.delete_conference(conf, mock_session)
        mock_conference_repository.delete.assert_called_once_with(conf, mock_session)


class TestGetFutureConferences:

    def test_returns_future(self, conference_service, mock_conference_repository, mock_session):
        mock_conference_repository.get_future_conferences.return_value = ["conf1"]

        result = conference_service.get_future_conferences(mock_session)
        assert result == ["conf1"]


class TestGetPastConferences:

    def test_returns_past(self, conference_service, mock_conference_repository, mock_session):
        mock_conference_repository.get_past_conferences.return_value = ["conf0"]

        result = conference_service.get_past_conferences(mock_session)
        assert result == ["conf0"]
