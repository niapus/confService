from unittest.mock import MagicMock

import pytest

from tests.factories import (
    make_conference, make_application, make_application_dto,
    make_conference_dto, make_thesis, make_thesis_dto,
    make_email_queue, make_conference_file, make_schedule_item,
    make_schedule_dto,
)


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def mock_admin_repository():
    return MagicMock()


@pytest.fixture
def mock_conference_repository():
    return MagicMock()


@pytest.fixture
def mock_application_repository():
    return MagicMock()


@pytest.fixture
def mock_thesis_repository():
    return MagicMock()


@pytest.fixture
def mock_email_repository():
    return MagicMock()


@pytest.fixture
def mock_conference_file_repository():
    return MagicMock()


@pytest.fixture
def mock_schedule_repository():
    return MagicMock()


@pytest.fixture
def mock_application_mapper():
    return MagicMock()


@pytest.fixture
def mock_schedule_mapper():
    return MagicMock()


@pytest.fixture
def mock_markdown_service():
    return MagicMock()


@pytest.fixture
def mock_email_queue_service():
    return MagicMock()


@pytest.fixture
def mock_email_service():
    return MagicMock()


@pytest.fixture
def mock_file_service():
    return MagicMock()


@pytest.fixture
def mock_conference_service():
    return MagicMock()


@pytest.fixture
def mock_application_service():
    return MagicMock()


@pytest.fixture
def mock_thesis_service():
    return MagicMock()


@pytest.fixture
def mock_jwt_service():
    return MagicMock()


@pytest.fixture
def mock_notification_service():
    return MagicMock()


@pytest.fixture
def conference():
    return make_conference()


@pytest.fixture
def application():
    return make_application()


@pytest.fixture
def application_dto():
    return make_application_dto()


@pytest.fixture
def conference_dto():
    return make_conference_dto()


@pytest.fixture
def thesis():
    return make_thesis()


@pytest.fixture
def thesis_dto():
    return make_thesis_dto()


@pytest.fixture
def email_queue_item():
    return make_email_queue()


@pytest.fixture
def conference_file():
    return make_conference_file()


@pytest.fixture
def schedule_item():
    return make_schedule_item()


@pytest.fixture
def schedule_dto():
    return make_schedule_dto()


@pytest.fixture
def conference_file_dto():
    from app.dto.dto import ConferenceFileDTO
    return ConferenceFileDTO(title="Proceedings 2024")
