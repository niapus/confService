from unittest.mock import MagicMock

import pytest

from app.exceptions.validation_exception import ValidationException
from app.models.conference_file import ConferenceFileType
from app.service.conference_file_service import ConferenceFileService
from tests.factories import make_conference_file


@pytest.fixture
def conference_file_service(mock_file_service, mock_conference_service, mock_conference_file_repository):
    return ConferenceFileService(
        file_service=mock_file_service,
        conference_service=mock_conference_service,
        conference_file_repository=mock_conference_file_repository
    )


class TestCreateConferenceFile:

    def test_create_proceedings_file_success(self, conference_file_service, mock_conference_service,
                                              mock_file_service, mock_conference_file_repository, mock_session):
        mock_conference_service.exists.return_value = True
        mock_conference_file_repository.get_proceedings.return_value = None
        mock_file_service.save_conference_file.return_value = ("1/proceedings/test.pdf", "test.pdf")
        mock_conference_file_repository.save.side_effect = lambda cf, s: cf

        f = MagicMock()
        dto = MagicMock()
        dto.title = "Proceedings 2024"

        result = conference_file_service.create_conference_file(
            f, dto, 1, ConferenceFileType.PROCEEDINGS, mock_session
        )

        assert result.conference_id == 1
        assert result.file_type == ConferenceFileType.PROCEEDINGS
        assert result.title == "Proceedings 2024"
        mock_conference_file_repository.save.assert_called_once()

    def test_create_proceedings_file_already_exists(self, conference_file_service, mock_conference_service,
                                                     mock_conference_file_repository, mock_session):
        mock_conference_service.exists.return_value = True
        existing = make_conference_file()
        mock_conference_file_repository.get_proceedings.return_value = existing

        f = MagicMock()
        dto = MagicMock()

        with pytest.raises(ValidationException):
            conference_file_service.create_conference_file(
                f, dto, 1, ConferenceFileType.PROCEEDINGS, mock_session
            )

    def test_create_conference_file_type(self, conference_file_service, mock_conference_service,
                                           mock_file_service, mock_conference_file_repository, mock_session):
        mock_conference_service.exists.return_value = True
        mock_file_service.save_conference_file.return_value = ("1/files/test.pdf", "test.pdf")
        mock_conference_file_repository.save.side_effect = lambda cf, s: cf

        f = MagicMock()
        dto = MagicMock()
        dto.title = "Presentation"

        result = conference_file_service.create_conference_file(
            f, dto, 1, ConferenceFileType.CONFERENCE_FILE, mock_session
        )

        assert result.file_type == ConferenceFileType.CONFERENCE_FILE
        mock_conference_file_repository.get_proceedings.assert_not_called()

    def test_create_conference_file_checks_conference_exists(self, conference_file_service,
                                                              mock_conference_service, mock_session):
        from app.exceptions.not_found_exception import ConferenceNotFoundException
        mock_conference_service.exists.side_effect = ConferenceNotFoundException(1)

        f = MagicMock()
        dto = MagicMock()

        with pytest.raises(ConferenceNotFoundException):
            conference_file_service.create_conference_file(
                f, dto, 1, ConferenceFileType.CONFERENCE_FILE, mock_session
            )


class TestGetFileById:

    def test_returns_file(self, conference_file_service, mock_conference_file_repository, mock_session):
        cf = make_conference_file()
        mock_conference_file_repository.get_by_id.return_value = cf

        result = conference_file_service.get_file_by_id(1, mock_session)
        assert result == cf


class TestDeleteConferenceFile:

    def test_delete_conference_file(self, conference_file_service, mock_conference_file_repository,
                                     mock_file_service, mock_session):
        cf = make_conference_file()
        mock_conference_file_repository.get_by_id.return_value = cf

        conference_file_service.delete_conference_file(1, mock_session)

        mock_conference_file_repository.delete.assert_called_once_with(cf, mock_session)
        mock_file_service.delete_files.assert_called_once_with([cf])


class TestDeleteAllConferenceFiles:

    def test_delete_all_conference_files(self, conference_file_service, mock_conference_file_repository,
                                          mock_file_service, mock_session):
        files = [make_conference_file(file_id=1), make_conference_file(file_id=2)]
        mock_conference_file_repository.get_all_by_conf_id.return_value = files

        conference_file_service.delete_all_conference_files(1, mock_session)

        mock_file_service.delete_files.assert_called_once_with(files)
