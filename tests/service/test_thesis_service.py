from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.exceptions.conflict_exception import ThesisAfterDeadlineException
from app.exceptions.not_found_exception import ApplicationNotFoundException, ThesisNotFoundException
from app.models.thesis import ThesisStatus
from app.service.thesis_service import ThesisService
from tests.factories import make_conference, make_application, make_thesis, make_thesis_dto


@pytest.fixture
def thesis_service(mock_conference_service, mock_application_service, mock_file_service, mock_thesis_repository):
    return ThesisService(
        conference_service=mock_conference_service,
        application_service=mock_application_service,
        file_service=mock_file_service,
        thesis_repository=mock_thesis_repository
    )


class TestCreateThesis:

    def test_create_thesis_success(self, thesis_service, mock_conference_service,
                                    mock_application_service, mock_file_service,
                                    mock_thesis_repository, mock_session):
        conf = make_conference()
        app = make_application()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_application_service.get_confirmed_application_by_conf_email.return_value = app
        mock_file_service.save_thesis_file.return_value = ("1/theses/test.pdf", "test.pdf")
        mock_thesis_repository.save.side_effect = lambda t, s: t

        dto = make_thesis_dto()
        result = thesis_service.create_thesis(1, MagicMock(), dto, mock_session)

        assert result.application_id == app.id
        assert result.authors == "Ivanov I.I."
        assert result.title == "Test Thesis"
        assert result.status == ThesisStatus.PENDING
        mock_thesis_repository.save.assert_called_once()

    def test_create_thesis_after_deadline(self, thesis_service, mock_conference_service, mock_session):
        conf = make_conference(submission_deadline=date.today() - timedelta(days=1))
        mock_conference_service.get_conference_by_id.return_value = conf

        with pytest.raises(ThesisAfterDeadlineException):
            thesis_service.create_thesis(1, MagicMock(), make_thesis_dto(), mock_session)

    def test_create_thesis_application_not_found(self, thesis_service, mock_conference_service,
                                                  mock_application_service, mock_session):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_application_service.get_confirmed_application_by_conf_email.return_value = None

        with pytest.raises(ApplicationNotFoundException):
            thesis_service.create_thesis(1, MagicMock(), make_thesis_dto(), mock_session)


class TestGetAllTheses:

    def test_returns_all(self, thesis_service, mock_thesis_repository, mock_session):
        mock_thesis_repository.get_all.return_value = ["t1", "t2"]

        result = thesis_service.get_all_theses(mock_session)
        assert result == ["t1", "t2"]


class TestGetThesisById:

    def test_returns_thesis(self, thesis_service, mock_thesis_repository, mock_session):
        thesis = make_thesis()
        mock_thesis_repository.get_by_id.return_value = thesis

        result = thesis_service.get_thesis_by_id(1, mock_session)
        assert result == thesis

    def test_raises_not_found(self, thesis_service, mock_thesis_repository, mock_session):
        mock_thesis_repository.get_by_id.return_value = None

        with pytest.raises(ThesisNotFoundException):
            thesis_service.get_thesis_by_id(999, mock_session)


class TestUpdateThesisStatus:

    def test_update_status_to_accepted(self, thesis_service, mock_thesis_repository, mock_session):
        thesis = make_thesis()
        mock_thesis_repository.get_by_id.return_value = thesis
        mock_thesis_repository.save.side_effect = lambda t, s: t

        result = thesis_service.update_thesis_status(1, "accepted", mock_session)

        assert result.status == ThesisStatus.ACCEPTED
        mock_thesis_repository.save.assert_called_once()

    def test_update_status_to_rejected(self, thesis_service, mock_thesis_repository, mock_session):
        thesis = make_thesis()
        mock_thesis_repository.get_by_id.return_value = thesis
        mock_thesis_repository.save.side_effect = lambda t, s: t

        result = thesis_service.update_thesis_status(1, "rejected", mock_session)
        assert result.status == ThesisStatus.REJECTED


class TestDeleteAllConferenceThesesFiles:

    def test_deletes_files(self, thesis_service, mock_thesis_repository, mock_file_service, mock_session):
        theses = [make_thesis()]
        mock_thesis_repository.get_by_conf_id.return_value = theses

        thesis_service.delete_all_conference_theses_files(1, mock_session)

        mock_file_service.delete_files.assert_called_once_with(theses)


class TestGetAcceptedThesesWithApplications:

    def test_returns_accepted(self, thesis_service, mock_thesis_repository, mock_session):
        mock_thesis_repository.get_accepted_theses_with_applications.return_value = ["t1"]

        result = thesis_service.get_accepted_theses_with_applications(1, mock_session)
        assert result == ["t1"]
